// @vitest-environment jsdom
//
// The retired chart-editor address must keep its subject. Before, it sent
// every `/admin/edit/<key>` to the bare Buchstaben overview, so a bookmark to
// one letter opened the list of all of them.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import LegacyEditRedirect from './LegacyEditRedirect';

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
});

/** Where the redirect landed, as the router sees it. */
function Landed() {
  const location = useLocation();
  return <output>{`${location.pathname}${location.search}`}</output>;
}

function land(path: string): string {
  act(() => {
    root.render(
      // Keyed: a MemoryRouter reads `initialEntries` once, so a second
      // render into the same root would keep the first history.
      <MemoryRouter key={path} initialEntries={[path]}>
        <Routes>
          <Route path="/admin/edit/:glyphKey" element={<LegacyEditRedirect />} />
          <Route path="/admin/buchstaben" element={<Landed />} />
        </Routes>
      </MemoryRouter>,
    );
  });
  return container.querySelector('output')?.textContent ?? '';
}

describe('the retired /admin/edit/:glyphKey address', () => {
  it('opens the letter it names, not the overview', () => {
    expect(land('/admin/edit/a')).toBe('/admin/buchstaben?g=a');
    expect(land('/admin/edit/longs')).toBe('/admin/buchstaben?g=longs');
  });

  it('passes an unknown key on and leaves the verdict to the view', () => {
    // A positional key from before the R2 removal. The redirect does not judge
    // it: `readLetterFocus` sends a key the registry does not know to the
    // overview, one rule in one place.
    expect(land('/admin/edit/a-medial')).toBe('/admin/buchstaben?g=a-medial');
  });
});
