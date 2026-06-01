// Static client-side constants. The frontend hardcodes a single source for v1
// (multi-source is in the DB schema but out of UI scope) and the known set of
// markable glyph_keys so the sidebar can list expected glyphs even before
// bboxes have been drawn for them.
//
// The (glyph, position) tuple is sent with /trace requests; the glyph_key is
// just an opaque URL/UI identifier. The quiz (`/quiz`) reads whatever bboxes
// exist in the DB and maps each glyph_key back to its `answer` letter via this
// table, so marking a new letter on the chart immediately makes it quizzable.

export const SOURCE_ID = 'loth-1866';

export type Position = 'initial' | 'medial' | 'final';
export type LetterCase = 'upper' | 'lower';
// `mvp` = the curated §9 anchor set (allograph-aware, trace targets).
// `alphabet` = the rest of A–Z / a–z, markable so the quiz vocabulary can grow.
export type GlyphGroup = 'mvp' | 'alphabet';

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

// MVP set per `docs/concepts/architektur.md` §9 + medial-ſ allograph split.
//
// `position` here is the *chart role* of the allograph form (where Loth shows
// it on the teaching plate), NOT the position the form must occupy in running
// text. The round-s (`s` / `s-final`) for example also occurs word-internally
// at morpheme boundaries in compounds (`Aus-flug`, `Haus-thür`); the text→
// template mapping is a separate orthography layer planned for M4+
// (`core/orthography.py`). See `docs/reference/orthographie-regeln.md` §1 and
// `docs/proposals/planaenderungen.md` Vorschlag A.
const MVP_GLYPHS: KnownGlyph[] = [
  { key: 'a-initial', glyph: 'a', position: 'initial', label: 'a · initial', answer: 'a', letterCase: 'lower', group: 'mvp' },
  { key: 'a-medial', glyph: 'a', position: 'medial', label: 'a · medial', answer: 'a', letterCase: 'lower', group: 'mvp' },
  { key: 'd-initial', glyph: 'd', position: 'initial', label: 'd · initial', answer: 'd', letterCase: 'lower', group: 'mvp' },
  { key: 'e-medial', glyph: 'e', position: 'medial', label: 'e · medial', answer: 'e', letterCase: 'lower', group: 'mvp' },
  { key: 'e-final', glyph: 'e', position: 'final', label: 'e · final', answer: 'e', letterCase: 'lower', group: 'mvp' },
  { key: 'l-initial', glyph: 'l', position: 'initial', label: 'l · initial', answer: 'l', letterCase: 'lower', group: 'mvp' },
  { key: 'l-medial', glyph: 'l', position: 'medial', label: 'l · medial', answer: 'l', letterCase: 'lower', group: 'mvp' },
  { key: 'n-medial', glyph: 'n', position: 'medial', label: 'n · medial', answer: 'n', letterCase: 'lower', group: 'mvp' },
  { key: 'n-final', glyph: 'n', position: 'final', label: 'n · final', answer: 'n', letterCase: 'lower', group: 'mvp' },
  { key: 's-medial', glyph: 'ſ', position: 'medial', label: 'ſ · medial (long s)', answer: 's', letterCase: 'lower', group: 'mvp' },
  { key: 's-final', glyph: 's', position: 'final', label: 's · final', answer: 's', letterCase: 'lower', group: 'mvp' },
];

// Lowercase letters already covered (as allographs) by the MVP set above — we
// don't re-add a generic form for them, so the sidebar stays unambiguous.
const MVP_LOWER = new Set(MVP_GLYPHS.filter((g) => g.letterCase === 'lower').map((g) => g.answer));

const A_TO_Z = Array.from({ length: 26 }, (_, i) => String.fromCharCode(97 + i)); // 'a'…'z'

// Full alphabet, markable so the quiz vocabulary can grow beyond the MVP
// anchors. Capitals are the learner's main pain point (recognising Kurrent
// majuscules), so all 26 are listed; lowercase only fills the gaps the MVP set
// doesn't already cover. Position is a sensible default for an eventual trace,
// not a hard constraint (capitals open words → `initial`).
const UPPER_GLYPHS: KnownGlyph[] = A_TO_Z.map((c) => ({
  key: `uc-${c}`,
  glyph: c.toUpperCase(),
  position: 'initial',
  label: `${c.toUpperCase()} · Versal`,
  answer: c,
  letterCase: 'upper',
  group: 'alphabet',
}));

const LOWER_GLYPHS: KnownGlyph[] = A_TO_Z.filter((c) => !MVP_LOWER.has(c)).map((c) => ({
  key: `lc-${c}`,
  glyph: c,
  position: 'medial',
  label: `${c} · klein`,
  answer: c,
  letterCase: 'lower',
  group: 'alphabet',
}));

export const KNOWN_GLYPHS: KnownGlyph[] = [...MVP_GLYPHS, ...UPPER_GLYPHS, ...LOWER_GLYPHS];

const BY_KEY: Map<string, KnownGlyph> = new Map(KNOWN_GLYPHS.map((g) => [g.key, g]));

export const knownGlyph = (key: string): KnownGlyph | undefined => BY_KEY.get(key);

// Scripts selectable in the quiz. Only Kurrent (the Loth 1866 source) has data
// today; the others are shown disabled so the menu reflects the planned scope.
export interface ScriptOption {
  id: string;
  label: string;
  available: boolean;
}

export const SCRIPTS: ScriptOption[] = [
  { id: 'kurrent', label: 'Kurrent', available: true },
  { id: 'suetterlin', label: 'Sütterlin', available: false },
  { id: 'offenbacher', label: 'Offenbacher', available: false },
];
