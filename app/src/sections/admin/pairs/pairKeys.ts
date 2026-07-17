// The shaped glyph_keys behind a two-letter pair text — null when the pair
// folds into a closed-set ligature (one slot: ch, ck, …), which has no join
// to edit. Shared by the pair matrix and the word-comparison pair cards
// (kept out of the component files for react-refresh).

import { shapeText } from '@/domain/shaping';

export function pairKeysOf(text: string): [string, string] | null {
  const keyed = shapeText(text).filter((s) => s.key);
  if (keyed.length !== 2) return null;
  return [keyed[0].key!, keyed[1].key!];
}
