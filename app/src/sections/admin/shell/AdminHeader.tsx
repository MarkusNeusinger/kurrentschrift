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
// belongs to a single view: the three areas (Buchstaben · Übergänge · Wörter),
// which Vorlage is being worked on (click = back to the picker) and the
// Auftragskorb with its open count. The letter grid that used to sit here
// permanently moved into the Buchstaben view, where it belongs — see
// LetterPicker.

import FlagOutlinedIcon from '@mui/icons-material/FlagOutlined';
import { Badge, Box, Chip, IconButton, Tooltip } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';

import { HeaderBar, HeaderNavLink, Wordmark } from '@/components/HeaderBar';
import { useAdmin } from '@/context/AdminContext';
import { de, styleLabel } from '@/locales/admin';
import { paths } from '@/routes/paths';

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

  return (
    <HeaderBar
      maxWidth="none"
      // Above the workbench's own layers, still below the Korb drawer (1200)
      // and the LetterPicker popover (1300), which are meant to cover it.
      zIndex={1100}
      contentSx={{ flexWrap: 'wrap', justifyContent: 'flex-start' }}
    >
      {/* The wordmark leaves the workbench (→ the public landing); the Vorlage
          chip beside it is the way back to the picker. */}
      <Wordmark to={paths.home} />

      {/* The Vorlage is the workbench's premise, not a setting buried in a
          sidebar: it is named in the header and one click goes back to the
          picker to change it. */}
      {/* `describeChild`: without it MUI puts the hint on the child as an
          aria-label, which REPLACES the chip's visible „Sütterlin ·
          suetterlin-1922" in the accessibility tree (WCAG 2.5.3 Label in
          Name). As a description it is announced beside the name instead. */}
      <Tooltip title={t.switchSource} describeChild>
        <Chip
          size="small"
          variant="outlined"
          clickable
          component={RouterLink}
          to={paths.admin.root}
          // Style label AND source id: the Kurrent style can pool from several
          // chart sources (different hands of the same script), so the style
          // alone does not say which one is loaded.
          label={source ? `${styleLabel(source.style_id)} · ${source.id}` : t.noSource}
          sx={{ maxWidth: 280 }}
        />
      </Tooltip>

      {/* The three views. `order` puts them on their own full-width row on
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
          // No overflow container here: the links' hover hairline sits 4px
          // BELOW them, so an `overflow: auto` nav grows a scrollbar for those
          // four pixels. The row wraps instead — that is what `flex: 1 0 100%`
          // at xs is for.
          flexWrap: 'wrap',
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

      <Tooltip title={t.openKorb}>
        {/* At xs the nav drops to its own row, so nothing pushes the Korb
            right any more — `ml: auto` on this row does. */}
        <IconButton size="small" aria-label={t.openKorb} onClick={onOpenKorb} sx={{ ml: { xs: 'auto', sm: 0 } }}>
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
