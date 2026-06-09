// Re-exported tokens for components that want identity accents without
// pulling in @mui/material/styles directly. Keep this list small; if you
// reach for something not here, add it deliberately rather than re-exporting
// the entire object.

import { imprint, ink, surface } from '@/theme/palette';

export const tokens = {
  viridian: imprint.viridian,
  viridianDark: imprint.viridianDark,
  viridianTint: imprint.viridianTint,
  ink,
  surface,
} as const;
