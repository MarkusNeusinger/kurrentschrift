// Unit tests for the pure lock/split/quiz-unit helpers in domain/glyphs.ts —
// THE single source of truth for how the quiz and the admin sidebar group a
// letter's three position rows (lock-as-one, split, s/ſ allographs).

import { describe, expect, it } from 'vitest';

import { glyphKeyFor, isLetterSplit, LETTER_BY_KEY, quizKeysFromLocked, siblingKeys } from '@/domain/glyphs';

describe('siblingKeys', () => {
  it('fans a plain letter out across the three positions', () => {
    expect(siblingKeys('n-medial')).toEqual(['n-initial', 'n-medial', 'n-final']);
  });

  it('keeps the s/ſ allograph key overrides separate', () => {
    // Round s: historical final key `s-final`, medial override `s-round-medial`.
    expect(siblingKeys('s-final')).toContain('s-round-medial');
    expect(siblingKeys('s-final')).not.toContain('s-medial');
    // Long s owns `s-medial`; its siblings never include the round forms.
    expect(siblingKeys('s-medial')).not.toContain('s-final');
  });

  it('returns unknown keys as their own singleton group', () => {
    expect(siblingKeys('lc-legacy-alias')).toEqual(['lc-legacy-alias']);
  });
});

describe('isLetterSplit', () => {
  it('reads split from ANY sibling row (.some, not .every)', () => {
    const bboxes = { 'n-initial': { split: true }, 'n-medial': { split: false } };
    expect(isLetterSplit('n-medial', bboxes)).toBe(true);
    expect(isLetterSplit('n-final', bboxes)).toBe(true); // sibling added later self-heals
  });

  it('is false when no sibling carries the flag', () => {
    expect(isLetterSplit('n-medial', { 'n-medial': { locked: true } })).toBe(false);
  });
});

describe('quizKeysFromLocked', () => {
  const hasNoCanon = () => false;

  it('collapses a unified locked letter into one representative entry', () => {
    const bboxes = {
      'n-initial': { locked: true },
      'n-medial': { locked: true },
      'n-final': { locked: true },
    };
    const keys = quizKeysFromLocked(bboxes, hasNoCanon);
    expect(keys).toEqual(['n-medial']); // medial preferred without a canonical
  });

  it('prefers a position that has a canonical', () => {
    const bboxes = { 'n-initial': { locked: true }, 'n-medial': { locked: true } };
    const keys = quizKeysFromLocked(bboxes, (k) => k === 'n-initial');
    expect(keys).toEqual(['n-initial']);
  });

  it('keeps each locked position of a split letter as its own quiz unit', () => {
    const bboxes = {
      'e-initial': { locked: true, split: true },
      'e-final': { locked: true, split: true },
    };
    const keys = quizKeysFromLocked(bboxes, hasNoCanon);
    expect(keys.sort()).toEqual(['e-final', 'e-initial']);
  });

  it('excludes punctuation but keeps digits', () => {
    const comma = glyphKeyFor(LETTER_BY_KEY['comma-medial'], 'medial');
    const bboxes = {
      [comma]: { locked: true },
      '7-initial': { locked: true },
    };
    const keys = quizKeysFromLocked(bboxes, hasNoCanon);
    expect(keys.some((k) => k.startsWith('comma'))).toBe(false);
    expect(keys.some((k) => k.startsWith('7'))).toBe(true);
  });

  it('never merges the two s allographs into one unit', () => {
    const bboxes = {
      's-medial': { locked: true }, // long s ſ
      's-final': { locked: true }, // round s
    };
    const keys = quizKeysFromLocked(bboxes, hasNoCanon);
    expect(keys).toHaveLength(2);
  });
});
