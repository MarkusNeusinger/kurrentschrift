import { describe, expect, it } from 'vitest';

import { LETTER_BY_KEY } from '@/domain/glyphs';
import type { GlyphPairOut } from '@/lib/api';

import {
  PAIR_FILTERS,
  authoredLetters,
  buildPairRows,
  matchesPairFilter,
  matchesPairFilters,
  pairFilterCounts,
  pairsRankable,
  sortPairRows,
  type PairRow,
} from './pairRows';

const letter = (key: string) => {
  const found = LETTER_BY_KEY[key];
  if (!found) throw new Error(`unknown test letter ${key}`);
  return found;
};

const override = (leftKey: string, rightKey: string, approved: boolean): [string, GlyphPairOut] => [
  `${leftKey}|${rightKey}`,
  { left_key: leftKey, right_key: rightKey, variant: 0, approved } as GlyphPairOut,
];

const input = (over: Partial<Parameters<typeof buildPairRows>[0]> = {}) => ({
  anchor: letter('a'),
  lower: [letter('b'), letter('c')],
  upper: [letter('B')],
  pairsByKey: new Map<string, readonly unknown[]>([['a→b', [{}, {}, {}]]]),
  overrideRows: new Map<string, GlyphPairOut>([override('a', 'c', true)]),
  korbByPair: new Map<string, number>([['a→b', 2]]),
  ...over,
});

const row = (rows: PairRow[], text: string): PairRow => {
  const found = rows.find((r) => r.text === text);
  expect(found, text).toBeDefined();
  return found as PairRow;
};

describe('building the cells of one anchor letter', () => {
  it('pairs the anchor with every authored lowercase letter, in both directions', () => {
    const { asFirst, asSecond } = buildPairRows(input());
    expect(asFirst.map((r) => r.text)).toEqual(['ab', 'ac']);
    // As the SECOND letter the anchor takes capitals too — a capital only ever
    // stands on the left (architektur.md §4) — and never itself.
    expect(asSecond.map((r) => r.text)).toEqual(['ba', 'ca', 'Ba']);
  });

  it('gives a capital anchor only the „als erster Buchstabe" row', () => {
    const { asFirst, asSecond } = buildPairRows(input({ anchor: letter('B') }));
    expect(asFirst.map((r) => r.text)).toEqual(['Bb', 'Bc']);
    expect(asSecond).toEqual([]);
  });

  it('counts the plates, the stored override and the open basket items per cell', () => {
    const rows = buildPairRows(input()).asFirst;
    expect(row(rows, 'ab')).toMatchObject({ leftKey: 'a', rightKey: 'b', plate: 3, override: 'none', korbOpen: 2 });
    // The other cell has the override and nothing else — three independent
    // facts, three independent counters.
    expect(row(rows, 'ac')).toMatchObject({ plate: 0, override: 'approved', korbOpen: 0 });
  });

  it('keeps a draft apart from a released override', () => {
    const rows = buildPairRows(
      input({ overrideRows: new Map([override('a', 'b', false)]) }),
    ).asFirst;
    expect(row(rows, 'ab').override).toBe('draft');
  });

  it('gives a ligature-folding combination no counters at all', () => {
    // „ch" is ONE glyph, so there is no join to measure, to override or to
    // file a task against — and no keys to open a detail with.
    const rows = buildPairRows(input({ anchor: letter('c'), lower: [letter('h')] })).asFirst;
    expect(row(rows, 'ch')).toMatchObject({
      leftKey: null,
      rightKey: null,
      plate: null,
      override: null,
      korbOpen: null,
    });
  });

  it('never turns an unanswered read into a zero', () => {
    const rows = buildPairRows(input({ pairsByKey: null, overrideRows: null, korbByPair: null })).asFirst;
    expect(row(rows, 'ab')).toMatchObject({ plate: null, override: null, korbOpen: null });
  });
});

