// @vitest-environment jsdom
//
// The ONE promise of the compact list that a type checker cannot keep: a
// collapsed row loads no picture. That is the whole point of V14 — the card
// wall it replaces stacked 169 Wortproben at two faces of 220 px each, and a
// list that quietly mounted the same faces behind a `display: none` would be
// the old page with a new toolbar.
//
// So the assertion is made against the DOM: no `<img>` while everything is
// collapsed, and the card mounted only once a row is opened. The card itself is
// stubbed — what is under test is WHEN it is mounted, not what it draws, and a
// real `WordCard` would reach for the crop and the render endpoints.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import type { WordSampleOut } from '@/lib/api';

import { WordList } from './WordList';
import type { WordRow } from './wordRows';

vi.mock('@/sections/admin/compare/WordCard', () => ({
  // Stands in for the two faces — an image is exactly what must not be in the
  // document before the row is open.
  WordCard: ({ sample }: { sample: WordSampleOut }) => <img alt={`faces ${sample.id}`} src="/stub.png" />,
  ScoreChip: ({ score }: { score: { loss: number } }) => <span>{`Loss ${score.loss.toFixed(2)}`}</span>,
}));

const sample = (id: string, word: string, over: Partial<WordSampleOut> = {}): WordSampleOut => ({
  id,
  word,
  kind: 'word',
  sample_set: null,
  width: 400,
  height: 120,
  baseline_y: 90,
  midband_y: 50,
  ...over,
});

const row = (id: string, word: string, over: Partial<WordRow> = {}): WordRow => ({
  sampleId: id,
  word,
  foreign: false,
  foreignSet: null,
  status: 'open',
  traces: 0,
  korbOpen: 0,
  loss: null,
  scoreFailed: false,
  sample: sample(id, word),
  score: null,
  traced: null,
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

function render(rows: WordRow[]): void {
  act(() => {
    root.render(
      <WordList rows={rows} sourceId="suetterlin-1922" cropCacheBust={0} overlay={false} onPick={() => {}} />,
    );
  });
}

const expander = (label: string): HTMLButtonElement => {
  const button = [...container.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === label);
  expect(button, label).toBeDefined();
  return button as HTMLButtonElement;
};

it('draws no image at all while every row is collapsed', () => {
  render([row('s1', 'lesen'), row('s2', 'das'), row('s3', 'denen')]);
  expect(container.querySelectorAll('img')).toHaveLength(0);
  // The row still SAYS what the card's header said — word, specimen, state —
  // so nothing was traded away for the missing picture.
  expect(container.textContent).toContain('lesen');
  expect(container.textContent).toContain('s1');
});

it('leaves out a specimen id that only repeats the word', () => {
  // Most of the 1922 sidecar's ids ARE the word, and „unter" written under
  // „unter" reads as a rendering fault rather than as a second fact.
  render([row('unter', 'unter')]);
  expect(container.textContent?.match(/unter/g)).toHaveLength(1);
});

it('mounts the faces only for the row that was opened', () => {
  render([row('s1', 'lesen'), row('s2', 'das')]);
  act(() => expander('Wortprobe lesen aufklappen').click());
  // Exactly one card, and it is the one that was asked for — opening a row
  // must not warm its neighbours.
  expect([...container.querySelectorAll('img')].map((img) => img.getAttribute('alt'))).toEqual(['faces s1']);
});

it('names the Wortprobe in the expander and reports its state', () => {
  render([row('s1', 'lesen')]);
  expect(expander('Wortprobe lesen aufklappen').getAttribute('aria-expanded')).toBe('false');
  act(() => expander('Wortprobe lesen aufklappen').click());
  expect(expander('Wortprobe lesen zuklappen').getAttribute('aria-expanded')).toBe('true');
});

it('says „n Bahnen" and the Nachfahr-Status as two separate facts', () => {
  render([row('s1', 'lesen', { traces: 1, status: 'open' })]);
  // A harvested fit IS a stored Bahn, and it is not the author's pen work —
  // one chip may not answer for the other.
  expect(container.textContent).toContain('1 Bahn');
  expect(container.textContent).toContain('Offen');
  render([row('s1', 'lesen', { traces: 1, status: 'authored' })]);
  expect(container.textContent).toContain('von Hand ✓');
});

it('prints no number for a read that has not answered', () => {
  render([row('s1', 'lesen', { korbOpen: null })]);
  expect(container.textContent).not.toContain('im Korb');
  // And no Loss for a Wortprobe nobody measured — „Loss 0.00" would be an
  // excellent mark invented out of a missing sweep.
  expect(container.textContent).not.toContain('Loss');
});

it('announces a foreign writer rather than folding the plate in', () => {
  render([row('s9', 'du', { foreign: true, foreignSet: 'abb22', sample: sample('s9', 'du', { sample_set: 'abb22' }) })]);
  expect(container.textContent).toContain('Andere Hand');
  expect(container.textContent).toContain('abb22');
});
