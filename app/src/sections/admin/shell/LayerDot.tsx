// The colour swatch on a layer toggle — the same colour that layer draws with,
// so the button doubles as the legend for the line in the crop. Shared by the
// Wörter detail and the Übergänge drill panel.

import { Box } from '@mui/material';

export const LayerDot = ({ color }: { color: string }) => (
  <Box
    component="span"
    aria-hidden
    sx={{ width: 9, height: 9, borderRadius: '50%', bgcolor: color, mr: 0.75, flexShrink: 0 }}
  />
);
