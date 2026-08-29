// Lesarten — the alternative readings of a guessed word. For every letter that
// has a documented look-alike in the German cursive (orthographie-regeln.md
// §3, the Schriftkunde's Buchstaben-Besonderheiten, the quiz's Lesefallen
// catalogue), the word with exactly that one letter swapped: a person holding
// an old letter types what they believe it says and gets the readings that
// would look the same on the page — „Muhme" beside „Mnhme" and „Mufme" — to
// compare against the original. One swap per reading, left to right, so the
// list reads in the order of the word; a cap keeps the number of written
// words (one render request each) small.
//
// Typed letters, not glyph_keys: the long ſ is set by the shaping from a plain
// `s` everywhere but at the word end, so the ſ/f trap is the pair s ↔ f for a
// non-final s — a final s is the round s and looks nothing like an f.

export interface Lesart {
  readonly text: string;
  /** Index of the swapped character in the guess. */
  readonly index: number;
  readonly from: string;
  readonly to: string;
}

// Look-alikes by typed letter. Lowercase pairs from the reading-trap catalogue
// (n/u, e/n, n/m, m/w, v/w, i/j, i/e, t/l, f/h, f/t, ſ/f), umlaut ↔ base
// letter (the marks are the whole difference), and the capital confusion
// clusters (L/K/R, N/M, B/V).
export const LOOKALIKES: Readonly<Record<string, readonly string[]>> = {
  n: ['u', 'e', 'm'],
  u: ['n', 'ü'],
  e: ['n', 'i'],
  m: ['n', 'w'],
  w: ['m', 'v'],
  v: ['w'],
  i: ['e', 'j'],
  j: ['i'],
  t: ['l', 'f'],
  l: ['t'],
  f: ['s', 'h', 't'],
  h: ['f'],
  s: ['f'],
  a: ['ä'],
  ä: ['a'],
  o: ['ö'],
  ö: ['o'],
  ü: ['u'],
  L: ['K', 'R'],
  K: ['L', 'R'],
  R: ['L', 'K'],
  N: ['M'],
  M: ['N'],
  B: ['V'],
  V: ['B'],
};

export const MAX_LESARTEN = 8;

// A letter is word-final at the end of the guess or before anything that is
// not a letter (space, comma, full stop …).
const isWordFinal = (chars: readonly string[], i: number): boolean => i === chars.length - 1 || !/\p{L}/u.test(chars[i + 1]);

/** The readings that could look like `guess` on the page — one swapped letter
 * each, in word order, at most `max`, never the guess itself or a duplicate. */
export function lesarten(guess: string, max = MAX_LESARTEN): Lesart[] {
  const chars = [...guess];
  const out: Lesart[] = [];
  const seen = new Set<string>([guess]);
  for (let i = 0; i < chars.length && out.length < max; i++) {
    const from = chars[i];
    const alternatives = LOOKALIKES[from];
    if (!alternatives) continue;
    for (const to of alternatives) {
      if (out.length >= max) break;
      if (from === 's' && to === 'f' && isWordFinal(chars, i)) continue;
      const text = [...chars.slice(0, i), to, ...chars.slice(i + 1)].join('');
      if (seen.has(text)) continue;
      seen.add(text);
      out.push({ text, index: i, from, to });
    }
  }
  return out;
}
