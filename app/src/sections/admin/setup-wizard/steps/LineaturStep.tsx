// Schritt 2 · Lineatur — Oberlinie/Unterlinie toggles + the current line
// readout. Grundlinie/Mittellinie are dragged directly on WizardCanvas.

import { Checkbox, FormControlLabel, Stack, Typography } from '@mui/material';

import { de, fmt, LINEATUR_LABELS } from '@/locales';
import type { BboxOut, GuideConfig, SourceOut } from '@/lib/api';
import type { GuideValues } from '../wizardTypes';

export function LineaturStep({
  bbox,
  source,
  guideVals,
  updateGuides,
}: {
  bbox: BboxOut;
  source: SourceOut;
  guideVals: GuideValues;
  updateGuides: (patch: Partial<GuideConfig>) => Promise<void>;
}) {
  const xHeightPx = bbox.baseline_y - bbox.midband_y;
  return (
    <Stack spacing={1.5}>
      <Typography variant="subtitle2">{de.wizard.lineatur.title}</Typography>
      <Typography variant="body2" color="text.secondary">
        {de.wizard.lineatur.bodyIntro} <b style={{ color: '#ff5060' }}>{LINEATUR_LABELS.baseline}</b> {de.wizard.lineatur.bodyAfterBaseline}{' '}
        <b style={{ color: '#c060ff' }}>{LINEATUR_LABELS.midband}</b> {de.wizard.lineatur.bodyAfterMidband}{' '}
        <b>{LINEATUR_LABELS.ascender}</b> {de.wizard.lineatur.bodyAnd} <b>{LINEATUR_LABELS.descender}</b> {de.wizard.lineatur.bodyDerived}{' '}
        ({source.style_ratio.join(':')}).
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {de.wizard.lineatur.body2}
      </Typography>
      <Stack direction="row" spacing={1}>
        <FormControlLabel
          control={<Checkbox size="small" checked={guideVals.showAscender} onChange={(e) => updateGuides({ show_ascender: e.target.checked })} />}
          label={LINEATUR_LABELS.ascender}
          slotProps={{ typography: { variant: 'caption' } }}
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={guideVals.showDescender} onChange={(e) => updateGuides({ show_descender: e.target.checked })} />}
          label={LINEATUR_LABELS.descender}
          slotProps={{ typography: { variant: 'caption' } }}
        />
      </Stack>
      <Typography variant="caption" color="text.secondary">
        {fmt(de.wizard.lineatur.readout, { baseline: bbox.baseline_y, midband: bbox.midband_y, xHeight: xHeightPx })}
      </Typography>
    </Stack>
  );
}
