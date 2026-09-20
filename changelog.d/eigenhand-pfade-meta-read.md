### Added

- **One read for „which word boxes of this hand are in which state".**
  `GET /eigenhand/pfade/{hand}` answers the Streifen-Pfade of a whole hand as
  STATE and leaves the Bahnen where they are: per box its provenance, its
  Skip-Eintrag where it has one, the Tintentreue with the sensor that names it
  and its raw readings, the Absetzer-Soll and whether the box is still work —
  and not one of the few thousand points a path carries per word. Before it,
  the same question cost one request per (strip, Fassung) and put every stored
  path on the wire to answer it. The paths are read from the database once per
  row (`EigenhandRepository.strips_with_pfade`) and folded in plain Python, not
  in a JSONB operator: the HTTP suites run on SQLite, and a rule only the
  shared Postgres could evaluate is a rule no test here can hold. `?nur=offen`
  narrows the answer to the boxes that still want work and drops a Fassung with
  none left, while the per-Fassung counter („3 von 4 Kästen folgen") is taken
  before the filter — it answers the Fassung, not the query, and a Fassung
  still gets no colour of its own. The Absetzer-Soll comes from
  `core.eigenhand.befund.body_runs_expected` on the server so the editor's
  target and the Tintentreue's Absetzer sensor cannot disagree. Reserved and
  `private, no-store` like the pixels it is derived from, pinned as such in
  `tests/test_api_public_surface.py`.
