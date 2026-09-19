// @vitest-environment jsdom
//
// The guard, driven rather than reasoned about. `shortcuts.test.ts` pins the
// predicates; this pins that the LISTENER honours them — which is the half that
// actually ships the bug, because a guard that is never called is green in
// every unit test.
//
// Four things a reader would notice immediately if they broke: the binding
// fires on Alt+Shift+←/→, it does NOT fire while typing or inside the wizard, it
// does not fire with the Kurztasten off, and it never touches the browser's own
// Alt+← — the key the admin's whole linking doctrine rests on (P1-Q11 b).

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { SubjectNavProvider } from './SubjectNavContext';
import { useSubjectStepper } from './useSubjectStepper';

let host: HTMLDivElement;
let root: Root;
const steps: string[] = [];

function Detail({ prev = 'a', next = 'c' }: { prev?: string | null; next?: string | null }) {
  useSubjectStepper({ prev, next, onStep: (key) => steps.push(key) });
  return (
    <div>
      <button type="button">öffnen</button>
      <input aria-label="Proben filtern" />
      <div role="dialog">
        <button type="button">weiter</button>
      </div>
    </div>
  );
}

beforeEach(() => {
  steps.length = 0;
  host = document.createElement('div');
  document.body.appendChild(host);
  root = createRoot(host);
});

afterEach(() => {
  act(() => root.unmount());
  host.remove();
  vi.unstubAllGlobals();
});

const render = (node: React.ReactNode) => act(() => root.render(<SubjectNavProvider>{node}</SubjectNavProvider>));

/** A real key event on `target`, as the window listener sees it. Returns
 * whether anything called `preventDefault` — which is how „the browser keeps
 * this key" is actually asserted. */
function press(target: Element | Window, over: Partial<KeyboardEventInit>): boolean {
  const event = new KeyboardEvent('keydown', {
    key: 'ArrowRight',
    altKey: true,
    shiftKey: true,
    bubbles: true,
    cancelable: true,
    ...over,
  });
  act(() => void target.dispatchEvent(event));
  return event.defaultPrevented;
}

const control = () => host.querySelector('button')!;
const field = () => host.querySelector('input')!;
const inDialog = () => host.querySelector('[role="dialog"] button')!;

it('steps forward and back on Alt+Shift+←/→', () => {
  render(<Detail />);
  expect(press(control(), { key: 'ArrowRight' })).toBe(true);
  expect(press(control(), { key: 'ArrowLeft' })).toBe(true);
  expect(steps).toEqual(['c', 'a']);
});

it('stays silent while the reader is typing', () => {
  render(<Detail />);
  expect(press(field(), { key: 'ArrowRight' })).toBe(false);
  expect(steps).toEqual([]);
});

it('stays silent inside an open dialog — the wizard and the editor own their keys', () => {
  render(<Detail />);
  expect(press(inDialog(), { key: 'ArrowRight' })).toBe(false);
  expect(steps).toEqual([]);
});

it('never claims the browser’s own Alt+← / Alt+→', () => {
  render(<Detail />);
  // Without Shift the combination is Back/Forward, and `preventDefault` must
  // not be called on it — this is the reason the binding carries Shift at all.
  expect(press(control(), { key: 'ArrowLeft', shiftKey: false })).toBe(false);
  expect(press(control(), { key: 'ArrowRight', shiftKey: false })).toBe(false);
  expect(steps).toEqual([]);
});

it('does nothing at the ends of the order, and leaves the key alone there', () => {
  render(<Detail prev={null} next={null} />);
  expect(press(control(), { key: 'ArrowRight' })).toBe(false);
  expect(press(control(), { key: 'ArrowLeft' })).toBe(false);
  expect(steps).toEqual([]);
});

it('binds nothing at all with the Kurztasten switched off', () => {
  vi.stubGlobal('localStorage', { getItem: () => 'aus', setItem: () => {} });
  render(<Detail />);
  expect(press(control(), { key: 'ArrowRight' })).toBe(false);
  expect(steps).toEqual([]);
});

it('fires from <body> too — where focus sits right after a navigation', () => {
  // The reason the listener is on `window` and not on the view's container.
  render(<Detail />);
  expect(press(document.body, { key: 'ArrowRight' })).toBe(true);
  expect(steps).toEqual(['c']);
});

it('unbinds when the detail unmounts', () => {
  render(<Detail />);
  act(() => root.unmount());
  root = createRoot(host);
  expect(press(document.body, { key: 'ArrowRight' })).toBe(false);
  expect(steps).toEqual([]);
});
