// The glyph domain: the full alphabet the admin can curate (so the sidebar can
// list every letter even before bboxes have been drawn), the glyph_key scheme,
// and the lock/quiz-unit helpers. Framework-free — no React, no API.
//
// glyph_key convention: the bare `letter.base` (e.g. `a`, `A`, `ae`, `ch`,
// `comma`, `0`) — ONE template row and ONE bbox row per glyph. The word
// position (initial/medial/final) is render context assigned by shaping; it
// never feeds the key. The long-s (ſ) and round-s (s) allographs are *separate
// letters* (per `docs/concepts/architektur.md` §3): ſ → `longs`, round s → `s`.
//
// The quiz (`/quiz`) reads whatever bboxes exist in the DB and maps each
// glyph_key back to its `answer` letter via KNOWN_GLYPHS, so marking a new
// letter on the chart immediately makes it quizzable.


export type Position = 'initial' | 'medial' | 'final';
export type LetterCase = 'upper' | 'lower';
// `mvp` = the curated §9 anchor set (allograph-aware trace targets).
// `alphabet` = the rest of the alphabet, markable so the quiz vocabulary grows.
export type GlyphGroup = 'mvp' | 'alphabet';

// Front · middle · end of a word — render context only (shaping assigns it per
// run; the connection strokes are generated from entry/exit tangents). Kept
// exported for the shaping twin.
export const POSITIONS: Position[] = ['initial', 'medial', 'final'];

export type LetterGroup = 'lower' | 'upper' | 'comb' | 'digit' | 'punct';

export interface Letter {
  glyph: string; // the actual character(s); sent as TraceRequest.glyph
  group: LetterGroup;
  base: string; // ascii-safe glyph_key
  note?: string; // short descriptor shown in tooltips
  // False for the detached glyph classes (digits, punctuation): they render
  // but no Übergang ever enters or leaves them. Mirrors core/shaping.py.
  joins?: boolean;
}

function range(start: string, end: string): string[] {
  const out: string[] = [];
  for (let c = start.charCodeAt(0); c <= end.charCodeAt(0); c++) out.push(String.fromCharCode(c));
  return out;
}

const LOWER_SINGLE: Letter[] = range('a', 'z').map((c): Letter => {
  // Round s (Schluss-s) keys as `s`; the long-s ſ is its own letter (`longs`).
  if (c === 's') return { glyph: 's', group: 'lower', base: 's', note: 'rundes s' };
  return { glyph: c, group: 'lower', base: c };
});

const LOWER_EXTRA: Letter[] = [
  { glyph: 'ä', group: 'lower', base: 'ae' },
  { glyph: 'ö', group: 'lower', base: 'oe' },
  { glyph: 'ü', group: 'lower', base: 'ue' },
  { glyph: 'ſ', group: 'lower', base: 'longs', note: 'langes s' },
];

const UPPER: Letter[] = [
  ...range('A', 'Z').map((c): Letter => ({ glyph: c, group: 'upper', base: c })),
  { glyph: 'Ä', group: 'upper', base: 'Ae' },
  { glyph: 'Ö', group: 'upper', base: 'Oe' },
  { glyph: 'Ü', group: 'upper', base: 'Ue' },
];

// Closed ligature set per `docs/concepts/architektur.md` §4 / CLAUDE.md.
const COMB: Letter[] = [
  { glyph: 'ch', group: 'comb', base: 'ch' },
  { glyph: 'ck', group: 'comb', base: 'ck' },
  { glyph: 'tz', group: 'comb', base: 'tz' },
  { glyph: 'ſt', group: 'comb', base: 'longst', note: 'ſt-Ligatur' },
  { glyph: 'qu', group: 'comb', base: 'qu' },
  { glyph: 'ß', group: 'comb', base: 'sz', note: 'Eszett' },
];

// Digits and punctuation: real glyphs, but detached — written without any
// Übergang (joins: false). Kept in sync with core/shaping.py (_DIGITS/_PUNCT —
// alias characters like ’ ” ‐ — resolve in shaping).
const DIGITS: Letter[] = range('0', '9').map((c): Letter => ({ glyph: c, group: 'digit', base: c, joins: false }));

