// EB Garamond carries the body/UI (style-guide §3 Phase-B dial), so the whole
// site shares the landing's editorial serif. Display headlines opt into
// Playfair Display locally via the `display` token where they want more character.

import type { TypographyVariantsOptions } from '@mui/material/styles';

import { garamond } from '@/styles/paper';

export const typography: TypographyVariantsOptions = {
  fontFamily: garamond,
  h1: { fontWeight: 400, letterSpacing: '-0.01em' },
  h2: { fontWeight: 400, letterSpacing: '-0.01em' },
  h3: { fontWeight: 400 },
  h4: { fontWeight: 400 },
  h5: { fontWeight: 500 },
  h6: { fontWeight: 500 },
  // Legibility floor (style-guide §3 "Lesbarkeit vor Epoche"): MUI's defaults run
  // small, and EB Garamond's low x-height makes them read smaller still, so the
  // body/caption sizes are lifted explicitly. This carries across every page —
  // public and admin — since the theme is the single typographic source.
  body1: { fontSize: '1.0625rem', lineHeight: 1.6 },
  body2: { fontSize: '0.9375rem', lineHeight: 1.6 },
  subtitle1: { fontSize: '1.0625rem' },
  subtitle2: { fontSize: '0.9375rem' },
  caption: { fontSize: '0.8125rem', lineHeight: 1.55 },
  button: { textTransform: 'none', fontWeight: 500, letterSpacing: 0 },
  overline: { letterSpacing: '0.12em', fontWeight: 500 },
};
