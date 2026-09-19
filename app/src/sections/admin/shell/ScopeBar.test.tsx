// @vitest-environment jsdom
//
// The Scope-Leiste answers ONE question — what is this page about — and it
// answers it in three ways that only a rendered DOM can check: which field
// carries `aria-current`, whether the Korb count is really visible text in the
// field that names the Vorlage (V25 forbids it living in a tooltip only), and
// what an empty hand looks like. All three are label correctness, which is the
// whole reason the bar exists, so they are pinned rather than eyeballed.
//
// Since the keyboard round the bar also carries the „Kurztasten" switch (author
// decision P1-Q11 b), and that is label correctness of the same kind: its state
// has to be READABLE, not just switchable.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AdminCtx, type AdminState } from '@/context/adminState';
import type { SourceOut } from '@/lib/api';
import { ScopeBar } from './ScopeBar';
import { SHORTCUTS_STORAGE_KEY } from './shortcuts';
import { SubjectNavProvider } from './SubjectNavContext';

const SOURCE = {
  id: 'suetterlin-1922',
  style_id: 'suetterlin',
  hand_id: null,
  kind: 'chart',
  title: 'Sütterlin-Ausgangsschrift 1922',
  license: 'PD',
  chart_path: 'chart.svg',
  chart_size: { w: 100, h: 100 },
  style_ratio: [1, 1, 1],
  slant_deg: 90,
  attribution: null,
} satisfies SourceOut;

// Everything the bar does not read, as a no-op: the point of the fixture is
// that the bar reads exactly `source` and `handId`.
const adminState = (over: Partial<AdminState>): AdminState =>
  ({
    sourceId: SOURCE.id,
    source: SOURCE,
    sources: [SOURCE],
    switchSource: () => {},
    handId: 'mn-suetterlin',
    handChoices: ['mn-suetterlin'],
    setHand: () => {},
    handsLoaded: true,
    handsError: null,
    bboxesByKey: {},
    glyphsByKey: {},
    laufformKeys: new Set<string>(),
    refreshGlyphs: async () => {},
    loadError: null,
    waking: false,
    activeGlyph: null,
    visibleGlyphs: new Set<string>(),
    cropCacheBust: 0,
    setActiveGlyph: () => {},
    toggleVisible: () => {},
    setOnlyVisible: () => {},
    upsertBbox: () => {},
    removeBbox: () => {},
    markGlyphTraced: () => {},
    removeGlyph: () => {},
    refreshCrop: () => {},
    wizardGlyph: null,
    openWizard: () => {},
    closeWizard: () => {},
    diagnoseGlyph: null,
    openDiagnose: () => {},
    closeDiagnose: () => {},
    ...over,
  }) satisfies AdminState;

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

function render(path: string, state: Partial<AdminState> = {}, openCount: number | null = null): void {
  act(() => {
    root.render(
      <MemoryRouter initialEntries={[path]}>
        <SubjectNavProvider>
          <AdminCtx.Provider value={adminState(state)}>
            <ScopeBar openCount={openCount} />
          </AdminCtx.Provider>
        </SubjectNavProvider>
      </MemoryRouter>,
    );
  });
}

/** The field's whole line — the link plus what rides beside it in the field. */
const field = (href: string): HTMLElement => {
  const link = [...container.querySelectorAll('a')].find((a) => a.getAttribute('href') === href);
  expect(link, href).toBeDefined();
  return link!.parentElement as HTMLElement;
};

const sourceLink = () => field('/admin').querySelector('a')!;
const handLink = () => field('/admin/eigenhand').querySelector('a')!;

