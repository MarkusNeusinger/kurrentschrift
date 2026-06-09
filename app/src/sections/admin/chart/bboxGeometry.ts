// Pure bbox geometry for the chart editor: grip hit-testing, move/resize math
// and the resulting BboxIn payload. Framework-free — no React imports.

import { bboxInFromOut } from '@/lib/bbox';
import { MIN_BOX } from './chartConstants';
import type { BboxIn, BboxOut } from '@/lib/api';

// Move/resize of an existing bbox. `handle` is which grip was grabbed ('move'
// = the body, the rest are edges/corners).
export type EditHandle = 'move' | 'n' | 's' | 'e' | 'w' | 'ne' | 'nw' | 'se' | 'sw';
export interface Rect {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export const clamp = (v: number, lo: number, hi: number): number => Math.max(lo, Math.min(hi, v));

// Which grip of rect `b` sits at image point (x,y)? Resize only triggers on the
// eight little grip squares (corners + edge midpoints); the rest of the box body
// — edges included — moves, so the border lines never block a drag. `tol` is the
// grip hit half-size in image px (the caller scales it by zoom).
export function hitHandle(b: Rect, x: number, y: number, tol: number): EditHandle | null {
  const mx = (b.x0 + b.x1) / 2;
  const my = (b.y0 + b.y1) / 2;
  const onGrip = (gx: number, gy: number) => Math.abs(x - gx) <= tol && Math.abs(y - gy) <= tol;
  if (onGrip(b.x0, b.y0)) return 'nw';
  if (onGrip(b.x1, b.y0)) return 'ne';
  if (onGrip(b.x0, b.y1)) return 'sw';
  if (onGrip(b.x1, b.y1)) return 'se';
  if (onGrip(mx, b.y0)) return 'n';
  if (onGrip(mx, b.y1)) return 's';
  if (onGrip(b.x0, my)) return 'w';
  if (onGrip(b.x1, my)) return 'e';
  // Inclusive bounds so grabbing exactly on a border (between grips) still moves.
  if (x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1) return 'move';
  return null;
}

// Apply a drag delta to the original rect for the grabbed handle, clamped to
// the chart bounds and a minimum size.
export function applyHandle(handle: EditHandle, orig: Rect, dx: number, dy: number, w: number, h: number): Rect {
  if (handle === 'move') {
    const tx = clamp(dx, -orig.x0, w - orig.x1);
    const ty = clamp(dy, -orig.y0, h - orig.y1);
    return { x0: orig.x0 + tx, y0: orig.y0 + ty, x1: orig.x1 + tx, y1: orig.y1 + ty };
  }
  let { x0, y0, x1, y1 } = orig;
  if (handle.includes('n')) y0 = clamp(y0 + dy, 0, y1 - MIN_BOX);
  if (handle.includes('s')) y1 = clamp(y1 + dy, y0 + MIN_BOX, h);
  if (handle.includes('w')) x0 = clamp(x0 + dx, 0, x1 - MIN_BOX);
  if (handle.includes('e')) x1 = clamp(x1 + dx, x0 + MIN_BOX, w);
  return { x0, y0, x1, y1 };
}

// Build the BboxIn for a finished move/resize. A move carries the baseline,
// midband and eraser strokes along by the same offset; a resize keeps the guide
// lines but clamps them into the new bounds (eraser strokes stay in their
// absolute chart-pixel positions — the content under them didn't move).
export function editedBbox(current: BboxOut, handle: EditHandle, cur: Rect): BboxIn {
  const r = { x0: Math.round(cur.x0), y0: Math.round(cur.y0), x1: Math.round(cur.x1), y1: Math.round(cur.y1) };
  const base = bboxInFromOut(current);
  if (handle === 'move') {
    const dx = r.x0 - current.x0;
    const dy = r.y0 - current.y0;
    return {
      ...base,
      ...r,
      baseline_y: current.baseline_y + dy,
      midband_y: current.midband_y + dy,
      mask_strokes: current.mask_strokes.map((m) => ({
        ...m,
        points: m.points.map(([x, y]) => [x + dx, y + dy] as [number, number]),
      })),
    };
  }
  return {
    ...base,
    ...r,
    baseline_y: clamp(current.baseline_y, r.y0, r.y1),
    midband_y: clamp(current.midband_y, r.y0, r.y1),
  };
}
