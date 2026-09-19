// @vitest-environment jsdom
//
// The report half of the apply dialog, for the ONE skip reason whose payload is
// a name rather than a number: `foreign_hand` (the Eigner-Regel). Its chip is
// assembled from three pieces that live in three files — the reason code from
// the endpoint, the German label from the locale, the owner in parentheses from
// this component — and a missing locale key degrades into the raw code without
// failing anything. Only rendering the finished label catches that, which is
// why this file asks for a DOM.

import { act } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

import { applyLaufform } from '@/lib/api';
import type { AggregateApplyOut, AggregateOut } from '@/lib/api';
import { LaufformApplyDialog } from './LaufformApplyDialog';

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  applyLaufform: vi.fn(),
}));

const AGGREGATE: AggregateOut = {
  glyph_key: 'n',
  glyph: 'n',
  variant: 0,
  cluster_center: [[0, 0]],
  hull: {},
  mean_stats: {},
  n_instances: 4,
  laufform_anchors: [[0, 0]],
  laufform_dev_xh: 0.04,
};

function reply(overrides: Partial<AggregateApplyOut['skipped'][number]>): AggregateApplyOut {
  return {
    hand_id: 'zweithand',
    style_id: 'suetterlin',
    applied: [],
    skipped: [
      {
        glyph_key: 'n',
        variant: 0,
        reason: 'foreign_hand',
        n_instances: null,
        spike_ratio: null,
        spike_max: null,
        head_deviation: null,
        head_max: null,
        owner_hand_id: 'suetterlin-1922-norm',
        ...overrides,
      },
    ],
    excluded: [],
  };
}

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
  vi.clearAllMocks();
});

async function runApply(out: AggregateApplyOut): Promise<void> {
  vi.mocked(applyLaufform).mockResolvedValue(out);
  await act(async () => {
    root.render(
      <LaufformApplyDialog handId="zweithand" aggregates={[AGGREGATE]} onClose={() => {}} onApplied={() => {}} />,
    );
  });
  const confirm = [...document.querySelectorAll('button')].find((b) => b.textContent?.startsWith('Ja,'));
  expect(confirm).toBeDefined();
  await act(async () => confirm!.click());
}

it('names the owner beside the foreign_hand reason', async () => {
  await runApply(reply({}));
  // Reason word AND owner: the chip has to answer "why not" and "whose" in one
  // line, because the dialog offers no second place to ask.
  expect(document.body.textContent).toContain('n · gehört einer anderen Hand (suetterlin-1922-norm)');
});

it('prints the reason without an owner when the registration names none', async () => {
  // `owner_hand_id` is null when several hands are registered for one style —
  // the server refuses to invent a name, and the chip must not print "(null)".
  await runApply(reply({ owner_hand_id: null }));
  expect(document.body.textContent).toContain('n · gehört einer anderen Hand');
  expect(document.body.textContent).not.toContain('(null)');
});
