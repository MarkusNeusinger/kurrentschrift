import { describe, expect, it } from 'vitest';

import type { GlyphRenderData } from '@/lib/api';
import { WORD_BANK } from '@/sections/quiz/wordBank';
import { exampleWord, lookalikeKeys, strokeCount, strokeStarts } from './letterDetail';

const twoStrokes: GlyphRenderData = {
  anchors_template: [
    [0, 0],
    [1, 1],
  ],
  half_widths_template: [0.05],
  outline_paths: [[[[0, 0], [0.5, 0], [0.5, 1], [0, 1]]], [[[0.6, 0], [1, 0], [1, 1], [0.6, 1]]]],
  centerlines_template: [
    [
      [0.25, 0],
      [0.25, 1],
    ],
    [
      [0.8, 1],
      [0.8, 0],
    ],
  ],
  template_guides: { baseline: 0, midband: 1, ascender: 2, descender: -1 },
};

describe('letterDetail', () => {
  it('numbers the strokes at their first centerline point, in writing order', () => {
    expect(strokeStarts(twoStrokes)).toEqual([
      [0.25, 0],
      [0.8, 1],
    ]);
    expect(strokeCount(twoStrokes)).toBe(2);
  });

  it('maps the documented look-alikes to glyph keys, allographs included', () => {
    expect(lookalikeKeys('n')).toEqual(['u', 'e', 'm']);
    expect(lookalikeKeys('longs')).toEqual(['f', 's']);
    expect(lookalikeKeys('s')).toEqual(['longs']);
    expect(lookalikeKeys('a')).toEqual(['ae']);
    expect(lookalikeKeys('ae')).toEqual(['a']);
    expect(lookalikeKeys('L')).toEqual(['K', 'R']);
    expect(lookalikeKeys('g')).toEqual([]);
    expect(lookalikeKeys('0')).toEqual([]);
  });

  it('picks the shortest modern bank word that shows the letter as it is written', () => {
    expect(exampleWord('longs', WORD_BANK)).toMatch(/s\p{L}/u); // an s inside the word → long ſ
    expect(exampleWord('s', WORD_BANK)).toMatch(/s$/); // a final s → round s
    // Capitals: whichever capital the bank has a word for, the word starts with it.
    const capitals = ['A', 'B', 'D', 'H', 'K', 'M', 'S', 'W'].map((c) => [c, exampleWord(c, WORD_BANK)] as const).filter(([, w]) => w);
    expect(capitals.length).toBeGreaterThan(0);
    for (const [c, w] of capitals) expect(w!.startsWith(c), `${c}: ${w}`).toBe(true);
    expect(exampleWord('n', WORD_BANK)).toContain('n');
    expect(exampleWord('period', WORD_BANK)).toBeNull();
  });
});
