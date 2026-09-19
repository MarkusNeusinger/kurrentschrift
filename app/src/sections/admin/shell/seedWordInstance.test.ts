// Unit cover for the word editor's starting point on a Wortprobe that has
// never been traced.
//
// The seed exists so the TESTED write flow is called rather than rebuilt: the
// dialog keeps its props, its save body and its suites, and it is handed a row
// in the shape it already takes. That only works if the seed is right in four
// places, and each of them is a real failure otherwise:
//
// * identity (kind, specimen_id, word) comes off the sample — a mismatch would
//   upsert the trace onto a different occurrence;
// * `slots` is the shaper's list, the same one the harvest stores, because the
//   dialog sends it back verbatim and the API rejects an unknown registry key;
// * `strokes` is empty, so the save gate stays shut until something is drawn;
// * the registration is the sidecar's own lineature, so the editor's frame gate
//   reads the seed as current and does not open on „Rahmen veraltet" and a
//   pre-dirtied canvas.

import { describe, expect, it } from 'vitest';

import type { WordSampleOut } from '@/lib/api';
import { frameStale, traceRegistration } from '@/sections/admin/belege/registration';
import { seedWordInstance } from './model';

const SAMPLE = {
  id: 'muß-2',
  word: 'muß',
  kind: 'word',
  baseline_y: 68,
  midband_y: 38, // xh = 30 px
} as unknown as WordSampleOut;

describe('seedWordInstance', () => {
  it('takes its identity off the sample', () => {
    const seed = seedWordInstance(SAMPLE);
    expect(seed.kind).toBe('word');
    expect(seed.specimen_id).toBe('muß-2');
    expect(seed.word).toBe('muß');
  });

  it('labels the slots the way the shaper does — the harvest’s own list', () => {
    expect(seedWordInstance(SAMPLE).slots).toEqual(['m', 'u', 'sz']);
    expect(seedWordInstance({ ...SAMPLE, word: 'lesen' }).slots).toEqual(['l', 'e', 'longs', 'e', 'n']);
  });

  it('starts empty and marks what a save would write', () => {
    const seed = seedWordInstance(SAMPLE);
    expect(seed.strokes).toEqual([]);
    expect(seed.provenance).toBe('authored');
    // No sibling row to inherit a hand from: the dialog resolves one itself and
    // keeps saving disabled, with a reason, when nothing does.
    expect(seed.hand_id).toBeNull();
    expect(seed.updated_at).toBeNull();
  });

  it('registers on the sidecar’s lineature, so the frame gate reads it as current', () => {
    const seed = seedWordInstance(SAMPLE);
    expect(seed.measurements).toEqual({
      registration_px: { tx: 0, ty: 0, baseline_row: 68 },
      xh_px: 30,
    });
    expect(frameStale(traceRegistration(seed.measurements, SAMPLE), SAMPLE)).toBe(false);
  });

  it('carries no fit numbers — nothing has been fitted', () => {
    const { measurements } = seedWordInstance(SAMPLE);
    expect(measurements.fitted_slots).toBeUndefined();
    expect(measurements.unfitted_slots).toBeUndefined();
    expect(measurements.geo_rmse_px_by_slot).toBeUndefined();
  });
});
