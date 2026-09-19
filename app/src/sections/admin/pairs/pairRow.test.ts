import { describe, expect, it } from 'vitest';

import type { GlyphPairOut } from '@/lib/api';

import { findPairRow, pairCellKey, pairRowsByKeys } from './pairRow';

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

describe('pairRowsByKeys', () => {
  it('badges a cell with the row its editor opens', () => {
    const rows = [row('e', 'n'), row('a', 'b')];
    const byKeys = pairRowsByKeys(rows);
    expect(byKeys.get(pairCellKey('e', 'n'))).toBe(rows[0]);
    expect(byKeys.get(pairCellKey('a', 'b'))).toBe(rows[1]);
  });

  it('lets no other variant overwrite the rendered one', () => {
    // The list route orders by variant ASCENDING, so the foreign row arrives
    // last — which is exactly when a plain Map would let it win the cell.
    const wanted = row('a', 'b');
    const foreign = { ...row('a', 'b', 1), approved: true };
    const byKeys = pairRowsByKeys([wanted, foreign]);
    expect(byKeys.get(pairCellKey('a', 'b'))).toBe(wanted);
    expect(byKeys.size).toBe(1);
  });

  it('leaves a cell unbadged when only a foreign variant exists', () => {
    expect(pairRowsByKeys([row('a', 'b', 1)]).size).toBe(0);
    expect(pairRowsByKeys([]).size).toBe(0);
  });
});
