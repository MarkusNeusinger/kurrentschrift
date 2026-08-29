import { describe, expect, it } from 'vitest';

import { knownGlyph } from '@/domain/glyphs';
import { de } from '@/locales';
import { confusablesOf, explainMiss } from '@/sections/quiz/lesefallen';
import type { LetterQuestion } from '@/sections/quiz/useQuizEngine';

const question = (key: string): LetterQuestion => {
  const kg = knownGlyph(key);
  if (!kg) throw new Error(`unknown glyph key ${key}`);
  return { kind: 'letter', key, kg };
};

describe('explainMiss', () => {
  it('names the Querstrich for the ſ/f trap, in both directions', () => {
    expect(explainMiss(question('longs'), 'f')).toBe(de.quiz.play.rules.longsAsF);
    expect(explainMiss(question('f'), 's')).toBe(de.quiz.play.rules.fAsLongs);
  });

  it('describes the form on the card, so n→u and u→n read differently', () => {
    expect(explainMiss(question('n'), 'u')).toBe(de.quiz.play.rules.nAsU);
    expect(explainMiss(question('u'), 'n')).toBe(de.quiz.play.rules.uAsN);
    expect(explainMiss(question('n'), 'u')).not.toBe(explainMiss(question('u'), 'n'));
  });

  it('keeps the two s-allographs apart: the round s gets its position rule against any guess', () => {
    expect(explainMiss(question('s'), 'r')).toBe(de.quiz.play.rules.roundS);
    expect(explainMiss(question('s'), 'e')).toBe(de.quiz.play.rules.roundS);
    // The long ſ has a sentence only against the f — its documented trap.
    expect(explainMiss(question('longs'), 'r')).toBeNull();
  });

  it('explains the ß as a ligature against any guess', () => {
    expect(explainMiss(question('sz'), 's')).toBe(de.quiz.play.rules.szAsS);
    expect(explainMiss(question('sz'), 'b')).toBe(de.quiz.play.rules.szAsS);
  });

  it('points at the umlaut marks in both directions', () => {
    expect(explainMiss(question('ae'), 'a')).toContain('ein ä');
    expect(explainMiss(question('u'), 'ü')).toContain('einfache u');
    // A different vowel is not an umlaut confusion.
    expect(explainMiss(question('ae'), 'o')).toBeNull();
  });

  it('sends the capital clusters to the comparison, symmetrically', () => {
    const lk = explainMiss(question('L'), 'k');
    expect(lk).toContain('L, K und R');
    expect(explainMiss(question('K'), 'r')).toBe(lk);
    expect(explainMiss(question('B'), 'v')).toContain('B und V');
    // Lowercase pair rules never leak into the capitals (N/M is a cluster, n/m a feature).
    expect(explainMiss(question('N'), 'm')).toContain('N und M');
    expect(explainMiss(question('N'), 'e')).toBeNull();
  });

  it('returns null where the catalogue has no documented feature — never invents one', () => {
    expect(explainMiss(question('a'), 'd')).toBeNull();
    expect(explainMiss(question('g'), 'q')).toBeNull();
    expect(explainMiss(question('0'), '8')).toBeNull();
  });

  it('has nothing to say about a correct pick', () => {
    expect(explainMiss(question('longs'), 's')).toBeNull();
    expect(explainMiss(question('n'), 'n')).toBeNull();
  });
});

describe('confusablesOf', () => {
  it('lists exactly the letters a sentence exists for, so the trap is on offer', () => {
    expect(new Set(confusablesOf(question('n')))).toEqual(new Set(['u', 'e', 'm']));
    expect(confusablesOf(question('longs'))).toEqual(['f']);
    expect(confusablesOf(question('ae'))).toEqual(['a']);
    expect(confusablesOf(question('a'))).toEqual(['ä']);
    expect(new Set(confusablesOf(question('L')))).toEqual(new Set(['k', 'r']));
  });

  it('never lists the shown letter itself, and nothing for undocumented forms', () => {
    for (const key of ['n', 'L', 'ae', 'sz']) expect(confusablesOf(question(key))).not.toContain(question(key).kg.answer);
    expect(confusablesOf(question('g'))).toEqual([]);
    expect(confusablesOf(question('0'))).toEqual([]);
    // Every listed confusable round-trips to a sentence.
    for (const key of ['n', 'u', 'longs', 'f', 'ae', 'L', 'B']) {
      for (const guess of confusablesOf(question(key))) expect(explainMiss(question(key), guess)).not.toBeNull();
    }
  });
});
