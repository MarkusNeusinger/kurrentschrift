// EB Garamond carries the body/UI (style-guide §3 Phase-B dial), so the whole
// site shares the landing's editorial serif. Display headlines opt into
// Playfair Display locally via the `display` token where they want more character.

import type { TypographyVariantsOptions } from '@mui/material/styles';

import { garamond } from '@/styles/paper';

// One shared type ladder. Calibrated to a 19px body (style-guide §3 "Lesbarkeit
// vor Epoche"): EB Garamond's low x-height reads small, so the base sits at 19px
// and the whole scale is set explicitly here — h1–h6 used to carry no fontSize
// (MUI defaults), which is why sections grew their own ad-hoc clamps. Headlines
// opt into Playfair via the `display` font token + `letterpress` LOCALLY; their
// SIZES come from these variants. The fluid clamps keep one responsive ladder
// instead of per-page breakpoint objects. Carries across every page — public and
// admin — since the theme is the single typographic source.
export const typography: TypographyVariantsOptions = {
  fontFamily: garamond,
  h1: { fontWeight: 400, letterSpacing: '-0.01em', lineHeight: 1.12, fontSize: 'clamp(2.4rem, 1.7rem + 2.8vw, 3.1rem)' },
  h2: { fontWeight: 400, letterSpacing: '-0.01em', lineHeight: 1.16, fontSize: 'clamp(2.05rem, 1.5rem + 2.2vw, 2.6rem)' },
  h3: { fontWeight: 400, lineHeight: 1.2, fontSize: 'clamp(1.75rem, 1.4rem + 1.5vw, 2.15rem)' },
  h4: { fontWeight: 400, lineHeight: 1.25, fontSize: 'clamp(1.5rem, 1.25rem + 1vw, 1.85rem)' },
  h5: { fontWeight: 500, lineHeight: 1.3, fontSize: '1.45rem' },
  h6: { fontWeight: 500, lineHeight: 1.4, fontSize: '1.25rem' },
  body1: { fontSize: '1.1875rem', lineHeight: 1.6 },
  body2: { fontSize: '1.0625rem', lineHeight: 1.6 },
  subtitle1: { fontSize: '1.1875rem', lineHeight: 1.5 },
  subtitle2: { fontSize: '1.0625rem', lineHeight: 1.5 },
  caption: { fontSize: '0.875rem', lineHeight: 1.55 },
  button: { textTransform: 'none', fontWeight: 500, letterSpacing: 0 },
  overline: { letterSpacing: '0.12em', fontWeight: 500, fontSize: '0.8125rem' },
};
