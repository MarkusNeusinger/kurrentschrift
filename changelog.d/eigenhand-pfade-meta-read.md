### Added

- **One read for „which word boxes of this hand are in which state".**
  `GET /eigenhand/pfade/{hand}` answers the Streifen-Pfade of a whole hand as
  STATE and leaves the Bahnen where they are: per box its provenance, its
  Skip-Eintrag where it has one, the Tintentreue with the sensor that names it
  and its raw readings, the Absetzer-Soll and whether the box is still work —
  and not one of the few thousand points a path carries per word. Before it,
  the same question cost one request per (strip, Fassung) and put every stored
  path on the wire to answer it. The rows are STREAMED out of the database
  (`EigenhandRepository.strips_with_pfade`) and folded in plain Python, not in a
  JSONB operator: the HTTP suites run on SQLite, and a rule only the shared
  Postgres could evaluate is a rule no test here can hold — and „meta-only" has
  to hold in the process as well as on the wire, so a hand's Bahnen are never
  all resident at once. `?nur=offen` narrows the answer to the boxes that still
  want work and drops a Fassung with none left, while the per-Fassung counter
  („3 von 4 Kästen folgen") is taken before the filter — it answers the Fassung,
  not the query, and a Fassung still gets no colour of its own. Until a writer
  declares Streifen-Pfad format 2, every stored row still greys as „Format 1 —
  unvollständig gemessen", so today the filter returns everything and the
  counter's `folgt` is 0 hand-wide; that is the state of the data, not of the
  read. The Absetzer-Soll comes from
  `core.eigenhand.befund.body_runs_expected` on the server so the editor's
  target and the Tintentreue's Absetzer sensor cannot disagree. Reserved and
  `private, no-store` like the pixels it is derived from, pinned as such in
  `tests/test_api_public_surface.py`.

### Fixed

- **A skipped word box is no longer described as a missed measurement.** The
  Tintentreue read a Skip-Eintrag's sensors like any other box's, so a box whose
  entry states outright that there is no path came back grey as „unvollständig
  gemessen" — a sentence about a measurement nobody owed, and a re-merge of the
  four situations author decision C had just split apart. It now answers
  „übersprungen: unautoriert / aufgegeben / keine Bogen-Geometrie / nicht
  gewählt / ohne Angabe", read BEFORE any sensor. That also closes the latent
  half of it: `meta` is a free blob a skip carries through untouched, so a
  follower that one day records why it gave up would have handed the light a
  full diagnosis block on a box with no Bahn — and an all-green one would have
  called a path that does not exist the best kind there is, taken it off the
  work list and counted it in „3 von 4 Kästen folgen".
