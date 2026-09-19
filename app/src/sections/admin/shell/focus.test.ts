import { describe, expect, it } from 'vitest';

import {
  eigenhandUrl,
  joinsOfText,
  joinsUrl,
  keepHand,
  keysOfText,
  lettersUrl,
  neighbourLetters,
  pairKeysOfText,
  readEigenhandFocus,
  readHandFocus,
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

describe('the hand in the URL', () => {
  it('reads a hand id and rejects what is not one', () => {
    expect(readHandFocus(params('h=mn-suetterlin'))).toBe('mn-suetterlin');
    expect(readHandFocus(params('h=mn-zweite-suetterlin'))).toBe('mn-zweite-suetterlin');
    expect(readHandFocus(params(''))).toBeNull();
    expect(readHandFocus(params('h='))).toBeNull();
    // Shape only — which hands EXIST is a question for the loaded candidates
    // (handScope.ts) — but a value that cannot be a hand id at all is dropped
    // here, once, instead of being carried into every link the view writes.
    expect(readHandFocus(params('h=quatsch'))).toBeNull();
    expect(readHandFocus(params('h=MN-Suetterlin'))).toBeNull();
    expect(readHandFocus(params('h=mn suetterlin'))).toBeNull();
    expect(readHandFocus(params('h=mn-'))).toBeNull();
  });

  it('carries the hand through a focus change inside the view', () => {
    // The three views write the WHOLE query when the subject changes, so
    // without this an `h=` arriving on a Korb link would be gone on the first
    // click in the view.
    expect(keepHand(params('g=a&h=mn-suetterlin'), { g: 'b' })).toEqual({ g: 'b', h: 'mn-suetterlin' });
    // Leaving the detail keeps the scope too — the overview is still about
    // that hand.
    expect(keepHand(params('g=a&h=mn-suetterlin'), {})).toEqual({ h: 'mn-suetterlin' });
    expect(keepHand(params('g=a'), { g: 'b' })).toEqual({ g: 'b' });
    expect(keepHand(params('g=a&h=quatsch'), { g: 'b' })).toEqual({ g: 'b' });
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

  it('appends the hand last, and changes nothing without one', () => {
    // The hand is the LAST argument of every builder precisely so that these
    // strings stay byte-identical — every link already pasted into a task
    // keeps resolving to the same place.
    expect(lettersUrl('a', 'mn-suetterlin')).toBe('/admin/buchstaben?g=a&h=mn-suetterlin');
    expect(lettersUrl(null, 'mn-suetterlin')).toBe('/admin/buchstaben?h=mn-suetterlin');
    expect(joinsUrl('a', 'b', 'mn-suetterlin')).toBe('/admin/uebergaenge?l=a&r=b&h=mn-suetterlin');
    expect(wordsUrl('lesen', 'abb19-3', 'mn-suetterlin')).toBe(
      '/admin/woerter?w=lesen&s=abb19-3&h=mn-suetterlin',
    );
    expect(eigenhandUrl('streifen', { hand: 'mn-suetterlin' })).toBe(
      '/admin/eigenhand?reiter=streifen&h=mn-suetterlin',
    );
    // No hand — for instance while no script of this Vorlage has one.
    expect(lettersUrl('a', null)).toBe('/admin/buchstaben?g=a');
    expect(joinsUrl('a', 'b', null)).toBe('/admin/uebergaenge?l=a&r=b');
    expect(wordsUrl('lesen', null, null)).toBe('/admin/woerter?w=lesen');
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
