import { describe, expect, it } from 'vitest';

import { distanceProfile, resampleStroke, type Polyline } from './distanceProfile';

const line = (x0: number, x1: number, n: number, y = 0): Polyline =>
  Array.from({ length: n }, (_v, i) => [x0 + ((x1 - x0) * i) / (n - 1), y]);

describe('resampleStroke', () => {
  it('keeps the endpoints exactly and spaces samples uniformly', () => {
    const out = resampleStroke(
      [
        [0, 0],
        [1, 0],
        [1, 1],
        [3, 1],
      ],
      0.25,
    );
    expect(out[0]).toEqual([0, 0]);
    expect(out[out.length - 1]).toEqual([3, 1]);
    expect(out.length).toBe(4 / 0.25 + 1); // total arc 4.0
    const steps = out.slice(1).map((p, i) => Math.hypot(p[0] - out[i][0], p[1] - out[i][1]));
    expect(Math.max(...steps) - Math.min(...steps)).toBeLessThan(1e-9);
  });

  it('collapses a degenerate stroke to its endpoints instead of throwing', () => {
    expect(
      resampleStroke(
        [
          [1, 2],
          [1, 2],
        ],
        0.1,
      ),
    ).toEqual([
      [1, 2],
      [1, 2],
    ]);
    expect(resampleStroke([[4, 5]], 0.1)).toEqual([
      [4, 5],
      [4, 5],
    ]);
  });
});

describe('distanceProfile', () => {
  it('reads zero on identical geometry and the offset under a pure shift', () => {
    const trace = [line(0, 4, 200)];
    const identity = distanceProfile(trace, [line(0, 4, 10)]);
    expect(Math.max(...identity.points.map((p) => p.dist))).toBeLessThan(1e-9);

    const shifted = distanceProfile(trace, [line(0, 4, 10, 0.07)]);
    for (const p of shifted.points) expect(p.dist).toBeCloseTo(0.07, 6);
  });

  it('measures against segments, so a sparsely sampled engine line costs nothing', () => {
    // Two engine points only — a trace sample midway must read ~0, never the
    // distance to the nearest VERTEX.
    const profile = distanceProfile([line(0, 4, 100)], [line(0, 4, 2)]);
    expect(Math.max(...profile.points.map((p) => p.dist))).toBeLessThan(1e-9);
  });

  it('accumulates ink arc only and names the lifts', () => {
    const profile = distanceProfile(
      [
        [
          [0, 0],
          [1, 0],
        ],
        [
          [1.5, 0],
          [2.5, 0],
        ],
      ],
      [line(0, 3, 4)],
    );
    // 1.0 + 1.0 of ink; the 0.5 jump between the strokes adds no arc.
    expect(profile.points[profile.points.length - 1].arc).toBeCloseTo(2.0, 9);
    expect(profile.lifts).toHaveLength(1);
    expect(profile.lifts[0]).toBeCloseTo(1.0, 9);
  });

  it('never bridges the gap between two engine items', () => {
    // A trace sample sitting in the gap between two engine strokes must pay
    // its distance to the nearer stroke END, not to a phantom bridge.
    const profile = distanceProfile([[[1.5, 0.4]]], [
      [
        [0, 0],
        [1, 0],
      ],
      [
        [2, 0],
        [3, 0],
      ],
    ]);
    expect(profile.points[0].dist).toBeCloseTo(Math.hypot(0.5, 0.4), 9);
  });
});
