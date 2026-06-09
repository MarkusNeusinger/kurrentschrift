// Schritt 5 · Übersicht & Freigabe — Diagnose link, the unified-vs-split
// (applyAll) choice and the lock summary. The lock button itself sits in the
// wizard footer ("Abschließen & sperren").

import VisibilityIcon from '@mui/icons-material/Visibility';
import { Alert, Box, Button, FormControlLabel, Radio, RadioGroup, Stack, Typography } from '@mui/material';

import { isLetterSplit } from '@/domain/glyphs';
import { de, fmt, POSITION_LABEL } from '@/locales';
import type { KnownGlyph } from '@/domain/glyphs';
import type { BboxOut } from '@/lib/api';

export function OverviewStep({
  glyphKey,
  known,
  hasCanonical,
  applyAll,
  setApplyAll,
  bboxesByKey,
  openDiagnose,
}: {
  glyphKey: string;
  known: KnownGlyph;
  hasCanonical: boolean;
  applyAll: boolean;
  setApplyAll: (v: boolean) => void;
  bboxesByKey: Record<string, BboxOut>;
  openDiagnose: (key: string) => void;
}) {
  return (
    <Stack spacing={2} sx={{ maxWidth: 640 }}>
      <Typography variant="subtitle2">{de.wizard.overview.title}</Typography>
      <Typography variant="body2" color="text.secondary">
        {de.wizard.overview.bodyBeforeBold} <b>{de.wizard.overview.bodyBold}</b> {de.wizard.overview.bodyAfterBold}
      </Typography>
      {hasCanonical ? (
        <Button variant="outlined" startIcon={<VisibilityIcon />} onClick={() => openDiagnose(glyphKey)} sx={{ alignSelf: 'flex-start' }}>
          {de.wizard.overview.openDiagnose}
        </Button>
      ) : (
        <Alert severity="warning">{de.wizard.overview.noTraceYet}</Alert>
      )}
      <Box>
        <Typography variant="subtitle2" gutterBottom>
          {de.wizard.overview.positionsHeading}
        </Typography>
        <RadioGroup value={applyAll ? 'unified' : 'split'} onChange={(e) => setApplyAll(e.target.value === 'unified')}>
          <FormControlLabel value="unified" control={<Radio />} label={de.wizard.overview.unifiedOption} />
          <FormControlLabel value="split" control={<Radio />} label={fmt(de.wizard.overview.splitOption, { position: POSITION_LABEL[known.position] })} />
        </RadioGroup>
        <Typography variant="caption" color="text.secondary" component="div">
          {applyAll
            ? de.wizard.overview.unifiedCaption
            : fmt(de.wizard.overview.splitCaption, { position: POSITION_LABEL[known.position] })}
        </Typography>
        {isLetterSplit(glyphKey, bboxesByKey) && applyAll && (
          <Alert severity="warning" sx={{ mt: 1 }}>
            {de.wizard.overview.overwriteBeforeBold} <b>{de.wizard.overview.overwriteBold}</b> {de.wizard.overview.overwriteAfterBold}
          </Alert>
        )}
      </Box>
      <Typography variant="caption" color="text.secondary">
        {de.wizard.overview.lockCaption}
      </Typography>
    </Stack>
  );
}
