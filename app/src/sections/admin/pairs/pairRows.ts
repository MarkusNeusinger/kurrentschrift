// The Übergänge overview as CELLS that say something — what one cell of the
// matrix knows about its combination, which filters it answers to and how the
// two rows are ordered.
//
// Pure and JSX-free, the twin of `letters/letterRows.ts`. The rule it exists
// for is the plan's Idee 19: today a cell states its override as a BORDER
// COLOUR plus a chip, and states neither its plate occurrences nor its open
// basket items at all. A reader who cannot separate the success green from the
// warning amber therefore reads the whole matrix as „nothing stored anywhere".
// Every counter below is TEXT with a word beside it, and the cell that carries
// it needs no picture — which is what makes a matrix of ~60 combinations
// readable without ~60 server compositions.
//
// Three of the four facts are ANSWERS that may be missing, and each stays
// `null` rather than 0: the occurrence layer is public but may be in flight or
// have failed, the override list and the basket are admin-gated and may 401.
// „Keine Vorkommen" and „kein Override" are claims about the plates and about
// the library; neither may be made on a read that never landed.

import type { Letter } from '@/domain/glyphs';
import { glyphKeyFor } from '@/domain/glyphs';
import type { GlyphPairOut } from '@/lib/api';
import { pairCellKey } from '@/sections/admin/pairs/pairRow';
import { pairKeysOf } from '@/sections/admin/pairs/pairKeys';
import { pairCountKey } from '@/sections/admin/shell/korbTargets';
import type { ListSpec } from '@/sections/admin/shell/listState';

export const PAIR_FILTERS = ['mit-uebersteuerung', 'mit-korb', 'ohne-vorkommen'] as const;
export type PairFilter = (typeof PAIR_FILTERS)[number];

export const PAIR_SORTS = ['alphabet', 'vorkommen'] as const;
export type PairSort = (typeof PAIR_SORTS)[number];

/** The matrix is read along the alphabet by default — it is a grid before it
 * is a work list, and the anchor letter already narrows it to ~60 cells. */
export const PAIR_LIST_SPEC: ListSpec<PairFilter, PairSort> = {
  filters: PAIR_FILTERS,
  sorts: PAIR_SORTS,
  defaultSort: 'alphabet',
};

/** What the library holds for this combination. `none` is an answer; `null`
 * (on the row) is the absence of one. */
export type PairOverrideState = 'none' | 'draft' | 'approved';

export type PairRow = {
  // The two characters as they are written and composed — the cell's caption
  // and, in the gallery, the text `/write/word` is asked for.
  text: string;
  // null for a combination that folds into ONE glyph (ch, ck, tz, ſt, qu, ß):
  // there is no join to inspect, to override or to file a task against, so the
  // cell carries no counters and cannot be opened.
  leftKey: string | null;
  rightKey: string | null;
  // null = the occurrence layer has not answered (loading, or failed).
  plate: number | null;
  // null = the override list has not answered (loading, or admin-gated 401).
  override: PairOverrideState | null;
  // null = the basket read has not answered; 0 = it did and this join is clean.
  korbOpen: number | null;
};

export type PairRowInput = {
  /** The letter the grid is anchored on. */
  anchor: Letter;
  /** Authored lowercase letters, registry order — the right side of any join. */
  lower: readonly Letter[];
  /** Authored capitals; they only ever stand on the LEFT (architektur.md §4). */
  upper: readonly Letter[];
  /** Plate occurrences per „left→right"; null while the layer is unknown. */
  pairsByKey: Map<string, readonly unknown[]> | null;
  /** Stored override rows per `pairCellKey`; null while unknown. */
  overrideRows: Map<string, GlyphPairOut> | null;
  /** Open basket items per „left→right"; null while unknown. */
  korbByPair: Map<string, number> | null;
};

function rowFor(text: string, input: PairRowInput): PairRow {
  const keys = pairKeysOf(text);
  if (!keys) return { text, leftKey: null, rightKey: null, plate: null, override: null, korbOpen: null };
  const [leftKey, rightKey] = keys;
  const occurrenceKey = pairCountKey(leftKey, rightKey);
  const stored = input.overrideRows?.get(pairCellKey(leftKey, rightKey));
  return {
    text,
    leftKey,
    rightKey,
    plate: input.pairsByKey === null ? null : (input.pairsByKey.get(occurrenceKey)?.length ?? 0),
    override:
      input.overrideRows === null ? null : !stored ? 'none' : stored.approved ? 'approved' : 'draft',
    korbOpen: input.korbByPair === null ? null : (input.korbByPair.get(occurrenceKey) ?? 0),
  };
}

