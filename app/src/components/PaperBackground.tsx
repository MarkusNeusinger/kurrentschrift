// PaperBackground — the shared "aged paper" atmosphere: a warm radial gradient,
// fine SVG grain (multiplied), an inset vignette, plus the GLKurrent @font-face.
// Extracted from LandingPage so every page wears the same identity site-wide
// (style-guide §8). The three overlays are fixed, non-interactive and sit at
// z-index 0; children render in a z-index-1 layer above them.
//
// Work surfaces that need a neutral ground (the A4 worksheet preview, the letter
// crops, the chart scan / wizard canvas) opt out simply by painting their own
// solid background on top of this layer.

import { Box, GlobalStyles } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';
import type { ReactNode } from 'react';

import kurrentWoff2 from '../assets/fonts/gl-germancursive.woff2';
import { garamond, paper } from '../styles/paper';

// faint paper grain (greyscale fractal noise, multiplied over the warm base)
const GRAIN =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E\")";

interface PaperBackgroundProps {
  /** Optional so a bare ground can serve as a route Suspense fallback. */
  children?: ReactNode;
  /** Min-height of the page ground; defaults to a full viewport. */
  minHeight?: string | number;
  /** Extra sx merged onto the root (e.g. layout for the admin shell). */
  sx?: SxProps<Theme>;
}

export function PaperBackground({ children, minHeight = '100vh', sx }: PaperBackgroundProps) {
  return (
    <Box
      // Array form so every SxProps shape a caller might pass (object, array or
      // theme callback) is flattened by MUI rather than dropped by object spread.
      sx={[
        {
          position: 'relative',
          minHeight,
          color: paper.ink,
          bgcolor: paper.bg,
          fontFamily: garamond,
          backgroundImage: `radial-gradient(130% 90% at 50% -15%, ${paper.hi} 0%, ${paper.bg} 52%, ${paper.lo} 100%)`,
          // grain + vignette as fixed, non-interactive overlays behind the content
          '&::before': {
            content: '""',
            position: 'fixed',
            inset: 0,
            pointerEvents: 'none',
            zIndex: 0,
            backgroundImage: GRAIN,
            mixBlendMode: 'multiply',
            opacity: 0.5,
          },
          '&::after': {
            content: '""',
            position: 'fixed',
            inset: 0,
            pointerEvents: 'none',
            zIndex: 0,
            boxShadow: 'inset 0 0 200px rgba(60,40,20,.26)',
          },
        },
        ...(Array.isArray(sx) ? sx : sx ? [sx] : []),
      ]}
    >
      <GlobalStyles
        styles={{
          '@font-face': {
            fontFamily: 'GLKurrent',
            src: `url(${kurrentWoff2}) format('woff2')`,
            fontDisplay: 'swap',
          },
        }}
      />
      {/* content layer above the fixed overlays */}
      <Box sx={{ position: 'relative', zIndex: 1 }}>{children}</Box>
    </Box>
  );
}
