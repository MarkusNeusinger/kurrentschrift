import { describe, expect, it } from 'vitest';

import { REPLAY_CLEAR, REPLAY_GUTTER, replayGround } from './replayGround';

// What the box owes the button, checked the way the browser was checked: the
// 30 × 30 rect sits `bottom: 4; right: 4` inside the box, the ink is centred in
// it, so the ground beside or below the ink has to clear REPLAY_CLEAR.
const sideGround = (boxW: number, inkW: number) => (boxW - inkW) / 2;
const floorGround = (boxH: number, inkH: number) => (boxH - inkH) / 2;

describe('replayGround', () => {
  it('steps aside with a full gutter where the frame has room for one', () => {
    // The quiz's own case: 120 px of letter in a 286 px card.
    const g = replayGround(120, 150, 286);
    expect(g.width).toBe(120 + 2 * REPLAY_GUTTER);
    expect(g.minHeight).toBeUndefined();
    expect(sideGround(g.width!, 120)).toBe(REPLAY_GUTTER);
  });

  it('takes the full gutter at the exact boundary, not one ulp less', () => {
    // 208.1 = 120.1 + 88 in binary floats: the version that compared
    // `width - inkW >= 2 * GUTTER` fell through here and reserved vertically.
    const g = replayGround(120.1, 150, 120.1 + 2 * REPLAY_GUTTER);
    expect(g.minHeight).toBeUndefined();
    expect(sideGround(g.width!, 120.1)).toBeCloseTo(REPLAY_GUTTER, 6);
  });

  it('steps aside as far as a tight frame allows, still clear of the ink', () => {
    const inkW = 200;
    const frameW = inkW + 2 * REPLAY_CLEAR + 4; // under a gutter, over the footprint
    const g = replayGround(inkW, 150, frameW);
    expect(g.width).toBe(frameW);
    expect(g.minHeight).toBeUndefined();
    expect(sideGround(g.width!, inkW)).toBeGreaterThanOrEqual(REPLAY_CLEAR);
  });

  it('falls to a floor under the writing where the ink fills the frame', () => {
    // A wrapped line on a phone: 281 px of ink in a 286 px card.
    const g = replayGround(281, 159, 286);
    expect(g.width).toBe(286);
    expect(floorGround(g.minHeight!, 159)).toBe(REPLAY_GUTTER);
    expect(floorGround(g.minHeight!, 159)).toBeGreaterThanOrEqual(REPLAY_CLEAR);
  });

  it('reserves a floor and no width while the frame is unmeasured', () => {
    const g = replayGround(200, 100, 0);
    expect(g.width).toBeUndefined();
    expect(floorGround(g.minHeight!, 100)).toBeGreaterThanOrEqual(REPLAY_CLEAR);
  });

  it('leaves ground for the button at every frame width — the tiers are exhaustive', () => {
    const inkW = 120;
    const inkH = 150;
    for (let frameW = 0; frameW <= 400; frameW += 1) {
      const g = replayGround(inkW, inkH, frameW);
      const clear =
        (g.width !== undefined && sideGround(g.width, inkW) >= REPLAY_CLEAR) ||
        (g.minHeight !== undefined && floorGround(g.minHeight, inkH) >= REPLAY_CLEAR);
      expect(clear, `frame ${frameW}px left the button on the ink`).toBe(true);
    }
  });

  it('never asks for a box narrower than the ink it holds', () => {
    for (const frameW of [0, 50, 120, 208, 300]) {
      const g = replayGround(120, 150, frameW);
      if (g.width !== undefined) expect(g.width).toBeGreaterThanOrEqual(Math.min(120, frameW));
    }
  });
});
