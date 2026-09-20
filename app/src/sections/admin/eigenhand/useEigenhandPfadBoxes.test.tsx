// @vitest-environment jsdom
//
// Two rules of the hand-wide box read that no type checker keeps, and that both
// surfaces reading it depend on.
//
//  1. A FAILED RE-READ KEEPS THE BOXES. This read is asked again after every
//     box the author writes by hand, while his editor is still open on the next
//     one. Dropping the rows to null on that failure takes the list's error
//     branch, which unmounts the editor — with the drawing on it, past its own
//     discard guard. A hand-drawn Bahn is the one artefact in this repository
//     no run recreates (Copilot review).
//  2. THE CALLER'S REFRESH TOKEN IS PART OF THE REQUEST. A saved Fleckenmaske
//     re-measures the Streifen-Befund, and the Tintentreue every Ampel shows is
//     derived from that measurement — so the gallery has to ask again with the
//     listing, not at its next mount.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { ApiError } from '@/lib/api/client';
import type { EigenhandPfadBoxes, EigenhandPfadFassung } from '@/lib/api/types';

import { useEigenhandPfadBoxes } from './useEigenhandPfadBoxes';

const readBoxes = vi.fn();

vi.mock('@/lib/api', () => ({
  getEigenhandPfadBoxes: (...args: unknown[]) => readBoxes(...args),
}));

const fassung = (strip: string): EigenhandPfadFassung => ({
  strip,
  fassung: 'F02',
  sheet: 'B0001',
  row_index: 0,
  format: 2,
  gefolgt: true,
  zaehler: { kaesten: 0, gemessen: 0, folgt: 0, von_hand: 0 },
  kaesten: [],
});

const answer = (...strips: string[]): EigenhandPfadBoxes => ({
  hand: 'wegwerf-suetterlin',
  fassungen: strips.map(fassung),
});

let container: HTMLDivElement;
let root: Root;

/** The hook under a surface that shows what it holds — one line for the rows
 * in hand, one for the error beside them. */
function Probe({ refresh = 0 }: { refresh?: number }) {
  const { fassungen, error, reload } = useEigenhandPfadBoxes('wegwerf-suetterlin', true, refresh);
  return (
    <div>
      <span data-rows>{fassungen === null ? 'keine' : fassungen.map((f) => f.strip).join(' ')}</span>
      <span data-error>{error === null ? '' : error.detail}</span>
      <button type="button" onClick={reload}>
        neu
      </button>
    </div>
  );
}

const shown = (attribute: 'data-rows' | 'data-error'): string =>
  container.querySelector(`[${attribute}]`)?.textContent ?? '';

const reload = async (): Promise<void> => {
  await act(async () => {
    container.querySelector('button')?.click();
  });
};

beforeEach(() => {
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  readBoxes.mockResolvedValue(answer('S0041'));
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.clearAllMocks();
});

const render = async (refresh = 0): Promise<void> => {
  await act(async () => {
    root.render(<Probe refresh={refresh} />);
  });
};

it('keeps the boxes in hand when a re-read fails, and says so beside them', async () => {
  await render();
  expect(shown('data-rows')).toBe('S0041');

  readBoxes.mockRejectedValueOnce(new ApiError(503, '503: upstream unavailable'));
  await reload();

  // The rows stand. What the failed read says is that this state may be older
  // than the server's — not that there is none, and never that a surface built
  // on it should be taken down.
  expect(shown('data-rows')).toBe('S0041');
  expect(shown('data-error')).toContain('503');
});

it('clears the error once a later read lands', async () => {
  await render();
  readBoxes.mockRejectedValueOnce(new ApiError(503, '503: upstream unavailable'));
  await reload();
  expect(shown('data-error')).toContain('503');

  readBoxes.mockResolvedValue(answer('S0041', 'S0042'));
  await reload();
  expect(shown('data-error')).toBe('');
  expect(shown('data-rows')).toBe('S0041 S0042');
});

it('has nothing to keep on the FIRST read, and reports the failure alone', async () => {
  readBoxes.mockRejectedValue(new ApiError(503, '503: upstream unavailable'));
  await render();

  expect(shown('data-rows')).toBe('keine');
  expect(shown('data-error')).toContain('503');
});

it('asks again when the caller’s refresh token moves', async () => {
  await render();
  expect(readBoxes).toHaveBeenCalledTimes(1);

  // A saved Fleckenmaske: the picture is the same, what the server says about
  // it is not.
  readBoxes.mockResolvedValue(answer('S0041', 'S0042'));
  await render(1);

  expect(readBoxes).toHaveBeenCalledTimes(2);
  expect(shown('data-rows')).toBe('S0041 S0042');
});
