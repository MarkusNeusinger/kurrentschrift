// Wizard-level state + server mutations for the Einrichtungs-Wizard: the step
// position, the captured Weg strokes, the resolved guide values and every
// live-commit against the API (PUT bbox / POST trace / resample / the final
// lock fan-out). The canvas hands finished gestures to the commit* callbacks;
// in-flight gesture state itself lives in WizardCanvas.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { getDiagnostic, getGlyph, postResample, postTrace, postTracePreview, putBbox } from '@/lib/api';
import { bboxInFromOut } from '@/lib/bbox';
import { isLetterSplit, knownGlyph, siblingKeys } from '@/domain/glyphs';
import { useAdmin } from '@/context/AdminContext';
import { de, fmt } from '@/locales';
import { flattenStrokes, savablePointCount } from './strokeUtils';
import { STEPS } from './wizardTypes';
import type { CalibField, GuideValues } from './wizardTypes';
import type { BboxIn, GlyphSummary, GuideConfig, MaskStroke, StrokePoint, TracePreviewOut } from '@/lib/api';

// The already-saved Weg, shown faintly on the Weg step for reference: the raw
// pen path (chart coordinates) and the resampled anchors (crop-local pixels).
export interface SavedTraceOverlay {
  rawPath: StrokePoint[];
  anchorsPx: Array<[number, number]>;
}

const summaryOf = (g: { glyph_key: string; glyph: string; position: string; variant: number; advance: number }): GlyphSummary => ({
  glyph_key: g.glyph_key,
  glyph: g.glyph,
  position: g.position,
  variant: g.variant,
  advance: g.advance,
  has_data: true,
});

