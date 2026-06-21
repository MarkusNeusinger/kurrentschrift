// "Schräglage" — the shared slant angle + add/remove of the individually placed
// slant lines. The green drag handles live on WizardCanvas. Folded into the
// Lineatur step (rendered as a sub-section by LineaturStep), so it carries a
// sub-heading rather than a step number; the slant guides show on 'lineatur'.

import AddIcon from '@mui/icons-material/Add';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import { Box, Button, Chip, IconButton, Stack, TextField, Typography } from '@mui/material';
import { useState } from 'react';

import { de } from '@/locales';
import type { GuideConfig } from '@/lib/api';
import { SLANT_COLOR } from '../wizardTypes';
import type { GuideValues } from '../wizardTypes';
import { HintHeading } from './HintHeading';

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
  // While the field is being edited the raw text lives here, so it can be
  // cleared and retyped; valid values still commit per keystroke (live preview
  // of the slant lines), and blur snaps back to the committed angle.
  const [angleDraft, setAngleDraft] = useState<string | null>(null);

  return (
    <Stack spacing={1.5}>
      <HintHeading title={de.wizard.slant.title}>
        <Typography variant="body2" gutterBottom>
          {de.wizard.slant.body1}
        </Typography>
        <Typography variant="body2">
          {de.wizard.slant.body2BeforeBold} <b>{de.wizard.slant.body2Bold}</b> {de.wizard.slant.body2AfterBold}
        </Typography>
      </HintHeading>
      <Typography variant="body2" color="text.secondary">
        {de.wizard.slant.lead}
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TextField label={de.wizard.slant.angleLabel} type="number" size="small" value={angleDraft ?? Math.round(guideVals.slantDeg)} onChange={(e) => {
            const raw = e.target.value;
            setAngleDraft(raw);
            const v = Number(raw);
            if (raw !== '' && Number.isFinite(v)) void updateGuides({ slant_deg: v });
          }} onBlur={() => setAngleDraft(null)} slotProps={{ input: { sx: { color: SLANT_COLOR, fontFamily: 'monospace' }, endAdornment: '°' } }} sx={{ flex: 1 }} />
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
            onDelete={() => removeSlantLine(i)}
            sx={{ borderColor: SLANT_COLOR }}
            variant="outlined"
          />
        ))}
      </Box>
    </Stack>
  );
}
