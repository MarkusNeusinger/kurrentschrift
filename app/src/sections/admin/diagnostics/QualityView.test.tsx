// @vitest-environment jsdom
//
// The one confirmation this view gives after a WRITE to the shared production
// database — „Vorlage neu abgeleitet und gespeichert." — was invisible: apply()
// raises the flag and then bumps `cropCacheBust`, and the render-phase reset
// hanging off the load key cleared the flag again in the very same pass
// (website audit 2026-09-04, finding A39). Only a real click plus the refetch
// that click triggers can tell a shown note from a cleared one, which is why
// this file asks for a DOM where the rest of the suite renders to markup.

import { act, useState } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AdminCtx } from '@/context/adminState';
import type { AdminState } from '@/context/adminState';
import { getQuality, postResample } from '@/lib/api';
import type { GlyphOut, QualityComparison, QualityData } from '@/lib/api';
import { de } from '@/locales/admin';
import { QualityView } from './QualityView';

// The barrel keeps its other exports (the view's siblings read `ApiError` and
// the wire types through it); only the two calls this flow makes are replaced.
vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  getQuality: vi.fn(),
  postResample: vi.fn(),
}));

const SOURCE_ID = 'suetterlin-1922';

// Kurrent-metric shape: no `components`, so the per-category breakdown stays
// out of the markup and the assertions read the alerts, not a bar chart.
function quality(score: number): QualityData {
  return {
    iou: 0.82,
    dice: 0.9,
    chamfer_mean_px: 1.4,
    chamfer_p95_px: 3.1,
    pred_area_px: 4200,
    ink_area_px: 4400,
    score,
    loss: 100 - score,
    n_samples: 120,
    geo_rmse_px: 1.9,
    waviness_ratio: 0.12,
  };
}

const COMPARISON: QualityComparison = {
  stored: quality(78.4),
  // A candidate is what puts the „Neu ableiten & speichern" button on screen.
  candidate: quality(86.1),
  candidate_refine: null,
};

// Only `sourceId` and `refreshCrop` are read by the view; the rest of the
// workbench state would be dead weight in this file.
function adminState(refreshCrop: () => void): AdminState {
  return { sourceId: SOURCE_ID, refreshCrop } as unknown as AdminState;
}

// Mirrors the real wiring: `refreshCrop` from the context bumps the counter that
// comes back down as the `cropCacheBust` prop — the refetch the note must
// survive. `glyphKey` stays a prop so a test can switch letters without
// remounting, which is exactly what opening another glyph does.
function Harness({ glyphKey, onRefreshCrop }: { glyphKey: string; onRefreshCrop: () => void }) {
  const [bust, setBust] = useState(0);
  const state = adminState(() => {
    onRefreshCrop();
    setBust((n) => n + 1);
  });
  return (
    <AdminCtx.Provider value={state}>
      <QualityView glyphKey={glyphKey} cropCacheBust={bust} />
    </AdminCtx.Provider>
  );
}

describe('QualityView apply confirmation', () => {
  let container: HTMLDivElement;
  let root: Root;
  let refreshCrop: () => void;

  beforeEach(() => {
    (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
    vi.mocked(getQuality).mockResolvedValue(COMPARISON);
    vi.mocked(postResample).mockResolvedValue({} as GlyphOut);
    refreshCrop = vi.fn();
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    vi.clearAllMocks();
  });

  async function show(glyphKey: string) {
    await act(async () => {
      root.render(<Harness glyphKey={glyphKey} onRefreshCrop={refreshCrop} />);
    });
  }

  function successAlert(): Element | undefined {
    return [...container.querySelectorAll('[role="alert"]')].find((el) =>
      el.textContent?.includes(de.admin.quality.applied),
    );
  }

  async function clickApply() {
    const button = [...container.querySelectorAll('button')].find((b) =>
      b.textContent?.includes(de.admin.quality.apply),
    );
    expect(button, 'the apply button is not on screen').toBeDefined();
    await act(async () => {
      button?.click();
    });
  }

  it('keeps the confirmation through the refetch that applying triggers', async () => {
    await show('a');
    expect(successAlert(), 'nothing was applied yet').toBeUndefined();

    await clickApply();

    // The write went out, the crop cache was bumped, and the scores were read
    // again — the exact sequence that used to swallow the note.
    expect(postResample).toHaveBeenCalledWith(SOURCE_ID, 'a', { force: true });
    expect(refreshCrop).toHaveBeenCalledTimes(1);
    expect(getQuality).toHaveBeenCalledTimes(2);
    expect(successAlert()).toBeDefined();
  });

  it('drops the confirmation when another glyph is opened', async () => {
    await show('a');
    await clickApply();
    expect(successAlert()).toBeDefined();

    await show('e');

    expect(successAlert(), 'the note belongs to the letter it was written for').toBeUndefined();
  });
});
