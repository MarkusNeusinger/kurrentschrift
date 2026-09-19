// The Auftragskorb drawer's filter and grouping, kept out of the panel so both
// can be pinned by a unit test instead of by reading JSX.
//
// Why the filter is CLIENT-side: the panel already reads every row of the
// source in one call (`listWorkItems(sourceId, undefined)`), and the title's
// „n offen" plus the header badge have to count the whole basket, not the
// current view. A server-side filter would therefore need a second read for
// the counts and would buy nothing — the basket is a handful of prose notes,
// never a table of thousands.
//
// Why the grouping stays by STATUS and the Stufe is only a filter: `stage` is
// the DIAGNOSIS, and the API demands it at a transition rather than at filing
// (`_REQUIRED_FIELDS` in `api/routers/work_items.py` — `done` and `returned`;
// a target-less `note` closes on its resolution alone). A freshly filed row
// therefore carries `stage === null` — that is the bulk of the queue — while a
// handed-back row names one and an `open` row rejected after a diagnosed round
// keeps the stage it was sent back over. Grouping by stage would drop all those
// undiagnosed rows into one nameless bucket AND could no longer keep the
// handed-back ones on top. The honest consequence, pinned by the tests: a
// chosen Stufe skips every row that has not been diagnosed yet.

import type { WorkItemKind, WorkItemOut, WorkItemStage, WorkItemStatus } from '@/lib/api';

export type KorbFilter = {
  status: WorkItemStatus | 'all';
  // The Korb-Ebene — „wo gesehen", the level the ⚑ was raised on.
  kind: WorkItemKind | 'all';
  // The diagnosed stage of the writing path; only a row some transition has
  // already diagnosed carries one (see the header).
  stage: WorkItemStage | 'all';
};

/** Everything through — the state the drawer opens in. */
export const KORB_FILTER_ALL: KorbFilter = { status: 'all', kind: 'all', stage: 'all' };

export const isKorbFilterAll = (filter: KorbFilter): boolean =>
  filter.status === 'all' && filter.kind === 'all' && filter.stage === 'all';

/**
 * Handed back first (those wait on the author), then the queue, then what a
 * session is currently working on; the archive last. „`returned` oben" is a
 * property of this constant rather than a line of JSX.
 */
export const KORB_GROUP_ORDER: readonly WorkItemStatus[] = ['returned', 'open', 'ack', 'done'] as const;

/**
 * The stages the Stufe select offers, in the triage order §5 prescribes — the
 * declaration order of `WorkItemStage`. Data here rather than `Object.keys` of
 * the locale record: a `Record<WorkItemStage, string>` guarantees that every
 * stage is NAMED, never that the object carries nothing else, so a renamed
 * stage whose old locale key survived would ship as a phantom option that can
 * never match — and the menu order would be a side effect of how the locale
 * file happens to be written. The test pins both against the locale.
 */
export const KORB_FILTER_STAGES = [
  'chart_ductus',
  'laufform',
  'join_rule',
  'composition',
  'pair_override',
  'word_trace',
  'landmark_detector',
  'not_reproducible',
] as const satisfies readonly WorkItemStage[];

/** The three selects ANDed. A row with no diagnosed stage never matches a chosen one. */
export const matchesKorbFilter = (item: WorkItemOut, filter: KorbFilter): boolean =>
  (filter.status === 'all' || item.status === filter.status) &&
  (filter.kind === 'all' || item.kind === filter.kind) &&
  (filter.stage === 'all' || item.stage === filter.stage);

/**
 * Whether the `done` archive is on screen. Choosing „Erledigt" in the status
 * filter IS the request to see it, so it wins over the „erledigte anzeigen"
 * switch — two controls saying nearly the same thing would otherwise leave the
 * author with a filter that visibly selects nothing. The switch keeps
 * governing every other view.
 */
export const korbArchiveVisible = (filter: KorbFilter, showDone: boolean): boolean =>
  showDone || filter.status === 'done';

/**
 * Whether the archive gate ALONE is holding rows back — the only case in which
 * asking the author to turn „erledigte anzeigen" on changes anything on screen.
 * The mere existence of a `done` row is not enough: under status „Offen", or a
 * Ebene the archived rows do not carry, the switch is powerless and a hint to
 * flip it would name a cause that is not the one (the Leerzustands-Regel of
 * glossar.md, „Zwei Stillen").
 */
export const korbArchiveHides = (rows: WorkItemOut[], filter: KorbFilter, showDone: boolean): boolean =>
  !korbArchiveVisible(filter, showDone) && rows.some((row) => row.status === 'done' && matchesKorbFilter(row, filter));

export type KorbGroup = { key: WorkItemStatus; rows: WorkItemOut[] };

/**
 * The filtered rows in the four status groups, empty groups dropped and the
 * remaining ones in `KORB_GROUP_ORDER`. Row order inside a group is the
 * server's (`id` ascending, oldest first).
 */
export function groupKorb(rows: WorkItemOut[], filter: KorbFilter, showDone: boolean): KorbGroup[] {
  const matched = rows.filter((row) => matchesKorbFilter(row, filter));
  const archive = korbArchiveVisible(filter, showDone);
  return KORB_GROUP_ORDER.filter((key) => key !== 'done' || archive)
    .map((key) => ({ key, rows: matched.filter((row) => row.status === key) }))
    .filter((group) => group.rows.length > 0);
}
