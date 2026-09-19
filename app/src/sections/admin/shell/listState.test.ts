import { describe, expect, it } from 'vitest';

import {
  DEFAULT_LIST_VIEW,
  PAGE_ALL,
  PAGE_SIZE,
  clampPage,
  pageCount,
  pageSlice,
  readListState,
  writeListState,
  type ListSpec,
} from './listState';

// A synthetic vocabulary: this module must know nothing about which view it is
// serving, so the test does not borrow one view's tokens either.
type Filter = 'rot' | 'blau';
type Sort = 'alphabet' | 'schlechteste';
const SPEC: ListSpec<Filter, Sort> = {
  filters: ['rot', 'blau'],
  sorts: ['alphabet', 'schlechteste'],
  defaultSort: 'alphabet',
};

// The second shape a spec can take: free text instead of chips, plus the two
// optional axes. The Wörter overview is the one surface that needs all six.
type Status = 'alle' | 'offen';
type Tab = 'eins' | 'zwei';
const SIX: ListSpec<never, Sort, Status, Tab> = {
  filters: [],
  freeText: true,
  sorts: ['alphabet', 'schlechteste'],
  defaultSort: 'alphabet',
  statuses: ['alle', 'offen'],
  tabs: ['eins', 'zwei'],
};

const params = (query: string) => new URLSearchParams(query);
const write = (query: string, next: Parameters<typeof writeListState<Filter, Sort>>[1]) =>
  writeListState(params(query), next, SPEC).toString();
const write6 = (query: string, next: Parameters<typeof writeListState<never, Sort, Status, Tab>>[1]) =>
  writeListState(params(query), next, SIX).toString();

describe('list state parsing', () => {
  it('falls back to the view defaults on an empty query', () => {
    expect(readListState(params(''), SPEC)).toEqual({
      view: DEFAULT_LIST_VIEW,
      filters: [],
      // A spec that declares none of the three extra axes reports them as
      // absent — „this view has no status" rather than „the status is Alle".
      text: '',
      status: null,
      tab: null,
      sort: 'alphabet',
      page: 1,
    });
  });

  it('reads the four parameters', () => {
    expect(readListState(params('ansicht=galerie&filter=blau,rot&sort=schlechteste&seite=3'), SPEC)).toEqual({
      view: 'galerie',
      // Spec order, not URL order — two ways of ticking the same chips give one
      // state and therefore one URL.
      filters: ['rot', 'blau'],
      text: '',
      status: null,
      tab: null,
      sort: 'schlechteste',
      page: 3,
    });
  });

  it('answers an unknown token with the default instead of an empty view', () => {
    const state = readListState(params('ansicht=wand&filter=gruen&sort=beste'), SPEC);
    expect(state.view).toBe('liste');
    expect(state.filters).toEqual([]);
    expect(state.sort).toBe('alphabet');
  });

  it('keeps the known half of a filter list and drops the rest', () => {
    expect(readListState(params('filter=gruen,blau'), SPEC).filters).toEqual(['blau']);
  });

  it('treats a page that is not a positive whole number as the first one', () => {
    for (const query of ['seite=0', 'seite=-2', 'seite=abc', 'seite=', 'seite=1.5']) {
      expect(readListState(params(query), SPEC).page).toBe(1);
    }
    expect(readListState(params('seite=alle'), SPEC).page).toBe(PAGE_ALL);
  });
});

describe('list state writing', () => {
  it('leaves the default state out of the URL entirely', () => {
    expect(write('', { view: 'liste', filters: [], sort: 'alphabet', page: 1 })).toBe('');
    expect(write('ansicht=galerie&sort=schlechteste&seite=2', { view: 'liste', sort: 'alphabet', page: 1 })).toBe('');
  });

  it('round-trips every non-default value', () => {
    const query = write('', { view: 'galerie', filters: ['blau', 'rot'], sort: 'schlechteste', page: 4 });
    expect(readListState(params(query), SPEC)).toEqual({
      view: 'galerie',
      filters: ['rot', 'blau'],
      text: '',
      status: null,
      tab: null,
      sort: 'schlechteste',
      page: 4,
    });
  });

  it('carries the subject parameters through untouched', () => {
    // `h` is the scope's hand — not a parameter this module knows, which is the
    // point: the list owns four names and preserves everything else, so a Korb
    // link's extra key survives the first click in the view.
    const query = write('g=a&l=b&r=c&w=lesen&s=abb19-3&h=mn-suetterlin', { view: 'galerie' });
    const out = params(query);
    expect(out.get('g')).toBe('a');
    expect(out.get('l')).toBe('b');
    expect(out.get('r')).toBe('c');
    expect(out.get('w')).toBe('lesen');
    expect(out.get('s')).toBe('abb19-3');
    expect(out.get('h')).toBe('mn-suetterlin');
    expect(out.get('ansicht')).toBe('galerie');
  });

  it('sends a changed filter or sort back to the first page', () => {
    expect(params(write('seite=3', { filters: ['rot'] })).get('seite')).toBeNull();
    expect(params(write('seite=3', { sort: 'schlechteste' })).get('seite')).toBeNull();
    // An explicit page wins, and switching the VIEW keeps the page: the rows
    // are the same, only their shape changes.
    expect(params(write('seite=3', { filters: ['rot'], page: 3 })).get('seite')).toBe('3');
    expect(params(write('seite=3', { view: 'galerie' })).get('seite')).toBe('3');
  });

  it('keeps the page when the same filters are written again', () => {
    expect(params(write('filter=rot&seite=2', { filters: ['rot'] })).get('seite')).toBe('2');
  });
});

