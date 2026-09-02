### Added

- **The word bench now states which base it measured.** Every run prints two
  header lines per fixture root — `root: <name> exported_at=…` and
  `digest=<12 hex>` — from a new `root_digest()`: SHA-256 over the sorted list
  of (relative path, size, SHA-256 of the bytes) of every file under the root.
  The roots are gitignored, so a re-export used to leave no trace at all; the
  audit of 2026-09-02 found a headline pair whose base nobody could
  reconstruct. `--expect-root <prefix>[,…]` turns the expected base into a
  precondition and aborts before composing anything, and the manifest's
  `page_sha256` is now re-checked by the measuring run instead of only by the
  rebuild path. The frozen Sütterlin roots as of this change are
  `suetterlin-1922` `219182189b93` and `suetterlin-1922-pairs` `9f94ba7523f5`,
  both `exported_at=2026-08-14T06:02:45+00:00` (#478).
- **`seam_deg`: the kink where a connector meets its letters is now a number.**
  A report-only column per join — `dep` how far the generated connector leaves
  the letter's own last direction, `arr` how far the next letter starts off the
  connector's arrival — read over 0.05 xh of arc, deliberately smaller than the
  0.12 xh window the composer aligns its tangents on, since measuring the
  residual kink on the construction's own window would return zero by
  definition. On the frozen 1922 word plate the composer departs +11.87°
  (|Δ| 13.10) and arrives −3.26° (|Δ| 11.18) over 206 of 214 joins; connectors
  carrying a capital's prefixed ornament retrace are excluded and counted,
  genuine ſ/w/r/v reversals are kept. Both headlines stay byte-identical across
  the introduction (`bench_loss` 0.108091, `pair_loss` 0.148489), as the report
  column rule requires (#478).
