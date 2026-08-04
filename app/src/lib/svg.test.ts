// Unit cover for the two path helpers — specifically for the sign trap between
// them, which silently mirrored geometry in three admin surfaces.
//
// `ringsToPathD` defaults to NOT negating y, `polylineToPathD` defaults to
// negating it. A surface that draws both kinds of item under one y-flipping
// `<g>` therefore got the letters (rings) right side up and the generated
// connectors (polylines) flipped a second time — they appeared as loose strokes
// under the baseline, which is exactly what an admin reported seeing under a
// word. The asymmetric defaults stay (the public "as written" surfaces rely on
// them), so the guard has to be a test that states the rule out loud.

import { describe, expect, it } from 'vitest';

import { polylineToPathD, ringsToPathD, type Ring } from './svg';

const LINE: Ring = [
  [0, 0.5],
  [1, 0.75],
];
const RING: Ring[] = [
  [
    [0, 0],
    [1, 0],
    [1, 0.5],
  ],
];

describe('polylineToPathD', () => {
  it('negates y by default', () => {
    expect(polylineToPathD(LINE)).toBe('M0,-0.5 L1,-0.75');
  });

  it('keeps y when the caller already flips', () => {
    expect(polylineToPathD(LINE, 0, false)).toBe('M0,0.5 L1,0.75');
  });

  it('translates x without touching the sign rule', () => {
    expect(polylineToPathD(LINE, 2, false)).toBe('M2,0.5 L3,0.75');
    expect(polylineToPathD(LINE, 2)).toBe('M2,-0.5 L3,-0.75');
  });

  it('renders an empty polyline as an empty path', () => {
    expect(polylineToPathD([])).toBe('');
  });
});

describe('ringsToPathD', () => {
  it('keeps y by default and negates on request', () => {
    expect(ringsToPathD(RING)).toBe('M0,0 L1,0 L1,0.5 Z');
    // `-1 * 0` stringifies as "0", so only the non-zero ordinate shows a sign.
    expect(ringsToPathD(RING, true)).toBe('M0,0 L1,0 L1,-0.5 Z');
  });

  it('drops degenerate rings', () => {
    expect(
      ringsToPathD([
        [
          [0, 0],
          [1, 1],
        ],
      ]),
    ).toBe('');
  });
});

describe('the sign trap between them', () => {
  it('agrees only when both are told the same thing', () => {
    // THE rule for any surface drawing rings and polylines in one <g>: the two
    // helpers must be given the same flip, explicitly. Their defaults do not.
    const defaults = [ringsToPathD(RING), polylineToPathD(LINE)];
    expect(defaults[0].includes('-')).toBe(false);
    expect(defaults[1].includes('-')).toBe(true); // ← the mirrored connector

    const aligned = [ringsToPathD(RING, false), polylineToPathD(LINE, 0, false)];
    expect(aligned.every((d) => !d.includes('-'))).toBe(true);
  });
});
