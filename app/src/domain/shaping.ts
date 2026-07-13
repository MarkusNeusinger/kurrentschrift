// Text shaping for the German cursive scripts: turn a typed word or sentence
// into the ordered sequence of canonical glyph_keys. Framework-free (no React,
// no API). Word composition + geometry moved server-side to `core/shaping.py` +
// `core/compose.py`; this module is the TS twin trimmed to ONLY what the quiz
// word-bank gating needs — the `text → glyph_keys` mapping (`shapeText` +
// `glyphKeysOf`). It stays in sync with `core/shaping.py` on that mapping,
// pinned mechanically by the shared fixture `tests/fixtures/shaping_cases.json`
// (asserted here in `shaping.test.ts` and Python-side in `tests/test_tri_script.py`).
// The client-side compose fallbacks that used to live here (ligature-decompose,
// Fuge stripping for display) are Python-only now that composition is server-side.
//
// Two orthographic rules carry the historical look (architektur.md §3/§4):
//
//   1. Long-s vs round-s (Lang-s ſ / Schluss-s s). German Kurrent/Sütterlin
//      writes the long-s ſ at the start and in the middle of a word and the
//      round s only at the end. These are *separate allographs* with their own
//      ductus (`longs-*` / `s-medial` for ſ, `s-final` / `s-round-medial` for
//      the round s), not one letter with a transition. We approximate the
//      syllable rule with the pragmatic "ſ unless word-final" convention used by
//      historical type — good enough for the public live-writing demo; a full
//      syllabifier is post-MVP (orthographie-regeln.md §1.2). Until then a
//      Fuge marker `|` in the input lets the caller force the round s at a
//      morpheme boundary a compound needs it (`Haus|tür`, `Arbeits|amt`): the s
//      right before the `|` renders round, no ſt/ligature spans the boundary,
//      and the marker itself produces no glyph. For display the caller shows the
//      unmarked `word`/label form; only the render form (`entry.fugen`, passed
//      to `shapeText`) carries the `|`.
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
  // The canonical glyph_key to fetch + render, or null for a space / a
  // character with no glyph at all, which renders as an advance-only gap.
  key: string | null;
  // The source character(s) this slot stands for (availability UI / debugging).
  text: string;
  position: Position | null;
  // True for the closed-set ligatures (ch, ck, tz, ſt, qu, ß).
  ligature: boolean;
  // True for an inter-word space — renders as horizontal advance only and
  // breaks the connecting stroke (no Übergang spans a word gap).
  space: boolean;
  // False for the detached glyph classes (digits, punctuation): they render
  // but no Übergang ever enters or leaves them. Mirrors core/shaping.py.
  joins: boolean;
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

// Alias characters folding onto a registry glyph (typographic apostrophe,
// closing-quote variants, hyphen variants, em dash). The straight double
// quote is resolved by occurrence parity within the word instead (see the
// quoteAllograph token flag). Mirrors the alias entries in core/shaping.py's
// _PUNCT.
const CHAR_ALIASES: Record<string, string> = {
  '’': "'", // ’
  '”': '“', // ” → “
  '‐': '-',
  '‑': '-',
  '—': '–', // — → –
};
const STRAIGHT_QUOTE = '"';
const QUOTE_LOW = LETTERS.find((l) => l.base === 'quote-low');
const QUOTE_HIGH = LETTERS.find((l) => l.base === 'quote-high');

// A cased lowercase letter (so an uppercase initial is never folded into a
// lowercase ligature). `toLowerCase() === c` is true for non-letters too, hence
// the extra `toUpperCase() !== c` guard.
function isLowercaseLetter(c: string): boolean {
  return c === c.toLowerCase() && c !== c.toUpperCase();
}

// The Fuge marker: a morpheme boundary the caller places in a compound so the
// preceding s renders round (Schluss-s) and no ligature spans it. Internal only:
// the quiz passes the pre-marked render form (`entry.fugen`) straight through.
const FUGE = '|';

interface RawToken {
  letter: Letter | null; // null => unknown char (gap) or a deferred allograph
  text: string;
  ligature: boolean;
  sAllograph: boolean; // a lowercase s/ſ whose long-vs-round form depends on position
  forceRound: boolean; // an s immediately before a Fuge — always the round allograph
  joins: boolean; // false: digits/punctuation/unknown — detached, no Übergang
  quoteAllograph: boolean; // a straight " resolved low/high by occurrence parity
}

