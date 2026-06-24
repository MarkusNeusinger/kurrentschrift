// Reading-measure wrapper for running body text. Caps line length at a
// comfortable ~66 characters (~47rem ≈ 750px at the 19px body, style-guide §3)
// so prose stays legible inside the wide PageContainer (1152/1280). Only
// continuous paragraphs are wrapped — structured content (cards, tables,
// specimens, the operator block) keeps the full column width. `align` puts the
// text column at the left (editorial, default) or centered in the page column.

import type { ElementType, ReactNode } from 'react';
import { Box } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';

export interface ProseProps {
  children: ReactNode;
  /** Place the measure column left (default) or centered in the page width. */
  align?: 'left' | 'center';
  /** Override the max line length (default ~47rem ≈ 66 characters). */
  measure?: number | string;
  component?: ElementType;
  sx?: SxProps<Theme>;
}

export function Prose({ children, align = 'left', measure = '47rem', component = 'div', sx }: ProseProps) {
  return (
    <Box
      component={component}
      sx={[
        { maxWidth: measure, ml: align === 'center' ? 'auto' : 0, mr: 'auto' },
        ...(Array.isArray(sx) ? sx : sx ? [sx] : []),
      ]}
    >
      {children}
    </Box>
  );
}
