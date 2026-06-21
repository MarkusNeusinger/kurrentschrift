// SetupWizard — the step-by-step Einrichtungs-Wizard for authoring a canonical
// from a rough bbox already drawn on the chart. Steps (registration-style, with
// Back/Next and free jumping to earlier steps):
//   1. Ausschluss  — freehand eraser (Radierer): paint over neighbouring ink so
//                    it can't pollute the skeleton. Strokes → bbox.mask_strokes.
//   2. Lineatur    — the full writing grid in one step: drag Grundlinie /
//                    Mittellinie (Oberlinie/Unterlinie derive, each toggleable),
//                    AND the Schräglage — one or more slant guides (several
//                    individually placed lines for m/n/u; all share the angle).
//   3. Weg         — draw the ductus with the stylus; "Anpassen" then warp-drags
//                    the drawn line to iron out a wobble before saving; saves the
//                    canonical and lets you re-sample it to a different anchor count.
//   4. Übersicht   — open the (large) Diagnose modal to review, optionally apply
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
// −/slider/+ control; Schwenken toggle or a wheel-zoomed drag to pan). Every step
// opens fit-to-view — the whole glyph is visible for erasing the box edges,
// placing the grid lines and tracing the Weg alike; the stylus user zooms in or
// out by hand (the slider now also goes below fit, to shrink a big letter on a
// large screen). Anpassen returns to the full crop.
//
// This file is only the Dialog shell (title, Stepper, canvas-vs-panel layout,
// footer); the state + mutations live in useWizard, the viewport in useCropView,
// the drawing surface in WizardCanvas and the right-hand panels in steps/.

import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import LockIcon from '@mui/icons-material/Lock';
import { Alert, Box, Button, Dialog, Step, StepButton, Stepper, Typography, useMediaQuery, useTheme } from '@mui/material';

import { de } from '@/locales';
import { useCropView } from './useCropView';
import { useWizard } from './useWizard';
import { WizardCanvas } from './WizardCanvas';
import { STEPS } from './wizardTypes';
import { LineaturStep } from './steps/LineaturStep';
import { MaskStep } from './steps/MaskStep';
import { OverviewStep } from './steps/OverviewStep';
import { TraceStep } from './steps/TraceStep';