// Greedy left-to-right tokeniser over one whitespace-free word.
function tokenizeWord(word: string): RawToken[] {
  const chars = [...word];
  const tokens: RawToken[] = [];
  let i = 0;
  while (i < chars.length) {
    const c = chars[i];
    const next = chars[i + 1];
    // Fuge marker: a morpheme boundary carrying no glyph. Consumed here; its
    // only effect is on the preceding s (handled in the s branch below).
    if (c === FUGE) {
      i += 1;
      continue;
    }
    // Two-character ligatures, only when the cluster opens on a lowercase letter.
    if (next !== undefined && isLowercaseLetter(c)) {
      const pair = (c + next).toLowerCase();
      if (pair === 'ch' || pair === 'ck' || pair === 'tz' || pair === 'qu') {
        tokens.push({ letter: LIGATURE_BY_FORM.get(pair) ?? null, text: c + next, ligature: true, sAllograph: false, forceRound: false, joins: true, quoteAllograph: false });
        i += 2;
        continue;
      }
      // ſt-ligature: a long-s followed by t (the s before t is always a long-s
      // context). Accept both the typed 's' and an already-long 'ſ'. A Fuge
      // between them (`Aus|tritt`) blocks it — `next` is then the marker, not t.
      if (pair === 'st' || pair === 'ſt') {
        tokens.push({ letter: LIGATURE_BY_FORM.get('ſt') ?? null, text: c + next, ligature: true, sAllograph: false, forceRound: false, joins: true, quoteAllograph: false });
        i += 2;
        continue;
      }
    }
    // ß — a single-character ligature unit (Eszett).
    if (c === 'ß') {
      tokens.push({ letter: LIGATURE_BY_FORM.get('ß') ?? null, text: c, ligature: true, sAllograph: false, forceRound: false, joins: true, quoteAllograph: false });
      i += 1;
      continue;
    }
    // Lowercase s/ſ: defer the long-vs-round choice to position assignment,
    // unless a Fuge marker follows — then it's the round Schluss-s of a
    // compound's inner boundary (`Haus|tür`), regardless of position.
    if ((c === 's' || c === 'ſ') && isLowercaseLetter(c)) {
      tokens.push({ letter: null, text: c, ligature: false, sAllograph: true, forceRound: next === FUGE, joins: true, quoteAllograph: false });
      i += 1;
      continue;
    }
    // Straight double quote: low vs high resolved by occurrence parity („…“).
    if (c === STRAIGHT_QUOTE) {
      tokens.push({ letter: null, text: c, ligature: false, sAllograph: false, forceRound: false, joins: false, quoteAllograph: true });
      i += 1;
      continue;
    }
    const letter = LETTER_BY_CHAR.get(c) ?? LETTER_BY_CHAR.get(CHAR_ALIASES[c] ?? '') ?? null;
    tokens.push({ letter, text: c, ligature: false, sAllograph: false, forceRound: false, joins: letter !== null && letter.joins !== false, quoteAllograph: false });
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
  // Positions are assigned per RUN of same-joins-class tokens: a trailing
  // comma or a digit block must not steal the word-final position from the
  // last letter — "Haus," keeps the round Schluss-s — and a detached block
  // ("1922") resolves its own initial/medial/final internally. Mirrors
  // core/shaping.py::_assign_positions.
  const runs: RawToken[][] = [];
  for (const t of tokens) {
    const last = runs[runs.length - 1];
    if (last && last[last.length - 1].joins === t.joins) last.push(t);
    else runs.push([t]);
  }
  const out: GlyphSlot[] = [];
  let straightQuotes = 0; // occurrences within this word, for low/high pairing
  for (const run of runs) {
    run.forEach((t, runIdx) => {
      const position = positionOf(runIdx, run.length);
      // Long-s in initial/medial position, round s at the end of its letter
      // run — or forced round at a Fuge boundary regardless of position.
      if (t.sAllograph) {
        const letter = t.forceRound || position === 'final' ? ROUND_S : LONG_S;
        out.push({
          key: letter ? glyphKeyFor(letter, position) : null,
          text: t.text,
          position,
          ligature: false,
          space: false,
          joins: true,
        });
        return;
      }
      // Straight double quote ("): German quotes pair low-then-high („Ja“).
      // Resolved by occurrence parity within the word, so a quote after
      // other punctuation — ("Ja") — still opens low.
      if (t.quoteAllograph) {
        const letter = straightQuotes % 2 === 0 ? QUOTE_LOW : QUOTE_HIGH;
        straightQuotes += 1;
        out.push({
          key: letter ? glyphKeyFor(letter, position) : null,
          text: t.text,
          position,
          ligature: false,
          space: false,
          joins: false,
        });
        return;
      }
      if (!t.letter) {
        out.push({ key: null, text: t.text, position: null, ligature: false, space: false, joins: false });
        return;
      }
      out.push({ key: glyphKeyFor(t.letter, position), text: t.text, position, ligature: t.ligature, space: false, joins: t.joins });
    });
  }
  return out;
}

// One word → its ordered glyph slots (with positions + allographs resolved).
// Internal: `shapeText` is the only entry point the quiz uses.
function shapeWord(word: string): GlyphSlot[] {
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
      out.push({ key: null, text: ' ', position: null, ligature: false, space: true, joins: false });
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
