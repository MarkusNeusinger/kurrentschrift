// Step 4 "Weg" (the ductus trace) — stroke undo/discard, n_anchors + resample,
// and the entry/exit coupling heights. Strokes are drawn on WizardCanvas. The
// primary button saves the Weg (the pipeline optimizes on every save); the
// next step ("Optimieren") then shows the raw-vs-optimized comparison.

import RefreshIcon from '@mui/icons-material/Refresh';
import UndoIcon from '@mui/icons-material/Undo';
import { Alert, Box, Button, FormControlLabel, Stack, Switch, TextField, Typography } from '@mui/material';
import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from 'react';

import { couplingLabel, de } from '@/locales';
import type { BboxIn, BboxOut, CouplingHeight, GuideConfig, StrokePoint } from '@/lib/api';
import type { GuideValues } from '../wizardTypes';

const COUPLING_OPTIONS: CouplingHeight[] = ['baseline', 'midband', 'ascender', 'descender'];

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
  guideVals,
  showSaved,
  setShowSaved,
  saveTrace,
  resample,
  updateBboxField,
  updateGuides,
}: {
  bbox: BboxOut;
  strokes: StrokePoint[][];
  setStrokes: Dispatch<SetStateAction<StrokePoint[][]>>;
  savablePoints: number;
  hasCanonical: boolean;
  busy: boolean;
  guideVals: GuideValues;
  showSaved: boolean;
  setShowSaved: (v: boolean) => void;
  saveTrace: (nAnchors: number) => Promise<void>;
  resample: (nAnchors: number) => Promise<void>;
  updateBboxField: (patch: Partial<BboxIn>) => Promise<void>;
  updateGuides: (patch: Partial<GuideConfig>) => Promise<void>;
}) {
  // n_anchors edits buffer in a local draft and commit on blur/Enter (or via the
  // buttons): a field controlled straight by the server value can never be
  // cleared — each keystroke would PUT and snap the text back mid-typing.
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
      <Typography variant="subtitle2">{de.wizard.trace.title}</Typography>
      <Typography variant="body2" color="text.secondary">
        {de.wizard.trace.body1}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        <b>{de.wizard.trace.penLiftBold}</b> {de.wizard.trace.penLiftAfterBold} <b>u</b> {de.wizard.trace.penLiftRest}
      </Typography>
      <Stack direction="row" spacing={1}>
        <Button size="small" startIcon={<UndoIcon />} disabled={strokes.length === 0} onClick={() => setStrokes((s) => s.slice(0, -1))}>
          {de.wizard.trace.undoStroke} ({strokes.length})
        </Button>
        <Button size="small" color="inherit" disabled={strokes.length === 0} onClick={() => setStrokes([])}>
          {de.wizard.trace.discardAll}
        </Button>
        <Button size="small" variant="contained" disabled={savablePoints < 2 || busy} onClick={() => void saveTrace(commitAnchors())}>
          {de.wizard.trace.save}
        </Button>
      </Stack>
      {hasCanonical && strokes.length === 0 && <Alert severity="success" variant="outlined">{de.wizard.trace.saved}</Alert>}
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
        <Button size="small" variant="outlined" startIcon={<RefreshIcon />} disabled={!hasCanonical || busy} onClick={() => void resample(commitAnchors())}>
          {de.wizard.trace.resample}
        </Button>
      </Box>
      <Typography variant="caption" color="text.secondary">
        {de.wizard.trace.anchorsHint}
      </Typography>
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField select size="small" label={de.wizard.trace.entryCoupling} value={guideVals.entryCoupling} onChange={(e) => updateGuides({ entry_coupling: e.target.value as CouplingHeight })} sx={{ flex: 1 }} slotProps={{ select: { native: true } }}>
          {COUPLING_OPTIONS.map((c) => (
            <option key={c} value={c}>
              {couplingLabel(c)}
            </option>
          ))}
        </TextField>
        <TextField select size="small" label={de.wizard.trace.exitCoupling} value={guideVals.exitCoupling} onChange={(e) => updateGuides({ exit_coupling: e.target.value as CouplingHeight })} sx={{ flex: 1 }} slotProps={{ select: { native: true } }}>
          {COUPLING_OPTIONS.map((c) => (
            <option key={c} value={c}>
              {couplingLabel(c)}
            </option>
          ))}
        </TextField>
      </Box>
      <Typography variant="caption" color="text.secondary">
        {de.wizard.trace.couplingHint}
      </Typography>
    </Stack>
  );
}
