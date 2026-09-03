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

import { PAGE_WIDTHS, type PageWidth } from './widths';

export interface PageContainerProps {
  children: ReactNode;
  /** Max content width: a named step (default `text`) or an explicit px value. */
  width?: PageWidth | number;
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
          // The page gutter is 20/32/48px — but index.html opts the document
          // into `viewport-fit=cover`, so on a notched phone in landscape the
          // first ~47px of each edge sit under the cutout. `max()` keeps the
          // designed gutter everywhere it is already big enough and yields to
          // the device inset only where the inset is larger (design-system §4).
          pl: {
            xs: 'max(20px, env(safe-area-inset-left))',
            sm: 'max(32px, env(safe-area-inset-left))',
            md: 'max(48px, env(safe-area-inset-left))',
          },
          pr: {
            xs: 'max(20px, env(safe-area-inset-right))',
            sm: 'max(32px, env(safe-area-inset-right))',
            md: 'max(48px, env(safe-area-inset-right))',
          },
        },
        ...(Array.isArray(sx) ? sx : sx ? [sx] : []),
      ]}
    >
      {children}
    </Box>
  );
}
