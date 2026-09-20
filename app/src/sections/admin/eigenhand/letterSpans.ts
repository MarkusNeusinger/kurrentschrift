// Die Buchstabengrenzen einer Bahn, as the editor moves them — pure, so the
// one rule that decides what becomes ground truth is unit-tested rather than
// read out of a pointer handler.
//
// A span says which SAMPLES of which stroke belong to one shaped slot
// (`letter_spans`, checked server-side since Streifen-Pfad format 2). What the
// author corrects is never a span on its own but the SEAM between two of them:
// moving the end of „l" is the same act as moving the start of „e", and
// treating it as two independent edits is how a sample ends up in both letters
// or in neither — the overlap `check_paths` refuses.
//
// Two rules this module exists to keep:
//
//  1. A seam that did not MOVE changes nothing. The spans come back by
//     identity, so a tap on the canvas cannot re-stamp a follower's own
//     assignment as the author's (`herkunft: 'authored'` survives every later
//     re-follow — claiming it for a boundary nobody touched would freeze a
//     guess as truth and feed it to the Span-Zuordner's training set).
//  2. The boundaries belong to the RUN they sit on. They index samples of one
//     stroke, so a redrawn stroke invalidates every span on it; `spansStillFit`
//     is what the editor asks before it resends them. What that question is NOT
//     is „did the drawing change at all": appending a run — the very thing the
//     Absetzer warning asks for when a mark stroke is missing — leaves every
//     existing index valid, and dropping the author's own corrected seams over
//     it would destroy ground truth on the one surface built to create it.
//
// Which run is which is therefore tracked rather than guessed. Counting samples
// answered the wrong question: undo a spanned run, draw a replacement with as
// many samples, and a count comparison says „unchanged" while the boundaries
// now point into a line nobody measured them on (Copilot review). `Drawing`
// carries one id per stroke instead — kept where a stroke's POINTS move
// (Anpassen warps every coordinate and no run becomes another run by it, and
// the pen extends the run it is drawing), handed out fresh where a stroke
// appears at an index the drawing did not have.

import type { EigenhandPfadSpan } from '@/lib/api';
import { savableStrokeIndices, type TracePoint } from '@/sections/admin/belege/registration';

/** The provenance a corrected boundary carries (`core.eigenhand.pfad.AUTHORED`). */
export const SPAN_AUTHORED = 'authored';

export type SpanSeam = {
  /** Index into the span list of the letter BEFORE the boundary. */
  before: number;
  /** …and of the one after it. */
  after: number;
  /** The stroke both spans lie on. */
  stroke: number;
  /** The last sample still belonging to `before` — where the handle sits. */
  sample: number;
  /** The window the boundary may be dragged into, inclusive: each of the two
   * letters keeps at least one sample. */
  min: number;
  max: number;
};

/**
 * The draggable seams of one span list, in reading order per stroke.
 *
 * Only ADJACENT spans of the same stroke make one (`after.first === before.last
 * + 1`). A gap between two spans is a stretch the follower could not label, and
 * closing it by dragging would silently assign that ink to one of the
 * neighbours — that is the Span-Zuordner's job, not a drag's.
 */
export function seamsOf(spans: readonly EigenhandPfadSpan[] | null | undefined): SpanSeam[] {
  if (!spans || spans.length < 2) return [];
  const order = spans
    .map((span, index) => ({ span, index }))
    .sort((a, b) => a.span.stroke - b.span.stroke || a.span.first - b.span.first);
  const seams: SpanSeam[] = [];
  for (let i = 1; i < order.length; i += 1) {
    const before = order[i - 1];
    const after = order[i];
    if (before.span.stroke !== after.span.stroke) continue;
    if (after.span.first !== before.span.last + 1) continue;
    seams.push({
      before: before.index,
      after: after.index,
      stroke: before.span.stroke,
      sample: before.span.last,
      min: before.span.first,
      max: after.span.last - 1,
    });
  }
  return seams;
}

/**
 * The span list with one seam moved to `sample` — both sides stamped as the
 * author's own, and the list returned BY IDENTITY where nothing moved.
 */
export function moveBoundary(
  spans: readonly EigenhandPfadSpan[],
  seam: SpanSeam,
  sample: number,
): readonly EigenhandPfadSpan[] {
  const target = Math.max(seam.min, Math.min(seam.max, Math.round(sample)));
  if (target === seam.sample) return spans;
  return spans.map((span, index) => {
    if (index === seam.before) return { ...span, last: target, herkunft: SPAN_AUTHORED };
    if (index === seam.after) return { ...span, first: target + 1, herkunft: SPAN_AUTHORED };
    return span;
  });
}

/**
 * Which sample of `stroke` lies closest to `point`, within `min..max`.
 *
 * Compared in the path's OWN units (the frame the strokes are stored in), so
 * the answer does not depend on the zoom the author happens to be drawing at.
 */
