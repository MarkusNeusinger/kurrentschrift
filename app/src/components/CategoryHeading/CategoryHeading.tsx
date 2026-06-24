// CategoryHeading — the shared section title used by the public long-form pages
// (/impressum, /schriftkunde). An <h2> in ink Playfair on a hairline writing-line,
// opened by an oversized Kurrent show-script initial in viridian (the period
// rubrication move recast in the house green; #40826d is the real chromium-oxide
// pigment and, large/bold, clears the WCAG large-text bar). On hover the ornate
// initial crossfades to the plain letter — a site that teaches reading Kurrent
// translates its own initials. The reveal is a mouse-only flourish, not a
// legibility crutch: the <h2> carries aria-label={children} and every visual glyph
// is aria-hidden, so screen readers always get the plain word, and only the first
// letter is Kurrent (the rest stays Antiqua) so the heading reads without it.
// prefers-reduced-motion drops the fade.

import { Box } from '@mui/material';

import { display, letterpress, paper, script } from '@/styles/paper';

// Reduced-motion media-query key — matches the `reduce` const idiom used by the
// other animated public components (Reveal, HeroWritten).
const reduce = '@media (prefers-reduced-motion: reduce)';

export function CategoryHeading({ children }: { children: string }) {
  const first = children.slice(0, 1);
  const rest = children.slice(1);
  return (
    <Box sx={{ borderBottom: `1px solid ${paper.line}`, pb: 0.75, mb: 1.5 }}>
      <Box
        component="h2"
        aria-label={children}
        sx={{
          m: 0,
          display: 'flex',
          alignItems: 'baseline',
          fontFamily: display,
          fontWeight: 600,
          fontSize: { xs: '1.5rem', md: '1.75rem' },
          lineHeight: 1.25,
          color: paper.ink,
          textShadow: letterpress,
          '&:hover .init-kurrent': { opacity: 0 },
          '&:hover .init-latin': { opacity: 1 },
          [reduce]: { '& .init-kurrent, & .init-latin': { transition: 'none' } },
        }}
      >
        {/* initial slot — Kurrent glyph in flow, plain letter centred over it */}
        <Box component="span" aria-hidden sx={{ position: 'relative', display: 'inline-block', flexShrink: 0, color: paper.viridian }}>
          <Box
            component="span"
            className="init-kurrent"
            sx={{ fontFamily: script, fontWeight: 400, fontSize: { xs: '2.6rem', md: '2.9rem' }, lineHeight: 1, display: 'block', transition: 'opacity .28s ease' }}
          >
            {first}
          </Box>
          <Box
            component="span"
            className="init-latin"
            sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: display, fontWeight: 700, fontSize: { xs: '2rem', md: '2.3rem' }, lineHeight: 1, opacity: 0, transition: 'opacity .28s ease', pointerEvents: 'none' }}
          >
            {first}
          </Box>
        </Box>
        <Box component="span" aria-hidden sx={{ ml: '0.06em' }}>
          {rest}
        </Box>
      </Box>
    </Box>
  );
}
