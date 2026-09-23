// @vitest-environment jsdom
//
// WHERE the hand lives, which is the one thing about it a pure function cannot
// test. `resolveHand` is the rule (handScope.test.ts); this file pins the
// placement the rule depends on — the chosen hand sits in the OUTER provider,
// above the `key={sourceId}` remount, so two Vorlagen of one script share it
// (author decision Q25 a). Move that `useState` back down into
// `SourceScopedProvider` and every assertion in handScope.test.ts still passes
// while the workbench forgets the hand on every Vorlage switch, which is
// exactly the regression this guards.

import { act, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AdminProvider } from '@/context/AdminContext';
import { useAdmin } from '@/context/adminState';
import { getBboxes, getEigenhandHands, getEigenhandSetups, getGlyphs, getSource, getSources } from '@/lib/api';
import type { SourceOut } from '@/lib/api';

// Only the boot reads are replaced; everything else the barrel exports (the
// wire types, `ApiError`) stays the real thing.
vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  getSource: vi.fn(),
  getSources: vi.fn(),
  getBboxes: vi.fn(),
  getGlyphs: vi.fn(),
  getEigenhandHands: vi.fn(),
  getEigenhandSetups: vi.fn(),
}));

const source = (id: string, style: string): SourceOut => ({
  id,
  style_id: style,
  hand_id: null,
  kind: 'chart',
  title: id,
  license: 'PD',
  chart_path: 'chart.svg',
  chart_size: { w: 100, h: 100 },
  style_ratio: [1, 1, 1],
  slant_deg: 90,
  attribution: null,
});

// Two Kurrent charts — the real constellation behind Q25 a — plus one of
// another script, to check the way back.
const SOURCES = [source('kurrent-a', 'kurrent'), source('kurrent-b', 'kurrent'), source('suet-1922', 'suetterlin')];

// What the last render saw, plus the two switches the test drives. A probe
// instead of markup: the assertions are about context values, and rendering
// them to text would only add a parser between the test and the state.
let seen: { handId: string | null; handChoices: string[]; handsLoaded: boolean };
let switchTo: (id: string) => void;
let pick: (id: string) => void;

function Probe() {
  const admin = useAdmin();
  // In an effect, not during render: writing to a module variable from the
  // render body is the side effect `react-hooks/globals` forbids, and `act`
  // flushes effects before the assertion runs anyway.
  useEffect(() => {
    seen = { handId: admin.handId, handChoices: admin.handChoices, handsLoaded: admin.handsLoaded };
    switchTo = admin.switchSource;
    pick = admin.setHand;
  });
  return null;
}

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  localStorage.clear();
  // The provider's own entry point: it boots on the persisted Vorlage, so the
  // test starts on a Kurrent chart rather than on the build default.
  localStorage.setItem('kurrentschrift.admin.sourceId', 'kurrent-a');
  vi.mocked(getSources).mockResolvedValue(SOURCES);
  vi.mocked(getSource).mockImplementation(async (id: string) => SOURCES.find((s) => s.id === id)!);
  vi.mocked(getBboxes).mockResolvedValue([]);
  vi.mocked(getGlyphs).mockResolvedValue([]);
  vi.mocked(getEigenhandHands).mockResolvedValue({
    hands: ['mn-kurrent', 'zweit-kurrent', 'mn-suetterlin'],
    styles: ['kurrent', 'suetterlin', 'offenbacher'],
  });
  vi.mocked(getEigenhandSetups).mockResolvedValue({ setups: [] });
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.clearAllMocks();
});

/** Mount the provider and let both boot reads settle. */
async function mount(): Promise<void> {
  await act(async () => {
    root.render(
      <AdminProvider>
        <Probe />
      </AdminProvider>,
    );
  });
}

describe('the hand in the admin scope', () => {
  it('survives a switch between two Vorlagen of ONE script (Q25 a)', async () => {
    await mount();
    // Nothing chosen yet, so nothing is claimed — V19's „oder leer".
    expect(seen.handId).toBeNull();
    expect(seen.handChoices).toEqual(['mn-kurrent', 'zweit-kurrent']);

    await act(async () => pick('zweit-kurrent'));
    expect(seen.handId).toBe('zweit-kurrent');

    // The second Kurrent chart: a different Vorlage, the same script — and
    // therefore the same hand.
    await act(async () => switchTo('kurrent-b'));
    expect(seen.handId).toBe('zweit-kurrent');
    // And the candidates were read ONCE for the whole workbench. Under the
    // remount this pair of admin-gated requests would fire again on every
    // Vorlage switch, for an answer that cannot have changed.
    expect(vi.mocked(getEigenhandHands)).toHaveBeenCalledTimes(1);
    expect(vi.mocked(getEigenhandSetups)).toHaveBeenCalledTimes(1);
  });

  it('keeps it across the switch even where nothing can be persisted', async () => {
    // The assertion that actually pins the PLACEMENT. With `localStorage`
    // working, the per-style memory hides a hand held under the remount: it is
    // written on every pick and read back on every mount. In a private window
    // there is no such crutch, and the choice survives a Vorlage switch only
    // because it lives in the OUTER provider (Q25 a).
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('private mode');
    });
    try {
      await mount();
      await act(async () => pick('zweit-kurrent'));
      expect(seen.handId).toBe('zweit-kurrent');
      await act(async () => switchTo('kurrent-b'));
      expect(seen.handId).toBe('zweit-kurrent');
    } finally {
      vi.restoreAllMocks();
    }
  });

  it('drops a foreign-script hand on a style change and brings it back', async () => {
    await mount();
    await act(async () => pick('zweit-kurrent'));

    await act(async () => switchTo('suet-1922'));
    // Never a hand of another script — and Sütterlin's ONLY hand stands in for
    // a pick nobody has made yet (§15.5 Nr. 13).
    expect(seen.handId).toBe('mn-suetterlin');
    expect(seen.handChoices).toEqual(['mn-suetterlin']);

    // Back to Kurrent: the hand chosen for THAT script, remembered per style.
    await act(async () => switchTo('kurrent-a'));
    expect(seen.handId).toBe('zweit-kurrent');
  });

  it('opens a fresh browser on the script\'s only hand, with nothing written to storage', async () => {
    // The tablet case: no pick, no memory, one Sütterlin hand. The field is
    // filled from the candidates alone — and it is NOT remembered as a pick,
    // so a second hand appearing later leaves the choice to the author
    // instead of keeping a default nobody made.
    localStorage.setItem('kurrentschrift.admin.sourceId', 'suet-1922');
    await mount();
    expect(seen.handId).toBe('mn-suetterlin');
    expect(localStorage.getItem('kurrentschrift.admin.handByStyle')).toBeNull();
  });

  it('says nothing about hands while the two reads are still out', async () => {
    // A 401 is not retried, so „no candidates" can be permanent — and both the
    // Scope-Leiste's em-dash and the Eigenhand page's „noch keine Hand erfasst"
    // would then be claims about data never read. `handsLoaded` is what those
    // two surfaces wait for.
    vi.mocked(getEigenhandHands).mockRejectedValue(new Error('401 Unauthorized'));
    await mount();
    expect(seen.handsLoaded).toBe(false);
    expect(seen.handId).toBeNull();
  });
});
