// The contract the Eigenhand coverage grid depends on: a key never reaches the
// screen as a WORD.
//
// The grid used to keep its own hand-written key→character map, a second mirror
// of core/shaping.py's `_PUNCT`/`_LIGATURES`; by the audit of 2026-09-02 it had
// drifted by two entries and „Sonderzeichen" printed the literal string
// "semicolon" among twelve characters. The map is derived from the glyph
// registry now, so the drift cannot recur by omission — this pins the property
// itself, and would fail again if anyone replaced the derivation with a list.

import { describe, expect, it } from 'vitest';

import { LETTERS } from '@/domain/glyphs';
import { KEY_GLYPH_MAP, glyphOf } from './coverageLabels';

describe('glyphOf never leaves a key spelled out', () => {
  it('renders every registry glyph as its character', () => {
    const spelledOut = LETTERS.filter((letter) => glyphOf(letter.base) !== letter.glyph).map(
      (letter) => `${letter.base} → ${glyphOf(letter.base)} (want ${letter.glyph})`,
    );
    expect(spelledOut).toEqual([]);
  });

  it('covers the punctuation whose keys are names, semicolon and dash included', () => {
    // The two that were missing, plus their neighbours — a named regression
    // guard on top of the exhaustive check above.
    expect(glyphOf('semicolon')).toBe(';');
    expect(glyphOf('dash')).toBe('–');
    expect(glyphOf('longs')).toBe('ſ');
    expect(glyphOf('paren-open')).toBe('(');
  });

  it('leaves a key it does not know untouched', () => {
    // A join item or an unknown key must still print SOMETHING rather than
    // undefined — the fallback is deliberate.
    expect(glyphOf('a')).toBe('a');
    expect(glyphOf('nicht-im-register')).toBe('nicht-im-register');
  });

  it('holds no entry the registry does not know', () => {
    const bases = new Set(LETTERS.map((letter) => letter.base));
    expect(Object.keys(KEY_GLYPH_MAP).filter((key) => !bases.has(key))).toEqual([]);
  });
});
