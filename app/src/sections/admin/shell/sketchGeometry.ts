// The geometry the statistics sketches are drawn with — pure functions, no
// React, so both the full lens block (LensStats) and the miniature in the
// letters overview compute their frames identically. Kept out of the component
// files so react-refresh only ever sees components there (same reason as
// model.ts).

import type { AggregateOut } from '@/lib/api';

// Template units of air around the drawn geometry.
export const SKETCH_PAD = 0.3;

// The white work surface a sketch is drawn on — same framing as the chart crop
// beside it (design-system: an original lies on white).
export const SKETCH_FRAME = {
  bgcolor: '#fff',
  borderRadius: 1,
  border: 1,
  borderColor: 'divider',
  p: 0.5,
  width: 'fit-content',
} as const;

// A wire point is only usable once it really is a finite 2-vector — the rows
// come from JSONB, so length and finiteness are worth asserting before any
// bounds math turns a NaN into an invisible sketch. The offset's MAD goes
// through the SAME check: a spread is a 2-vector too, and a NaN in it would
// reach `toFixed` (or a whisker's coordinates) just as easily.
export const isPoint = (p: unknown): p is number[] =>
  Array.isArray(p) && p.length >= 2 && Number.isFinite(p[0]) && Number.isFinite(p[1]);

// Bounds of a point cloud in template units, padded, plus the y values that
// must stay visible (baseline/midband) whatever the geometry does.
export function boundsOf(points: number[][], extraY: number[]): { minX: number; minY: number; w: number; h: number } {
  const xs = points.map(([x]) => x);
  const ys = [...points.map(([, y]) => y), ...extraY];
  const minX = Math.min(...xs) - SKETCH_PAD;
  const maxX = Math.max(...xs) + SKETCH_PAD;
  const minY = Math.min(...ys) - SKETCH_PAD;
  const maxY = Math.max(...ys) + SKETCH_PAD;
  // Guard against a degenerate cloud (a single anchor, a flat connector):
  // a zero extent would make the viewBox — and every derived stroke width —
  // collapse.
  const w = Math.max(maxX - minX, 0.2);
  const h = Math.max(maxY - minY, 0.2);
  return { minX, minY, w, h };
}

// Template units are y-UP (baseline = 0, midband = 1), SVG is y-down: drawing
// every point mirrored keeps the viewBox a plain rectangle.
export const pathOf = (points: number[][]): string =>
  points.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${-y}`).join(' ');

// One median anchor together with the spread that belongs to IT.
export interface SketchAnchor {
  x: number;
  y: number;
  // Mean of the two axes' MAD, template units; undefined where the aggregate
  // carries none (an absent spread is not a zero spread).
  mad?: number;
}

// Anchors zipped with `hull.anchor_mad` BEFORE any validity filtering: the MAD
// list is positional, so a dropped anchor has to take its own circle with it —
// indexing the spread with the FILTERED index slides every circle one anchor
// along.
export function letterSketchAnchors(aggregate: AggregateOut): SketchAnchor[] {
  const mad = aggregate.hull.anchor_mad ?? [];
  return (aggregate.cluster_center ?? [])
    .map((point, i) => ({ point, spread: mad[i] }))
    .filter(({ point }) => isPoint(point))
    .map(({ point, spread }) => {
      const r = isPoint(spread) ? (spread[0] + spread[1]) / 2 : 0;
      return { x: point[0], y: point[1], mad: r > 0 ? r : undefined };
    });
}

// The per-occurrence anchor chains of one letter, ready to draw: validated and
// dropped where a chain is too short to be a line at all.
export const occurrenceChainsOf = (occurrences: { anchors?: number[][] }[]): number[][][] =>
  occurrences.map((inst) => (inst.anchors ?? []).filter(isPoint)).filter((line) => line.length >= 2);
