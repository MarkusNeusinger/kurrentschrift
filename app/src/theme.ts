// MUI theme — the "paper & ink" identity, applied site-wide (style-guide §8).
// Aged cream paper as the page ground, aged iron-gall brown as the text ink,
// EB Garamond as the body/UI face, viridian (chromium-oxide green, ~1859) as the
// single sharp accent. The expressive paper *texture* (grain + vignette + radial
// gradient) lives in <PaperBackground>; this theme carries the flat colours, type
// and component defaults so every page — landing, quiz, worksheet and the admin —
// shares one look. The only neutral exceptions are the work surfaces that need a
// plain ground (the A4 worksheet preview, the letter crops, the chart scan); those
// paint their own solid background on top.
//
// The palette tokens are sourced from styles/paper.ts so the theme and the
// landing's expressive surfaces never drift apart.

import { createTheme } from '@mui/material/styles';
import { garamond, paper } from './styles/paper';

const ink = {
  // aged iron-gall ink + sepia, from the paper token set
  primary: paper.ink,
  soft: paper.inkSoft,
  muted: paper.sepia,
  rule: 'rgba(36, 26, 16, 0.14)', // warm hairline / A4-preview mat
} as const;

const imprint = {
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

const surface = {
  // Cream page ground; panels/cards sit on a lighter sheet (paper.hi) so an
  // outlined Paper reads as a raised leaf over the page rather than a white box.
  page: paper.bg,
  card: paper.hi,
  elevated: '#f4ecda',
} as const;

export const theme = createTheme({
  palette: {
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
  },
  shape: { borderRadius: 6 },
  typography: {
    // EB Garamond carries the body/UI now (style-guide §3 Phase-B dial), so the
    // whole site shares the landing's editorial serif. Display headlines opt into
    // Cormorant locally via the `display` token where they want more character.
    fontFamily: garamond,
    h1: { fontWeight: 400, letterSpacing: '-0.01em' },
    h2: { fontWeight: 400, letterSpacing: '-0.01em' },
    h3: { fontWeight: 400 },
    h4: { fontWeight: 400 },
    h5: { fontWeight: 500 },
    h6: { fontWeight: 500 },
    button: { textTransform: 'none', fontWeight: 500, letterSpacing: 0 },
    overline: { letterSpacing: '0.12em', fontWeight: 500 },
  },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 4 },
      },
    },
    MuiLink: {
      defaultProps: { underline: 'hover' },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none' },
      },
    },
  },
});

// Re-exported tokens for components that want anyplot-style accents without
// pulling in @mui/material/styles directly. Keep this list small; if you
// reach for something not here, add it deliberately rather than re-exporting
// the entire object.
export const tokens = {
  viridian: imprint.viridian,
  viridianDark: imprint.viridianDark,
  viridianTint: imprint.viridianTint,
  ink,
  surface,
} as const;
