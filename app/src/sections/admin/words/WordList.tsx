// The Wörter overview as a compact work list — the default since V14.
//
// One line per Wortprobe: the word, its specimen id, how many Bahnen are
// stored for it, where it stands in the Nachfahr-Pass, whether it belongs to
// another writer's plate, what the basket holds against it, and its Loss once
// somebody has paid for one. NO image — the card wall this replaces stacked
// 169 specimens at two faces of 220 px each, so the first question („welche
// Probe braucht Arbeit?") cost minutes of scrolling.
//
// The two faces are one click away and stay in place: a row expands INTO the
// existing `WordCard`, and only an open row mounts it — which is why no
// collapsed row loads a single byte of ink (a jsdom test pins exactly that).

import { Box, Button, Chip, Typography } from '@mui/material';
import { useState } from 'react';

import { de, fmt } from '@/locales/admin';
import { ScoreChip, WordCard } from '@/sections/admin/compare/WordCard';
import { WorkRow } from '@/sections/admin/shell/WorkList';
import { TOUCH_TARGET } from '@/styles/hitArea';
import { garamond } from '@/styles/paper';

import type { WordRow } from './wordRows';

/** The second line of a row: which plate this Wortprobe was cut from, and
 * whose hand wrote it — empty where the id only repeats the word above it. */
function subline(row: WordRow): string {
  const parts = [
    row.sampleId === row.word ? '' : row.sampleId,
    row.foreignSet ?? '',
    // What the two flagged states MEAN, as text on the row. Both used to hang
    // in a hover over an unfocusable chip; the clipped specimen's own note is
    // authored free text and may never need a mouse (V25). Short forms, because
    // a work-list row is one line — the long sentences stay in the card.
    row.foreign ? de.admin.werkbank.foreignSetShort : '',
    row.status === 'incomplete' ? row.sample.note || de.admin.compare.incompleteChipHint : '',
  ].filter(Boolean);
  return parts.join(' · ');
}

export function WordList({
  rows,
  sourceId,
  cropCacheBust,
  overlay,
  onPick,
}: {
  // Already filtered, sorted and paged by the overview.
  rows: WordRow[];
  sourceId: string;
  cropCacheBust: number;
  overlay: boolean;
  onPick: (row: WordRow) => void;
}) {
  const t = de.admin.words;
  // Which rows are open. Deliberately NOT in the URL, for the reason
  // `LetterList` states: the list state a link carries is what the reader is
  // looking FOR, while an expanded row is where they happen to be looking.
  const [expanded, setExpanded] = useState<ReadonlySet<string>>(() => new Set());
  const toggle = (sampleId: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (!next.delete(sampleId)) next.add(sampleId);
      return next;
    });

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75, maxWidth: 1400 }}>
      {rows.map((row) => {
        const open = expanded.has(row.sampleId);
        return (
          <WorkRow
            key={row.sampleId}
            expanded={open}
            onToggle={() => toggle(row.sampleId)}
            expandLabel={fmt(open ? t.rowCollapse : t.rowExpand, { word: row.word })}
            title={
              <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
                <Typography component="span" sx={{ fontFamily: garamond, fontSize: 24, lineHeight: 1.2 }}>
                  {row.word}
                </Typography>
              </Box>
            }
            chips={
              <>
                {/* The Loss first — it is what „Schlechteste zuerst" sorts by,
                    and it is simply absent until the sweep has run: an
                    unmeasured Wortprobe carries no number, never a zero. */}
                {row.score && <ScoreChip score={row.score} />}
                {/* „n Bahnen" and the Nachfahr-Status are two statements, not
                    one: a harvested fit is a stored Bahn too, and only an
                    authored one is the author's own pen work. */}
                {row.traces > 0 && (
                  <Chip
                    size="small"
                    variant="outlined"
                    label={fmt(row.traces === 1 ? t.traceCountOne : t.traceCount, { count: row.traces })}
                  />
                )}
                {/* All three chips carried their explanation in a hover over a
                    plain `div` — no keyboard, no touch. The chips keep their
                    words; the sentences move into the row's ONE `InfoHint`
                    below, and the clipped specimen's authored note becomes the
                    subline (V25, design-system.md §9.4). */}
                {row.status === 'authored' ? (
                  <Chip size="small" color="success" label={de.admin.compare.authoredChip} />
                ) : row.status === 'incomplete' ? (
                  <Chip size="small" color="warning" variant="outlined" label={de.admin.compare.incompleteChip} />
                ) : (
                  <Chip size="small" variant="outlined" label={de.admin.compare.statusOpen} />
                )}
                {/* The foreign writer's samples are announced, not folded in —
                    a separate chip under their own name is the only way both
                    statements stay true (V4). */}
                {row.foreign && <Chip size="small" variant="outlined" label={de.admin.compare.tabOther} />}
                {/* The basket read is admin-gated: `null` stays silent rather
                    than reporting a clean Wortprobe. */}
                {row.korbOpen !== null && row.korbOpen > 0 && (
                  <Chip size="small" color="warning" label={fmt(de.admin.liste.chipKorb, { count: row.korbOpen })} />
                )}
              </>
            }
            actions={
              <Button
                size="small"
                onClick={() => onPick(row)}
                aria-label={fmt(de.admin.compare.openWordFor, { word: row.word })}
                sx={{ minHeight: TOUCH_TARGET, minWidth: TOUCH_TARGET }}
              >
                {de.admin.compare.openWord}
              </Button>
            }
            // Which plate the Wortprobe was cut from — text, so a collapsed
            // row stays image-free. The id is left out where it only repeats
            // the word: most of this sidecar's ids ARE the word, and a line
            // that says „unter" under „unter" reads as a rendering fault.
            subline={
              subline(row) ? (
                <Typography variant="caption" color="text.secondary">
                  {subline(row)}
                </Typography>
              ) : undefined
            }
          >
            {/* No frame and no header of its own — the row around it already
                carries the word, its chips and the way in. Keyed on the reload
                stamp like the gallery's card, so „Neu laden" really recomposes
                an open row instead of leaving it on its cached faces. */}
            <WordCard
              key={`${row.sampleId}:${cropCacheBust}`}
              sample={row.sample}
              sourceId={sourceId}
              overlay={overlay}
              traced={row.traced}
              status={row.status}
              bust={cropCacheBust}
              score={row.score ?? undefined}
              framed={false}
              header={false}
            />
          </WorkRow>
        );
      })}
    </Box>
  );
}
