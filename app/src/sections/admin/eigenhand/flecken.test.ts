// The eraser's arithmetic, pinned — because a wrong circle looks right.
//
// A mask placed against the wrong scale or origin still renders as a tidy row
// of circles; what it destroys only shows up in the served image, on the
// author's own ink. So the conversion, the hit test and the click semantics
// are asserted here rather than inspected in a screenshot.

import { describe, expect, it } from 'vitest';

import type { EigenhandFleck } from '@/lib/api';
import { circleAt, displayScale, insideStrip, pointAt, toggleAt, FLECK_MAX_R_MM } from './flecken';

const DPI = 300;
const SCALE = displayScale(DPI, 1); // ≈ 11.81 display px per mm at 1:1

function fleck(x_mm: number, y_mm: number, r_mm = 0.5, quelle: EigenhandFleck['quelle'] = 'hand'): EigenhandFleck {
  return { x_mm, y_mm, r_mm, quelle };
}

describe('the display scale', () => {
  it('is the strip resolution times the shown zoom', () => {
    expect(displayScale(DPI, 1)).toBeCloseTo(11.811, 3);
    expect(displayScale(DPI, 2)).toBeCloseTo(23.622, 3);
    expect(displayScale(DPI, 0.25)).toBeCloseTo(2.953, 3);
  });

  it('turns a pointer offset into the strip’s own millimetres', () => {
    // Doubling the zoom halves the millimetres one pixel stands for — the
    // point of the whole conversion, and where an eraser goes wrong silently.
    expect(pointAt(118.11, 23.62, SCALE).x_mm).toBeCloseTo(10, 2);
    expect(pointAt(118.11, 23.62, displayScale(DPI, 2)).x_mm).toBeCloseTo(5, 2);
    expect(pointAt(118.11, 23.62, SCALE).y_mm).toBeCloseTo(2, 2);
  });
});

describe('finding a circle under the pointer', () => {
  const circles = [fleck(10, 5, 0.5, 'auto'), fleck(30, 8, 0.6)];

  it('hits the circle the point lies in', () => {
    expect(circleAt(circles, { x_mm: 10.2, y_mm: 5.1 })).toBe(0);
    expect(circleAt(circles, { x_mm: 30, y_mm: 8 })).toBe(1);
  });

  it('misses everything outside every radius', () => {
    expect(circleAt(circles, { x_mm: 10, y_mm: 6 })).toBe(-1);
    expect(circleAt([], { x_mm: 0, y_mm: 0 })).toBe(-1);
  });

  it('takes the topmost where two overlap', () => {
    const stacked = [fleck(10, 5, 1.0), fleck(10.2, 5, 0.4)];
    expect(circleAt(stacked, { x_mm: 10.2, y_mm: 5 })).toBe(1);
  });
});

describe('one click', () => {
  it('adds a hand circle on empty paper', () => {
    const after = toggleAt([], { x_mm: 12.3456, y_mm: 4 }, 0.6);
    expect(after).toEqual([{ x_mm: 12.346, y_mm: 4, r_mm: 0.6, quelle: 'hand' }]);
  });

  it('removes the circle it lands on, an automatic one included', () => {
    const circles = [fleck(10, 5, 0.5, 'auto'), fleck(30, 8)];
    expect(toggleAt(circles, { x_mm: 10, y_mm: 5 }, 0.6)).toEqual([circles[1]]);
  });

  it('never places a circle wider than the server accepts', () => {
    const [added] = toggleAt([], { x_mm: 1, y_mm: 1 }, FLECK_MAX_R_MM + 5);
    expect(added.r_mm).toBe(FLECK_MAX_R_MM);
  });

  it('leaves the previous list untouched — undo has something to go back to', () => {
    const circles = [fleck(10, 5)];
    toggleAt(circles, { x_mm: 30, y_mm: 8 }, 0.6);
    expect(circles).toEqual([fleck(10, 5)]);
  });
});

describe('the strip’s edges', () => {
  it('accepts a point inside and refuses one past the corner', () => {
    expect(insideStrip({ x_mm: 10, y_mm: 5 }, 185, 30)).toBe(true);
    expect(insideStrip({ x_mm: 0, y_mm: 0 }, 185, 30)).toBe(true);
    expect(insideStrip({ x_mm: 186, y_mm: 5 }, 185, 30)).toBe(false);
    expect(insideStrip({ x_mm: 10, y_mm: -1 }, 185, 30)).toBe(false);
  });
});
