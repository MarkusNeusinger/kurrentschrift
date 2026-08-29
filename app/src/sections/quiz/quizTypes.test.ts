import { describe, expect, it } from 'vitest';

import { DIFFICULTIES, MODES, offersChoice, SCRIPTS } from '@/sections/quiz/quizTypes';

describe('offersChoice', () => {
  it('is a choice only with two or more available options', () => {
    expect(offersChoice([{ available: true }, { available: true }])).toBe(true);
    expect(offersChoice([{ available: true }, { available: false }, { available: false }])).toBe(false);
    expect(offersChoice([{ available: false }, { available: false }])).toBe(false);
    expect(offersChoice([])).toBe(false);
  });

  it('pins today’s first screen: the Aufgabe row only — script and difficulty are facts, not rows', () => {
    // When a second script or a messier hand lands, flip its `available` flag
    // and the row returns by itself; this test then documents the new state.
    expect(offersChoice(MODES)).toBe(true);
    expect(offersChoice(SCRIPTS)).toBe(false);
    expect(offersChoice(DIFFICULTIES)).toBe(false);
  });
});
