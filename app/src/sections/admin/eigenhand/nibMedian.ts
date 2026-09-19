// The one statistic the Eigenhand page can derive from what it already holds:
// the hand's pen, read back off its own writing.
//
// `befund.nib.units` is the median half width on the medial axis of ONE
// Fassung, in x-heights (core/eigenhand/befund.py). There is no per-hand
// aggregate route, so the hand's figure is the median of the Fassung medians —
// a median of medians, which is what „welche Feder schreibt diese Hand" asks
// for and robust against the one badly scanned strip.
//
// The critical rule is what counts as a reading. `befund.py` writes
// `nib_units = summary["nib_units"] or 0.0`, so an unmeasured Fassung carries
// a literal 0.0, and a Fassung filed before the Befund existed carries no
// `befund` at all. Both are ABSENT readings, not thin pens: averaging them in
// would pull the number towards zero and quietly invent a hairline hand.
//
// This is the twin of `core.eigenhand.befund.hand_nib_median`, over the same
// set: the listing states a Befund only for ACCEPTED Fassungen
// (`befunde_of_strip`), which is the filter the Python side applies too, and
// both drop a falsy width. NOT read off `befund.nib.referenz`, which is the
// same number where it exists and silently the PLATE's pen where it does not
// (`reference = nib_referenz or PLATE_PEN_HALF_WIDTH_UNITS`) — a hand with
// nothing measured would then be reported as writing a century-old plate's
// nib. Measured in the browser against a seeded hand: three readings 0.030 ·
// 0.046 · 0.038 give 0.038 here and 0.038 as the server's own `referenz`.

import type { EigenhandStrip } from '@/lib/api';

export type NibMedian = {
  /** The hand's median half width in x-heights, `null` when nothing was measured. */
  units: number | null;
  /** How many Fassungen the median rests on — the honesty half of the number. */
  count: number;
};

const reading = (strip: EigenhandStrip): number | null => {
  const value = strip.befund?.nib?.units;
  // `nib` is a loose record (numbers for a tooltip, not a contract), so the
  // type check is real work: a string or a null must not become NaN here.
  return typeof value === 'number' && Number.isFinite(value) && value > 0 ? value : null;
};

export function nibMedian(strips: readonly EigenhandStrip[]): NibMedian {
  const values = strips.map(reading).filter((value): value is number => value !== null);
  if (!values.length) return { units: null, count: 0 };
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  const units = sorted.length % 2 === 1 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  return { units, count: sorted.length };
}
