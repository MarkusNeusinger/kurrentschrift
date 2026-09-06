### Added

- **Kringel-Landmarke — a per-letter, per-loop expectation instead of one
  threshold.** Whether a loop has to stay open is not a number for the whole
  hand: it is a property of one loop of one letter, read off the plate. The new
  frozen catalogue `tools/tracebench/kringel_catalogue.json` carries, for all 46
  loops of 27 Sütterlin glyphs, how wide the plate holds the loop (`D0`), which
  size class that is in widths of the plate's own pen (`klein` · `mittel` ·
  `gross`), and — over every occurrence — whether the plate keeps it `offen`,
  `wechselnd` or as a `punkt` (a Punktkringel, closed by construction and never
  a defect). `tools/tracebench/kringelcat.py` builds it from one frozen fixture
  root; `tools/tracebench/kringel.py` is the sensor that reads it.
- **A Kringel column in the trace bench report, report-only.** Every word line
  gains `kringel <lost>/<offen>`, and the block gains `kringel_lost` and
  `kringel_wechselnd_zu`. Only loops the plate holds `offen` count as losses;
  `wechselnd` closures are carried apart because the plate closes those itself,
  and `punkt` loops are exempt. No scored number reads the column — the word
  and pair headlines stay byte-identical (0.108444 · 0.148236), and the trace
  report is line-for-line unchanged beside the new column.

### Changed

- **The „26 closing words" of the counter diagnosis are re-read through the
  catalogue.** On that diagnosis's own path — its eight loop keys, and only
  where the plate shows the hole in that very occurrence — 27 words close at
  half width 0.097, of which **24 carry a real `offen` loss and 3 only a
  `wechselnd` one**, so the honest figure replacing 26 is 24. Over ALL loops the
  number goes the other way: **34 of the 63 word specimens** lose an `offen`
  loop, and beside them stand 19 counters no composed loop accounts for at all —
  a topology loss, not a narrow one.
