// The swatch on a layer toggle — the same colour AND the same stroke style
// that layer draws with, so the button doubles as the legend for the line in
// the crop. Shared by the Wörter detail and the Übergänge drill panel.
//
// It draws a short LINE rather than a dot, and that is the point: two of the
// overlay hues are one colour for a reader with a red-green deficiency
// (styles/paper.ts, Ebenen-Token), so colour alone cannot carry which line is
// which. Colour, stroke style and the label beside it are three channels for
// one distinction — the Strichart-Regel of design-system.md §2.

import { Box } from '@mui/material';

const SWATCH = 18; // px of line — two dash cycles at the factors the tokens use
const WEIGHT = 2.5; // px; the dash factors are multiples of the line's own width

export const LayerDot = ({ color, dash }: { color: string; dash?: readonly number[] | null }) => (
  <Box
    component="svg"
    aria-hidden
    viewBox={`0 0 ${SWATCH} ${WEIGHT}`}
    sx={{ width: SWATCH, height: WEIGHT, mr: 0.75, flexShrink: 0, overflow: 'visible' }}
  >
    <line
      x1={0}
      x2={SWATCH}
      y1={WEIGHT / 2}
      y2={WEIGHT / 2}
      stroke={color}
      strokeWidth={WEIGHT}
      strokeDasharray={dash ? dash.map((d) => d * WEIGHT).join(' ') : undefined}
      strokeLinecap="butt"
    />
  </Box>
);
