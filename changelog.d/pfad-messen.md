### Added

- **`pfad --messen`: a hand-drawn Bahn is measured, so it carries the same
  traffic light (V21).** The Streifen-Editor saves a drawing with an empty
  `meta`, and the Tintentreue light greys such a box („von Hand gezeichnet")
  because nothing measured it. The new mode of `tools.eigenhand.pfad` computes
  the follower's sensor block for the DRAWN strokes, on the same ink a follow
  is handed (the label mask by default): the paper excursion and the AIoU come
  out of the follower's own code, and the two decode counts are read off the
  same inputs the decode stands on (`tools/eigenhand/messen.py`) — „Tinte ohne
  Bahn" on the follower's own strands, a strand counting as travelled where
  half its arc lies within 0.10 x-heights of the drawing (proximity alone
  would count every stroke the drawing merely crosses), and the Absetzer as
  the drawing's runs minus one minus the lifts the composed seed sanctions,
  never below zero. Jumps and hairpins are decoder events and stay null.
- **Measure-only, and checked twice.** Strokes, registration and letter
  boundaries go back byte for byte and `verfahren` stays `authored`; the
  entry gains `meta.tintenpfad`, `meta.messung` (`gemessen_von: "messen"`,
  `herkunft: "authored"`, the day, the input stages and the travelled-strand
  rule) and `flecken_n` — the mask the NUMBERS were taken under, so „Maske
  geändert" can still grey a measured drawing after the author brushes the
  strip. The tool refuses to send an entry whose other fields moved, and
  stops the run if the server's answer comes back with one moved.
- **Authored boxes only, one box at a time.** A `--box` naming a followed
  Bahn, a skip or an empty box is refused; a drawing that already carries a
  measurement is left alone unless `--neu`, or unless its numbers were taken
  under an older Fleckenmaske. Dry run by default (the list is filed as
  `pfade/<strip>-<fassung>.messen.json`); `--apply` writes through the per-box
  `PATCH …/pfade/{box}` with `If-Match`, the token chained from answer to
  answer and the ROW's own format declared — never the full replacement.
  `--spans`, `--replace-authored`, `--resample-plate` and `--register-seed`
  are refused beside it.

### Changed

- **Whether a measured drawing counts for the Tintentreue calibration round
  stays open** (`admin-redesign.md` §15.7, question 34). The filter
  `boxes_of_hand` is deliberately unchanged, so the round takes a measured
  drawing until the author decides otherwise; the docs that said `pfad
  --messen` was not built now say it is.
- **The Nachfahr-Liste names the command.** The hints on a sensor-less Bahn,
  on the unranked list, on the Erledigt filter and on a hand-drawn box now say
  that `tools.eigenhand.pfad --messen` measures a drawing without touching it,
  and that a measured drawing's light counts like any other.