export function useWizard(glyphKey: string, open: boolean, onClose: () => void) {
  const { sourceId, source, bboxesByKey, glyphsByKey, cropCacheBust, upsertBbox, markGlyphTraced, refreshCrop, openDiagnose } = useAdmin();
  const bbox = bboxesByKey[glyphKey] ?? null;
  // Always-current bbox map, read (not subscribed) by the open/reset effect so it
  // can seed applyAll from the letter's split state without re-running on edits.
  const bboxesByKeyRef = useRef(bboxesByKey);
  bboxesByKeyRef.current = bboxesByKey;
  const known = knownGlyph(glyphKey);
  const hasCanonical = glyphsByKey[glyphKey]?.has_data === true;

  const [step, setStep] = useState(0);
  const stepId = STEPS[step].id;

  // The Weg path is captured as a list of strokes (one per pen-down→pen-up); a
  // pen lift starts a new stroke instead of extending the last one, so separate
  // strokes never get joined by a line.
  const [strokes, setStrokes] = useState<StrokePoint[][]>([]);
  // Weg step interaction: draw new strokes, or "Anpassen" — drag the already
  // drawn line to iron out a wobble before saving (warps nearby points toward
  // the pointer, with the falloff radius below). Edits the draft only.
  const [wegTool, setWegTool] = useState<'draw' | 'adjust'>('draw');
  const [nudgeRadius, setNudgeRadius] = useState(10);
  const [maskRadius, setMaskRadius] = useState(8);
  // Which brush the Ausschluss step paints with: the eraser (Radierer, blanks
  // neighbour ink) or the ink brush (Tinte, fills specks). Shares maskRadius.
  const [tool, setTool] = useState<'eraser' | 'ink'>('eraser');
  // "Maske zeigen": swap the raw crop for the binarised mask (auto-fill
  // colour-coded) so the Lücken-füllen effect — invisible on the raw scan — and
  // the remaining holes to ink by hand are visible. Ausschluss step only.
  const [showMask, setShowMask] = useState(false);
  const [applyAll, setApplyAll] = useState(true);
  const [busy, setBusy] = useState(false);
  const [snack, setSnack] = useState<string | null>(null);
  // Saved-Weg reference overlay on the Weg step (toggleable, on by default).
  const [showSaved, setShowSaved] = useState(true);
  const [savedTrace, setSavedTrace] = useState<SavedTraceOverlay | null>(null);

  // The Optimieren step (step 5) is a comparison surface: the Weg is already
  // saved on step 4 (optimized), and this holds the raw-vs-optimized dry run
  // (trace-preview from the stored raw_path) the step renders side by side.
  const [preview, setPreview] = useState<TracePreviewOut | null>(null);
  const [previewBusy, setPreviewBusy] = useState(false);
  const previewEpoch = useRef(0);

  // Mounted once and reused for every glyph: when a different glyph opens (or the
  // dialog reopens), drop transient state so one glyph's draft never leaks onto
  // the next.
  useEffect(() => {
    setStep(0);
    setTool('eraser');
    setWegTool('draw');
    setShowMask(false);
    setStrokes([]);
    previewEpoch.current++;
    setPreview(null);
    setPreviewBusy(false);
    // Seed the unified/split choice from the letter's current state: an already
    // split letter defaults to keeping this position separate; a unified letter
    // defaults to "one form for all". The user can still flip it before finishing.
    setApplyAll(!isLetterSplit(glyphKey, bboxesByKeyRef.current));
  }, [glyphKey, open]);

  // Savable points (strokes with ≥2 points; stray taps excluded) — gates "save".
  const savablePoints = savablePointCount(strokes);

  // Load the saved Weg + anchors for the reference overlay. Runs when the dialog
  // opens on a glyph that already has a canonical (hasCanonical flips also right
  // after the first save); save/resample refresh it explicitly, so the overlay
  // always reflects the latest server state. The epoch counter discards slow
  // responses that land after the wizard moved on to another glyph — the hook is
  // mounted once and reused, so a stale setState would otherwise paint glyph A's
  // Weg over glyph B's canvas.
  const overlayEpoch = useRef(0);
  const refreshSavedTrace = useCallback(async () => {
    const epoch = ++overlayEpoch.current;
    try {
      const [tpl, diag] = await Promise.all([getGlyph(sourceId, glyphKey), getDiagnostic(sourceId, glyphKey)]);
      if (overlayEpoch.current === epoch) setSavedTrace({ rawPath: tpl.raw_path, anchorsPx: diag.anchors_px });
    } catch {
      // 404 (no canonical) or transient error → no overlay.
      if (overlayEpoch.current === epoch) setSavedTrace(null);
    }
  }, [sourceId, glyphKey]);
  useEffect(() => {
    overlayEpoch.current++; // invalidate any in-flight fetch for the previous glyph
    setSavedTrace(null);
    if (open && hasCanonical) void refreshSavedTrace();
  }, [open, hasCanonical, refreshSavedTrace]);

  const guideVals = useMemo<GuideValues>(() => {
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

  const updateBboxField = useCallback(
    async (patch: Partial<BboxIn>) => {
      if (!bbox) return;
      try {
        const saved = await putBbox(sourceId, glyphKey, { ...bboxInFromOut(bbox), ...patch });
        upsertBbox(glyphKey, saved);
      } catch (err) {
        setSnack(`${de.wizard.snack.saveFailed} ${err}`);
      }
    },
    [sourceId, bbox, glyphKey, upsertBbox],
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

  // ------------------------------------------------- gesture commits (canvas)
  // Called by WizardCanvas on pointer-up with the finished gesture's values.

  // Finished Grundlinie/Mittellinie drag.
  const commitCalib = useCallback(
    async (field: CalibField, curY: number) => {
      // Keep the baseline below the midband (server enforces baseline_y > midband_y).
      if (bbox) {
        const other = field === 'baseline_y' ? bbox.midband_y : bbox.baseline_y;
        const ok = field === 'baseline_y' ? curY > other : curY < other;
        if (ok) await updateBboxField({ [field]: curY });
        else setSnack(de.wizard.snack.baselineBelowMidband);
      }
    },
    [bbox, updateBboxField],
  );

  // Finished slant-handle drag: snap the dragged line's x and persist.
  const commitSlant = useCallback(
    async (index: number, curX: number) => {
      const xs = guideVals.slantXs.slice();
      xs[index] = Math.round(curX);
      await updateGuides({ slant_xs: xs });
    },
    [guideVals, updateGuides],
  );

  // Finished eraser stroke at the current brush radius.
  const commitMaskStroke = useCallback(
    async (points: Array<[number, number]>) => {
      const stroke: MaskStroke = { points, radius: maskRadius };
      if (bbox) {
        await updateBboxField({ mask_strokes: [...bbox.mask_strokes, stroke] });
        refreshCrop();
      }
    },
    [maskRadius, bbox, updateBboxField, refreshCrop],
  );

  const undoMask = useCallback(async () => {
    if (!bbox || bbox.mask_strokes.length === 0) return;
    await updateBboxField({ mask_strokes: bbox.mask_strokes.slice(0, -1) });
    refreshCrop();
  }, [bbox, updateBboxField, refreshCrop]);

  // Finished ink-brush stroke (Tinte) — the eraser's positive twin: appended to
  // ink_strokes, painted as ink into the crop before binarisation.
  const commitInkStroke = useCallback(
    async (points: Array<[number, number]>) => {
      const stroke: MaskStroke = { points, radius: maskRadius };
      if (bbox) {
        await updateBboxField({ ink_strokes: [...bbox.ink_strokes, stroke] });
        refreshCrop();
      }
    },
    [maskRadius, bbox, updateBboxField, refreshCrop],
  );

  const undoInk = useCallback(async () => {
    if (!bbox || bbox.ink_strokes.length === 0) return;
    await updateBboxField({ ink_strokes: bbox.ink_strokes.slice(0, -1) });
    refreshCrop();
  }, [bbox, updateBboxField, refreshCrop]);

  // Per-glyph speck auto-fill threshold (Lücken füllen); 0 = off. Re-derivation
  // and the diagnostic read it from the bbox, so refresh the crop preview too.
  const setFillHoles = useCallback(
    async (maxArea: number) => {
      if (bbox) {
        await updateBboxField({ fill_holes_max_area: Math.max(0, Math.round(maxArea)) });
        refreshCrop();
      }
    },
    [bbox, updateBboxField, refreshCrop],
  );

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

  // Save the drawn Weg (step 4). The pipeline optimizes on every save, so the
  // stored canonical is the optimized one; step 5 then visualises raw vs
  // optimized. `nAnchors` comes from the TraceStep's just-committed field so
  // the call never races the PUT that persists it.
  const saveTrace = useCallback(async (nAnchors: number) => {
    const rawPath = flattenStrokes(strokes);
    if (rawPath.length < 2 || !known || !bbox) return;
    setBusy(true);
    try {
      const g = await postTrace(sourceId, glyphKey, {
        glyph: known.glyph,
        position: known.position,
        raw_path: rawPath,
        n_anchors: nAnchors,
      });
      markGlyphTraced(glyphKey, summaryOf(g));
      setSnack(fmt(de.wizard.snack.traceSaved, { count: g.anchors.length }));
      setStrokes([]);
      void refreshSavedTrace();
    } catch (err) {
      setSnack(String(err));
    } finally {
      setBusy(false);
    }
  }, [sourceId, strokes, known, bbox, glyphKey, markGlyphTraced, refreshSavedTrace]);

  // Step 5: compute the raw-vs-optimized comparison from the freshly drawn Weg
  // (if any) or the stored raw_path. A pure dry run — nothing is written; the
  // glyph is already saved on step 4.
  const computePreview = useCallback(async (nAnchors: number) => {
    if (!known || !bbox) return;
    let rawPath = flattenStrokes(strokes);
    if (rawPath.length < 2) {
      if (!hasCanonical) return;
      try {
        rawPath = (await getGlyph(sourceId, glyphKey)).raw_path; // the saved Weg
      } catch (err) {
        setSnack(String(err));
        return;
      }
    }
    const epoch = ++previewEpoch.current;
    setPreview(null);
    setPreviewBusy(true);
    try {
      const p = await postTracePreview(sourceId, glyphKey, {
        glyph: known.glyph,
        position: known.position,
        raw_path: rawPath,
        n_anchors: nAnchors,
      });
      if (previewEpoch.current === epoch) setPreview(p);
    } catch (err) {
      if (previewEpoch.current === epoch) setSnack(String(err));
    } finally {
      if (previewEpoch.current === epoch) setPreviewBusy(false);
    }
  }, [sourceId, strokes, known, bbox, hasCanonical, glyphKey]);

  // Re-sample the stored canonical to the given n_anchors without re-drawing.
  const resample = useCallback(async (nAnchors: number) => {
    if (!bbox || !hasCanonical) return;
    setBusy(true);
    try {
      const g = await postResample(sourceId, glyphKey, { nAnchors });
      markGlyphTraced(glyphKey, summaryOf(g));
      setSnack(fmt(de.wizard.snack.resampled, { count: g.anchors.length }));
      void refreshSavedTrace();
    } catch (err) {
      setSnack(String(err));
    } finally {
      setBusy(false);
    }
  }, [sourceId, bbox, hasCanonical, glyphKey, markGlyphTraced, refreshSavedTrace]);

  // Approve → lock. applyAll is the unified-vs-split decision:
  //   true  (unified) — THIS position's form is the one form for the letter. Fan
  //                     it out to every sibling (overwriting any divergent split
  //                     forms — "eine Form übernehmen") and clear `split` on all.
  //   false (split)   — author only this position; flag the letter `split` across
  //                     every sibling-with-bbox so isLetterSplit (a `.some` read)
  //                     stays consistent and the siblings keep their own forms.
  const finish = useCallback(async () => {
    if (!bbox || !known) return;
    setBusy(true);
    try {
      if (applyAll) {
        const tpl = await getGlyph(sourceId, glyphKey); // carries the raw_path to copy
        for (const k of siblingKeys(glyphKey)) {
          if (k === glyphKey) continue;
          const kg = knownGlyph(k);
          if (!kg) continue;
          // Create the bbox UNLOCKED first (the trace precondition needs a bbox),
          // post the trace, and only THEN lock — so a mid-loop failure never
          // leaves a locked-but-empty sibling that can't be reopened in the wizard.
          await putBbox(sourceId, k, { ...bboxInFromOut(bbox), locked: false, split: false });
          const g = await postTrace(sourceId, k, {
            glyph: kg.glyph,
            position: kg.position,
            raw_path: tpl.raw_path,
            // The fetched template's REAL count, not bbox.n_anchors: the bbox in
            // this closure can lag a just-committed field edit, and the fan-out
            // must reproduce exactly the form the user approved.
            n_anchors: tpl.anchors.length,
          });
          markGlyphTraced(k, summaryOf(g));
          const savedB = await putBbox(sourceId, k, { ...bboxInFromOut(bbox), locked: true, split: false });
          upsertBbox(k, savedB);
        }
        const saved = await putBbox(sourceId, glyphKey, { ...bboxInFromOut(bbox), locked: true, split: false });
        upsertBbox(glyphKey, saved);
      } else {
        // Split: flag every existing sibling so the letter reads as split, leaving
        // their forms and lock state untouched; only this position is (re)authored.
        for (const k of siblingKeys(glyphKey)) {
          if (k === glyphKey) continue;
          const sib = bboxesByKey[k];
          if (!sib) continue;
          const savedB = await putBbox(sourceId, k, { ...bboxInFromOut(sib), split: true });
          upsertBbox(k, savedB);
        }
        const saved = await putBbox(sourceId, glyphKey, { ...bboxInFromOut(bbox), locked: true, split: true });
        upsertBbox(glyphKey, saved);
      }
      onClose();
    } catch (err) {
      setSnack(`${de.wizard.snack.finishFailed} ${err}`);
    } finally {
      setBusy(false);
    }
  }, [sourceId, bbox, known, applyAll, glyphKey, bboxesByKey, upsertBbox, markGlyphTraced, onClose]);

  return {
    // admin-context reads the shell/canvas/panels need
    source,
    bbox,
    bboxesByKey,
    known,
    hasCanonical,
    cropCacheBust,
    openDiagnose,
    // step position
    step,
    setStep,
    stepId,
    // Weg strokes (committed; the in-progress stroke is appended live by the canvas)
    strokes,
    setStrokes,
    savablePoints,
    wegTool,
    setWegTool,
    nudgeRadius,
    setNudgeRadius,
    // saved-Weg reference overlay (Weg step)
    savedTrace,
    showSaved,
    setShowSaved,
    // per-step knobs + status
    maskRadius,
    setMaskRadius,
    tool,
    setTool,
    showMask,
    setShowMask,
    applyAll,
    setApplyAll,
    busy,
    snack,
    setSnack,
    guideVals,
    // Weg step (step 4) saves; Optimieren step (step 5) is the comparison view
    saveTrace,
    preview,
    previewBusy,
    computePreview,
    // mutations
    updateBboxField,
    updateGuides,
    commitCalib,
    commitSlant,
    commitMaskStroke,
    undoMask,
    commitInkStroke,
    undoInk,
    setFillHoles,
    addSlantLine,
    removeSlantLine,
    resample,
    finish,
  };
}
