// Die Tintentreue as one chip — the ONE place a step is given a colour.
//
// Shared by the Nachfahr-Zeile and the gallery tile since the crop tiles got
// their verdict back (§7.2): two surfaces showing the same judgement in two
// colour schemes is the drift the Ampel replaced the free-standing warning
// chip to end.
//
// The step is the server's own German word and is never translated here. The
// grey state takes the default chip rather than a fourth colour, because „nicht
// beurteilt" is the ABSENCE of a measurement and not a fourth step — and its
// reason always travels beside the chip, so nothing here is carried by hue
// alone (design-system §2, Idee 19).
//
// `flexShrink: 0` is not cosmetic: in the narrow chip box of a phone row a MUI
// chip shrinks below its own text and ellipsises it, so „folgt nicht" once
// shipped as „folgt …" — the one word that carries the verdict, cut at exactly
// the width this list is read at on the tablet's narrow side (measured 390 px).

import { Chip } from '@mui/material';

import type { EigenhandTintentreue, EigenhandTintentreueStufe } from '@/lib/api';

const STUFE_COLOR: Record<EigenhandTintentreueStufe, 'success' | 'warning' | 'error' | 'default'> = {
  folgt: 'success',
  'folgt teils': 'warning',
  'folgt nicht': 'error',
  'nicht beurteilt': 'default',
};

/** One STEP as a chip, without a box behind it — the statistik view counts
 * steps and has no single verdict to hand over, and a second colour table
 * there is exactly the drift this file exists to prevent. */
export function StufeChip({ stufe }: { stufe: EigenhandTintentreueStufe }) {
  return (
    <Chip
      size="small"
      color={STUFE_COLOR[stufe]}
      variant={stufe === 'nicht beurteilt' ? 'outlined' : 'filled'}
      label={stufe}
      sx={{ flexShrink: 0 }}
    />
  );
}

export function AmpelChip({ urteil }: { urteil: EigenhandTintentreue }) {
  return <StufeChip stufe={urteil.stufe} />;
}
