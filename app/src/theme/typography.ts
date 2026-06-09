// EB Garamond carries the body/UI (style-guide §3 Phase-B dial), so the whole
// site shares the landing's editorial serif. Display headlines opt into
// Cormorant locally via the `display` token where they want more character.

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
  button: { textTransform: 'none', fontWeight: 500, letterSpacing: 0 },
  overline: { letterSpacing: '0.12em', fontWeight: 500 },
};
