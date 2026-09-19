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

const params = (query: string) => new URLSearchParams(query);
const write = (query: string, next: Parameters<typeof writeListState<Filter, Sort>>[1]) =>
  writeListState(params(query), next, SPEC).toString();

describe('list state parsing', () => {
  it('falls back to the view defaults on an empty query', () => {
    expect(readListState(params(''), SPEC)).toEqual({
      view: DEFAULT_LIST_VIEW,
      filters: [],
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
