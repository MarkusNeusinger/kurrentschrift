// MUI theme — anyplot's imprint palette transposed onto a neutral sans
// (Roboto/system stack, NOT MonoLisa). Light mode only for now; dark theme
// can be added later if needed.
//
// Discipline (per anyplot's style-guide.md §4.4): brand green is a *signal*
// colour — used on accents, hover states, CTAs. The rest of the chrome is
// warm grayscale on an off-white paper background.

import { createTheme } from '@mui/material/styles';

const ink = {
  // warm-tinted grayscale, anyplot §4.3
  primary: '#1A1A17',
  soft: '#4A4A44',
  muted: '#6B6A63',
  rule: 'rgba(26, 26, 23, 0.10)',
} as const;

const imprint = {
  // anyplot §4.1 — categorical palette + semantic anchors
  green: '#009E73', // brand
  greenDark: '#007A59', // hover / accent-dark
  greenTint: 'rgba(0, 158, 115, 0.12)',
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
    primary: { main: imprint.green, dark: imprint.greenDark, contrastText: '#FFFFFF' },
    secondary: { main: imprint.blue },
    error: { main: imprint.red },
    warning: { main: imprint.amber },
    info: { main: imprint.blue },
    success: { main: imprint.green },
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
  green: imprint.green,
  greenDark: imprint.greenDark,
  greenTint: imprint.greenTint,
  ink,
  surface,
} as const;
