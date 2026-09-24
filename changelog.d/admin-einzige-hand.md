### Changed

- **A script with exactly one own hand opens on it.** The admin's hand scope
  used to fall back from the hand chosen this session to the hand last
  chosen for the script, and otherwise to none — so every fresh browser, the
  tablet above all, stood on „Hand: —" and an empty Eigenhand picker beside a
  script that has one hand to offer, until the author picked the obvious
  once per device. `resolveHand` now has a third step before „none": the
  script's ONLY hand. Never the first of several — with two hands of one
  script the field still waits for a pick, because a default by code point
  would put a scope nobody chose into every Korb link — and never an
  invented id for a script without a hand. The default is not stored as a
  pick, so a second hand arriving later leaves the choice to the author.
  The author's tip of the open taste question „Hand: —" (admin-redesign.md
  §15.5 Nr. 13). Every script opens on its hand: Sütterlin on
  `mn-suetterlin`, Kurrent on `mn-kurrent` and Offenbacher on
  `mn-offenbacher` — the latter two created on 2026-09-23 as setups without
  material, which the candidate list reads beside the hands that hold
  sheets.
