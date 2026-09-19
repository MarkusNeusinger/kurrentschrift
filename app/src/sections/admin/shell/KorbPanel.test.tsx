// @vitest-environment jsdom
//
// The Auftragskorb's one opener. It used to be a `<p role="link" tabIndex={0}>`
// with a hand-rolled Enter/Space handler — a tab stop that showed NOTHING when
// reached, because the focus ring lives on `ButtonBase` and `MuiTypography` has
// no focus-visible rule of its own (V24 „jeder Öffner", §9.1).
//
// What the DOM has to say now: the opener is a real `<button>` carrying the
// task's own words, a row that points nowhere offers no control at all, and no
// element is faking interactivity with a bare `tabIndex`.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { AdminCtx, type AdminState } from '@/context/adminState';
import { listWorkItems } from '@/lib/api';
import type { WorkItemOut } from '@/lib/api';
import { KorbPanel } from './KorbPanel';

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  listWorkItems: vi.fn(),
}));

const item = (over: Partial<WorkItemOut>): WorkItemOut =>
  ({
    id: 1,
    source_id: 'suetterlin-1922',
    kind: 'letter',
    status: 'open',
    glyph_key: 'a',
    left_key: null,
    right_key: null,
    word: null,
    specimen_id: null,
    note: 'Der Bogen des a schließt zu früh.',
    understanding: null,
    reproduced: null,
    stage: null,
    resolution: null,
    created_at: null,
    closed_at: null,
    ...over,
  }) as WorkItemOut;

// The panel reads exactly one field of the admin state: the active hand, which
// it appends to every link it offers.
const adminState = { handId: 'mn-suetterlin' } as unknown as AdminState;

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

async function render(rows: WorkItemOut[]): Promise<void> {
  vi.mocked(listWorkItems).mockResolvedValue(rows);
  await act(async () => {
    root.render(
      <MemoryRouter>
        <AdminCtx.Provider value={adminState}>
          <KorbPanel sourceId="suetterlin-1922" refreshKey={0} />
        </AdminCtx.Provider>
      </MemoryRouter>,
    );
  });
}

const named = (name: string): HTMLButtonElement | undefined =>
  [...container.querySelectorAll('button')].find((b) => (b.textContent ?? '').includes(name));

it('opens a targeted task through a real button that carries the task words', async () => {
  await render([item({})]);
  const opener = named('Buchstabe a');
  expect(opener).toBeDefined();
  expect(opener?.tagName).toBe('BUTTON');
  // The retired shape: a paragraph pretending to be a link.
  expect(container.querySelector('[role="link"]')).toBeNull();
});

it('offers no opener at all for a row that points nowhere', async () => {
  await render([item({ kind: 'note', glyph_key: null, note: 'Wording im Kopf stimmt nicht.' })]);
  expect(named('Wording im Kopf')).toBeUndefined();
  // The text is still there — only the affordance is gone.
  expect(container.textContent).toContain('Wording im Kopf');
});

it('fakes interactivity nowhere: no bare tabIndex outside a real control', async () => {
  await render([item({}), item({ id: 2, kind: 'pair', glyph_key: null, left_key: 'd', right_key: 'a' })]);
  // MUI's own selects are `<div role="combobox" tabindex="0">` — a real
  // control announced as one. What this forbids is an element that is neither:
  // a `<p>` or `<span>` made focusable so a hover could be reached by keyboard.
  const faked = [...container.querySelectorAll<HTMLElement>('[tabindex="0"]')].filter(
    (el) => !['BUTTON', 'A', 'INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName) && !el.getAttribute('role'),
  );
  expect(faked.map((el) => el.outerHTML.slice(0, 80))).toEqual([]);
});