// The three axes the Wörter overview needs on top of the four (author decision
// Q5 a). They are declared in the SPEC, which is what keeps a view that has no
// tabs from eating a `reiter=` it happens to find.
describe('the free-text, status and tab axes', () => {
  it('reads all six, unknown tokens falling back to the first entry', () => {
    expect(readListState(params('filter=les&status=offen&reiter=zwei&sort=schlechteste'), SIX)).toEqual({
      view: DEFAULT_LIST_VIEW,
      filters: [],
      text: 'les',
      status: 'offen',
      tab: 'zwei',
      sort: 'schlechteste',
      page: 1,
    });
    const nonsense = readListState(params('status=grün&reiter=drei'), SIX);
    expect(nonsense.status).toBe('alle');
    expect(nonsense.tab).toBe('eins');
  });

  it('reads `filter=` as TEXT where the spec says so, and as chips where it does not', () => {
    // The same parameter name, two readings, and each view only ever gets its
    // own: a needle that happens to spell a chip token is still a needle.
    expect(readListState(params('filter=rot'), SIX).text).toBe('rot');
    expect(readListState(params('filter=rot'), SIX).filters).toEqual([]);
    expect(readListState(params('filter=rot'), SPEC).filters).toEqual(['rot']);
    expect(readListState(params('filter=rot'), SPEC).text).toBe('');
  });

  it('leaves the default state out of the URL entirely', () => {
    expect(write6('', { text: '', status: 'alle', tab: 'eins', view: 'liste', sort: 'alphabet' })).toBe('');
    expect(write6('filter=les&status=offen&reiter=zwei', { text: '', status: 'alle', tab: 'eins' })).toBe('');
  });

  it('round-trips a needle with a space in it', () => {
    const query = write6('', { text: 'der see' });
    expect(readListState(params(query), SIX).text).toBe('der see');
  });

  it('sends a changed tab, status or needle back to the first page — and keeps the filter', () => {
    // The tab is a different row set, so page 3 of the old one means nothing;
    // the SEARCH is what the reader is looking for and survives the switch.
    const out = params(write6('filter=les&status=offen&seite=3', { tab: 'zwei' }));
    expect(out.get('seite')).toBeNull();
    expect(out.get('filter')).toBe('les');
    expect(out.get('status')).toBe('offen');
    expect(params(write6('seite=3', { status: 'offen' })).get('seite')).toBeNull();
    expect(params(write6('seite=3', { text: 'les' })).get('seite')).toBeNull();
    // Writing the same value again is not a change.
    expect(params(write6('filter=les&seite=2', { text: 'les' })).get('seite')).toBe('2');
  });

  it('leaves an axis alone that the spec does not declare', () => {
    // `SPEC` has no statuses and no tabs, so both travel through its view
    // untouched — the Eigenhand page's `reiter=` is the live case.
    const out = params(write('status=offen&reiter=streifen&h=mn-suetterlin', { view: 'galerie' }));
    expect(out.get('status')).toBe('offen');
    expect(out.get('reiter')).toBe('streifen');
    expect(out.get('h')).toBe('mn-suetterlin');
  });
});

describe('paging', () => {
  const rows = Array.from({ length: PAGE_SIZE * 2 + 5 }, (_, i) => i);

  it('counts at least one page, even for an empty list', () => {
    expect(pageCount(0)).toBe(1);
    expect(pageCount(PAGE_SIZE)).toBe(1);
    expect(pageCount(PAGE_SIZE + 1)).toBe(2);
    expect(pageCount(rows.length)).toBe(3);
  });

  it('clamps a page a shrinking filter left behind', () => {
    expect(clampPage(3, rows.length)).toBe(3);
    // The same page number after a filter cut the list down to one page.
    expect(clampPage(3, 4)).toBe(1);
    expect(clampPage(99, rows.length)).toBe(3);
    expect(clampPage(PAGE_ALL, 4)).toBe(PAGE_ALL);
  });

  it('slices the clamped page and shows everything under „alle zeigen"', () => {
    expect(pageSlice(rows, 1)).toEqual(rows.slice(0, PAGE_SIZE));
    expect(pageSlice(rows, 3)).toEqual(rows.slice(PAGE_SIZE * 2));
    // Out of range: the last page, never an empty screen.
    expect(pageSlice(rows, 9)).toEqual(rows.slice(PAGE_SIZE * 2));
    expect(pageSlice(rows, PAGE_ALL)).toEqual(rows);
    expect(pageSlice([], 2)).toEqual([]);
  });
});
