// One counted figure: the number large, what it counts underneath.
//
// Lifted out of EigenhandView when the page split into its four Unteransichten
// — the counters live on `bestand`, the pen figure on `statistik`, and a
// second hand-rolled copy of the same two Typographys would have drifted the
// moment one of them got a unit.

import { Box, Typography } from '@mui/material';

import { paper } from '@/styles/paper';

export function Stat({ value, label }: { value: number | string; label: string }) {
  return (
    <Box sx={{ minWidth: '5.5rem' }}>
      <Typography variant="h5" sx={{ color: paper.ink, lineHeight: 1.1 }}>
        {value}
      </Typography>
      <Typography variant="caption" sx={{ color: paper.inkSoft }}>
        {label}
      </Typography>
    </Box>
  );
}