export function SetupWizard({ glyphKey, open, onClose }: { glyphKey: string; open: boolean; onClose: () => void }) {
  const wizard = useWizard(glyphKey, open, onClose);
  const { source, bbox, known, hasCanonical, step, setStep, stepId, busy, snack, setSnack, finish } = wizard;

  // On a portrait phone the fixed-width side panel used to squeeze the crop
  // canvas to near-zero (only visible after rotating to landscape). Below `md`
  // we go full-screen and stack canvas-over-panel so the crop always gets room.
  const theme = useTheme();
  const compact = useMediaQuery(theme.breakpoints.down('md'));

  const view = useCropView(bbox, glyphKey, open, stepId);

  if (!source || !bbox || !known) return null;

  // ------------------------------------------------------------- step panels
  const panel = (() => {
    switch (stepId) {
      case 'mask':
        return (
          <MaskStep
            bbox={bbox}
            maskRadius={wizard.maskRadius}
            setMaskRadius={wizard.setMaskRadius}
            tool={wizard.tool}
            setTool={wizard.setTool}
            showMask={wizard.showMask}
            setShowMask={wizard.setShowMask}
            undoMask={wizard.undoMask}
            undoInk={wizard.undoInk}
            setFillHoles={wizard.setFillHoles}
          />
        );
      case 'lineatur':
        return (
          <LineaturStep
            bbox={bbox}
            source={source}
            guideVals={wizard.guideVals}
            updateGuides={wizard.updateGuides}
            addSlantLine={wizard.addSlantLine}
            removeSlantLine={wizard.removeSlantLine}
          />
        );
      case 'weg':
        return (
          <TraceStep
            bbox={bbox}
            strokes={wizard.strokes}
            setStrokes={wizard.setStrokes}
            savablePoints={wizard.savablePoints}
            hasCanonical={hasCanonical}
            busy={busy}
            guideVals={wizard.guideVals}
            showSaved={wizard.showSaved}
            setShowSaved={wizard.setShowSaved}
            saveTrace={wizard.saveTrace}
            resample={wizard.resample}
            updateBboxField={wizard.updateBboxField}
            updateGuides={wizard.updateGuides}
            wegTool={wizard.wegTool}
            setWegTool={wizard.setWegTool}
            nudgeRadius={wizard.nudgeRadius}
            setNudgeRadius={wizard.setNudgeRadius}
            glyphKey={glyphKey}
            cropCacheBust={wizard.cropCacheBust}
            savedAnchorCount={wizard.savedTrace?.anchorsPx.length}
            preview={wizard.preview}
            previewBusy={wizard.previewBusy}
            computePreview={wizard.computePreview}
          />
        );
      case 'overview':
        return (
          <OverviewStep
            glyphKey={glyphKey}
            known={known}
            hasCanonical={hasCanonical}
            applyAll={wizard.applyAll}
            setApplyAll={wizard.setApplyAll}
            bboxesByKey={wizard.bboxesByKey}
            openDiagnose={wizard.openDiagnose}
            cropCacheBust={wizard.cropCacheBust}
            nAnchors={wizard.savedTrace?.anchorsPx.length}
            preview={wizard.preview}
            previewBusy={wizard.previewBusy}
            computePreview={wizard.computePreview}
          />
        );
    }
  })();

  // Weg → Übersicht needs the Weg SAVED first (the inline preview + the overview
  // both read the stored canonical); every other step advances freely.
  const canAdvance = stepId === 'weg' ? hasCanonical : true;

  return (
    <Dialog open={open} onClose={onClose} fullScreen={compact} fullWidth maxWidth="lg" slotProps={{ paper: { sx: { height: compact ? '100%' : '92vh' } } }}>
      <Box sx={{ px: 2, pt: 2 }}>
        <Typography variant="h6">{de.wizard.title} {known.label}</Typography>
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
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, flex: 1, minHeight: 0, gap: { xs: 1, md: 2 }, p: { xs: 1, md: 2 } }}>
        {stepId === 'overview' ? (
          <Box sx={{ flex: 1, overflowY: 'auto' }}>{panel}</Box>
        ) : (
          <>
            <WizardCanvas
              glyphKey={glyphKey}
              open={open}
              stepId={stepId}
              bbox={bbox}
              source={source}
              known={known}
              guideVals={wizard.guideVals}
              view={view}
              cropCacheBust={wizard.cropCacheBust}
              maskRadius={wizard.maskRadius}
              tool={wizard.tool}
              wegTool={wizard.wegTool}
              nudgeRadius={wizard.nudgeRadius}
              showMask={wizard.showMask}
              strokes={wizard.strokes}
              setStrokes={wizard.setStrokes}
              savedTrace={wizard.savedTrace}
              showSaved={wizard.showSaved}
              commitCalib={wizard.commitCalib}
              commitSlant={wizard.commitSlant}
              commitMaskStroke={wizard.commitMaskStroke}
              commitInkStroke={wizard.commitInkStroke}
            />
            {/* On mobile this drops below the canvas with a capped, scrollable
                height so the crop above it always stays visible. The merged
                Lineatur & Schräglage panel is the tallest, and its step needs no
                fine drawing, so it gets more room there (the whole letter still
                fits the shorter canvas) to surface the slant controls; the
                drawing steps (Ausschluss/Weg) keep the canvas dominant. */}
            <Box sx={{ width: { xs: '100%', md: 340 }, flexShrink: 0, overflowY: 'auto', maxHeight: { xs: stepId === 'lineatur' ? '50%' : '40%', md: 'none' } }}>{panel}</Box>
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
          {de.wizard.footer.back}
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={onClose}>{de.wizard.footer.close}</Button>
          {step < STEPS.length - 1 ? (
            <Button variant="contained" endIcon={<ArrowForwardIcon />} disabled={!canAdvance} onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))}>
              {de.wizard.footer.next}
            </Button>
          ) : (
            <Button variant="contained" color="success" startIcon={<LockIcon />} disabled={!hasCanonical || busy} onClick={finish}>
              {de.wizard.footer.finish}
            </Button>
          )}
        </Box>
      </Box>
    </Dialog>
  );
}
