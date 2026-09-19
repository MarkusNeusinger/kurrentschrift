// @vitest-environment jsdom
//
// What `lib/roving.test.ts` cannot reach: the promises the hook makes about the
// DOM. One tab stop for the whole list, focus that walks with the arrows, and —
// the one that a type checker and an arithmetic test would both wave through —
// focus that does NOT end up on `<body>` when the row it stood on is filtered
// away. That was the actual failure mode of every hand-rolled roving list: the
// reader presses a filter chip and the next Tab restarts at the top of the
// document.
//
// `createRoot` + `act` directly, no @testing-library (the repo has none) — the
// pattern of `letters/LaufformApplyDialog.test.tsx`.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { ROVING_SKIP, useRovingList } from './useRovingList';

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
  host = document.createElement('div');
  document.body.appendChild(host);
  root = createRoot(host);
  // jsdom gives every element `offsetParent === null`, which the hook reads as
  // „not rendered". Real browsers do not; the property is simply unimplemented
  // here, so it is taught to answer the way a laid-out element would.
  vi.spyOn(HTMLElement.prototype, 'offsetParent', 'get').mockReturnValue(document.body);
});

afterEach(() => {
  act(() => root.unmount());
  host.remove();
  vi.restoreAllMocks();
});

/** A list of rows, each with an „aufklappen" and an „öffnen" button — the shape
 * of the three work lists. `body` mimics an expanded row. */
