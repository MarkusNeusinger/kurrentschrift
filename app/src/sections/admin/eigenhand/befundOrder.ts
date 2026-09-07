// How the Streifen-Befund reads on screen: the suggestion's severity, its
// colour, and the „weakest first" order.
//
// One table, two uses — the chip's colour and the sort's rank come from the
// same `sauber < brauchbar < neu schreiben` ladder, so a chip and its place in
// the list can never disagree. Kept beside the panel rather than inside it so
// the order is testable without rendering: the order IS the answer to „what do
// I write again", and a comparator that quietly sorts the wrong way would be
// invisible in a screenshot.

import type { EigenhandStrip, EigenhandVorschlag } from '@/lib/api';

export const VORSCHLAG_SEVERITY: Record<EigenhandVorschlag, number> = {
  sauber: 0,
  brauchbar: 1,
  'neu schreiben': 2,
};

export const VORSCHLAG_COLOR: Record<EigenhandVorschlag, 'success' | 'warning' | 'error'> = {
  sauber: 'success',
  brauchbar: 'warning',
  'neu schreiben': 'error',
};

/**
 * Weakest first: the severest suggestion, then the lowest composite. A Fassung
 * with no Befund sorts LAST — a missing reading is not a bad one, and putting
 * it at the top of a rewrite list would send the author to rewrite a strip
 * nobody measured.
 */
export function byBefund(a: EigenhandStrip, b: EigenhandStrip): number {
  const severity = (row: EigenhandStrip) => (row.befund ? VORSCHLAG_SEVERITY[row.befund.vorschlag] : -1);
  const guete = (row: EigenhandStrip) => row.befund?.guete ?? Number.POSITIVE_INFINITY;
  return (
    severity(b) - severity(a) ||
    guete(a) - guete(b) ||
    a.strip.localeCompare(b.strip) ||
    a.fassung.localeCompare(b.fassung)
  );
}
