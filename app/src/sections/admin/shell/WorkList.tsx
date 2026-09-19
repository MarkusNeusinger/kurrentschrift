// The parts every Arbeitsliste is built from — the filter chip row, the two
// switches, the pager, the expandable row and the two empty states.
//
// They live here rather than in one view because the three overviews
// (Buchstaben · Übergänge · Wörter) are the same surface over different
// subjects: a toolbar that writes its state into the URL, a compact row per
// subject, and the existing card as the expanded body. What differs is the
// vocabulary, and that is data the caller passes (`letters/letterRows.ts`),
// never anything this file knows.
//
// Two rules of the design system bite here in particular, and both are built
// into the components rather than left to each call site:
//   · every interactive target is at least 44 px in its smaller edge (§9.3) —
//     the chips are grown rather than given an invisible hit area, because in a
//     dense row the neighbour would win the extra pixels (§9.3, „wo Nachbarn
//     dicht stehen");
//   · on a phone the filter row is ONE scroll-snapping line instead of a block
//     of wrapped chips that pushes the list itself below the fold.

import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Box, Button, Chip, Collapse, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { useId } from 'react';
import type { ReactNode } from 'react';

import { de, fmt } from '@/locales/admin';
import { LIST_VIEWS, PAGE_ALL, pageCount, type ListPage, type ListView } from '@/sections/admin/shell/listState';
import { TOUCH_TARGET } from '@/styles/hitArea';

/** What one filter chip offers: its token, its German label and how many rows
 * it would select ON ITS OWN — `null` while the read behind it has not
 * answered, so the chip carries no number rather than a „0" it cannot back. */
export type FilterChipModel = {
  token: string;
  label: string;
  count: number | null;
  active: boolean;
};

/** One sort option; `disabledHint` says WHY it cannot be chosen, where a
 * disabled control alone would look like a bug. */
export type SortOptionModel = {
  token: string;
  label: string;
  disabled?: boolean;
  disabledHint?: string;
};

// A control grown to the touch floor rather than given an invisible hit area.
const target = { minHeight: TOUCH_TARGET, minWidth: TOUCH_TARGET } as const;

export function FilterChipRow({
  chips,
  onToggle,
  label,
}: {
  chips: FilterChipModel[];
  onToggle: (token: string) => void;
  label: string;
}) {
  return (
    <Box
      role="group"
      aria-label={label}
      sx={{
        display: 'flex',
        gap: 1,
        // One scrolling line on the phone, a wrapping block from `sm` up. The
        // chips carry their own scroll-snap points so a swipe lands on a chip
        // instead of halfway through one.
        flexWrap: { xs: 'nowrap', sm: 'wrap' },
        overflowX: { xs: 'auto', sm: 'visible' },
        scrollSnapType: { xs: 'x mandatory', sm: 'none' },
        // The focus ring is drawn OUTSIDE the chip; without the padding the
        // scroll container would clip it on the first and last chip.
        px: '2px',
        py: '2px',
      }}
    >
      {chips.map((chip) => (
        <Chip
          key={chip.token}
          size="small"
          clickable
          // The chips are a set of independent toggles, not a radio group — the
          // pressed state has to be announced, and the colour alone must not
          // carry it (Idee 19).
          aria-pressed={chip.active}
          color={chip.active ? 'primary' : 'default'}
          variant={chip.active ? 'filled' : 'outlined'}
          onClick={() => onToggle(chip.token)}
          label={`${chip.active ? '✓ ' : ''}${chip.label}${chip.count === null ? '' : ` · ${chip.count}`}`}
          sx={{ ...target, borderRadius: `${TOUCH_TARGET / 2}px`, flex: '0 0 auto', scrollSnapAlign: 'start' }}
        />
      ))}
    </Box>
  );
}

