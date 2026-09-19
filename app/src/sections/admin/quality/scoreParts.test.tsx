// @vitest-environment jsdom
//
// The non-hover rule (V25, design-system.md §9.4) in the one place it cost the
// most: the score breakdown of a work-list row.
//
// Every category used to be a `<Typography tabIndex={0}>` with its own tooltip
// — six ringless tab stops per row and, on a list page of twelve rows, 72 stops
// that say nothing when reached and nothing at all to a finger. What the DOM
// must now show: the numbers are still all there as TEXT, nothing but the one
// help button is focusable, and that button has a name.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it } from 'vitest';

import type { QualityData } from '@/lib/api';
import { ScoreBreakdown, ScoreBreakdownInline, ScoreChip } from './scoreParts';

const quality = (over: Partial<QualityData> = {}): QualityData =>
  ({
    score: 81.4,
    components: {
      smoothness: 0.21,
      verticality: 0.12,
      corner: 0.03,
      collinearity: 0.0,
      retrace: 0.18,
      coverage: 0.99,
    },
    ...over,
  }) as QualityData;

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

/** Everything a Tab press could land on, inside the rendered fragment. */
const focusables = (): HTMLElement[] => [
  ...container.querySelectorAll<HTMLElement>('button, a[href], input, [tabindex]:not([tabindex="-1"])'),
];

it('keeps every per-category number as visible text', () => {
  act(() => root.render(<ScoreBreakdownInline quality={quality()} />));
  const text = container.textContent ?? '';
  // Worst first, as the bar chart orders them; the two below the epsilon drop.
  expect(text).toContain('Deckungslücke');
  expect(text).toContain('0.99');
  expect(text).toContain('Glätte');
  expect(text).toContain('0.21');
  expect(text).toContain('Doppelzug');
  expect(text).toContain('0.18');
});

it('offers exactly ONE focusable affordance per row, and it is a named button', () => {
  act(() => root.render(<ScoreBreakdownInline quality={quality()} />));
  const stops = focusables();
  expect(stops).toHaveLength(1);
  expect(stops[0].tagName).toBe('BUTTON');
  expect(stops[0].getAttribute('aria-label')).toBe('Score und Abzüge erklären');
  // The old shape: a non-interactive span carrying a bare tabIndex.
  expect(container.querySelector('span[tabindex]')).toBeNull();
});

it('puts the category explanations behind that one button, reachable by click', () => {
  act(() => root.render(<ScoreBreakdownInline quality={quality()} />));
  expect(document.body.textContent).not.toContain('Bögen ohne Zacken');
  act(() => focusables()[0].click());
  // A click, not a hover — which is what makes it work on the tablet.
  const open = document.body.textContent ?? '';
  expect(open).toContain('Bögen ohne Zacken');
  expect(open).toContain('Abstriche wirklich senkrecht');
  // And the caveat that used to hang on the score chip itself.
  expect(open).toContain('Gestempelt bei der letzten Ableitung');
});

it('says so plainly when the metric stores no categories, instead of rendering nothing', () => {
  act(() => root.render(<ScoreBreakdownInline quality={quality({ components: null })} />));
  expect(container.textContent).toContain('Keine Abzüge nach Kategorie');
  expect(focusables()).toHaveLength(1);
});

it('gives the bar chart the same single help and no tab stop per label', () => {
  act(() => root.render(<ScoreBreakdown quality={quality()} />));
  const stops = focusables();
  expect(stops).toHaveLength(1);
  expect(stops[0].tagName).toBe('BUTTON');
  expect(container.querySelector('[tabindex="0"]:not(button)')).toBeNull();
});

it('leaves the score chip a plain, unfocusable label', () => {
  act(() => root.render(<ScoreChip score={81.4} />));
  expect(container.textContent).toContain('81.4');
  expect(focusables()).toHaveLength(0);
});
