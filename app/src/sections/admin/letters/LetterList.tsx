// The Buchstaben overview as a compact work list — the default since V14.
//
// One line per authored letter: the glyph, its key, the stored score with its
// deductions, and the chips that say what is missing (gesperrt · Laufform ·
// Vorkommen · offene Korb-Aufträge). NO image: the card wall this replaces was
// about ten thousand pixels tall, so the first question („welcher Buchstabe
// braucht Arbeit?") cost a minute of scrolling to answer.
//
// The four faces are one click away and stay in place: a row expands INTO the
// existing `CompareCard`, and only an open row mounts it — which is why no
// collapsed row loads a single byte of ink (a jsdom test pins exactly that).
//
// Everything the rows are built from is already in the browser: the workbench
// layer's occurrences, the admin context's bboxes and template rows, the
// basket's own read. This surface adds no request of its own.

import { Box, Button, Chip, Typography } from '@mui/material';
import { useState } from 'react';

import { useRovingList } from '@/hooks/useRovingList';
import type { AggregateOut, InstanceOut } from '@/lib/api';
import { de, fmt } from '@/locales/admin';
import { CompareCard } from '@/sections/admin/compare/CompareCard';
import { ScoreBreakdownInline, ScoreChip, ScoreHelp } from '@/sections/admin/quality/scoreParts';
import { WorkRow } from '@/sections/admin/shell/WorkList';
import { garamond } from '@/styles/paper';
import { TOUCH_TARGET } from '@/styles/hitArea';

import type { LetterRow } from './letterRows';

export function LetterList({
  rows,
  sourceId,
  cropCacheBust,
  reloadKey,
  overlay,
  aggregatesByKey,
  instancesByKey,
  statsHint,
  occurrencesKnown,
  onPick,
}: {
  // Already filtered, sorted and paged by the overview.
  rows: LetterRow[];
  sourceId: string;
  cropCacheBust: number;
  reloadKey: number;
  overlay: boolean;
  aggregatesByKey: Map<string, AggregateOut>;
  instancesByKey: Map<string, InstanceOut[]>;
  statsHint: string;
  occurrencesKnown: boolean;
  onPick: (glyphKey: string) => void;
}) {
  const t = de.admin.letters;
  // Which rows are open. Deliberately NOT in the URL: the list state a link
  // carries is what the reader is looking FOR (filter, sort, page), while an
  // expanded row is where they happen to be looking right now — and a Korb link
  // that reopened three arbitrary accordions would be noise.
  const [expanded, setExpanded] = useState<ReadonlySet<string>>(() => new Set());
  const toggle = (glyphKey: string) =>
    setExpanded((prev) => {
      const next = new Set(prev);
      if (!next.delete(glyphKey)) next.add(glyphKey);
      return next;
    });
  // One tab stop for the whole list; ↑/↓ walk the letters, ←/→ the controls of
  // the row you stand on. Keyed on the glyph key, so a filter or a page change
  // hands the stop to the row that takes the place of the one that left.
  const roving = useRovingList();

  return (
    <Box {...roving.containerProps} sx={{ display: 'flex', flexDirection: 'column', gap: 0.75, maxWidth: 1400 }}>
      {rows.map((row) => {
        const open = expanded.has(row.glyphKey);
        return (
          <WorkRow
            key={row.glyphKey}
            rowProps={roving.rowProps(row.glyphKey)}
            expanded={open}
            onToggle={() => toggle(row.glyphKey)}
            expandLabel={fmt(open ? t.rowCollapse : t.rowExpand, { key: row.glyphKey })}
            title={
              <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
                <Typography component="span" sx={{ fontFamily: garamond, fontSize: 24, lineHeight: 1.2 }}>
                  {row.letterGlyph}
                </Typography>
                <Typography component="span" variant="caption" color="textSecondary">
                  {row.glyphKey}
                </Typography>
              </Box>
            }
            chips={
              <>
                {/* The score first — it is what „Schlechteste zuerst" sorts by.
                    Three states, not two, exactly as the card keeps them: while
                    the admin read is in flight the row says NOTHING, and only
                    once it has answered is „kein Score" a claim about this
                    form rather than about the read. */}
                {!row.scoreKnown ? null : row.score !== null ? (
                  <ScoreChip score={row.score} />
                ) : (
                  // The reason a form carries no score used to hang in this
                  // chip's tooltip — on a `div`, so neither keyboard nor finger
                  // ever reached it. It is one of the lines of `ScoreHelp` now,
                  // which an unscored row carries beside the chip (a scored one
                  // gets it from the breakdown in its subline).
                  <>
                    <Chip size="small" variant="outlined" label={de.admin.compare.scoreNone} />
                    <ScoreHelp />
                  </>
                )}
                {row.locked && <Chip size="small" variant="outlined" label={t.stateLocked} />}
                {/* Both directions are stated, because a missing chip would
                    otherwise be ambiguous with „noch nicht geladen". */}
                <Chip
                  size="small"
                  variant="outlined"
                  color={row.hasLaufform ? 'default' : 'warning'}
                  label={row.hasLaufform ? t.chipLaufform : t.chipNoLaufform}
                />
                {/* „0 Vorkommen" is a claim about the plates — it waits for the
                    read that can support it. */}
                {row.occurrences === null ? (
                  <Typography variant="caption" color="textDisabled">
                    {de.admin.compare.occurrencesUnknown}
                  </Typography>
                ) : (
                  <Chip
                    size="small"
                    variant="outlined"
                    label={fmt(t.occurrenceCount, { count: row.occurrences })}
                  />
                )}
                {/* The basket read is admin-gated: `null` stays silent rather
                    than reporting a clean letter. */}
                {row.korbOpen !== null && row.korbOpen > 0 && (
                  <Chip size="small" color="warning" label={fmt(de.admin.liste.chipKorb, { count: row.korbOpen })} />
                )}
              </>
            }
            actions={
              <Button
                size="small"
                onClick={() => onPick(row.glyphKey)}
                aria-label={fmt(de.admin.compare.openLetterFor, { key: row.glyphKey })}
                sx={{ minHeight: TOUCH_TARGET, minWidth: TOUCH_TARGET }}
              >
                {de.admin.compare.openLetter}
              </Button>
            }
            // Where the score went — the same wording and colours as the card's
            // own line, and text, so a collapsed row stays image-free.
            subline={row.quality ? <ScoreBreakdownInline quality={row.quality} /> : undefined}
          >
            {/* No frame and no header of its own — the row around it already
                carries the letter, its key, its chips and the way in.

                Keyed like the gallery's card (`GlyphComparison.tsx`): the
                per-card „this letter has no Laufform" answer is a one-way flag,
                so a re-derive or „Neu laden" has to throw the instance away
                rather than leave an open row asserting the old answer. */}
            <CompareCard
              key={`${row.glyphKey}:${cropCacheBust}:${reloadKey}`}
              glyphKey={row.glyphKey}
              letterGlyph={row.letterGlyph}
              sourceId={sourceId}
              cropCacheBust={cropCacheBust}
              reloadKey={reloadKey}
              overlay={overlay}
              aggregate={aggregatesByKey.get(row.glyphKey)}
              occurrences={instancesByKey.get(row.glyphKey) ?? []}
              quality={row.quality}
              statsHint={statsHint}
              occurrencesKnown={occurrencesKnown}
              framed={false}
              header={false}
            />
          </WorkRow>
        );
      })}
    </Box>
  );
}
