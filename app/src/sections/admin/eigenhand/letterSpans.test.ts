// The rule that decides what becomes ground truth: a boundary the author moved
// is his, one he did not touch stays the follower's.
//
// Both halves matter and only one of them is obvious. A drag has to stamp BOTH
// sides of the seam (one sample belongs to one letter, so the neighbour moves
// with it or the two overlap — which `check_paths` refuses). A tap that moved
// nothing has to change nothing: `herkunft: 'authored'` survives every later
// re-follow, so claiming it for an assignment nobody looked at would freeze a
// guess as truth and feed it to the Span-Zuordner's training set.

import { describe, expect, it } from 'vitest';

import type { EigenhandPfadSpan } from '@/lib/api';

import {
  authoredSpanCount,
  moveBoundary,
  nearestSample,
  seamAt,
  seamsOf,
  spansStillFit,
} from './letterSpans';

const span = (over: Partial<EigenhandPfadSpan> = {}): EigenhandPfadSpan => ({
  stroke: 0,
  slot: 0,
  first: 0,
  last: 3,
  herkunft: 'auto',
  ...over,
});

/** „le" on one stroke: samples 0..3 are the l, 4..9 the e. */
const PAIR: EigenhandPfadSpan[] = [
  span({ slot: 0, first: 0, last: 3 }),
  span({ slot: 1, first: 4, last: 9 }),
];

describe('seamsOf', () => {
  it('makes one seam per ADJACENT pair of the same stroke', () => {
    const seams = seamsOf(PAIR);
    expect(seams).toHaveLength(1);
    // The handle sits on the last sample of the left letter, and the window
    // keeps one sample for each side.
    expect(seams[0]).toMatchObject({ before: 0, after: 1, stroke: 0, sample: 3, min: 0, max: 8 });
  });

  it('makes none across a gap, and none across two strokes', () => {
    // A stretch the follower could not label is the Zuordner's business —
    // closing it by dragging would assign that ink to a neighbour silently.
    expect(seamsOf([span({ first: 0, last: 3 }), span({ slot: 1, first: 6, last: 9 })])).toEqual([]);
    // An i-dot is its own stroke; „the end of the body" and „the start of the
    // dot" are not one boundary.
    expect(seamsOf([span({ first: 0, last: 3 }), span({ stroke: 1, slot: 1, first: 0, last: 2 })])).toEqual([]);
  });

  it('reads the list in stroke order, not in the order it was stored', () => {
    const seams = seamsOf([PAIR[1], PAIR[0]]);
    expect(seams).toHaveLength(1);
    expect(seams[0]).toMatchObject({ before: 1, after: 0, sample: 3 });
  });
});

describe('moveBoundary', () => {
  const seam = seamsOf(PAIR)[0];

  it('moves both sides and stamps both as the author’s', () => {
    const moved = moveBoundary(PAIR, seam, 6);
    expect(moved[0]).toMatchObject({ last: 6, herkunft: 'authored' });
    expect(moved[1]).toMatchObject({ first: 7, herkunft: 'authored' });
    // …and nothing else: the slots keep their letters.
    expect(moved.map((s) => s.slot)).toEqual([0, 1]);
  });

  it('returns the list BY IDENTITY where the boundary did not move', () => {
    // The whole point: a pen-down on the handle without a drag must not
    // re-label the follower's own assignment as ground truth.
    expect(moveBoundary(PAIR, seam, 3)).toBe(PAIR);
    expect(authoredSpanCount(moveBoundary(PAIR, seam, 3))).toBe(0);
  });

  it('keeps one sample on each side of the seam', () => {
    expect(moveBoundary(PAIR, seam, -5)[0].last).toBe(seam.min);
    expect(moveBoundary(PAIR, seam, 99)[0].last).toBe(seam.max);
    expect(moveBoundary(PAIR, seam, 99)[1].first).toBe(seam.max + 1);
  });

  it('leaves every OTHER span untouched, object for object', () => {
    const three = [...PAIR, span({ stroke: 1, slot: 2, first: 0, last: 2 })];
    const moved = moveBoundary(three, seamsOf(three)[0], 5);
    expect(moved[2]).toBe(three[2]);
    expect(moved[2].herkunft).toBe('auto');
  });
});

describe('nearestSample and seamAt', () => {
  const stroke = [
    [0, 0],
    [1, 0],
    [2, 0],
    [3, 0],
  ];

  it('picks the closest sample inside the window', () => {
    expect(nearestSample(stroke, [2.4, 0], 0, 3)).toBe(2);
    // …and never outside it, however close the pointer comes.
    expect(nearestSample(stroke, [3.0, 0], 0, 1)).toBe(1);
  });

  it('takes the seam under the pen, and none where the pen is nowhere near', () => {
    const seams = seamsOf(PAIR);
    const line = Array.from({ length: 10 }, (_, i) => [i, 0]);
    expect(seamAt(seams, [line], [3.2, 0.1], 0.8)).toBe(0);
    expect(seamAt(seams, [line], [7, 0], 0.8)).toBeNull();
  });
});

describe('spansStillFit', () => {
  const ONE: EigenhandPfadSpan[] = [
    { stroke: 0, slot: 0, first: 0, last: 0, herkunft: 'auto' },
    { stroke: 0, slot: 1, first: 1, last: 1, herkunft: 'authored' },
  ];

  it('asks about the SHAPE, not the coordinates', () => {
    // Anpassen moves points and never their count, so the spans still index
    // the samples they were drawn on.
    expect(spansStillFit([[[0, 0], [1, 1]]], [[[0.5, 0.4], [1, 1]]], ONE)).toBe(true);
    // A redrawn stroke is a different list of samples entirely.
    expect(spansStillFit([[[0, 0], [1, 1]]], [[[0, 0], [0.5, 0.5], [1, 1]]], ONE)).toBe(false);
    expect(spansStillFit([[[0, 0], [1, 1]]], [], ONE)).toBe(false);
  });

  it('keeps the boundaries when a run is drawn BESIDE the ones they sit on', () => {
    // The Absetzer warning asks for exactly this — a missing mark stroke. It
    // shifts no index, so giving up an `authored` seam over it would destroy
    // ground truth the per-box write then deletes for good.
    const seeded = [[[0, 0], [1, 1]]];
    const grown = [[[0, 0], [1, 1]], [[2, 2], [3, 3]]];
    expect(spansStillFit(seeded, grown, ONE)).toBe(true);
    // …but a change to the stroke a span DOES sit on still gives them up.
    expect(spansStillFit(seeded, [[[0, 0], [0.5, 0.5], [1, 1]], [[2, 2], [3, 3]]], ONE)).toBe(false);
  });

  it('gives them up where the stroke a span names is gone', () => {
    const onSecond: EigenhandPfadSpan[] = [{ stroke: 1, slot: 0, first: 0, last: 1, herkunft: 'auto' }];
    expect(spansStillFit([[[0, 0]], [[1, 1], [2, 2]]], [[[0, 0]]], onSecond)).toBe(false);
    // A stroke BELOW the reach that changed length renumbers nothing here, but
    // a dropped one would — so everything up to the reach is compared.
    expect(spansStillFit([[[0, 0]], [[1, 1], [2, 2]]], [[[0, 0], [9, 9]], [[1, 1], [2, 2]]], onSecond)).toBe(false);
  });

  it('has nothing to give up where there are no spans', () => {
    expect(spansStillFit([[[0, 0]]], [[[0, 0]], [[1, 1]]], [])).toBe(true);
    expect(spansStillFit([[[0, 0]]], [[[0, 0]]], null)).toBe(false);
  });
});
