import { describe, expect, it } from 'vitest';

import type { GlyphPairOut } from '@/lib/api';

import { findPairRow } from './pairRow';

const row = (left_key: string, right_key: string, variant = 0): GlyphPairOut => ({
  left_key,
  right_key,
  variant,
  geometry: { offset: [0.3, 0], connector: [] },
  provenance: 'authored',
  provenance_source_id: null,
  specimen_id: null,
  approved: false,
});

describe('findPairRow', () => {
  const rows = [row('e', 'n'), row('a', 'b'), row('a', 'b', 1)];

  it('finds the row of exactly this pair', () => {
    expect(findPairRow(rows, 'e', 'n')).toBe(rows[0]);
  });

  it('answers null for a pair with no override — the normal case', () => {
    expect(findPairRow(rows, 'l', 'e')).toBeNull();
    expect(findPairRow([], 'e', 'n')).toBeNull();
  });

  it('does not hand back another variant of the same pair', () => {
    expect(findPairRow(rows, 'a', 'b')).toBe(rows[1]);
    expect(findPairRow(rows, 'a', 'b', 2)).toBeNull();
  });

  it('never confuses the two sides of a pair', () => {
    expect(findPairRow(rows, 'n', 'e')).toBeNull();
  });
});
