// How an overview's LIST state travels — the twin of `focus.ts`, one layer out.
//
// `focus.ts` carries the subject (which letter, which join, which word).; this
// module carries how the overview around it is being looked at: list or
// gallery, which filters are on, how it is sorted, which page. Both live in the
// query string for the same reason (focus.ts:6-9) and for one more: a link out
// of the Auftragskorb has to open the same view on another device, which
// `localStorage` cannot do. So nothing here is ever persisted per browser.
//
// The four parameter names are German because they are visible URL vocabulary
// (admin-redesign.md §5.1 Idee 4 writes them out):
// `?ansicht=liste|galerie&filter=&sort=&seite=`.
//
// One reader, MANY vocabularies: `ansicht` also names the Eigenhand page's
// sub-view, and each overview has its own filter and sort tokens. So the reader
// is always handed a `ListSpec` and validates against THAT — never against a
// global union of every token any view knows.
//
// Pure functions only; the views call them from their `useSearchParams` pair.

// Deliberately short and German — they end up in every deep link.
export const LIST_PARAMS = { view: 'ansicht', filter: 'filter', sort: 'sort', page: 'seite' } as const;

export const LIST_VIEWS = ['liste', 'galerie'] as const;
export type ListView = (typeof LIST_VIEWS)[number];

/** The compact work list is the default; the card wall is the opt-in (V14). */
export const DEFAULT_LIST_VIEW: ListView = 'liste';

/** Rows per page, uniform across the overviews (author question Q6, option a). */
export const PAGE_SIZE = 24;

/** The pager's last entry — „alle zeigen", as a page value so it is one URL word. */
export const PAGE_ALL = 'alle';
export type ListPage = number | typeof PAGE_ALL;

/** What one view allows: its filter tokens, its sort tokens, its default sort. */
export type ListSpec<F extends string, S extends string> = {
  filters: readonly F[];
  sorts: readonly S[];
  defaultSort: S;
};

export type ListState<F extends string, S extends string> = {
  view: ListView;
  // Multi-select, ANDed by the view's own row model. Normalised to the spec's
  // order, so two ways of ticking the same chips give the same URL.
  filters: F[];
  sort: S;
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
export function readListState<F extends string, S extends string>(
  params: URLSearchParams,
  spec: ListSpec<F, S>,
): ListState<F, S> {
  const raw = (params.get(LIST_PARAMS.filter) ?? '').split(',');
  // Spec order, not URL order, and each token at most once.
  const filters = spec.filters.filter((token) => raw.includes(token));
  return {
    view: inList(params.get(LIST_PARAMS.view), LIST_VIEWS) ?? DEFAULT_LIST_VIEW,
    filters,
    sort: inList(params.get(LIST_PARAMS.sort), spec.sorts) ?? spec.defaultSort,
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
 * („the list owns four names and nothing else") keeps every future parameter
 * safe without a second list to maintain.
 *
 * Changing a filter or the sort sends the reader back to page 1 — the page they
 * were on belongs to the previous row set, and silently landing on an empty
 * page reads as „nothing matches". An explicit `page` in `next` wins.
 */
export function writeListState<F extends string, S extends string>(
  params: URLSearchParams,
  next: Partial<ListState<F, S>>,
  spec: ListSpec<F, S>,
): URLSearchParams {
  const current = readListState(params, spec);
  const rowsChanged =
    (next.filters !== undefined && next.filters.join(',') !== current.filters.join(',')) ||
    (next.sort !== undefined && next.sort !== current.sort);
  const merged: ListState<F, S> = {
    ...current,
    ...next,
    page: next.page ?? (rowsChanged ? 1 : current.page),
  };

  const out = new URLSearchParams();
  for (const [key, value] of params) {
    if ((Object.values(LIST_PARAMS) as string[]).includes(key)) continue;
    out.append(key, value);
  }
  if (merged.view !== DEFAULT_LIST_VIEW) out.set(LIST_PARAMS.view, merged.view);
  const filters = spec.filters.filter((token) => merged.filters.includes(token));
  if (filters.length > 0) out.set(LIST_PARAMS.filter, filters.join(','));
  if (merged.sort !== spec.defaultSort) out.set(LIST_PARAMS.sort, merged.sort);
  if (merged.page !== 1) out.set(LIST_PARAMS.page, String(merged.page));
  return out;
}

/** How many pages `total` rows fill — at least one, so an empty list has a page. */
export const pageCount = (total: number, page: ListPage = 1): number =>
  page === PAGE_ALL ? 1 : Math.max(1, Math.ceil(total / PAGE_SIZE));

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
