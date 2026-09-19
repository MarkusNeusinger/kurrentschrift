// @vitest-environment jsdom
//
// The same promise the Buchstaben and the Wörter lists make, for the matrix:
// the default cell says what it knows IN WORDS and composes nothing. A grid of
// ~60 cells that quietly asked `/write/word` for each of them would be the old
// card wall with a counter printed on top — and the counters exist precisely so
// the page can be read without the pictures.
//
// The composed face is stubbed: what is under test is WHEN it is mounted, not
// what it draws.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { PairCellGrid } from './PairCells';
import type { PairRow } from './pairRows';

vi.mock('@/components/WrittenWord', () => ({
  WrittenWord: ({ text }: { text: string }) => <img alt={`written ${text}`} src="/stub.png" />,
}));

// The grid's own lazy gate would never open in jsdom (no IntersectionObserver
// layout), so the hook reports „in view" and the test really measures the
// component's decision rather than the observer's.
vi.mock('@/hooks/useInView', () => ({
  useInView: () => [{ current: null }, true],
}));

const row = (text: string, over: Partial<PairRow> = {}): PairRow => ({
  text,
  leftKey: text[0],
  rightKey: text[1],
  plate: 0,
  override: 'none',
  korbOpen: 0,
  ...over,
});

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
  vi.clearAllMocks();
});

function render(rows: PairRow[], view: 'liste' | 'galerie' = 'liste'): void {
  act(() => {
    root.render(<PairCellGrid rows={rows} sourceId="suetterlin-1922" view={view} onPick={() => {}} />);
  });
}

it('composes nothing in the default view, and everything in the gallery', () => {
  render([row('ab'), row('ac')]);
  expect(container.querySelectorAll('img')).toHaveLength(0);
  render([row('ab'), row('ac')], 'galerie');
  expect([...container.querySelectorAll('img')].map((img) => img.getAttribute('alt'))).toEqual([
    'written ab',
    'written ac',
  ]);
});

it('says every counter in words, never in a colour alone', () => {
  render([row('ab', { plate: 3, override: 'approved', korbOpen: 2 })]);
  expect(container.textContent).toContain('3 Vorkommen');
  expect(container.textContent).toContain('Override');
  expect(container.textContent).toContain('2 im Korb');
});

it('keeps „kein Override" apart from „nicht gelesen"', () => {
  render([row('ab')]);
  expect(container.textContent).toContain('generiert');
  // An unanswered read says nothing at all here — the grid says it once,
  // above itself, rather than putting „generiert" on 60 cells it cannot back.
  render([row('ab', { override: null, plate: null, korbOpen: null })]);
  expect(container.textContent).not.toContain('generiert');
  expect(container.textContent).not.toContain('Vorkommen');
});

it('names the combination AND its counters in the cell that opens it', () => {
  // An `aria-label` REPLACES the content as the accessible name, so it has to
  // carry the counters too — they are the whole point of „Zähler statt Farbe",
  // and a label that said only „Verbindung ab öffnen" would hand a
  // screen-reader user exactly the empty cell this change removed.
  render([row('ab', { plate: 3, override: 'approved', korbOpen: 2 })]);
  const label = container.querySelector('button')?.getAttribute('aria-label') ?? '';
  expect(label).toContain('Verbindung ab öffnen');
  expect(label).toContain('3 Vorkommen');
  expect(label).toContain('Override');
  expect(label).toContain('2 im Korb');
  // Without the ⚑: the flag is a second VISUAL channel and reads as „schwarze
  // Flagge" out loud.
  expect(label).not.toContain('⚑');
});

it('leaves an unanswered read out of the accessible name too', () => {
  render([row('ab', { plate: null, override: null, korbOpen: null })]);
  const label = container.querySelector('button')?.getAttribute('aria-label') ?? '';
  expect(label).toBe('Verbindung ab öffnen');
});

it('leaves a ligature cell closed and says why', () => {
  // „ch" is ONE glyph: no join to open, and no counters to print.
  render([row('ch', { leftKey: null, rightKey: null, plate: null, override: null, korbOpen: null })]);
  expect(container.querySelectorAll('button')).toHaveLength(0);
  expect(container.textContent).toContain('eine Glyphe');
});
