// SetupWizard — the step-by-step Einrichtungs-Wizard for authoring a canonical
// from a rough bbox already drawn on the chart. Steps (registration-style, with
// Back/Next and free jumping to earlier steps):
//   1. Ausschluss  — freehand eraser (Radierer): paint over neighbouring ink so
//                    it can't pollute the skeleton. Strokes → bbox.mask_strokes.
//   2. Lineatur    — drag Grundlinie / Mittellinie; Oberlinie/Unterlinie derive,
//                    each toggleable per glyph.
//   3. Schräge     — place + angle one or more slant guides (several individually
//                    placed lines for m/n/u; all share the angle).
//   4. Weg         — draw the ductus with the stylus; saves the canonical and
//                    lets you re-sample it to a different anchor count.
//   5. Übersicht   — open the (large) Diagnose modal to review, optionally apply
//                    to all positions, then approve → lock (the bbox's `locked`).
//
// This is the single editing surface — the advanced EditorPage was retired, so
// everything that used to live there (ascender/descender toggles, n_anchors
// resample, the diagnostic + M4 fit) is reachable from here. Changes live-commit
// (PUT bbox / POST trace); the lock IS the commit gesture, so there is no
// separate cancel-revert. Mounted once in AppLayout and driven by `wizardGlyph`
// in the admin context.
//
// The crop canvas carries a shared zoom/pan on every step (wheel or the floating
// −/slider/+ control; Schwenken toggle or a wheel-zoomed drag to pan). It opens
// pre-zoomed (defaultZoomFor) so a small letter — a fresh bbox seeds its x-height
// band at only ~35 % of the box height — already fills the frame on Ausschluss
// instead of sitting tiny in the middle; Anpassen returns to the full crop.

import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';
import LockIcon from '@mui/icons-material/Lock';
import OpenWithIcon from '@mui/icons-material/OpenWith';
import RefreshIcon from '@mui/icons-material/Refresh';
import RemoveIcon from '@mui/icons-material/Remove';
import UndoIcon from '@mui/icons-material/Undo';
import VisibilityIcon from '@mui/icons-material/Visibility';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  FormControlLabel,
  IconButton,
  Slider,
  Stack,
  Step,
  StepButton,
  Stepper,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';

import { cropUrl, getGlyph, postResample, postTrace, putBbox } from '../../api';
import { glyphKeyFor, knownGlyph, LETTER_BY_KEY, POSITIONS } from '../../constants';
import { couplingLabel } from '../../lib/labels';
import { useAdmin } from '../../state';
import type { BboxIn, BboxOut, CouplingHeight, GlyphSummary, GuideConfig, MaskStroke, StrokePoint } from '../../types';

const SLANT_COLOR = '#39d98a';
const COUPLING_OPTIONS: CouplingHeight[] = ['baseline', 'midband', 'ascender', 'descender'];

// Wizard canvas zoom. 1 = fit-to-view (the whole bbox fills the frame); above
// that the crop is magnified and can be panned (Schwenken) to reach the box
// edges, where a neighbour's ink pokes in and needs erasing.
const ZOOM_MIN = 1;
const ZOOM_MAX = 6;

const clamp = (v: number, lo: number, hi: number): number => Math.max(lo, Math.min(hi, v));

// Keep the panned content from being dragged off-screen: the offset can move at
// most half the overflow (content beyond the viewport) in each direction, so a
// content edge never crosses past the matching viewport edge. When the content
// fits (no overflow) the offset is pinned to 0 → centred.
const clampPan = (offset: number, content: number, viewport: number): number => {
  const limit = Math.max(0, (content - viewport) / 2);
  return clamp(offset, -limit, limit);
};

type StepId = 'mask' | 'lineatur' | 'slant' | 'weg' | 'overview';
const STEPS: { id: StepId; label: string }[] = [
  { id: 'mask', label: 'Ausschluss' },
  { id: 'lineatur', label: 'Lineatur' },
  { id: 'slant', label: 'Schräge' },
  { id: 'weg', label: 'Weg' },
  { id: 'overview', label: 'Übersicht' },
];

function bboxInFromOut(b: BboxOut): BboxIn {
  return {
    y0: b.y0,
    y1: b.y1,
    x0: b.x0,
    x1: b.x1,
    mask_strokes: b.mask_strokes,
    baseline_y: b.baseline_y,
    midband_y: b.midband_y,
    n_anchors: b.n_anchors,
    guides: b.guides,
    locked: b.locked,
  };
}

const summaryOf = (g: { glyph_key: string; glyph: string; position: string; variant: number; advance: number }): GlyphSummary => ({
  glyph_key: g.glyph_key,
  glyph: g.glyph,
  position: g.position,
  variant: g.variant,
  advance: g.advance,
  has_data: true,
});

// All three position keys for the letter behind `glyphKey` (deduped, via the
// override-aware glyphKeyFor so s / ſ map correctly). Used by the fan-out.
function siblingKeys(glyphKey: string): string[] {
  const letter = LETTER_BY_KEY[glyphKey];
  if (!letter) return [glyphKey];
  return Array.from(new Set(POSITIONS.map((p) => glyphKeyFor(letter, p))));
}

