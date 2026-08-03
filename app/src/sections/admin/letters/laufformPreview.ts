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

// Below this many occurrences a median is one writing's idiosyncrasy as much as
// a form model. Since the aggregate gate is `min_n = 1` (issue #273) such rows
// EXIST — seeing them is measurement, nothing renders — so the caution moved
// here, to the one step that renders: they are marked in the preview table and
// start out unselected. Nothing forbids applying them; the human decides with
// the number in front of them.
export const LOW_N = 3;

export const isLowN = (row: Preview): boolean => row.nInstances < LOW_N;

// Which rows a freshly opened dialog proposes to write: the well-attested ones.
// A deliberate proposal, not a filter — every row stays selectable.
export const defaultSelection = (rows: Preview[]): string[] =>
  rows.filter((row) => !isLowN(row)).map((row) => row.glyphKey);

// Would this row actually change what the engine writes?
//
// A null distance has two very different causes, and only one of them is a
// change: no stored running form at all (this glyph GAINS one) versus a stored
// one whose anchor count disagrees with the median — which the endpoint reports
// as `anchor_count` and skips. Counting the second as a change would have the
// summary over-report and push the admin toward a confirmation on work that
// will not happen.
export const willChange = (row: Preview): boolean => row.creates || (row.dev !== null && row.dev > 0);
