// Human writing kinematics for the reveal animation (framework-free maths).
//
// A constant sweep speed is the tell that a machine writes: real pens obey the
// two-thirds power law — tangential speed v ∝ κ^(−1/3), i.e. the pen slows in
// curves (Lacquaniti/Viviani; holds for handwriting) — and isochrony: stroke
// duration grows sublinearly with stroke length. Both are cheap to apply on
// the existing stroke-dashoffset path (docs/concepts/federmodelle.md §5):
//
//  - per-sample time weight  w_i = Δs_i · (1 + κ_i·r_ref)^(1/3)  with
//    r_ref = 1 x-height (coordinates are template units), the +1 clamping
//    straight-line speed;
//  - a stroke's total weight drives its duration share, raised to
//    ISOCHRONY_BETA < 1 so long strokes don't drag;
//  - the cumulative weight curve becomes non-linear dashoffset KEYFRAMES, so
//    the front visibly decelerates into bends and accelerates out of them.

export type Point = [number, number];

// Sublinear length→duration exponent (β ≈ 0.5–0.6 in the handwriting
// literature; 1 would be the old proportional allocation).
export const ISOCHRONY_BETA = 0.6;

// Keyframe steps per stroke: offsets at 10 % time increments approximate the
// smooth speed profile with piecewise-linear CSS segments.
const KEYFRAME_STEPS = 10;

export interface StrokeTimeProfile {
  // Total time weight of the stroke (arc length, curvature-inflated) — the
  // isochrony basis for duration allocation across strokes.
  weight: number;
  // Arc-length fraction ŝ (0..1) reached at each time fraction t̂ = k/steps,
  // k = 0..steps — feeds `stroke-dashoffset: 1 − ŝ` keyframes.
  arcAtTime: number[];
}

// Discrete curvature at an interior sample: turn angle over the mean of the
// adjacent segment lengths (radians per x-height ≈ 1/radius).
function curvatureAt(prev: Point, cur: Point, next: Point): number {
  const ax = cur[0] - prev[0];
  const ay = cur[1] - prev[1];
  const bx = next[0] - cur[0];
  const by = next[1] - cur[1];
  const la = Math.hypot(ax, ay);
  const lb = Math.hypot(bx, by);
  if (la < 1e-9 || lb < 1e-9) return 0;
  const cross = ax * by - ay * bx;
  const dot = ax * bx + ay * by;
  const turn = Math.abs(Math.atan2(cross, dot));
  return turn / ((la + lb) / 2);
}

export function strokeTimeProfile(points: Point[]): StrokeTimeProfile {
  const n = points.length;
  if (n < 2) return { weight: 0, arcAtTime: Array.from({ length: KEYFRAME_STEPS + 1 }, (_, k) => k / KEYFRAME_STEPS) };
  // Per-segment arc length and time weight (curvature sampled at the segment's
  // start vertex; only the FIRST segment has no preceding turn → plain length).
  const segLen: number[] = [];
  const segW: number[] = [];
  for (let i = 0; i < n - 1; i++) {
    const ds = Math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1]);
    const kappa = i > 0 ? curvatureAt(points[i - 1], points[i], points[i + 1]) : 0;
    segLen.push(ds);
    segW.push(ds * Math.cbrt(1 + kappa));
  }
  const totalLen = segLen.reduce((s, v) => s + v, 0);
  const totalW = segW.reduce((s, v) => s + v, 0);
  if (totalLen < 1e-9 || totalW < 1e-9) {
    return { weight: 0, arcAtTime: Array.from({ length: KEYFRAME_STEPS + 1 }, (_, k) => k / KEYFRAME_STEPS) };
  }
  // Cumulative (t̂, ŝ) pairs per vertex, then sample ŝ at even t̂ steps.
  const tHat: number[] = [0];
  const sHat: number[] = [0];
  let accW = 0;
  let accL = 0;
  for (let i = 0; i < n - 1; i++) {
    accW += segW[i];
    accL += segLen[i];
    tHat.push(accW / totalW);
    sHat.push(accL / totalLen);
  }
  const arcAtTime: number[] = [];
  let j = 0;
  for (let k = 0; k <= KEYFRAME_STEPS; k++) {
    const t = k / KEYFRAME_STEPS;
    while (j < tHat.length - 1 && tHat[j + 1] < t) j++;
    const t0 = tHat[j];
    const t1 = tHat[Math.min(j + 1, tHat.length - 1)];
    const s0 = sHat[j];
    const s1 = sHat[Math.min(j + 1, sHat.length - 1)];
    const f = t1 > t0 ? (t - t0) / (t1 - t0) : 1;
    arcAtTime.push(Math.min(1, Math.max(0, s0 + f * (s1 - s0))));
  }
  arcAtTime[0] = 0;
  arcAtTime[KEYFRAME_STEPS] = 1;
  return { weight: totalW, arcAtTime };
}

// Allocate ~totalMs across strokes with isochrony: share ∝ weight^β. The
// per-stroke floor may push the SUM above totalMs on stroke-rich texts —
// deliberately the same behaviour as the pre-kinematics allocation (a stroke
// shorter than minMs reads as a flicker); totalMs is a target, not a contract.
export function allocateDurations(weights: number[], totalMs: number, minMs: number): number[] {
  const powered = weights.map((w) => Math.pow(Math.max(w, 1e-6), ISOCHRONY_BETA));
  const sum = powered.reduce((s, v) => s + v, 0) || 1;
  return powered.map((p) => Math.max(minMs, (p / sum) * totalMs));
}
