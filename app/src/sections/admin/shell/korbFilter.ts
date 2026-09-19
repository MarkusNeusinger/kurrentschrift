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
// Why the grouping stays by STATUS and the Stufe is only a filter: the API
// asks for a `stage` when a row closes (`_REQUIRED_FIELDS` in
// `api/routers/work_items.py` — `done` and `returned`), never when it is
// filed. Every row of the live queue therefore carries `stage === null` by
// construction, so grouping by stage would drop the whole queue into one
// bucket AND could no longer keep the handed-back rows on top. The honest
// consequence, pinned by the tests: a Stufe other than „alle" selects only
// rows that have already been closed once.

import type { WorkItemKind, WorkItemOut, WorkItemStage, WorkItemStatus } from '@/lib/api';

export type KorbFilter = {
  status: WorkItemStatus | 'all';
  // The Korb-Ebene — „wo gesehen", the level the ⚑ was raised on.
  kind: WorkItemKind | 'all';
  // The diagnosed stage of the writing path; only closed rows carry one.
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

/** The three selects ANDed. A row without a stage never matches a chosen one. */
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
