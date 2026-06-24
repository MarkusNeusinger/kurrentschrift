// One shared content column for the public pages. Replaces the per-section MUI
// <Container maxWidth="sm|md|lg">, which let pages drift between 600 and 1280px
// (so /schriftkunde and /impressum at md=960 read "squeezed" next to the lg
// landing). Three calibrated widths instead: `text` (1152, most pages), `wide`
// (1280, landing/worksheet) and `narrow` (760, focused single-column drills like
// the quiz — also the ~66-character reading measure). Running text constrains
// itself further via <Prose>. Sits above the PaperBackground overlays
// (position relative, z-index 1); vertical padding stays per-page via `sx`.

import type { ElementType, ReactNode } from 'react';
import { Box } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';

export const PAGE_WIDTHS = { narrow: 760, text: 1152, wide: 1280 } as const;

export interface PageContainerProps {
  children: ReactNode;
  /** Max content width: a named step (default `text`) or an explicit px value. */
  width?: keyof typeof PAGE_WIDTHS | number;
  /** Rendered element/landmark (e.g. `'section'`). Defaults to `div`. */
  component?: ElementType;
  sx?: SxProps<Theme>;
}

export function PageContainer({ children, width = 'text', component = 'div', sx }: PageContainerProps) {
  const maxWidth = typeof width === 'number' ? width : PAGE_WIDTHS[width];
  return (
    <Box
      component={component}
      sx={[
        {
          position: 'relative',
          zIndex: 1,
          width: '100%',
          maxWidth,
          mx: 'auto',
          px: { xs: 2.5, sm: 4, md: 6 },
        },
        ...(Array.isArray(sx) ? sx : sx ? [sx] : []),
      ]}
    >
      {children}
    </Box>
  );
}
