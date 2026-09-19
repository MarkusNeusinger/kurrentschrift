// The Buchstaben overview as ROWS — what one line of the work list knows about
// a letter, which filters it answers to and how the list is ordered.
//
// Pure and JSX-free on purpose (the idiom of `shell/korbFilter.ts`): the truth
// table of four filters ANDed, and the rule „a letter without a score sorts
// last", are worth a unit test and worthless to read out of a component.
//
// The vocabularies below are declared as DATA rather than derived from the
// locale's keys, for the reason `korbFilter.ts:55-64` spells out: a
// `Record<Token, string>` guarantees that every token is named, never that the
// record carries nothing else — a renamed token whose old locale key survived
// would ship as a chip that can never match, and the chip ORDER would be a side
// effect of how the locale file happens to be written.
//
// Two of the five facts per row are not measurements but ANSWERS that may be
// missing, and both stay `null` rather than 0: the occurrence layer is public
// but may still be in flight or have failed, and the score read is admin-gated
// and may 401. „0 Vorkommen" and „kein Score" are claims about the plates and
// about the row; neither may be made on a read that never landed.

import { glyphKeyFor, LETTERS } from '@/domain/glyphs';
import type { BboxOut, InstanceOut, QualityData } from '@/lib/api';
import type { ListSpec } from '@/sections/admin/shell/listState';

export const LETTER_FILTERS = ['gesperrt', 'ohne-laufform', 'ohne-vorkommen', 'mit-korb'] as const;
export type LetterFilter = (typeof LETTER_FILTERS)[number];

export const LETTER_SORTS = ['alphabet', 'schlechteste'] as const;
export type LetterSort = (typeof LETTER_SORTS)[number];

/** Q6 (a): the overview is an overview first, so the alphabet is the default. */
export const LETTER_LIST_SPEC: ListSpec<LetterFilter, LetterSort> = {
  filters: LETTER_FILTERS,
  sorts: LETTER_SORTS,
  defaultSort: 'alphabet',
};

export type LetterRow = {
  glyphKey: string;
  // The character itself, for the row's own title — a list of keys would be
  // unreadable for exactly the glyphs that need work (`longs`, `sz`, `ch`).
  letterGlyph: string;
  locked: boolean;
  // Whether a running form (variant 100) is stored. Read from the TEMPLATE
  // rows, not from a failed render: a list without images cannot probe.
  hasLaufform: boolean;
  // null = the occurrence layer has not answered (loading, or failed).
  occurrences: number | null;
  // Has the admin score read answered AT ALL? False while it is in flight —
  // without it `score: null` would mean two different things, and the row would
  // print „kein Score" about a read that has not landed (`CompareCard` keeps
  // the same two states apart as `undefined` vs `null`).
  scoreKnown: boolean;
  // null = the score read answered and this row carries none, or it 401'd.
  score: number | null;
  quality: QualityData | null;
  // null = the basket read has not answered; 0 = it did and this letter is clean.
  korbOpen: number | null;
};

export type LetterRowInput = {
  /** The authored letters, in registry order — `glyphsByKey[key].has_data`. */
  authoredKeys: string[];
  bboxesByKey: Record<string, BboxOut>;
  laufformKeys: Set<string>;
  instancesByKey: Map<string, InstanceOut[]>;
  /** null while the score read is in flight; a Map once it answered. */
  quality: Map<string, QualityData | null> | null;
  /** null while the basket read is unknown. */
  korbByGlyph: Map<string, number> | null;
  /** Has the public occurrence layer answered at all? */
  occurrencesKnown: boolean;
};

/**
 * One row per AUTHORED letter, in the registry's order (which is the alphabet
 * plus the trailing groups — the same order the card wall used).
 */
export function buildLetterRows(input: LetterRowInput): LetterRow[] {
  const authored = new Set(input.authoredKeys);
  const rows: LetterRow[] = [];
  for (const letter of LETTERS) {
    const glyphKey = glyphKeyFor(letter);
    if (!authored.has(glyphKey)) continue;
    const quality = input.quality === null ? null : (input.quality.get(glyphKey) ?? null);
    rows.push({
      glyphKey,
      letterGlyph: letter.glyph,
      locked: input.bboxesByKey[glyphKey]?.locked === true,
      hasLaufform: input.laufformKeys.has(glyphKey),
      occurrences: input.occurrencesKnown ? (input.instancesByKey.get(glyphKey)?.length ?? 0) : null,
      scoreKnown: input.quality !== null,
      score: quality?.score ?? null,
      quality,
      korbOpen: input.korbByGlyph === null ? null : (input.korbByGlyph.get(glyphKey) ?? 0),
    });
  }
  return rows;
}

/**
 * Whether one row answers one filter. An UNKNOWN fact never answers „ohne …":
 * while the occurrence layer is still loading, „ohne Vorkommen" would otherwise
 * select the whole alphabet and read as a finding.
 */
export function matchesLetterFilter(row: LetterRow, filter: LetterFilter): boolean {
  if (filter === 'gesperrt') return row.locked;
  if (filter === 'ohne-laufform') return !row.hasLaufform;
  if (filter === 'ohne-vorkommen') return row.occurrences === 0;
  return (row.korbOpen ?? 0) > 0;
}

/** The chips ANDed — every ticked one has to hold. */
export const matchesLetterFilters = (row: LetterRow, filters: readonly LetterFilter[]): boolean =>
  filters.every((filter) => matchesLetterFilter(row, filter));

/**
 * How many rows EACH chip would select on its own — the number on the chip.
 * Deliberately not „how many would remain beside the other ticked chips": a
 * count that changes with the neighbours cannot be read as „so viele gibt es".
 *
 * `null` where the chip's own fact is not in yet. Two of the four rest on reads
 * that may still be in flight, and `matchesLetterFilter` answers false for an
 * unknown — which would put a „· 0" on the chip while the rows below it say
 * „Vorkommen werden geladen …". A missing number is the honest half of the same
 * rule that keeps the rows from printing one.
 */
export function letterFilterCounts(rows: LetterRow[]): Record<LetterFilter, number | null> {
  const unknown: Record<LetterFilter, boolean> = {
    gesperrt: false,
    'ohne-laufform': false,
    'ohne-vorkommen': rows.some((row) => row.occurrences === null),
    'mit-korb': rows.some((row) => row.korbOpen === null),
  };
  const counts = {} as Record<LetterFilter, number | null>;
  for (const filter of LETTER_FILTERS) {
    counts[filter] = unknown[filter] ? null : rows.filter((row) => matchesLetterFilter(row, filter)).length;
  }
  return counts;
}

/**
 * Alphabet = the order the rows were built in; „Schlechteste zuerst" = ascending
 * score with the UNSCORED letters at the end — unknown is not bad (the rule
 * `GlyphComparison` carried since the sort existed, pinned here for the first
 * time). Ties keep the alphabet, so the list does not reshuffle under equal
 * scores.
 */
export function sortLetterRows(rows: LetterRow[], sort: LetterSort): LetterRow[] {
  if (sort === 'alphabet') return rows;
  return rows
    .map((row, index) => ({ row, index }))
    .sort((a, b) => (a.row.score ?? Infinity) - (b.row.score ?? Infinity) || a.index - b.index)
    .map((entry) => entry.row);
}

/** Is there anything to rank by? Without a single stored score, worst-first
 * would silently be the alphabet again — the toolbar says so instead. */
export const lettersRankable = (rows: LetterRow[]): boolean => rows.some((row) => row.score !== null);
