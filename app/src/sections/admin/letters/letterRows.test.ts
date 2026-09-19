import { describe, expect, it } from 'vitest';

import type { BboxOut, InstanceOut, QualityData } from '@/lib/api';

import {
  LETTER_FILTERS,
  buildLetterRows,
  letterFilterCounts,
  lettersRankable,
  matchesLetterFilter,
  matchesLetterFilters,
  sortLetterRows,
  type LetterRow,
  type LetterRowInput,
} from './letterRows';

const bbox = (glyphKey: string, locked: boolean): BboxOut => ({
  glyph_key: glyphKey,
  y0: 0,
  y1: 1,
  x0: 0,
  x1: 1,
  mask_strokes: [],
  ink_strokes: [],
  patches: [],
  baseline_y: 1,
  midband_y: 0,
  n_anchors: 3,
  guides: {} as BboxOut['guides'],
  locked,
  fill_holes_max_area: 0,
});

const instance = (glyphKey: string): InstanceOut =>
  ({ glyph_key: glyphKey, measurements: {} }) as unknown as InstanceOut;

const quality = (score: number): QualityData => ({ score }) as QualityData;

// Everything answered, nothing set — each test turns on exactly what it needs.
function input(over: Partial<LetterRowInput> = {}): LetterRowInput {
  return {
    authoredKeys: ['a', 'b', 'c'],
    bboxesByKey: {},
    laufformKeys: new Set(),
    instancesByKey: new Map(),
    quality: new Map(),
    korbByGlyph: new Map(),
    occurrencesKnown: true,
    ...over,
  };
}

const keysOf = (rows: LetterRow[]) => rows.map((row) => row.glyphKey);

describe('building the rows', () => {
  it('keeps the authored letters in registry order and drops the rest', () => {
    // `b` comes first in the input, the alphabet still wins — the list order is
    // the registry's, not the map's.
    expect(keysOf(buildLetterRows(input({ authoredKeys: ['c', 'a'] })))).toEqual(['a', 'c']);
    expect(keysOf(buildLetterRows(input({ authoredKeys: ['nonsense'] })))).toEqual([]);
  });

  it('reads „ohne Laufform" from the stored template rows, not from a render flag', () => {
    const rows = buildLetterRows(input({ laufformKeys: new Set(['b']) }));
    expect(rows.map((row) => row.hasLaufform)).toEqual([false, true, false]);
  });

  it('leaves an unanswered read as null instead of as a zero', () => {
    const rows = buildLetterRows(input({ occurrencesKnown: false, quality: null, korbByGlyph: null }));
    expect(rows[0].occurrences).toBeNull();
    expect(rows[0].score).toBeNull();
    expect(rows[0].korbOpen).toBeNull();
  });

  it('counts an answered read, including the honest zero', () => {
    const rows = buildLetterRows(
      input({
        instancesByKey: new Map([['a', [instance('a'), instance('a')]]]),
        quality: new Map([['a', quality(72)]]),
        korbByGlyph: new Map([['a', 3]]),
      }),
    );
    expect(rows[0]).toMatchObject({ occurrences: 2, score: 72, korbOpen: 3 });
    expect(rows[1]).toMatchObject({ occurrences: 0, score: null, korbOpen: 0 });
  });
});

describe('the four filters', () => {
  const rows = buildLetterRows(
    input({
      authoredKeys: ['a', 'b', 'c', 'd'],
      bboxesByKey: { a: bbox('a', true), b: bbox('b', false) },
      laufformKeys: new Set(['a', 'b']),
      instancesByKey: new Map([
        ['a', [instance('a')]],
        ['c', [instance('c')]],
      ]),
      korbByGlyph: new Map([['a', 1]]),
    }),
  );

  it('selects exactly its own rows', () => {
    expect(keysOf(rows.filter((row) => matchesLetterFilter(row, 'gesperrt')))).toEqual(['a']);
    expect(keysOf(rows.filter((row) => matchesLetterFilter(row, 'ohne-laufform')))).toEqual(['c', 'd']);
    expect(keysOf(rows.filter((row) => matchesLetterFilter(row, 'ohne-vorkommen')))).toEqual(['b', 'd']);
    expect(keysOf(rows.filter((row) => matchesLetterFilter(row, 'mit-korb')))).toEqual(['a']);
  });

  it('ANDs the ticked chips', () => {
    expect(keysOf(rows.filter((row) => matchesLetterFilters(row, ['ohne-laufform', 'ohne-vorkommen'])))).toEqual(['d']);
    expect(keysOf(rows.filter((row) => matchesLetterFilters(row, ['gesperrt', 'ohne-laufform'])))).toEqual([]);
    // No chip ticked is the whole list, not an empty one.
    expect(keysOf(rows.filter((row) => matchesLetterFilters(row, [])))).toEqual(['a', 'b', 'c', 'd']);
  });

  it('counts each chip on its own, independent of the others', () => {
    expect(letterFilterCounts(rows)).toEqual({
      gesperrt: 1,
      'ohne-laufform': 2,
      'ohne-vorkommen': 2,
      'mit-korb': 1,
    });
    // Every declared chip has a count — a chip with no number would look broken.
    expect(Object.keys(letterFilterCounts(rows)).sort()).toEqual([...LETTER_FILTERS].sort());
  });

  it('never selects „ohne Vorkommen" on a read that has not answered', () => {
    // The occurrence layer is public but may be in flight or failed; „ohne
    // Vorkommen" would otherwise select the whole alphabet and read as a
    // finding about the plates.
    const unknown = buildLetterRows(input({ occurrencesKnown: false }));
    expect(unknown.filter((row) => matchesLetterFilter(row, 'ohne-vorkommen'))).toEqual([]);
  });

  it('never selects „mit Korb-Auftrag" while the basket read is unknown', () => {
    const unknown = buildLetterRows(input({ korbByGlyph: null }));
    expect(unknown.filter((row) => matchesLetterFilter(row, 'mit-korb'))).toEqual([]);
  });
});

describe('sorting', () => {
  const rows = buildLetterRows(
    input({
      authoredKeys: ['a', 'b', 'c'],
      quality: new Map([
        ['a', quality(90)],
        ['c', quality(40)],
      ]),
    }),
  );

  it('leaves the alphabet alone', () => {
    expect(keysOf(sortLetterRows(rows, 'alphabet'))).toEqual(['a', 'b', 'c']);
  });

  it('puts the worst first and the UNSCORED letter last — unknown is not bad', () => {
    expect(keysOf(sortLetterRows(rows, 'schlechteste'))).toEqual(['c', 'a', 'b']);
  });

  it('breaks a tie by the alphabet, so the list does not reshuffle', () => {
    const tied = buildLetterRows(
      input({
        quality: new Map([
          ['a', quality(50)],
          ['b', quality(50)],
          ['c', quality(50)],
        ]),
      }),
    );
    expect(keysOf(sortLetterRows(tied, 'schlechteste'))).toEqual(['a', 'b', 'c']);
  });

  it('knows when there is nothing to rank by', () => {
    expect(lettersRankable(rows)).toBe(true);
    expect(lettersRankable(buildLetterRows(input({ quality: null })))).toBe(false);
    expect(lettersRankable(buildLetterRows(input({ quality: new Map() })))).toBe(false);
  });
});
