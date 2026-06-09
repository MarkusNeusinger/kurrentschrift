// Schritt 4 · Weg (Ductus) — stroke undo/discard/save, n_anchors + resample,
// and the entry/exit coupling heights. The strokes are drawn on WizardCanvas.

import RefreshIcon from '@mui/icons-material/Refresh';
import UndoIcon from '@mui/icons-material/Undo';
import { Alert, Box, Button, Stack, TextField, Typography } from '@mui/material';
import type { Dispatch, SetStateAction } from 'react';

import { couplingLabel } from '@/lib/labels';
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
      <Typography variant="subtitle2">Schritt 4 · Weg (Ductus)</Typography>
      <Typography variant="body2" color="text.secondary">
        Den Buchstaben in Schreibrichtung mit dem Stift (S-Pen) oder der Maus nachziehen — das
        ist der Ductus, die eigentliche Vorlage über der Loth-Geometrie.
      </Typography>
      <Typography variant="body2" color="text.secondary">
        <b>Jedes Absetzen beginnt einen neuen Strich</b> — zwischen den Strichen wird keine
        Verbindungslinie gezogen. Beim <b>u</b> also erst den ersten Abstrich, absetzen, dann den
        zweiten — nacheinander, nicht in einem Zug.
      </Typography>
      <Stack direction="row" spacing={1}>
        <Button size="small" startIcon={<UndoIcon />} disabled={strokes.length === 0} onClick={() => setStrokes((s) => s.slice(0, -1))}>
          Letzter Strich ({strokes.length})
        </Button>
        <Button size="small" color="inherit" disabled={strokes.length === 0} onClick={() => setStrokes([])}>
          Alles verwerfen
        </Button>
        <Button size="small" variant="contained" disabled={savablePoints < 2 || busy} onClick={saveTrace}>
          Weg speichern
        </Button>
      </Stack>
      {hasCanonical && strokes.length === 0 && <Alert severity="success" variant="outlined">Weg gespeichert. Weiter zur Übersicht.</Alert>}
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
}
