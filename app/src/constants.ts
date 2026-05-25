// Static client-side constants. The frontend hardcodes a single source for v1
// (multi-source is in the DB schema but out of UI scope) and the known set of
// MVP glyph_keys so the sidebar can list expected glyphs even before bboxes
// have been drawn for them.
//
// The (glyph, position) tuple is sent with /trace requests; the glyph_key is
// just an opaque URL/UI identifier.

export const SOURCE_ID = 'loth-1866';

export type Position = 'initial' | 'medial' | 'final';

export interface KnownGlyph {
  key: string;
  glyph: string;
  position: Position;
  label: string;
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
export const KNOWN_GLYPHS: KnownGlyph[] = [
  { key: 'a-initial', glyph: 'a', position: 'initial', label: 'a · initial' },
  { key: 'a-medial', glyph: 'a', position: 'medial', label: 'a · medial' },
  { key: 'd-initial', glyph: 'd', position: 'initial', label: 'd · initial' },
  { key: 'e-medial', glyph: 'e', position: 'medial', label: 'e · medial' },
  { key: 'e-final', glyph: 'e', position: 'final', label: 'e · final' },
  { key: 'l-initial', glyph: 'l', position: 'initial', label: 'l · initial' },
  { key: 'l-medial', glyph: 'l', position: 'medial', label: 'l · medial' },
  { key: 'n-medial', glyph: 'n', position: 'medial', label: 'n · medial' },
  { key: 'n-final', glyph: 'n', position: 'final', label: 'n · final' },
  { key: 's-medial', glyph: 'ſ', position: 'medial', label: 'ſ · medial (long s)' },
  { key: 's-final', glyph: 's', position: 'final', label: 's · final' },
];

export const knownGlyph = (key: string): KnownGlyph | undefined => KNOWN_GLYPHS.find((g) => g.key === key);
