// The one admin header — the admin's counterpart to PublicHeader, and
// deliberately closer to it than the old icon strip in the sidebar was: same
// wordmark, same hairline, same viridian accent, so entering /admin does not
// feel like leaving the site.
//
// It carries everything that is true for the WHOLE workbench and nothing that
// belongs to a single view: the three areas (Buchstaben · Übergänge · Wörter),
// which Vorlage is being worked on (click = back to the picker) and the
// Auftragskorb with its open count. The letter grid that used to sit here
// permanently moved into the Buchstaben view, where it belongs — see
// LetterPicker.

import FlagOutlinedIcon from '@mui/icons-material/FlagOutlined';
import { Badge, Box, Button, Chip, IconButton, Tooltip } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';

import { useAdmin } from '@/context/AdminContext';
import { de, styleLabel } from '@/locales/admin';
import { paths } from '@/routes/paths';
import { display, paper } from '@/styles/paper';

const AREAS = [
  { to: paths.admin.letters, label: de.admin.shell.areaLetters },
  { to: paths.admin.joins, label: de.admin.shell.areaJoins },
  { to: paths.admin.words, label: de.admin.shell.areaWords },
] as const;

export function AdminHeader({ openCount, onOpenKorb }: { openCount: number | null; onOpenKorb: () => void }) {
  const { source } = useAdmin();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const t = de.admin.shell;

  return (
    <Box
      component="header"
      sx={{
        position: 'sticky',
        top: 0,
        zIndex: (theme) => theme.zIndex.appBar,
        borderBottom: 1,
        borderColor: 'divider',
        bgcolor: (theme) => alpha(theme.palette.background.default, 0.92),
        backdropFilter: 'blur(6px)',
        px: { xs: 1.5, md: 3 },
        py: 1,
        display: 'flex',
        alignItems: 'center',
        gap: { xs: 1, md: 2 },
        flexWrap: 'wrap',
      }}
    >
      <Box
        component={RouterLink}
        to={paths.home}
        sx={{
          fontFamily: display,
          fontSize: 19,
          fontWeight: 600,
          textDecoration: 'none',
          color: 'text.primary',
          whiteSpace: 'nowrap',
        }}
      >
        {de.common.brand.name}
      </Box>

      {/* The Vorlage is the workbench's premise, not a setting buried in a
          sidebar: it is named in the header and one click goes back to the
          picker to change it. */}
      <Tooltip title={t.switchSource}>
        <Chip
          size="small"
          variant="outlined"
          clickable
          onClick={() => navigate(paths.admin.root)}
          // Style label AND source id: two of the four sources are „Kurrent"
          // (loth-1866 and petzendorfer-1889 are different hands of the same
          // script), so the style alone does not say which one is loaded.
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
          gap: { xs: 0.5, md: 1 },
          flex: { xs: '1 0 100%', sm: 1 },
          order: { xs: 3, sm: 0 },
          minWidth: 0,
          overflowX: 'auto',
        }}
      >
        {AREAS.map((area) => {
          const active = pathname.startsWith(area.to);
          return (
            <Button
              key={area.to}
              component={RouterLink}
              to={area.to}
              size="small"
              sx={{
                px: 1.25,
                whiteSpace: 'nowrap',
                color: active ? 'primary.main' : 'text.primary',
                borderBottom: 2,
                borderRadius: 0,
                borderColor: active ? 'primary.main' : 'transparent',
                '&:hover': { borderColor: active ? 'primary.main' : paper.line, bgcolor: 'transparent' },
              }}
            >
              {area.label}
            </Button>
          );
        })}
      </Box>

      <Tooltip title={t.openKorb}>
        <IconButton size="small" aria-label={t.openKorb} onClick={onOpenKorb} sx={{ ml: 'auto' }}>
          {/* No badge at all while the count is unknown (the read is
              admin-gated and may 401) — a silent "0" would claim an empty
              basket the header never actually read. */}
          <Badge badgeContent={openCount ?? 0} color="warning" invisible={!openCount}>
            <FlagOutlinedIcon fontSize="small" />
          </Badge>
        </IconButton>
      </Tooltip>
    </Box>
  );
}
