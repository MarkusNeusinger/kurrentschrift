// @vitest-environment jsdom
//
// The legend swatch is where the Strichart-Regel is actually kept: a reader who
// cannot separate the Pfad's Ocker from the engine's Zinnober has the stroke
// style and the label, and both only work if the swatch really DRAWS the dash
// the layer is drawn with. That is a rendering question — the token file cannot
// answer it — so this file asks for a DOM.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it } from 'vitest';

import { layer, layerDash } from '@/styles/paper';
import { LayerDot } from './LayerDot';

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

const lineOf = (color: string, dash: readonly number[] | null) => {
  act(() => root.render(<LayerDot color={color} dash={dash} />));
  const line = container.querySelector('line');
  if (!line) throw new Error('the swatch drew no line');
  return line;
};

it('draws a solid line for a layer that has no dash', () => {
  const line = lineOf(layer.trace, layerDash.trace);
  expect(line.getAttribute('stroke')).toBe(layer.trace);
  expect(line.getAttribute('stroke-dasharray')).toBeNull();
});

it('draws the engine layer dashed, in the factors the token names', () => {
  const line = lineOf(layer.engine, layerDash.engine);
  expect(line.getAttribute('stroke')).toBe(layer.engine);
  // Factors times the swatch's line width — the same arithmetic the overlay
  // does with its own width, so the swatch and the crop cannot disagree.
  const dash = (line.getAttribute('stroke-dasharray') ?? '').split(' ').map(Number);
  expect(dash).toHaveLength(layerDash.engine.length);
  expect(dash[0] / dash[1]).toBeCloseTo(layerDash.engine[0] / layerDash.engine[1], 5);
});

it('never falls back to a colour-only swatch', () => {
  // A dot would mean the legend carries the distinction in hue alone, which is
  // exactly what the two colliding hues cannot do.
  act(() => root.render(<LayerDot color={layer.path} dash={layerDash.path} />));
  expect(container.querySelector('svg')).not.toBeNull();
});
