// Lesefallen — the rule the quiz shows after a wrong pick (vision goal 4: a
// miss triggers the structured explanation, not only the solution). Each entry
// pairs the SHOWN form with the GUESSED letter and names the feature that tells
// them apart, in the words of docs/schriftkunde/orthographie-regeln.md §1/§3 and
// the Schriftkunde page's „Buchstaben-Besonderheiten" (ſ/f Querstrich, u-Bogen,
// e ≈ n, the ſ/s position rule, ß = ſʒ, the umlaut marks). Direction matters:
// the sentence describes the form on the card, so n→u and u→n read differently.
// A pair without a documented feature returns null — no explanation is better
// than an invented one; the verdict line then stands alone as before.

import { de, fmt } from '@/locales';
import type { LetterQuestion } from '@/sections/quiz/useQuizEngine';

type RuleId = keyof typeof de.quiz.play.rules;

// Exact pairs, keyed by the shown glyph_key (so the two s-allographs keep their
// own sentences) and the guessed lowercase answer.
const PAIRS: Record<string, RuleId> = {
  'longs>f': 'longsAsF',
  'f>s': 'fAsLongs',
  'n>u': 'nAsU',
  'u>n': 'uAsN',
  'e>n': 'eAsN',
  'n>e': 'nAsE',
  'm>n': 'mAsN',
  'n>m': 'nAsM',
  'i>j': 'iAsJ',
  'j>i': 'jAsI',
  'i>e': 'iAsE',
  't>l': 'tAsL',
  'l>t': 'lAsT',
  'h>f': 'hAsF',
  'f>h': 'fAsH',
  'f>t': 'fAsT',
  't>f': 'tAsF',
  'v>w': 'vAsW',
  'w>v': 'wAsV',
};

// Shown forms whose rule holds against ANY wrong guess: the round s (its
// position rule) and the ß (a ligature, not a letter of its own).
const BY_SHOWN: Record<string, RuleId> = {
  s: 'roundS',
  sz: 'szAsS',
};

// Umlaut ↔ base letter, both directions (the marks are the whole difference).
const UMLAUT_BASE: Record<string, string> = { ae: 'a', oe: 'o', ue: 'u' };
const BASE_UMLAUT: Record<string, string> = { a: 'ä', o: 'ö', u: 'ü' };

// Capital confusion clusters (§3) — the same sentence either way round; the
// rules catalogue names the cluster, not a single distinguishing feature, so
// the sentence sends the learner to the side-by-side comparison.
const CAPITAL_CLUSTERS: string[][] = [
  ['l', 'k', 'r'],
  ['n', 'm'],
  ['b', 'v'],
];

const listCapitals = (letters: string[]): string => {
  const upper = letters.map((l) => l.toUpperCase());
  return upper.length <= 2 ? upper.join(' und ') : `${upper.slice(0, -1).join(', ')} und ${upper[upper.length - 1]}`;
};

/** The guessable letters this shown form is documented to be confused with —
 * the distractors the engine offers first, so a learner who falls into the
 * trap gets the sentence instead of a random miss. Lowercase answers, the
 * shown letter excluded; empty when the catalogue has nothing for the key. */
export function confusablesOf(question: LetterQuestion): string[] {
  const { key, kg } = question;
  const out = new Set<string>();
  if (kg.letterCase === 'upper') {
    for (const cluster of CAPITAL_CLUSTERS) if (cluster.includes(kg.answer)) cluster.forEach((l) => out.add(l));
  } else {
    for (const pair of Object.keys(PAIRS)) {
      const [shown, guessed] = pair.split('>');
      if (shown === key) out.add(guessed);
    }
    if (UMLAUT_BASE[key]) out.add(UMLAUT_BASE[key]);
    if (BASE_UMLAUT[key]) out.add(BASE_UMLAUT[key]);
  }
  out.delete(kg.answer);
  return [...out];
}

/** The explanation for a wrong pick, or null when the catalogue has none for this pair. */
export function explainMiss(question: LetterQuestion, guessed: string): string | null {
  const { key, kg } = question;
  const shown = kg.answer;
  if (guessed === shown) return null;
  const rules = de.quiz.play.rules;

  if (kg.letterCase === 'upper') {
    const cluster = CAPITAL_CLUSTERS.find((c) => c.includes(shown) && c.includes(guessed));
    return cluster ? fmt(rules.capitalCluster, { letters: listCapitals(cluster) }) : null;
  }

  const pair = PAIRS[`${key}>${guessed}`];
  if (pair) return rules[pair];

  if (UMLAUT_BASE[key] === guessed) return fmt(rules.umlautShown, { letter: kg.glyph });
  if (BASE_UMLAUT[key] === guessed) return fmt(rules.umlautGuessed, { letter: kg.glyph });

  const byShown = BY_SHOWN[key];
  return byShown ? rules[byShown] : null;
}
