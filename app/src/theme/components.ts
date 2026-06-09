// MUI component defaults/overrides. Deliberately tiny — only the three
// components the identity actually adjusts. Resist the file-per-override
// pattern until this outgrows a single screen.

import type { Components, Theme } from '@mui/material/styles';

export const components: Components<Theme> = {
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
};
