// Word composition geometry: lay a sequence of canonical glyphs along a shared
// baseline and generate the connecting strokes (Übergänge) between them, so a
// whole word reads as one continuous pen performance. Framework-free — consumes
// the per-glyph `DiagnosticData` (template-frame centerlines, silhouette rings,
// entry/exit points) and emits flat, render-ready draw items in writing order.
//
// "Übergänge sind Konsequenz, keine Daten" (architektur.md §4): we never store a
// bigram. A connector is a short cubic Bézier from glyph A's `exit_pt` (point +
// travel tangent) to glyph B's `entry` (point + travel tangent). Each glyph's
// geometry stays in its own template frame (x origin at its first sample, y up,
// baseline = 0); we only translate it horizontally by `dx` so its entry meets
// the previous glyph's exit. The shared baseline keeps the coupling heights
// (baseline vs midband) honoured implicitly, because entry/exit `xy` already
// encode the join height.

import type { DiagnosticData } from '@/lib/api';
import type { Ring } from '@/lib/svg';

export type Point = [number, number];

// One stroke to draw, in the composed word frame (y up). A glyph stroke carries
// filled silhouette `rings`; a connector carries a constant `strokeWidth`
// (Sütterlin Gleichzug). Both carry a `centerline` the renderer sweeps a reveal
// mask along, in writing order.
export interface DrawItem {
  centerline: Point[];
  rings?: Ring[];
  strokeWidth?: number;
  // Width of the reveal sweep along this centerline (≥ the ink it must uncover).
  maskWidth: number;
  // A pen lift precedes this item (a within-glyph Absetzen) → the renderer
  // inserts a short pause. Connectors and inter-glyph joins flow without a lift.
  lift: boolean;
}

export interface ComposedWord {
  items: DrawItem[];
  bounds: { minX: number; maxX: number; minY: number; maxY: number };
  // Lineature levels (from the first rendered glyph; all share the style ratio).
  guides: DiagnosticData['template_guides'] | null;
  // glyph_keys that could not be placed (no canonical / fetch failed) — surfaced
  // so a caller (the hero) can fall back, or the playground can flag the letter.
  missing: string[];
}

export interface ComposeSlot {
  key: string | null;
  space: boolean;
  data: DiagnosticData | null;
}

const SPACE_ADV = 0.55; // inter-word gap, x-height units
const MISSING_ADV = 0.7; // advance reserved for an unrenderable glyph
const CONNECT_GAP = 0.16; // horizontal span of a connecting stroke
const CONNECT_SAMPLES = 16; // Bézier samples per connector
const DEFAULT_HALF = 0.05; // fallback stroke half-width

function median(xs: number[]): number {
  if (!xs.length) return DEFAULT_HALF;
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

function unit(deg: number): Point {
  const r = (deg * Math.PI) / 180;
  return [Math.cos(r), Math.sin(r)];
}

// Travel direction (degrees, y up) at the start (entering) or end (leaving) of a
// polyline, used when a payload predates the entry/exit tangents. Entering = the
// pen's heading from the first sample to the second; leaving = from the
// second-to-last to the last.
function tangentOf(line: Point[], atEnd = false): number {
  if (line.length < 2) return 0;
  const [p, q] = atEnd ? [line[line.length - 2], line[line.length - 1]] : [line[0], line[1]];
  return (Math.atan2(q[1] - p[1], q[0] - p[0]) * 180) / Math.PI;
}

function sampleBezier(p0: Point, p1: Point, p2: Point, p3: Point, n: number): Point[] {
  const out: Point[] = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    const u = 1 - t;
    const x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0];
    const y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1];
    out.push([x, y]);
  }
  return out;
}

