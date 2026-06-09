// The glyph domain: the full alphabet the admin can curate (so the sidebar can
// list every letter even before bboxes have been drawn), the glyph_key scheme,
// and the lock/split/quiz-unit helpers. Framework-free — no React, no API.
//
// The admin sidebar groups by *letter*; the (initial/medial/final) position is
// a secondary choice surfaced only once a letter is selected. The (glyph,
// position) tuple is sent with /trace requests; the glyph_key is just an opaque
// URL/UI identifier the DB stores rows under.
//
// glyph_key convention: `${letter.base}-${position}` (e.g. `a-initial`). A few
// letters carry `keyOverrides` to preserve historical keys that already hold
// data in the DB — never change those, or existing bboxes/canonicals orphan.
// The long-s (ſ) and round-s (s) allographs are *separate letters* (per
// `docs/concepts/architektur.md` §3) that happen to share the `s-` prefix
// historically: ſ-medial → `s-medial`, s-final → `s-final`.
//
// The quiz (`/quiz`) reads whatever bboxes exist in the DB and maps each
// glyph_key back to its `answer` letter via KNOWN_GLYPHS, so marking a new
// letter on the chart immediately makes it quizzable.


export type Position = 'initial' | 'medial' | 'final';
export type LetterCase = 'upper' | 'lower';
// `mvp` = the curated §9 anchor set (allograph-aware trace targets).
// `alphabet` = the rest of the alphabet, markable so the quiz vocabulary grows.
export type GlyphGroup = 'mvp' | 'alphabet';

// Front · middle · end of a word. On a teaching plate like Loth 1866 there is
// usually a single specimen per letter, so the three positions start out
// identical; they diverge only as distinct ductus get traced.
// (The German per-position UI label lives in `@/locales` as POSITION_LABEL.)
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

// Flat (glyph, position) registry derived from LETTERS. Carries the quiz fields
// (`answer`, `letterCase`, `group`) so the quiz can map any marked bbox back to
// a Latin letter, and keeps the KnownGlyph shape callers look up by key.
export interface KnownGlyph {
  key: string;
  glyph: string; // the rendered form shown as the solution (ſ, A, …)
  position: Position;
  label: string;
  // The Latin letter the learner types in the quiz, normalised to lowercase
  // (long-s `ſ` and round-s `s` both answer `s`).
  answer: string;
  letterCase: LetterCase;
  group: GlyphGroup;
}

// Historical §9 anchor keys — they hold real traced data, so they keep the
// `mvp` group; every other derived key is `alphabet`.
const MVP_KEYS = new Set([
  'a-initial',
  'a-medial',
  'd-initial',
  'e-medial',
  'e-final',
  'l-initial',
  'l-medial',
  'n-medial',
  'n-final',
  's-medial',
  's-final',
]);

// Glyphs whose lowercase form is not the letter a learner would type.
const ANSWER_OVERRIDE: Record<string, string> = { ſ: 's', ſt: 'st' };

function makeLabel(letter: Letter, position: Position): string {
  return letter.note ? `${letter.glyph} · ${position} · ${letter.note}` : `${letter.glyph} · ${position}`;
}

function answerOf(glyph: string): string {
  return ANSWER_OVERRIDE[glyph] ?? glyph.toLowerCase();
}

const DERIVED_GLYPHS: KnownGlyph[] = LETTERS.flatMap((letter) =>
  POSITIONS.map((position): KnownGlyph => {
    const key = glyphKeyFor(letter, position);
    return {
      key,
      glyph: letter.glyph,
      position,
      label: makeLabel(letter, position),
      answer: answerOf(letter.glyph),
      letterCase: letter.group === 'upper' ? 'upper' : 'lower',
      group: MVP_KEYS.has(key) ? 'mvp' : 'alphabet',
    };
  }),
);

