// Minimal dark MUI theme. Same palette spirit as the v1 plain-CSS styles:
// black-ish background, warm accent, no flashy gradients.

import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#ffae00' },
    secondary: { main: '#5da8ff' },
    background: { default: '#1c1c1c', paper: '#262626' },
  },
  shape: { borderRadius: 4 },
  components: {
    MuiButton: { defaultProps: { disableElevation: true } },
  },
});
