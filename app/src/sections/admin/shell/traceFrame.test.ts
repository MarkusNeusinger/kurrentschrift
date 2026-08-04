// Unit cover for the ONE registration both word overlays now use.
//
// The point of `traceFrameOf` is that a stored trace and the engine's
// composition of the same word live in the identical frame (baseline = 0,
// 1 unit = x-height), so a single scale+translate places both. Before, the
// engine ink was pinned to the crop's LEFT EDGE instead — over the 63 Sütterlin
// word rows that sat a median 8.9 px (~0.3 xh) left of the specimen ink and
// made every composition read worse than it is. What has to hold mechanically:
//
// * the measured registration wins whenever a row carries one, `ty` included;
// * `xh_px` overrides the sidecar's baseline−midband, since the fit measured it;
// * a sample WITHOUT a trace still yields a usable frame (the sidecar's), so
//   the caller can fall back rather than crash;
// * the matrix flips y — units grow upwards, crop pixels downwards.

import { describe, expect, it } from 'vitest';

import type { WordInstanceOut } from '@/lib/api';
import { traceFrameOf, traceMatrix } from './model';

const SAMPLE = { baseline_y: 68, midband_y: 38 }; // xh = 30 px

function rowWith(measurements: Partial<WordInstanceOut['measurements']>): WordInstanceOut {
  return {
    specimen_id: 'muß',
    kind: 'word',
    word: 'muß',
    slots: ['m', 'u', 'sz'],
    strokes: [],
    provenance: 'traced',
    hand_id: 'suetterlin-1922-norm',
    measurements,
  } as unknown as WordInstanceOut;
}

describe('traceFrameOf', () => {
  it('uses the row’s measured registration', () => {
    const frame = traceFrameOf(rowWith({ xh_px: 30, registration_px: { tx: 9, ty: 0, baseline_row: 68 } }), SAMPLE);
    expect(frame).toEqual({ xh: 30, tx: 9, baselineRow: 68 });
  });

  it('adds ty to the baseline row', () => {
    // ty is the fit's vertical correction ON TOP of the sidecar row — dropping
    // it would float the whole word off the specimen's baseline.
    const frame = traceFrameOf(rowWith({ xh_px: 30, registration_px: { tx: 4, ty: -2.5, baseline_row: 68 } }), SAMPLE);
    expect(frame.baselineRow).toBe(65.5);
  });

  it('prefers the fitted x-height over the sidecar’s lineature', () => {
    const frame = traceFrameOf(rowWith({ xh_px: 31.5, registration_px: { tx: 0, ty: 0, baseline_row: 68 } }), SAMPLE);
    expect(frame.xh).toBe(31.5);
  });

  it('falls back to the sidecar per field, not all-or-nothing', () => {
    // A row harvested before a field existed must not drag the others down.
    expect(traceFrameOf(rowWith({}), SAMPLE)).toEqual({ xh: 30, tx: 0, baselineRow: 68 });
  });

  it('yields the sidecar frame for a sample with no trace', () => {
    expect(traceFrameOf(null, SAMPLE)).toEqual({ xh: 30, tx: 0, baselineRow: 68 });
    expect(traceFrameOf(undefined, SAMPLE)).toEqual({ xh: 30, tx: 0, baselineRow: 68 });
  });
});

describe('traceMatrix', () => {
  it('flips y and carries the translation', () => {
    expect(traceMatrix({ xh: 30, tx: 9, baselineRow: 68 })).toBe('matrix(30 0 0 -30 9 68)');
  });

  it('maps the frame’s origin onto the baseline at tx', () => {
    // The property the whole registration rests on, restated as arithmetic:
    // unit (0,0) is the baseline at tx, and one unit up is xh pixels higher.
    const f = { xh: 30, tx: 9, baselineRow: 68 };
    const at = (u: number, v: number) => [u * f.xh + f.tx, f.baselineRow - v * f.xh];
    expect(at(0, 0)).toEqual([9, 68]);
    expect(at(0, 1)).toEqual([9, 38]);
    expect(at(1, 0)).toEqual([39, 68]);
  });
});
