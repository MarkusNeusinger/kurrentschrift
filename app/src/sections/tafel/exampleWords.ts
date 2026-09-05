// The LAST rung of the „im Wort sehen" ladder (letterDetail.ts): a checked
// word for the glyphs the quiz word bank cannot serve. The bank stays the
// first source — it is curated, era-tagged, source-backed and shared with the
// quiz — so this map is consulted only when neither a modern nor a historic
// bank word shows the letter.
//
// Website audit 2026-09-02 (finding 29) found 39 of 69 letters without any
// example word, among them j k p q x y z ä ö ü ß and 19 capitals. #476 filled
// that hole from here, with 35 hand-written entries beside the bank rather
// than in it. The bundled bank has since been extended with the curated
// entries the DB bank already carried for those letters (`quiz/wordBank.ts`,
// „Letter coverage"), so 64 of the 66 spelled glyphs are answered by the bank
// itself and only these two remain.
//
// Two letters German cannot show on their own, and that is not a gap in the
// bank: a lowercase q only ever appears inside the qu unit, a lowercase c only
// inside ch/ck (outside names and loanwords). Their word is therefore the
// cluster word — which is exactly where a reader meets them. Curation rules
// for anything that might join them: an ordinary modern word; it must SHOW the
// letter as the letter is written (a capital opens the word, a lowercase one
// sits inside it); and no letter of it may fold into a cluster that hides it —
// a lowercase `ch ck tz qu st` pair is ONE glyph (`domain/shaping.ts`), so
// „Nacht" is not an N-word and „Obst" is not an O-word.
export const EXAMPLE_WORDS: Record<string, string> = {
  c: 'Buch',
  q: 'bequem',
};
