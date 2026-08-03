// Shared identity header for the public pages: a sticky, translucent, blurred
// bar with a bottom hairline. Left = the brand wordmark (•kurrentschrift.ink,
// with ".ink" in viridian italic); right = the three-area nav (Schriftkunde ·
// Lesen · Schreiben) with a viridian hover-underline. Modelled on the HTML mockup.
//
// One tone: the cream "paper & ink" identity — it carries across every public
// page (the former `plain` fallback had no caller and no palette token, so it
// was removed rather than left as a drift risk). The chrome itself (bar,
// wordmark, nav link) lives in components/HeaderBar and is shared with the
// admin's AdminHeader, so the two bars cannot drift apart again.
//
// Hidden admin entry: 5 quick clicks on the wordmark → /admin (no visible admin
// link anywhere), which is the Vorlage picker the workbench starts at. The
// brand still navigates home on a normal single click.
// Render this OUTSIDE the page's content Container so the bar spans full width.

import { type MouseEvent, useRef } from 'react';
import { Box, Stack } from '@mui/material';
import type { SxProps, Theme } from '@mui/material/styles';
import { useLocation, useNavigate } from 'react-router-dom';

import { HeaderBar, HeaderNavLink, Wordmark } from '@/components/HeaderBar';
import { de } from '@/locales';
import { paths } from '@/routes/paths';

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

// Which standalone tool routes belong to which area link, so the nav can mark
// the current AREA even off its hub page (/quiz and /tafel are Lesen tools,
// /federprobe a Schreiben tool — they keep their stable top-level URLs and are
// not nested under the hubs; see routes/paths.ts).
const AREA_ROUTES: Record<string, string[]> = {
  [paths.lesen]: [paths.lesen, paths.quiz, paths.tafel],
  [paths.schreiben]: [paths.schreiben, paths.scribe],
  [paths.schriftkunde]: [paths.schriftkunde],
};

interface PublicHeaderProps {
  sx?: SxProps<Theme>;
}

export function PublicHeader({ sx }: PublicHeaderProps) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const tap = useRef({ count: 0, last: 0 });

  const navLink = (label: string, to: string, linkSx?: SxProps<Theme>) => {
    // Current-area indication: the area link stays "on" (ink + full underline
    // + aria-current) while any page of that area is open — the hub itself,
    // its nested routes (/schreiben/uebungsblatt), or the area's standalone
    // tool routes (AREA_ROUTES: /quiz, /tafel → Lesen; /federprobe → Schreiben).
    const roots = AREA_ROUTES[to] ?? [to];
    const active = roots.some((root) => pathname === root || pathname.startsWith(`${root}/`));
    return <HeaderNavLink key={to} label={label} to={to} active={active} exact={pathname === to} sx={linkSx} />;
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
      navigate(paths.admin.root);
    }
  };

  return (
    <HeaderBar sx={sx}>
      {/* brand — dot + kurrentschrift + .ink (accent italic). 5 taps → admin. */}
      <Wordmark to={paths.home} onClick={handleWordmark} />

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
    </HeaderBar>
  );
}
