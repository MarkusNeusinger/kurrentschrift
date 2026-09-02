// The LAST rung of the „im Wort sehen" ladder (letterDetail.ts): one checked
// everyday word per glyph the quiz word bank cannot serve. The bank stays the
// first source — it is curated, era-tagged and shared with the quiz — so this
// map is consulted only when neither a modern nor a historic bank word shows
// the letter. Website audit 2026-09-02 (finding 29): 39 of 69 letters had no
// example word at all, among them j k p q x y z ä ö ü ß and 19 capitals, so
// more than half of the letter detail pages ended without the bridge into the
// Federprobe.
//
// Curation rules, in order:
//   1. an ordinary modern German word — no proper nouns, no learned rarities;
//   2. it must SHOW the letter the way the letter is written: a capital opens
//      the word, a lowercase letter sits inside it;
//   3. it must be one the composer can write, so no letter of the word may
//      fold into a cluster the source has not been taught. Watch the closed
//      ligature set (`domain/shaping.ts`): a lowercase `ch ck tz qu st` pair
//      becomes ONE glyph, so „Nacht" is not an N-word and „Obst" is not an
//      O-word. The five ligature entries below are the deliberate exception:
//      their own word must contain their own cluster, and it renders complete
//      as soon as that ligature is traced on the chart.
//
// Two letters German cannot show on their own, and their entries say so:
// a lowercase q only ever appears in the qu unit, a lowercase c only inside
// ch/ck — their word is the cluster word, which is where a reader meets them.
export const EXAMPLE_WORDS: Record<string, string> = {
  // lowercase
  c: 'Buch',
  j: 'jeder',
  k: 'danke',
  p: 'Papier',
  q: 'bequem',
  x: 'Hexe',
  y: 'Physik',
  z: 'zehn',
  ae: 'spät',
  oe: 'hören',
  ue: 'für',
  // capitals
  A: 'Abend',
  C: 'Chor',
  D: 'Dorf',
  E: 'Erde',
  F: 'Feder',
  G: 'Garten',
  I: 'Insel',
  L: 'Land',
  N: 'Name',
  O: 'Ofen',
  Q: 'Quelle',
  R: 'Rose',
  // Not „Stube": a capital S before a t is written as the St cluster, which
  // leaves no S to point at.
  S: 'Sonne',
  U: 'Uhr',
  X: 'Xylophon',
  Y: 'Ypsilon',
  Ae: 'Äpfel',
  Oe: 'Öl',
  Ue: 'Übung',
  // the closed ligature set: the cluster IS the letter here
  ck: 'Zucker',
  tz: 'Katze',
  longst: 'Fenster',
  qu: 'bequem',
  sz: 'Fuß',
};
