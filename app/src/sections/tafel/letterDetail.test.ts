import { describe, expect, it } from 'vitest';

import { LETTERS } from '@/domain/glyphs';
import type { GlyphRenderData } from '@/lib/api';
import { WORD_BANK, type WordEntry } from '@/sections/quiz/wordBank';
import { EXAMPLE_WORDS } from './exampleWords';
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
    expect(lookalikeKeys('g')).toEqual(['p']); // the descender pair, documented 2026-09-04
    expect(lookalikeKeys('p')).toEqual(['g']);
    expect(lookalikeKeys('q')).toEqual([]);
    expect(lookalikeKeys('0')).toEqual([]);
  });

  it('picks the shortest modern bank word that shows the letter as it is written', () => {
    // An s before another letter is the long ſ — but not before a t, which
    // folds into the ſt ligature.
    expect(exampleWord('longs', WORD_BANK)?.word).toMatch(/s(?!t)\p{L}/u);
    expect(exampleWord('s', WORD_BANK)?.word).toMatch(/s$/); // a final s → round s
    // Capitals: whichever capital the bank has a word for, the word starts with it.
    const capitals = ['A', 'B', 'D', 'H', 'K', 'M', 'S', 'W'].map((c) => [c, exampleWord(c, WORD_BANK)] as const);
    for (const [c, w] of capitals) {
      expect(w, `${c} has no example word`).not.toBeNull();
      expect(w?.word.startsWith(c), `${c}: ${w?.word}`).toBe(true);
    }
    expect(exampleWord('n', WORD_BANK)?.word).toContain('n');
    expect(exampleWord('n', WORD_BANK)?.historic).toBe(false);
    // Digits and punctuation are the only glyphs no word can show.
    expect(exampleWord('period', WORD_BANK)).toBeNull();
  });

  it('falls back to a historic bank word, then to the checked constant', () => {
    // Rung 2, on a bank built for it: with no modern word showing the letter,
    // the historic one answers and the link is told to say so.
    const onlyHistoric: WordEntry[] = [
      { word: 'Magd', distractors: ['Mahd'], era: 'historic' },
      { word: 'neu', distractors: ['nie'], era: 'modern' },
    ];
    expect(exampleWord('M', onlyHistoric)).toEqual({ word: 'Magd', historic: true });
    // Rung 1 keeps precedence over rung 2 for a letter both layers show.
    expect(exampleWord('n', onlyHistoric)).toEqual({ word: 'neu', historic: false });
    // Rung 3, on the real bank: German writes a lowercase q only inside the qu
    // unit and a lowercase c only inside ch/ck, so no bank word can ever show
    // them alone — the constant answers, as an ordinary modern word.
    expect(exampleWord('q', WORD_BANK)).toEqual({ word: EXAMPLE_WORDS.q, historic: false });
    expect(exampleWord('c', WORD_BANK)).toEqual({ word: EXAMPLE_WORDS.c, historic: false });
    // Those two are the only ones left: every other spelled glyph is answered
    // by the bank itself, so the map never has to grow back.
    expect(Object.keys(EXAMPLE_WORDS).sort()).toEqual(['c', 'q']);
  });

  it('gives every letter, capital and ligature an example word — from the bank', () => {
    // Website audit 2026-09-02 (finding 29): 35 of these had no example word
    // at all and 6 more only a historic one, so 41 of 66 letter detail pages
    // ended without an everyday bridge into the Federprobe. Digits and
    // punctuation are out of scope — no word shows them.
    const spelled = LETTERS.filter((l) => l.group === 'lower' || l.group === 'upper' || l.group === 'comb');
    const without = spelled.filter((l) => !exampleWord(l.base, WORD_BANK)).map((l) => l.base);
    expect(without).toEqual([]);
    // And the source is the curated bank, not the map beside it: a word that
    // stands in the bank is shared with the quiz and carries its era tag, so
    // the ladder must only fall through for c and q. Guards the map from
    // quietly filling up again the next time a letter goes uncovered.
    const fromMap = spelled.filter((l) => exampleWord(l.base, WORD_BANK)?.word === EXAMPLE_WORDS[l.base]);
    expect(fromMap.map((l) => l.base)).toEqual(['c', 'q']);
    // Every one of them an everyday word, too — the historic layer is the
    // second rung and today nothing needs it.
    const historic = spelled.filter((l) => exampleWord(l.base, WORD_BANK)?.historic);
    expect(historic.map((l) => l.base)).toEqual([]);
  });

  it('keeps the fallback words free of clusters that hide their own letter', () => {
    // A lowercase ch/ck/tz/qu/st pair is written as ONE ligature glyph
    // (domain/shaping.ts), so such a word would not show the letter it was
    // picked for. The ligature entries are the exception: their cluster IS
    // their letter — and q, which German writes only inside qu.
    const ownCluster: Record<string, string> = { longst: 'st', q: 'qu', c: 'ch' };
    for (const [key, word] of Object.entries(EXAMPLE_WORDS)) {
      const clusters = word.match(/ch|ck|tz|qu|st/g) ?? [];
      for (const c of clusters) {
        expect(c, `${key}: ${word}`).toBe(ownCluster[key] ?? key);
      }
      // A capital opens its word, a lowercase letter sits inside it.
      const letter = LETTERS.find((l) => l.base === key);
      if (letter?.group === 'upper') expect(word.startsWith(letter.glyph), `${key}: ${word}`).toBe(true);
    }
  });
});
