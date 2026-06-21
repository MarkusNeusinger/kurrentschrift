// HintHeading — a wizard panel's subtitle heading paired with an InfoHint (i)
// that tucks the detailed explanation away, plus an optional trailing action
// (e.g. the Übersicht "Neu schreiben" replay or the preview's refresh button).
// Every step panel leads with this same row, so it lives once here instead of
// being hand-rolled per step. The `title` doubles as the InfoHint popover title.

import { Box, Typography } from '@mui/material';
import type { ReactNode } from 'react';

import { InfoHint } from '@/components/InfoHint';

export function HintHeading({ title, children, action }: { title: string; children: ReactNode; action?: ReactNode }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <Typography variant="subtitle2">{title}</Typography>
      <InfoHint title={title}>{children}</InfoHint>
      {action != null && (
        <>
          <Box sx={{ flex: 1 }} />
          {action}
        </>
      )}
    </Box>
  );
}
