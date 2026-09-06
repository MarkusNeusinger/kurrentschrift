### Added

- **The harvest can be seeded from the chart instead of from its own last
  output.** `tools.laufform.harvest --chain-seed chart` (and the matching
  `tools.tracebench.run --chain-seed`) starts the chain solve on a composition built
  WITHOUT the running-form rows. The default seed composes the word from those
  rows, so a harvest reads the rows it is about to replace and its map depends
  on its own previous map — measured in `messjournal.md` §14 „Laufform LF15".
  Default off; a non-default seed labels a trace-bench run `chain+<seed>` so a
  report can never be mistaken for the frozen baseline.
- **The harvest names its base and can be run against a candidate map.**
  `--expect-root` states and checks the fixture root the run reads, the way
  every bench does — the harvest is the tool whose output a running-form write
  puts into production, so it owes its base's identity. `--laufform` composes
  against a candidate map instead of the root's own rows (the same file and
  overlay semantics `wordbench.run --laufform` has), which is what makes the
  harvest-twice self-check one command per step instead of a patched root.
