// @vitest-environment jsdom
//
// The provider's one real rule: it keeps ONE order PER KIND.
//
// The bug this pins is the walk the workbench exists for. A letter detail links
// to „Alle Übergänge"; that overview's matrix publishes a JOIN order; the reader
// presses Back. With a single slot the letter order was gone by then and the
// stepper quietly walked the alphabet again — on the very button the admin's
// linking doctrine rests on.

import { act, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it } from 'vitest';

import { SubjectNavProvider } from './SubjectNavContext';
import { usePublishSubjectOrder, useSubjectNav, type SubjectOrders } from './subjectNav';

let host: HTMLDivElement;
let root: Root;
let seen: SubjectOrders = {};

function Publisher({ kind, keys, caption }: { kind: 'letter' | 'join'; keys: string[]; caption: string }) {
  usePublishSubjectOrder(kind, keys, caption);
  return null;
}

function Probe() {
  const { orders } = useSubjectNav();
  // In an effect, not during render: reading is what this does, and a render
  // that writes outside itself is the one thing React forbids.
  useEffect(() => {
    seen = orders;
  });
  return null;
}

beforeEach(() => {
  seen = {};
  host = document.createElement('div');
  document.body.appendChild(host);
  root = createRoot(host);
});

afterEach(() => {
  act(() => root.unmount());
  host.remove();
});

const render = (node: React.ReactNode) =>
  act(() =>
    root.render(
      <SubjectNavProvider>
        {node}
        <Probe />
      </SubjectNavProvider>,
    ),
  );

it('keeps the letter order while the reader is over in the joins view', () => {
  render(<Publisher kind="letter" keys={['n', 'a', 'e']} caption="Reihenfolge: Schlechteste zuerst" />);
  expect(seen.letter?.keys).toEqual(['n', 'a', 'e']);

  // „Alle Übergänge" — the matrix behind it publishes a join order.
  render(<Publisher kind="join" keys={['a→b', 'b→c']} caption="Reihenfolge: Registerfolge" />);
  expect(seen.join?.keys).toEqual(['a→b', 'b→c']);
  // …and Back to the letter detail still finds the worst-first order standing.
  expect(seen.letter?.keys).toEqual(['n', 'a', 'e']);
});

it('replaces an order of the same kind, because a filter click is a new order', () => {
  render(<Publisher kind="letter" keys={['a', 'b', 'c']} caption="Reihenfolge: Registerfolge" />);
  render(<Publisher kind="letter" keys={['c', 'a']} caption="Reihenfolge: Schlechteste zuerst · gefiltert" />);
  expect(seen.letter).toEqual({
    kind: 'letter',
    keys: ['c', 'a'],
    caption: 'Reihenfolge: Schlechteste zuerst · gefiltert',
  });
});

it('hands back the same object when an overview republishes an unchanged order', () => {
  // The publisher's effect runs on every rebuild of its rows; a fresh object
  // each time would re-render every consumer and feed the effect back to itself.
  render(<Publisher kind="letter" keys={['a', 'b']} caption="Reihenfolge: Registerfolge" />);
  const first = seen.letter;
  render(<Publisher kind="letter" keys={['a', 'b']} caption="Reihenfolge: Registerfolge" />);
  expect(seen.letter).toBe(first);
});
