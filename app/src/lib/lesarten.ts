// The look-alike table of the German cursive, keyed by TYPED letter: which
// letters a reader can mistake for one another (orthographie-regeln.md §3,
// the Schriftkunde's Buchstaben-Besonderheiten, the quiz's Lesefallen
// catalogue). Lowercase pairs (n/u, e/n, n/m, m/w, v/w, i/j, i/e, t/l, f/h,
// f/t, ſ/f as s ↔ f — the long ſ is typed `s`), umlaut ↔ base letter (the
// marks are the whole difference), the capital confusion clusters (L/K/R,
// N/M, B/V). Symmetric: if n reads as u, u reads as n (pinned by the test).
//
// Consumers: the Tafel's letter detail (its look-alike strip) and the crawler
// page of the Lesart page (the table as text). The READINGS themselves —
// real words that look like a guess — come from the API (`GET /lesarten`),
// whose Python twin of this table (core/lesarten) buckets the vocabulary;
// tests/test_lesarten_core.py holds the two tables together. Since
// 2026-08-30 no reading is generated here: a letter swap without a word
// behind it („Mnhme") is not a Lesart (owner).

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
