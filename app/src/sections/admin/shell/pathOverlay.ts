// The geometry of a DRAWN PEN PATH — the pure half of `PathOverlay`.
//
// A stored path is a list of polylines in word units (baseline 0, midband 1,
// x growing from the word's origin), one per pen-down stretch. Drawn flat it
// says only WHERE the ink is; everything that makes it a path — which stretch
// came first, which way the pen ran, where it left the paper — has to be
// derived, and that derivation lives here rather than inside a component so it
// can be tested without a DOM.
//
// Three things are computed:
//   * the ORDER ramp: one colour per pen-down stretch, first → last;
//   * the DIRECTION arrow: a triangle at each stretch's end, aimed along its
//     last non-degenerate segment;
//   * the LIFTS: the segment from one stretch's end to the next one's start —
//     the Absetzer, which a flat line hides completely.
//
// Everything is in the path's own units; the SVG matrix does the scaling, so
// nothing here knows about pixels.

export type Point = [number, number];
export type Stroke = Point[];

/** Where one pen-down stretch ends, and which way the pen was going there. */
export interface Tip {
  at: Point;
  // Unit direction of the last non-degenerate segment. `null` for a stretch
  // that stands still (every point identical) — there is no direction to draw,
  // and an arrow pointing nowhere is worse than none.
  dir: Point | null;
}

/** One Absetzer: the pen up at `from`, down again at `to`. */
export interface Lift {
  from: Point;
  to: Point;
}

const clamp01 = (value: number): number => (value < 0 ? 0 : value > 1 ? 1 : value);

function hexToRgb(hex: string): [number, number, number] {
  const value = hex.replace('#', '');
  const full =
    value.length === 3
      ? value
          .split('')
          .map((c) => c + c)
          .join('')
      : value;
  return [
    parseInt(full.slice(0, 2), 16) || 0,
    parseInt(full.slice(2, 4), 16) || 0,
    parseInt(full.slice(4, 6), 16) || 0,
  ];
}

const toHex = (n: number): string => Math.round(clamp01(n / 255) * 255).toString(16).padStart(2, '0');

/** Linear RGB blend of two hex colours — `t` 0 gives `from`, 1 gives `to`. */
export function mixHex(from: string, to: string, t: number): string {
  const a = hexToRgb(from);
  const b = hexToRgb(to);
  const k = clamp01(t);
  return `#${a.map((channel, i) => toHex(channel + (b[i] - channel) * k)).join('')}`;
}

/**
 * One colour per pen-down stretch, first → last along the ramp. A single
 * stroke keeps the ramp's START colour: with nothing to compare it to, the
 * word should look like the plain trace it effectively is.
 */
export function orderColors(count: number, from: string, to: string): string[] {
  if (count <= 0) return [];
  if (count === 1) return [from];
  return Array.from({ length: count }, (_, i) => mixHex(from, to, i / (count - 1)));
}

/**
 * The end of one stretch with its direction — the anchor of the arrow head.
 *
 * The direction is taken from the last segment that actually MOVES. Followed
 * paths carry repeated points where the pen slowed at a reversal, and the
 * naive last-two-points reading turns those into arrows pointing at random.
 */
export function tipOf(stroke: Stroke): Tip | null {
  if (!stroke || stroke.length === 0) return null;
  const at = stroke[stroke.length - 1];
  for (let i = stroke.length - 2; i >= 0; i -= 1) {
    const dx = at[0] - stroke[i][0];
    const dy = at[1] - stroke[i][1];
    const len = Math.hypot(dx, dy);
    if (len > 1e-9) return { at, dir: [dx / len, dy / len] };
  }
  return { at, dir: null };
}

/** The start of the whole path — where the pen first touched the paper. */
export function startPointOf(strokes: Stroke[]): Point | null {
  const first = (strokes ?? []).find((stroke) => stroke.length > 0);
  return first ? first[0] : null;
}

/**
 * The Absetzer between consecutive stretches. A lift of (almost) no length is
 * dropped: a path that lifts and sets down in the same spot has nothing to
 * draw, and a zero-length dash renders as a dot that reads like a marker.
 */
export function liftsOf(strokes: Stroke[], minLength = 1e-6): Lift[] {
  const lifts: Lift[] = [];
  const drawn = (strokes ?? []).filter((stroke) => stroke.length > 0);
  for (let i = 0; i + 1 < drawn.length; i += 1) {
    const from = drawn[i][drawn[i].length - 1];
    const to = drawn[i + 1][0];
    if (Math.hypot(to[0] - from[0], to[1] - from[1]) >= minLength) lifts.push({ from, to });
  }
  return lifts;
}

/**
 * The arrow head at a tip as an SVG polygon — a triangle of `size` units
 * pointing along `dir`, `spread` wide across it. Returns null where the
 * stretch has no direction.
 */
export function arrowPoints(tip: Tip, size: number, spread = 0.5): string | null {
  if (!tip.dir) return null;
  const [dx, dy] = tip.dir;
  const [nx, ny] = [-dy, dx];
  const base: Point = [tip.at[0] - dx * size, tip.at[1] - dy * size];
  const half = size * spread;
  const left: Point = [base[0] + nx * half, base[1] + ny * half];
  const right: Point = [base[0] - nx * half, base[1] - ny * half];
  return [tip.at, left, right].map(([x, y]) => `${x},${y}`).join(' ');
}

/** A polyline as an SVG path `d` — the same spelling the word cards used inline. */
export const strokePathD = (stroke: Stroke): string =>
  stroke.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${y}`).join(' ');

/**
 * Where a stroke index label is set: a little PAST the stretch's start, along
 * its opening direction, so the number never sits on the first ink point.
 */
export function labelPointOf(stroke: Stroke, offset: number): Point | null {
  if (!stroke || stroke.length === 0) return null;
  const at = stroke[0];
  for (let i = 1; i < stroke.length; i += 1) {
    const dx = stroke[i][0] - at[0];
    const dy = stroke[i][1] - at[1];
    const len = Math.hypot(dx, dy);
    // Backwards along the opening direction: the label stands where the pen
    // came FROM, which is the one place the path itself is guaranteed not to be.
    if (len > 1e-9) return [at[0] - (dx / len) * offset, at[1] - (dy / len) * offset];
  }
  return [at[0], at[1] + offset];
}