// Pick a starting zoom so the letter already fills the frame on the first step
// instead of sitting small in the middle. A fresh bbox seeds its x-height band
// at ~35 % of the box height, so a letter without ascender/descender (e.g. `a`)
// only paints that middle slice — fit-to-view then shows mostly empty margin.
// We zoom roughly in inverse proportion to that band fraction, gently capped so
// tall letters (ascender + descender) are never clipped hard; Anpassen (fit)
// and the slider stay one tap away.
function defaultZoomFor(b: BboxOut | null): number {
  if (!b) return 1;
  const h = b.y1 - b.y0;
  if (h <= 0) return 1;
  const bandFraction = Math.max(0.18, (b.baseline_y - b.midband_y) / h);
  return clamp(0.62 / bandFraction, 1, 1.6);
}

export function SetupWizard({ glyphKey, open, onClose }: { glyphKey: string; open: boolean; onClose: () => void }) {
  const { source, bboxesByKey, glyphsByKey, cropCacheBust, upsertBbox, markGlyphTraced, refreshCrop, openDiagnose } = useAdmin();
  const bbox = bboxesByKey[glyphKey] ?? null;
  // Always-current bbox, read (not subscribed) by the open/reset effect so it can
  // seed the default zoom without re-running on every mask/lineature edit.
  const bboxRef = useRef(bbox);
  bboxRef.current = bbox;
  const known = knownGlyph(glyphKey);
  const hasCanonical = glyphsByKey[glyphKey]?.has_data === true;

  const [step, setStep] = useState(0);
  const stepId = STEPS[step].id;

  const hostRef = useRef<HTMLDivElement | null>(null);
  const [hostSize, setHostSize] = useState({ w: 0, h: 0 });

  // Per-step interaction state.
  const [pathPts, setPathPts] = useState<StrokePoint[]>([]);
  const [drawing, setDrawing] = useState(false);
  const [maskRadius, setMaskRadius] = useState(8);
  const [maskDraft, setMaskDraft] = useState<Array<[number, number]> | null>(null);
  const [calibDrag, setCalibDrag] = useState<{ field: 'baseline_y' | 'midband_y'; curY: number } | null>(null);
  // Which slant line is being dragged (index into slant_xs) and its live x.
  const [slantDrag, setSlantDrag] = useState<{ index: number; curX: number } | null>(null);
  // Canvas zoom/pan, shared by every step. `userZoom` multiplies the fit scale;
  // pan{X,Y} translate the magnified crop in CSS px; `panning` is the Schwenken
  // toggle (drags pan instead of draw); `panDrag` holds a live pan gesture.
  const [userZoom, setUserZoom] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const [panning, setPanning] = useState(false);
  const [panDrag, setPanDrag] = useState<{ sx: number; sy: number; px: number; py: number } | null>(null);
  const [applyAll, setApplyAll] = useState(true);
  const [busy, setBusy] = useState(false);
  const [snack, setSnack] = useState<string | null>(null);

  useLayoutEffect(() => {
    const el = hostRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setHostSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el);
    setHostSize({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, [open, step]);

  // Mounted once and reused for every glyph: when a different glyph opens (or the
  // dialog reopens), drop transient state so one glyph's draft never leaks onto
  // the next.
  useEffect(() => {
    setStep(0);
    setPathPts([]);
    setDrawing(false);
    setMaskDraft(null);
    setCalibDrag(null);
    setSlantDrag(null);
    // Fresh letter → re-centre and seed the auto-zoom from its bbox.
    setPanX(0);
    setPanY(0);
    setPanning(false);
    setPanDrag(null);
    setUserZoom(defaultZoomFor(bboxRef.current));
  }, [glyphKey, open]);

  const cropW = bbox ? bbox.x1 - bbox.x0 : 0;
  const cropH = bbox ? bbox.y1 - bbox.y0 : 0;
  // baseScale fits the whole bbox into the host; `scale` is that times the user
  // zoom and is what every coordinate transform below uses (so nothing else has
  // to know about zoom). displayW/H are the on-screen crop size at that scale.
  const baseScale = useMemo(() => {
    if (!cropW || !cropH || !hostSize.w || !hostSize.h) return 1;
    const padding = 24;
    return Math.max(0.4, Math.min((hostSize.w - padding) / cropW, (hostSize.h - padding) / cropH));
  }, [cropW, cropH, hostSize]);
  const scale = baseScale * userZoom;
  const displayW = cropW * scale;
  const displayH = cropH * scale;

  // Set the zoom and re-clamp the pan to the new crop size (so zooming out never
  // leaves the crop stranded off-centre). Centred on the frame, not the cursor.
  const applyZoom = useCallback(
    (next: number) => {
      const z = clamp(next, ZOOM_MIN, ZOOM_MAX);
      setUserZoom(z);
      setPanX((p) => clampPan(p, cropW * baseScale * z, hostSize.w));
      setPanY((p) => clampPan(p, cropH * baseScale * z, hostSize.h));
    },
    [cropW, cropH, baseScale, hostSize],
  );
  const zoomBy = useCallback((factor: number) => applyZoom(userZoom * factor), [applyZoom, userZoom]);
  const fitZoom = useCallback(() => {
    setUserZoom(1);
    setPanX(0);
    setPanY(0);
  }, []);

  // Mouse-wheel zoom, anchored on the cursor so the point under it stays put
  // (mirrors the chart). Needs a non-passive listener to preventDefault the page
  // scroll, so it's attached imperatively rather than via onWheel.
  useEffect(() => {
    const el = hostRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const nz = clamp(userZoom * (e.deltaY < 0 ? 1.15 : 1 / 1.15), ZOOM_MIN, ZOOM_MAX);
      if (nz === userZoom) return;
      const rect = el.getBoundingClientRect();
      const cx = e.clientX - rect.left;
      const cy = e.clientY - rect.top;
      // Fraction of the current crop under the cursor (crop is centred + panned).
      const leftX = rect.width / 2 - displayW / 2 + panX;
      const topY = rect.height / 2 - displayH / 2 + panY;
      const fracX = displayW > 0 ? clamp((cx - leftX) / displayW, 0, 1) : 0.5;
      const fracY = displayH > 0 ? clamp((cy - topY) / displayH, 0, 1) : 0.5;
      const dW = cropW * baseScale * nz;
      const dH = cropH * baseScale * nz;
      setUserZoom(nz);
      setPanX(clampPan(cx - rect.width / 2 + dW / 2 - fracX * dW, dW, rect.width));
      setPanY(clampPan(cy - rect.height / 2 + dH / 2 - fracY * dH, dH, rect.height));
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [userZoom, panX, panY, baseScale, cropW, cropH, displayW, displayH]);

  const guideVals = useMemo(() => {
    const g: GuideConfig = bbox?.guides ?? {};
    const center = bbox ? (bbox.x0 + bbox.x1) / 2 : 0;
    // slant_xs is the source of truth; fall back to the legacy single slant_x so
    // glyphs authored before multi-line still show their one line.
    const xs = g.slant_xs && g.slant_xs.length > 0 ? g.slant_xs : [g.slant_x ?? center];
    return {
      slantDeg: g.slant_deg ?? (source ? source.slant_deg : 65),
      slantXs: xs,
      showAscender: g.show_ascender ?? true,
      showDescender: g.show_descender ?? true,
      entryCoupling: g.entry_coupling ?? 'baseline',
      exitCoupling: g.exit_coupling ?? 'baseline',
    };
  }, [bbox, source]);

  const cssToChart = useCallback(
    (clientX: number, clientY: number, host: Element | null) => {
      if (!host || !bbox) return { x: 0, y: 0 };
      const r = host.getBoundingClientRect();
      return { x: bbox.x0 + (clientX - r.left) / scale, y: bbox.y0 + (clientY - r.top) / scale };
    },
    [bbox, scale],
  );

  const updateBboxField = useCallback(
    async (patch: Partial<BboxIn>) => {
      if (!bbox) return;
      try {
        const saved = await putBbox(glyphKey, { ...bboxInFromOut(bbox), ...patch });
        upsertBbox(glyphKey, saved);
      } catch (err) {
        setSnack(`Speichern fehlgeschlagen: ${err}`);
      }
    },
    [bbox, glyphKey, upsertBbox],
  );

  const updateGuides = useCallback(
    (patch: Partial<GuideConfig>) => {
      const merged: GuideConfig = {
        slant_deg: guideVals.slantDeg,
        slant_xs: guideVals.slantXs,
        show_ascender: guideVals.showAscender,
        show_descender: guideVals.showDescender,
        entry_coupling: guideVals.entryCoupling,
        exit_coupling: guideVals.exitCoupling,
        ...patch,
      };
      // Derive the legacy single-line fallback from the RESOLVED slant_xs (after
      // the patch), so slant_x always mirrors slant_xs[0] even when a line is
      // dragged or the first line is removed.
      const next: GuideConfig = { ...merged, slant_x: merged.slant_xs?.[0] ?? null };
      return updateBboxField({ guides: next });
    },
    [guideVals, updateBboxField],
  );

  // ------------------------------------------------------------- pointer routing
  const onSvgPointerDown = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (!bbox) return;
      if (panning) {
        e.preventDefault();
        setPanDrag({ sx: e.clientX, sy: e.clientY, px: panX, py: panY });
        e.currentTarget.setPointerCapture(e.pointerId);
        return;
      }
      const { x, y } = cssToChart(e.clientX, e.clientY, e.currentTarget);
      if (stepId === 'mask') {
        e.preventDefault();
        setMaskDraft([[x, y]]);
        e.currentTarget.setPointerCapture(e.pointerId);
      } else if (stepId === 'weg') {
        if (e.pointerType !== 'pen' && e.pointerType !== 'mouse' && e.pointerType !== 'touch') return;
        e.preventDefault();
        setDrawing(true);
        setPathPts((prev) =>
          prev.length > 0
            ? [...prev, { x, y, pressure: e.pressure || null, t: performance.now() }]
            : [{ x, y, pressure: e.pressure || null, t: 0 }],
        );
        e.currentTarget.setPointerCapture(e.pointerId);
      }
    },
    [bbox, stepId, cssToChart, panning, panX, panY],
  );

  const onSvgPointerMove = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (!bbox) return;
      if (panDrag) {
        setPanX(clampPan(panDrag.px + (e.clientX - panDrag.sx), displayW, hostSize.w));
        setPanY(clampPan(panDrag.py + (e.clientY - panDrag.sy), displayH, hostSize.h));
        return;
      }
      const { x, y } = cssToChart(e.clientX, e.clientY, e.currentTarget);
      if (calibDrag) {
        setCalibDrag({ ...calibDrag, curY: Math.round(y) });
        return;
      }
      if (slantDrag) {
        setSlantDrag({ ...slantDrag, curX: x });
        return;
      }
      if (stepId === 'mask' && maskDraft) {
        const last = maskDraft[maskDraft.length - 1];
        if (last && (x - last[0]) ** 2 + (y - last[1]) ** 2 < 1) return;
        setMaskDraft([...maskDraft, [x, y]]);
        return;
      }
      if (stepId === 'weg' && drawing) {
        setPathPts((prev) => {
          const last = prev[prev.length - 1];
          if (last && (x - last.x) ** 2 + (y - last.y) ** 2 < 0.36) return prev;
          return [...prev, { x, y, pressure: e.pressure || null, t: performance.now() }];
        });
      }
    },
    [bbox, calibDrag, slantDrag, stepId, maskDraft, drawing, cssToChart, panDrag, displayW, displayH, hostSize],
  );

  const onSvgPointerUp = useCallback(async () => {
    if (panDrag) {
      setPanDrag(null);
      return;
    }
    if (calibDrag) {
      const { field, curY } = calibDrag;
      setCalibDrag(null);
      // Keep the baseline below the midband (server enforces baseline_y > midband_y).
      if (bbox) {
        const other = field === 'baseline_y' ? bbox.midband_y : bbox.baseline_y;
        const ok = field === 'baseline_y' ? curY > other : curY < other;
        if (ok) await updateBboxField({ [field]: curY });
        else setSnack('Grundlinie muss unter der Mittellinie liegen.');
      }
      return;
    }
    if (slantDrag) {
      const { index, curX } = slantDrag;
      setSlantDrag(null);
      const xs = guideVals.slantXs.slice();
      xs[index] = Math.round(curX);
      await updateGuides({ slant_xs: xs });
      return;
    }
    if (stepId === 'mask' && maskDraft) {
      const stroke: MaskStroke = { points: maskDraft, radius: maskRadius };
      setMaskDraft(null);
      if (bbox) {
        await updateBboxField({ mask_strokes: [...bbox.mask_strokes, stroke] });
        refreshCrop();
      }
      return;
    }
    if (stepId === 'weg') setDrawing(false);
  }, [panDrag, calibDrag, slantDrag, stepId, maskDraft, maskRadius, bbox, guideVals, updateBboxField, updateGuides, refreshCrop]);

  const undoMask = useCallback(async () => {
    if (!bbox || bbox.mask_strokes.length === 0) return;
    await updateBboxField({ mask_strokes: bbox.mask_strokes.slice(0, -1) });
    refreshCrop();
  }, [bbox, updateBboxField, refreshCrop]);

  const addSlantLine = useCallback(() => {
    const xs = guideVals.slantXs;
    const last = xs.length ? xs[xs.length - 1] : bbox ? (bbox.x0 + bbox.x1) / 2 : 0;
    void updateGuides({ slant_xs: [...xs, Math.round(last + 24)] });
  }, [guideVals, bbox, updateGuides]);

  const removeSlantLine = useCallback(
    (i: number) => {
      if (guideVals.slantXs.length <= 1) return;
      void updateGuides({ slant_xs: guideVals.slantXs.filter((_, k) => k !== i) });
    },
    [guideVals, updateGuides],
  );

  const saveTrace = useCallback(async () => {
    if (pathPts.length < 2 || !known || !bbox) return;
    setBusy(true);
    try {
      const g = await postTrace(glyphKey, {
        glyph: known.glyph,
        position: known.position,
        raw_path: pathPts,
        n_anchors: bbox.n_anchors,
      });
      markGlyphTraced(glyphKey, summaryOf(g));
      setSnack(`Weg gespeichert · ${g.anchors.length} Anker`);
      setPathPts([]);
    } catch (err) {
      setSnack(String(err));
    } finally {
      setBusy(false);
    }
  }, [pathPts, known, bbox, glyphKey, markGlyphTraced]);

  // Re-sample the stored canonical to the current n_anchors without re-drawing.
  const resample = useCallback(async () => {
    if (!bbox || !hasCanonical) return;
    setBusy(true);
    try {
      const g = await postResample(glyphKey, bbox.n_anchors);
      markGlyphTraced(glyphKey, summaryOf(g));
      setSnack(`neu abgetastet · ${g.anchors.length} Anker`);
    } catch (err) {
      setSnack(String(err));
    } finally {
      setBusy(false);
    }
  }, [bbox, hasCanonical, glyphKey, markGlyphTraced]);

  // Approve → fan out to all positions (optional) and lock.
  const finish = useCallback(async () => {
    if (!bbox || !known) return;
    setBusy(true);
    try {
      if (applyAll) {
        const tpl = await getGlyph(glyphKey); // carries the raw_path to copy
        for (const k of siblingKeys(glyphKey)) {
          if (k === glyphKey) continue;
          const kg = knownGlyph(k);
          if (!kg) continue;
          // Create the bbox UNLOCKED first (the trace precondition needs a bbox),
          // post the trace, and only THEN lock — so a mid-loop failure never
          // leaves a locked-but-empty sibling that can't be reopened in the wizard.
          await putBbox(k, { ...bboxInFromOut(bbox), locked: false });
          const g = await postTrace(k, {
            glyph: kg.glyph,
            position: kg.position,
            raw_path: tpl.raw_path,
            n_anchors: bbox.n_anchors,
          });
          markGlyphTraced(k, summaryOf(g));
          const savedB = await putBbox(k, { ...bboxInFromOut(bbox), locked: true });
          upsertBbox(k, savedB);
        }
      }
      const saved = await putBbox(glyphKey, { ...bboxInFromOut(bbox), locked: true });
      upsertBbox(glyphKey, saved);
      onClose();
    } catch (err) {
      setSnack(`Abschließen fehlgeschlagen: ${err}`);
    } finally {
      setBusy(false);
    }
  }, [bbox, known, applyAll, glyphKey, upsertBbox, markGlyphTraced, onClose]);

  if (!source || !bbox || !known) return null;

  // ------------------------------------------------------------- geometry (css)
  const baselineCss = (bbox.baseline_y - bbox.y0) * scale;
  const midbandCss = (bbox.midband_y - bbox.y0) * scale;
  const xHeightPx = bbox.baseline_y - bbox.midband_y;
  const [aR, xR, dR] = source.style_ratio;
  const ascenderCss = (bbox.midband_y - (aR / xR) * xHeightPx - bbox.y0) * scale;
  const descenderCss = (bbox.baseline_y + (dR / xR) * xHeightPx - bbox.y0) * scale;
  const dragCss = calibDrag ? (calibDrag.curY - bbox.y0) * scale : null;

  const tanSlant = Math.tan(((90 - guideVals.slantDeg) * Math.PI) / 180);
  const slantLineCss = (xBase: number) => ({
    x1: (xBase + tanSlant * (bbox.baseline_y - bbox.y0) - bbox.x0) * scale,
    y1: 0,
    x2: (xBase + tanSlant * (bbox.baseline_y - bbox.y1) - bbox.x0) * scale,
    y2: displayH,
  });
  // Live positions: the dragged line follows the pointer; the rest stay put.
  const slantXsLive = slantDrag
    ? guideVals.slantXs.map((x, i) => (i === slantDrag.index ? slantDrag.curX : x))
    : guideVals.slantXs;

  const toLocal = (pts: Array<[number, number]>) =>
    pts.map(([x, y]) => `${(x - bbox.x0) * scale},${(y - bbox.y0) * scale}`).join(' ');

  const canvas = (
    <Box ref={hostRef} sx={{ flex: 1, minHeight: 0, position: 'relative', bgcolor: '#111', overflow: 'hidden' }}>
      {displayW > 0 && (
        <Box
          sx={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            width: displayW,
            height: displayH,
            transform: `translate(-50%, -50%) translate(${panX}px, ${panY}px)`,
          }}
        >
          <img
            src={cropUrl(glyphKey, cropCacheBust)}
            alt={known.label}
            width={displayW}
            height={displayH}
            draggable={false}
            style={{ display: 'block', imageRendering: 'pixelated', pointerEvents: 'none' }}
          />
          <svg
            width={displayW}
            height={displayH}
            style={{
              position: 'absolute',
              inset: 0,
              touchAction: 'none',
              cursor: panning ? (panDrag ? 'grabbing' : 'grab') : stepId === 'mask' || stepId === 'weg' ? 'crosshair' : 'default',
            }}
            onPointerDown={onSvgPointerDown}
            onPointerMove={onSvgPointerMove}
            onPointerUp={onSvgPointerUp}
            onPointerCancel={() => {
              setPanDrag(null);
              setCalibDrag(null);
              setSlantDrag(null);
              setMaskDraft(null);
              setDrawing(false);
            }}
          >
            {/* Lineature guides — read-only except on their own step */}
            {guideVals.showAscender && ascenderCss >= 0 && ascenderCss <= displayH && (
              <line x1={0} y1={ascenderCss} x2={displayW} y2={ascenderCss} stroke="#888" strokeWidth={1} strokeDasharray="2 4" opacity={0.6} />
            )}
            {guideVals.showDescender && descenderCss >= 0 && descenderCss <= displayH && (
              <line x1={0} y1={descenderCss} x2={displayW} y2={descenderCss} stroke="#888" strokeWidth={1} strokeDasharray="2 4" opacity={0.6} />
            )}
            <g>
              {stepId === 'lineatur' && (
                <line
                  x1={0}
                  y1={baselineCss}
                  x2={displayW}
                  y2={baselineCss}
                  stroke="transparent"
                  strokeWidth={22}
                  style={{ cursor: 'ns-resize', pointerEvents: 'stroke' }}
                  onPointerDown={(e) => {
                    if (panning) return; // let the drag bubble to the SVG → pan
                    e.stopPropagation();
                    setCalibDrag({ field: 'baseline_y', curY: bbox.baseline_y });
                    e.currentTarget.ownerSVGElement?.setPointerCapture(e.pointerId);
                  }}
                />
              )}
              <line x1={0} y1={baselineCss} x2={displayW} y2={baselineCss} stroke="#ff5060" strokeWidth={1.5} strokeDasharray="6 4" style={{ pointerEvents: 'none' }} />
            </g>
            <g>
              {stepId === 'lineatur' && (
                <line
                  x1={0}
                  y1={midbandCss}
                  x2={displayW}
                  y2={midbandCss}
                  stroke="transparent"
                  strokeWidth={22}
                  style={{ cursor: 'ns-resize', pointerEvents: 'stroke' }}
                  onPointerDown={(e) => {
                    if (panning) return; // let the drag bubble to the SVG → pan
                    e.stopPropagation();
                    setCalibDrag({ field: 'midband_y', curY: bbox.midband_y });
                    e.currentTarget.ownerSVGElement?.setPointerCapture(e.pointerId);
                  }}
                />
              )}
              <line x1={0} y1={midbandCss} x2={displayW} y2={midbandCss} stroke="#c060ff" strokeWidth={1.5} strokeDasharray="3 3" style={{ pointerEvents: 'none' }} />
            </g>
            {dragCss != null && (
              <line x1={0} y1={dragCss} x2={displayW} y2={dragCss} stroke={calibDrag?.field === 'baseline_y' ? '#ff5060' : '#c060ff'} strokeWidth={2} opacity={0.6} style={{ pointerEvents: 'none' }} />
            )}

            {/* Slant guide(s) — one or more parallel lines, each draggable on the slant step */}
            {(stepId === 'slant' || stepId === 'weg') &&
              slantXsLive.map((xb, i) => {
                const ln = slantLineCss(xb);
                const dragging = slantDrag?.index === i;
                return (
                  <line
                    key={i}
                    x1={ln.x1}
                    y1={ln.y1}
                    x2={ln.x2}
                    y2={ln.y2}
                    stroke={SLANT_COLOR}
                    strokeWidth={dragging ? 2 : 1.2}
                    strokeDasharray="5 4"
                    opacity={dragging ? 0.6 : 0.85}
                    style={{ pointerEvents: 'none' }}
                  />
                );
              })}
            {stepId === 'slant' &&
              slantXsLive.map((xb, i) => (
                <circle
                  key={i}
                  cx={(xb - bbox.x0) * scale}
                  cy={baselineCss}
                  r={8}
                  fill={SLANT_COLOR}
                  stroke="#0a2a14"
                  strokeWidth={1}
                  style={{ cursor: 'ew-resize' }}
                  onPointerDown={(e) => {
                    if (panning) return; // let the drag bubble to the SVG → pan
                    e.stopPropagation();
                    setSlantDrag({ index: i, curX: guideVals.slantXs[i] });
                    e.currentTarget.ownerSVGElement?.setPointerCapture(e.pointerId);
                  }}
                />
              ))}

            {/* Eraser strokes (committed + in-progress) */}
            {bbox.mask_strokes.map((m, i) => (
              <polyline key={i} points={toLocal(m.points)} fill="none" stroke="#ff6b35" strokeOpacity={0.55} strokeWidth={Math.max(1, m.radius * 2 * scale)} strokeLinecap="round" strokeLinejoin="round" style={{ pointerEvents: 'none' }} />
            ))}
            {maskDraft && <polyline points={toLocal(maskDraft)} fill="none" stroke="#ff6b35" strokeOpacity={0.8} strokeWidth={Math.max(1, maskRadius * 2 * scale)} strokeLinecap="round" strokeLinejoin="round" style={{ pointerEvents: 'none' }} />}

            {/* Trace draft */}
            {pathPts.length > 1 && <polyline points={pathPts.map((p) => `${(p.x - bbox.x0) * scale},${(p.y - bbox.y0) * scale}`).join(' ')} fill="none" stroke="#00d2ff" strokeWidth={2} style={{ pointerEvents: 'none' }} />}
            {pathPts.length > 0 && <circle cx={(pathPts[0].x - bbox.x0) * scale} cy={(pathPts[0].y - bbox.y0) * scale} r={4} fill="#fff" stroke="#00d2ff" style={{ pointerEvents: 'none' }} />}
          </svg>
        </Box>
      )}
      {/* Floating zoom controls — Schwenken toggle · −/Slider/+ · Anpassen (fit) */}
      <Box
        sx={{
          position: 'absolute',
          top: 8,
          right: 8,
          display: 'flex',
          alignItems: 'center',
          gap: 0.25,
          px: 0.5,
          py: 0.25,
          borderRadius: 1,
          bgcolor: 'rgba(20, 20, 20, 0.78)',
        }}
      >
        <Tooltip title="Schwenken — Ausschnitt verschieben">
          <IconButton size="small" onClick={() => setPanning((p) => !p)} sx={{ color: panning ? SLANT_COLOR : '#bbb' }}>
            <OpenWithIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <IconButton size="small" onClick={() => zoomBy(1 / 1.3)} sx={{ color: '#bbb' }} aria-label="herauszoomen">
          <RemoveIcon fontSize="small" />
        </IconButton>
        <Slider
          size="small"
          sx={{ width: 84, color: '#ccc' }}
          min={ZOOM_MIN}
          max={ZOOM_MAX}
          step={0.05}
          value={userZoom}
          onChange={(_e, v) => typeof v === 'number' && applyZoom(v)}
        />
        <IconButton size="small" onClick={() => zoomBy(1.3)} sx={{ color: '#bbb' }} aria-label="hineinzoomen">
          <AddIcon fontSize="small" />
        </IconButton>
        <Tooltip title="Anpassen — ganzen Ausschnitt zeigen">
          <IconButton size="small" onClick={fitZoom} sx={{ color: '#bbb' }}>
            <CenterFocusStrongIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Typography variant="caption" sx={{ color: '#bbb', minWidth: 32, textAlign: 'right' }}>
          {Math.round(userZoom * 100)}%
        </Typography>
      </Box>
    </Box>
  );

  // ------------------------------------------------------------- step panels
  const panel = (() => {
    switch (stepId) {
      case 'mask':
        return (
          <Stack spacing={1.5}>
            <Typography variant="subtitle2">Schritt 1 · Ausschluss (Radierer)</Typography>
            <Typography variant="body2" color="text.secondary">
              Auf den Lehrtafeln stehen die Buchstaben dicht beieinander — ragt Tinte vom Nachbarn
              in diesen Ausschnitt, verfälscht sie später Skelett und Anker. Mit dem Pinsel direkt
              über die störenden Stellen malen; das Übermalte wird vor der Skelettberechnung entfernt.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Nur fremde Tinte ausschließen — vom eigentlichen Buchstaben nichts wegradieren.
            </Typography>
            <Box>
              <Typography variant="caption">Pinselgröße: {maskRadius}px</Typography>
              <Slider size="small" min={2} max={30} value={maskRadius} onChange={(_e, v) => typeof v === 'number' && setMaskRadius(v)} />
            </Box>
            <Button size="small" startIcon={<UndoIcon />} disabled={bbox.mask_strokes.length === 0} onClick={undoMask}>
              Letzten Strich zurück ({bbox.mask_strokes.length})
            </Button>
          </Stack>
        );
      case 'lineatur':
        return (
          <Stack spacing={1.5}>
            <Typography variant="subtitle2">Schritt 2 · Lineatur</Typography>
            <Typography variant="body2" color="text.secondary">
              Die <b style={{ color: '#ff5060' }}>Grundlinie</b> (auf der die Mittellänge aufsitzt)
              und die <b style={{ color: '#c060ff' }}>Mittellinie</b> (Oberkante der Mittellänge)
              direkt im Bild an die richtige Höhe ziehen. <b>Oberlinie</b> und <b>Unterlinie</b> (grau)
              ergeben sich automatisch aus dem Stil-Verhältnis ({source.style_ratio.join(':')}).
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Diese vier Linien sind das Lineatur-System (Zonen: Oberlänge · Mittellänge · Unterlänge)
              und der Bezug für alle weiteren Maße.
            </Typography>
            <Stack direction="row" spacing={1}>
              <FormControlLabel
                control={<Checkbox size="small" checked={guideVals.showAscender} onChange={(e) => updateGuides({ show_ascender: e.target.checked })} />}
                label="Oberlinie"
                slotProps={{ typography: { variant: 'caption' } }}
              />
              <FormControlLabel
                control={<Checkbox size="small" checked={guideVals.showDescender} onChange={(e) => updateGuides({ show_descender: e.target.checked })} />}
                label="Unterlinie"
                slotProps={{ typography: { variant: 'caption' } }}
              />
            </Stack>
            <Typography variant="caption" color="text.secondary">
              Grundlinie {bbox.baseline_y} · Mittellinie {bbox.midband_y} · Mittellänge (x-Höhe) {xHeightPx}px
            </Typography>
          </Stack>
        );
      case 'slant':
        return (
          <Stack spacing={1.5}>
            <Typography variant="subtitle2">Schritt 3 · Schräge</Typography>
            <Typography variant="body2" color="text.secondary">
              Die Schräge ist die Neigung der Hauptstriche, gemessen von der Grundlinie aus
              (≈65° = typisches Kurrent, 90° = senkrecht). Den grünen Punkt ziehen, um eine Linie
              über den Buchstaben zu legen.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Für die meisten Buchstaben reicht <b>eine</b> Linie. Bei mehreren gleich geneigten
              Hauptstrichen (m · n · u) kannst du weitere Linien hinzufügen und jede einzeln
              platzieren — alle teilen denselben Winkel.
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TextField label="Schräge" type="number" size="small" value={Math.round(guideVals.slantDeg)} onChange={(e) => updateGuides({ slant_deg: Number(e.target.value) })} slotProps={{ input: { sx: { color: SLANT_COLOR, fontFamily: 'monospace' }, endAdornment: '°' } }} sx={{ flex: 1 }} />
              <IconButton size="small" onClick={() => updateGuides({ slant_deg: Math.round(guideVals.slantDeg) + 1 })} sx={{ color: SLANT_COLOR }}>
                <ArrowUpwardIcon fontSize="small" />
              </IconButton>
              <IconButton size="small" onClick={() => updateGuides({ slant_deg: Math.round(guideVals.slantDeg) - 1 })} sx={{ color: SLANT_COLOR }}>
                <ArrowDownwardIcon fontSize="small" />
              </IconButton>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="caption" color="text.secondary">
                Schräglinien ({guideVals.slantXs.length})
              </Typography>
              <Button size="small" startIcon={<AddIcon />} onClick={addSlantLine}>
                Linie hinzufügen
              </Button>
            </Box>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {guideVals.slantXs.map((_, i) => (
                <Chip
                  key={i}
                  size="small"
                  label={`Linie ${i + 1}`}
                  onDelete={guideVals.slantXs.length > 1 ? () => removeSlantLine(i) : undefined}
                  sx={{ borderColor: SLANT_COLOR }}
                  variant="outlined"
                />
              ))}
            </Box>
            <Typography variant="caption" color="text.secondary">
              Den grünen Punkt einer Linie ziehen, um sie zu verschieben; das ✕ am Chip entfernt sie.
            </Typography>
          </Stack>
        );
      case 'weg':
        return (
          <Stack spacing={1.5}>
            <Typography variant="subtitle2">Schritt 4 · Weg (Ductus)</Typography>
            <Typography variant="body2" color="text.secondary">
              Den Buchstaben in Schreibrichtung mit dem Stift (S-Pen) oder der Maus nachziehen — das
              ist der Ductus, die eigentliche Vorlage über der Loth-Geometrie. Auf den weißen
              Startpunkt setzen, um einen unterbrochenen Strich fortzusetzen.
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button size="small" startIcon={<UndoIcon />} disabled={pathPts.length === 0} onClick={() => setPathPts([])}>
                Verwerfen
              </Button>
              <Button size="small" variant="contained" disabled={pathPts.length < 2 || busy} onClick={saveTrace}>
                Weg speichern
              </Button>
            </Stack>
            {hasCanonical && pathPts.length === 0 && <Alert severity="success" variant="outlined">Weg gespeichert. Weiter zur Übersicht.</Alert>}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TextField
                label="Anker (n_anchors)"
                type="number"
                size="small"
                value={bbox.n_anchors}
                onChange={(e) => updateBboxField({ n_anchors: Math.max(4, Number(e.target.value)) })}
                sx={{ flex: 1 }}
              />
              <Button size="small" variant="outlined" startIcon={<RefreshIcon />} disabled={!hasCanonical || busy} onClick={resample}>
                Neu abtasten
              </Button>
            </Box>
            <Typography variant="caption" color="text.secondary">
              n_anchors = Zahl der Stützpunkte, auf die der Pen-Pfad abgetastet wird. Der Originalpfad
              bleibt erhalten, also jederzeit ohne Neuzeichnen neu abtastbar.
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField select size="small" label="Kopplung Anfang" value={guideVals.entryCoupling} onChange={(e) => updateGuides({ entry_coupling: e.target.value as CouplingHeight })} sx={{ flex: 1 }} slotProps={{ select: { native: true } }}>
                {COUPLING_OPTIONS.map((c) => (
                  <option key={c} value={c}>
                    {couplingLabel(c)}
                  </option>
                ))}
              </TextField>
              <TextField select size="small" label="Kopplung Ende" value={guideVals.exitCoupling} onChange={(e) => updateGuides({ exit_coupling: e.target.value as CouplingHeight })} sx={{ flex: 1 }} slotProps={{ select: { native: true } }}>
                {COUPLING_OPTIONS.map((c) => (
                  <option key={c} value={c}>
                    {couplingLabel(c)}
                  </option>
                ))}
              </TextField>
            </Box>
            <Typography variant="caption" color="text.secondary">
              Höhe, auf der ein Nachbarbuchstabe ansetzt (Anfang) bzw. weiterläuft (Ende). Greift bei
              bestehendem Canonical sofort beim nächsten Speichern.
            </Typography>
          </Stack>
        );
      case 'overview':
        return (
          <Stack spacing={2} sx={{ maxWidth: 640 }}>
            <Typography variant="subtitle2">Schritt 5 · Übersicht & Freigabe</Typography>
            <Typography variant="body2" color="text.secondary">
              Alles geprüft? Mit der <b>Diagnose</b> kannst du das Ergebnis groß ansehen: der reine
              Crop, das Skelett mit Ankern und die kanonische Vorlage nebeneinander (plus den M4-Fit).
            </Typography>
            {hasCanonical ? (
              <Button variant="outlined" startIcon={<VisibilityIcon />} onClick={() => openDiagnose(glyphKey)} sx={{ alignSelf: 'flex-start' }}>
                Diagnose öffnen
              </Button>
            ) : (
              <Alert severity="warning">Noch kein Weg gezeichnet — Schritt „Weg" zuerst.</Alert>
            )}
            <FormControlLabel control={<Checkbox checked={applyAll} onChange={(e) => setApplyAll(e.target.checked)} />} label="Gilt für alle Positionen (Anfang · Mitte · Ende)" />
            <Typography variant="caption" color="text.secondary">
              Übernimmt dieselbe Form für alle drei Positionen — die Anschlussstriche werden je Position
              aus Anfang/Ende erzeugt. Mit „Abschließen & sperren" wird der Glyph gesperrt (🔒) und ist
              erst nach Entsperren wieder änderbar.
            </Typography>
          </Stack>
        );
    }
  })();

  const canAdvance = stepId !== 'weg' || hasCanonical;

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="lg" slotProps={{ paper: { sx: { height: '92vh' } } }}>
      <Box sx={{ px: 2, pt: 2 }}>
        <Typography variant="h6">Einrichten · {known.label}</Typography>
        <Stepper nonLinear activeStep={step} sx={{ mt: 1 }}>
          {STEPS.map((s, i) => (
            <Step key={s.id} completed={false}>
              <StepButton color="inherit" onClick={() => setStep(i)}>
                {s.label}
              </StepButton>
            </Step>
          ))}
        </Stepper>
      </Box>
      <Box sx={{ display: 'flex', flex: 1, minHeight: 0, gap: 2, p: 2 }}>
        {stepId === 'overview' ? (
          <Box sx={{ flex: 1, overflowY: 'auto' }}>{panel}</Box>
        ) : (
          <>
            {canvas}
            <Box sx={{ width: 340, flexShrink: 0, overflowY: 'auto' }}>{panel}</Box>
          </>
        )}
      </Box>
      {snack && (
        <Alert severity="info" onClose={() => setSnack(null)} sx={{ mx: 2 }}>
          {snack}
        </Alert>
      )}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Button startIcon={<ArrowBackIcon />} disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>
          Zurück
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={onClose}>Schließen</Button>
          {step < STEPS.length - 1 ? (
            <Button variant="contained" endIcon={<ArrowForwardIcon />} disabled={!canAdvance} onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}>
              Weiter
            </Button>
          ) : (
            <Button variant="contained" color="success" startIcon={<LockIcon />} disabled={!hasCanonical || busy} onClick={finish}>
              Abschließen & sperren
            </Button>
          )}
        </Box>
      </Box>
    </Dialog>
  );
}
