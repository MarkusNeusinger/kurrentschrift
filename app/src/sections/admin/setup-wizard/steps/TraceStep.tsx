// Schritt 4 · Weg (Ductus) — stroke undo/discard/save, n_anchors + resample,
// and the entry/exit coupling heights. The strokes are drawn on WizardCanvas.

import RefreshIcon from '@mui/icons-material/Refresh';
import UndoIcon from '@mui/icons-material/Undo';
import { Alert, Box, Button, Stack, TextField, Typography } from '@mui/material';
import type { Dispatch, SetStateAction } from 'react';

import { couplingLabel, de } from '@/locales';
import type { BboxIn, BboxOut, CouplingHeight, GuideConfig, StrokePoint } from '@/lib/api';
import type { GuideValues } from '../wizardTypes';

const COUPLING_OPTIONS: CouplingHeight[] = ['baseline', 'midband', 'ascender', 'descender'];

export function TraceStep({
  bbox,
  strokes,
  setStrokes,
  savablePoints,
  hasCanonical,
  busy,
  guideVals,
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
  saveTrace: () => Promise<void>;
  resample: () => Promise<void>;
  updateBboxField: (patch: Partial<BboxIn>) => Promise<void>;
  updateGuides: (patch: Partial<GuideConfig>) => Promise<void>;
}) {
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
        <Button size="small" variant="contained" disabled={savablePoints < 2 || busy} onClick={saveTrace}>
          {de.wizard.trace.save}
        </Button>
      </Stack>
      {hasCanonical && strokes.length === 0 && <Alert severity="success" variant="outlined">{de.wizard.trace.saved}</Alert>}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TextField
          label={de.wizard.trace.anchorsLabel}
          type="number"
          size="small"
          value={bbox.n_anchors}
          onChange={(e) => updateBboxField({ n_anchors: Math.max(4, Number(e.target.value)) })}
          sx={{ flex: 1 }}
        />
        <Button size="small" variant="outlined" startIcon={<RefreshIcon />} disabled={!hasCanonical || busy} onClick={resample}>
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
