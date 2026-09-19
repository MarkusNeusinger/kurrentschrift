// @vitest-environment jsdom
//
// The letter sketch is the one overlay surface a local database cannot show —
// it needs a hand, its occurrences and a rendered Laufform — so what it draws
// is pinned here instead of in the browser.
//
// The question is the Strichart-Regel's: the sketch puts TWO chains in one
// frame, and the reference one must not borrow a stroke style the legend has
// already taught as something else. `WERKBANK_COLORS.current` wears the Pfad's
// hue; if it also wore the engine's 4:3 dash, a reader who learned that
// signature on the word and join views would read "Engine" here.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it } from 'vitest';

import { layerDash } from '@/styles/paper';
import { AggregateSketch } from './AggregateSketch';
import { WERKBANK_COLORS } from './model';

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

const ANCHORS = [
  { x: 0, y: 0 },
  { x: 10, y: 12 },
  { x: 20, y: 0 },
];
const LAUFFORM = [
  [0, 1],
  [10, 13],
  [20, 1],
];

const render = (laufform: number[][]) => {
  act(() =>
    root.render(<AggregateSketch anchors={ANCHORS} glyphKey="a" occurrences={[]} laufform={laufform} />),
  );
  return Array.from(container.querySelectorAll('path'));
};

const dashOf = (el: Element): number[] => (el.getAttribute('stroke-dasharray') ?? '').split(' ').map(Number);

it('draws the Laufform reference dotted — zero-length dashes under a round cap', () => {
  const dashed = render(LAUFFORM).filter((p) => p.getAttribute('stroke-dasharray'));
  const reference = dashed.find((p) => p.getAttribute('stroke') === WERKBANK_COLORS.current);
  if (!reference) throw new Error('the sketch drew no Laufform reference');

  // BOTH halves, because either alone is a lie about the channel: `[2, 2]` with
  // the default `butt` cap renders square dashes, and a zero-length dash under
  // that cap renders nothing at all (PR #620 review).
  const dash = dashOf(reference);
  expect(dash[0]).toBe(0);
  expect(dash[1]).toBeGreaterThan(0);
  expect(reference.getAttribute('stroke-linecap')).toBe('round');
  expect(dash[0] / dash[1]).not.toBeCloseTo(layerDash.engine.dash[0] / layerDash.engine.dash[1], 5);
});

it('leaves the median solid, so the figure stays the figure', () => {
  const median = render(LAUFFORM).find((p) => p.getAttribute('stroke') === WERKBANK_COLORS.trace);
  if (!median) throw new Error('the sketch drew no median');
  expect(median.getAttribute('stroke-dasharray')).toBeNull();
});

it('draws no reference at all when there is no rendered Laufform', () => {
  // A one-point chain is not a chain: the caller may hand over anything the
  // aggregate row holds, and an empty reference must not become a stray mark.
  const dashed = render([]).filter((p) => p.getAttribute('stroke-dasharray'));
  expect(dashed.some((p) => p.getAttribute('stroke') === WERKBANK_COLORS.current)).toBe(false);
});