const PUNCT: Letter[] = [
  { glyph: '.', group: 'punct', base: 'period', note: 'Punkt', joins: false },
  { glyph: ',', group: 'punct', base: 'comma', note: 'Komma', joins: false },
  { glyph: ';', group: 'punct', base: 'semicolon', note: 'Semikolon', joins: false },
  { glyph: ':', group: 'punct', base: 'colon', note: 'Doppelpunkt', joins: false },
  { glyph: '!', group: 'punct', base: 'exclam', note: 'Ausrufezeichen', joins: false },
  { glyph: '?', group: 'punct', base: 'question', note: 'Fragezeichen', joins: false },
  { glyph: "'", group: 'punct', base: 'apostrophe', note: 'Apostroph', joins: false },
  { glyph: '„', group: 'punct', base: 'quote-low', note: 'Anführungszeichen öffnend', joins: false },
  { glyph: '“', group: 'punct', base: 'quote-high', note: 'Anführungszeichen schließend', joins: false },
  { glyph: '-', group: 'punct', base: 'hyphen', note: 'Bindestrich (schräger Doppelstrich ⸗)', joins: false },
  { glyph: '–', group: 'punct', base: 'dash', note: 'Gedankenstrich', joins: false },
  { glyph: '(', group: 'punct', base: 'paren-open', note: 'Klammer auf', joins: false },
  { glyph: ')', group: 'punct', base: 'paren-close', note: 'Klammer zu', joins: false },
  { glyph: '§', group: 'punct', base: 'section', note: 'Paragraf', joins: false },
];

export const LETTERS: Letter[] = [...LOWER_SINGLE, ...LOWER_EXTRA, ...UPPER, ...COMB, ...DIGITS, ...PUNCT];

export function glyphKeyFor(letter: Letter): string {
  return letter.base;
}

// Flat glyph registry derived from LETTERS. Carries the quiz fields
// (`answer`, `letterCase`, `group`) so the quiz can map any marked bbox back to
// a Latin letter, and keeps the KnownGlyph shape callers look up by key.
export interface KnownGlyph {
  key: string;
  glyph: string; // the rendered form shown as the solution (ſ, A, …)
  label: string;
  // The Latin letter the learner types in the quiz, normalised to lowercase
  // (long-s `ſ` and round-s `s` both answer `s`).
  answer: string;
  letterCase: LetterCase;
  group: GlyphGroup;
}

// The §9 anchor letters — they hold real traced data, so they keep the
// `mvp` group; every other derived key is `alphabet`.
const MVP_KEYS = new Set(['a', 'd', 'e', 'l', 'n', 'longs', 's']);

// Glyphs whose lowercase form is not the letter a learner would type.
const ANSWER_OVERRIDE: Record<string, string> = { ſ: 's', ſt: 'st' };

function makeLabel(letter: Letter): string {
  return letter.note ? `${letter.glyph} · ${letter.note}` : letter.glyph;
}

function answerOf(glyph: string): string {
  return ANSWER_OVERRIDE[glyph] ?? glyph.toLowerCase();
}

const DERIVED_GLYPHS: KnownGlyph[] = LETTERS.map(
  (letter): KnownGlyph => ({
    key: glyphKeyFor(letter),
    glyph: letter.glyph,
    label: makeLabel(letter),
    answer: answerOf(letter.glyph),
    letterCase: letter.group === 'upper' ? 'upper' : 'lower',
    group: MVP_KEYS.has(glyphKeyFor(letter)) ? 'mvp' : 'alphabet',
  }),
);

// Read-only back-compat: an earlier full-alphabet scheme keyed capitals as
// `uc-<letter>` and lowercase gaps as `lc-<letter>` (single chart role). The
// admin now writes base keys, but any bbox already marked under the old scheme
// stays resolvable here so the quiz keeps recognising it.
const LEGACY_ALIASES: KnownGlyph[] = range('a', 'z').flatMap((c): KnownGlyph[] => [
  { key: `uc-${c}`, glyph: c.toUpperCase(), label: `${c.toUpperCase()} · Versal`, answer: c, letterCase: 'upper', group: 'alphabet' },
  { key: `lc-${c}`, glyph: c, label: `${c} · klein`, answer: c, letterCase: 'lower', group: 'alphabet' },
]);

export const KNOWN_GLYPHS: KnownGlyph[] = [...DERIVED_GLYPHS, ...LEGACY_ALIASES];

export const LETTER_BY_KEY: Record<string, Letter> = {};
for (const letter of LETTERS) LETTER_BY_KEY[glyphKeyFor(letter)] = letter;

// Minimal shape of a stored bbox the quiz helper needs. Kept structural (not
// the full BboxOut) so this module stays free of an API-types import.
interface BboxFlags {
  locked?: boolean;
}

// The locked glyph keys that enter the reading quiz: every locked key whose
// letter is not punctuation (there is no letter to type); digits stay — reading
// period digits is a real drill. Legacy uc-/lc- aliases (not in LETTER_BY_KEY)
// stay singletons. One key = one glyph, so s and ſ (`s` / `longs`) are always
// distinct units.
export function quizKeysFromLocked(bboxesByKey: Record<string, BboxFlags>): string[] {
  const out: string[] = [];
  for (const [key, b] of Object.entries(bboxesByKey)) {
    if (!b?.locked) continue;
    if (LETTER_BY_KEY[key]?.group === 'punct') continue;
    out.push(key);
  }
  return out;
}

const BY_KEY: Map<string, KnownGlyph> = new Map(KNOWN_GLYPHS.map((g) => [g.key, g]));

export const knownGlyph = (key: string): KnownGlyph | undefined => BY_KEY.get(key);
