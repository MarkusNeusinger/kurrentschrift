// @vitest-environment jsdom
//
// The coverage grid — ~90 cells the author reads daily, and the densest place
// in the workbench where a hover carried the answer.
//
// Each written cell is a button that opens that key's evidence. What it SAID
// was its glyph plus a 9.6 px count, and the sentence („b: 3 geschrieben, 6 im
// Plan · anklicken zeigt die Belege") lived in a tooltip. The count stays where
// it is, deliberately — lifting its type re-flows the grid and that is the
// author's call — but the sentence is the button's accessible NAME now, so a
// keyboard or screen reader gets it without a pointer (V25, §9.4).

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import type { EigenhandBestand } from '@/lib/api';
import { BestandView } from './BestandView';

// The setup panel reads the server on mount; this file is about the grid.
vi.mock('@/sections/admin/eigenhand/SetupPanel', () => ({
  SetupPanel: () => null,
}));

const BESTAND = {
  hand: 'wegwerf-suetterlin',
  style: 'suetterlin',
  strips: { total: 4, belegt: 2, unterwegs: 1, geplant: 1 },
  fassungen: { angenommen: 2, verworfen: 0, zurueckgezogen: 0 },
  sheets: { printed: 1, last: 'B01' },
  glyphs: {
    klein: {
      covered: 1,
      possible: 2,
      belege: 3,
      keys: [
        { key: 'a', belege: 3, planned: 6 },
        { key: 'b', belege: 0, planned: 6 },
      ],
    },
  },
  joins: { covered: 0, possible: 0, belege: 0, rows: [] },
  quoten: null,
  queue: [],
  redo: [],
  faellig: [],
  nib_median: null,
  nib_readings: 0,
} as unknown as EigenhandBestand;

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

function render(onShowBelege: (item: string) => void = () => {}): void {
  act(() => {
    root.render(
      <BestandView
        hand="wegwerf-suetterlin"
        bestand={BESTAND}
        labelOf={(item) => item}
        onShowBelege={onShowBelege}
      />,
    );
  });
}

const cells = (): HTMLButtonElement[] =>
  [...container.querySelectorAll('button')].filter((b) => (b.getAttribute('aria-label') ?? '').includes('im Plan'));

it('names a written cell with its own numbers and what a click does', () => {
  render();
  const written = cells();
  expect(written).toHaveLength(1);
  expect(written[0].getAttribute('aria-label')).toBe('a: 3 geschrieben, 6 im Plan · anklicken zeigt die Belege');
});

it('leaves an unwritten cell a plain cell — nothing to open, so no control', () => {
  render();
  // Two keys, one button: „b" has no evidence and stays a `div`.
  expect(container.querySelectorAll('button[aria-label]')).toHaveLength(1);
});

it('still NAMES the unwritten cell — the count is the point of the grid', () => {
  render();
  // The cell cannot be focused, so a tooltip would be its only carrier and
  // reach nobody. `role="img"` + `aria-label` puts the same sentence in the
  // accessibility tree without inventing a control that does nothing.
  const unwritten = container.querySelector('[role="img"]');
  expect(unwritten?.getAttribute('aria-label')).toBe('b: 0 geschrieben, 6 im Plan');
});

it('opens the key it names', () => {
  const opened: string[] = [];
  render((item) => opened.push(item));
  act(() => cells()[0].click());
  expect(opened).toEqual(['a']);
});

it('keeps the 9.6 px counter out of the accessible name instead of saying it twice', () => {
  render();
  // The number is decoration beside a name that already states it.
  const counters = [...container.querySelectorAll('[aria-hidden="true"]')].map((el) => el.textContent);
  expect(counters).toContain('3');
});
