// @vitest-environment jsdom
//
// The Abzugs-Linse as the author meets it: a tap selects the same site in the
// list AND on the image (both ways, nothing hover-only), a legend chip is a
// real switch only where there is something to switch, ⚑ hands the Korb the
// site it names, and a script without deduction categories gets the list's own
// sentence instead of an empty lens. The payload is synthetic.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { PenaltyCategoryKey, PenaltyCategoryOut, PenaltySitesOut } from '@/lib/api';
import type { PenaltyRef } from '@/sections/admin/shell/model';

const payload = vi.hoisted(() => ({ current: null as unknown }));

vi.mock('@/lib/api', async (orig) => ({
  ...(await orig<typeof import('@/lib/api')>()),
  cropUrl: () => 'crop.png',
  getPenaltySites: () => Promise.resolve(payload.current),
}));

import { PenaltyPanel } from './PenaltyPanel';

const empty = (over: Partial<PenaltyCategoryOut> = {}): PenaltyCategoryOut => ({
  value: 0,
  applicable: false,
  in_sync: true,
  exact: false,
  points_est: 0,
  sites: [],
  numbers: {},
  parts: {},
  context_paths: [],
  context_cells: [],
  ...over,
});

const gleichzug = (): PenaltySitesOut => {
  const sites: Record<PenaltyCategoryKey, PenaltyCategoryOut> = {
    smoothness: empty({ applicable: true }),
    verticality: empty(),
    corner: empty({
      value: 0.1711,
      applicable: true,
      exact: true,
      sites: [
        {
          index: 0,
          kind: 'corner',
          value: 0.0954,
          share: 0.56,
          exact: true,
          points_est: 2.28,
          x: 12,
          y: 8,
          numbers: { anchor: 71 },
          paths: [],
          cells: [],
        },
        {
          index: 1,
          kind: 'corner',
          value: 0.0757,
          share: 0.44,
          exact: true,
          points_est: 1.81,
          x: 30,
          y: 20,
          numbers: { anchor: 90 },
          paths: [],
          cells: [],
        },
      ],
    }),
    collinearity: empty(),
    retrace: empty(),
    coverage: empty({
      value: 0.0658,
      applicable: true,
      sites: [
        {
          index: 0,
          kind: 'rim',
          value: 0.0658,
          share: 1,
          exact: false,
          points_est: 3.3,
          x: null,
          y: null,
          numbers: { missed_px: 12 },
          paths: [],
          cells: [],
        },
      ],
    }),
  };
  return {
    glyph_key: 'a',
    style_id: 'suetterlin',
    variant: 0,
    metric: 'suetterlin_naturalness',
    reason: null,
    stamped: { corner: 0.171, coverage: 0.0301 },
    score: 80.4,
    components: { corner: 0.1711, coverage: 0.0658, smoothness: 0 },
    applicable: { corners: 2, vertical_runs: 0, crossings: 0, retrace_pairs: 0 },
    frame: { width: 40, height: 30, unit_px: 20 },
    centerline: [
      [
        [2, 2],
        [30, 20],
      ],
    ],
    sites,
    pins: [
      { rank: 1, category: 'corner', index: 0, points_est: 2.28, x: 12, y: 8 },
      { rank: 2, category: 'corner', index: 1, points_est: 1.81, x: 30, y: 20 },
    ],
  };
};

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  // jsdom has no layout observer; the lens falls back to a phone-sized column.
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe() {}
      disconnect() {}
    },
  );
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
});

async function mount(data: PenaltySitesOut, onMark: (ref: PenaltyRef) => void = () => undefined) {
  payload.current = data;
  await act(async () => {
    root.render(<PenaltyPanel sourceId="src" glyphKey="a" onMark={onMark} />);
  });
}

// Real controls only: a `<button>` or MUI's clickable chip (`role="button"`).
const buttons = () => [...container.querySelectorAll<HTMLElement>('button, [role="button"]')];
const byText = (text: string) => buttons().find((b) => b.textContent?.includes(text));

describe('PenaltyPanel', () => {
  it('shows today’s numbers, and the stamp only where it drifted', async () => {
    await mount(gleichzug());
    const text = container.textContent ?? '';
    expect(text).toContain('Abzüge (neu gemessen):');
    expect(text).toContain('Ecken 0.1711 · 2 Stellen');
    // Coverage moved 0.0301 → 0.0658; the corner stamp is within 0.005.
    expect(text).toContain('gespeichert: Deckungslücke 0.0301');
    expect(text).not.toContain('Ecken 0.1710');
  });

  it('makes a chip a switch only where there is something to draw', async () => {
    await mount(gleichzug());
    const corner = byText('Ecken 0.1711');
    expect(corner?.getAttribute('aria-pressed')).toBe('true');
    // „nicht anwendbar" and a map without a place are labels, not dead tab stops.
    expect(byText('Kreuzungsflucht · nicht anwendbar')).toBeUndefined();
    expect(container.textContent).toContain('Kreuzungsflucht · nicht anwendbar');
    expect(byText('Deckungslücke 0.0658')).toBeUndefined();

    await act(async () => corner?.click());
    expect(byText('Ecken 0.1711')?.getAttribute('aria-pressed')).toBe('false');
  });

  it('selects the same site from the list and from the image', async () => {
    await mount(gleichzug());
    const row = byText('Ecken #1 · Ecke');
    expect(row?.getAttribute('aria-pressed')).toBe('false');

    // From the list: the row is pressed and the detail names the site.
    await act(async () => row?.click());
    expect(byText('Ecken #1 · Ecke')?.getAttribute('aria-pressed')).toBe('true');
    expect(container.textContent).toContain('0.0757 von 0.1711 (44 %) · Term');

    // From the image: a tap on the first corner's target moves the selection
    // in the list too.
    const targets = [...container.querySelectorAll<SVGCircleElement>('svg circle[aria-hidden="true"]')];
    const first = targets.find((c) => c.getAttribute('cx') === '12' && c.getAttribute('cy') === '8');
    await act(async () => first?.dispatchEvent(new MouseEvent('click', { bubbles: true })));
    expect(byText('Ecken #0 · Ecke')?.getAttribute('aria-pressed')).toBe('true');
    expect(byText('Ecken #1 · Ecke')?.getAttribute('aria-pressed')).toBe('false');
  });

  it('hands ⚑ the selected site, with its part of the category number', async () => {
    const onMark = vi.fn();
    await mount(gleichzug(), onMark);
    await act(async () => byText('Ecken #0 · Ecke')?.click());
    await act(async () => byText('Bemängeln')?.click());
    expect(onMark).toHaveBeenCalledWith(
      expect.objectContaining({ category: 'corner', index: 0, value: 0.0954, categoryValue: 0.1711 }),
    );
  });

  it('lists the part without a place, and draws nothing for it', async () => {
    await mount(gleichzug());
    await act(async () => byText('Alle Stellen')?.click());
    const rim = byText('Deckungslücke #0');
    expect(rim?.textContent).toContain('ohne Ort');
    await act(async () => rim?.click());
    expect(container.textContent).toContain('ohne Ort — zählt in der Zahl');
  });

  it('gives a script without categories the list’s own sentence', async () => {
    await mount({
      ...gleichzug(),
      metric: null,
      reason: 'no_components',
      sites: null,
      frame: null,
      centerline: null,
      components: null,
      applicable: null,
      score: null,
      pins: [],
    });
    expect(container.textContent).toContain('Keine Abzüge nach Kategorie — diese Schrift misst anders.');
    expect(container.querySelector('svg circle')).toBeNull();
  });
});