// Read-only back-compat: an earlier full-alphabet scheme keyed capitals as
// `uc-<letter>` and lowercase gaps as `lc-<letter>` (single chart role). The
// admin sidebar now writes position-based keys, but any bbox already marked
// under the old scheme stays resolvable here so the quiz keeps recognising it.
const LEGACY_ALIASES: KnownGlyph[] = range('a', 'z').flatMap((c): KnownGlyph[] => [
  { key: `uc-${c}`, glyph: c.toUpperCase(), position: 'initial', label: `${c.toUpperCase()} · Versal`, answer: c, letterCase: 'upper', group: 'alphabet' },
  { key: `lc-${c}`, glyph: c, position: 'medial', label: `${c} · klein`, answer: c, letterCase: 'lower', group: 'alphabet' },
]);

export const KNOWN_GLYPHS: KnownGlyph[] = [...DERIVED_GLYPHS, ...LEGACY_ALIASES];

export const LETTER_BY_KEY: Record<string, Letter> = {};
for (const letter of LETTERS) for (const p of POSITIONS) LETTER_BY_KEY[glyphKeyFor(letter, p)] = letter;

// All three position keys (Anfang/Mitte/Ende) for the letter behind `glyphKey`,
// deduped via the override-aware glyphKeyFor (so s / ſ map correctly). Lock and
// unlock fan out across these so a letter is locked "as one" — the sidebar's
// lock icon and the quiz both treat the positions as a single unit.
export function siblingKeys(glyphKey: string): string[] {
  const letter = LETTER_BY_KEY[glyphKey];
  if (!letter) return [glyphKey];
  return Array.from(new Set(POSITIONS.map((p) => glyphKeyFor(letter, p))));
}

// Minimal shape of a stored bbox the split/group helpers need. Kept structural
// (not the full BboxOut) so this module stays free of an API-types import.
interface BboxFlags {
  locked?: boolean;
  split?: boolean;
}

// Is the letter behind `glyphKey` authored per-position (German: aufgetrennt)?
// THE single source of truth for split state — read from the sibling bboxes with
// `.some`, mirroring the lock aggregate: a letter counts as split if ANY of its
// position rows carries the flag. The quiz, the sidebar and ChartPage MUST all
// route through this; inlining a single-key or `.every` check would reintroduce
// the mixed-state inconsistency the lock-as-one fix removed. `.some` also lets a
// sibling added later (defaulting false) still read as split, self-healing.
export function isLetterSplit(glyphKey: string, bboxesByKey: Record<string, BboxFlags>): boolean {
  return siblingKeys(glyphKey).some((k) => bboxesByKey[k]?.split === true);
}

// Collapse the locked glyph keys into quiz units: a unified letter (default)
// becomes ONE entry; a split letter keeps one entry per locked position; legacy
// uc-/lc- aliases (not in LETTER_BY_KEY) stay singletons. For a unified letter
// the representative key prefers has-canonical → medial → first-locked, so the
// quiz crop/animation resolves to a real form. Routes through siblingKeys (hence
// glyphKeyFor), so the s/ſ allographs never merge. THE one place quiz dedup lives.
export function quizKeysFromLocked(
  bboxesByKey: Record<string, BboxFlags>,
  hasCanon: (key: string) => boolean,
): string[] {
  const out: string[] = [];
  const seenGroups = new Set<string>();
  for (const [key, b] of Object.entries(bboxesByKey)) {
    if (!b?.locked) continue;
    if (isLetterSplit(key, bboxesByKey)) {
      out.push(key); // split: each locked position is its own quiz unit
      continue;
    }
    const sibs = siblingKeys(key);
    const groupId = sibs.join('|'); // stable per letter (same for every sibling)
    if (seenGroups.has(groupId)) continue;
    seenGroups.add(groupId);
    const lockedSibs = sibs.filter((k) => bboxesByKey[k]?.locked);
    const letter = LETTER_BY_KEY[key];
    const medialKey = letter ? glyphKeyFor(letter, 'medial') : key;
    const rep =
      lockedSibs.find((k) => hasCanon(k)) ??
      (lockedSibs.includes(medialKey) ? medialKey : undefined) ??
      lockedSibs[0] ??
      key;
    out.push(rep);
  }
  return out;
}

const BY_KEY: Map<string, KnownGlyph> = new Map(KNOWN_GLYPHS.map((g) => [g.key, g]));

export const knownGlyph = (key: string): KnownGlyph | undefined => BY_KEY.get(key);
