// @vitest-environment jsdom
//
// WHY a toolbar button is unavailable is the state the author acts on — unlock
// first, or draw a Weg in the wizard first. It used to live in a tooltip on the
// `<span>` that wraps a DISABLED control, which is the worst of both worlds: a
// disabled button takes no focus, so the span's `onFocus` never fires, and a
// finger has no hover at all. The reason is a line in the toolbar now (V25).

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it } from 'vitest';

import { ChartToolbar } from './ChartToolbar';

let container: HTMLDivElement;
let root: Root;

const noop = () => {};

function render(over: Partial<Parameters<typeof ChartToolbar>[0]> = {}): void {
  act(() => {
    root.render(
      <ChartToolbar
        mode="pan"
        onModeChange={noop}
        activeGlyph="a"
        activeLocked={false}
        hasActiveBbox
        activeHasCanonical
        zoom={1}
        onZoomChange={noop}
        onZoomOut={noop}
        onZoomIn={noop}
        onToggleLock={noop}
        onDelete={noop}
        onOpenWizard={noop}
        onOpenDiagnose={noop}
        onOpenRederiveAll={noop}
        {...over}
      />,
    );
  });
}

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

it('says nothing extra while everything is available', () => {
  render();
  expect(container.textContent).not.toContain('gesperrt');
  expect(container.textContent).not.toContain('Noch kein Canonical');
});

it('names the lock as visible text, with the glyph it is about', () => {
  render({ activeLocked: true });
  expect(container.textContent).toContain('a ist gesperrt — erst entsperren');
});

it('names the missing canonical as visible text', () => {
  render({ activeHasCanonical: false });
  expect(container.textContent).toContain('Noch kein Canonical');
});

it('names only the FIRST obstacle — a glyph without a bbox has no canonical either', () => {
  render({ hasActiveBbox: false, activeHasCanonical: false });
  expect(container.textContent).toContain('Glyph mit Bbox wählen');
  expect(container.textContent).not.toContain('Noch kein Canonical');
});

it('names BOTH where they gate different buttons — the lock does not block Diagnose', () => {
  render({ activeLocked: true, activeHasCanonical: false });
  expect(container.textContent).toContain('a ist gesperrt — erst entsperren');
  expect(container.textContent).toContain('Noch kein Canonical');
});

it('claims nothing while no glyph is active at all', () => {
  render({ activeGlyph: null, hasActiveBbox: false, activeHasCanonical: false });
  expect(container.textContent).toContain('kein aktiver Glyph');
  expect(container.textContent).not.toContain('Glyph mit Bbox wählen');
});
