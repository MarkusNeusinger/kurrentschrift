### Added

- **The evidence floor now guards the card, not just the write.** `tools/laufform/smoothrow.py`
  grew a `--floor` that defaults to the write path's own
  `LAUFFORM_MIN_OCCURRENCES`: a glyph whose fresh harvest carries fewer
  occurrences is not re-derived from too little evidence at all — it keeps its
  stored row verbatim, and the report says which reason applies („no usable
  fits" is a gap in the harvest, „under the floor" a gap in the evidence). The
  floor used to live only in `PUT …/templates/{key}/laufform`, so a card could
  be built, measured and carried all the way to the write before the endpoint
  refused it with a 422 — or, worse, be waved through with an author statement
  nobody had thought about. Every finished card also prints how many of its
  rows sit under the floor, including the ones it merely carried over from the
  root. `--floor 1` is that author statement, spelled out, and reproduces the
  LF11 card of `sep02` byte for byte.
- **The Laufform survey flags the rows under the floor.**
  `tools/laufform/inventory.py` knew two flags, „über τ" and „Kopf", and used
  the floor only to pick the trusted rows that set τ — so a stored row below it
  was silently counted out instead of named. It now carries a third flag and
  its own summary line, which is what the 2026-09-02 audit had to reconstruct
  by hand and what the re-harvest of `sep04` needed to notice that the
  population had grown from two rows to four.
