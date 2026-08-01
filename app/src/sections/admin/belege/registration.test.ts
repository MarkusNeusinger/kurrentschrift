import { describe, expect, it } from 'vitest';

import type { WordSampleOut } from '@/lib/api';

import {
  MAX_STROKE_POINTS,
  MAX_TRACE_COORD,
  cropToTrace,
  registrationMatrix,
  sanitizeStrokes,
  strokePathD,
  traceRegistration,
  traceToCrop,
  type TracePoint,
} from './registration';

const sample = (over: Partial<WordSampleOut> = {}): WordSampleOut => ({
  id: 'wenn',
  word: 'wenn',
  kind: 'word',
  sample_set: null,
  width: 200,
  height: 90,
  baseline_y: 60,
  midband_y: 30,
  ...over,
});

describe('traceRegistration', () => {
  it('uses the measured registration when the harvest wrote one', () => {
    const r = traceRegistration({ registration_px: { tx: 12, ty: 3, baseline_row: 58 }, xh_px: 31 }, sample());
    expect(r).toEqual({ xh: 31, tx: 12, baselineRow: 61 });
  });

  // A hand-written row may carry no fit context at all; the sidecar lineature
  // keeps it displayable (x-height = Grundlinie − Mittellinie).
  it('falls back to the sidecar lineature without measurements', () => {
    expect(traceRegistration({}, sample())).toEqual({ xh: 30, tx: 0, baselineRow: 60 });
  });
});

describe('crop ↔ trace mapping', () => {
  const r = traceRegistration({ registration_px: { tx: 12, ty: 3, baseline_row: 58 }, xh_px: 31 }, sample());

  it('puts the baseline on v = 0 and the midband on v = 1', () => {
    expect(traceToCrop(r, [0, 0])).toEqual([12, 61]);
    expect(traceToCrop(r, [0, 1])).toEqual([12, 30]);
  });

  it('round-trips a pointer sample', () => {
    const px: TracePoint = [143.5, 22.25];
    const [u, v] = cropToTrace(r, px);
    const [x, y] = traceToCrop(r, [u, v]);
    expect(x).toBeCloseTo(px[0], 9);
    expect(y).toBeCloseTo(px[1], 9);
  });

  // The matrix is the display twin of traceToCrop — a drift between the two
  // would offset the drawn line from the saved one.
  it('matches the SVG matrix', () => {
    expect(registrationMatrix(r)).toBe('matrix(31 0 0 -31 12 61)');
  });
});

describe('strokePathD', () => {
  it('emits a moveto followed by linetos', () => {
    expect(strokePathD([[0, 0], [1, 0.5]])).toBe('M0,0 L1,0.5');
  });
});

describe('sanitizeStrokes', () => {
  it('drops stray taps and rounds the survivors', () => {
    expect(
      sanitizeStrokes([
        [[0.123456, 0.5]],
        [
          [0.123456, 0.5],
          [1.000049, -0.25],
        ],
      ]),
    ).toEqual([
      [
        [0.1235, 0.5],
        [1, -0.25],
      ],
    ]);
  });

  it('clamps coordinates into the schema range', () => {
    const [stroke] = sanitizeStrokes([
      [
        [-500, 0],
        [500, 0],
      ],
    ]);
    expect(stroke).toEqual([
      [-MAX_TRACE_COORD, 0],
      [MAX_TRACE_COORD, 0],
    ]);
  });

  it('decimates an over-long stroke down to the point cap, keeping its end', () => {
    const long: TracePoint[] = Array.from({ length: MAX_STROKE_POINTS + 500 }, (_, i) => [i / 1000, 0]);
    const [stroke] = sanitizeStrokes([long]);
    expect(stroke.length).toBeLessThanOrEqual(MAX_STROKE_POINTS);
    expect(stroke[stroke.length - 1]).toEqual(long[long.length - 1]);
  });

  it('reports nothing savable when only taps were captured', () => {
    expect(sanitizeStrokes([[[0, 0]]])).toEqual([]);
  });
});
