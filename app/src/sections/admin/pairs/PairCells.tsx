// One row of the pair matrix, in either of its two shapes — and nothing else:
// no fetching, no URL, no vocabulary. What a cell says is decided by
// `pairRows.ts`, what it looks like is decided here, and that split is what
// makes „does a collapsed matrix draw pictures?" a question a jsdom test can
// ask without an admin context behind it.
//
// The default shape is the COUNTER cell (V14 · plan §7.2 „Zähler statt
// Farbe"): the combination, how often the plates wrote it, what the library
// stores for it and how many basket items point at it — all as words, because
// the border colour this replaces was the one piece of state on the whole
// overview that a red-green-deficient reader could not read (Idee 19). The
// mini render is the gallery's job, and a mini render is one server
// composition per cell.

import { Box, ButtonBase, Typography } from '@mui/material';

import { WrittenWord } from '@/components/WrittenWord';
import { useInView } from '@/hooks/useInView';
import { useRovingList } from '@/hooks/useRovingList';
import { de, fmt } from '@/locales/admin';
import type { PairRow } from '@/sections/admin/pairs/pairRows';
import type { ListView } from '@/sections/admin/shell/listState';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { garamond } from '@/styles/paper';

const CELL_H = 88; // px — big enough to judge a join, small enough for a grid

/**
 * The three counters as text. Absent where the read behind one has not
 * answered: the grid says so once, above itself, rather than 60 times.
 *
 * All three stand in the cell's own ink (17.07:1 on the white cell, measured),
 * and none of them is tinted. Two reasons, and the second is the stronger one:
 * the counters ARE the cell's content now that it draws no picture, so dimming
 * them would recede the only thing it says; and the tint this replaces would
 * have to be the warning ochre, which measures 3.37:1 on white — enough for a
 * graphical object (§9, WCAG 1.4.11) and NOT enough for text. What tells the
 * three counters apart is the word beside each number, which is the whole
 * point of „Zähler statt Farbe" (Idee 19).
 */
function Counters({ row }: { row: PairRow }) {
  const t = de.admin.pairs;
  if (row.leftKey === null) {
    return <Typography variant="caption">{t.ligature}</Typography>;
  }
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', lineHeight: 1.3 }}>
      {row.plate !== null && (
        <Typography variant="caption">{fmt(de.admin.joins.occurrenceCount, { count: row.plate })}</Typography>
      )}
      {row.override !== null && (
        <Typography variant="caption">
          {row.override === 'approved'
            ? t.badgeApproved
            : row.override === 'draft'
              ? t.badgeDraft
              : de.admin.joins.generated}
        </Typography>
      )}
      {row.korbOpen !== null && row.korbOpen > 0 && (
        // The ⚑ is the second channel the basket count needs — it is the one
        // counter that asks for an action, and it may not lean on a hue to
        // say so.
        <Typography variant="caption">{`⚑ ${fmt(de.admin.liste.chipKorb, { count: row.korbOpen })}`}</Typography>
      )}
    </Box>
  );
}

/**
 * What a screen reader hears instead of the cell. An `aria-label` REPLACES the
 * content as the accessible name, so it has to carry the counters too — they
 * are the whole point of „Zähler statt Farbe", and a label that said only
 * „Verbindung ab öffnen" would hand a screen-reader user exactly the cell that
 * states nothing, which is what this change set out to remove. Without the ⚑:
 * the flag is a second visual channel for the basket count and reads as
 * „schwarze Flagge" out loud.
 */
function cellLabel(row: PairRow): string {
  const t = de.admin.pairs;
  const parts = [fmt(t.openPair, { pair: row.text })];
  if (row.leftKey === null) {
    parts.push(t.ligature);
  } else {
    if (row.plate !== null) parts.push(fmt(de.admin.joins.occurrenceCount, { count: row.plate }));
    if (row.override !== null) {
      parts.push(
        row.override === 'approved' ? t.badgeApproved : row.override === 'draft' ? t.badgeDraft : de.admin.joins.generated,
      );
    }
    if (row.korbOpen !== null && row.korbOpen > 0) {
      parts.push(fmt(de.admin.liste.chipKorb, { count: row.korbOpen }));
    }
  }
  return parts.join(' · ');
}

function PairCell({
  row,
  sourceId,
  view,
  onPick,
  rowProps,
}: {
  row: PairRow;
  sourceId: string;
  view: ListView;
  onPick?: () => void;
  rowProps: Record<string, string>;
}) {
  const [ref, inView] = useInView<HTMLDivElement>();
  return (
    <Box
      ref={ref}
      {...rowProps}
      component={onPick ? ButtonBase : Box}
      onClick={onPick}
      aria-label={onPick ? cellLabel(row) : undefined}
      sx={{
        border: 1,
        // The border no longer carries the override state — it is a box, not a
        // statement (the statement is the word inside it).
        borderColor: 'divider',
        borderRadius: 1,
        bgcolor: '#fff',
        p: 0.75,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 0.25,
        minWidth: 96,
        minHeight: TOUCH_TARGET,
        cursor: onPick ? 'pointer' : 'default',
      }}
    >
      <Typography component="span" sx={{ fontFamily: garamond, fontSize: 20, lineHeight: 1.2 }}>
        {row.text}
      </Typography>
      <Counters row={row} />
      {view === 'galerie' && (
        <Box sx={{ height: CELL_H, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {inView && (
            <WrittenWord text={row.text} sourceId={sourceId} height={CELL_H} animate={false} showLineature />
          )}
        </Box>
      )}
    </Box>
  );
}

export function PairCellGrid({
  rows,
  sourceId,
  view,
  onPick,
}: {
  rows: PairRow[];
  sourceId: string;
  view: ListView;
  onPick: (leftKey: string, rightKey: string) => void;
}) {
  // A WRAPPING grid, so the roving is horizontal: ←/→ walk the cells, Home/End
  // jump to the ends, and ↑/↓ do nothing at all. A flex grid re-wraps with the
  // window, so it has no stable column count to step down through — a Down that
  // jumped six cells at 1440 px and three at 1024 px would be worse than none
  // (`lib/roving.ts`). Before this each grid was ~60 tab stops.
  const roving = useRovingList({ orientation: 'horizontal' });
  return (
    <Box {...roving.containerProps} sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
      {rows.map((row) => (
        <PairCell
          // The page/view is part of the key because `useInView` is one-shot:
          // a cell swapped in under an old key would keep the previous one's
          // „already seen" flag and never fetch its own render.
          key={`${row.text}:${view}`}
          rowProps={roving.rowProps(row.text)}
          row={row}
          sourceId={sourceId}
          view={view}
          onPick={
            row.leftKey && row.rightKey
              ? () => onPick(row.leftKey as string, row.rightKey as string)
              : undefined
          }
        />
      ))}
    </Box>
  );
}
