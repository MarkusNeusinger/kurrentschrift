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

// Would this row actually change what the engine writes?
//
// A null distance has two very different causes, and only one of them is a
// change: no stored running form at all (this glyph GAINS one) versus a stored
// one whose anchor count disagrees with the median — which the endpoint reports
// as `anchor_count` and skips. Counting the second as a change would have the
// summary over-report and push the admin toward a confirmation on work that
// will not happen.
export const willChange = (row: Preview): boolean => row.creates || (row.dev !== null && row.dev > 0);
