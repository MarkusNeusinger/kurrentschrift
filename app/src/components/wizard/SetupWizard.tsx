// SetupWizard — the step-by-step Einrichtungs-Wizard for authoring a canonical
// from a rough bbox already drawn on the chart. Steps (registration-style, with
// Back/Next and free jumping to earlier steps):
//   1. Ausschluss  — freehand eraser (Radierer): paint over neighbouring ink so
//                    it can't pollute the skeleton. Strokes → bbox.mask_strokes.
//   2. Lineatur    — drag Grundlinie / Mittellinie; Oberlinie/Unterlinie derive.
//   3. Schräge     — place + angle the slant guide.
//   4. Weg         — draw the ductus with the stylus; saves the canonical.
//   5. Übersicht   — review the 3-column diagnostic, optionally apply to all
//                    positions, then approve → lock (the bbox's `locked` flag).
//
// Changes live-commit (PUT bbox / POST trace) as in the editor; the lock IS the
// commit gesture, so there is no separate cancel-revert. The canvas mirrors the
// editor's coordinate math but is purpose-built per step. This is the wizard's
// own GlyphCanvas; EditorPage keeps its inline canvas as the advanced surface.

import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import LockIcon from '@mui/icons-material/Lock';
import UndoIcon from '@mui/icons-material/Undo';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Dialog,
  FormControlLabel,
  IconButton,
  Slider,
  Stack,
  Step,
  StepButton,
  Stepper,
  TextField,
  Typography,
} from '@mui/material';
import { useCallback, useLayoutEffect, useMemo, useRef, useState } from 'react';

import { cropUrl, getGlyph, postTrace, putBbox } from '../../api';
import { glyphKeyFor, knownGlyph, LETTER_BY_KEY, POSITIONS } from '../../constants';
import { couplingLabel } from '../../lib/labels';
import { useAdmin } from '../../state';
import type { BboxIn, BboxOut, CouplingHeight, GlyphSummary, GuideConfig, MaskStroke, StrokePoint } from '../../types';
import { DiagnosticView } from '../DiagnosticView';

const SLANT_COLOR = '#39d98a';
const COUPLING_OPTIONS: CouplingHeight[] = ['baseline', 'midband', 'ascender', 'descender'];

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

