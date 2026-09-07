### Added

- **Die Fleckenmaske: the printer's toner specks removed as data, never as
  pixels.** The author's colour laser drops loose toner in the right part of
  every sheet, and cleaning does not help — the specks land inside a filed
  strip as foreign ink, and inside the writer's verdict box they can fake a
  tick. Both halves he asked for are now one mechanism. `ingest` finds the
  isolated specks per row and files them as a list of circles in the strip
  crop's own millimetres, with the QC flag `flecken:<n>` and the circles drawn
  over the crop on the Siebung page; `/admin/eigenhand` gets a „Flecken
  radieren" mode where the pointer becomes a round brush (0.3 / 0.6 / 1.0 mm)
  — a click sets a circle, a click on an existing one takes it away
  (automatic ones included), „Rückgängig" walks back and „Speichern" replaces
  the list through the admin-gated `PATCH /eigenhand/strips/{hand}/{strip}/
  {fassung}/flecken`. **The stored bytes are never modified.** That is the
  two-channel doctrine `without_rulings` already runs on: the strip is the
  reserved dataset's primary evidence, so the mask is DATA and
  `crop.without_flecken` fills the circles with the LOCAL paper level (read
  off a ring around each — a scan's paper is neither white nor even, and a
  white disc on it reads as a hole) when the image is served. Deleting the
  mask brings the raw strip back byte for byte, and `?flecken=mit` (the „roh"
  toggle) shows it at any time. The automatic pass is deliberately timid,
  because a missed speck costs one brush click while an erased i-dot destroys
  ground truth: it touches only what is small (≤ 0.6 mm across), touches no
  letter, stands 2.5 mm clear of the writing, does not sit as a dot above a
  letter within its x-extent, and lies inside the writing window rather than
  on the printed strip id or the clear-text label. The Befund is measured on
  the masked plane, so a speck can no longer count as a body run or drag the
  pen width — and a hand edit RE-MEASURES it, through the same entry point
  (`befund.measure_plane`) on the same plane (`crop.working_plane`) that
  `apply` reads, so erasing a speck cannot leave the ranking it distorted
  standing. Stored per Fassung in `meta.json`, in the Kartei and in
  `eigenhand_fassungen.flecken` (migration `0030`, nullable and additive).

### Fixed

- **Three printer specks could fake the writer's tick.** `read_pen_mark`
  measured plain ink coverage of the verdict box, and three toner dots came to
  more than the 4 % a tick needs — filing a row the author never accepted. The
  reading now drops isolated speck-sized components first and then asks for an
  extent no accumulation of dots can have: a tick is a stroke, a speck is a
  dot.

### Changed

- **The Fleckenmaske is the one field of the capture chain whose master is the
  server.** Specks are found locally at import, but they are erased in the
  workbench — so `sync` fills a row that has none (reported as
  `flecken_filled`) and never overwrites one that does, and the new
  `tools.eigenhand.pull --flecken` brings the hand-edited lists back into the
  Kartei and the Fassungen's `meta.json`. `null` („nobody has looked yet") and
  `[]` („looked, nothing to erase") are kept apart all the way through, because
  the fill rule turns on the difference: an emptied mask that came back as
  `null` would be open to the stale automatic list again. The mask carries its
  detector format like the Befund does, so a newer tool at an older API gets a
  409 instead of a silent reinterpretation. The Kartei is what carries the
  masks into the archive (it is re-filed in full at every snapshot, while an
  archived Fassung directory is never rewritten) and back out of it through
  `sync --from`.
