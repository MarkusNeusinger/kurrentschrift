import { describe, expect, it } from 'vitest';

import {
  joinsOfText,
  joinsUrl,
  keysOfText,
  lettersUrl,
  neighbourLetters,
  pairKeysOfText,
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

describe('focus links', () => {
  it('omits absent parameters entirely', () => {
    expect(lettersUrl()).toBe('/admin/buchstaben');
    expect(lettersUrl('a')).toBe('/admin/buchstaben?g=a');
    expect(joinsUrl()).toBe('/admin/uebergaenge');
    expect(joinsUrl('a', 'b')).toBe('/admin/uebergaenge?l=a&r=b');
    expect(wordsUrl('lesen')).toBe('/admin/woerter?w=lesen');
    expect(wordsUrl('lesen', 'abb19-3')).toBe('/admin/woerter?w=lesen&s=abb19-3');
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
