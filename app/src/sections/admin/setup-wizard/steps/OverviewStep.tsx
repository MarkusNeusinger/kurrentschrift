// Step 4 "Übersicht & Freigabe" — two columns. Left: the Diagnose link and the
// lock summary. Right: the verification panel (OverviewVerify) — crop · written
// · overlaid + the score criteria, so it's visible at a glance that the
// synthesised form fits before locking. The lock button itself sits in the
// wizard footer.

import VisibilityIcon from '@mui/icons-material/Visibility';
import { Alert, Box, Button, Stack, Typography } from '@mui/material';

import { de } from '@/locales/admin';
import type { TracePreviewOut } from '@/lib/api';
import { HintHeading } from './HintHeading';
import { OverviewVerify } from './OverviewVerify';

export function OverviewStep({
  glyphKey,
  hasCanonical,
  openDiagnose,
  cropCacheBust,
  nAnchors,
  preview,
  previewBusy,
  computePreview,
}: {
  glyphKey: string;
  hasCanonical: boolean;
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
