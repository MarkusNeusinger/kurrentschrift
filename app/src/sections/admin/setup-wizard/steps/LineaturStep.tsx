// Schritt 2 · Lineatur — Oberlinie/Unterlinie toggles + the current line
// readout. Grundlinie/Mittellinie are dragged directly on WizardCanvas.

import { Checkbox, FormControlLabel, Stack, Typography } from '@mui/material';

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
      <Typography variant="subtitle2">Schritt 2 · Lineatur</Typography>
      <Typography variant="body2" color="text.secondary">
        Die <b style={{ color: '#ff5060' }}>Grundlinie</b> (auf der die Mittellänge aufsitzt)
        und die <b style={{ color: '#c060ff' }}>Mittellinie</b> (Oberkante der Mittellänge)
        direkt im Bild an die richtige Höhe ziehen. <b>Oberlinie</b> und <b>Unterlinie</b> (grau)
        ergeben sich automatisch aus dem Stil-Verhältnis ({source.style_ratio.join(':')}).
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Diese vier Linien sind das Lineatur-System (Zonen: Oberlänge · Mittellänge · Unterlänge)
        und der Bezug für alle weiteren Maße.
      </Typography>
      <Stack direction="row" spacing={1}>
        <FormControlLabel
          control={<Checkbox size="small" checked={guideVals.showAscender} onChange={(e) => updateGuides({ show_ascender: e.target.checked })} />}
          label="Oberlinie"
          slotProps={{ typography: { variant: 'caption' } }}
        />
        <FormControlLabel
          control={<Checkbox size="small" checked={guideVals.showDescender} onChange={(e) => updateGuides({ show_descender: e.target.checked })} />}
          label="Unterlinie"
          slotProps={{ typography: { variant: 'caption' } }}
        />
      </Stack>
      <Typography variant="caption" color="text.secondary">
        Grundlinie {bbox.baseline_y} · Mittellinie {bbox.midband_y} · Mittellänge (x-Höhe) {xHeightPx}px
      </Typography>
    </Stack>
  );
}
