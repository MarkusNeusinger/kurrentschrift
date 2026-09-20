### Added

- **A stored format marker on every Streifen-Pfad row.**
  `eigenhand_strips.pfade_format` (migration `0032`, NOT NULL, server default
  `1`, so every existing row is stamped in place) says which Streifen-Pfad
  format that row's `pfade` cell was written in, and the read now answers with
  it. Until now the answer came from the core constant `PFAD_FORMAT`, which
  means the row said whatever the running image believed: the moment that
  constant becomes 2, every path followed under 1 would read as 2 and a reader
  would apply the newer semantics to entries nothing had measured that way.
  Two formats cannot coexist until the row itself says which it is, so this is
  the half that has to be in place before a second format may be admitted.
  A column rather than an envelope inside the JSON cell — the deferred `pfade`
  cell is not rewritten at all this way, and every reader of it keeps working
  untouched. It is deliberately NOT deferred alongside `pfade`: it is one small
  integer, and „which Fassungen still stand on the old format" is a listing
  question that must not pull a single path to answer.

### Changed

- **The two wire defaults for the path format follow the constant.**
  `EigenhandPfadeIn.format` and `EigenhandPfadeOut.format` were written out as
  `1`; they now bind to `core.eigenhand.pfad.PFAD_FORMAT`, so a push that names
  no format still means „the format this API reads" once that number moves.
  Nothing else changes: the write still admits exactly one format and still
  produces only format 1, and it now stamps what it admitted onto the row
  instead of forgetting it.
