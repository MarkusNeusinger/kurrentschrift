// InfoHint — the one recognizable, unobtrusive info affordance used across the
// whole app (public + admin). It keeps surfaces minimal while holding the detail
// a tap away: instead of an explanatory sentence under every control, the
// explanation lives behind this mark and is revealed on click. Click/tap toggles
// a popover (touch-friendly — no hover dependency).
//
// The mark is the site's own hand: a Kurrent "i" (GLKurrent) in viridian, set
// large and cropped to a hairline ink ring (a small monogram). "i" for
// information, written rather than drawn from a UI kit (style-guide §1/§2).

import { useId, useState, type MouseEvent, type ReactNode } from 'react';

import { Box, IconButton, Popover, Typography } from '@mui/material';

import { de } from '@/locales';
import { paper } from '@/styles/paper';

// The Kurrent-i monogram. The glyph is set oversized and clipped to the ring so
// the ornate cursive "i" reads big and centred; `currentColor` lets the button
// drive its tone (viridian at rest, darker on hover). A unique clip id per
// instance avoids cross-SVG id collisions.
function InfoMark() {
  const id = useId().replace(/:/g, '');
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" style={{ display: 'block' }}>
      <defs>
        <clipPath id={`ih-${id}`}>
          <circle cx="12" cy="12" r="9.75" />
        </clipPath>
      </defs>
      <circle cx="12" cy="12" r="10.25" fill="none" stroke={paper.line} strokeWidth="1" />
      <g clipPath={`url(#ih-${id})`}>
        <text x="12" y="10" textAnchor="middle" dominantBaseline="central" fontFamily="'GLKurrent', cursive" fontSize="34" fill="currentColor">
          i
        </text>
      </g>
    </svg>
  );
}

interface InfoHintProps {
  /** Detail content revealed on tap — the explanation we tuck away. */
  children: ReactNode;
  /** Optional bold lead line shown above the detail text. */
  title?: string;
  /** Overrides the trigger's aria-label (defaults to the shared string). */
  label?: string;
}

export function InfoHint({ children, title, label }: InfoHintProps) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const open = Boolean(anchor);
  return (
    <>
      <IconButton
        size="small"
        aria-label={label ?? de.common.info.open}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={(e: MouseEvent<HTMLElement>) => setAnchor(e.currentTarget)}
        sx={{
          // p 0.25 keeps the hit area >= the WCAG 2.2 target-size floor (22px
          // mark + 2*2px = 26px). Viridian at rest, darker viridian on hover.
          p: 0.25,
          color: 'primary.main',
          verticalAlign: 'text-bottom',
          '&:hover, &:focus-visible': { color: 'primary.dark', bgcolor: 'transparent' },
        }}
      >
        <InfoMark />
      </IconButton>
      <Popover
        open={open}
        anchorEl={anchor}
        onClose={() => setAnchor(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        slotProps={{ paper: { variant: 'outlined', sx: { maxWidth: 320, p: 2 } } }}
      >
        {title && (
          <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
            {title}
          </Typography>
        )}
        <Box sx={{ color: 'text.secondary', typography: 'body2' }}>{children}</Box>
      </Popover>
    </>
  );
}
