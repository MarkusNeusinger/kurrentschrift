import { describe, expect, it } from 'vitest';

import {
  eigenhandUrl,
  joinsOfText,
  joinsUrl,
  keysOfText,
  lettersUrl,
  neighbourLetters,
  pairKeysOfText,
  readEigenhandFocus,
  readJoinFocus,
  readLetterFocus,
  readWordFocus,
  textForPair,
  wordsUrl,
} from './focus';

const params = (query: string) => new URLSearchParams(query);

describe('focus parsing', () => {
  it('reads a known letter key and rejects an unknown one', () => {
    expect(readLetterFocus(params('g=a')).glyphKey).toBe('a');
    expect(readLetterFocus(params('g=nonsense')).glyphKey).toBeNull();
    expect(readLetterFocus(params('')).glyphKey).toBeNull();
  });

  it('treats a half-given pair as no focus at all', () => {
    expect(readJoinFocus(params('l=a&r=b'))).toEqual({ leftKey: 'a', rightKey: 'b' });
    expect(readJoinFocus(params('l=a'))).toEqual({ leftKey: null, rightKey: null });
    expect(readJoinFocus(params('l=a&r=nonsense'))).toEqual({ leftKey: null, rightKey: null });
  });

  it('trims the word and keeps its specimen', () => {
    expect(readWordFocus(params('w=%20lesen%20&s=abb19-3'))).toEqual({ text: 'lesen', specimenId: 'abb19-3' });
    expect(readWordFocus(params('w=%20%20'))).toEqual({ text: null, specimenId: null });
  });
});

describe('eigenhand sub-view', () => {
  it('sends an absent or unknown view to the Bestand', () => {
    expect(readEigenhandFocus(params('')).ansicht).toBe('bestand');
    expect(readEigenhandFocus(params('reiter=streifen')).ansicht).toBe('streifen');
    expect(readEigenhandFocus(params('reiter=statistik')).ansicht).toBe('statistik');
    expect(readEigenhandFocus(params('reiter=drucken')).ansicht).toBe('drucken');
    expect(readEigenhandFocus(params('reiter=quatsch')).ansicht).toBe('bestand');
  });

  it('never reads the display mode as a sub-view', () => {
    // `ansicht` is spoken for: it carries the list/gallery display mode of the
    // overviews (V14, author decision Q1 c of 2026-09-19). A `?ansicht=liste`
    // that a later PR puts on another page must therefore mean NOTHING here —
    // not even when its value happens to spell one of our four views.
    expect(readEigenhandFocus(params('ansicht=streifen')).ansicht).toBe('bestand');
    expect(readEigenhandFocus(params('ansicht=liste')).ansicht).toBe('bestand');
    expect(readEigenhandFocus(params('ansicht=liste&reiter=streifen')).ansicht).toBe('streifen');
  });

  it('passes the strips filter through un-validated', () => {
    // A coverage item is a join (`a>b`) or a positioned key (`a@medial`), and
    // the search is free text — none of them is a glyph registry key, so the
    // reader must not gate them the way it gates `g`/`l`/`r`.
    expect(readEigenhandFocus(params('item=a%3Eb'))).toEqual({ ansicht: 'bestand', item: 'a>b', wort: null });
    expect(readEigenhandFocus(params('reiter=streifen&item=a@medial')).item).toBe('a@medial');
    expect(readEigenhandFocus(params('wort=lesen')).wort).toBe('lesen');
    expect(readEigenhandFocus(params('item=&wort='))).toEqual({ ansicht: 'bestand', item: null, wort: null });
  });

  it('keeps an unknown view out of the way of the rest', () => {
    expect(readEigenhandFocus(params('reiter=quatsch&item=a%3Eb'))).toEqual({
      ansicht: 'bestand',
      item: 'a>b',
      wort: null,
    });
  });
});

describe('focus links', () => {
  it('omits absent parameters entirely', () => {
    expect(lettersUrl()).toBe('/admin/buchstaben');
    expect(lettersUrl('a')).toBe('/admin/buchstaben?g=a');
    expect(joinsUrl()).toBe('/admin/uebergaenge');
    expect(joinsUrl('a', 'b')).toBe('/admin/uebergaenge?l=a&r=b');
    expect(wordsUrl('lesen')).toBe('/admin/woerter?w=lesen');
    expect(wordsUrl('lesen', 'abb19-3')).toBe('/admin/woerter?w=lesen&s=abb19-3');
  });

  it('builds the Eigenhand sub-view link, clean when nothing is given', () => {
    expect(eigenhandUrl()).toBe('/admin/eigenhand');
    expect(eigenhandUrl('bestand')).toBe('/admin/eigenhand?reiter=bestand');
    expect(eigenhandUrl('streifen')).toBe('/admin/eigenhand?reiter=streifen');
    expect(eigenhandUrl('streifen', { item: 'a>b' })).toBe('/admin/eigenhand?reiter=streifen&item=a%3Eb');
    expect(eigenhandUrl('streifen', { wort: 'lesen' })).toBe('/admin/eigenhand?reiter=streifen&wort=lesen');
    // An options object with nothing in it adds nothing — the builder keeps
    // its promise that an absent value never reaches the query string.
    expect(eigenhandUrl(null, { item: undefined, wort: null })).toBe('/admin/eigenhand');
  });
});

describe('text ↔ keys', () => {
  it('shapes a word into its keys, long-s rule included', () => {
    expect(keysOfText('lesen')).toEqual(['l', 'e', 'longs', 'e', 'n']);
    expect(keysOfText('das')).toEqual(['d', 'a', 's']);
  });

  it('lists exactly the adjacent joins the composer generates', () => {
    expect(joinsOfText('das')).toEqual([
      { leftKey: 'd', rightKey: 'a' },
      { leftKey: 'a', rightKey: 's' },
    ]);
  });

  it('breaks the join chain at a space', () => {
    const joins = joinsOfText('ab cd');
    expect(joins).toEqual([
      { leftKey: 'a', rightKey: 'b' },
      { leftKey: 'c', rightKey: 'd' },
    ]);
  });

  it('has no join across a detached glyph (digits do not connect)', () => {
    expect(joinsOfText('a1')).toEqual([]);
  });

  it('reports no pair for a combination that folds into a ligature', () => {
    expect(pairKeysOfText('ab')).toEqual(['a', 'b']);
    expect(pairKeysOfText('ch')).toBeNull();
  });

  it('spells a pair of keys back into text', () => {
    expect(textForPair('a', 'b')).toBe('ab');
    expect(textForPair('longs', 'e')).toBe('ſe');
  });
});

describe('letter stepping', () => {
  it('steps inside the letter group and stops at its edges', () => {
    expect(neighbourLetters('b')).toEqual({ prev: 'a', next: 'c' });
    expect(neighbourLetters('a').prev).toBeNull();
    expect(neighbourLetters('nonsense')).toEqual({ prev: null, next: null });
  });
});
