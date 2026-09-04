### Added

- **Every arm the word round can judge is now a switch the composer already
  had.** `wordarm.py --exit-trim` hands the composer's own `exit_trim` flag
  through, so the rejected J4 exit-collinearity arm can be drawn dry — no core
  change, the default stays off and the golden fixture holds. Together with
  `--laufform` and `--nib` that covers both rounds the author decided on, and
  the arm file records which switch produced it: which knob was on is the one
  thing a round cannot reconstruct from the drawn geometry afterwards.
- **Two pre-registrations for the rounds themselves**, written before the pages
  were built: the plate nib (audit finding 20) and J4 as the third rescue path
  of its `tintenfolger.md` §7.9 row. Both name what a result may license — for
  the nib that is deliberately less than adoption, because the audit's own side
  condition is already broken dry (`gleichzug_doublings` 13 → 21).

### Fixed

- **Two word rounds no longer share one resume namespace.** The rounds over one
  fixture set draw the same words in the same order under the same display ids,
  so a browser key built from the ids alone was shared: the second round would
  have opened on the first one's verdicts, silently, part-answered. Each round
  now carries its own key, derived from its identity — mode, number, seed and
  the arms it drew — and the page says which round it is above the question.
  That is the resume half of the defect `menschliche-bewertung.md` §3.6b was
  written for: what could not be settled about the LF11 round afterwards was
  not only what the page had drawn but which page the judge had in front of him.
