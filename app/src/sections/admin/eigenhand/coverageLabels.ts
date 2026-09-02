// How the Eigenhand coverage grid names a key or an item.
//
// The grid shows every glyph and every join the plan asks the hand to write, so
// what it prints has to BE the character: a wall of spelled-out keys („semicolon"
// among twelve punctuation marks) hides the shape of the coverage, which is the
// one thing the grid exists to show.
//
// The key→character map is DERIVED from `domain/glyphs.ts`, not hand-kept. It
// used to be a literal list maintained as a second mirror of core/shaping.py's
// `_PUNCT`/`_LIGATURES`, and by the audit of 2026-09-02 it had drifted by two
// entries (`semicolon`, `dash`) — a hand-written copy of a list that already has
// a copy in the same codebase can only ever drift. `LETTERS` is that copy, the
// one the whole SPA reads, so reading it here removes the second source rather
// than adding a test to watch it.

import { LETTERS } from '@/domain/glyphs';

// Only the keys that are SPELLED OUT need translating: a base equal to its own
// glyph (`a`, `7`, `ch`) already prints correctly on its own.
const KEY_GLYPHS: Record<string, string> = Object.fromEntries(
  LETTERS.filter((letter) => letter.base !== letter.glyph).map((letter) => [letter.base, letter.glyph]),
);

export const glyphOf = (key: string): string => KEY_GLYPHS[key] ?? key;

// Exported for the drift test only: the point of the derivation is that this
// map can never again be shorter than the registry it mirrors.
export const KEY_GLYPH_MAP = KEY_GLYPHS;