export function ListSortSwitch({
  sort,
  options,
  onChange,
  label,
}: {
  sort: string;
  options: SortOptionModel[];
  onChange: (token: string) => void;
  label: string;
}) {
  // WHY a sort cannot be chosen is a reason the reader acts on („kein Score
  // gelesen"), and a disabled button takes no focus — so in a tooltip it was
  // reachable by mouse alone (V25). It stands under the switch as text, and the
  // disabled button points at ITS OWN line with `aria-describedby` so a screen
  // reader hears the two together.
  //
  // One line per blocked option, each named by the option it belongs to: three
  // overviews mount this component, a page can show more than one blocked
  // option, and a single merged sentence („kein Score gelesen · keine Spur")
  // leaves the reader to guess which greyed button it explains. The id prefix
  // comes from `useId` for the same reason — a hard-coded one is a duplicate
  // waiting for two instances to meet on one screen.
  const blocked = options.filter((option) => option.disabled && option.disabledHint);
  const hintBase = useId();
  const hintId = (token: string) => `${hintBase}${token}`;
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, alignItems: 'flex-start' }}>
      <ToggleButtonGroup
        size="small"
        exclusive
        value={sort}
        onChange={(_, value: string | null) => value && onChange(value)}
        aria-label={label}
      >
        {options.map((option) => (
          <ToggleButton
            key={option.token}
            value={option.token}
            disabled={option.disabled}
            aria-describedby={option.disabled && option.disabledHint ? hintId(option.token) : undefined}
            sx={target}
          >
            {option.label}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
      {blocked.map((option) => (
        <Typography key={option.token} id={hintId(option.token)} variant="caption" color="text.secondary">
          {`${option.label} — ${option.disabledHint}`}
        </Typography>
      ))}
    </Box>
  );
}

export function ListViewSwitch({ view, onChange }: { view: ListView; onChange: (view: ListView) => void }) {
  const t = de.admin.liste;
  return (
    <ToggleButtonGroup
      size="small"
      exclusive
      value={view}
      onChange={(_, value: ListView | null) => value && onChange(value)}
      aria-label={t.viewLabel}
    >
      {LIST_VIEWS.map((value) => (
        <ToggleButton key={value} value={value} sx={target}>
          {value === 'liste' ? t.viewList : t.viewGallery}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
}

/**
 * Pages of a fixed size plus „alle zeigen" as the last entry (author question
 * Q6, option a). Absent entirely while everything fits on one page — a pager
 * that offers exactly one page is furniture.
 */
export function ListPager({
  page,
  total,
  onChange,
}: {
  page: ListPage;
  total: number;
  onChange: (page: ListPage) => void;
}) {
  const t = de.admin.liste;
  const count = pageCount(total);
  if (count <= 1) return null;
  const pages = Array.from({ length: count }, (_, i) => i + 1);
  return (
    <ToggleButtonGroup
      size="small"
      exclusive
      value={page}
      onChange={(_, value: ListPage | null) => value !== null && onChange(value)}
      aria-label={t.pagerLabel}
      sx={{ flexWrap: 'wrap' }}
    >
      {pages.map((n) => (
        <ToggleButton key={n} value={n} aria-label={fmt(t.pageAria, { n })} sx={target}>
          {n}
        </ToggleButton>
      ))}
      <ToggleButton value={PAGE_ALL} sx={target}>
        {t.pageAll}
      </ToggleButton>
    </ToggleButtonGroup>
  );
}

/**
 * One row of a work list: the subject, its chips and numbers, and the existing
 * card as the body it expands INTO. The card is mounted only while the row is
 * open (`unmountOnExit`), which is what keeps a collapsed list free of images.
 */
export function WorkRow({
  expanded,
  onToggle,
  expandLabel,
  title,
  chips,
  actions,
  subline,
  children,
}: {
  expanded: boolean;
  onToggle: () => void;
  // Names the SUBJECT, because a list of 63 rows would otherwise offer 63
  // buttons all called „Aufklappen".
  expandLabel: string;
  title: ReactNode;
  chips?: ReactNode;
  actions?: ReactNode;
  // The second line of a collapsed row — the numbers behind the chips (for a
  // letter: where its score went). Text only; an image belongs in the body.
  subline?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Box
      sx={{
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        px: 1.5,
        py: 1,
        bgcolor: 'background.paper',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        <Button
          size="small"
          onClick={onToggle}
          aria-expanded={expanded}
          aria-label={expandLabel}
          endIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          sx={{ ...target, justifyContent: 'flex-start', textAlign: 'left', px: 1 }}
        >
          {title}
        </Button>
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center', flex: 1, minWidth: 0 }}>
          {chips}
        </Box>
        {actions}
      </Box>
      {subline && <Box sx={{ pl: 1, pb: 0.5 }}>{subline}</Box>}
      <Collapse in={expanded} unmountOnExit>
        {children}
      </Collapse>
    </Box>
  );
}

/**
 * „Nichts gefunden" with its CAUSE — three silences kept apart. A source that
 * holds no rows at all is a different answer from a filter that matches none;
 * and a ticked chip whose evidence has not arrived is not an answer at all, so
 * it may not borrow the second one's wording. Only the last two can be undone
 * with a button.
 */
export function ListEmpty({
  filtered,
  pending,
  emptyText,
  onReset,
}: {
  filtered: boolean;
  /** A ticked filter's underlying read has not answered — nothing is claimed. */
  pending?: boolean;
  emptyText: string;
  onReset: () => void;
}) {
  const t = de.admin.liste;
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 1, py: 2 }}>
      <Typography variant="body2" color="text.secondary">
        {pending ? t.emptyPending : filtered ? t.emptyFiltered : emptyText}
      </Typography>
      {filtered && (
        <Button size="small" variant="outlined" onClick={onReset} sx={target}>
          {t.resetFilters}
        </Button>
      )}
    </Box>
  );
}
