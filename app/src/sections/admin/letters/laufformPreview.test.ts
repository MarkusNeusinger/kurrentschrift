import { describe, expect, it } from 'vitest';

import type { AggregateOut } from '@/lib/api';

import { LOW_N, defaultSelection, isLowN, previewOf, willChange } from './laufformPreview';

// Only the fields the preview reads; the rest of AggregateOut is irrelevant
// here and would only make the cases harder to read.
const agg = (over: Partial<AggregateOut> & Pick<AggregateOut, 'glyph_key'>): AggregateOut =>
  ({
    glyph: over.glyph_key,
    variant: 0,
    cluster_center: [],
    hull: {},
    mean_stats: {},
    n_instances: 5,
    laufform_anchors: null,
    laufform_dev_xh: null,
    ...over,
  }) as AggregateOut;

describe('previewOf', () => {
  it('keeps only base-variant aggregates — a Laufform may not derive from itself', () => {
    const rows = previewOf([agg({ glyph_key: 'a' }), agg({ glyph_key: 'b', variant: 100 })]);
    expect(rows.map((r) => r.glyphKey)).toEqual(['a']);
  });

  it('marks a row without a stored running form as a creation', () => {
    expect(previewOf([agg({ glyph_key: 'a' })])[0].creates).toBe(true);
    expect(previewOf([agg({ glyph_key: 'a', laufform_anchors: [[0, 0]] })])[0].creates).toBe(false);
  });

  it('sorts the largest distance first, unknown distances on top', () => {
    const rows = previewOf([
      agg({ glyph_key: 'small', laufform_anchors: [[0, 0]], laufform_dev_xh: 0.01 }),
      agg({ glyph_key: 'big', laufform_anchors: [[0, 0]], laufform_dev_xh: 0.4 }),
      agg({ glyph_key: 'new' }),
    ]);
    expect(rows.map((r) => r.glyphKey)).toEqual(['new', 'big', 'small']);
  });
});

describe('low-n marking and the proposed selection', () => {
  it('marks a median that rests on fewer than LOW_N occurrences', () => {
    expect(isLowN({ glyphKey: 'A', nInstances: 1, dev: null, creates: true })).toBe(true);
    expect(isLowN({ glyphKey: 'A', nInstances: LOW_N - 1, dev: null, creates: true })).toBe(true);
    expect(isLowN({ glyphKey: 'n', nInstances: LOW_N, dev: null, creates: true })).toBe(false);
  });

  it('proposes the well-attested rows and leaves the thin ones unticked', () => {
    const rows = previewOf([
      agg({ glyph_key: 'n', n_instances: 12 }),
      agg({ glyph_key: 'A', n_instances: 1 }),
      agg({ glyph_key: 'e', n_instances: LOW_N }),
    ]);
    expect(defaultSelection(rows).sort()).toEqual(['e', 'n']);
  });

  it('proposes nothing when every key is thin — but the rows stay applicable', () => {
    const rows = previewOf([agg({ glyph_key: 'A', n_instances: 1 }), agg({ glyph_key: 'B', n_instances: 2 })]);
    expect(defaultSelection(rows)).toEqual([]);
    expect(rows).toHaveLength(2);
  });
});

describe('willChange', () => {
  it('counts a first write and a drifted running form', () => {
    expect(willChange({ glyphKey: 'a', nInstances: 5, dev: null, creates: true })).toBe(true);
    expect(willChange({ glyphKey: 'a', nInstances: 5, dev: 0.05, creates: false })).toBe(true);
  });

  it('does not count a running form that already equals the median', () => {
    expect(willChange({ glyphKey: 'a', nInstances: 5, dev: 0, creates: false })).toBe(false);
  });

  it('does not count an incomparable row — the endpoint skips it, it changes nothing', () => {
    // Stored running form present, but its anchor count disagrees with the
    // median: `anchor_count` in the endpoint's skip list, not a change.
    expect(willChange({ glyphKey: 'a', nInstances: 5, dev: null, creates: false })).toBe(false);
  });
});
