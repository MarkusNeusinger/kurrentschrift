// The sensors one word box's Bahn carries — read out of an UNTYPED blob.
//
// `meta` is free-form JSON the whole way down: `core/eigenhand/pfad.py` stores
// what was pushed without validating it, `api/schemas.py` types it as
// `dict[str, Any]`, and the wire type mirrors that as `Record<string, unknown>`.
// Typing `meta.tintenpfad` over there would claim a contract the server does
// not enforce, so the reading happens here instead — once, defensively, and
// testable without rendering a panel.
//
// The one trap this module exists for: `ink_unvisited_share: 0` is the BEST
// reading a Bahn can get, and `tools/eigenhand/pfad.py` projects every sensor
// with `.get(key)`, so a key the follower never emitted is stored as `null`.
// A `||` reader collapses both into one 0 — and the unmeasured box then claims
// the perfect path. Zero and „never measured" are kept apart here so the panel
// can say which of the two it is looking at.
//
// A reading, never a verdict: these are the numbers, and the verdict is the
// Tintentreue traffic light's (#638, admin-redesign.md V26), shown in the
// Nachfahr-Liste and on the gallery tile.

import type { EigenhandPfad } from '@/lib/api';

export type PfadRohzahlen = {
  /** Share of the ink skeleton the Bahn never travels, 0..1 — „Tinte ohne Bahn". */
  inkUnvisitedShare: number | null;
  /** How often the decoder took the pen off the paper — „Absetzer". */
  paperLifts: number | null;
  /** Strand changes across paper — „Sprünge". */
  jumps: number | null;
  /** Reversals on one and the same strand — „Haken". */
  hairpins: number | null;
  /**
   * Whether the Bahn carries any sensor at all. `false` is a hand-traced box
   * or a run from before the follower emitted them — never four zeros.
   */
  measured: boolean;
};

/**
 * A finite number, or `null` for everything else the blob may hold.
 *
 * `NaN` and `Infinity` are refused along with strings and booleans: they are
 * `typeof 'number'` and would render as „NaN %" rather than as the missing
 * reading they stand for.
 */
function reading(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

/** The four numbers of one stored path, plus whether any of them was measured. */
export function pfadRohzahlen(pfad: EigenhandPfad): PfadRohzahlen {
  const block = pfad.meta?.tintenpfad;
  // An array is an object too, and a follower writing a list here would
  // otherwise read as an empty sensor set with no complaint.
  const sensors: Record<string, unknown> =
    typeof block === 'object' && block !== null && !Array.isArray(block) ? (block as Record<string, unknown>) : {};
  const readings = {
    inkUnvisitedShare: reading(sensors.ink_unvisited_share),
    paperLifts: reading(sensors.paper_lifts),
    jumps: reading(sensors.jumps),
    hairpins: reading(sensors.hairpins),
  };
  return { ...readings, measured: Object.values(readings).some((value) => value !== null) };
}
