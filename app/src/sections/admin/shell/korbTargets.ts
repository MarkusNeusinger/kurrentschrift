// What the open Auftragskorb rows point AT, counted per subject — so a work
// list can say „dieser Buchstabe hat 2 offene Aufträge" without a second read.
//
// The rows are already in the browser: `KorbContext` fetches every work item of
// the source for its badge (`KorbContext.tsx`) and used to keep only the count.
// Counting them by target here is the whole „DERIVABLE" of the plan's §7.2 row
// „offene Korb-Aufträge je Buchstabe" — no route, no request, no schema.
//
// The target rules are the ones the basket's own links already follow
// (`KorbPanel.tsx`, `workItemUrl`), so a chip and the link it promises can
// never disagree:
//   letter | landmark → its glyph (a landmark is an observation ON a letter)
//   pair              → "left→right", the key the matrix and the join view use
//   word              → the word TEXT (a row filed by specimen id alone names
//                       no subject a list can key on)
//   note              → nothing; a general note points at no subject by
//                       definition, and counting it somewhere would invent one.
//
// „Offen" means what the badge means: `open` plus `returned` — a handed-back
// row is work waiting, not work done.

import type { WorkItemOut } from '@/lib/api';

export type KorbCounts = {
  byGlyph: Map<string, number>;
  byPair: Map<string, number>;
  byWord: Map<string, number>;
};

/** The key the join surfaces use for one ordered pair. */
export const pairCountKey = (leftKey: string, rightKey: string): string => `${leftKey}→${rightKey}`;

const bump = (map: Map<string, number>, key: string): void => {
  map.set(key, (map.get(key) ?? 0) + 1);
};

/**
 * Open and handed-back rows counted onto their subjects. `null` (the basket
 * read has not answered, or it 401'd) stays null all the way to the chip: a
 * missing read is not „keine Aufträge".
 */
export function korbCountsOf(items: WorkItemOut[] | null): KorbCounts | null {
  if (items === null) return null;
  const counts: KorbCounts = { byGlyph: new Map(), byPair: new Map(), byWord: new Map() };
  for (const item of items) {
    if (item.status !== 'open' && item.status !== 'returned') continue;
    if (item.kind === 'letter' || item.kind === 'landmark') {
      if (item.glyph_key) bump(counts.byGlyph, item.glyph_key);
    } else if (item.kind === 'pair') {
      if (item.left_key && item.right_key) bump(counts.byPair, pairCountKey(item.left_key, item.right_key));
    } else if (item.kind === 'word') {
      if (item.word) bump(counts.byWord, item.word);
    }
  }
  return counts;
}