/**
 * The two rows of the matrix: the anchor as the FIRST letter of a combination
 * (against every authored lowercase letter), and — for a lowercase anchor — as
 * the second one. A capital gets only the first row, because Kurrent and
 * Sütterlin capitals open a word and never sit on the right of a join.
 */
export function buildPairRows(input: PairRowInput): { asFirst: PairRow[]; asSecond: PairRow[] } {
  const anchorGlyph = input.anchor.glyph;
  const asFirst = input.lower.map((right) => rowFor(anchorGlyph + right.glyph, input));
  const asSecond =
    input.anchor.group === 'lower'
      ? [...input.lower, ...input.upper]
          .filter((left) => left.glyph !== anchorGlyph)
          .map((left) => rowFor(left.glyph + anchorGlyph, input))
      : [];
  return { asFirst, asSecond };
}

/**
 * Whether one cell answers one filter. An UNKNOWN fact never answers: while the
 * override list is still loading, „mit Übersteuerung" would select nothing and
 * read as „es gibt keine" — and a ligature cell, which has no join at all, is
 * never selected by any of the three.
 */
export function matchesPairFilter(row: PairRow, filter: PairFilter): boolean {
  if (filter === 'mit-uebersteuerung') return row.override === 'draft' || row.override === 'approved';
  if (filter === 'mit-korb') return (row.korbOpen ?? 0) > 0;
  return row.plate === 0;
}

/** The chips ANDed — every ticked one has to hold. */
export const matchesPairFilters = (row: PairRow, filters: readonly PairFilter[]): boolean =>
  filters.every((filter) => matchesPairFilter(row, filter));

/**
 * How many cells EACH chip would select on its own, over both rows — the number
 * on the chip. Not „how many would remain beside the other ticked chips": a
 * count that changes with its neighbours cannot be read as „so viele gibt es".
 *
 * `null` where the chip's own read has not answered, for the same reason the
 * cells print no zero then.
 */
export function pairFilterCounts(rows: readonly PairRow[]): Record<PairFilter, number | null> {
  const unknown: Record<PairFilter, boolean> = {
    'mit-uebersteuerung': rows.some((row) => row.override === null && row.leftKey !== null),
    'mit-korb': rows.some((row) => row.korbOpen === null && row.leftKey !== null),
    'ohne-vorkommen': rows.some((row) => row.plate === null && row.leftKey !== null),
  };
  const counts = {} as Record<PairFilter, number | null>;
  for (const filter of PAIR_FILTERS) {
    counts[filter] = unknown[filter] ? null : rows.filter((row) => matchesPairFilter(row, filter)).length;
  }
  return counts;
}

/**
 * Alphabet = the order the cells were built in; „Meiste Vorkommen" = descending
 * plate count with the unmeasured cells at the end — a combination no plate
 * wrote is not the best-written one, it is the one with no evidence. Ties keep
 * the alphabet, so the grid does not reshuffle under equal counts.
 */
export function sortPairRows(rows: readonly PairRow[], sort: PairSort): PairRow[] {
  if (sort === 'alphabet') return [...rows];
  return rows
    .map((row, index) => ({ row, index }))
    .sort((a, b) => (b.row.plate ?? -1) - (a.row.plate ?? -1) || a.index - b.index)
    .map((entry) => entry.row);
}

/** Is there anything to rank by? Without a single measured occurrence the
 * „Meiste Vorkommen" order would silently be the alphabet again. */
export const pairsRankable = (rows: readonly PairRow[]): boolean => rows.some((row) => (row.plate ?? 0) > 0);

/** The authored letters of one group, in registry order — the grid's two axes.
 * Kept here beside the rows so the matrix component holds no vocabulary. */
export const authoredLetters = (
  letters: readonly Letter[],
  hasCanonical: (glyphKey: string) => boolean,
): { lower: Letter[]; upper: Letter[] } => ({
  lower: letters.filter((letter) => letter.group === 'lower' && hasCanonical(glyphKeyFor(letter))),
  upper: letters.filter((letter) => letter.group === 'upper' && hasCanonical(glyphKeyFor(letter))),
});
