### Added

- **The calibration instrument for the Tintentreue traffic light.** Every one
  of the eight bounds in `core/eigenhand/tintentreue.py` is borrowed — off the
  1922 plate, off the dev-19 set, or off no measurement at all — and the single
  measured value among them belongs to a known coverage failure.
  `tools/eigenhand/tintentreue_calibration.py` builds the round that replaces
  them: 30 word boxes of one hand, judged blind in three steps plus four marks,
  drawn stratified by the provisional step, with a hold-out reserve, blind
  repeats and a provenance stamp. `analyse` walks the pasted result text in the
  pre-registered order and PRINTS a `Schwellen(…)` block instead of writing one
  — adopting it is a dated step of the author's, and every fatal gate of the
  pre-registration stops the block before it is reached. A rebuild, not a mode
  of `humanbench`: that builder cuts from word-bench fixture roots, its taxonomy
  has six fit categories, and its page is published — this one never is, because
  its crops are the reserved own-hand pixels. Exactly one thing is shared: the
  page.
- **A fourth category set for the judging page.** Beside the six fit categories
  `page.py` now knows the three traffic-light steps with their four marks
  (`STRIP_CATEGORIES`, question `tintentreue`). New with it is the kind
  `detail`: a mark ADDS to the step instead of clearing it, the way a defect
  clears „Gut" in the fit taxonomy — here the step IS the verdict, and a mark
  only says which sensor should have seen it. The page's result file is tagged
  with the hand and the build digest, so a result can only be read back onto the
  build it came out of.
- **The method is written before the code.** `menschliche-bewertung.md` §8b
  carries the question, the categories, the mapping onto the three steps, the
  construction rules and the analysis plan; `messjournal.md` §14 pre-registers
  the round itself with its floors, its quantile rule, its rounding direction
  and its kill criteria. The round has not run: it needs 30 real boxes and the
  author's blind pass, so `VORLAEUFIG` is untouched and the „vorläufig" label
  still stands.
