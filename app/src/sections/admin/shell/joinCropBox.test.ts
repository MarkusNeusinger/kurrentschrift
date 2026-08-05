// Unit cover for the join thumbnail's box.
//
// A `pair_instance` carries no pixel box: its geometry lives in the glyph_pairs
// frame (units relative to the left glyph's exit). What it does carry is the
// specimen and the LEFT glyph's slot, and the letter occurrences of the same
// plate carry those slots as page-pixel boxes. `joinCropBoxOf` is that lookup
// plus the union — which is exactly where it can go wrong, so:
//
// * the box spans BOTH letters, in the crop's frame (rect origin subtracted);
// * a slot index that lands on a different letter yields nothing, because the
//   two harvests then disagree about the word's slotting and the tile would
//   show the wrong ink;
// * a missing neighbour or a missing rect yields nothing rather than page
//   coordinates drawn into a crop frame.

import { describe, expect, it } from 'vitest';

import type { InstanceOut } from '@/lib/api';
import { joinCropBoxOf } from './model';

function letter(glyphKey: string, slot: number, x0: number, y0: number, x1: number, y1: number): InstanceOut {
  return {
    glyph_key: glyphKey,
    glyph: glyphKey,
    position: 'medial',
    variant: 0,
    hand_id: 'suetterlin-1922-norm',
    x0,
    y0,
    x1,
    y1,
    anchors: [],
    half_widths: [],
    measurements: { specimen_id: 'muß', slot },
  } as unknown as InstanceOut;
}

const RECT = [100, 50, 400, 200];
// "mu" — the m at slot 0, the u right of it at slot 1.
const LETTERS = [letter('m', 0, 120, 80, 180, 110), letter('u', 1, 175, 75, 220, 120)];
const OCC = { left_key: 'm', right_key: 'u', slot: 0 };

describe('joinCropBoxOf', () => {
  it('spans both letters in the crop frame', () => {
    expect(joinCropBoxOf(OCC, LETTERS, RECT)).toEqual({ x: 20, y: 25, w: 100, h: 45 });
  });

  it('refuses a slot that carries a different letter', () => {
    expect(joinCropBoxOf({ ...OCC, right_key: 'n' }, LETTERS, RECT)).toBeNull();
  });

  it('refuses when the neighbour was never fitted', () => {
    expect(joinCropBoxOf(OCC, [LETTERS[0]], RECT)).toBeNull();
    expect(joinCropBoxOf(OCC, undefined, RECT)).toBeNull();
  });

  it('refuses without a crop rect', () => {
    expect(joinCropBoxOf(OCC, LETTERS, undefined)).toBeNull();
  });
});
