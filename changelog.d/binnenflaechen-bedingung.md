### Added

- **Binnenflächen-Bedingung — the counter condition as a term in the solve.**
  The two-stroke model's statement about the ink is unchanged: where the plate
  holds a counter open, no pen sample can have passed within the plate's own
  half width of it. What moves is where it is stated. As a post-hoc push (R3,
  R3b) the condition's aim and its smoothness both hang on one blend length —
  measured, not argued: 107 of 108 counters opened, but the aperture landed
  within the pre-registered tolerance in only 83 of them, and the correction
  added 1626 kink events because the fade is shorter than the spacing of the
  points it fades over. The new `tools/pairlab/counterfield.py` states the same
  condition as a quadratic hinge on the signed distance field of the plate's
  `offen` counters, priced like the ink term and folded back onto the far
  sparser anchors, so the solver trades aperture against smoothness with the
  machinery that already keeps a trace smooth. It leaves the post-hoc
  scaffolding behind — no fade (the anchors are the smoothing) and no closure
  acceptance rule (the structure guard already rejects a round that loses an
  initialisation crossing) — and keeps everything else, the scope included, so
  the conversion changes where the condition is stated and nothing else.
- **`--counter-constraint` on the ink follower, default off**, with
  `--counter-weight` on the ink term's own scale, `--counter-half-width` for the
  pen the condition is stated for and `--counter-size-classes` for the catalogue
  classes it binds. The field is built once per word from the
  plate and the frozen Kringel catalogue — never from a Laufform row, so it
  cannot close the harvest fixed point — and it enters the follower's ROUNDS
  only: `chain.fit_word_chain` is untouched, so every other consumer of the
  chain, the harvest included, is byte-identical by construction. Every run
  stamps the per-loop scope into its report, refusals included.
- **The per-loop aperture reader.** `python -m tools.pairlab.counterfield
  <candidate> [--base <candidate>]` prints, for every catalogue loop in scope,
  the plate's counter, the expectation it implies and the aperture the
  candidate's own trace draws around it — one instrument for both sides of a
  paired round.
