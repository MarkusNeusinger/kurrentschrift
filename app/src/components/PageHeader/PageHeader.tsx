// PageHeader — the one shared header block for every public page (except the
// landing hero): a muted area-eyebrow on a hairline, the page title in Playfair
// (the display voice — ALL page titles share it now), and an optional running
// intro at the reading measure. One component so the header can't drift per page
// (design-system §3): same font, same eyebrow style, same left-aligned position.
//
// Before this, titles split between Playfair (content pages) and italic Garamond
// (tool pages), only one page carried a (green) eyebrow, and the quiz title sat
// indented — see the design-system §3 note.

import type { ReactNode } from 'react';
import { Box, Typography } from '@mui/material';

import { Prose } from '@/components/Prose';
import { display, garamond, letterpress, paper } from '@/styles/paper';

interface PageHeaderProps {
  /** Small area kicker over the title (e.g. Lesen / Schreiben / Schriftkunde).
   *  Uppercased + tracked on a hairline. Omit on the area hubs (title = area). */
  eyebrow?: string;
  /** The page title — always Playfair, in h1 size. */
  title: string;
  /** Running intro paragraph(s); wrapped to the ~66-char reading measure. */
  children?: ReactNode;
}

export function PageHeader({ eyebrow, title, children }: PageHeaderProps) {
  return (
    <Box component="header" sx={{ mb: { xs: 3.5, md: 4 } }}>
      {eyebrow && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: '0.7rem', mb: '1rem' }}>
          <Box component="span" sx={{ width: 42, height: '1px', bgcolor: paper.sepia }} />
          <Typography
            component="span"
            variant="overline"
            sx={{ fontFamily: garamond, textTransform: 'uppercase', color: paper.sepia }}
          >
            {eyebrow}
          </Typography>
        </Box>
      )}
      <Typography
        component="h1"
        variant="h1"
        sx={{ fontFamily: display, fontWeight: 600, color: paper.ink, textShadow: letterpress }}
      >
        {title}
      </Typography>
      {children && (
        <Prose align="left" sx={{ mt: 2 }}>
          {children}
        </Prose>
      )}
    </Box>
  );
}
