// The one admin header — and since the design round it is literally the public
// header's chrome: same wordmark (•kurrentschrift.ink, dot and TLD included),
// same height, same hairline, same Playfair area links with the viridian
// hover-underline. All three come from components/HeaderBar, so „entering the
// admin" cannot look like leaving the site and the two bars cannot drift apart
// again. The one deliberate difference is the content column: the public pages
// sit in a centred 1280 column, the workbench is full-bleed because it needs
// the width for chart crops, letter grids and pair matrices.
//
// It carries everything that is true for the WHOLE workbench and nothing that
// belongs to a single view: the four areas (Buchstaben · Übergänge · Wörter ·
// Eigenhand) and the Auftragskorb with its open count. The letter grid that
// used to sit here permanently moved into the Buchstaben view, where it belongs
// — see LetterPicker.
//
// WHICH Vorlage is being worked on moved one row down, into the Scope-Leiste:
// the chip and the bar's Vorlage field were the same link to the same picker,
// and saying it twice kept the phone header at three rows where V15 wants two.
// The bar rides in the header's own `below` slot, so header and scope stick as
// one block.

import FlagOutlinedIcon from '@mui/icons-material/FlagOutlined';
import { Badge, Box, IconButton, Tooltip } from '@mui/material';
import { useLocation } from 'react-router-dom';

import { HeaderBar, HeaderNavLink, Wordmark } from '@/components/HeaderBar';
import { useAdmin } from '@/context/adminState';
import { de, fmt, styleLabel } from '@/locales/admin';
import { paths } from '@/routes/paths';
import { ScopeBar } from '@/sections/admin/shell/ScopeBar';

const AREAS = [
  { to: paths.admin.letters, label: de.admin.shell.areaLetters },
  { to: paths.admin.joins, label: de.admin.shell.areaJoins },
  { to: paths.admin.words, label: de.admin.shell.areaWords },
  // Beside the three Vorlage views rather than inside them: Eigenhand belongs
  // to a hand, and the Vorlage chip does not apply to it.
  { to: paths.admin.eigenhand, label: de.admin.shell.areaEigenhand },
] as const;

export function AdminHeader({ openCount, onOpenKorb }: { openCount: number | null; onOpenKorb: () => void }) {
  const { source } = useAdmin();
  const { pathname } = useLocation();
  const t = de.admin.shell;
  // The basket belongs to the VORLAGE. The bar says so visibly; the icon
  // button says it in its name, so the two never disagree — and it names the
  // same two halves the bar does, style AND id: Kurrent alone is taught by two
  // charts here, so „der Vorlage Kurrent" would be the name of two baskets.
  const korbLabel = source
    ? fmt(t.korbScoped, { style: styleLabel(source.style_id), id: source.id })
    : t.openKorb;

  return (
    <HeaderBar
      maxWidth="none"
      // Above the workbench's own layers, still below the Korb drawer (1200)
      // and the LetterPicker popover (1300), which are meant to cover it.
      zIndex={1100}
      contentSx={{ flexWrap: 'wrap', justifyContent: 'flex-start' }}
      below={<ScopeBar openCount={openCount} />}
    >
      {/* The wordmark leaves the workbench (→ the public landing). */}
      <Wordmark to={paths.home} />

      {/* The four views. `order` puts them on their own full-width row on
          phones, under the wordmark instead of squeezed beside it. */}
      <Box
        component="nav"
        aria-label={t.areaNavAria}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: { xs: 2, md: 3 },
          flex: { xs: '1 0 100%', sm: 1 },
          order: { xs: 3, sm: 0 },
          justifyContent: { xs: 'flex-start', sm: 'flex-end' },
          // At xs the four links scroll instead of wrapping, so the header
          // stays TWO rows on a phone (V15) — with the Scope-Leiste under it
          // a third row would push the work off the screen.
          //
          // The 4px of `pb` are load-bearing, and they are why this row had no
          // overflow container before: the links' hover hairline sits 4px BELOW
          // the text, so an `overflow: auto` without that padding grows a
          // vertical scrollbar for exactly those four pixels — and
          // `overflowY: hidden` would clip the active link's underline instead.
          flexWrap: { xs: 'nowrap', sm: 'wrap' },
          overflowX: { xs: 'auto', sm: 'visible' },
          pb: { xs: '4px', sm: 0 },
          scrollSnapType: { xs: 'x proximity', sm: 'none' },
          '& > a': { scrollSnapAlign: { xs: 'start', sm: 'none' } },
          minWidth: 0,
          ml: { sm: 'auto' },
        }}
      >
        {AREAS.map((area) => (
          <HeaderNavLink
            key={area.to}
            label={area.label}
            to={area.to}
            active={pathname.startsWith(area.to)}
            exact={pathname === area.to}
          />
        ))}
      </Box>

      <Tooltip title={korbLabel}>
        {/* At xs the nav drops to its own row, so nothing pushes the Korb
            right any more — `ml: auto` on this row does. */}
        <IconButton size="small" aria-label={korbLabel} onClick={onOpenKorb} sx={{ ml: { xs: 'auto', sm: 0 } }}>
          {/* No badge at all while the count is unknown (the read is
              admin-gated and may 401) — a silent "0" would claim an empty
              basket the header never actually read. */}
          <Badge badgeContent={openCount ?? 0} color="warning" invisible={!openCount}>
            <FlagOutlinedIcon fontSize="small" />
          </Badge>
        </IconButton>
      </Tooltip>
    </HeaderBar>
  );
}
