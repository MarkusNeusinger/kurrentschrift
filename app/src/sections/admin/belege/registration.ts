// Registration frame of a stored word-occurrence trace (handmodell H1/H2):
// the ONE place that maps between the trace's template units and the specimen
// crop's pixels, in both directions. Pure (no React, no fetch) so the display
// path (Belege cards) and the editing path (WordTraceEditorDialog, which has
// to invert the mapping for every pointer sample) cannot drift apart.
//
// The trace frame is the word's registration frame: baseline (Grundlinie) =
// v 0, midband (Mittellinie) = v 1, y up, x from the word origin. The crop
// frame is SVG-style pixels of the specimen cut-out, y down.

import type { WordInstanceMeasurements, WordSampleOut } from '@/lib/api';

export type TracePoint = [number, number];

export interface TraceRegistration {
  /** Crop pixels per x-height unit (Grundlinie → Mittellinie). */
  xh: number;
  /** Crop x of the word origin (trace u = 0). */
  tx: number;
  /** Crop row of the Grundlinie (trace v = 0), the row shift already folded in. */
  baselineRow: number;
}

// Schema bounds of WordInstanceItem in api/schemas.py — a save that violates
// them is rejected with a 422, so the editor clamps/caps instead of guessing.
export const MIN_STROKE_POINTS = 2;
export const MAX_STROKES = 128;
export const MAX_STROKE_POINTS = 4096;
export const MAX_TRACE_COORD = 100;

/** Rounding of the stored coordinates — 1e-4 xh is far below pen precision. */
const COORD_DECIMALS = 4;

/**
 * The row's own registration if the harvest measured one, else the sidecar's
 * lineature — the fallback keeps a hand-written row without measurements
 * displayable instead of collapsing it onto y = 0.
 */
export function traceRegistration(
  measurements: WordInstanceMeasurements,
  sample: WordSampleOut,
): TraceRegistration {
  const reg = measurements.registration_px;
  return {
    xh: measurements.xh_px ?? sample.baseline_y - sample.midband_y,
    tx: reg?.tx ?? 0,
    baselineRow: (reg?.baseline_row ?? sample.baseline_y) + (reg?.ty ?? 0),
  };
}

/**
 * SVG transform for a group whose children are drawn in RAW trace coordinates:
 * px = (u·xh + tx, baselineRow − v·xh). Keeping it a matrix means the path `d`
 * stays in trace units, so what is drawn is literally what is stored.
 */
export const registrationMatrix = (r: TraceRegistration): string =>
  `matrix(${r.xh} 0 0 ${-r.xh} ${r.tx} ${r.baselineRow})`;

export const traceToCrop = (r: TraceRegistration, [u, v]: TracePoint): TracePoint => [
  u * r.xh + r.tx,
  r.baselineRow - v * r.xh,
];

export const cropToTrace = (r: TraceRegistration, [px, py]: TracePoint): TracePoint => [
  (px - r.tx) / r.xh,
  (r.baselineRow - py) / r.xh,
];

/** One stroke as an SVG path in trace units (draw it inside registrationMatrix). */
export const strokePathD = (stroke: TracePoint[]): string =>
  stroke.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${y}`).join(' ');

const round = (v: number): number => {
  const f = 10 ** COORD_DECIMALS;
  return Math.round(v * f) / f;
};

// A pointer captured outside the crop still delivers samples; clamping keeps
// such a slip inside the schema's range instead of failing the whole save.
const clamp = (v: number): number => Math.max(-MAX_TRACE_COORD, Math.min(MAX_TRACE_COORD, v));

/** Drop every `keep`-th point until the stroke fits the schema's point cap. */
function decimate(stroke: TracePoint[]): TracePoint[] {
  if (stroke.length <= MAX_STROKE_POINTS) return stroke;
  const step = Math.ceil(stroke.length / MAX_STROKE_POINTS);
  const out = stroke.filter((_, i) => i % step === 0);
  const last = stroke[stroke.length - 1];
  if (out[out.length - 1] !== last) out.push(last);
  return out;
}

/**
 * The captured strokes as the API accepts them: stray taps (a pen-down without
 * movement, which is a lift, not a stroke) dropped, coordinates rounded and
 * clamped, stroke/point counts capped. Returns [] when nothing savable is
 * left — the editor gates its save button on that.
 */
export function sanitizeStrokes(strokes: TracePoint[][]): TracePoint[][] {
  return strokes
    .filter((s) => s.length >= MIN_STROKE_POINTS)
    .slice(0, MAX_STROKES)
    .map((s) => decimate(s).map(([x, y]) => [round(clamp(x)), round(clamp(y))] as TracePoint));
}
