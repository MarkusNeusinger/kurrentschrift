// The Scope-Leiste: the line under the header that says what the page in front
// of you is ABOUT — which Vorlage, which own hand — and nothing else.
//
// The workbench carries two scopes at once, and until now the header only named
// one of them. On /admin/eigenhand the Vorlagen-Chip and the Vorlagen-Korb kept
// standing over a page that belongs to a HAND; on the three Vorlagen views the
// hand was named nowhere at all. That is a labelling error, not a missing
// feature — so the answer is a bar that shows both and highlights the one the
// page is about (admin-redesign.md §3.1, §7.1–§7.2).
//
// It never SWITCHES. A bar that both states the scope and changes it is the
// confusion it exists to end: the Vorlage is changed in the picker, the hand on
// the Eigenhand page, and both fields are simply links there. The Vorlage field
// is also the one the header's chip used to be — keeping both would say the
// same thing twice and cost the phone header its second row (V15).
//
// The Hand field ALWAYS names the Eigenhand, never the plate hand, and carries
// the role gloss so it cannot be read as one (author decision P1-Q3 a,
// 2026-09-19). The plate hand stays named at the statistics panels that
// actually belong to it.

import FlagOutlinedIcon from '@mui/icons-material/FlagOutlined';
import { Box, Link, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useEffect, useRef, type ReactNode, type RefObject } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';

import { useAdmin } from '@/context/adminState';
import { de, fmt, styleLabel } from '@/locales/admin';
import { paths } from '@/routes/paths';
import { eigenhandUrl } from '@/sections/admin/shell/focus';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { paper } from '@/styles/paper';

function ScopeField({
  to,
  active,
  label,
  value,
  gloss,
  trailing,
  fieldRef,
}: {
  to: string;
  /** Whether THIS scope is what the open page is about. */
  active: boolean;
  label: string;
  value: string;
  /** The role behind the value, where the value alone could be misread. */
  gloss?: string;
  /** Rides inside the field, outside the link — see the Korb count below. */
  trailing?: ReactNode;
  fieldRef?: RefObject<HTMLDivElement | null>;
}) {
  return (
    <Box
      ref={fieldRef}
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 0.75,
        flex: '0 0 auto',
        // Both fields fit on one phone row only on the widest phones; the row
        // scrolls instead of wrapping, and a field is always snapped to whole.
        scrollSnapAlign: 'start',
        // The active field wears a viridian rule BESIDE it, not just a colour:
        // presence and position are the channels a colour-blind reader keeps
        // (design-system.md §9, Strichart-Regel). The inactive field holds the
        // same 2px transparent, so nothing shifts when the page changes.
        borderLeft: '2px solid',
        borderColor: active ? paper.viridian : 'transparent',
        pl: 1,
      }}
    >
      <Link
        component={RouterLink}
        to={to}
        // „true", never „page": the field names a SCOPE, and the open page is
        // one of several that share it.
        aria-current={active ? 'true' : undefined}
        sx={{
          display: 'inline-flex',
          alignItems: 'baseline',
          gap: 0.75,
          // The 44px floor as real height (design-system.md §9.3) — the bar has
          // no room for an invisible overlay that would reach into the nav row
          // above it.
          minHeight: TOUCH_TARGET,
          textDecoration: 'none',
          whiteSpace: 'nowrap',
          color: active ? paper.ink : paper.inkSoft,
          transition: 'color .25s',
          '&:hover': { color: paper.ink, textDecoration: 'underline' },
          '&:focus-visible': { outline: `2px solid ${paper.viridian}`, outlineOffset: 3 },
        }}
      >
        <Typography variant="caption" component="span" sx={{ color: paper.sepia }}>
          {label}
        </Typography>
        <Typography variant="body2" component="span" sx={{ color: 'inherit' }}>
          {value}
        </Typography>
        {gloss && (
          <Typography variant="caption" component="span" sx={{ color: paper.sepia }}>
            {gloss}
          </Typography>
        )}
      </Link>
      {trailing}
    </Box>
  );
}

export function ScopeBar({ openCount }: { openCount: number | null }) {
  const { source, handId } = useAdmin();
  const { pathname } = useLocation();
  const t = de.admin.shell;
  // Eigenhand is the one hand-scoped page; everything else in the workbench is
  // about the Vorlage, including the picker itself.
  const onHand = pathname.startsWith(paths.admin.eigenhand);

  const barRef = useRef<HTMLDivElement | null>(null);
  const activeRef = useRef<HTMLDivElement | null>(null);
  // On a phone both fields do not fit and the row scrolls. Left alone it starts
  // at the Vorlage, so on `/admin/eigenhand` — the one page that IS about the
  // hand — the highlighted field would sit off-screen and have to be looked
  // for. Scroll the active one into view instead; the scroll is set on the row
  // itself rather than through `scrollIntoView`, which would walk up and move
  // the page under the sticky header too.
  useEffect(() => {
    const bar = barRef.current;
    const field = activeRef.current;
    if (!bar || !field || bar.scrollWidth <= bar.clientWidth) return;
    bar.scrollLeft += field.getBoundingClientRect().left - bar.getBoundingClientRect().left;
  }, [onHand, handId, source?.id]);

  return (
    <Box
      component="nav"
      ref={barRef}
      aria-label={t.scopeAria}
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: { xs: 1.5, sm: 3 },
        px: { xs: 2.5, sm: 4, md: 6 },
        borderTop: '1px solid',
        borderColor: alpha(paper.line, 0.55),
        // One row at every size; on a phone it scrolls rather than wraps, so
        // the sticky block stays two rows tall (V15).
        overflowX: 'auto',
        scrollSnapType: 'x proximity',
      }}
    >
      <ScopeField
        to={paths.admin.root}
        active={!onHand}
        fieldRef={onHand ? undefined : activeRef}
        label={t.scopeSource}
        // Style label AND source id: one script can be taught by several
        // charts, so the style alone does not say which one is loaded.
        value={source ? `${styleLabel(source.style_id)} · ${source.id}` : t.noSource}
        trailing={
          // The Korb counts the VORLAGE's tasks, and until now it said so
          // nowhere — not even in the hover (V25: no decision-carrying state in
          // a tooltip only). It says it here by sitting in the field that names
          // the Vorlage, as text rather than as a bare badge. Outside the link,
          // so the link's name stays „Vorlage: …" and the flag is not read out
          // as part of it. No count while it is unknown (the read is
          // admin-gated and may 401) — a „0" would claim an empty basket.
          openCount ? (
            <Typography
              variant="caption"
              component="span"
              sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, color: paper.sepia }}
            >
              <FlagOutlinedIcon aria-hidden fontSize="inherit" />
              {fmt(t.korbOpen, { n: openCount })}
            </Typography>
          ) : null
        }
      />

      <ScopeField
        to={eigenhandUrl()}
        active={onHand}
        fieldRef={onHand ? activeRef : undefined}
        label={t.scopeHand}
        // An em-dash, not an invented id: a script whose own hand has not been
        // written yet has none, and V19 forbids borrowing another script's.
        value={handId ?? t.scopeHandNone}
        gloss={t.roleEigenhandGloss}
      />

      {/* The rest of the row stays deliberately empty: the „Kurztasten" switch
          belongs here (author decision P1-Q11 b) and is built by the keyboard
          PR of this phase. It is an operability control, not a third scope —
          which is why it may sit in a bar that never switches a scope. */}
      <Box sx={{ flex: '1 1 auto', minWidth: 16 }} aria-hidden />
    </Box>
  );
}
