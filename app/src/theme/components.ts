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
  MuiToggleButton: {
    styleOverrides: {
      // MUI's default unselected toggle text is neutral action.active alpha-black
      // (~#6f6b62, only 4.35:1 on the card and off the warm "one ink" palette).
      // Use soft ink instead — legible (~9.7:1) and on-identity; the selected
      // state keeps its own fill, the disabled state its own dimming.
      root: ({ theme }) => ({ color: theme.palette.text.secondary }),
    },
  },
};