describe('the filter chips', () => {
  const rows = buildPairRows(input()).asFirst;

  it('selects by each chip on its own', () => {
    expect(rows.filter((r) => matchesPairFilter(r, 'mit-uebersteuerung')).map((r) => r.text)).toEqual(['ac']);
    expect(rows.filter((r) => matchesPairFilter(r, 'mit-korb')).map((r) => r.text)).toEqual(['ab']);
    expect(rows.filter((r) => matchesPairFilter(r, 'ohne-vorkommen')).map((r) => r.text)).toEqual(['ac']);
  });

  it('ANDs the ticked ones', () => {
    expect(rows.filter((r) => matchesPairFilters(r, ['mit-uebersteuerung', 'ohne-vorkommen'])).map((r) => r.text)).toEqual(
      ['ac'],
    );
    // No cell has both an override and a basket item here.
    expect(rows.filter((r) => matchesPairFilters(r, ['mit-uebersteuerung', 'mit-korb']))).toEqual([]);
    // Nothing ticked selects everything.
    expect(rows.filter((r) => matchesPairFilters(r, []))).toHaveLength(rows.length);
  });

  it('never selects a ligature cell', () => {
    const ligature = buildPairRows(input({ anchor: letter('c'), lower: [letter('h')] })).asFirst;
    for (const filter of PAIR_FILTERS) expect(matchesPairFilter(ligature[0], filter), filter).toBe(false);
  });

  it('counts each chip on its own, and carries no number for an unanswered read', () => {
    expect(pairFilterCounts(rows)).toEqual({
      'mit-uebersteuerung': 1,
      'mit-korb': 1,
      'ohne-vorkommen': 1,
    });
    // A missing number is the honest half of the rule that keeps the cells
    // from printing one: „· 0" beside rows that say nothing would be a claim.
    const pending = buildPairRows(input({ overrideRows: null })).asFirst;
    expect(pairFilterCounts(pending)['mit-uebersteuerung']).toBeNull();
    expect(pairFilterCounts(pending)['mit-korb']).toBe(1);
  });

  it('does not let a ligature cell make a chip count unknown', () => {
    // Its nulls mean „there is nothing to know here", not „the read is out" —
    // a grid holding one would otherwise never show a single count.
    const withLigature = buildPairRows(input({ anchor: letter('c'), lower: [letter('h'), letter('b')] })).asFirst;
    expect(pairFilterCounts(withLigature)['mit-uebersteuerung']).toBe(0);
  });
});

describe('the order of the cells', () => {
  it('keeps the alphabet as it was built', () => {
    const rows = buildPairRows(input()).asFirst;
    expect(sortPairRows(rows, 'alphabet').map((r) => r.text)).toEqual(['ab', 'ac']);
  });

  it('puts the most-written combination first and the unmeasured ones last', () => {
    const rows = buildPairRows(
      input({
        lower: [letter('b'), letter('c'), letter('d')],
        pairsByKey: new Map<string, readonly unknown[]>([
          ['a→b', [{}]],
          ['a→d', [{}, {}]],
        ]),
      }),
    ).asFirst;
    expect(sortPairRows(rows, 'vorkommen').map((r) => r.text)).toEqual(['ad', 'ab', 'ac']);
  });

  it('reports whether there is anything to rank by', () => {
    expect(pairsRankable(buildPairRows(input()).asFirst)).toBe(true);
    expect(pairsRankable(buildPairRows(input({ pairsByKey: new Map() })).asFirst)).toBe(false);
    expect(pairsRankable(buildPairRows(input({ pairsByKey: null })).asFirst)).toBe(false);
  });
});

describe('the grid axes', () => {
  it('keeps only the authored letters, split by group and in registry order', () => {
    const { lower, upper } = authoredLetters(
      [letter('a'), letter('b'), letter('B'), letter('c')],
      (key) => key !== 'b',
    );
    expect(lower.map((l) => l.glyph)).toEqual(['a', 'c']);
    expect(upper.map((l) => l.glyph)).toEqual(['B']);
  });
});
