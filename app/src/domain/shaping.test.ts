// Twin-sync guard: the TS shaper (this module) MUST agree with the Python
// shaper (core/shaping.py) on the `text → glyph_keys` mapping (CLAUDE.md
// mandate). Both sides assert the SAME shared fixture
// (tests/fixtures/shaping_cases.json), whose expected keys are generated from
// the Python source of truth — so deliberately mutating one shaping without the
// other fails CI here (TS) or in tests/test_tri_script.py (Python).

import { readFileSync } from 'node:fs';

import { describe, expect, it } from 'vitest';

import { glyphKeysOf, shapeText } from '@/domain/shaping';

interface ShapingCase {
  text: string;
  keys: (string | null)[];
}

// Read via node fs rather than an import so the fixture can live at the repo
// root (shared with the Python test) without tripping vite's fs allow-list.
const CASES: ShapingCase[] = JSON.parse(
  readFileSync(new URL('../../../tests/fixtures/shaping_cases.json', import.meta.url), 'utf-8'),
);

describe('shapeText twin parity', () => {
  it('has a non-empty shared fixture', () => {
    expect(CASES.length).toBeGreaterThan(0);
  });

  it.each(CASES)('shapes $text like core/shaping.py', ({ text, keys }) => {
    expect(shapeText(text).map((s) => s.key)).toEqual(keys);
  });
});

describe('glyphKeysOf', () => {
  it('returns the distinct, in-order keys the composer fetches', () => {
    // "lesen" repeats e-medial → deduped; the null space slot is dropped.
    expect(glyphKeysOf(shapeText('lesen das'))).toEqual([
      'l-initial',
      'e-medial',
      's-medial',
      'n-final',
      'd-initial',
      'a-medial',
      's-final',
    ]);
  });
});
