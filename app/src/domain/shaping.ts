// Text shaping for the German cursive scripts: turn a typed word or sentence
// into the ordered sequence of canonical glyph_keys the renderer fetches and
// connects. Framework-free (no React, no API) — the geometry lives in
// `domain/compose.ts`, the rendering in `components/WrittenWord`.
//
// Two orthographic rules carry the historical look (architektur.md §3/§4):
//
//   1. Long-s vs round-s (Lang-s ſ / Schluss-s s). German Kurrent/Sütterlin
//      writes the long-s ſ at the start and in the middle of a word and the
//      round s only at the end. These are *separate allographs* with their own
//      ductus (`longs-*` / `s-medial` for ſ, `s-final` for the round s), not one
//      letter with a transition. We approximate the syllable rule with the
//      pragmatic "ſ unless word-final" convention used by historical type — good
//      enough for the public live-writing demo; a full syllabifier is post-MVP.
//
//   2. The closed ligature set ch · ck · tz · ſt · qu · ß are *taught units*
//      with their own template, not exit→entry chains (architektur.md §4). We
//      detect them greedily, but only when the cluster starts on a lowercase
//      letter — a capitalised "China"/"Stein" is a capital C/S plus the rest,
//      not the lowercase ligature.
//
// Everything else (arbitrary letter pairs) is connected by generated Übergänge
// at render time, which is the whole point of avoiding a bigram table.

import { glyphKeyFor, LETTERS, type Letter, type Position } from '@/domain/glyphs';

export interface GlyphSlot {
  // The canonical glyph_key to fetch + render, or null for a space / a character
  // with no glyph (punctuation, digits) which renders as an advance-only gap.
  key: string | null;
  // The source character(s) this slot stands for (availability UI / debugging).
  text: string;
  position: Position | null;
  // True for the closed-set ligatures (ch, ck, tz, ſt, qu, ß).
  ligature: boolean;
  // True for an inter-word space — renders as horizontal advance only and
  // breaks the connecting stroke (no Übergang spans a word gap).
  space: boolean;
}

// Single-character glyphs keyed by their character (a–z, ä/ö/ü, ſ, s, A–Z, …).
const LETTER_BY_CHAR = new Map<string, Letter>();
// The closed ligature set keyed by its written form ('ch', …, 'ſt', 'ß').
const LIGATURE_BY_FORM = new Map<string, Letter>();
for (const letter of LETTERS) {
  if (letter.group === 'comb') LIGATURE_BY_FORM.set(letter.glyph, letter);
  else if ([...letter.glyph].length === 1) LETTER_BY_CHAR.set(letter.glyph, letter);
}

// The two s-allographs, resolved per position in `assignPositions`.
const LONG_S = LETTER_BY_CHAR.get('ſ');
const ROUND_S = LETTER_BY_CHAR.get('s');

// A cased lowercase letter (so an uppercase initial is never folded into a
// lowercase ligature). `toLowerCase() === c` is true for non-letters too, hence
// the extra `toUpperCase() !== c` guard.
function isLowercaseLetter(c: string): boolean {
  return c === c.toLowerCase() && c !== c.toUpperCase();
}

interface RawToken {
  letter: Letter | null; // null => unknown char (gap) or a deferred s-allograph
  text: string;
  ligature: boolean;
  sAllograph: boolean; // a lowercase s/ſ whose long-vs-round form depends on position
}

// Greedy left-to-right tokeniser over one whitespace-free word.
function tokenizeWord(word: string): RawToken[] {
  const chars = [...word];
  const tokens: RawToken[] = [];
  let i = 0;
  while (i < chars.length) {
    const c = chars[i];
    const next = chars[i + 1];
    // Two-character ligatures, only when the cluster opens on a lowercase letter.
    if (next !== undefined && isLowercaseLetter(c)) {
      const pair = (c + next).toLowerCase();
      if (pair === 'ch' || pair === 'ck' || pair === 'tz' || pair === 'qu') {
        tokens.push({ letter: LIGATURE_BY_FORM.get(pair) ?? null, text: c + next, ligature: true, sAllograph: false });
        i += 2;
        continue;
      }
      // ſt-ligature: a long-s followed by t (the s before t is always a long-s
      // context). Accept both the typed 's' and an already-long 'ſ'.
      if (pair === 'st' || pair === 'ſt') {
        tokens.push({ letter: LIGATURE_BY_FORM.get('ſt') ?? null, text: c + next, ligature: true, sAllograph: false });
        i += 2;
        continue;
      }
    }
    // ß — a single-character ligature unit (Eszett).
    if (c === 'ß') {
      tokens.push({ letter: LIGATURE_BY_FORM.get('ß') ?? null, text: c, ligature: true, sAllograph: false });
      i += 1;
      continue;
    }
    // Lowercase s/ſ: defer the long-vs-round choice to position assignment.
    if ((c === 's' || c === 'ſ') && isLowercaseLetter(c)) {
      tokens.push({ letter: null, text: c, ligature: false, sAllograph: true });
      i += 1;
      continue;
    }
    const letter = LETTER_BY_CHAR.get(c) ?? null;
    tokens.push({ letter, text: c, ligature: false, sAllograph: false });
    i += 1;
  }
  return tokens;
}

function positionOf(index: number, count: number): Position {
  if (count === 1 || index === 0) return 'initial';
  if (index === count - 1) return 'final';
  return 'medial';
}

function assignPositions(tokens: RawToken[]): GlyphSlot[] {
  return tokens.map((t, idx): GlyphSlot => {
    const position = positionOf(idx, tokens.length);
    // Long-s in initial/medial position, round s word-final (the historical rule).
    if (t.sAllograph) {
      const letter = position === 'final' ? ROUND_S : LONG_S;
      return {
        key: letter ? glyphKeyFor(letter, position) : null,
        text: t.text,
        position,
        ligature: false,
        space: false,
      };
    }
    if (!t.letter) return { key: null, text: t.text, position: null, ligature: false, space: false };
    return { key: glyphKeyFor(t.letter, position), text: t.text, position, ligature: t.ligature, space: false };
  });
}

// One word → its ordered glyph slots (with positions + allographs resolved).
export function shapeWord(word: string): GlyphSlot[] {
  if (!word) return [];
  return assignPositions(tokenizeWord(word));
}

// A whole line (word(s) + spaces) → slots, with a space slot between words so
// the renderer leaves a gap and breaks the connecting stroke there.
export function shapeText(text: string): GlyphSlot[] {
  const out: GlyphSlot[] = [];
  for (const part of text.split(/(\s+)/)) {
    if (part === '') continue;
    if (/^\s+$/.test(part)) {
      out.push({ key: null, text: ' ', position: null, ligature: false, space: true });
      continue;
    }
    out.push(...shapeWord(part));
  }
  return out;
}

// Distinct glyph_keys a text needs — what the renderer fetches (deduped).
export function glyphKeysOf(slots: GlyphSlot[]): string[] {
  const seen = new Set<string>();
  for (const s of slots) if (s.key) seen.add(s.key);
  return [...seen];
}