export function nearestSample(
  stroke: readonly (readonly number[])[],
  point: readonly number[],
  min: number,
  max: number,
): number {
  let best = Math.max(0, Math.min(stroke.length - 1, min));
  let bestDistance = Number.POSITIVE_INFINITY;
  const last = Math.min(stroke.length - 1, max);
  for (let i = Math.max(0, min); i <= last; i += 1) {
    const dx = stroke[i][0] - point[0];
    const dy = stroke[i][1] - point[1];
    const distance = dx * dx + dy * dy;
    if (distance < bestDistance) {
      bestDistance = distance;
      best = i;
    }
  }
  return best;
}

/**
 * Which seam the pen came down on — the nearest handle within `radius`, or
 * `null` where the pen touched down nowhere near one.
 *
 * Everything is in the path's OWN units, the frame the strokes are stored in:
 * a radius in x-heights means the same reach on a big strip and a small one,
 * and on a zoomed canvas and a shrunk one.
 */
export function seamAt(
  seams: readonly SpanSeam[],
  strokes: readonly (readonly (readonly number[])[])[],
  point: readonly number[],
  radius: number,
): number | null {
  let best: number | null = null;
  let bestDistance = radius * radius;
  seams.forEach((seam, index) => {
    const handle = strokes[seam.stroke]?.[seam.sample];
    if (!handle) return;
    const dx = handle[0] - point[0];
    const dy = handle[1] - point[1];
    const distance = dx * dx + dy * dy;
    if (distance <= bestDistance) {
      bestDistance = distance;
      best = index;
    }
  });
  return best;
}

/**
 * The drawing on the canvas, with one identity per stroke.
 *
 * The ids exist for the span guard alone: a boundary names a stroke by its
 * INDEX, and an index says nothing about whether the run under it is still the
 * run the boundary was measured on.
 */
export type Drawing = {
  strokes: TracePoint[][];
  /** One id per stroke, in the strokes' own order. */
  ids: readonly number[];
  /** The next free id — carried in the value so an update is pure, and two
   * invocations of the same one (React's double-render) agree. */
  nextId: number;
};

/** The ids a seeded Bahn's runs carry: 0…n−1, in the order it was stored. */
export const seedStrokeIds = (count: number): number[] => Array.from({ length: count }, (_, index) => index);

/** The drawing a session starts from — the stored Bahn, run for run. */
export const seedDrawing = (strokes: TracePoint[][]): Drawing => ({
  strokes,
  ids: seedStrokeIds(strokes.length),
  nextId: strokes.length,
});

/**
 * The same drawing after one edit, with the ids carried across.
 *
 * A stroke at an index the drawing already had keeps its id: that covers the
 * Anpassen warp (every coordinate moves, no run becomes another run) and the
 * pen extending the run it is currently drawing. An index the drawing did NOT
 * have is a new run — including the one that appears where an undone run
 * stood, which is exactly the replacement a boundary must not survive.
 */
export function advanceDrawing(previous: Drawing, strokes: TracePoint[][]): Drawing {
  if (strokes === previous.strokes) return previous;
  const ids: number[] = [];
  let nextId = previous.nextId;
  for (let i = 0; i < strokes.length; i += 1) {
    if (i < previous.ids.length) ids.push(previous.ids[i]);
    else {
      ids.push(nextId);
      nextId += 1;
    }
  }
  return { strokes, ids, nextId };
}

/** The ids of the runs a save would actually send, in the order it sends them —
 * `sanitizeStrokes` drops stray taps, and dropping one renumbers the rest. */
export const savableStrokeIds = (drawing: Drawing): number[] =>
  savableStrokeIndices(drawing.strokes).map((index) => drawing.ids[index]);

/**
 * Whether the stored boundaries still describe the drawing that is about to be
 * sent — asked of the RUNS' identities, not of their coordinates.
 *
 * Anpassen moves points and never their count, and an ironed-out wobble keeps
 * its letters, so a moved run still carries the samples its boundaries name.
 * A REPLACED run does not, however many samples it happens to have: undoing a
 * spanned run and drawing another one is a different line, and equal counts
 * would have called it unchanged.
 *
 * Only the runs a span actually REACHES are asked: runs are appended at the
 * end, so one drawn beside the ones the boundaries sit on shifts no index and
 * invalidates nothing. That narrower question matters — the Absetzer-Soll
 * invites exactly this edit („a mark stroke is missing"), and the wide answer
 * would silently give up every `authored` seam the author corrected in an
 * earlier session, which the per-box write, replacing the entry whole, then
 * deletes for good.
 */
export function spansStillFit(
  seeded: readonly number[],
  current: readonly number[],
  spans: readonly EigenhandPfadSpan[] | null | undefined,
): boolean {
  if (!spans) return false;
  const reach = spans.reduce((max, span) => Math.max(max, span.stroke), -1) + 1;
  if (reach > seeded.length || reach > current.length) return false;
  for (let i = 0; i < reach; i += 1) {
    if (seeded[i] !== current[i]) return false;
  }
  return true;
}

/** How many boundaries of this list the author has corrected by hand. */
export const authoredSpanCount = (spans: readonly EigenhandPfadSpan[] | null | undefined): number =>
  (spans ?? []).filter((span) => span.herkunft === SPAN_AUTHORED).length;
