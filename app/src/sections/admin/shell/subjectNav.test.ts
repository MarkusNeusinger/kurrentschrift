// The two rules ‹ › rests on: WHICH order it walks, and where the ends are.

import { describe, expect, it } from 'vitest';

import { neighboursInOrder, orderCaption, sameSubjectKeys, stepOrder, type SubjectOrder } from './subjectNav';

const worstFirst: SubjectOrder = { kind: 'letter', keys: ['n', 'a', 'e'], caption: 'Reihenfolge: Schlechteste zuerst' };
const registry = { keys: ['a', 'b', 'c', 'd', 'e', 'n'], caption: 'Reihenfolge: Registerfolge' };

describe('stepOrder', () => {
  it('follows the overview the reader came from', () => {
    // The point of P1-Q12 (a): after „Schlechteste zuerst", › is the
    // second-worst letter and not „b".
    expect(stepOrder(worstFirst, 'letter', 'n', registry)).toBe(worstFirst);
    expect(neighboursInOrder(stepOrder(worstFirst, 'letter', 'n', registry).keys, 'n').next).toBe('a');
  });

  it('falls back to the register when nothing was published', () => {
    // A deep link straight into a detail — from the Korb, from a task, from a
    // reload.
    expect(stepOrder(null, 'letter', 'a', registry)).toBe(registry);
  });

  it('falls back when the published order is about another subject', () => {
    // The reader walked from the Buchstaben list over into a join: the letter
    // order is not a join order, and must not be read as one.
    expect(stepOrder(worstFirst, 'join', 'a→b', registry)).toBe(registry);
  });

  it('falls back when the current subject is not in the published order', () => {
    // Reached through the picker or a Korb link while the overview is filtered
    // down to something else: a stepper that went dead there would be worse
    // than one that quietly walks the register.
    expect(stepOrder(worstFirst, 'letter', 'b', registry)).toBe(registry);
  });
});

describe('neighboursInOrder', () => {
  it('names both neighbours in the middle', () => {
    expect(neighboursInOrder(['a', 'b', 'c'], 'b')).toEqual({ prev: 'a', next: 'c' });
  });

  it('does not wrap at either end — the ‹ › buttons go disabled there', () => {
    expect(neighboursInOrder(['a', 'b', 'c'], 'a')).toEqual({ prev: null, next: 'b' });
    expect(neighboursInOrder(['a', 'b', 'c'], 'c')).toEqual({ prev: 'b', next: null });
  });

  it('answers nothing for a subject the order does not hold', () => {
    expect(neighboursInOrder(['a', 'b'], 'z')).toEqual({ prev: null, next: null });
    expect(neighboursInOrder([], 'a')).toEqual({ prev: null, next: null });
  });

  it('answers nothing for an order of one', () => {
    expect(neighboursInOrder(['a'], 'a')).toEqual({ prev: null, next: null });
  });
});

describe('orderCaption', () => {
  it('names the sort, and says when a filter narrows it', () => {
    expect(orderCaption('Schlechteste zuerst', false)).toBe('Reihenfolge: Schlechteste zuerst');
    expect(orderCaption('Schlechteste zuerst', true)).toBe('Reihenfolge: Schlechteste zuerst · gefiltert');
  });
});

describe('sameSubjectKeys', () => {
  it('compares by value, so a rebuilt array does not look like a new order', () => {
    expect(sameSubjectKeys(['a', 'b'], ['a', 'b'])).toBe(true);
    expect(sameSubjectKeys(['a', 'b'], ['b', 'a'])).toBe(false);
    expect(sameSubjectKeys(['a'], ['a', 'b'])).toBe(false);
  });
});
