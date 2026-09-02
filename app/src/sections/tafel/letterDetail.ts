// The pure half of the Schreibtafel's letter detail (LetterDetail.tsx): what
// to show for one written letter — the numbered stroke starts and the stroke
// count for the stepper, the documented look-alikes as glyph keys, and an
// example word for „im Wort sehen". No React, no fetch.

import { LETTERS } from '@/domain/glyphs';
import { glyphKeysOf, shapeText } from '@/domain/shaping';
import type { GlyphRenderData } from '@/lib/api';
import { LOOKALIKES } from '@/lib/lesarten';
import type { WordEntry } from '@/sections/quiz/wordBank';
import { EXAMPLE_WORDS } from '@/sections/tafel/exampleWords';

type Pt = [number, number];

// Display character → glyph_key (ä → ae, ſ → longs, A → A …), from the one
// letter registry; the reverse of LETTER_BY_KEY.
const KEY_BY_GLYPH: Record<string, string> = {};
for (const letter of LETTERS) KEY_BY_GLYPH[letter.glyph] = letter.base;

/** The first point of every stroke's centerline, in writing order — where the
 * numbered markers go. A payload without centerlines has nothing to number. */
export function strokeStarts(data: GlyphRenderData): Pt[] {
  const lines = data.centerlines_template ?? [];
  return lines.filter((l) => l.length > 0).map((l) => [l[0][0], l[0][1]] as Pt);
}

/** How many pen strokes the payload draws. */
export function strokeCount(data: GlyphRenderData): number {
  return data.outline_paths?.length ?? data.outline_polygons?.length ?? (data.outline_polygon ? 1 : 0);
}

/** The documented look-alikes of a written letter as glyph keys, in catalogue
 * order. Typed-letter table (lib/lesarten): the long ſ is typed `s`, so it
 * gets the s-row (f) plus its allograph, the round s gets the long ſ; keys
 * the registry does not know are dropped. */
export function lookalikeKeys(key: string): string[] {
  if (key === 's') return ['longs'];
  const typed = key === 'longs' ? 's' : (LETTERS.find((l) => l.base === key)?.glyph ?? key);
  const chars = LOOKALIKES[typed] ?? [];
  const keys = chars.map((c) => KEY_BY_GLYPH[c]).filter((k): k is string => !!k && k !== key);
  if (key === 'longs') keys.push('s');
  return [...new Set(keys)];
}

/** An example word for the „im Wort sehen" bridge into the Federprobe. */
export interface ExampleWord {
  word: string;
  /** True for a word from the bank's historic layer (the vocabulary of old
   * letters, not of today's speech) — the link says so rather than passing
   * „Muhme" off as everyday German. */
  historic: boolean;
}

/** A short word that shows the letter in use, picked in three rungs: the
 * shortest MODERN bank word that shows it, else the shortest HISTORIC one,
 * else the checked constant in exampleWords.ts. Null only for the glyphs no
 * word shows — digits and punctuation.
 *
 * „Shows it" is asked of the shaper itself (domain/shaping), not of the
 * spelling: a word shows the letter when the slots it is written in carry
 * this glyph_key. That is what makes „sein" a ſ-word but „Fenster" an
 * ſt-word, „das" an s-word but „sein" not, and „Buch" no h-word at all — the
 * h there is written inside the ch ligature, where nobody can point at it.
 * Words with a Fuge marker stay out: their render form carries a `|` the
 * Federprobe link would not pass on, so the s at the seam would come out long
 * (`Donners|tag`). */
export function exampleWord(key: string, bank: readonly WordEntry[]): ExampleWord | null {
  const letter = LETTERS.find((l) => l.base === key);
  if (!letter) return null;
  const matches = (w: string): boolean => glyphKeysOf(shapeText(w)).includes(key);
  const shortest = (era: WordEntry['era']): string | undefined =>
    bank
      .filter((e) => e.era === era && !e.fugen && matches(e.word))
      .map((e) => e.word)
      .sort((a, b) => a.length - b.length || a.localeCompare(b))[0];

  const modern = shortest('modern');
  if (modern) return { word: modern, historic: false };
  const historic = shortest('historic');
  if (historic) return { word: historic, historic: true };
  const fallback = EXAMPLE_WORDS[key];
  return fallback ? { word: fallback, historic: false } : null;
}
