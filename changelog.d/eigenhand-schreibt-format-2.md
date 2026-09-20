### Added

- **The Streifen-Pfad follower measures the two sensors the Tintentreue was
  missing.** Beside every followed word box `tools.eigenhand.pfad` now stores
  the **paper excursion** in x-heights and the **AIoU**, both read against
  that box's own binarised ink mask — the one the follower was already handed.
  Neither is a new metric: the excursion is the bench's standing K-D kernel
  (`tools/tracebench/excursions.py`) with its fixture wiring lifted off, and
  the AIoU is the ruler's own, which grades against an image and needs no
  reference trace. That matters because a written strip has none by doctrine.
  The numbers are measured once and stored, never derived per read (author
  decision D: „Gemessen wird gespeichert, beurteilt wird abgeleitet"), and
  the projection into the stored row is a fixed list with a test that holds it
  against every key `core/eigenhand/tintentreue.py` reads — a sensor missing
  from it would reach nobody and afterwards be indistinguishable from
  „measured 0".
- **A box the follower could not follow says why, in the same list.** Three of
  the four situations that were one indistinguishable „no entry" now write a
  Skip-Eintrag: `no_geometry` (a Bogen printed before the cut geometry),
  `unauthored` (the word needs glyphs the plate does not carry) and `gave_up`
  (the follower itself). They are not the same work — only the last is
  follower work at all — and the Nachfahr-Liste routes by exactly that.
  `not_selected` stays deliberately unwritten: `--box` narrows a RUN and says
  nothing about the other boxes, and the write is a full replacement. For the
  same reason a skip never displaces a stored path: „unauthored" depends on
  today's plate and „gave up" on this run's arms, so a box followed cleanly
  last week can produce a skip this week, and the run drops its own finding
  rather than a good Bahn.

### Changed

- **`PFAD_FORMAT` is 2 — the second release of the lockstep.** The API has
  read and accepted format 2 since the release before, so the tool moving is
  a one-sided change; every push now declares 2 and every row is stamped with
  it. Rows followed under 1 keep saying so, which is the whole point of the
  stored marker: the traffic light greys them („Format 1 — unvollständig
  gemessen") instead of claiming colours for sensors nothing computed. The
  follower's own letter boundaries stop travelling in the free `meta`, where
  format 2 refuses them; they return as the checked field with
  `pfad --spans`. Boundaries the author corrected by hand are untouched and
  ride along as before.
- **A restore recognises the Bahn it put back itself.** `sync --from` compared
  the live box against the archived entry for equality, and a format-1 Bahn
  restored under format 2 comes back normalised — so a second run over the
  same snapshot would have reported its own first restore as a box the author
  had changed. It now asks the question the closing count already asked: did
  everything that was sent come back.
