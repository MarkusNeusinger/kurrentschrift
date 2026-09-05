### Changed

- **The Schreibtafel's „im Wort sehen" example now comes from the curated word
  bank for 64 of 66 letters, not from a hand-written map beside it.** The
  letter detail page (`/tafel?g=<key>`) reads the bundled offline copy of the
  quiz bank, and that copy had been left out of the bank's 2026-08-29 gap
  closure: it still held 42 high-frequency words, which between them never
  contain a j, an x, a ß or 19 of the capitals. So 40 of the 66 spelled glyphs
  had no modern bank word and 35 had none at all — the website audit's finding
  29 — and #476 answered them from a 35-entry constant written next to the
  bank rather than in it. The 35 curated entries the DB bank already carried
  for exactly those letters are now copied into the bundled bank verbatim
  (word, pinned distractor and `era` straight from `quiz_words.json` — the
  same curation, no new source), taking it from 42 to 77 words. The example
  words are therefore era-tagged, shared with the quiz and honest about the
  Fugen rule again, and the offline quiz gets a wider draw as a side effect.
  The constant keeps two entries: German writes a lowercase q only inside the
  qu unit and a lowercase c only inside ch/ck, so their cluster word is where a
  reader actually meets them — no bank word can do better. A test pins that
  every spelled glyph has an example, that only those two reach the constant,
  and that none of them has to fall back to the historic layer.
