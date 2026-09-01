### Added

- **The form distance of a Laufform row (LF10) — pre-registered, measured,
  not adopted.** `core.laufform.form_distance` measures how far a running-form
  row leaves its chart's path: per anchor the distance to the other side's
  rendered centerline of the same stroke, in chart nib radii, in both
  directions; the pre-registered gate quantity is the worse directional p90,
  because the defects it was built for (a flat segment instead of the v's
  diagonal, the E's cross stroke sitting sideways, the P's bow beside the
  chart) are local while the hand's legitimate deviation is global and
  smooth. The inventory (`tools/laufform/inventory.py`) gains the columns
  `form`/`f-med`/`f-max`, a data-derived τ_form with the pre-registered
  sensitivity variants in its footer, black markers in `--png` for a row's
  anchors at or above its own p90, and `--laufform FILE` to measure
  candidate rows (harvest drafts, row backups) over the root's charts without
  any DB write. Measured on the 2026-09-01 export: τ_form 1.40 (the w), the
  stored reference row P sits at 1.01 — the pre-registered kill fired, so no
  write path reads the quantity and no row was touched; the entry, the
  autopsy and the rescue paths are in `qualitaetsmetrik.md` §14 („Laufform
  LF10") and `tintenfolger.md` §7.9 (#474).
