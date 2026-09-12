import { describe, expect, it } from 'vitest';

import {
  arrowPoints,
  labelPointOf,
  liftsOf,
  mixHex,
  orderColors,
  startPointOf,
  strokePathD,
  tipOf,
  type Stroke,
} from './pathOverlay';

describe('orderColors', () => {
  it('walks the ramp from the first pen-down stretch to the last', () => {
    expect(orderColors(3, '#000000', '#ffffff')).toEqual(['#000000', '#808080', '#ffffff']);
  });

  it('keeps a single stretch at the ramp start — there is nothing to compare it to', () => {
    expect(orderColors(1, '#112233', '#ffffff')).toEqual(['#112233']);
    expect(orderColors(0, '#112233', '#ffffff')).toEqual([]);
  });

  it('blends short hex the same as long hex', () => {
    expect(mixHex('#000', '#fff', 1)).toBe('#ffffff');
    expect(mixHex('#ff0000', '#0000ff', 0)).toBe('#ff0000');
  });
});

describe('tipOf', () => {
  it('aims at the last segment that actually moves', () => {
    // Followed paths repeat points where the pen slowed at a reversal; reading
    // the last two points alone would aim the arrow at random there.
    const stroke: Stroke = [
      [0, 0],
      [1, 0],
      [1, 0],
      [1, 0],
    ];
    expect(tipOf(stroke)).toEqual({ at: [1, 0], dir: [1, 0] });
  });

  it('has no direction for a stretch that stands still', () => {
    expect(tipOf([[2, 2]])).toEqual({ at: [2, 2], dir: null });
    expect(
      tipOf([
        [2, 2],
        [2, 2],
      ]),
    ).toEqual({ at: [2, 2], dir: null });
  });

  it('is null for an empty stretch', () => {
    expect(tipOf([])).toBeNull();
  });
});

describe('liftsOf', () => {
  const a: Stroke = [
    [0, 0],
    [1, 1],
  ];
  const b: Stroke = [
    [2, 1],
    [3, 0],
  ];

  it('joins the end of one stretch to the start of the next', () => {
    expect(liftsOf([a, b])).toEqual([{ from: [1, 1], to: [2, 1] }]);
  });

  it('drops a lift that sets down where it lifted', () => {
    const same: Stroke = [
      [1, 1],
      [4, 4],
    ];
    expect(liftsOf([a, same])).toEqual([]);
  });

  it('skips empty stretches instead of drawing lifts to nowhere', () => {
    expect(liftsOf([a, [], b])).toEqual([{ from: [1, 1], to: [2, 1] }]);
    expect(liftsOf([])).toEqual([]);
  });
});

describe('arrowPoints', () => {
  it('points along the direction and spans the spread across it', () => {
    const points = arrowPoints({ at: [1, 0], dir: [1, 0] }, 0.2, 0.5);
    // Tip at the stretch's end, base one `size` back, half a `spread` of the
    // size to either side of it.
    expect(points).toBe('1,0 0.8,0.1 0.8,-0.1');
  });

  it('draws nothing where there is no direction', () => {
    expect(arrowPoints({ at: [1, 0], dir: null }, 0.2)).toBeNull();
  });
});

describe('startPointOf / labelPointOf / strokePathD', () => {
  it('finds the first point the pen set down', () => {
    expect(
      startPointOf([
        [],
        [
          [5, 1],
          [6, 2],
        ],
      ]),
    ).toEqual([5, 1]);
    expect(startPointOf([])).toBeNull();
  });

  it('sets the index label back along the opening direction, off the ink', () => {
    expect(
      labelPointOf(
        [
          [1, 0],
          [2, 0],
        ],
        0.3,
      ),
    ).toEqual([0.7, 0]);
  });

  it('writes a polyline as one move plus lines', () => {
    expect(
      strokePathD([
        [0, 0],
        [1, 2],
      ]),
    ).toBe('M0,0 L1,2');
  });
});
