// Step 4 "Übersicht & Freigabe" — two columns. Left: the unified-vs-split
// (applyAll) choice, the Diagnose link and the lock summary. Right: the
// verification panel (OverviewVerify) — crop · written · overlaid + the score
// criteria, so it's visible at a glance that the synthesised form fits before
// locking. The lock button itself sits in the wizard footer.

import VisibilityIcon from '@mui/icons-material/Visibility';
import { Alert, Box, Button, FormControlLabel, Radio, RadioGroup, Stack, Typography } from '@mui/material';

import { isLetterSplit } from '@/domain/glyphs';
import { de, fmt, POSITION_LABEL } from '@/locales/admin';
import type { KnownGlyph } from '@/domain/glyphs';
import type { BboxOut, TracePreviewOut } from '@/lib/api';
import { HintHeading } from './HintHeading';
import { OverviewVerify } from './OverviewVerify';

export function OverviewStep({
  glyphKey,
  known,
  hasCanonical,
  applyAll,
  setApplyAll,
  bboxesByKey,
  openDiagnose,
  cropCacheBust,
  nAnchors,
  preview,
  previewBusy,
  computePreview,
}: {
  glyphKey: string;
  known: KnownGlyph;
  hasCanonical: boolean;
  applyAll: boolean;
  setApplyAll: (v: boolean) => void;
  bboxesByKey: Record<string, BboxOut>;
  openDiagnose: (key: string) => void;
  cropCacheBust?: number;
  nAnchors?: number;
  preview: TracePreviewOut | null;
  previewBusy: boolean;
  computePreview: (nAnchors: number) => Promise<void>;
}) {
  return (
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={{ xs: 2, md: 4 }} sx={{ alignItems: 'flex-start' }}>
      <Stack spacing={2} sx={{ flex: 1, minWidth: 0, maxWidth: 560 }}>
        <HintHeading title={de.wizard.overview.title}>
          <Typography variant="body2" gutterBottom>
            {de.wizard.overview.bodyBeforeBold} <b>{de.wizard.overview.bodyBold}</b> {de.wizard.overview.bodyAfterBold}
          </Typography>
          <Typography variant="body2">{de.wizard.overview.lockCaption}</Typography>
        </HintHeading>
        {hasCanonical ? (
          <Button variant="outlined" startIcon={<VisibilityIcon />} onClick={() => openDiagnose(glyphKey)} sx={{ alignSelf: 'flex-start' }}>
            {de.wizard.overview.openDiagnose}
          </Button>
        ) : (
          <Alert severity="warning">{de.wizard.overview.noTraceYet}</Alert>
        )}
        <Box>
          <Box sx={{ mb: 0.5 }}>
            <HintHeading title={de.wizard.overview.positionsHeading}>
              <Typography variant="body2" gutterBottom>
                {de.wizard.overview.unifiedCaption}
              </Typography>
              <Typography variant="body2">{fmt(de.wizard.overview.splitCaption, { position: POSITION_LABEL[known.position] })}</Typography>
            </HintHeading>
          </Box>
          <RadioGroup value={applyAll ? 'unified' : 'split'} onChange={(e) => setApplyAll(e.target.value === 'unified')}>
            <FormControlLabel value="unified" control={<Radio />} label={de.wizard.overview.unifiedOption} />
            <FormControlLabel value="split" control={<Radio />} label={fmt(de.wizard.overview.splitOption, { position: POSITION_LABEL[known.position] })} />
          </RadioGroup>
          {isLetterSplit(glyphKey, bboxesByKey) && applyAll && (
            <Alert severity="warning" sx={{ mt: 1 }}>
              {de.wizard.overview.overwriteBeforeBold} <b>{de.wizard.overview.overwriteBold}</b> {de.wizard.overview.overwriteAfterBold}
            </Alert>
          )}
        </Box>
      </Stack>

      <Box sx={{ width: { xs: '100%', md: 'auto' }, flexShrink: 0 }}>
        <OverviewVerify
          glyphKey={glyphKey}
          cropCacheBust={cropCacheBust}
          hasCanonical={hasCanonical}
          nAnchors={nAnchors}
          preview={preview}
          previewBusy={previewBusy}
          computePreview={computePreview}
        />
      </Box>
    </Stack>
  );
}
