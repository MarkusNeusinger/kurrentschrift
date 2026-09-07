### Added

- **The K-E tie-breaker round is built, and building it found that the ruler
  has changed sides.** Author decision of 2026-09-07 („ja, Urteilsrunde") runs
  rescue path (1) of the closed K-E family — the pre-registered methodology case
  in its purest form, where the `aug21` aiou median over the moved words was
  −0.0002 and four local coverage losses stood against a target that healed on
  every axis. Re-run against today's production chain v5 instead of the v4 it
  was rejected on, `--mark-claim` now moves 38 of 63 words, drops the
  reference-free Soll distance 85 → 82, reads +0.0008 median aiou, and leaves
  only TWO words under the standing −0.003 gate (`regieren`, `muß`) — all four
  of the named `aug21` losers are winners or neutral today, while `die-2` still
  heals (Soll 5 → 4, +0.0227, the V needle gone). The `aug21` gate stays torn
  and is not softened, so the round decides. Round 9: 44 screens plus 10
  mirrored repeats, both followed TRACES over the plate's own ink, judged on
  §8's accuracy question. Pre-registration, construction measurement and the
  analysis plan are in `docs/reference/messjournal.md` §14 „Kette K-E `sep07`".
- **`tools/humanbench/tracearm.py` — the arm producer for a round whose
  candidate is a trace, not a composition.** `wordarm.py` composes a word and
  draws it as ink for the authenticity question; this one takes any
  `tools.tracebench` file-provider candidate (the ink-follower's own
  `--candidate-out`) and hands the builder the followed path in the fixture
  entry's frame. It is a frame translation and nothing else — the same
  separation `wordarm`'s docstring argues for, so an instrument can never drift
  away from the ruler that has to confirm its candidate.

### Changed

- **A word round's question now follows its arms instead of a default.** Ink can
  be asked whether it looks written; a centerline cannot, so a round built from
  trace arms asks „welche Linie folgt der Tinte besser?" and tags its result
  file `VERGLEICH`. `build.py::draws_ink` reads that off the arms and writes it
  into both the payload envelope and the provenance stamp, so a result file can
  no longer claim to answer a question the round never asked.
- **The `mess-runde-route` docs budget is raised to 8541** (measured 7765 plus
  the documented 10 %). The round measures a Kette knob and therefore owes
  `verfahren-kette.md` a ledger line, and that line has to carry the finding
  that inverts the family's own record — two aiou losers instead of four — or
  the next reader is sent to the `aug21` numbers as if they still held. The row
  was condensed three times first; `mess-runde` is not raised.

### Fixed

- **A width-less arm is drawn as a centerline again, not as ink.** The page
  decides its display from the panel — filled shapes or per-stroke widths mean
  „this draws ink", so the specimen is faded to 45 % and the cartographic casing
  drops away — but the builder emitted a widths array of zeros for an arm that
  had no widths at all. A trace arm would therefore have been judged on a faded
  crop without the halo that makes a dark line legible inside dark ink, which is
  the safeguard `menschliche-bewertung.md` §3.5 exists for. All-zero widths are
  now emitted as none.
