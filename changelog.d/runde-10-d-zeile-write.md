### Added

- **The one-row round on the `d` running form is judged, and its class clears
  both thresholds without a single vote against.** Round 10 — 48 screens, the
  stored rows against the same composition plus ONE overlaid Laufform row
  (`d`), everything else identical down to the pinned registration — returned
  `d-rein` **0 : 10 for the candidate at 0 % ties**: every one of the ten words
  that draws a `d` without a `u` neighbour went to the candidate, and so did
  both mirrored repeats of that class. The instrument is the strongest so far:
  8 of 8 mirrored pairs named the same arm, and on the four DECIDED pairs the
  judge switched sides with the mirroring every single time; the 26 bit-identical
  null probes were all read as "no difference". The global line still says
  `adopt: false` — by construction, because those 26 null probes are a tie
  floor of exactly 65.0 %, computed in the pre-registration before anyone
  clicked, which is why the plan reads the verdict inside `d-rein`.
- **The round's own artefacts are in the repo** (`data/humanbench/runde-10-*`):
  the result text, the narrow key with its class per screen, the analysis JSON
  (reproduced byte-identically from the full key, checked) and a provenance
  stamp carrying both arm checksums, the root export the round was built
  against, and — for the first time in a word round — a clean build worktree.
  The full key, the payload, the two arm files and the candidate card stay out.
  The stamp says what the narrow key cannot recompute, and here that is the
  verdict itself: it shows that `d-rein` was decided ten times, not for whom.

### Changed

- **The `d` running form is written, and the word ruler is re-baselined on the
  root that write produced.** On the round's result the author put the single
  row into production (decision A44): one PUT of `d` (n = 11 occurrences, 120
  anchors) as variant 100 on `suetterlin-1922`, snapshots either side, readback
  deviation 0.000000, nothing else in the database touched. Both fixture roots
  were then rebuilt over HTTPS and the headline re-measured with BLAS pinned:
  words 0.108153 → **0.108339** (+0.000186), pairs **byte-identical** at
  0.148236, `worst_word` still `regieren` 0.233052, on
  `a4eb48420ccb…` / `e3a5d03d0f37…`. This is a declared re-baseline — numbers
  from before the write are no longer paired with these, and `--expect-root`
  pins the new base for every future round. The dry overlay prediction of the
  pre-registration is reproduced **byte for byte**, and not only in the
  headline: all 96 entries match to the last digit, which proves independently
  that the stored row IS the card that was judged.
- **The ruler's sign carries no information about this verdict, and that is
  now measured rather than argued.** Over the fourteen moved words the ruler
  reads 5 better : 9 worse; inside `d-rein` it is 3 : 7 and costs +0.001459 at
  the median. The eye names all ten anyway — including both words the ruler
  punishes hardest (`der-2` +0.007563, `Feinde` +0.004178) and both it rewards
  hardest (`Soldaten` −0.004612, `laden` −0.002505). The same constellation
  carried `exit_trim` on `sep06` (+0.000582) and did NOT carry the fifteen-row
  card on `sep08`; the +0.000186 here is a sixteenth of what that card would
  have cost.
- **The pairs root did not stay byte-identical this time, and the entry says
  why instead of glossing it.** Each of the three roots keeps its own copy of
  the stored Laufform rows (words 21 · pairs 14 · abb22 18), so a row write
  necessarily moves all three; on top of that the pairs root had not actually
  been re-exported on `sep07`, so today's `--set all` also stamps it with a
  fresh `exported_at`. Compared file by file against the previous roots, all
  three differ in exactly two files — `manifest.json` and the `d` key of
  `templates_laufform.json`, largest anchor deviation 0.044500 xh, digit for
  digit the maximum the pre-registration had measured against the stored row.
  Every other file is identical — 255 of 257 in the words root, 135 of 137 in
  the pairs root, 427 of 429 in abb22 — and the pairs NUMBER is unmoved because
  the Abb. 20 drills are too short for the run-length gate and never see a
  Laufform row at all.
- **What the row does not fix is filed as its own arm, on the right route.**
  All four `und…` words went to the BASE, 4 : 0 without a tie, both mirrored
  repeats confirming — descriptively, at n = 4 below the class floor, but
  unanimously, and it is exactly where round 8's two base votes for the `d`
  column sat. The row is better where `d` stands alone and worse where `d`
  meets `u`, which makes it a seam question for the Übergänge route rather
  than a row question; it is registered as an open arm with its own
  pre-registration to come and deliberately **no knob named yet**, plus its
  rescue-path row. The duel numbers are likewise flagged: Kette and Lotse
  still stand on the `sep07` root and owe a re-measurement on this one.
