### Added

- **Der Grundwortschatz — the words everyday writing is actually made of.**
  A new curation layer `everyday` in the Wortvorrat, grouped by word class:
  the closed classes and auxiliaries, the everyday full verbs in the forms a
  letter really writes, everyday nouns and adverbs, and the sentence openers
  with their capital (`Ich` and `ich` shape to different glyph sequences and
  are two pool entries on purpose). Own curation rather than a copied list:
  the consulted corpus is subtitle-derived and undercounts exactly what a
  letter needs.
- **The Alltagswelle and the plan block `everyday`.** `pool everyday`
  appends the still-unplanned words as a PACKED wave — four to six short
  words per row, unlike a pin, which gives its one word the whole row. In
  plan order the block does not lead but INTERLEAVES with the frozen strips:
  five everyday rows, two frozen ones, so every Bogen carries both. Additive
  like `pins`, so the plan format stays 2.

### Fixed

- **The commonest words of the language were missing from the strip plan.**
  Of the 50 most frequent German words, 28 were in the Wortvorrat, 13 were
  planned at all, and exactly one stood in the first 40 strips; of the 300
  most frequent, 169 were missing from the pool entirely. The cause was the
  builder: both phases measure a word by the joins it carries, and joins grow
  with word length, so `Schwindsucht` beat `ist` every round. A new phase A0
  lifts every word class to a floor it is owed, and it runs FIRST — phase A
  can consume a whole wave by itself, so a floor queued behind it starves in
  exactly the waves that matter — bounded to a third of a wave so the even
  build-out survives. The head of the print queue drops from 7.0 to 5.0
  letters per word.
