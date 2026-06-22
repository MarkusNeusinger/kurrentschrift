// Shared identity header for the public pages (landing, quiz, worksheet): a sticky,
// translucent, blurred bar with a bottom hairline. Left = the brand wordmark
// (•kurrentschrift.ink, with ".ink" in viridian italic); right = the Schreiben/Lesen
// nav with a viridian hover-underline. Modelled on the HTML mockup's nav.
//
// Two tones: `paper` (now the default everywhere, since the cream "paper & ink"
// identity carries across all pages) and a slightly lighter `plain` fallback. The
// viridian accent is the same in both.
//
// Hidden admin entry: 5 quick clicks on the wordmark → /admin/chart (no visible
// admin link anywhere). The brand still navigates home on a normal single click.
// Render this OUTSIDE the page's content Container so the bar spans full width.

import { type MouseEvent, useRef } from 'react';
import { Box, Link, Stack } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';
import { Link as RouterLink, useNavigate } from 'react-router-dom';

import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { display, paper } from '@/styles/paper';

const ADMIN_TAPS = 5;
const TAP_WINDOW_MS = 800;

const NAV = [
  { label: de.common.nav.write, to: paths.worksheet },
  { label: de.common.nav.scribe, to: paths.scribe },
  { label: de.common.nav.tafel, to: paths.tafel },
  { label: de.common.nav.read, to: paths.quiz },
];

interface PublicHeaderProps {
  tone?: 'plain' | 'paper';
  sx?: SxProps<Theme>;
}

export function PublicHeader({ tone = 'paper', sx }: PublicHeaderProps) {
  const navigate = useNavigate();
  const tap = useRef({ count: 0, last: 0 });
  const isPaper = tone === 'paper';
  const textMain = isPaper ? paper.ink : 'text.primary';
  const textSoft = isPaper ? paper.inkSoft : 'text.secondary';
  const accent = paper.viridian;
  const barBg = isPaper ? 'rgba(231,221,193,0.86)' : 'rgba(250,248,241,0.86)';
  const border = isPaper ? paper.line : 'divider';

  // Count quick successive taps on the wordmark; the 5th within the window opens
  // admin instead of following the home link. Per-instance state (useRef) — the
  // landing header stays mounted while you tap, so the gesture accumulates fine.
  const handleWordmark = (e: MouseEvent) => {
    const now = Date.now();
    const t = tap.current;
    t.count = now - t.last < TAP_WINDOW_MS ? t.count + 1 : 1;
    t.last = now;
    if (t.count >= ADMIN_TAPS) {
      t.count = 0;
      e.preventDefault();
      navigate(paths.admin.chart);
    }
  };

  return (
    <Box
      component="header"
      sx={{
        position: 'sticky',
        top: 0,
        zIndex: 20,
        bgcolor: barBg,
        backdropFilter: 'blur(6px)',
        borderBottom: '1px solid',
        borderColor: border,
        ...sx,
      }}
    >
      <Box
        sx={{
          maxWidth: 1120,
          mx: 'auto',
          px: { xs: 2.5, sm: 4, md: 6 },
          py: 1.75,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 2,
        }}
      >
        {/* brand — dot + kurrentschrift + .ink (accent italic). 5 taps → admin. */}
        <Box
          component={RouterLink}
          to={paths.home}
          onClick={handleWordmark}
          sx={{
            display: 'inline-flex',
            alignItems: 'baseline',
            textDecoration: 'none',
            fontFamily: display,
            fontWeight: 600,
            fontSize: { xs: '1.3rem', sm: '1.5rem' },
            letterSpacing: '0.02em',
            color: textMain,
          }}
        >
          <Box
            component="span"
            sx={{
              width: '0.42em',
              height: '0.42em',
              borderRadius: '50%',
              bgcolor: accent,
              alignSelf: 'center',
              mr: '0.2em',
              boxShadow: `0 0 6px ${accent}80`,
            }}
          />
          {de.common.brand.name}
          <Box component="span" sx={{ color: accent, fontStyle: 'italic' }}>
            {de.common.brand.tld}
          </Box>
        </Box>

        {/* nav — viridian hover-underline */}
        <Stack direction="row" spacing={{ xs: 2.5, sm: 3.5 }} sx={{ alignItems: 'center' }}>
          {NAV.map((n) => (
            <Link
              key={n.to}
              component={RouterLink}
              to={n.to}
              sx={{
                color: textSoft,
                textDecoration: 'none',
                fontFamily: display,
                fontSize: '1.05rem',
                position: 'relative',
                transition: 'color .25s',
                '&::after': {
                  content: '""',
                  position: 'absolute',
                  left: 0,
                  bottom: -4,
                  height: '1px',
                  width: 0,
                  bgcolor: accent,
                  transition: 'width .3s ease',
                },
                '&:hover': { color: textMain },
                '&:hover::after': { width: '100%' },
              }}
            >
              {n.label}
            </Link>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
