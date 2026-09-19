// How an overview's LIST state travels — the twin of `focus.ts`, one layer out.
//
// `focus.ts` carries the subject (which letter, which join, which word); this
// module carries how the overview around it is being looked at: list or
// gallery, which filters are on, how it is sorted, which page. Both live in the
// query string for the same reason (focus.ts:6-9) and for one more: a link out
// of the Auftragskorb has to open the same view on another device, which
// `localStorage` cannot do. So nothing here is ever persisted per browser.
//
// The parameter names are German because they are visible URL vocabulary
// (admin-redesign.md §5.1 Idee 4 writes them out):
// `?ansicht=liste|galerie&filter=&sort=&seite=`, plus `status=` and `reiter=`
// on the one overview that genuinely has six axes (author decision Q5 a of
// 2026-09-19 — the Wörter list searches by text, selects a Nachfahr-Status and
// stands in one of three tabs, all at the same time).
//
// One reader, MANY vocabularies: each overview has its own filter and sort
// tokens, so the reader is handed a `ListSpec` and validates against THAT,
// never against a global union of every token any view knows. `ansicht` is the
// exception and deliberately NOT in the spec: „Liste oder Galerie" is the same
// pair on every overview, and a third mode is not a thing any surface wants
// today — when one does, it moves into the spec beside the others.
//
// The three axes past the first four are OPTIONAL and declared the same way:
// a spec that names no `statuses` does not own `status=`, so the parameter
// travels through that view's URL untouched instead of being eaten by it. That
// is why they live in the spec rather than in a second module — one reader and
// one writer keep the „defaults are absent from the URL" rule in ONE place,
// and a view that grows an axis declares it instead of hand-rolling a setter.
//
// `ansicht` is the DISPLAY MODE and nothing else (author decision Q1 c of
// 2026-09-19). A page's sub-view is `reiter` — the Eigenhand page's four tabs,
// the Wörter overview's three — and the two words never stand for each other.
//
// Pure functions only; the views call them from their `useSearchParams` pair.

// Deliberately short and German — they end up in every deep link.
export const LIST_PARAMS = {
  view: 'ansicht',
  filter: 'filter',
  sort: 'sort',
  page: 'seite',
  status: 'status',
  tab: 'reiter',
} as const;

export const LIST_VIEWS = ['liste', 'galerie'] as const;
export type ListView = (typeof LIST_VIEWS)[number];

/** The compact work list is the default; the card wall is the opt-in (V14). */
export const DEFAULT_LIST_VIEW: ListView = 'liste';

/** Rows per page, uniform across the overviews (author question Q6, option a). */
export const PAGE_SIZE = 24;

/** The pager's last entry — „alle zeigen", as a page value so it is one URL word. */
export const PAGE_ALL = 'alle';
export type ListPage = number | typeof PAGE_ALL;

/**
 * What one view allows: its filter tokens, its sort tokens, its default sort —
 * and, where it has them, its free-text search, its status vocabulary and its
 * tabs. The last three are opt-in: a view that declares none of them owns four
 * parameter names and leaves every other one alone.
 */
export type ListSpec<
  F extends string,
  S extends string,
  T extends string = never,
  R extends string = never,
> = {
  filters: readonly F[];
  sorts: readonly S[];
  defaultSort: S;
  // `filter=` carries FREE TEXT rather than chip tokens. The two readings of
  // one name are exclusive by construction: a view searching by text has no
  // chips to encode there, and the plan gives both the same word because both
  // answer „was soll übrig bleiben?".
  freeText?: boolean;
  // `status=` — ONE value out of this vocabulary, the first entry being the
  // default (and therefore the value that never appears in the URL).
  statuses?: readonly T[];
  // `reiter=` — which tab of this page; first entry the default. Never a
  // display mode: that is `ansicht`.
  tabs?: readonly R[];
};

export type ListState<
  F extends string,
  S extends string,
  T extends string = never,
  R extends string = never,
> = {
  view: ListView;
  // Multi-select, ANDed by the view's own row model. Normalised to the spec's
  // order, so two ways of ticking the same chips give the same URL.
  filters: F[];
  // The free-text search, empty unless the spec declares `freeText`.
  text: string;
  sort: S;
  // `null` where the spec declares no such axis — „this view has no status",
  // which is a different statement from „the status is Alle".
  status: T | null;
  tab: R | null;
  page: ListPage;
};

const inList = <T extends string>(value: string | null, allowed: readonly T[]): T | null =>
  value !== null && (allowed as readonly string[]).includes(value) ? (value as T) : null;

// A page number is only usable as a positive integer. `0`, `-2`, `abc` and an
// empty parameter all mean „no page was asked for" — the first one. The upper
// end cannot be judged here (the row count is not known until the rows are
// built); `clampPage` does that at render time.
function readPage(raw: string | null): ListPage {
  if (raw === PAGE_ALL) return PAGE_ALL;
  const n = Number(raw);
  return Number.isInteger(n) && n >= 1 ? n : 1;
}

/**
 * The list state a query string describes, every unknown token falling back to
 * its default — the same doctrine `knownKey` applies to the subject
 * (`focus.ts:38-39`): a hand-edited URL lands on the plain view rather than on
 * a filter nothing can match.
 */
export function readListState<
  F extends string,
  S extends string,
  T extends string = never,
  R extends string = never,
