// Shared identity header for the public pages: a sticky, translucent, blurred
// bar with a bottom hairline. Left = the brand wordmark (•kurrentschrift.ink,
// with ".ink" in viridian italic); right = the three-area nav (Schriftkunde ·
// Lesen · Schreiben) with a viridian hover-underline. Modelled on the HTML mockup.
//
// Two tones: `paper` (now the default everywhere, since the cream "paper & ink"
// identity carries across all pages) and a slightly lighter `plain` fallback. The
// viridian accent is the same in both.
//
// Hidden admin entry: 5 quick clicks on the wordmark → /admin/chart (no visible
// admin link anywhere). The brand still navigates home on a normal single click.
// Render this OUTSIDE the page's content Container so the bar spans full width.

import { type MouseEvent, type ReactNode, useRef } from 'react';
import { Box, Link, Stack } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';

import { PAGE_WIDTHS } from '@/components/PageContainer';
import { de } from '@/locales';
import { paths } from '@/routes/paths';
import { display, paper } from '@/styles/paper';

const ADMIN_TAPS = 5;
const TAP_WINDOW_MS = 800;

// Three areas only: Schriftkunde (reference), Lesen (Quiz + Tafel hub) and
// Schreiben (Übungsblatt + Federprobe hub). The five-link bar was confusing —
// it wasn't clear whether the Tafel or the Federprobe belonged to reading or
// writing; the two hubs resolve that.
//
// Schriftkunde is kept apart from the Lesen/Schreiben pair so that when the bar
// is too narrow for one row (phones), the nav stacks as two rows: Lesen +
// Schreiben sit together on the lower row, right-aligned, with Schriftkunde
// centred above them. On sm+ all three sit inline on one row.
const SCHRIFTKUNDE = { label: de.common.nav.schriftkunde, to: paths.schriftkunde };
const READ_WRITE = [
  { label: de.common.nav.read, to: paths.lesen },
  { label: de.common.nav.write, to: paths.schreiben },
];

interface PublicHeaderProps {
  tone?: 'plain' | 'paper';
  sx?: SxProps<Theme>;
}

export function PublicHeader({ tone = 'paper', sx }: PublicHeaderProps) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const tap = useRef({ count: 0, last: 0 });
  const isPaper = tone === 'paper';
  const textMain = isPaper ? paper.ink : 'text.primary';
  const textSoft = isPaper ? paper.inkSoft : 'text.secondary';
  const accent = paper.viridian;
  const barBg = isPaper ? 'rgba(231,221,193,0.86)' : 'rgba(250,248,241,0.86)';
  const border = isPaper ? paper.line : 'divider';

  const navLink = (label: ReactNode, to: string, sx?: SxProps<Theme>) => {
    // Current-area indication: the area link stays "on" (ink + full underline
    // + aria-current) while any page of that area is open (/lesen also covers
    // /quiz + /tafel etc. once those routes nest; exact match covers today's flat ones).
    const active = pathname === to || pathname.startsWith(`${to}/`);
    return (
      <Link
        key={to}
        component={RouterLink}
        to={to}
        aria-current={active ? 'page' : undefined}
        sx={{
          color: active ? textMain : textSoft,
          textDecoration: 'none',
          fontFamily: display,
          fontSize: { xs: '0.95rem', sm: '1.05rem' },
          position: 'relative',
          transition: 'color .25s',
          '&::after': {
            content: '""',
            position: 'absolute',
            left: 0,
            bottom: -4,
            height: '1px',
            width: active ? '100%' : 0,
            bgcolor: accent,
            transition: 'width .3s ease',
          },
          '&:hover': { color: textMain },
          '&:hover::after': { width: '100%' },
          // Visible keyboard-focus ring (2px viridian, offset).
          '&:focus-visible': { color: textMain, outline: `2px solid ${accent}`, outlineOffset: 3 },
          ...sx,
        }}
      >
        {label}
      </Link>
    );
  };

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
          maxWidth: PAGE_WIDTHS.wide,
          mx: 'auto',
          px: { xs: 2.5, sm: 4, md: 6 },
          py: 1.75,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: { xs: 1, sm: 2 },
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
            // Fluid so the long ".ink" wordmark eases down on the narrowest
            // phones instead of forcing the bar wider than the viewport (it used
            // to overflow ≤360px); holds at 1.5rem on sm+ as before.
            fontSize: 'clamp(1.05rem, 0.58rem + 2.4vw, 1.5rem)',
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

        {/* nav — viridian hover-underline. On sm+ the three areas sit inline on
            one row; on phones the bar is too narrow, so it stacks into two rows:
            Lesen + Schreiben together on the lower row (right-aligned) with
            Schriftkunde centred above them. */}
        <Box
          component="nav"
          sx={{
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            // xs: stretch so the lower Lesen/Schreiben row can right-align to the
            // bar's right edge while Schriftkunde (alignSelf:center) sits centred
            // above it. sm+: a normal centred single row.
            alignItems: { xs: 'stretch', sm: 'center' },
            columnGap: { sm: 3 },
            rowGap: 0.5,
          }}
        >
          {navLink(SCHRIFTKUNDE.label, SCHRIFTKUNDE.to, { alignSelf: 'center' })}
          <Stack
            direction="row"
            spacing={{ xs: 1.5, sm: 3 }}
            sx={{ alignItems: 'center', justifyContent: { xs: 'flex-end', sm: 'flex-start' } }}
          >
            {READ_WRITE.map((n) => navLink(n.label, n.to))}
          </Stack>
        </Box>
      </Box>
    </Box>
  );
}
