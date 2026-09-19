// @vitest-environment jsdom
//
// What the path overlay DRAWS, as opposed to what `pathOverlay.ts` computes —
// the pure geometry has its own suite next door, and a dash pattern is not
// geometry: it is an attribute pair, and the pair is the whole point. `[2, 2]`
// under SVG's default `butt` cap renders square dashes, so the lift connector's
// documented „gepunktet" channel was a second dashed line until the cap
// travelled with the dash (PR #620 review). Only a DOM can show that.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it } from 'vitest';

import { liftConnector } from '@/styles/paper';
import { PathOverlay } from './PathOverlay';
import type { Stroke } from './pathOverlay';

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

// Two pen-down stretches that do not meet, so exactly one lift is drawn.
const STROKES: Stroke[] = [
  [
    [0, 0],
    [1, 1],
  ],
  [
    [2, 1],
    [3, 0],
  ],
];

const draw = (detail: boolean) => {
  act(() =>
    root.render(
      <svg>
        <PathOverlay strokes={STROKES} unit={0.01} detail={detail} />
      </svg>,
    ),
  );
  return container;
};

const dashOf = (el: Element): number[] => (el.getAttribute('stroke-dasharray') ?? '').split(' ').map(Number);

it('draws the lift connector dotted — zero-length dashes under a round cap', () => {
  const lift = draw(true).querySelector('line');
  if (!lift) throw new Error('the overlay drew no lift connector');

  const dash = dashOf(lift);
  expect(dash[0]).toBe(0);
  expect(dash[1]).toBeGreaterThan(0);
  expect(lift.getAttribute('stroke-linecap')).toBe('round');
  expect(lift.getAttribute('stroke-linecap')).toBe(liftConnector.stroke.cap);
  expect(lift.getAttribute('stroke')).toBe(liftConnector.color);
});

it('leaves the pen strokes themselves solid and round-capped', () => {
  // The lift is a mark ABOUT the path; the path is the ink and keeps the cap a
  // pen leaves. A dashed stroke here would say the hand lifted where it did not.
  const paths = Array.from(draw(true).querySelectorAll('path'));
  expect(paths.length).toBe(STROKES.length);
  for (const path of paths) {
    expect(path.getAttribute('stroke-dasharray')).toBeNull();
    expect(path.getAttribute('stroke-linecap')).toBe('round');
  }
});

it('draws no lift at all without the detail layer', () => {
  expect(draw(false).querySelector('line')).toBeNull();
});
