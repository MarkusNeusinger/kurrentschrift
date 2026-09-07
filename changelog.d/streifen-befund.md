### Added

- **The Streifen-Befund: what one written Fassung says about itself.** When a
  strip is filed, `apply` now measures six fields off the ink itself — the pen
  (median half width on the medial axis, read against the plate's pen AND
  against this hand's own median), the continuity of that axis (Knick, Wackler,
  Bogen, Krümmungsverlust from the frozen #558 arithmetic), the counters the
  ink encloses against the per-loop expectation of the Kringel catalogue, the
  ductus (body runs against the number the script joins the word into), how the
  ink sits in the ruling, and the §5-shaped composite that orders them. Out of
  that comes a **suggestion** (`sauber` · `brauchbar` · `neu schreiben`) with
  the ONE reason that dominates it, in the author's own words („Knick im
  Übergang", „Kringel zu", „Strichfolge weicht ab", „Feder zu dünn/dick",
  „wackelig"). This is what makes it safe to upload strips that are not yet
  perfect: the loop write → scan → Befund → tick → rewrite the weakest shows
  which Fassung of a strip is the weak one and why, instead of making the
  Bestand wait for flawless sheets. **Nothing rejects automatically** — the
  tick on the paper stays the verdict, „ersetzt durch F0n" only says a later
  Fassung came out cleaner, and a Fassung leaves the training data solely
  through `redo --retire`. Stored is the MEASUREMENT alone
  (`eigenhand_fassungen.befund`, migration `0029`); the suggestion, its reason,
  the composite and the rank among a strip's Fassungen are derived on read —
  the same doctrine as the derived strip state, because a rank changes the
  moment a better Fassung arrives. Visible in `report --befund` (with the
  rewrite list, weakest first) and in `/admin/eigenhand` as chips per Fassung,
  sortable by them. Thresholds are pre-registered from the physical scale and
  from constants this repo already calibrated; no bench headline reads any of
  it.

### Changed

- **The continuity arithmetic and the skeleton graph move into `core/`.** The
  word bench's Unstetigkeits-Sensor and the writing-order recovery both
  computed things the Streifen-Befund needs — and the API image ships `core/`,
  not `tools/`. `core/continuity.py` (Knick · Wackler · Pfeilhöhe ·
  Krümmungsverlust with their frozen window ladder) and `core/skeleton_graph.py`
  (nodes and edges of a thinned ink mask) are now the single source;
  `tools/wordbench/continuity.py` and `tools/routeg/graph.py` read from there
  without a single number moving. The plate pen and the Kringel catalogue come
  from `core/landmarks.py`, where the Landmarken-Linse already put them, and
  the import's ink threshold now lives where ink is read. Tests pin each of
  those connections as an IDENTITY, so a move can never decay into a copy.