function List({ keys, body = false }: { keys: string[]; body?: boolean }) {
  const roving = useRovingList();
  return (
    <div {...roving.containerProps}>
      {keys.map((key) => (
        <div key={key} {...roving.rowProps(key)}>
          <button type="button">{`${key} aufklappen`}</button>
          <button type="button">{`${key} öffnen`}</button>
          {body && (
            <div {...ROVING_SKIP}>
              <button type="button">{`${key} im Körper`}</button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function Grid({ keys }: { keys: string[] }) {
  const roving = useRovingList({ orientation: 'horizontal', label: 'Paar-Zellen' });
  return (
    <div {...roving.containerProps}>
      {keys.map((key) => (
        <button type="button" key={key} {...roving.rowProps(key)}>
          {key}
        </button>
      ))}
    </div>
  );
}

const buttons = () => [...host.querySelectorAll('button')];
const stops = () => buttons().filter((b) => b.tabIndex === 0);
const active = () => (document.activeElement as HTMLElement | null)?.textContent ?? null;

/** A real key event, bubbling to the container's React handler. */
function press(key: string, over: Partial<KeyboardEventInit> = {}) {
  act(() => {
    document.activeElement?.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, ...over }));
  });
}

const render = (node: React.ReactNode) => act(() => root.render(node));

it('makes the whole list ONE tab stop, at the first row', () => {
  render(<List keys={['a', 'b', 'c']} />);
  expect(buttons()).toHaveLength(6);
  expect(stops().map((b) => b.textContent)).toEqual(['a aufklappen']);
});

it('walks the rows with Up/Down and the row with Left/Right', () => {
  render(<List keys={['a', 'b', 'c']} />);
  act(() => buttons()[0].focus());
  press('ArrowDown');
  expect(active()).toBe('b aufklappen');
  press('ArrowRight');
  expect(active()).toBe('b öffnen');
  // The column is kept across rows.
  press('ArrowDown');
  expect(active()).toBe('c öffnen');
  press('ArrowUp');
  expect(active()).toBe('b öffnen');
});

it('moves the ONE tab stop with the focus', () => {
  render(<List keys={['a', 'b', 'c']} />);
  act(() => buttons()[0].focus());
  press('ArrowDown');
  expect(stops().map((b) => b.textContent)).toEqual(['b aufklappen']);
});

it('jumps to the ends with Home/End and stops there', () => {
  render(<List keys={['a', 'b', 'c']} />);
  act(() => buttons()[0].focus());
  press('End');
  expect(active()).toBe('c öffnen');
  press('ArrowDown');
  expect(active()).toBe('c öffnen');
  press('Home');
  expect(active()).toBe('a aufklappen');
  press('ArrowUp');
  expect(active()).toBe('a aufklappen');
});

it('leaves Enter, Space and a modified arrow to whoever owns them', () => {
  render(<List keys={['a', 'b']} />);
  act(() => buttons()[0].focus());
  press('Enter');
  press(' ');
  expect(active()).toBe('a aufklappen');
  // Alt+Shift+→ is the Subjekt-Stepper's, not this list's.
  press('ArrowDown', { altKey: true, shiftKey: true });
  expect(active()).toBe('a aufklappen');
});

it('keeps the stop on the same ROW across a re-render that re-orders the list', () => {
  render(<List keys={['a', 'b', 'c']} />);
  act(() => buttons()[0].focus());
  press('ArrowDown');
  expect(active()).toBe('b aufklappen');
  render(<List keys={['c', 'b', 'a']} />);
  // Keyed on the subject, not on the index — „b" is still the stop although it
  // did not move and the rows around it did.
  expect(stops().map((b) => b.textContent)).toEqual(['b aufklappen']);
});

it('never loses focus to <body> when the focused row is filtered away', () => {
  render(<List keys={['a', 'b', 'c']} />);
  act(() => buttons()[0].focus());
  press('ArrowDown');
  expect(active()).toBe('b aufklappen');
  // „b" no longer matches the filter: the stop goes to whatever now stands at
  // its index, and the focus goes with it.
  render(<List keys={['a', 'c']} />);
  expect(document.activeElement).not.toBe(document.body);
  expect(active()).toBe('c aufklappen');
});

it('lands on the last row when the list shrinks past the remembered index', () => {
  render(<List keys={['a', 'b', 'c']} />);
  act(() => buttons()[0].focus());
  press('End');
  expect(active()).toBe('c öffnen');
  render(<List keys={['a'] } />);
  expect(active()).toBe('a öffnen');
});

it('leaves an expanded row’s body out of the roving, as its own tab stops', () => {
  render(<List keys={['a', 'b']} body />);
  // Six managed controls, two body buttons — and the body keeps the browser's
  // default tabIndex rather than being taken off the tab order.
  const body = buttons().filter((b) => b.textContent?.includes('im Körper'));
  expect(body).toHaveLength(2);
  for (const button of body) expect(button.tabIndex).toBe(0);
  // The list itself is still exactly one stop.
  expect(stops().filter((b) => !b.textContent?.includes('im Körper'))).toHaveLength(1);
});

it('names a wrapping grid as a toolbar, so a screen reader hands the arrows on', () => {
  // One tab stop without a composite role leaves a screen reader in Lesemodus:
  // it keeps the arrow keys for its own cursor, and the rows this hook took out
  // of the Tab order are then reachable by nothing at all.
  render(<Grid keys={['ab', 'ac']} />);
  const container = host.querySelector('[role="toolbar"]');
  expect(container).not.toBeNull();
  expect(container!.getAttribute('aria-orientation')).toBe('horizontal');
  expect(container!.getAttribute('aria-label')).toBe('Paar-Zellen');
});

it('leaves a work list role-less — its rows are subjects, not a flat control set', () => {
  // The deliberate other half of the rule above (§9.5): a `toolbar` would flatten
  // three controls per subject into one strip, and the honest shape — a `grid` of
  // `row`/`gridcell` — is a restructure of three components. Every control here
  // already carries its subject in its own accessible name.
  render(<List keys={['a', 'b']} />);
  expect(host.querySelector('[role]')).toBeNull();
});

it('walks a wrapping grid sideways only', () => {
  render(<Grid keys={['ab', 'ac', 'ad']} />);
  expect(stops().map((b) => b.textContent)).toEqual(['ab']);
  act(() => buttons()[0].focus());
  press('ArrowRight');
  expect(active()).toBe('ac');
  // No stable column count, so Down is not this grid's key to take.
  press('ArrowDown');
  expect(active()).toBe('ac');
  press('End');
  expect(active()).toBe('ad');
});

it('does not steal focus back when the reader has moved elsewhere', () => {
  const outside = document.createElement('button');
  outside.textContent = 'Werkzeugleiste';
  document.body.appendChild(outside);
  render(<List keys={['a', 'b', 'c']} />);
  act(() => buttons()[0].focus());
  act(() => outside.focus());
  render(<List keys={['b', 'c']} />);
  expect(document.activeElement).toBe(outside);
  outside.remove();
});

it('does not steal focus back after a blur that named no new target either', () => {
  // The leak the direct case above does not cover: a click on plain page chrome
  // blurs to `<body>` WITHOUT naming a `relatedTarget` — the same signature a
  // removed element leaves behind — so the list's claim on the focus survives
  // it. Only where the focus actually stands decides.
  const outside = document.createElement('button');
  outside.textContent = 'Werkzeugleiste';
  document.body.appendChild(outside);
  render(<List keys={['a', 'b', 'c']} />);
  act(() => buttons()[0].focus());
  act(() => (document.activeElement as HTMLElement).blur());
  act(() => outside.focus());
  // …and only NOW does a filter click take the remembered row away.
  render(<List keys={['b', 'c']} />);
  expect(document.activeElement).toBe(outside);
  outside.remove();
});
