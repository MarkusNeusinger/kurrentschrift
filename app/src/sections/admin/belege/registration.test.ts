import { describe, expect, it } from 'vitest';

import type { WordSampleOut } from '@/lib/api';

import {
  MAX_STROKE_POINTS,
  MAX_TRACE_COORD,
  cropToTrace,
  frameStale,
  reanchorStrokes,
  registrationMatrix,
  sanitizeStrokes,
  strokePathD,
  traceRegistration,
  traceToCrop,
  warpTraceStrokes,
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

describe('frameStale', () => {
  it('accepts the sidecar frame and small drift, flags the exporter-gate breaches', () => {
    const s = sample(); // baseline 60, midband 30 → xh 30
    expect(frameStale({ xh: 30, tx: 5, baselineRow: 60 }, s)).toBe(false);
    expect(frameStale({ xh: 30.5, tx: 5, baselineRow: 63.9 }, s)).toBe(false); // inside 0.51 / 4 px
    expect(frameStale({ xh: 30, tx: 5, baselineRow: 65 }, s)).toBe(true); // baseline drifted > 4 px
    expect(frameStale({ xh: 31, tx: 5, baselineRow: 60 }, s)).toBe(true); // xh drifted > 0.51 px
  });
});

describe('reanchorStrokes', () => {
  it('keeps every point on its crop pixel while moving it into the new frame', () => {
    const from = { xh: 30, tx: 10, baselineRow: 80 };
    const to = { xh: 32, tx: 10, baselineRow: 60 };
    const stroke: TracePoint[] = [
      [0, 0],
      [1.2, 0.8],
    ];
    const [out] = reanchorStrokes([stroke], from, to);
    stroke.forEach((p, i) => {
      const before = traceToCrop(from, p);
      const after = traceToCrop(to, out[i]);
      expect(after[0]).toBeCloseTo(before[0], 9);
      expect(after[1]).toBeCloseTo(before[1], 9);
    });
    // The coordinates themselves changed — the frame moved under the line.
    expect(out[0]).not.toEqual(stroke[0]);
  });
});

describe('warpTraceStrokes', () => {
  const line: TracePoint[][] = [
    [
      [0, 0],
      [0.5, 0],
      [1, 0],
      [2, 0],
    ],
  ];

  it('moves the grabbed point fully and eases out to the rim', () => {
    const [warped] = warpTraceStrokes(line, [0.5, 0], 0, 0.2, 0.6);
    expect(warped[1]).toEqual([0.5, 0.2]); // at the grab: full delta
    // Halfway to the rim moves by smoothstep(0.5) = 0.5 of the delta …
    const t = 1 - 0.5 / 0.6;
    expect(warped[2][1]).toBeCloseTo(0.2 * t * t * (3 - 2 * t), 9);
    // … and outside the radius nothing moves at all.
    expect(warped[3]).toEqual([2, 0]);
    expect(warped[0][1]).toBeGreaterThan(0);
  });

  it('never inserts, drops, merges or reorders — structure is bench-measured', () => {
    const strokes: TracePoint[][] = [
      [
        [0, 0],
        [1, 0],
      ],
      [
        [0.4, 1.2],
        [0.6, 1.2],
      ],
    ];
    const warped = warpTraceStrokes(strokes, [0.5, 1.2], 0.1, 0, 0.3);
    expect(warped.length).toBe(strokes.length);
    expect(warped.map((s) => s.length)).toEqual(strokes.map((s) => s.length));
    // The snapshot itself stays untouched — the editor re-warps it per move.
    expect(strokes[1][0]).toEqual([0.4, 1.2]);
  });
});
