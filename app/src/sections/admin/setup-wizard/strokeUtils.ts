// Pure helpers for the Weg (ductus) stroke capture — no React.

import type { StrokePoint } from '@/lib/api';

// A real stroke needs at least two points; a single point is a stray tap (pointer
// down/up without moving) and must not become its own stroke.
export const MIN_STROKE_POINTS = 2;

// Flatten the captured per-stroke points into one raw_path, marking the last
// sample of every stroke but the final one with pen_up. The backend splits there
// so a pen lift (Absetzen) stays a real gap — no connecting line from the end of
// one stroke to the start of the next (e.g. the two downstrokes of a u). Strokes
// shorter than MIN_STROKE_POINTS are dropped first, so a stray tap never reaches
// the backend as a degenerate zero-length segment (and the pen_up boundaries are
// computed over the real strokes only).
export function flattenStrokes(strokes: StrokePoint[][]): StrokePoint[] {
  const real = strokes.filter((s) => s.length >= MIN_STROKE_POINTS);
  const out: StrokePoint[] = [];
  real.forEach((stroke, si) => {
    stroke.forEach((p, pi) => {
      const isLiftPoint = pi === stroke.length - 1 && si < real.length - 1;
      out.push(isLiftPoint ? { ...p, pen_up: true } : p);
    });
  });
  return out;
}

// Points that will actually be saved (stray taps dropped) — gates "save" so the
// button matches what flattenStrokes would send.
export const savablePointCount = (strokes: StrokePoint[][]): number =>
  strokes.reduce((n, s) => n + (s.length >= MIN_STROKE_POINTS ? s.length : 0), 0);

// Inverse of flattenStrokes: split a stored raw_path back into per-stroke
// polylines at the pen_up markers, for overlaying the saved Weg on the canvas.
export function splitRawPath(rawPath: StrokePoint[]): StrokePoint[][] {
  const strokes: StrokePoint[][] = [];
  let current: StrokePoint[] = [];
  for (const p of rawPath) {
    current.push(p);
    if (p.pen_up) {
      strokes.push(current);
      current = [];
    }
  }
  if (current.length > 0) strokes.push(current);
  return strokes;
}
