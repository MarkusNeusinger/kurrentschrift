### Changed

- **The admin-redesign plan books the close of Phase 2: all thirteen PRs
  shipped, the calibration round open.** Docs only, no code.
  `docs/proposals/admin-redesign.md` §15.6 gains a second table — one row
  per PR with its number and, where the built thing differs from the
  planned row, what differs. Two rows changed shape in the building: the
  plan called the Nachfahr-Liste "der Filter ‚Nachfahren'" and there was no
  Eigenhand work list to filter, so a whole list surface with one row per
  word BOX was built instead; and the plan expected one rebuilt editor
  dialog, while author decision G made it a second, slim editor sharing one
  drawing canvas with the plate one. PR 12 (`pfad --spans`, #650) never
  needed the named exception of the wave's ordering, and PR 13 shipped its
  instrument (#649). **Still open is the ROUND of PR 13**, a completion
  condition of the phase: it judges 30 word boxes blind whose Bahn the
  follower laid AND measured under format 2, and none exists yet — a Bahn
  drawn by hand stays grey and does not count. So the traffic light stands
  and is not calibrated, and its eight thresholds stay labelled
  provisional.

- **§4.7 gains the author decisions of rounds 2 and 3.** D — the tool
  measures the two missing sensors while following and the row stores them
  ("measured is stored, judged is derived"), because the pixels are only
  there while following and `core/` may not import `tools`. E — a Fassung
  gets a counter ("3 of 4 boxes follow"), never a colour, because a second
  colour over the same Fassung would stand beside `befund.vorschlag` with a
  vocabulary of its own. F — the calibration instrument goes into the plan
  now and is built last. G — a second, slim strip editor, the plate flow
  untouched, with the drawing surface extracted into one shared component
  rather than copied. H — **TWO separate hold-out sets, against the
  recommendation**, which answers FM3 of the Freigabe-Maschine in the same
  direction and is booked there too. I — existing Fassungen stay grey,
  because a Bahn followed under format 1 never saw sensors 4 and 5. Three
  further decisions of the same day ride along: a German Fachbegriff without
  an established English term may be an identifier (the rule itself lives in
  `docs/reference/sprachregelung.md` §5 and is cited, not restated), the
  sensor "Sprünge und Haken" is read and shown but not graded until the
  calibration gives it a bound, and hand-corrected letter boundaries survive
  an ordinary re-follow.

### Fixed

- **Five claims the code PRs could not correct, because the wave reserved
  this file for the docs PR.** §7.2 still called the strip surface "der
  Filter ‚Nachfahren'" in its own Flächen line; no V-row said that
  `?reiter=streifen` opens on the LIST and that the gallery is the
  `?ansicht=galerie` opt-in (V14 now says it, and names why the flip back is
  not a one-line constant); V20 and §6.4 described the write path more
  narrowly than it was built — the token hashes `{format, pfade}` rather
  than `pfade` alone, the ladder is 428 · 412 · 409, `If-Match: *` is
  refused while a weak validator of the same digest is accepted, a row lock
  covers the short window inside one request, and `displaced_authored`
  deliberately does not apply on the per-box path; §6.4 and §6.7 did not
  record that the editor needs the box's NOMINAL ruling from the API
  (`nominal_baseline_row` + `nominal_xh_px` — a box whose follower gave up
  carries no registration at all and would otherwise have no frame); and
  §6.4 still had the Absetzer target as `body_runs_expected` + Markenzüge,
  while it counts BODY runs only.

- **`docs/proposals/eigenhand-erfassung.md` §7.5 still described the
  Streifen-Pfad as format 1 only.** It now carries the two-release lockstep,
  the three real schema changes of format 2 (skip entries, span provenance,
  the field-level authored guard), the content rule enforced in both
  directions, `format` having become mandatory on the write path, and the
  fact that the surface which writes an `authored` box exists. The
  field-level protection of hand-corrected letter boundaries is no longer
  written as future work.

- **`CLAUDE.md` and `.github/copilot-instructions.md` still said the
  measurement journal carries 132 dated entries.** It carries 134.
