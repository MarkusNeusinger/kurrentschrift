// @vitest-environment jsdom
//
// The one promise of this list that is not about the list: it may not take the
// editor down with it.
//
// Every box written by hand re-reads the whole hand („der Stand der Kästen"),
// and that re-read runs WHILE the editor stays open and walks to the next box.
// A failed one used to clear the rows, which took the list's early error return
// — and with it the editor, its canvas and whatever was drawn on it, past the
// discard guard that exists for exactly this loss (Copilot review). A
// hand-drawn Bahn is the one artefact here that no follower run recreates, so
// a background read failing somewhere else may never be the thing that deletes
// it.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { ApiError } from '@/lib/api/client';
import type {
  EigenhandPfad,
  EigenhandPfadBox,
  EigenhandPfadBoxes,
  EigenhandPfadList,
  EigenhandTintentreue,
} from '@/lib/api/types';
import { KorbCtx } from '@/sections/admin/shell/korbState';

import { NachfahrListe } from './NachfahrListe';

const readBoxes = vi.fn();
const readPfade = vi.fn();
const patchPfad = vi.fn();
const fetchStrip = vi.fn();

vi.mock('@/lib/api', () => ({
  getEigenhandPfadBoxes: (...args: unknown[]) => readBoxes(...args),
  getEigenhandPfadeWithEtag: (...args: unknown[]) => readPfade(...args),
  patchEigenhandPfad: (...args: unknown[]) => patchPfad(...args),
  fetchEigenhandStrip: (...args: unknown[]) => fetchStrip(...args),
}));

const RECT = [120, 30, 320, 190];
const CROP_W = 200;
const CROP_H = 160;

const urteil = (): EigenhandTintentreue => ({
  stufe: 'folgt nicht',
  grund: 'Absetzer (Bahn)',
  gemessen: true,
  sensor: 'Absetzer (Bahn)',
  sensoren: [],
  format: 2,
  schwellen_stand: '2026-09-20',
  vorlaeufig: true,
});

const kasten = (): EigenhandPfadBox => ({
  box_index: 0,
  word: 'lesen',
  absetzer_soll: 1,
  status: null,
  grund: null,
  detail: null,
  verfahren: 'tintenpfad',
  erzeugt_am: '2026-09-19',
  flecken_n: 0,
  stale: false,
  offen: true,
  tintentreue: urteil(),
});

const boxes = (): EigenhandPfadBoxes => ({
  hand: 'wegwerf-suetterlin',
  fassungen: [
    {
      strip: 'S0041',
      fassung: 'F02',
      sheet: 'B0001',
      row_index: 0,
      format: 2,
      gefolgt: true,
      zaehler: { kaesten: 1, gemessen: 1, folgt: 0, von_hand: 0 },
      kaesten: [kasten()],
    },
  ],
});

const pfad = (): EigenhandPfad => ({
  box_index: 0,
  word: 'lesen',
  status: 'ok',
  grund: null,
  detail: null,
  strokes: [
    [
      [0, 0],
      [0.5, 1],
      [1, 0],
    ],
  ],
  letter_spans: null,
  registration_px: { tx: 140, ty: 4, baseline_row: 150 },
  xh_px: 40,
  verfahren: 'tintenpfad',
  konfiguration: {},
  meta: {},
  erzeugt_am: '2026-09-19',
  flecken_n: 0,
});

const list = (): EigenhandPfadList => ({
  hand: 'wegwerf-suetterlin',
  strip: 'S0041',
  fassung: 'F02',
  format: 2,
  pfade: [pfad()],
  boxes: [{ index: 0, word: 'lesen', items: [], rect_px: RECT, nominal_baseline_row: 152, nominal_xh_px: 38 }],
});

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  readBoxes.mockResolvedValue(boxes());
  readPfade.mockResolvedValue({ list: list(), etag: '"first"' });
  patchPfad.mockResolvedValue({ list: list(), etag: '"second"' });
  fetchStrip.mockResolvedValue(new Blob(['png'], { type: 'image/png' }));
  globalThis.URL.createObjectURL = vi.fn(() => 'blob:strip');
  globalThis.URL.revokeObjectURL = vi.fn();
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.clearAllMocks();
});

const text = (): string => document.body.textContent ?? '';

const button = (label: string): HTMLButtonElement => {
  const found = [...document.body.querySelectorAll('button')].find((b) => b.textContent?.trim() === label);
  if (!found) throw new Error(`no button „${label}"`);
  return found;
};

const canvas = (): SVGSVGElement => {
  const svg = document.body.querySelector('[data-trace-canvas] svg');
  if (!svg) throw new Error('no drawing surface');
  return svg as SVGSVGElement;
};

function pen(type: 'pointerdown' | 'pointermove' | 'pointerup', x: number, y: number): void {
  const event = new MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y });
  Object.defineProperty(event, 'pointerId', { value: 1 });
  Object.defineProperty(event, 'pointerType', { value: 'pen' });
  act(() => {
    canvas().dispatchEvent(event);
  });
}

/** Mount the list and open its one box in the editor, ready to be drawn on. */
async function openEditor(): Promise<void> {
  await act(async () => {
    root.render(
      <MemoryRouter>
        <KorbCtx.Provider value={{ openCount: null, items: null, fileMark: vi.fn(), openKorb: vi.fn() }}>
          <NachfahrListe hand="wegwerf-suetterlin" wort="" item={null} onShowGalerie={() => {}} />
        </KorbCtx.Provider>
      </MemoryRouter>,
    );
  });
  await act(async () => button('Nachfahren').click());
  const svg = canvas();
  svg.getBoundingClientRect = () =>
    ({ left: 0, top: 0, right: CROP_W, bottom: CROP_H, width: CROP_W, height: CROP_H, x: 0, y: 0 }) as DOMRect;
  svg.setPointerCapture = () => {};
  svg.releasePointerCapture = () => {};
}

it('keeps the open editor when the re-read after a saved box fails', async () => {
  await openEditor();
  pen('pointerdown', 30, 120);
  pen('pointermove', 60, 100);
  pen('pointermove', 90, 120);
  pen('pointerup', 90, 120);

  // The save lands; the hand-wide re-read it triggers does not.
  readBoxes.mockRejectedValue(new ApiError(503, '503: upstream unavailable'));
  await act(async () => button('Speichern').click());

  expect(patchPfad).toHaveBeenCalledTimes(1);
  // Still on the surface, with the box it was opened on: the author writes the
  // next one here, and that drawing exists nowhere else until he saves it.
  expect(document.body.querySelector('[data-trace-canvas]')).not.toBeNull();
  expect(text()).toContain('Kasten 0');
  // The failure is said, over a list that still stands.
  expect(text()).toContain('Der Stand der Kästen konnte nicht neu gelesen werden');
});

it('replaces the list with the error only while there is no list', async () => {
  readBoxes.mockRejectedValue(new ApiError(503, '503: upstream unavailable'));
  await act(async () => {
    root.render(
      <MemoryRouter>
        <KorbCtx.Provider value={{ openCount: null, items: null, fileMark: vi.fn(), openKorb: vi.fn() }}>
          <NachfahrListe hand="wegwerf-suetterlin" wort="" item={null} onShowGalerie={() => {}} />
        </KorbCtx.Provider>
      </MemoryRouter>,
    );
  });

  expect(text()).toContain('Die Kastenliste konnte nicht geladen werden');
  expect(text()).not.toContain('lesen');
});
