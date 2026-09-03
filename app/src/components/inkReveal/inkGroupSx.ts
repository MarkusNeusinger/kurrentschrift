// ── Iron-gall settle ───────────────────────────────────────────────────────
// German school ink wrote blue-black and oxidized to near-black (Reichs-
// Tintenprüfung 1888/1912) — compressed here from weeks to seconds after the
// write-in completes. Knowingly expressive synthesis. Two keyframes: glyph/sheet
// age only their fill; a word also ages the stroke (its connectors are stroked).
//
// Beside `index.tsx` rather than in it: this is the one export of the ink-reveal
// set that is not a component, and a module that mixes the two takes no
// Fast-Refresh update (react-refresh/only-export-components).
import { keyframes, type SxProps, type Theme } from '@mui/material';

import { inkState } from '@/styles/paper';

const inkSettleFill = keyframes`from { fill: ${inkState.fresh}; } to { fill: ${inkState.oxidized}; }`;
const inkSettleFillStroke = keyframes`
  from { fill: ${inkState.fresh}; stroke: ${inkState.fresh}; }
  to { fill: ${inkState.oxidized}; stroke: ${inkState.oxidized}; }
`;

// The `sx` for the filled-ink group: hold the fresh (or fixed inkColor) tone,
// then play the settle once, `writeEndMs` after mount. A fixed `inkColor` (the
// quiz comparison's red/black) skips the settle and holds one tone.
export function inkGroupSx(opts: {
  animate: boolean;
  writeEndMs: number;
  settleMs: number;
  inkColor?: string;
  // Age the stroke too (word connectors), not just the fill.
  withStroke?: boolean;
}): SxProps<Theme> {
  const { animate, writeEndMs, settleMs, inkColor, withStroke } = opts;
  const tone = inkColor ?? (animate ? inkState.fresh : inkState.oxidized);
  const kf = withStroke ? inkSettleFillStroke : inkSettleFill;
  return {
    fill: tone,
    ...(withStroke ? { stroke: tone } : {}),
    animation: animate && !inkColor ? `${kf} ${settleMs}ms ease ${writeEndMs}ms forwards` : undefined,
  };
}
