// Abstandsprofil — the word card's display distance: for every point along the
// stored trace, the nearest distance to the engine composition's centerlines,
// in the shared frame both inks already live in (baseline = 0, 1 unit = xh).
//
// Deliberately NOT the duel page's DTW Residualprofil: the trace and the
// composition segment their strokes differently (generated connectors,
// deferred diacritics), so a writing-order pairing would report segmentation
// as error. Nearest distance answers the Werkbank question — WHERE does the
// composition sit beside the author's line — and is labeled a display
// measure, never a bench number. One direction only (trace → engine): extra
// engine ink the hand never wrote is the overlay's job to show, not this
// curve's.
//
// Pure module, no React — unit-tested without a DOM (the pairMeasurement
// pattern).

// Display sampling of the trace, in x-heights. Coarser than the bench's
// 0.02 — this is a reading instrument, and 0.05 keeps a long word's profile
// under ~a thousand points without hiding any deviation wide enough to act on.
export const PROFILE_STEP_UNITS = 0.05;

export type Polyline = Array<[number, number]>;

export interface ProfilePoint {
  arc: number; // arc position along the trace, in xh — written ink only
  dist: number; // nearest distance to the engine centerlines, in xh
  u: number; // the trace sample itself, for the probe over the crop
  v: number;
}

export interface DistanceProfile {
  points: ProfilePoint[];
  lifts: number[]; // arc positions where the pen left the paper
  max: number;
}

// Arc-length-uniform resampling, endpoints exact (the metric.resample_by_step
// contract, restated in TS for display use). Degenerate strokes collapse to
// their endpoints instead of throwing — a stray tap is data, not an error.
export function resampleStroke(points: Polyline, step: number): Polyline {
  if (points.length === 0) return [];
  if (points.length === 1) return [points[0], points[0]];
  const arc: number[] = [0];
  for (let i = 1; i < points.length; i += 1) {
    arc.push(arc[i - 1] + Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]));
  }
  const total = arc[arc.length - 1];
  if (total <= 0 || step <= 0) return [points[0], points[points.length - 1]];
  const n = Math.max(2, Math.round(total / step) + 1);
  const out: Polyline = [];
  let seg = 0;
  for (let k = 0; k < n; k += 1) {
    const t = (total * k) / (n - 1);
    while (seg < arc.length - 2 && arc[seg + 1] < t) seg += 1;
    const span = arc[seg + 1] - arc[seg];
    const w = span > 0 ? (t - arc[seg]) / span : 0;
    out.push([
      points[seg][0] + (points[seg + 1][0] - points[seg][0]) * w,
      points[seg][1] + (points[seg + 1][1] - points[seg][1]) * w,
    ]);
  }
  return out;
}

// Squared point-to-segment distance — squared so the hot loop takes no sqrt.
function segmentDistSq(px: number, py: number, ax: number, ay: number, bx: number, by: number): number {
  const dx = bx - ax;
  const dy = by - ay;
  const lenSq = dx * dx + dy * dy;
  const t = lenSq > 0 ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / lenSq)) : 0;
  const qx = ax + t * dx;
  const qy = ay + t * dy;
  return (px - qx) * (px - qx) + (py - qy) * (py - qy);
}

// The profile: trace strokes and engine centerlines in the SAME unit frame.
// Segments are only ever formed WITHIN one polyline — a pen lift (trace) or an
// item boundary (engine) is never bridged, so the curve cannot credit the
// engine with ink between two of its strokes.
export function distanceProfile(
  traceStrokes: Polyline[],
  engineCenterlines: Polyline[],
  step: number = PROFILE_STEP_UNITS,
): DistanceProfile {
  const targets = engineCenterlines.filter((line) => line.length > 0);
  const points: ProfilePoint[] = [];
  const lifts: number[] = [];
  let offset = 0;
  let max = 0;
  const resampled = traceStrokes.map((stroke) => resampleStroke(stroke, step)).filter((s) => s.length > 0);
  resampled.forEach((stroke, strokeIndex) => {
    let arc = 0;
    stroke.forEach(([u, v], i) => {
      if (i > 0) arc += Math.hypot(u - stroke[i - 1][0], v - stroke[i - 1][1]);
      let best = Infinity;
      for (const line of targets) {
        if (line.length === 1) {
          best = Math.min(best, segmentDistSq(u, v, line[0][0], line[0][1], line[0][0], line[0][1]));
          continue;
        }
        for (let s = 0; s < line.length - 1; s += 1) {
          const d = segmentDistSq(u, v, line[s][0], line[s][1], line[s + 1][0], line[s + 1][1]);
          if (d < best) best = d;
        }
      }
      const dist = targets.length ? Math.sqrt(best) : 0;
      if (dist > max) max = dist;
      points.push({ arc: offset + arc, dist, u, v });
    });
    offset += arc;
    if (strokeIndex < resampled.length - 1) lifts.push(offset);
  });
  return { points, lifts, max };
}
