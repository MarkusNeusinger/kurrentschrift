// @vitest-environment jsdom
//
// The ONE promise of the compact list that a type checker cannot keep: a
// collapsed row loads no picture. That is the whole point of V14 — the card
// wall it replaces was about ten thousand pixels of crops and SVG renders, and
// a list that quietly mounted the same faces behind a `display: none` would be
// the old page with a new toolbar.
//
// So the assertion is made against the DOM: no `<img>` while everything is
// collapsed, and the card mounted only once a row is opened. The card itself is
// stubbed — what is under test is WHEN it is mounted, not what it draws, and a
// real `CompareCard` would reach for the render endpoints.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { LetterList } from './LetterList';
import type { LetterRow } from './letterRows';

vi.mock('@/sections/admin/compare/CompareCard', () => ({
  // Stands in for the four faces — an image is exactly what must not be in the
  // document before the row is open.
  CompareCard: ({ glyphKey }: { glyphKey: string }) => <img alt={`faces ${glyphKey}`} src="/stub.png" />,
}));

const row = (glyphKey: string, letterGlyph: string, over: Partial<LetterRow> = {}): LetterRow => ({
  glyphKey,
  letterGlyph,
  locked: false,
  hasLaufform: false,
  occurrences: 3,
  scoreKnown: true,
  score: 81.4,
  quality: null,
  korbOpen: 0,
  ...over,
});

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  // React's own flag for „this environment drives the act queue"; without it
  // every `act` here writes a warning to stderr.
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.clearAllMocks();
});

function render(rows: LetterRow[]): void {
  act(() => {
    root.render(
      <LetterList
        rows={rows}
        sourceId="suetterlin-1922"
        cropCacheBust={0}
        reloadKey={0}
        overlay={false}
        aggregatesByKey={new Map()}
        instancesByKey={new Map()}
        statsHint="keine Statistik"
        occurrencesKnown
        onPick={() => {}}
      />,
    );
  });
}

const expander = (label: string): HTMLButtonElement => {
  const button = [...container.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === label);
  expect(button, label).toBeDefined();
  return button as HTMLButtonElement;
};

it('draws no image at all while every row is collapsed', () => {
  render([row('a', 'a'), row('b', 'b'), row('longs', 'ſ')]);
  expect(container.querySelectorAll('img')).toHaveLength(0);
  // The row still SAYS everything the card's header said — glyph, key, score,
  // occurrences — so nothing was traded away for the missing picture.
  expect(container.textContent).toContain('longs');
  expect(container.textContent).toContain('81.4');
  expect(container.textContent).toContain('3 Vorkommen');
});

it('mounts the faces only for the row that was opened', () => {
  render([row('a', 'a'), row('b', 'b')]);
  act(() => expander('Buchstabe a aufklappen').click());
  // Exactly one card, and it is the one that was asked for — opening a row must
  // not warm its neighbours.
  const images = [...container.querySelectorAll('img')];
  expect(images.map((img) => img.getAttribute('alt'))).toEqual(['faces a']);
});

it('names the letter in the expander and reports its state', () => {
  render([row('a', 'a')]);
  expect(expander('Buchstabe a aufklappen').getAttribute('aria-expanded')).toBe('false');
  act(() => expander('Buchstabe a aufklappen').click());
  expect(expander('Buchstabe a zuklappen').getAttribute('aria-expanded')).toBe('true');
});

it('says both whether a Laufform is there and whether it is missing', () => {
  render([row('a', 'a', { hasLaufform: true })]);
  expect(container.textContent).toContain('Laufform');
  expect(container.textContent).not.toContain('ohne Laufform');
  render([row('a', 'a', { hasLaufform: false })]);
  expect(container.textContent).toContain('ohne Laufform');
});

it('prints no number for a read that has not answered', () => {
  render([row('a', 'a', { occurrences: null, scoreKnown: false, score: null, korbOpen: null })]);
  expect(container.textContent).toContain('Vorkommen werden geladen');
  expect(container.textContent).not.toContain('0 Vorkommen');
  expect(container.textContent).not.toContain('im Korb');
  // „kein Score" is a claim about the FORM, so it waits for the read that can
  // support it — the same three states the card keeps apart.
  expect(container.textContent).not.toContain('kein Score');
});

it('says „kein Score" only once the score read has answered', () => {
  render([row('a', 'a', { scoreKnown: true, score: null })]);
  expect(container.textContent).toContain('kein Score');
});
