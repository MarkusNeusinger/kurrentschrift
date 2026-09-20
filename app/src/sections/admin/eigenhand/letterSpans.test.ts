// The rule that decides what becomes ground truth: a boundary the author moved
// is his, one he did not touch stays the follower's.
//
// Both halves matter and only one of them is obvious. A drag has to stamp BOTH
// sides of the seam (one sample belongs to one letter, so the neighbour moves
// with it or the two overlap — which `check_paths` refuses). A tap that moved
// nothing has to change nothing: `herkunft: 'authored'` survives every later
// re-follow, so claiming it for an assignment nobody looked at would freeze a
// guess as truth and feed it to the Span-Zuordner's training set.
//
// And the same rule from the other side: a boundary may only be RESENT while
// the run it names is still that run. Counting samples answered a different
// question — undo a spanned run, draw another one with as many samples, and
// the count says „unchanged" while the boundaries now describe a line nobody
// measured them on. The ids `advanceDrawing` carries are what that costs.

import { describe, expect, it } from 'vitest';

import type { EigenhandPfadSpan } from '@/lib/api';

import type { TracePoint } from '@/sections/admin/belege/registration';

import {
  advanceDrawing,
  authoredSpanCount,
  moveBoundary,
  nearestSample,
  savableStrokeIds,
  seamAt,
  seamsOf,
  seedDrawing,
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

/** Two runs, the way the editor holds them. */
const RUN = (x: number): TracePoint[] => [
  [x, 0],
  [x + 1, 1],
];

describe('advanceDrawing', () => {
  it('keeps a run’s id while its POINTS move — that is what Anpassen does', () => {
    const seeded = seedDrawing([RUN(0), RUN(4)]);
    const warped = advanceDrawing(seeded, [
      [
        [0.5, 0.4],
        [1, 1],
      ],
      RUN(4),
    ]);
    expect(warped.ids).toEqual(seeded.ids);
    expect(warped.strokes[0]).not.toBe(seeded.strokes[0]);
  });

  it('hands out a FRESH id where a run appears at an index the drawing did not have', () => {
    const seeded = seedDrawing([RUN(0)]);
    const appended = advanceDrawing(seeded, [RUN(0), RUN(4)]);
    // Drawn beside the seeded one: it keeps its own id, the new run gets one.
    expect(appended.ids).toEqual([0, 1]);

    // …and the same index, vacated and filled again, is a DIFFERENT run: this
    // is the undo-and-redraw a count comparison called „unchanged".
    const undone = advanceDrawing(seeded, []);
    const redrawn = advanceDrawing(undone, [RUN(9)]);
    expect(redrawn.ids).toEqual([1]);
  });

  it('returns the drawing by identity where nothing was replaced', () => {
    const seeded = seedDrawing([RUN(0)]);
    expect(advanceDrawing(seeded, seeded.strokes)).toBe(seeded);
  });
});

describe('savableStrokeIds', () => {
  it('follows the renumbering a save does — a stray tap is dropped with its id', () => {
    // A pen-down without a move never reaches the API; the run behind it moves
    // up one index, and a boundary that did not follow would name it.
    const drawing = advanceDrawing(seedDrawing([RUN(0), RUN(4)]), [RUN(0), [[9, 9]], RUN(4)]);
    expect(drawing.ids).toEqual([0, 1, 2]);
    expect(savableStrokeIds(drawing)).toEqual([0, 2]);
  });
});

describe('spansStillFit', () => {
  const ONE: EigenhandPfadSpan[] = [
    { stroke: 0, slot: 0, first: 0, last: 0, herkunft: 'auto' },
    { stroke: 0, slot: 1, first: 1, last: 1, herkunft: 'authored' },
  ];

  it('asks WHICH RUN, not how many samples it has', () => {
    const seeded = seedDrawing([RUN(0)]);
    // Anpassen moves points and never their count, and the run stays the run.
    expect(spansStillFit(seeded.ids, advanceDrawing(seeded, [RUN(2)]).ids, ONE)).toBe(true);
    // A replacement with exactly as many samples is still another line — the
    // case equal counts used to wave through (Copilot review).
    const redrawn = advanceDrawing(advanceDrawing(seeded, []), [RUN(7)]);
    expect(redrawn.strokes[0]).toHaveLength(seeded.strokes[0].length);
    expect(spansStillFit(seeded.ids, redrawn.ids, ONE)).toBe(false);
    expect(spansStillFit(seeded.ids, [], ONE)).toBe(false);
  });

  it('keeps the boundaries when a run is drawn BESIDE the ones they sit on', () => {
    // The Absetzer warning asks for exactly this — a missing mark stroke. It
    // shifts no index, so giving up an `authored` seam over it would destroy
    // ground truth the per-box write then deletes for good.
    const seeded = seedDrawing([RUN(0)]);
    const grown = advanceDrawing(seeded, [RUN(0), RUN(4)]);
    expect(spansStillFit(seeded.ids, grown.ids, ONE)).toBe(true);
    // Undoing the run BESIDE them changes nothing about them either — the run
    // they sit on is untouched.
    expect(spansStillFit(seeded.ids, advanceDrawing(grown, [RUN(0)]).ids, ONE)).toBe(true);
    // …but redrawing the run they DO sit on still gives them up, whatever is
    // standing beside it.
    const cleared = advanceDrawing(grown, []);
    expect(spansStillFit(seeded.ids, advanceDrawing(cleared, [RUN(4), RUN(8)]).ids, ONE)).toBe(false);
  });

  it('gives them up where the run a span names is gone', () => {
    const onSecond: EigenhandPfadSpan[] = [{ stroke: 1, slot: 0, first: 0, last: 1, herkunft: 'auto' }];
    const seeded = seedDrawing([RUN(0), RUN(4)]);
    expect(spansStillFit(seeded.ids, advanceDrawing(seeded, [RUN(0)]).ids, onSecond)).toBe(false);
    // A run BELOW the reach that was replaced renumbers nothing here, but the
    // one it pushed down is a different run — so everything up to the reach is
    // compared.
    const firstRedrawn = advanceDrawing(advanceDrawing(seeded, []), [RUN(1), RUN(5)]);
    expect(spansStillFit(seeded.ids, firstRedrawn.ids, onSecond)).toBe(false);
  });

  it('has nothing to give up where there are no spans', () => {
    const seeded = seedDrawing([RUN(0)]);
    expect(spansStillFit(seeded.ids, advanceDrawing(seeded, [RUN(0), RUN(4)]).ids, [])).toBe(true);
    expect(spansStillFit(seeded.ids, seeded.ids, null)).toBe(false);
  });
});
