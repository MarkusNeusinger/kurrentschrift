// Curated word bank for the word-reading drill. Each entry is a real German
// word plus deliberately form-similar distractors — the typical Kurrent /
// Sütterlin reading confusions (e/n, m/n/u, u/a, h/k, b/l, f/ſ …) — so a wrong
// pick is a genuine misread, not a careless one.
//
// The mix is deliberate (see `docs/concepts/architektur.md` §9 and the quiz
// research note): a modern high-frequency core (what a learner reads first)
// blended with vocabulary from *around 1900* that no longer sits in everyday
// speech but keeps turning up in the old letters this app exists to decode
// (Muhme, Magd, Hornung, „verbleibe …“). Every entry carries an `era` tag so a
// later UI can bias the draw (Alltag ↔ alte Briefe).
//
// Long-s vs round-s is NOT encoded here: `domain/shaping.ts` sets the allographs
// automatically (long ſ initial/medial, round s word-final). We therefore store
// the plain modern spelling — `lesen` renders as `leſen`. The one case the
// automatic rule gets wrong is the Fugen-s / inner syllable-final s of compounds
// (`Donnerstag`, `Haustür` → wrongly long), so such words carry `avoidAutoS` and
// stay out of the word mode until the engine can force a round s.
//
// This is the FULL candidate set. The engine keeps only the words whose every
// Sütterlin glyph is actually locked + traced in the live source (see the word
// pool in useQuizEngine), so a word is never shown half-rendered. Distractors
// are filtered the same way for the comparison, falling back to plain type when
// a distractor isn't fully traced.

export interface WordEntry {
  word: string;
  // Three form-similar alternatives; the engine samples from these for the
  // multiple-choice options. Real words, same case as `word`, hand-picked to
  // fit the rules `similarity` below encodes.
  distractors: string[];
  // 'modern' = today's high-frequency core; 'historic' = still readable but
  // dated, the vocabulary of old letters. Drives an optional era filter.
  era: 'modern' | 'historic';
  // Shown in the answer reveal for words a modern reader may not know
  // (archaisms, dated meanings). Omitted for self-evident everyday words.
  note?: string;
  // Compound with a Fugen-s / inner syllable-final s the automatic ſ-rule would
  // render long by mistake. Excluded from the word mode until shaping can force
  // a round s; kept here so the word is ready the moment it can.
  avoidAutoS?: boolean;
}

export const WORD_BANK: WordEntry[] = [
  // ——— Modern high-frequency core (everyday, no gloss needed) ———
  { word: 'lesen', distractors: ['leben', 'losen', 'lehren'], era: 'modern' },
  { word: 'finden', distractors: ['binden', 'fanden', 'sinken'], era: 'modern' },
  { word: 'waren', distractors: ['malen', 'fahren', 'wagen'], era: 'modern' },
  { word: 'mehr', distractors: ['sehr', 'wehr', 'leer'], era: 'modern' },
  { word: 'haben', distractors: ['hoben', 'heben', 'laben'], era: 'modern' },
  { word: 'gehen', distractors: ['geben', 'sehen', 'nehmen'], era: 'modern' },
  { word: 'das', distractors: ['des', 'dass', 'was'], era: 'modern' },
  { word: 'und', distractors: ['uns', 'nun', 'aus'], era: 'modern' },
  { word: 'der', distractors: ['den', 'dem', 'des'], era: 'modern' },
  { word: 'sein', distractors: ['mein', 'dein', 'kein'], era: 'modern' },
  { word: 'neu', distractors: ['nie', 'nun', 'neun'], era: 'modern' },
  { word: 'alt', distractors: ['als', 'oft', 'kalt'], era: 'modern' },
  { word: 'gut', distractors: ['tut', 'gab', 'tat'], era: 'modern' },
  { word: 'Tag', distractors: ['Tat', 'Rat', 'Tor'], era: 'modern' },
  { word: 'Haus', distractors: ['Maus', 'Laus', 'Hans'], era: 'modern' },
  { word: 'Kind', distractors: ['Rind', 'Wind', 'Kino'], era: 'modern' },
  { word: 'Hand', distractors: ['Wand', 'Land', 'Rand'], era: 'modern' },
  { word: 'Jahr', distractors: ['Haar', 'Paar', 'Bahn'], era: 'modern' },
  { word: 'Zeit', distractors: ['Leid', 'Seite', 'Zeile'], era: 'modern' },
  { word: 'Wort', distractors: ['Ort', 'Wert', 'Sorte'], era: 'modern' },
  { word: 'Buch', distractors: ['Bach', 'Bruch', 'Busch'], era: 'modern' },
  { word: 'Wasser', distractors: ['Messer', 'Wesen', 'Wasen'], era: 'modern' },

  // ——— Vocabulary of old letters (around 1900) — glossed ———
  { word: 'Muhme', distractors: ['Mütze', 'Mulde', 'Mähne'], era: 'historic', note: 'veraltet für Tante oder weibliche Verwandte' },
  { word: 'Base', distractors: ['Hase', 'Vase', 'Nase'], era: 'historic', note: 'veraltet für Cousine' },
  { word: 'Vetter', distractors: ['Wetter', 'Retter', 'Blätter'], era: 'historic', note: 'Cousin, männlicher Verwandter' },
  { word: 'Weib', distractors: ['Leib', 'Wein', 'Reim'], era: 'historic', note: 'früher wertneutral für Frau / Ehefrau' },
  { word: 'Magd', distractors: ['Mahd', 'Made', 'Jagd'], era: 'historic', note: 'Dienstmädchen, Landarbeiterin' },
  { word: 'Knecht', distractors: ['Recht', 'Nacht', 'Gicht'], era: 'historic', note: 'landwirtschaftlicher Dienstbote' },
  { word: 'Stube', distractors: ['Stufe', 'Grube', 'Staub'], era: 'historic', note: 'beheizbares Wohnzimmer' },
  { word: 'Kammer', distractors: ['Hammer', 'Kummer', 'Jammer'], era: 'historic', note: 'kleiner, meist unbeheizter Nebenraum' },
  { word: 'Truhe', distractors: ['Trübe', 'Traube', 'Trage'], era: 'historic', note: 'großer Aufbewahrungskasten mit Deckel' },
  { word: 'Witwe', distractors: ['Wiege', 'Wippe', 'Wanne'], era: 'historic', note: 'Frau eines Verstorbenen (veraltet: Wittib)' },
  { word: 'Pfarrer', distractors: ['Pfeffer', 'Sparren', 'Pfarrei'], era: 'historic', note: 'Geistlicher der Gemeinde' },
  { word: 'Taufe', distractors: ['Taube', 'Traube', 'Haube'], era: 'historic', note: 'kirchliche Namensgebung' },
  { word: 'Hornung', distractors: ['Wohnung', 'Rechnung', 'Ordnung'], era: 'historic', note: 'alter Name für den Februar' },
  { word: 'selig', distractors: ['ledig', 'eilig', 'wenig'], era: 'historic', note: 'verstorben („mein seliger Vater“); auch: glückselig' },
  { word: 'weiland', distractors: ['weinen', 'weilen', 'weichen'], era: 'historic', note: 'einst, ehemals; vor einem Namen: der verstorbene …' },
  { word: 'ergebenst', distractors: ['ergeben', 'erhoben', 'gegeben'], era: 'historic', note: 'unterwürfige Grußformel: „Ihr ergebenster …“' },
  { word: 'verbleibe', distractors: ['verbleibt', 'verweile', 'verkleide'], era: 'historic', note: 'Schlussformel: „so verbleibe ich …“' },

  // ——— Compound with a Fugen-s the automatic rule renders wrong ———
  // Excluded from the word mode (avoidAutoS) until shaping can force a round s;
  // `Donnerstag` = Donners·tag, the junction s is round, not long.
  { word: 'Donnerstag', distractors: ['Sonntag', 'Freitag', 'Feiertag'], era: 'modern', note: 'Fugen-s: rundes s (Donners·tag)', avoidAutoS: true },
];

