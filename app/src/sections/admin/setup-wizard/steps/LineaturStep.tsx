// Step 2 "Lineatur & Schräglage" — the whole writing grid in one step:
// Oberlinie/Unterlinie toggles + the current line readout, then (below a divider)
// the folded-in Schräglage controls (SlantStep). Grundlinie/Mittellinie are
// dragged directly on WizardCanvas, as are the slant guides.

import { Checkbox, Divider, FormControlLabel, Stack, Typography } from '@mui/material';

import { de, fmt, LINEATUR_LABELS } from '@/locales/admin';
import type { BboxOut, GuideConfig, SourceOut } from '@/lib/api';
import type { GuideValues } from '../wizardTypes';
import { HintHeading } from './HintHeading';
import { SlantStep } from './SlantStep';

export function LineaturStep({
  bbox,
  source,
  guideVals,
  updateGuides,
  addSlantLine,
  removeSlantLine,
}: {
  bbox: BboxOut;
  source: SourceOut;
  guideVals: GuideValues;
  updateGuides: (patch: Partial<GuideConfig>) => Promise<void>;
  addSlantLine: () => void;
  removeSlantLine: (i: number) => void;
}) {
  const xHeightPx = bbox.baseline_y - bbox.midband_y;
  return (
    <Stack spacing={2}>
      <Stack spacing={1.5}>
        <HintHeading title={de.wizard.lineatur.title}>
          <Typography variant="body2" gutterBottom>
            {de.wizard.lineatur.bodyIntro} <b style={{ color: '#ff5060' }}>{LINEATUR_LABELS.baseline}</b> {de.wizard.lineatur.bodyAfterBaseline}{' '}
            <b style={{ color: '#c060ff' }}>{LINEATUR_LABELS.midband}</b> {de.wizard.lineatur.bodyAfterMidband}{' '}
            <b>{LINEATUR_LABELS.ascender}</b> {de.wizard.lineatur.bodyAnd} <b>{LINEATUR_LABELS.descender}</b> {de.wizard.lineatur.bodyDerived}{' '}
            ({source.style_ratio.join(':')}).
          </Typography>
          <Typography variant="body2">{de.wizard.lineatur.body2}</Typography>
        </HintHeading>
        <Typography variant="body2" color="text.secondary">
          <b style={{ color: '#ff5060' }}>{LINEATUR_LABELS.baseline}</b> {de.wizard.lineatur.bodyAnd}{' '}
          <b style={{ color: '#c060ff' }}>{LINEATUR_LABELS.midband}</b> {de.wizard.lineatur.leadAction}
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
      <Divider />
      <SlantStep guideVals={guideVals} updateGuides={updateGuides} addSlantLine={addSlantLine} removeSlantLine={removeSlantLine} />
    </Stack>
  );
}
