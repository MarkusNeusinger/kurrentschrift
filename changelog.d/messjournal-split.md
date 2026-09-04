### Changed

- **The campaign journal is its own document.** §14 of
  `docs/reference/qualitaetsmetrik.md` — 7 366 lines, two thirds of the file
  and the single largest thing an AI session had to load to answer a question
  about the metric — moved verbatim into `docs/reference/messjournal.md`, with
  `docs/reference/messjournal-archiv.md` waiting for the entries whose arm is
  finished. The move is provably pure: sorting the lines of the old file and of
  the new ones gives the same multiset once the 93 lines of new prose are
  subtracted, so no entry changed a word and all 83 anchors are unchanged. The
  section keeps the number **14** because its entries are cited as „§14
  «Titel»“ about 350 times across the repo; a one-off script rewrote the 120
  citations that name the file, leaving `CHANGELOG.md` and the two dated audit
  notes of 2026-09-02 alone as historical records. `tools.docs_register` reads
  the journal from its new home, accepts a register row that links into the
  archive page, and keeps taking the headline pair from the metric document's
  status blockquote, which is still the one place the current headlines stand.
