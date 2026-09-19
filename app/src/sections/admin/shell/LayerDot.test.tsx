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

import { layer, layerDash, role, roleDash, type StrokeStyle } from '@/styles/paper';
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

const lineOf = (color: string, style: StrokeStyle) => {
  act(() => root.render(<LayerDot color={color} style={style} />));
  const line = container.querySelector('line');
  if (!line) throw new Error('the swatch drew no line');
  return line;
};

const dashOf = (el: Element): number[] => (el.getAttribute('stroke-dasharray') ?? '').split(' ').map(Number);

it('draws a solid line for a layer that has no dash', () => {
  const line = lineOf(layer.trace, layerDash.trace);
  expect(line.getAttribute('stroke')).toBe(layer.trace);
  expect(line.getAttribute('stroke-dasharray')).toBeNull();
  expect(line.getAttribute('stroke-linecap')).toBe(layerDash.trace.cap);
});

it('draws the engine layer dashed, in the factors AND the cap the token names', () => {
  const line = lineOf(layer.engine, layerDash.engine);
  expect(line.getAttribute('stroke')).toBe(layer.engine);
  // Factors times the swatch's line width — the same arithmetic the overlay
  // does with its own width, so the swatch and the crop cannot disagree.
  const dash = dashOf(line);
  expect(dash).toHaveLength(layerDash.engine.dash.length);
  expect(dash[0] / dash[1]).toBeCloseTo(layerDash.engine.dash[0] / layerDash.engine.dash[1], 5);
  // A dash needs the butt cap: round caps grow every dash by its own width at
  // both ends, which closes the gaps the dash exists for.
  expect(line.getAttribute('stroke-linecap')).toBe('butt');
});

it('draws a dotted role as real dots — zero-length dashes under a round cap', () => {
  // The finding this pins (PR #620 review): `[2, 2]` with the SVG default cap
  // renders SQUARE dashes, so a swatch that carried only the dash showed the
  // „gepunktet" channel as a second dashed one.
  const line = lineOf(role.eigenhand, roleDash.eigenhand);
  const dash = dashOf(line);
  expect(dash[0]).toBe(0);
  expect(dash[1]).toBeGreaterThan(0);
  expect(line.getAttribute('stroke-linecap')).toBe('round');
});

it('never falls back to a colour-only swatch', () => {
  // A dot would mean the legend carries the distinction in hue alone, which is
  // exactly what the two colliding hues cannot do.
  act(() => root.render(<LayerDot color={layer.path} style={layerDash.path} />));
  expect(container.querySelector('svg')).not.toBeNull();
});
