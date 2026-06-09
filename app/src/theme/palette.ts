// Palette of the "paper & ink" identity (style-guide §2/§8): aged cream paper
// as the page ground, aged iron-gall brown as the text ink, viridian
// (chromium-oxide green, ~1859) as the single sharp accent. All colour truth
// lives in styles/paper.ts — this file only arranges those tokens into the
// MUI palette plus the small semantic groups the components consume.

import type { PaletteOptions } from '@mui/material/styles';

import { paper } from '@/styles/paper';

export const ink = {
  // aged iron-gall ink + sepia, from the paper token set
  primary: paper.ink,
  soft: paper.inkSoft,
  muted: paper.sepia,
  rule: 'rgba(36, 26, 16, 0.14)', // warm hairline / A4-preview mat
} as const;

export const imprint = {
  // Brand accent = viridian — the single sharp accent of the "paper & ink"
  // identity (see docs/concepts/style-guide.md §2). Semantic anchors (red/amber/
  // blue) stay so quiz feedback and warnings read clearly against the cream.
  viridian: paper.viridian, // brand
  viridianDark: '#336152', // hover / accent-dark
  viridianTint: 'rgba(64, 130, 109, 0.12)',
  red: '#AE3030',
  amber: '#DDCC77',
  blue: '#4467A3',
} as const;

export const surface = {
  // Cream page ground; panels/cards sit on a lighter sheet (paper.hi) so an
  // outlined Paper reads as a raised leaf over the page rather than a white box.
  page: paper.bg,
  card: paper.hi,
  elevated: '#f4ecda',
} as const;

export const palette: PaletteOptions = {
  mode: 'light',
  primary: { main: imprint.viridian, dark: imprint.viridianDark, contrastText: '#FFFFFF' },
  secondary: { main: imprint.blue },
  error: { main: imprint.red },
  warning: { main: imprint.amber },
  info: { main: imprint.blue },
  // success / "correct" also runs on viridian — one accent across the site; the
  // quiz still pairs it with red for "falsch", so the two stay distinguishable.
  success: { main: imprint.viridian, dark: imprint.viridianDark },
  background: { default: surface.page, paper: surface.card },
  text: { primary: ink.primary, secondary: ink.soft, disabled: ink.muted },
  divider: paper.line,
};
