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
  // A deferred diacritic (i-dot, j-dot, the Sütterlin u-bow, the ä/ö/ü umlaut):
  // a mark that floats above the midband and is written only once the word
  // body is finished. Emitted after the word, never threaded into the flow.
  diacritic?: boolean;
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
// Exit y (baseline = 0, descender ≈ −1) below which a glyph's stroke is judged
// to end inside its descender loop, so the connector becomes a return upstroke
// rather than following the downward exit tangent (see the long-s ſ).
const DESCENDER_EXIT_Y = -0.2;

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

  // Diacritic strokes are held back until the current word is finished, then
  // flushed in encounter (left-to-right) order — the writer dots the i's and
  // sets the umlauts after the word body, not mid-flow. Each becomes its own
  // pen-down (lift) so the renderer pauses before placing it.
  const pendingDiacritics: DrawItem[] = [];
  const flushDiacritics = () => {
    for (const it of pendingDiacritics) {
      it.lift = true;
      items.push(it);
    }
    pendingDiacritics.length = 0;
  };

  for (const slot of slots) {
    if (slot.space) {
      flushDiacritics(); // the word's marks land before the gap to the next word
      cursorX += SPACE_ADV;
      prev = null;
      continue;
    }
    const data = slot.data;
    const centerlines = data?.centerlines_template;
    if (!data || !centerlines || !centerlines.length) {
      if (slot.key) missing.push(slot.key);
      // A null-key slot (punctuation, digit) or a missing glyph breaks the
      // writing run just like a space: flush the marks gathered so far before
      // the gap, so a preceding i-dot/umlaut lands at the end of its word and
      // never after the placeholder.
      flushDiacritics();
      cursorX += MISSING_ADV;
      prev = null;
      continue;
    }
    if (!guides) guides = data.template_guides;

    const halfWidths = data.half_widths_template ?? [];
    const maxHalf = halfWidths.length ? Math.max(...halfWidths) : DEFAULT_HALF;
    const medHalf = median(halfWidths);

    // Classify each pen-stroke. A diacritic (i-dot, j-dot, the Sütterlin u-bow,
    // the ä/ö/ü umlaut) floats entirely above the midband and is never the
    // glyph's first stroke; it is deferred to the end of the word. The
    // t-crossbar sits inside the x-height band (and doubles as t's connecting
    // exit), so it correctly stays in flow.
    const midband = data.template_guides?.midband ?? 1;
    const diacriticFlags = centerlines.map((cl, si) => {
      if (si === 0) return false;
      let minY = Infinity;
      for (const [, y] of cl as Point[]) if (y < minY) minY = y;
      return minY > midband;
    });
    const hasDiacritic = diacriticFlags.some(Boolean);

    const firstLine = centerlines[0] as Point[];
    const lastLine = centerlines[centerlines.length - 1] as Point[];
    // Last NON-diacritic stroke — the part that sits on the writing line and
    // carries the join to the next glyph.
    let lastBodyIdx = centerlines.length - 1;
    if (hasDiacritic) {
      for (let si = centerlines.length - 1; si >= 0; si--) {
        if (!diacriticFlags[si]) {
          lastBodyIdx = si;
          break;
        }
      }
    }
    const bodyExitLine = centerlines[lastBodyIdx] as Point[];

    const entryXY: Point = (data.entry?.xy as Point) ?? firstLine[0];
    // The connector to the NEXT glyph must leave from the body's exit, never
    // from a floating mark. The stored `exit_pt` is the end of the LAST stroke,
    // which on a dotted/umlauted letter is the diacritic (e.g. i's `exit_pt` is
    // the i-dot high above the baseline) — so derive the exit from the last body
    // stroke when the glyph carries one, and keep the precise stored tangent
    // otherwise (no diacritic → last stroke IS the body).
    const exitXY: Point = hasDiacritic
      ? bodyExitLine[bodyExitLine.length - 1]
      : (data.exit_pt?.xy as Point) ?? lastLine[lastLine.length - 1];
    const exitDeg = hasDiacritic
      ? tangentOf(bodyExitLine, true)
      : data.exit_pt?.tangent_deg ?? tangentOf(lastLine, true);

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
      let dOut = unit(prev.tangentDeg);
      // A glyph whose stroke ends deep in its descender loop (the long-s ſ,
      // whose authored ductus stops at the loop bottom) exits pointing downward
      // — following that tangent makes the connector dive even deeper before
      // climbing. There the connector IS the return upstroke: aim it from the
      // loop bottom toward the next entry instead of continuing the descent.
      // Glyphs that finish a descender properly (g, h, j) exit above the
      // baseline, so the guard never fires for them.
      if (p0[1] < DESCENDER_EXIT_Y && dOut[1] < 0 && span > 0) {
        dOut = [(p3[0] - p0[0]) / span, (p3[1] - p0[1]) / span];
      }
      const entryDeg = data.entry?.tangent_deg ?? tangentOf(firstLine, false);
      const dIn = unit(entryDeg);
      const p1: Point = [p0[0] + handle * dOut[0], p0[1] + handle * dOut[1]];
      const p2: Point = [p3[0] - handle * dIn[0], p3[1] - handle * dIn[1]];
      const centerline = sampleBezier(p0, p1, p2, p3, CONNECT_SAMPLES);
      const strokeWidth = 2 * Math.min(prev.width, medHalf);
      items.push({ centerline, strokeWidth, maskWidth: strokeWidth * 1.3, lift: false });
      track(centerline);
    }

    // The glyph's own strokes (silhouette + centerline), translated by dx. Body
    // strokes flow in writing order; diacritic strokes are held back and
    // flushed once the whole word is written.
    const ringsByStroke = data.outline_paths ?? [];
    centerlines.forEach((cl, si) => {
      const offset = (cl as Point[]).map(([x, y]): Point => [x + dx, y]);
      const rings = (ringsByStroke[si] ?? []).map((r) => r.map(([x, y]): Point => [x + dx, y]));
      const item: DrawItem = {
        centerline: offset,
        rings: rings.length ? rings : undefined,
        maskWidth: 2.2 * maxHalf,
        lift: si > 0, // a within-glyph pen lift precedes every stroke after the first
      };
      track(offset);
      for (const r of rings) track(r);
      if (diacriticFlags[si]) {
        item.diacritic = true;
        pendingDiacritics.push(item);
      } else {
        items.push(item);
      }
    });

    const exitAbs: Point = [exitXY[0] + dx, exitXY[1]];
    prev = { exit: exitAbs, tangentDeg: exitDeg, width: medHalf };
    cursorX = exitAbs[0];
  }

  flushDiacritics(); // the last word's marks, once its body is complete

  if (!Number.isFinite(minX)) {
    minX = 0;
    maxX = 1;
    minY = 0;
    maxY = 1;
  }
  return { items, bounds: { minX, maxX, minY, maxY }, guides, missing };
}
