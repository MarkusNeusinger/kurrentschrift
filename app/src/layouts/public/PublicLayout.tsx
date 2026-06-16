// PublicLayout — shared chrome for the public pages (landing · worksheet · quiz ·
// impressum · 404): the aged-paper atmosphere, the sticky brand header, a single
// <main> landmark wrapping the page content, and the optional legal footer.
//
// The <main> landmark is the reason this wrapper exists. Each public page used to
// render its content straight into <PaperBackground> with no landmark, so
// assistive tech and Lighthouse found no "main" region (PR #90 fixed only the
// impressum, ad hoc). Centralising the chrome here closes that gap for every
// public page at once and keeps header/main/footer composition in one place.
//
// Footer policy: the landing carries its own richer inline footer, so it stays
// off (footer={false}, the default); worksheet and quiz opt into the shared
// <PublicFooter>; impressum and 404 need none.

import type { ReactNode } from 'react';
import { Box } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';

import { PaperBackground } from '@/components/PaperBackground';
import { PublicFooter } from '@/components/PublicFooter';
import { PublicHeader } from '@/components/PublicHeader';

interface PublicLayoutProps {
  children: ReactNode;
  /** Render the shared legal <PublicFooter> after the content (default off). */
  footer?: boolean;
  /** Header tone, forwarded to <PublicHeader>; defaults to the paper identity. */
  headerTone?: 'plain' | 'paper';
  /** Min-height forwarded to <PaperBackground> (defaults to a full viewport). */
  minHeight?: string | number;
  /** Extra sx merged onto the <main> content wrapper. */
  sx?: SxProps<Theme>;
}

export function PublicLayout({ children, footer = false, headerTone = 'paper', minHeight, sx }: PublicLayoutProps) {
  return (
    <PaperBackground minHeight={minHeight}>
      <PublicHeader tone={headerTone} />
      <Box component="main" sx={sx}>
        {children}
      </Box>
      {footer && <PublicFooter />}
    </PaperBackground>
  );
}