// ——— Distractor vetting (curation / future generation helper) ———
//
// Not called at render time — the lists above are hand-picked — but this
// encodes the rules used while curating them, kept executable so new entries and
// a future corpus-fed generator can be scored the same way. It advises; it does
// not enforce the bank.

// Typical Kurrent/Sütterlin misreadings: unordered letter pairs that look alike
// in the cursive hand. A distractor differing from the answer only in these is a
// plausible misread; one differing in arbitrary letters is a careless option.
const CONFUSABLE: ReadonlyArray<readonly [string, string]> = [
  ['e', 'n'], ['n', 'u'], ['u', 'a'], ['n', 'm'], ['m', 'w'],
  ['h', 'k'], ['h', 'b'], ['b', 'l'], ['k', 'l'],
  ['f', 's'], ['f', 'ſ'], ['c', 'e'], ['r', 'x'], ['g', 'z'],
  ['i', 'e'], ['t', 'l'],
];

const isConfusablePair = (a: string, b: string): boolean =>
  CONFUSABLE.some(([x, y]) => (a === x && b === y) || (a === y && b === x));

// Initial-capital (a noun like `Haus`) vs. lowercase (`das`): a different
// reading target, not a confusion. Non-letters (upper === lower) count as
// lowercase.
const isCapitalized = (w: string): boolean => {
  const first = w[0];
  return first !== undefined && first === first.toUpperCase() && first !== first.toLowerCase();
};

// Heuristic distractor quality for (answer, candidate): higher is a better
// (more confusable) distractor. Encodes the rules asked for — near-equal length,
// a shared start OR end letter, and same-position differences that are cursive
// confusions rather than arbitrary swaps. A candidate equal to the answer, of a
// different case pattern, or too far in length scores 0.
export function similarity(answer: string, candidate: string): number {
  if (!answer || !candidate || answer === candidate) return 0;
  if (isCapitalized(answer) !== isCapitalized(candidate)) return 0; // rule: same case pattern
  const a = [...answer];
  const b = [...candidate];
  if (Math.abs(a.length - b.length) > 1) return 0; // rule: length ±1

  let score = 0;
  if (a[0].toLowerCase() === b[0]?.toLowerCase()) score += 2; // shared start
  if (a[a.length - 1].toLowerCase() === b[b.length - 1]?.toLowerCase()) score += 2; // shared end
  if (score === 0) return 0; // rule: must share a start or end letter

  if (a.length === b.length) {
    for (let i = 0; i < a.length; i += 1) {
      const x = a[i].toLowerCase();
      const y = b[i].toLowerCase();
      if (x === y) continue;
      score += isConfusablePair(x, y) ? 1 : -2; // confusion rewarded, noise penalised
    }
  } else {
    score -= 1; // a length difference is a milder confusion than an equal-length swap
  }
  return score;
}

// A candidate is an acceptable distractor when it clears a positive bar.
export const isPlausibleDistractor = (answer: string, candidate: string): boolean =>
  similarity(answer, candidate) > 0;
