### Added

- **Landmarken-Linse: the detected structure of a letter, drawn on the
  letter.** A „Landmarken" switch in the workbench's Buchstaben detail
  overlays what the structure detectors find on the written form — crossing
  as a ring, retrace zone as a band along the path, lift as a tick, corner
  as a square, Kringel as a circle scaled to its measured aperture `D0`,
  merge as a hatched band — for the chart ductus and, where one exists, the
  Laufform. Every marker carries its numbers and a ⚑; the empty area of the
  letter carries one too, so „here a marker is MISSING" can be reported at
  all. The layer is generated, so the lens offers exactly that one handle
  and no way to hand-patch it (optimierungs-werkbank.md §3/§8). It closes
  the gap the author named: the structures that carry the Duktus-Soll, the
  Tintenfolger counters and the Kringel catalogue were visible only inside
  a measurement run, never on the surface where the ductus is authored.
- **`GET /sources/{id}/templates/{glyph_key}/landmarks`.** Both stored rows
  in one admin-gated read — a second round trip would show two different
  moments of the same letter — with every landmark in template units, the
  ductus loop finder's anchor ranges, and the catalogue rows NO detected
  loop could be paired with. That last list is the honest half: the `t`
  holds three plate counters the finders see no loop for, and showing
  nothing there would claim the letter has no Kringel.
- **`work_items.kind = "landmark"` and the stage `landmark_detector`.** A
  complaint about one detected structure reuses the letter's `glyph_key` —
  the landmark layer is derived from that row, so a second key column would
  be a second name for the same thing — and the lens itself writes which
  marker with which numbers into the note's first two lines, so a working
  session can reproduce it from the row alone. No migration. The new stage
  is the one entry in the §5 vocabulary that names no step of the writing
  path: the letter was right and the detector wrong, which is why it sits
  last in the triage order.

### Changed

- **The structure detectors moved to `core/landmarks.py`.** Self-crossings
  (§13a), the v2 pierce test with the retrace/touch/overlap classification
  (§14 `aug16`) and the loop aperture with its size class and plate-read
  state (§14 `sep06`) now live in one place, and `tools/pairlab/landmarks.py`,
  `tools/tracebench/counters.py` and `tools/tracebench/kringel.py`
  re-export them under their old names. Moved verbatim, thresholds and
  provenance included: `core/` may never import `tools/`, so serving the
  same detectors over HTTP needed a shared home rather than a copy — and a
  copy would drift on the first threshold change, leaving the lens and the
  bench disagreeing about a letter while both claimed to detect crossings.
