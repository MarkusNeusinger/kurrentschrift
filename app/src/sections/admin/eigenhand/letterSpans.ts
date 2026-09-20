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
//  2. The boundaries belong to the BAHN. They index samples, so a redrawn
//     stroke invalidates every span on it; `sameStrokeShape` is what the
//     editor asks before it resends them. Anpassen (which moves points and
//     never their count) keeps them, drawing does not.

import type { EigenhandPfadSpan } from '@/lib/api';

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
 * Whether two stroke lists have the same SHAPE — same number of strokes, each
 * with the same number of samples. That, and not equality of coordinates, is
 * what a stored span needs: it indexes positions, so moving a point keeps it
 * valid and adding or dropping one does not.
 */
export function sameStrokeShape(
  a: readonly (readonly unknown[])[],
  b: readonly (readonly unknown[])[],
): boolean {
  return a.length === b.length && a.every((stroke, i) => stroke.length === b[i].length);
}

/** How many boundaries of this list the author has corrected by hand. */
export const authoredSpanCount = (spans: readonly EigenhandPfadSpan[] | null | undefined): number =>
  (spans ?? []).filter((span) => span.herkunft === SPAN_AUTHORED).length;
