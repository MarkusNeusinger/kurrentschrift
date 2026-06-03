// MUI theme — anyplot's imprint palette transposed onto a neutral sans
// (Roboto/system stack, NOT MonoLisa). Light mode only for now; dark theme
// can be added later if needed.
//
// Discipline (per anyplot's style-guide.md §4.4): the brand accent (viridian) is
// a *signal* colour — used on accents, hover states, CTAs. The rest of the chrome
// is warm grayscale on an off-white paper background.

import { createTheme } from '@mui/material/styles';

const ink = {
  // warm-tinted grayscale, anyplot §4.3
  primary: '#1A1A17',
  soft: '#4A4A44',
  muted: '#6B6A63',
  rule: 'rgba(26, 26, 23, 0.10)',
} as const;

const imprint = {
  // Brand accent = viridian (chromium-oxide green, ~1859) — the single sharp accent
  // of the "paper & ink" identity (see docs/concepts/style-guide.md §2). Replaces
  // anyplot's emerald #009E73, which the guide rejects (reads digital, too light as
  // body text). Semantic anchors (red/amber/blue) stay.
  viridian: '#40826d', // brand
  viridianDark: '#336152', // hover / accent-dark
  viridianTint: 'rgba(64, 130, 109, 0.12)',
  red: '#AE3030',
  amber: '#DDCC77',
  blue: '#4467A3',
} as const;

const surface = {
  // anyplot §4.2
  page: '#FAF8F1',
  card: '#FAF8F1',
  elevated: '#FFFDF6',
} as const;

const sansStack =
  '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", "Helvetica Neue", sans-serif';

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
    divider: ink.rule,
  },
  shape: { borderRadius: 6 },
  typography: {
    fontFamily: sansStack,
    h1: { fontWeight: 300, letterSpacing: '-0.02em' },
    h2: { fontWeight: 300, letterSpacing: '-0.015em' },
    h3: { fontWeight: 300, letterSpacing: '-0.01em' },
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
