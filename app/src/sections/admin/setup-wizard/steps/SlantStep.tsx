// Schritt 3 · Schräge — the shared slant angle + add/remove of the individually
// placed slant lines. The green drag handles live on WizardCanvas.

import AddIcon from '@mui/icons-material/Add';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import { Box, Button, Chip, IconButton, Stack, TextField, Typography } from '@mui/material';

import type { GuideConfig } from '@/lib/api';
import { SLANT_COLOR } from '../wizardTypes';
import type { GuideValues } from '../wizardTypes';

export function SlantStep({
  guideVals,
  updateGuides,
  addSlantLine,
  removeSlantLine,
}: {
  guideVals: GuideValues;
  updateGuides: (patch: Partial<GuideConfig>) => Promise<void>;
  addSlantLine: () => void;
  removeSlantLine: (i: number) => void;
}) {
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
}
