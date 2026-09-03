### Fixed

- **The glyph bench's fixture export let a Laufform overwrite the chart row it
  was supposed to sit beside.** Every variant of a key was written into the same
  `<glyph_key>/` directory, and because the rows come back ordered by
  `(glyph_key, variant)` the Laufform (variant 100) ran last and won. A Laufform
  is a median over word occurrences — no chart cell, no stylus path — so the
  bench could not re-derive it: the first re-export after the LF11 write came
  back with 44 crashes out of 84 index entries. The export now takes only rows
  that carry a stylus path, which is the property the bench actually needs and
  catches an untraced form variant too, and it names each row it left behind
  instead of shrinking quietly (#516).
- **The same export merged into its output directory instead of replacing it.**
  Glyph keys changed shape when migration `0017` dropped the position suffixes,
  so the June root's `A-final` directories had been sitting beside current ones
  ever since, indistinguishable from live fixtures — 136 directories serving 84
  index entries. The root is replaced on every export — built in a staging
  sibling and swapped in at the end, so a failure partway through costs neither
  the old baseline nor a usable new one — and the index now records each row's
  `variant` so a second row on one key is visible (#516).
- **Two glyphlab tests were asserting against glyph keys that no longer exist.**
  They loaded `i-initial` and `longs-final`, suffixes migration `0017` dropped,
  and passed only because the June fixture root still carried them — in CI they
  never ran at all, since the fixtures are gitignored and the module skips
  without them. They now use `i` and `longs` and name their source, because
  those keys live in both roots since `0017` and a bare lookup was resolving to
  the wrong script (#516).

### Changed

- **Declared re-baseline of the glyph-bench fixture roots, which were nearly
  three months old.** They still held the June export, from before migration
  `0017` and before any Laufform existed. Re-exported, both scripts measured one
  per run with BLAS pinned: Sütterlin 0.182809 → 0.212277 and Kurrent 0.125104 →
  0.121916. Neither move is a pipeline change — every glyph present in both the
  old and the new root scores bit-identically, and the whole difference is the
  population: 28 glyphs authored since June joined the Sütterlin set (mean loss
  0.246530 against the old set's 0.184069), and one Kurrent glyph swapped out
  for another. The word bench was re-exported in the same pass and reproduces
  0.109218 / 0.148198 exactly, so only its root digests moved. Numbers either
  side of this line are not comparable; `qualitaetsmetrik.md` §3, §5 and the
  headline ledger carry the entries (#516).
