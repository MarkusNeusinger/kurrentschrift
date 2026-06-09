// MUI theme assembly — the "paper & ink" identity, applied site-wide
// (style-guide §8). The expressive paper *texture* (grain + vignette + radial
// gradient) lives in <PaperBackground>; this theme carries the flat colours,
// type and component defaults so every page — landing, quiz, worksheet and the
// admin — shares one look. The only neutral exceptions are the work surfaces
// that need a plain ground (the A4 worksheet preview, the letter crops, the
// chart scan); those paint their own solid background on top.

import { createTheme } from '@mui/material/styles';

import { components } from '@/theme/components';
import { palette } from '@/theme/palette';
import { typography } from '@/theme/typography';

export const theme = createTheme({
  palette,
  shape: { borderRadius: 6 },
  typography,
  components,
});

export { tokens } from '@/theme/tokens';
