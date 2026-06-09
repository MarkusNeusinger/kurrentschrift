// Step 3 "Schräge" — the shared slant angle + add/remove of the individually
// placed slant lines. The green drag handles live on WizardCanvas.

import AddIcon from '@mui/icons-material/Add';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import { Box, Button, Chip, IconButton, Stack, TextField, Typography } from '@mui/material';

import { de } from '@/locales';
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
      <Typography variant="subtitle2">{de.wizard.slant.title}</Typography>
      <Typography variant="body2" color="text.secondary">
        {de.wizard.slant.body1}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {de.wizard.slant.body2BeforeBold} <b>{de.wizard.slant.body2Bold}</b> {de.wizard.slant.body2AfterBold}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TextField label={de.wizard.slant.angleLabel} type="number" size="small" value={Math.round(guideVals.slantDeg)} onChange={(e) => {
            // Guard NaN (cleared field) — it would serialize to null and corrupt the guides.
            const v = Number(e.target.value);
            if (Number.isFinite(v)) updateGuides({ slant_deg: v });
          }} slotProps={{ input: { sx: { color: SLANT_COLOR, fontFamily: 'monospace' }, endAdornment: '°' } }} sx={{ flex: 1 }} />
        <IconButton size="small" onClick={() => updateGuides({ slant_deg: Math.round(guideVals.slantDeg) + 1 })} sx={{ color: SLANT_COLOR }}>
          <ArrowUpwardIcon fontSize="small" />
        </IconButton>
        <IconButton size="small" onClick={() => updateGuides({ slant_deg: Math.round(guideVals.slantDeg) - 1 })} sx={{ color: SLANT_COLOR }}>
          <ArrowDownwardIcon fontSize="small" />
        </IconButton>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="caption" color="text.secondary">
          {de.wizard.slant.linesHeading} ({guideVals.slantXs.length})
        </Typography>
        <Button size="small" startIcon={<AddIcon />} onClick={addSlantLine}>
          {de.wizard.slant.addLine}
        </Button>
      </Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {guideVals.slantXs.map((_, i) => (
          <Chip
            key={i}
            size="small"
            label={`${de.wizard.slant.lineChip} ${i + 1}`}
            onDelete={guideVals.slantXs.length > 1 ? () => removeSlantLine(i) : undefined}
            sx={{ borderColor: SLANT_COLOR }}
            variant="outlined"
          />
        ))}
      </Box>
      <Typography variant="caption" color="text.secondary">
        {de.wizard.slant.dragHint}
      </Typography>
    </Stack>
  );
}
