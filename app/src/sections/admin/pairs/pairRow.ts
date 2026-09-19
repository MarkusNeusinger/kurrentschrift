// Picking one pair's override row out of the style's list.
//
// The editor used to ask for the single row (GET /pairs/{l}/{r}) and treat its
// 404 as „no override yet" — the normal case, and one the browser logs as a red
// network line on every open. The list route answers the same rows including
// their geometry, the matrix loads it anyway, so the row is picked here instead
// of asked for.
//
// `variant` is part of the identity: the single read defaults to variant 0 and
// the editor only ever writes 0, while the list returns every variant of the
// style — without the check a future variant row could be edited in place of
// the one on screen.

import type { GlyphPairOut } from '@/lib/api';

// The one variant the admin edits and the composer renders: the single read
// defaults to it, `approved_for_pairs` selects it for /write/word, and the
// editor only ever writes it. Everything on screen has to mean THIS row.
export const DEFAULT_PAIR_VARIANT = 0;

export function findPairRow(
  rows: GlyphPairOut[],
  leftKey: string,
  rightKey: string,
  variant = DEFAULT_PAIR_VARIANT,
): GlyphPairOut | null {
  return rows.find((r) => r.left_key === leftKey && r.right_key === rightKey && r.variant === variant) ?? null;
}

// The matrix cell a pair's badge belongs to.
export const pairCellKey = (leftKey: string, rightKey: string): string => `${leftKey}|${rightKey}`;

// The badge row per cell, keyed for lookup. The variant filter is load-bearing,
// not defensive: the list route orders by variant ASCENDING and a Map keeps the
// last write, so a variant-1 row would badge a cell whose editor opens variant 0
// and whose geometry the composer renders from variant 0 — the overview would
// report an approval that never reaches the page.
export function pairRowsByKeys(rows: GlyphPairOut[]): Map<string, GlyphPairOut> {
  const byKeys = new Map<string, GlyphPairOut>();
  for (const r of rows) {
    if (r.variant === DEFAULT_PAIR_VARIANT) byKeys.set(pairCellKey(r.left_key, r.right_key), r);
  }
  return byKeys;
}