export function SetupWizard({ glyphKey, open, onClose }: { glyphKey: string; open: boolean; onClose: () => void }) {
  const { source, bboxesByKey, glyphsByKey, cropCacheBust, upsertBbox, markGlyphTraced, refreshCrop } = useAdmin();
  const bbox = bboxesByKey[glyphKey] ?? null;
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
  const [slantDrag, setSlantDrag] = useState<{ curX: number } | null>(null);
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

  const cropW = bbox ? bbox.x1 - bbox.x0 : 0;
  const cropH = bbox ? bbox.y1 - bbox.y0 : 0;
  const scale = useMemo(() => {
    if (!cropW || !cropH || !hostSize.w || !hostSize.h) return 1;
    const padding = 24;
    return Math.max(0.4, Math.min((hostSize.w - padding) / cropW, (hostSize.h - padding) / cropH));
  }, [cropW, cropH, hostSize]);
  const displayW = cropW * scale;
  const displayH = cropH * scale;

  const guideVals = useMemo(() => {
    const g: GuideConfig = bbox?.guides ?? {};
    return {
      slantDeg: g.slant_deg ?? (source ? source.slant_deg : 65),
      slantX: g.slant_x ?? (bbox ? (bbox.x0 + bbox.x1) / 2 : 0),
      slantCount: Math.max(1, g.slant_count ?? 1),
      slantSpacing: g.slant_spacing ?? 0,
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
      const next: GuideConfig = {
        slant_deg: guideVals.slantDeg,
        slant_x: guideVals.slantX,
        slant_count: guideVals.slantCount,
        slant_spacing: guideVals.slantSpacing,
        show_ascender: guideVals.showAscender,
        show_descender: guideVals.showDescender,
        entry_coupling: guideVals.entryCoupling,
        exit_coupling: guideVals.exitCoupling,
        ...patch,
      };
      return updateBboxField({ guides: next });
    },
    [guideVals, updateBboxField],
  );

  // ------------------------------------------------------------- pointer routing
  const onSvgPointerDown = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (!bbox) return;
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
    [bbox, stepId, cssToChart],
  );

  const onSvgPointerMove = useCallback(
    (e: React.PointerEvent<SVGSVGElement>) => {
      if (!bbox) return;
      const { x, y } = cssToChart(e.clientX, e.clientY, e.currentTarget);
      if (calibDrag) {
        setCalibDrag({ ...calibDrag, curY: Math.round(y) });
        return;
      }
      if (slantDrag) {
        setSlantDrag({ curX: x });
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
    [bbox, calibDrag, slantDrag, stepId, maskDraft, drawing, cssToChart],
  );

  const onSvgPointerUp = useCallback(async () => {
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
      const v = Math.round(slantDrag.curX);
      setSlantDrag(null);
      await updateGuides({ slant_x: v });
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
  }, [calibDrag, slantDrag, stepId, maskDraft, maskRadius, bbox, updateBboxField, updateGuides, refreshCrop]);

  const undoMask = useCallback(async () => {
    if (!bbox || bbox.mask_strokes.length === 0) return;
    await updateBboxField({ mask_strokes: bbox.mask_strokes.slice(0, -1) });
    refreshCrop();
  }, [bbox, updateBboxField, refreshCrop]);

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
          const savedB = await putBbox(k, { ...bboxInFromOut(bbox), locked: true });
          upsertBbox(k, savedB);
          const g = await postTrace(k, {
            glyph: kg.glyph,
            position: kg.position,
            raw_path: tpl.raw_path,
            n_anchors: bbox.n_anchors,
          });
          markGlyphTraced(k, summaryOf(g));
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
  const slantBases: number[] = [];
  for (let k = 0; k < guideVals.slantCount; k++) {
    slantBases.push(guideVals.slantX + (k - (guideVals.slantCount - 1) / 2) * guideVals.slantSpacing);
  }
  const slantHandleCss = (guideVals.slantX - bbox.x0) * scale;
  const slantDragLine = slantDrag ? slantLineCss(slantDrag.curX) : null;

  const toLocal = (pts: Array<[number, number]>) =>
    pts.map(([x, y]) => `${(x - bbox.x0) * scale},${(y - bbox.y0) * scale}`).join(' ');

  const canvas = (
    <Box ref={hostRef} sx={{ flex: 1, minHeight: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#111', overflow: 'hidden' }}>
      {displayW > 0 && (
        <Box sx={{ position: 'relative', width: displayW, height: displayH }}>
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
            style={{ position: 'absolute', inset: 0, touchAction: 'none', cursor: stepId === 'mask' || stepId === 'weg' ? 'crosshair' : 'default' }}
            onPointerDown={onSvgPointerDown}
            onPointerMove={onSvgPointerMove}
            onPointerUp={onSvgPointerUp}
            onPointerCancel={() => {
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
            <line
              x1={0}
              y1={baselineCss}
              x2={displayW}
              y2={baselineCss}
              stroke="#ff5060"
              strokeWidth={1.5}
              strokeDasharray="6 4"
              style={{ cursor: stepId === 'lineatur' ? 'ns-resize' : 'default', pointerEvents: stepId === 'lineatur' ? 'stroke' : 'none' }}
              onPointerDown={(e) => {
                if (stepId !== 'lineatur') return;
                e.stopPropagation();
                setCalibDrag({ field: 'baseline_y', curY: bbox.baseline_y });
                e.currentTarget.ownerSVGElement?.setPointerCapture(e.pointerId);
              }}
            />
            <line
              x1={0}
              y1={midbandCss}
              x2={displayW}
              y2={midbandCss}
              stroke="#c060ff"
              strokeWidth={1.5}
              strokeDasharray="3 3"
              style={{ cursor: stepId === 'lineatur' ? 'ns-resize' : 'default', pointerEvents: stepId === 'lineatur' ? 'stroke' : 'none' }}
              onPointerDown={(e) => {
                if (stepId !== 'lineatur') return;
                e.stopPropagation();
                setCalibDrag({ field: 'midband_y', curY: bbox.midband_y });
                e.currentTarget.ownerSVGElement?.setPointerCapture(e.pointerId);
              }}
            />
            {dragCss != null && (
              <line x1={0} y1={dragCss} x2={displayW} y2={dragCss} stroke={calibDrag?.field === 'baseline_y' ? '#ff5060' : '#c060ff'} strokeWidth={2} opacity={0.6} style={{ pointerEvents: 'none' }} />
            )}

            {/* Slant guide(s) */}
            {(stepId === 'slant' || stepId === 'weg' || stepId === 'overview') &&
              slantBases.map((xb, i) => {
                const ln = slantLineCss(xb);
                return <line key={i} x1={ln.x1} y1={ln.y1} x2={ln.x2} y2={ln.y2} stroke={SLANT_COLOR} strokeWidth={1.2} strokeDasharray="5 4" opacity={0.85} style={{ pointerEvents: 'none' }} />;
              })}
            {stepId === 'slant' && (
              <circle
                cx={slantHandleCss}
                cy={baselineCss}
                r={8}
                fill={SLANT_COLOR}
                stroke="#0a2a14"
                strokeWidth={1}
                style={{ cursor: 'ew-resize' }}
                onPointerDown={(e) => {
                  e.stopPropagation();
                  setSlantDrag({ curX: guideVals.slantX });
                  e.currentTarget.ownerSVGElement?.setPointerCapture(e.pointerId);
                }}
              />
            )}
            {slantDragLine && <line x1={slantDragLine.x1} y1={slantDragLine.y1} x2={slantDragLine.x2} y2={slantDragLine.y2} stroke={SLANT_COLOR} strokeWidth={2} opacity={0.6} style={{ pointerEvents: 'none' }} />}

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
    </Box>
  );

  // ------------------------------------------------------------- step panels
  const panel = (() => {
    switch (stepId) {
      case 'mask':
        return (
          <Stack spacing={1.5}>
            <Typography variant="body2" color="text.secondary">
              Überlappendes Nachbar-Ink wegradieren, damit es das Skelett nicht stört. Über die störenden Stellen malen.
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
            <Typography variant="body2" color="text.secondary">
              Die <b style={{ color: '#ff5060' }}>Grundlinie</b> und <b style={{ color: '#c060ff' }}>Mittellinie</b> ziehen. Oberlinie/Unterlinie (grau) ergeben sich aus dem Stil-Verhältnis.
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Grundlinie {bbox.baseline_y} · Mittellinie {bbox.midband_y} · Mittellänge (x-Höhe) {xHeightPx}px
            </Typography>
          </Stack>
        );
      case 'slant':
        return (
          <Stack spacing={1.5}>
            <Typography variant="body2" color="text.secondary">
              Den grünen Punkt ziehen, um die Schräge über den Buchstaben zu legen; Winkel von der Grundlinie aus.
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
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField label="Linien" type="number" size="small" value={guideVals.slantCount} onChange={(e) => updateGuides({ slant_count: Math.max(1, Math.round(Number(e.target.value))) })} sx={{ flex: 1 }} />
              <TextField label="Abstand px" type="number" size="small" value={guideVals.slantSpacing} disabled={guideVals.slantCount < 2} onChange={(e) => updateGuides({ slant_spacing: Math.max(0, Number(e.target.value)) })} sx={{ flex: 1 }} />
            </Box>
          </Stack>
        );
      case 'weg':
        return (
          <Stack spacing={1.5}>
            <Typography variant="body2" color="text.secondary">
              Den Buchstaben in Schreibrichtung mit dem Stift nachziehen. Auf den Startpunkt setzen, um fortzusetzen.
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
          </Stack>
        );
      case 'overview':
        return (
          <Stack spacing={1.5}>
            <Typography variant="body2" color="text.secondary">
              Alles auf einen Blick prüfen. Passt es, abschließen — dann wird der Glyph gesperrt (🔒) und ist erst nach Entsperren wieder änderbar.
            </Typography>
            {hasCanonical ? <DiagnosticView glyphKey={glyphKey} /> : <Alert severity="warning">Noch kein Weg gezeichnet — Schritt „Weg" zuerst.</Alert>}
            <FormControlLabel control={<Checkbox checked={applyAll} onChange={(e) => setApplyAll(e.target.checked)} />} label="Gilt für alle Positionen (Anfang · Mitte · Ende)" />
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
        {canvas}
        <Box sx={{ width: 320, flexShrink: 0, overflowY: 'auto' }}>{panel}</Box>
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
