// The pure half of the Schreibtafel's letter detail (LetterDetail.tsx): what
// to show for one written letter — the numbered stroke starts and the stroke
// count for the stepper, the documented look-alikes as glyph keys, and an
// example word for „im Wort sehen". No React, no fetch.

import { LETTERS } from '@/domain/glyphs';
import type { GlyphRenderData } from '@/lib/api';
import { LOOKALIKES } from '@/lib/lesarten';
import type { WordEntry } from '@/sections/quiz/wordBank';

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

/** A short everyday word that shows the letter in use — the shortest modern
 * bank word containing it: a non-final s for the long ſ, a final s for the
 * round s, a word-initial capital for an uppercase letter. Null when the
 * bank has none. */
export function exampleWord(key: string, bank: readonly WordEntry[]): string | null {
  const letter = LETTERS.find((l) => l.base === key);
  if (!letter) return null;
  const glyph = letter.glyph;
  const matches = (w: string): boolean => {
    if (key === 'longs') return /s\p{L}/u.test(w); // an s followed by a letter is set as the long ſ
    if (key === 's') return w.endsWith('s'); // only a final s is the round s
    if (letter.group === 'upper') return w.startsWith(glyph);
    return w.includes(glyph);
  };
  const candidates = bank.filter((e) => e.era === 'modern' && !e.fugen && matches(e.word)).map((e) => e.word);
  if (!candidates.length) return null;
  return candidates.sort((a, b) => a.length - b.length || a.localeCompare(b))[0];
}
