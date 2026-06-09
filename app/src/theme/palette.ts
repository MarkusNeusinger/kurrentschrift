// Palette of the "paper & ink" identity (style-guide §2/§8): aged cream paper
// as the page ground, aged iron-gall brown as the text ink, viridian
// (chromium-oxide green, ~1859) as the single sharp accent. All colour truth
// lives in styles/paper.ts — this file only arranges those tokens into the
// MUI palette plus the small semantic groups the components consume.

import type { PaletteOptions } from '@mui/material/styles';

import { paper, pigment } from '@/styles/paper';

export const ink = {
  // aged iron-gall ink + sepia, from the paper token set
  primary: paper.ink,
  soft: paper.inkSoft,
  muted: paper.sepia,
  rule: 'rgba(36, 26, 16, 0.14)', // warm hairline / A4-preview mat
} as const;

export const imprint = {
  // Brand accent = viridian — the single sharp accent of the "paper & ink"
  // identity (see docs/concepts/style-guide.md §2). The semantic anchors are
  // grounded in the period pigment set (styles/paper.ts `pigment`): vermilion
  // for error, ochre for warning, Prussian blue for info/secondary — the
  // chromolithography palette of period school charts instead of arbitrary
  // modern picks.
  viridian: paper.viridian, // brand
  viridianDark: '#336152', // hover / accent-dark
  viridianTint: 'rgba(64, 130, 109, 0.12)',
  // Ochre text/icon shade where the raw pigment (2.44:1) is too light.
  // (derived for contrast, not a period hex)
  ochreDark: '#a85f17',
  // Prussian blue lift for surfaces where #003153 sinks away.
  // (derived for contrast, not a period hex)
  prussianBlueLight: '#2a4a66',
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
  secondary: { main: pigment.prussianBlue, light: imprint.prussianBlueLight },
  // Oxblood error family (user decision, R1): deep period red with excellent
  // legibility on the cream ground (7.41:1); raw vermilion (Zinnober) stays
  // the light fill/border tone. A deepened-vermilion alternative (#b5301f)
  // was rejected in favour of the calmer, more paper-bound oxblood.
  error: { main: pigment.oxblood, light: pigment.vermilion },
  // Ochre replaces the old amber (#DDCC77 was 1.17:1 on cream — invisible).
  warning: { main: pigment.ochre, dark: imprint.ochreDark },
  info: { main: pigment.prussianBlue, light: imprint.prussianBlueLight },
  // success / "correct" also runs on viridian — one accent across the site; the
  // quiz still pairs it with red for the wrong-answer state, so the two stay
  // distinguishable.
  success: { main: imprint.viridian, dark: imprint.viridianDark },
  background: { default: surface.page, paper: surface.card },
  text: { primary: ink.primary, secondary: ink.soft, disabled: ink.muted },
  divider: paper.line,
};
