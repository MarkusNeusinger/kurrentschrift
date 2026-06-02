// Static client-side constants. The frontend hardcodes a single source for v1
// (multi-source is in the DB schema but out of UI scope) and the full alphabet
// of glyphs the admin can curate, so the sidebar can list every letter even
// before bboxes have been drawn for them.
//
// The sidebar groups by *letter*; the (initial/medial/final) position is a
// secondary choice surfaced only once a letter is selected. The (glyph,
// position) tuple is sent with /trace requests; the glyph_key is just an
// opaque URL/UI identifier the DB stores rows under.
//
// glyph_key convention: `${letter.base}-${position}` (e.g. `a-initial`). A few
// letters carry `keyOverrides` to preserve historical keys that already hold
// data in the DB — never change those, or existing bboxes/canonicals orphan.
// The long-s (ſ) and round-s (s) allographs are *separate letters* (per
// `docs/concepts/architektur.md` §3) that happen to share the `s-` prefix
// historically: ſ-medial → `s-medial`, s-final → `s-final`.

export const SOURCE_ID = 'loth-1866';

export type Position = 'initial' | 'medial' | 'final';

// `forne · mitte · hinten` — initial/medial/final. On a teaching plate like
// Loth 1866 there is usually a single specimen per letter, so the three
// positions start out identical; they diverge only as distinct ductus get
// traced.
export const POSITIONS: Position[] = ['initial', 'medial', 'final'];

export type LetterGroup = 'lower' | 'upper' | 'comb';

export interface Letter {
  glyph: string; // the actual character(s); sent as TraceRequest.glyph
  group: LetterGroup;
  base: string; // ascii-safe glyph_key base
  note?: string; // short descriptor shown in tooltips
  keyOverrides?: Partial<Record<Position, string>>; // historical keys to preserve
}

function range(start: string, end: string): string[] {
  const out: string[] = [];
  for (let c = start.charCodeAt(0); c <= end.charCodeAt(0); c++) out.push(String.fromCharCode(c));
  return out;
}

const LOWER_SINGLE: Letter[] = range('a', 'z').map((c): Letter => {
  if (c === 's') {
    // Round s. Historical final key `s-final` must stay; its medial gets a
    // distinct key so it never collides with long-s' historical `s-medial`.
    return { glyph: 's', group: 'lower', base: 's', note: 'rundes s', keyOverrides: { medial: 's-round-medial' } };
  }
  return { glyph: c, group: 'lower', base: c };
});

const LOWER_EXTRA: Letter[] = [
  { glyph: 'ä', group: 'lower', base: 'ae' },
  { glyph: 'ö', group: 'lower', base: 'oe' },
  { glyph: 'ü', group: 'lower', base: 'ue' },
  { glyph: 'ſ', group: 'lower', base: 'longs', note: 'langes s', keyOverrides: { medial: 's-medial' } },
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

export const LETTERS: Letter[] = [...LOWER_SINGLE, ...LOWER_EXTRA, ...UPPER, ...COMB];

export function glyphKeyFor(letter: Letter, position: Position): string {
  return letter.keyOverrides?.[position] ?? `${letter.base}-${position}`;
}

// Flat (glyph, position) registry derived from LETTERS — keeps the old
// KnownGlyph shape so callers that look up by key keep working.
export interface KnownGlyph {
  key: string;
  glyph: string;
  position: Position;
  label: string;
}

function makeLabel(letter: Letter, position: Position): string {
  return letter.note ? `${letter.glyph} · ${position} · ${letter.note}` : `${letter.glyph} · ${position}`;
}

export const KNOWN_GLYPHS: KnownGlyph[] = LETTERS.flatMap((letter) =>
  POSITIONS.map((position) => ({
    key: glyphKeyFor(letter, position),
    glyph: letter.glyph,
    position,
    label: makeLabel(letter, position),
  })),
);

export const LETTER_BY_KEY: Record<string, Letter> = {};
for (const letter of LETTERS) for (const p of POSITIONS) LETTER_BY_KEY[glyphKeyFor(letter, p)] = letter;

const GLYPH_BY_KEY: Record<string, KnownGlyph> = {};
for (const kg of KNOWN_GLYPHS) GLYPH_BY_KEY[kg.key] = kg;

export const knownGlyph = (key: string): KnownGlyph | undefined => GLYPH_BY_KEY[key];