>(params: URLSearchParams, spec: ListSpec<F, S, T, R>): ListState<F, S, T, R> {
  const raw = params.get(LIST_PARAMS.filter) ?? '';
  // Spec order, not URL order, and each token at most once.
  const filters = spec.freeText ? [] : spec.filters.filter((token) => raw.split(',').includes(token));
  // A free-text needle is NOT validated — it is whatever was typed, and the
  // only thing that could be checked about it is whether it matches something,
  // which is the list's answer rather than the reader's.
  return {
    view: inList(params.get(LIST_PARAMS.view), LIST_VIEWS) ?? DEFAULT_LIST_VIEW,
    filters,
    text: spec.freeText ? raw : '',
    sort: inList(params.get(LIST_PARAMS.sort), spec.sorts) ?? spec.defaultSort,
    status: spec.statuses ? (inList(params.get(LIST_PARAMS.status), spec.statuses) ?? spec.statuses[0]) : null,
    tab: spec.tabs ? (inList(params.get(LIST_PARAMS.tab), spec.tabs) ?? spec.tabs[0]) : null,
    page: readPage(params.get(LIST_PARAMS.page)),
  };
}

/**
 * The query string for a changed list state: the given fields over the current
 * ones, DEFAULT values omitted (so the plain view has a clean URL) and every
 * parameter this module does not own — the subject keys `g`/`l`/`r`/`w`/`s`,
 * the scope's `h`, anything a later view adds — carried through untouched.
 *
 * Preserving by exclusion rather than by an allow-list is deliberate: the three
 * views rewrite their whole query on a focus change today, which is how a Korb
 * link's extra parameter gets dropped on the first click in the view. One rule
 * („the list owns four names, plus the axes its spec declares") keeps every
 * future parameter safe without a second list to maintain.
 *
 * Changing anything that changes WHICH rows are listed — a filter, the search
 * text, the status, the tab, the sort — sends the reader back to page 1: the
 * page they were on belongs to the previous row set, and silently landing on an
 * empty page reads as „nothing matches". An explicit `page` in `next` wins, and
 * switching between list and gallery keeps the page, because the rows are the
 * same and only their shape changes.
 */
export function writeListState<
  F extends string,
  S extends string,
  T extends string = never,
  R extends string = never,
>(
  params: URLSearchParams,
  next: Partial<ListState<F, S, T, R>>,
  spec: ListSpec<F, S, T, R>,
): URLSearchParams {
  const current = readListState(params, spec);
  const rowsChanged =
    (next.filters !== undefined && next.filters.join(',') !== current.filters.join(',')) ||
    (next.sort !== undefined && next.sort !== current.sort) ||
    (next.text !== undefined && next.text !== current.text) ||
    (next.status !== undefined && next.status !== current.status) ||
    (next.tab !== undefined && next.tab !== current.tab);
  const merged: ListState<F, S, T, R> = {
    ...current,
    ...next,
    page: next.page ?? (rowsChanged ? 1 : current.page),
  };

  // What this view owns, and nothing beyond it: an overview without tabs must
  // leave a `reiter=` it finds standing, or a link built for another surface
  // would lose half its meaning on the first click here.
  const owned: string[] = [LIST_PARAMS.view, LIST_PARAMS.filter, LIST_PARAMS.sort, LIST_PARAMS.page];
  if (spec.statuses) owned.push(LIST_PARAMS.status);
  if (spec.tabs) owned.push(LIST_PARAMS.tab);

  const out = new URLSearchParams();
  for (const [key, value] of params) {
    if (owned.includes(key)) continue;
    out.append(key, value);
  }
  if (merged.view !== DEFAULT_LIST_VIEW) out.set(LIST_PARAMS.view, merged.view);
  if (spec.freeText) {
    if (merged.text !== '') out.set(LIST_PARAMS.filter, merged.text);
  } else {
    const filters = spec.filters.filter((token) => merged.filters.includes(token));
    if (filters.length > 0) out.set(LIST_PARAMS.filter, filters.join(','));
  }
  if (merged.sort !== spec.defaultSort) out.set(LIST_PARAMS.sort, merged.sort);
  if (spec.statuses && merged.status !== null && merged.status !== spec.statuses[0]) {
    out.set(LIST_PARAMS.status, merged.status);
  }
  if (spec.tabs && merged.tab !== null && merged.tab !== spec.tabs[0]) out.set(LIST_PARAMS.tab, merged.tab);
  if (merged.page !== 1) out.set(LIST_PARAMS.page, String(merged.page));
  return out;
}

/** How many pages `total` rows fill — at least one, so an empty list has a page.
 * A count of the LIST, not of a state: „alle zeigen" is a choice among these
 * pages, so it does not change how many there are. */
export const pageCount = (total: number): number => Math.max(1, Math.ceil(total / PAGE_SIZE));

/**
 * The page actually shown. A filter that shrinks the list must not leave the
 * reader on page 3 of one page — that is the empty screen with no cause on it
 * the Leerzustands-Regel exists against.
 */
export const clampPage = (page: ListPage, total: number): ListPage =>
  page === PAGE_ALL ? PAGE_ALL : Math.min(Math.max(1, page), pageCount(total));

/** The rows of the clamped page — the whole list under „alle zeigen". */
export function pageSlice<T>(rows: T[], page: ListPage): T[] {
  const clamped = clampPage(page, rows.length);
  if (clamped === PAGE_ALL) return rows;
  const start = (clamped - 1) * PAGE_SIZE;
  return rows.slice(start, start + PAGE_SIZE);
}
