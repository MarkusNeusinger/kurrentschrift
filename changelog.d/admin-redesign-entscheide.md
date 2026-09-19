### Changed

- **The author's decisions on the Admin-Redesign plan are booked where they
  bind (`docs/proposals/admin-redesign.md`).** On 2026-09-18 the author
  answered the whole question catalogue — all 25 questions, the two
  sub-points, the defaults V1–V26 and the small print. Each decision now
  stands as a dated line under its question in §12 and in one consolidated
  table (§4.5), with his three additions quoted verbatim (Q4, Q10, Q15) and
  the two guiding sentences that follow from them: hand-traced strip paths
  and hand-corrected letter boundaries are ALSO the training set that makes
  the follower and the span assigner better, and the own hand is the
  optimisation target while the plate stays the yardstick. The chosen form
  — A first, the C building blocks as phase 4, B selectively, phase 5 in
  parallel — gets its implementation section (§15: phases 0–5, the Phase 0
  PR slicing, the parallel phase 5 track that starts with a
  Freigabe-Maschine proposal), and what was not chosen moves to §13 with
  its reason. Two decisions go against the panel's recommendation and the
  text follows them: a tested write flow MAY be rebuilt when its suites move
  in the same PR (Q6 b), and the English UI labels stay (Q8 without c).
  Nothing is built with this PR; the status stays `offen`. §15.2 names who
  flips it, and the same-PR lifecycle rule holds as written: the first
  merged PR that delivers a row of §5.2 carries the flip (the header line and
  the `docs/index.md` cell, nothing else in that doc) — possible without a
  conflict because the wave's PRs are merged one after another.
- **The declared doctrine deltas are executed in their owning docs, each as
  a dated update.** `optimierungs-werkbank.md` §6: exactly one hand as the
  subject, a second hand only collapsed, labelled and never averaged in
  (Q3 a). `eigenhand-erfassung.md` §7.3: one pre-registered calibration per
  hand for the Tintentreue thresholds (Q10 b); §7.5 and §8.1: a hand-traced
  path is not derivable, is archived, is never replaced by the follower and
  is read by the harvest before `tintenpfad` — and it is training data the
  dev-19 headline never reads (Q4 a); §9: the harvest writes `instances` and
  `pair_instances`, never `word_instances`, and the source question is
  settled as `sources.kind='eigenhand'` (Q20 a, Q21 a).
  `tintenfolger.md` §2.5 names the training set next to the frozen sets.
  The glossary gains the planned terms these decisions coin.

### Fixed

- **Plan claims the Phase 0 reconnaissance proved wrong, corrected after
  checking each against the code.** The 16 px overflow comes from the
  hand-rolled visually-hidden `h1` in `shell/Panel.tsx`, not from a grid
  track; the Korb drawer already groups by status and lacks a way to SELECT
  a group; the Laufform owner stamp lives at
  `templates.trace_meta["laufform"]["hand_id"]`; the `apply-laufform` cases
  live in `tests/test_api_aggregates.py`; grouping the Korb by stage cannot
  work while open rows carry no stage; the overlay green is a contrast bug
  (2.71:1 on white) as well as a colour-vision one, with a second red/green
  pair behind tokens. Also fixed: `vom-scan-zum-schreiben.md` and the plan's
  §4.4 still gave the glyph rebuild a `min_n` of 4 — the route default has
  been 1 since issue #273.