describe('the Scope-Leiste', () => {
  it('names both scopes and links each to where it is changed', () => {
    render('/admin/buchstaben');
    expect(sourceLink().textContent).toContain('Vorlage:');
    expect(sourceLink().textContent).toContain('Sütterlin · suetterlin-1922');
    expect(handLink().textContent).toContain('Hand:');
    expect(handLink().textContent).toContain('mn-suetterlin');
    // The role gloss, so „Hand" on a Vorlagen page cannot be read as the
    // plate hand whose statistics the panels below show (P1-Q3 a).
    expect(handLink().textContent).toContain('Eigenhand (meine Hand)');
  });

  it('highlights the Vorlage on the Vorlagen views', () => {
    for (const path of ['/admin', '/admin/buchstaben', '/admin/uebergaenge', '/admin/woerter']) {
      render(path);
      expect(sourceLink().getAttribute('aria-current'), path).toBe('true');
      expect(handLink().getAttribute('aria-current'), path).toBeNull();
    }
  });

  it('highlights the hand on the Eigenhand page, sub-view and all', () => {
    for (const path of ['/admin/eigenhand', '/admin/eigenhand?reiter=streifen']) {
      render(path);
      expect(handLink().getAttribute('aria-current'), path).toBe('true');
      expect(sourceLink().getAttribute('aria-current'), path).toBeNull();
    }
  });

  it('says the Korb count in the field that names the Vorlage', () => {
    render('/admin/buchstaben', {}, 3);
    // Both in ONE field: the count and its scope are read together, and the
    // scope is never something you have to hover to learn.
    const line = field('/admin').textContent ?? '';
    expect(line).toContain('Sütterlin');
    expect(line).toContain('3 offen');
    // …and not in the field that names the hand, whose basket it is not.
    expect(field('/admin/eigenhand').textContent).not.toContain('offen');
  });

  it('claims no basket while the count is unknown, and none when it is empty', () => {
    // The read is admin-gated and may 401 — a „0 offen" would claim an empty
    // basket the bar never read.
    render('/admin/buchstaben', {}, null);
    expect(field('/admin').textContent).not.toContain('offen');
    render('/admin/buchstaben', {}, 0);
    expect(field('/admin').textContent).not.toContain('offen');
  });

  it('writes an em-dash where a script has no hand of its own', () => {
    render('/admin/buchstaben', { handId: null, handChoices: [] });
    expect(handLink().textContent).toContain('—');
    // Still a link: the Eigenhand page is where the first one is written.
    expect(handLink().getAttribute('href')).toBe('/admin/eigenhand');
  });

  it('says nothing at all while the hands are unknown', () => {
    // The em-dash is a STATEMENT — „this script has none". Before the two
    // admin-gated reads answer, and after a 401 (which is not retried), the
    // bar has not read anything that would justify it. Same rule as the Korb
    // count: unknown shows nothing, it does not show a zero.
    render('/admin/buchstaben', { handId: null, handChoices: [], handsLoaded: false });
    expect(handLink().textContent).toContain('Hand:');
    expect(handLink().textContent).not.toContain('—');
    expect(handLink().textContent).not.toContain('Eigenhand');
  });

  it('says so when no Vorlage has loaded yet', () => {
    render('/admin/buchstaben', { source: null });
    expect(sourceLink().textContent).toContain('keine Vorlage');
  });
});

describe('the Kurztasten switch', () => {
  const box = (): HTMLInputElement => {
    const input = container.querySelector<HTMLInputElement>('input[type="checkbox"]');
    expect(input).not.toBeNull();
    return input!;
  };
  /** The switch's own line — label, state word and the binding. */
  const line = (): string => box().closest('div')?.parentElement?.textContent ?? '';
  /** The state word's OWN node: the span beside the switch's label. Read off the
   * whole line instead, „an" would also be found inside „Gegenstand" and the
   * assertion would hold with the word deleted. */
  const stateWord = (): string => {
    const span = box().closest('label')?.nextElementSibling;
    expect(span).not.toBeNull();
    return span!.textContent ?? '';
  };

  it('is on by default and says so in words, not just in the knob', () => {
    // A switch read only by where its knob sits is a colour-only state in
    // another shape (§9.5) — so „an"/„aus" stands beside it as text.
    render('/admin/buchstaben');
    expect(box().checked).toBe(true);
    expect(line()).toContain('Kurztasten');
    expect(stateWord()).toBe('an');
  });

  it('tells the reader the combination', () => {
    render('/admin/buchstaben');
    // The one sentence that keeps the binding from being a secret. Alt+SHIFT,
    // because Alt+← alone is the browser's Back (P1-Q11 b).
    expect(line()).toContain('Alt + Umschalt + ← / →');
  });

  it('flips, says „aus", and remembers the choice', () => {
    const store = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => void store.set(key, value),
    });
    render('/admin/buchstaben');
    act(() => box().click());
    expect(box().checked).toBe(false);
    expect(stateWord()).toBe('aus');
    expect(store.get(SHORTCUTS_STORAGE_KEY)).toBe('aus');
    vi.unstubAllGlobals();
  });

  it('reads a remembered „aus" back on the next mount', () => {
    vi.stubGlobal('localStorage', {
      getItem: () => 'aus',
      setItem: () => {},
    });
    render('/admin/buchstaben');
    expect(box().checked).toBe(false);
    vi.unstubAllGlobals();
  });

  it('still switches when the browser refuses to store anything', () => {
    // A private window throws on the property access itself. The switch works
    // for this session; it just does not outlive it — and nothing is reported
    // to the reader, because nothing they did failed.
    vi.stubGlobal('localStorage', {
      getItem() {
        throw new DOMException('denied', 'SecurityError');
      },
      setItem() {
        throw new DOMException('denied', 'SecurityError');
      },
    });
    render('/admin/buchstaben');
    expect(box().checked).toBe(true);
    act(() => box().click());
    expect(box().checked).toBe(false);
    expect(stateWord()).toBe('aus');
    vi.unstubAllGlobals();
  });
});
