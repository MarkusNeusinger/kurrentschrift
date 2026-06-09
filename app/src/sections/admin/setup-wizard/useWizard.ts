// Wizard-level state + server mutations for the Einrichtungs-Wizard: the step
// position, the captured Weg strokes, the resolved guide values and every
// live-commit against the API (PUT bbox / POST trace / resample / the final
// lock fan-out). The canvas hands finished gestures to the commit* callbacks;
// in-flight gesture state itself lives in WizardCanvas.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { getGlyph, postResample, postTrace, putBbox } from '@/lib/api';
import { bboxInFromOut } from '@/lib/bbox';
import { isLetterSplit, knownGlyph, siblingKeys } from '@/domain/glyphs';
import { useAdmin } from '@/context/AdminContext';
import { de, fmt } from '@/locales';
import { flattenStrokes, savablePointCount } from './strokeUtils';
import { STEPS } from './wizardTypes';
import type { CalibField, GuideValues } from './wizardTypes';
import type { BboxIn, GlyphSummary, GuideConfig, MaskStroke, StrokePoint } from '@/lib/api';

const summaryOf = (g: { glyph_key: string; glyph: string; position: string; variant: number; advance: number }): GlyphSummary => ({
  glyph_key: g.glyph_key,
  glyph: g.glyph,
  position: g.position,
  variant: g.variant,
  advance: g.advance,
  has_data: true,
});

export function useWizard(glyphKey: string, open: boolean, onClose: () => void) {
  const { source, bboxesByKey, glyphsByKey, cropCacheBust, upsertBbox, markGlyphTraced, refreshCrop, openDiagnose } = useAdmin();
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
  const [maskRadius, setMaskRadius] = useState(8);
  const [applyAll, setApplyAll] = useState(true);
  const [busy, setBusy] = useState(false);
  const [snack, setSnack] = useState<string | null>(null);

  // Mounted once and reused for every glyph: when a different glyph opens (or the
  // dialog reopens), drop transient state so one glyph's draft never leaks onto
  // the next.
  useEffect(() => {
    setStep(0);
    setStrokes([]);
    // Seed the unified/split choice from the letter's current state: an already
    // split letter defaults to keeping this position separate; a unified letter
    // defaults to "one form for all". The user can still flip it before finishing.
    setApplyAll(!isLetterSplit(glyphKey, bboxesByKeyRef.current));
  }, [glyphKey, open]);

  // Savable points (strokes with ≥2 points; stray taps excluded) — gates "save".
  const savablePoints = savablePointCount(strokes);

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
        const saved = await putBbox(glyphKey, { ...bboxInFromOut(bbox), ...patch });
        upsertBbox(glyphKey, saved);
      } catch (err) {
        setSnack(`${de.wizard.snack.saveFailed} ${err}`);
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
    const rawPath = flattenStrokes(strokes);
    if (rawPath.length < 2 || !known || !bbox) return;
    setBusy(true);
    try {
      const g = await postTrace(glyphKey, {
        glyph: known.glyph,
        position: known.position,
        raw_path: rawPath,
        n_anchors: bbox.n_anchors,
      });
      markGlyphTraced(glyphKey, summaryOf(g));
      setSnack(fmt(de.wizard.snack.traceSaved, { count: g.anchors.length }));
      setStrokes([]);
    } catch (err) {
      setSnack(String(err));
    } finally {
      setBusy(false);
    }
  }, [strokes, known, bbox, glyphKey, markGlyphTraced]);

  // Re-sample the stored canonical to the current n_anchors without re-drawing.
  const resample = useCallback(async () => {
    if (!bbox || !hasCanonical) return;
    setBusy(true);
    try {
      const g = await postResample(glyphKey, bbox.n_anchors);
      markGlyphTraced(glyphKey, summaryOf(g));
      setSnack(fmt(de.wizard.snack.resampled, { count: g.anchors.length }));
    } catch (err) {
      setSnack(String(err));
    } finally {
      setBusy(false);
    }
  }, [bbox, hasCanonical, glyphKey, markGlyphTraced]);

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
        const tpl = await getGlyph(glyphKey); // carries the raw_path to copy
        for (const k of siblingKeys(glyphKey)) {
          if (k === glyphKey) continue;
          const kg = knownGlyph(k);
          if (!kg) continue;
          // Create the bbox UNLOCKED first (the trace precondition needs a bbox),
          // post the trace, and only THEN lock — so a mid-loop failure never
          // leaves a locked-but-empty sibling that can't be reopened in the wizard.
          await putBbox(k, { ...bboxInFromOut(bbox), locked: false, split: false });
          const g = await postTrace(k, {
            glyph: kg.glyph,
            position: kg.position,
            raw_path: tpl.raw_path,
            n_anchors: bbox.n_anchors,
          });
          markGlyphTraced(k, summaryOf(g));
          const savedB = await putBbox(k, { ...bboxInFromOut(bbox), locked: true, split: false });
          upsertBbox(k, savedB);
        }
        const saved = await putBbox(glyphKey, { ...bboxInFromOut(bbox), locked: true, split: false });
        upsertBbox(glyphKey, saved);
      } else {
        // Split: flag every existing sibling so the letter reads as split, leaving
        // their forms and lock state untouched; only this position is (re)authored.
        for (const k of siblingKeys(glyphKey)) {
          if (k === glyphKey) continue;
          const sib = bboxesByKey[k];
          if (!sib) continue;
          const savedB = await putBbox(k, { ...bboxInFromOut(sib), split: true });
          upsertBbox(k, savedB);
        }
        const saved = await putBbox(glyphKey, { ...bboxInFromOut(bbox), locked: true, split: true });
        upsertBbox(glyphKey, saved);
      }
      onClose();
    } catch (err) {
      setSnack(`${de.wizard.snack.finishFailed} ${err}`);
    } finally {
      setBusy(false);
    }
  }, [bbox, known, applyAll, glyphKey, bboxesByKey, upsertBbox, markGlyphTraced, onClose]);

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
    // per-step knobs + status
    maskRadius,
    setMaskRadius,
    applyAll,
    setApplyAll,
    busy,
    snack,
    setSnack,
    guideVals,
    // mutations
    updateBboxField,
    updateGuides,
    commitCalib,
    commitSlant,
    commitMaskStroke,
    undoMask,
    addSlantLine,
    removeSlantLine,
    saveTrace,
    resample,
    finish,
  };
}
