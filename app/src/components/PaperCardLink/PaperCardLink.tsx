// PaperCardLink — THE public "paper card that is a link" (style-guide surface
// rule: identity = paper, cards lift on hover/focus with a viridian border).
// One place for the hover/keyboard-focus affordance that LandingView, HubView
// and the Schriftkunde try-cards used to copy from each other, so contrast and
// focus fixes land once. `PaperCardCta` is the matching CTA line whose hairline
// underline sweeps in on card hover/focus (the former hub-cta/try-cta spans).

import type { ReactNode } from 'react';
import { Box, Typography } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';
import { Link as RouterLink } from 'react-router-dom';

import { display, paper } from '@/styles/paper';

interface PaperCardLinkProps {
  to: string;
  children: ReactNode;
  sx?: SxProps<Theme>;
}

export function PaperCardLink({ to, children, sx }: PaperCardLinkProps) {
  return (
    <Box
      component={RouterLink}
      to={to}
      sx={[
        {
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          textDecoration: 'none',
          color: paper.ink,
          p: 2.5,
          borderRadius: 2,
          border: `1px solid ${paper.line}`,
          bgcolor: paper.hi,
          transition: 'border-color .25s, transform .25s, box-shadow .25s',
          // Hover and keyboard focus share the affordance; the outline marks
          // the focused card for tab users.
          '&:hover, &:focus-visible': {
            borderColor: paper.viridian,
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 24px rgba(36,26,16,0.10)',
          },
          '&:focus-visible': { outline: `2px solid ${paper.viridian}`, outlineOffset: 3 },
          '&:hover .card-cta::after, &:focus-visible .card-cta::after': { width: '100%' },
        },
        ...(Array.isArray(sx) ? sx : sx ? [sx] : []),
      ]}
    >
      {children}
    </Box>
  );
}

// The CTA line of a PaperCardLink: viridian text (AA-darkened variant) with a
// hairline underline that sweeps in when the CARD is hovered/focused.
export function PaperCardCta({ children, sx }: { children: ReactNode; sx?: SxProps<Theme> }) {
  return (
    <Typography
      className="card-cta"
      component="span"
      variant="body2"
      sx={[
        {
          mt: 2.5,
          alignSelf: 'flex-start',
          position: 'relative',
          color: paper.viridianText,
          fontFamily: display,
          '&::after': {
            content: '""',
            position: 'absolute',
            left: 0,
            bottom: -3,
            height: '1px',
            width: 0,
            bgcolor: paper.viridian,
            transition: 'width .3s ease',
          },
        },
        ...(Array.isArray(sx) ? sx : sx ? [sx] : []),
      ]}
    >
      {children}
    </Typography>
  );
}
