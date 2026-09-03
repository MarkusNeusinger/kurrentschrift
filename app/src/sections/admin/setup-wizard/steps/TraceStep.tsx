// Step 4 "Weg" (the ductus trace) — Zeichnen/Anpassen tool toggle (draw new
// strokes vs. warp-drag the drawn line to smooth a wobble, with a falloff
// radius), stroke undo/discard, n_anchors + resample. Strokes are drawn/warped
// on WizardCanvas. The primary button
// saves the Weg (the pipeline optimizes on every save); once saved, an inline
// WegPreview shows the optimized silhouette over the crop with its score.

import RefreshIcon from '@mui/icons-material/Refresh';
import UndoIcon from '@mui/icons-material/Undo';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControlLabel,
  Slider,
  Stack,
  Switch,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from 'react';

import { InfoHint } from '@/components/InfoHint';
import { de, fmt } from '@/locales/admin';
import type { BboxIn, BboxOut, StrokePoint, TracePreviewOut } from '@/lib/api';
import { HintHeading } from './HintHeading';
import { WegPreview } from './WegPreview';

// Mirrors the server-side bounds on n_anchors (api/schemas.py) so a committed
// value can never 422.
const MIN_ANCHORS = 4;
const MAX_ANCHORS = 1000;

export function TraceStep({
  bbox,
  strokes,
  setStrokes,
  savablePoints,
  hasCanonical,
  busy,
  showSaved,
  setShowSaved,
  saveTrace,
  resample,
  updateBboxField,
  wegTool,
  setWegTool,
  nudgeRadius,
  setNudgeRadius,
  glyphKey,
  cropCacheBust,
  savedAnchorCount,
  preview,
  previewBusy,
  computePreview,
  locked,
  draft,
  restoreDraft,
  dismissDraft,
}: {
  bbox: BboxOut;
  strokes: StrokePoint[][];
  setStrokes: Dispatch<SetStateAction<StrokePoint[][]>>;
  savablePoints: number;
  hasCanonical: boolean;
  busy: boolean;
  showSaved: boolean;
  setShowSaved: (v: boolean) => void;
  // `force` overrides the server's lock guard and is passed ONLY by the
  // confirmation dialog below — never straight from a button.
  saveTrace: (nAnchors: number, force?: boolean) => Promise<void>;
  resample: (nAnchors: number, force?: boolean) => Promise<void>;
  updateBboxField: (patch: Partial<BboxIn>) => Promise<void>;
  wegTool: 'draw' | 'adjust';
  setWegTool: (t: 'draw' | 'adjust') => void;
  nudgeRadius: number;
  setNudgeRadius: (r: number) => void;
  glyphKey: string;
  cropCacheBust?: number;
  // The saved canonical's authoritative anchor count (from the loaded overlay),
  // used as the preview's resample target instead of the possibly-lagging
  // bbox.n_anchors. Undefined until the overlay loads → falls back to the bbox.
  savedAnchorCount?: number;
  preview: TracePreviewOut | null;
  previewBusy: boolean;
  computePreview: (nAnchors: number) => Promise<void>;
  // The bbox's lock. The author settled the doctrine on 2026-09-03 (audit
  // finding 13): a locked glyph stays fully OFFERED and carries the lock
  // visibly, and overwriting it is a deliberate confirmation here rather than
  // a detour to the Tafel's lock toggle. So `locked` changes two things on this
  // step — the warning and the button's label — and routes both writes through
  // the dialog that is allowed to send `force`.
  locked: boolean;
  // A Weg the last visit closed on, offered back rather than restored silently.
  draft: StrokePoint[][] | null;
  restoreDraft: () => void;
  dismissDraft: () => void;
}) {
  // n_anchors edits buffer in a local draft and commit on blur/Enter (or via the
  // buttons): a field controlled straight by the server value can never be
  // cleared — each keystroke would PUT and snap the text back mid-typing.
  // Adjust mode warps existing strokes; once they're all undone/discarded there's
  // nothing to drag (and pointer-down would be a no-op), so fall back to drawing.
  useEffect(() => {
    if (wegTool === 'adjust' && savablePoints < 2) setWegTool('draw');
  }, [wegTool, savablePoints, setWegTool]);

  // Which write is waiting for the lock confirmation, if any. Both writes on
  // this step rewrite the stored canonical and both meet the server's 423, so
  // both ask the same question — with the wording of the write they belong to.
  const [confirmWrite, setConfirmWrite] = useState<'trace' | 'resample' | null>(null);

  const [anchorsDraft, setAnchorsDraft] = useState(String(bbox.n_anchors));
  const committedAnchors = useRef(bbox.n_anchors);
  useEffect(() => {
    committedAnchors.current = bbox.n_anchors;
    setAnchorsDraft(String(bbox.n_anchors));
  }, [bbox.n_anchors]);

  // Commit the draft (clamped to ≥MIN_ANCHORS) and return the effective count;
  // an empty/invalid draft snaps back to the last committed value. The buttons
  // pass the returned count onward so save/resample never race the PUT.
  const commitAnchors = (): number => {
    // Number, not parseInt: the number input passes scientific notation ('1e3')
    // through, which parseInt would silently truncate to 1. Empty → invalid.
    const parsed = anchorsDraft.trim() === '' ? NaN : Math.trunc(Number(anchorsDraft));
    if (!Number.isFinite(parsed)) {
      setAnchorsDraft(String(committedAnchors.current));
      return committedAnchors.current;
    }
    const v = Math.min(MAX_ANCHORS, Math.max(MIN_ANCHORS, parsed));
    setAnchorsDraft(String(v));
    if (v !== committedAnchors.current) {
      committedAnchors.current = v;
      void updateBboxField({ n_anchors: v });
    }
    return v;
  };

  return (
    <Stack spacing={1.5}>
      <HintHeading title={de.wizard.trace.title}>
        <Typography variant="body2" gutterBottom>
          {de.wizard.trace.body1}
        </Typography>
        <Typography variant="body2">
          <b>{de.wizard.trace.penLiftBold}</b> {de.wizard.trace.penLiftAfterBold} <b>u</b> {de.wizard.trace.penLiftRest}
        </Typography>
      </HintHeading>
      <Typography variant="body2" color="text.secondary">
        {de.wizard.trace.lead}
      </Typography>

      {/* Before the work, not after it. The lock no longer blocks the step —
          it announces that a finished Weg is at stake, and the save button
          below says so too, so the confirmation is expected rather than a
          surprise at the end of a trace. */}
      {locked && <Alert severity="warning">{de.wizard.lock.warning}</Alert>}

      {/* The rescue offer. Only while nothing new is drawn — a restore that
          replaced live strokes would be the very loss this exists to prevent. */}
      {draft && strokes.length === 0 && (
        <Alert
          severity="info"
          action={
            <Stack direction="row" spacing={1}>
              <Button size="small" onClick={restoreDraft}>
                {de.wizard.draft.restore}
              </Button>
              <Button size="small" color="inherit" onClick={dismissDraft}>
                {de.wizard.draft.dismiss}
              </Button>
            </Stack>
          }
        >
          {fmt(de.wizard.draft.offer, { count: draft.length })}
        </Alert>
      )}

      <ToggleButtonGroup
        size="small"
        exclusive
        value={wegTool}
        onChange={(_e, v: 'draw' | 'adjust' | null) => v && setWegTool(v)}
        fullWidth
      >
        <ToggleButton value="draw">{de.wizard.trace.toolDraw}</ToggleButton>
        <ToggleButton value="adjust" disabled={savablePoints < 2}>
          {de.wizard.trace.toolAdjust}
        </ToggleButton>
      </ToggleButtonGroup>
      {wegTool === 'adjust' && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="caption">
              {de.wizard.trace.nudgeRadius} {nudgeRadius}px
            </Typography>
            <InfoHint title={de.wizard.trace.toolAdjust}>{de.wizard.trace.adjustHint}</InfoHint>
          </Box>
          <Slider
            size="small"
            min={3}
            max={40}
            value={nudgeRadius}
            onChange={(_e, v) => typeof v === 'number' && setNudgeRadius(v)}
            aria-label={de.wizard.trace.nudgeRadius}
          />
        </Box>
      )}

      <Stack direction="row" spacing={1}>
        <Button size="small" startIcon={<UndoIcon />} disabled={strokes.length === 0} onClick={() => setStrokes((s) => s.slice(0, -1))}>
          {de.wizard.trace.undoStroke} ({strokes.length})
        </Button>
        <Button size="small" color="inherit" disabled={strokes.length === 0} onClick={() => setStrokes([])}>
          {de.wizard.trace.discardAll}
        </Button>
        {/* On a locked glyph the click ASKS instead of writing; only the
            dialog's confirm re-enters with force. Everything else is the
            unchanged path. */}
        <Button
          size="small"
          variant="contained"
          disabled={savablePoints < 2 || busy}
          onClick={() => (locked ? setConfirmWrite('trace') : void saveTrace(commitAnchors()))}
        >
          {locked ? de.wizard.lock.saveLocked : de.wizard.trace.save}
        </Button>
      </Stack>
      {/* A standing fact, not an event. This used to be a green success Alert —
          which MUI renders as role="alert"/aria-live="assertive" — so opening a
          glyph traced months ago announced „Weg gespeichert." as if it had just
          happened. The EVENT keeps its own channel: the alert bar says „Weg
          gespeichert · n Anker" once, when it is true. */}
      {hasCanonical && strokes.length === 0 && (
        <Typography variant="caption" color="text.secondary">
          {de.wizard.trace.hasSaved}
        </Typography>
      )}
      {hasCanonical && (
        <FormControlLabel
          control={<Switch size="small" checked={showSaved} onChange={(_e, v) => setShowSaved(v)} />}
          label={<Typography variant="body2">{de.wizard.trace.showSaved}</Typography>}
        />
      )}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TextField
          label={de.wizard.trace.anchorsLabel}
          type="number"
          size="small"
          value={anchorsDraft}
          onChange={(e) => setAnchorsDraft(e.target.value)}
          onBlur={commitAnchors}
          onKeyDown={(e) => {
            if (e.key === 'Enter') commitAnchors();
          }}
          slotProps={{ htmlInput: { min: MIN_ANCHORS, max: MAX_ANCHORS } }}
          sx={{ flex: 1 }}
        />
        <Button
          size="small"
          variant="outlined"
          startIcon={<RefreshIcon />}
          disabled={!hasCanonical || busy}
          onClick={() => (locked ? setConfirmWrite('resample') : void resample(commitAnchors()))}
        >
          {de.wizard.trace.resample}
        </Button>
        <InfoHint title={de.wizard.trace.anchorsLabel}>{de.wizard.trace.anchorsHint}</InfoHint>
      </Box>

      {hasCanonical && (
        <WegPreview
          glyphKey={glyphKey}
          cropCacheBust={cropCacheBust}
          hasDraftSource={savablePoints >= 2 || hasCanonical}
          nAnchors={savedAnchorCount ?? bbox.n_anchors}
          preview={preview}
          previewBusy={previewBusy}
          computePreview={computePreview}
        />
      )}

      {/* THE only place `force` is ever set. The lock stays a real gate — the
          server refuses without it (423) — but the gate is now one deliberate
          answer here rather than a detour through the Tafel's lock toggle. */}
      <Dialog open={confirmWrite !== null} onClose={() => setConfirmWrite(null)} maxWidth="xs">
        <DialogTitle>
          {confirmWrite === 'resample' ? de.wizard.lock.confirmResample.title : de.wizard.lock.confirm.title}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {confirmWrite === 'resample' ? de.wizard.lock.confirmResample.body : de.wizard.lock.confirm.body}
          </DialogContentText>
          <DialogContentText sx={{ mt: 1 }}>
            {confirmWrite === 'resample' ? de.wizard.lock.confirmResample.hint : de.wizard.lock.confirm.hint}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmWrite(null)}>{de.wizard.lock.confirm.cancel}</Button>
          <Button
            color="warning"
            onClick={() => {
              const pending = confirmWrite;
              setConfirmWrite(null);
              const n = commitAnchors();
              if (pending === 'resample') void resample(n, true);
              else void saveTrace(n, true);
            }}
          >
            {de.wizard.lock.confirm.confirm}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