export function composeWord(slots: ComposeSlot[]): ComposedWord {
  const items: DrawItem[] = [];
  const missing: string[] = [];
  let guides: DiagnosticData['template_guides'] | null = null;
  let cursorX = 0;
  // The previous glyph's exit, in the composed frame, for the next connector.
  let prev: { exit: Point; tangentDeg: number; width: number } | null = null;

  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  const track = (pts: Point[]) => {
    for (const [x, y] of pts) {
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
  };

  for (const slot of slots) {
    if (slot.space) {
      cursorX += SPACE_ADV;
      prev = null;
      continue;
    }
    const data = slot.data;
    const centerlines = data?.centerlines_template;
    if (!data || !centerlines || !centerlines.length) {
      if (slot.key) missing.push(slot.key);
      cursorX += MISSING_ADV;
      prev = null;
      continue;
    }
    if (!guides) guides = data.template_guides;

    const halfWidths = data.half_widths_template ?? [];
    const maxHalf = halfWidths.length ? Math.max(...halfWidths) : DEFAULT_HALF;
    const medHalf = median(halfWidths);

    const firstLine = centerlines[0] as Point[];
    const lastLine = centerlines[centerlines.length - 1] as Point[];
    const entryXY: Point = (data.entry?.xy as Point) ?? firstLine[0];
    const exitXY: Point = (data.exit_pt?.xy as Point) ?? lastLine[lastLine.length - 1];

    // Place this glyph so its entry meets the previous glyph's exit + a small
    // gap. With no connector (first glyph, or after a space / unrenderable glyph)
    // start at the running `cursorX` — falling back to 0 would yank the next word
    // back to the origin and overlap it onto earlier glyphs.
    const desiredEntryX = prev ? prev.exit[0] + CONNECT_GAP : cursorX;
    const dx = desiredEntryX - entryXY[0];

    // Connector first (writing order): the pen slides from A's exit into B's entry.
    if (prev) {
      const p0 = prev.exit;
      const p3: Point = [entryXY[0] + dx, entryXY[1]];
      const span = Math.hypot(p3[0] - p0[0], p3[1] - p0[1]);
      const handle = Math.max(0.04, span * 0.4);
      const dOut = unit(prev.tangentDeg);
      const entryDeg = data.entry?.tangent_deg ?? tangentOf(firstLine, false);
      const dIn = unit(entryDeg);
      const p1: Point = [p0[0] + handle * dOut[0], p0[1] + handle * dOut[1]];
      const p2: Point = [p3[0] - handle * dIn[0], p3[1] - handle * dIn[1]];
      const centerline = sampleBezier(p0, p1, p2, p3, CONNECT_SAMPLES);
      const strokeWidth = 2 * Math.min(prev.width, medHalf);
      items.push({ centerline, strokeWidth, maskWidth: strokeWidth * 1.3, lift: false });
      track(centerline);
    }

    // The glyph's own strokes (silhouette + centerline), translated by dx.
    const ringsByStroke = data.outline_paths ?? [];
    centerlines.forEach((cl, si) => {
      const offset = (cl as Point[]).map(([x, y]): Point => [x + dx, y]);
      const rings = (ringsByStroke[si] ?? []).map((r) => r.map(([x, y]): Point => [x + dx, y]));
      items.push({
        centerline: offset,
        rings: rings.length ? rings : undefined,
        maskWidth: 2.2 * maxHalf,
        lift: si > 0, // a within-glyph pen lift precedes every stroke after the first
      });
      track(offset);
      for (const r of rings) track(r);
    });

    const exitAbs: Point = [exitXY[0] + dx, exitXY[1]];
    const exitDeg = data.exit_pt?.tangent_deg ?? tangentOf(lastLine, true);
    prev = { exit: exitAbs, tangentDeg: exitDeg, width: medHalf };
    cursorX = exitAbs[0];
  }

  if (!Number.isFinite(minX)) {
    minX = 0;
    maxX = 1;
    minY = 0;
    maxY = 1;
  }
  return { items, bounds: { minX, maxX, minY, maxY }, guides, missing };
}
