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
//   4. Übersicht   — open the (large) Diagnose modal to review, then
//                    approve → lock (the bbox's `locked`).
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
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Step,
  StepButton,
  Stepper,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { useState } from 'react';

import { de, fmt } from '@/locales/admin';
import { ErrorText } from '@/sections/admin/shell/ErrorText';
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
  const { source, bbox, known, hasCanonical, step, setStep, stepId, busy, snack, setSnack, finish, dirty } = wizard;

  // Asked before an unsaved Weg would be dropped — see `requestClose` below.
  const [confirmClose, setConfirmClose] = useState(false);

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
            sourceId={source.id}
            chartW={source.chart_size.w}
            chartH={source.chart_size.h}
            maskRadius={wizard.maskRadius}
            setMaskRadius={wizard.setMaskRadius}
            tool={wizard.tool}
            setTool={wizard.setTool}
            showMask={wizard.showMask}
            setShowMask={wizard.setShowMask}
            undoMask={wizard.undoMask}
            undoInk={wizard.undoInk}
            setFillHoles={wizard.setFillHoles}
            addPatch={wizard.addPatch}
            removePatch={wizard.removePatch}
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
            showSaved={wizard.showSaved}
            setShowSaved={wizard.setShowSaved}
            saveTrace={wizard.saveTrace}
            resample={wizard.resample}
            updateBboxField={wizard.updateBboxField}
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
            locked={bbox.locked}
            draft={wizard.draft}
            restoreDraft={wizard.restoreDraft}
            dismissDraft={wizard.dismissDraft}
          />
        );
      case 'overview':
        return (
          <OverviewStep
            glyphKey={glyphKey}
            hasCanonical={hasCanonical}
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

  // THE single way out. MUI hands `onClose` the reason, so `escapeKeyDown` and
  // `backdropClick` land here just like the footer's „Schließen" — which is the
  // whole point: all three used to drop a drawn Weg without a word, and the Weg
  // is the one thing in this dialog that is not already on the server.
  const requestClose = () => {
    if (dirty) {
      setConfirmClose(true);
      return;
    }
    onClose();
  };

  // Shown BEFORE the work rather than as a 423 after it. The wizard already
  // reads the bbox, so the lock was knowable all along — it just never said so,
  // and „Weg speichern" then failed with an English server line.
  const locked = bbox.locked;

  return (
    <Dialog
      open={open}
      onClose={requestClose}
      fullScreen={compact}
      fullWidth
      maxWidth="lg"
      // overflowX on the paper: a sub-pixel cell width in step 4 used to push a
      // full-width horizontal scrollbar under the whole dialog and clip the one
      // cell („Überlagert") that answers the step's question.
      slotProps={{ paper: { sx: { height: compact ? '100%' : '92vh', overflowX: 'hidden' } } }}
    >
      <Box sx={{ px: 2, pt: 2, minWidth: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          <Typography variant="h6">
            {de.wizard.title} {known.label}
          </Typography>
          {locked && <Chip size="small" color="warning" variant="outlined" label={de.wizard.lock.chip} />}
        </Box>
        {/* The stepper's own list overflowed its box by 8px at every width. */}
        <Stepper nonLinear activeStep={step} sx={{ mt: 1, minWidth: 0 }}>
          {STEPS.map((s, i) => (
            <Step key={s.id} completed={false} sx={{ minWidth: 0 }}>
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
              updatePatch={wizard.updatePatch}
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
        <Alert severity={snack.kind} onClose={() => setSnack(null)} sx={{ mx: 2 }}>
          {snack.error ? <ErrorText error={snack.error} prefix={snack.text} /> : snack.text}
        </Alert>
      )}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Button startIcon={<ArrowBackIcon />} disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>
          {de.wizard.footer.back}
        </Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button onClick={requestClose}>{de.wizard.footer.close}</Button>
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

      {/* The guard itself. It names what is lost AND what is not — the author
          should not have to remember which of the four steps live-commit. Its
          „Verwerfen" still tucks the strokes into sessionStorage, so even the
          deliberate discard is offered back on the next opening. */}
      <Dialog open={confirmClose} onClose={() => setConfirmClose(false)} maxWidth="xs">
        <DialogTitle>{de.wizard.confirmClose.title}</DialogTitle>
        <DialogContent>
          <DialogContentText>{de.wizard.confirmClose.body}</DialogContentText>
          <DialogContentText sx={{ mt: 1 }}>
            {fmt(de.wizard.confirmClose.strokes, { count: wizard.strokes.length })}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmClose(false)}>{de.wizard.confirmClose.keep}</Button>
          <Button
            color="warning"
            onClick={() => {
              setConfirmClose(false);
              wizard.discardAndClose();
            }}
          >
            {de.wizard.confirmClose.discard}
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
}
