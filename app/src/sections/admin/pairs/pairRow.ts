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

export function findPairRow(
  rows: GlyphPairOut[],
  leftKey: string,
  rightKey: string,
  variant = 0,
): GlyphPairOut | null {
  return rows.find((r) => r.left_key === leftKey && r.right_key === rightKey && r.variant === variant) ?? null;
}
