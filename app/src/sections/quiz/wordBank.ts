// Curated word bank for the word-reading drill. Each entry is a common short
// German word plus deliberately form-similar distractors — the typical Kurrent /
// Sütterlin reading confusions (e/n, m/n/u, u/a, h/k, b/l, f/ſ …) — so a wrong
// pick is a genuine misread, not a careless one.
//
// This is the FULL candidate set. The engine keeps only the words whose every
// Sütterlin glyph is actually locked + traced in the live source (see the word
// pool in useQuizEngine), so a word is never shown half-rendered. Distractors
// are filtered the same way for the comparison, falling back to plain type when
// a distractor isn't fully traced.

export interface WordEntry {
  word: string;
  // Three form-similar alternatives; the engine samples from these for the
  // multiple-choice options.
  distractors: string[];
}

export const WORD_BANK: WordEntry[] = [
  { word: 'lesen', distractors: ['leben', 'losen', 'lehren'] },
  { word: 'finden', distractors: ['binden', 'fanden', 'sinken'] },
  { word: 'waren', distractors: ['malen', 'fahren', 'wagen'] },
  { word: 'mehr', distractors: ['sehr', 'wehr', 'leer'] },
  { word: 'haben', distractors: ['hoben', 'heben', 'halten'] },
  { word: 'gehen', distractors: ['geben', 'sehen', 'nehmen'] },
  { word: 'das', distractors: ['des', 'dass', 'was'] },
  { word: 'und', distractors: ['uns', 'nun', 'aus'] },
  { word: 'der', distractors: ['den', 'dem', 'des'] },
  { word: 'sein', distractors: ['mein', 'dein', 'kein'] },
  { word: 'Tag', distractors: ['Tat', 'Rat', 'Tor'] },
  { word: 'Haus', distractors: ['Maus', 'Hans', 'Raus'] },
];
