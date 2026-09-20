// The frame under the drawing, and the way back into the pixels the column
// stores.
//
// A Bahn drawn, saved, read again and re-seeded has to land on the SAME pixels.
// Everything between those two states is one subtraction and one addition — and
// an off-by-the-rectangle there looks like a drawing error on screen, which is
// why it is pinned here rather than judged from a screenshot.

import { describe, expect, it } from 'vitest';

import type { EigenhandPfad, EigenhandPfadList } from '@/lib/api';

import { cropRegistration, stripRegistration, stripTraceSeed } from './stripTraceFrame';

const RECT = [120, 30, 320, 190];

const bahn = (over: Partial<EigenhandPfad> = {}): EigenhandPfad => ({
  box_index: 1,
  word: 'lesen',
  status: 'ok',
  grund: null,
  detail: null,
  strokes: [
    [
      [0, 0],
      [1, 1],
    ],
  ],
  letter_spans: null,
  registration_px: { tx: 140, ty: 4, baseline_row: 150 },
  xh_px: 40,
  verfahren: 'tintenpfad',
  konfiguration: {},
  meta: {},
  erzeugt_am: '2026-09-20',
  flecken_n: 0,
  ...over,
});

const list = (over: Partial<EigenhandPfadList> = {}): EigenhandPfadList => ({
  hand: 'mn-suetterlin',
  strip: 'S0041',
  fassung: 'F02',
  format: 2,
  pfade: [bahn()],
  boxes: [
    { index: 0, word: 'das', items: [], rect_px: [0, 30, 110, 190] },
    { index: 1, word: 'lesen', items: [], rect_px: RECT, nominal_baseline_row: 152, nominal_xh_px: 38 },
  ],
  ...over,
});

describe('the crop frame', () => {
  it('moves a stored frame into the crop and back unchanged', () => {
    const stored = { tx: 140, ty: 4, baseline_row: 150 };
    const crop = cropRegistration(stored, 40, RECT);
    // The crop's own pixels: the box rectangle comes off both axes, and the
    // row shift is folded into the baseline exactly as every reader adds it.
    expect(crop).toEqual({ xh: 40, tx: 20, baselineRow: 124 });
    expect(stripRegistration(crop, RECT)).toEqual({ tx: 140, ty: 0, baseline_row: 154 });
    // …and that frame reads back to the same crop pixels, which is what „the
    // same pixels after a round trip" means.
    expect(cropRegistration(stripRegistration(crop, RECT), crop.xh, RECT)).toEqual(crop);
  });
});

describe('stripTraceSeed', () => {
  it('seeds from the stored Bahn, frame and strokes alike', () => {
    const seed = stripTraceSeed(list(), 1);
    expect(seed).not.toBeNull();
    expect(seed?.herkunft).toBe('bahn');
    expect(seed?.width).toBe(200);
    expect(seed?.height).toBe(160);
    expect(seed?.reg).toEqual({ xh: 40, tx: 20, baselineRow: 124 });
    expect(seed?.strokes).toEqual([
      [
        [0, 0],
        [1, 1],
      ],
    ]);
  });

  it('falls back to the PRINTED ruling where the box carries no Bahn', () => {
    // The box the author most needs to draw: the follower gave up, and its
    // Skip-Eintrag carries neither registration nor scale by construction.
    const seed = stripTraceSeed(
      list({ pfade: [bahn({ status: 'skipped', grund: 'gave_up', strokes: [], registration_px: null, xh_px: null })] }),
      1,
    );
    expect(seed?.herkunft).toBe('saat');
    expect(seed?.strokes).toEqual([]);
    expect(seed?.reg).toEqual({ xh: 38, tx: 0, baselineRow: 122 });
  });

  it('answers null where the Bogen has no geometry at all', () => {
    // „nie machbar": no rectangle means neither a crop to draw on nor a frame
    // to store a Bahn in.
    expect(stripTraceSeed(list({ boxes: [{ index: 1, word: 'lesen', items: [], rect_px: null }] }), 1)).toBeNull();
    // …and the same where the rectangle is there but the ruling is not: a
    // frame would have to be invented, and an invented x-height is what the
    // server's own bound refuses.
    expect(
      stripTraceSeed(list({ pfade: null, boxes: [{ index: 1, word: 'lesen', items: [], rect_px: RECT }] }), 1),
    ).toBeNull();
  });

  it('carries the stored letter boundaries through', () => {
    const spans = [{ stroke: 0, slot: 0, first: 0, last: 1, herkunft: 'auto' as const }];
    expect(stripTraceSeed(list({ pfade: [bahn({ letter_spans: spans })] }), 1)?.spans).toEqual(spans);
  });
});
