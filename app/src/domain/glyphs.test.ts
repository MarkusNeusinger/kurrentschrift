// Unit tests for the pure key/quiz-unit helpers in domain/glyphs.ts — THE
// single source of truth for how the quiz and the admin sidebar resolve a
// letter's glyph_key (base keys, s/ſ allographs, legacy aliases).

import { describe, expect, it } from 'vitest';

import { glyphKeyFor, LETTER_BY_KEY, quizKeysFromLocked } from '@/domain/glyphs';

describe('glyphKeyFor', () => {
  it('returns the bare base key with no position suffix', () => {
    expect(glyphKeyFor(LETTER_BY_KEY['n'])).toBe('n');
    expect(glyphKeyFor(LETTER_BY_KEY['A'])).toBe('A');
    expect(glyphKeyFor(LETTER_BY_KEY['ae'])).toBe('ae');
    expect(glyphKeyFor(LETTER_BY_KEY['comma'])).toBe('comma');
  });

  it('keeps the s/ſ allographs as separate base keys', () => {
    // Round s keys as `s`, the long-s ſ as `longs` — never one letter.
    expect(glyphKeyFor(LETTER_BY_KEY['s'])).toBe('s');
    expect(LETTER_BY_KEY['s'].glyph).toBe('s');
    expect(glyphKeyFor(LETTER_BY_KEY['longs'])).toBe('longs');
    expect(LETTER_BY_KEY['longs'].glyph).toBe('ſ');
  });
});

describe('quizKeysFromLocked', () => {
  it('passes every locked key through as its own quiz unit', () => {
    const bboxes = {
      n: { locked: true },
      e: { locked: true },
      a: { locked: false },
    };
    expect(quizKeysFromLocked(bboxes).sort()).toEqual(['e', 'n']);
  });

  it('excludes punctuation but keeps digits', () => {
    const bboxes = {
      comma: { locked: true },
      '7': { locked: true },
    };
    const keys = quizKeysFromLocked(bboxes);
    expect(keys).not.toContain('comma');
    expect(keys).toContain('7');
  });

  it('keeps legacy uc-/lc- alias keys as singletons', () => {
    const bboxes = { 'uc-a': { locked: true }, 'lc-a': { locked: true } };
    expect(quizKeysFromLocked(bboxes).sort()).toEqual(['lc-a', 'uc-a']);
  });

  it('never merges the two s allographs into one unit', () => {
    const bboxes = {
      longs: { locked: true }, // long s ſ
      s: { locked: true }, // round s
    };
    const keys = quizKeysFromLocked(bboxes);
    expect(keys).toHaveLength(2);
    expect(keys.sort()).toEqual(['longs', 's']);
  });
});
