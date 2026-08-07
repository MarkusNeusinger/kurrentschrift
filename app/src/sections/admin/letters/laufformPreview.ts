// What `apply-laufform` would do, read off the aggregate rows the letter view
// already holds — so the confirmation dialog's preview costs no extra request
// and cannot disagree with the freshness chips shown beside it.
//
// Pure, and in its own file like the other shared helpers (`shell/focus.ts`,
// `pairs/pairKeys.ts`, `belege/registration.ts`), so react-refresh only ever
// sees components in the component file.

import type { AggregateOut } from '@/lib/api';

export interface Preview {
  glyphKey: string;
  nInstances: number;
  // Distance between the median and the running form in use, x-height units.
  // Null has TWO causes — see `willChange`.
  dev: number | null;
  // No stored running form yet: this glyph gains one.
  creates: boolean;
}

export function previewOf(aggregates: AggregateOut[]): Preview[] {
  return (
    aggregates
      // Only base-variant aggregates feed the derived row (a variant-100
      // aggregate would let the Laufform derive from itself) — the endpoint
      // skips the rest, so the preview must not promise them either.
      .filter((agg) => agg.variant === 0)
      .map((agg) => ({
        glyphKey: agg.glyph_key,
        nInstances: agg.n_instances,
        dev: agg.laufform_dev_xh,
        creates: agg.laufform_anchors === null,
      }))
      .sort((a, b) => (b.dev ?? Infinity) - (a.dev ?? Infinity) || a.glyphKey.localeCompare(b.glyphKey))
  );
}

// Below this many occurrences the per-anchor median stops being a form model:
// at two occurrences it is their MEAN, so one blown-up fitted anchor lands in
// the written form at half its amplitude (this is how the capital S got its
// spike). Since the aggregate gate is `min_n = 1` (issue #273) such rows EXIST
// — seeing them is measurement, nothing renders — so the caution belongs at the
// one step that renders.
//
// MIRROR of `core.aggregate.LAUFFORM_MIN_OCCURRENCES`, which the endpoint now
// ENFORCES: this list shapes the PROPOSAL, the server decides the write. Keep
// the two numbers equal — a client that proposed below the server's floor would
// promise writes that come back as `below_min_occurrences` skips.
export const LOW_N = 3;

export const isLowN = (row: Preview): boolean => row.nInstances < LOW_N;

// Which rows a freshly opened dialog proposes to write: the well-attested ones.
// A deliberate proposal, not a filter — every row stays selectable.
export const defaultSelection = (rows: Preview[]): string[] =>
  rows.filter((row) => !isLowN(row)).map((row) => row.glyphKey);

// The floor to send with a run, given what the human actually ticked.
//
// Undefined leaves the endpoint on its own default — the safe case, and the one
// every ordinary run takes. A ticked thin row is the deliberate exception the
// doctrine always allowed, and lowering the floor to that row's own count is
// how the REQUEST states it: the intent is recorded on the wire instead of
// being a check nobody ran. It never drops below 1 (the endpoint's `ge=1`), and
// a tick on a well-attested row alone never lowers anything.
export const minOccurrencesFor = (rows: Preview[], selected: ReadonlySet<string>): number | undefined => {
  const thin = rows.filter((row) => selected.has(row.glyphKey) && isLowN(row));
  if (thin.length === 0) return undefined;
  return Math.max(1, Math.min(...thin.map((row) => row.nInstances)));
};

// Would this row actually change what the engine writes?
//
// A null distance has two very different causes, and only one of them is a
// change: no stored running form at all (this glyph GAINS one) versus a stored
// one whose anchor count disagrees with the median — which the endpoint reports
// as `anchor_count` and skips. Counting the second as a change would have the
// summary over-report and push the admin toward a confirmation on work that
// will not happen.
export const willChange = (row: Preview): boolean => row.creates || (row.dev !== null && row.dev > 0);
