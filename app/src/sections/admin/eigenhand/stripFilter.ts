// The client half of the strip search: which WORD BOX of a listed row answers
// the filter the coverage grid or the search box set.

import type { EigenhandStripBox, EigenhandStripFilter } from '@/lib/api';

/**
 * Does one box hold the filter — the client half of the server's strip-level
 * match (`coverage.matches_item`). Plain `toLowerCase()`, the same simple
 * mapping as the server's `str.lower()`: a locale-aware or folding variant
 * (ß → ss, the Turkish i) would let the two halves disagree.
 */
export function boxMatches(box: EigenhandStripBox, filter: EigenhandStripFilter): boolean {
  if (filter.wort && !box.word.toLowerCase().includes(filter.wort.toLowerCase())) return false;
  if (filter.item) {
    const wanted = filter.item;
    if (wanted.includes('>') || wanted.includes('@')) return box.items.includes(wanted);
    return box.items.some((item) => item.startsWith(`${wanted}@`));
  }
  return true;
}
