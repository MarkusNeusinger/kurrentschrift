### Added

- **The evidence floor now guards the card, not just the write.** `tools/laufform/smoothrow.py`
  grew a `--floor` that defaults to the write path's own
  `LAUFFORM_MIN_OCCURRENCES`: a glyph whose fresh harvest carries fewer
  occurrences is not re-derived from too little evidence at all, and drops out
  of the card — so walking the file with a PUT per key can never meet a row
  `PUT …/templates/{key}/laufform` refuses with a 422. It costs nothing in
  measurement, because the file is an overlay: an unnamed key keeps its frozen
  row, which is exactly the row a carried-over entry would have repeated. The
  floor used to live only in the endpoint, so a card could be built, measured
  and carried all the way to the write before it was refused — or, worse, be
  waved through with an author statement nobody had thought about. The report
  names each omitted key with its reason („no usable fits" is a gap in the
  harvest, „under the floor" a gap in the evidence), and every finished card
  says whether it is writable. `--keep-stored` copies the omitted rows back for
  a card meant as a snapshot — patching a fixture root needs the complete list,
  since `templates_laufform.json` is not an overlay.
- **The Laufform survey flags the rows under the floor.**
  `tools/laufform/inventory.py` knew two flags, „über τ" and „Kopf", and used
  the floor only to pick the trusted rows that set τ — so a stored row below it
  was silently counted out instead of named. It now carries a third flag and
  its own summary line, which is what the 2026-09-02 audit had to reconstruct
  by hand and what the re-harvest of `sep04` needed to notice that the two rows
  the audit found had become three.
