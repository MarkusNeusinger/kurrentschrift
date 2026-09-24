// @vitest-environment jsdom
//
// The panel's three honest answers besides the counts: a failed read is said
// as a failure, a hand with no stored strip is said as „nothing to count" (not
// as four zeroes), and „vorläufig" stands wherever a counted box was graded
// under borrowed bounds.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { ApiError } from '@/lib/api/client';
import type { EigenhandPfadBox, EigenhandTintentreue } from '@/lib/api/types';

import { TintentreuePanel } from './TintentreuePanel';

const readBoxes = vi.fn();

vi.mock('@/lib/api', () => ({
  getEigenhandPfadBoxes: (...args: unknown[]) => readBoxes(...args),
}));

const urteil = (over: Partial<EigenhandTintentreue> = {}): EigenhandTintentreue => ({
  stufe: 'nicht beurteilt',
  grund: 'kein Eintrag',
  gemessen: false,
  sensor: null,
  sensoren: [],
  format: 2,
  schwellen_stand: '2026-09-20',
  vorlaeufig: true,
  ...over,
});

const box = (index: number, tintentreue: EigenhandTintentreue, over: Partial<EigenhandPfadBox> = {}): EigenhandPfadBox => ({
  box_index: index,
  word: `wort${index}`,
  absetzer_soll: 1,
  status: null,
  grund: null,
  detail: null,
  verfahren: null,
  erzeugt_am: null,
  flecken_n: null,
  stale: false,
  offen: true,
  tintentreue,
  ...over,
});

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  readBoxes.mockReset();
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

async function render() {
  await act(async () => {
    root.render(
      <MemoryRouter>
        <TintentreuePanel hand="mn-suetterlin" />
      </MemoryRouter>,
    );
  });
}

it('counts the steps, names the grey reasons and says „vorläufig"', async () => {
  readBoxes.mockResolvedValue({
    hand: 'mn-suetterlin',
    fassungen: [
      {
        strip: 'S0001',
        fassung: 'F01',
        sheet: 'B0001',
        row_index: 0,
        format: 2,
        gefolgt: true,
        zaehler: { kaesten: 3, gemessen: 1, folgt: 0, von_hand: 0 },
        kaesten: [
          box(0, urteil({ stufe: 'folgt nicht', grund: 'AIoU', gemessen: true, sensor: 'AIoU' }), {
            verfahren: 'tintenpfad',
          }),
          box(1, urteil({ grund: 'Format 1 — unvollständig gemessen', format: 1 })),
          box(2, urteil()),
        ],
      },
    ],
  });
  await render();
  const text = container.textContent ?? '';
  expect(readBoxes).toHaveBeenCalledWith('mn-suetterlin', undefined, { retries: 2 });
  expect(text).toContain('3 Kästen in 1 Fassung · 1 davon beurteilt');
  expect(text).toContain('folgt nicht');
  expect(text).toContain('1 Kasten (33 %)');
  expect(text).toContain('2 Kästen (67 %)');
  expect(text).toContain('Format 1 — unvollständig gemessen: 1');
  expect(text).toContain('kein Eintrag: 1');
  expect(text).toContain('vorläufig');
});

it('says there is nothing to count instead of printing four zeroes', async () => {
  readBoxes.mockResolvedValue({ hand: 'mn-suetterlin', fassungen: [] });
  await render();
  const text = container.textContent ?? '';
  expect(text).toContain('noch kein Streifen abgelegt');
  expect(text).not.toContain('(0 %)');
  expect(text).not.toContain('vorläufig');
});

it('names a failed read as a failure', async () => {
  readBoxes.mockRejectedValue(new ApiError(503, 'down'));
  await render();
  expect(container.textContent ?? '').toContain('konnten nicht gelesen werden');
});
