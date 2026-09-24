### Added

- **The hand-wide Tintentreue distribution in the Eigenhand „Statistik"
  view.** `/admin/eigenhand?reiter=statistik` now counts the per-box Ampel
  over the whole hand — folgt · folgt teils · folgt nicht with the sensor that
  decided each, the grey state grouped by its reason („Format 1 —
  unvollständig gemessen", „von Hand gezeichnet", …), and an optional table
  per Fassung — where it used to carry a placeholder. It is counted from the
  existing hand-wide read `GET /eigenhand/pfade/{hand}` over the same rows as
  the Nachfahr-Liste, so the two surfaces cannot disagree, and never folded
  into one number (the Ampel refuses a scalar). The head says „vorläufig"
  with its (i) while any counted box was graded under borrowed thresholds. A
  count links into the Nachfahr-Liste only where an existing list axis
  selects exactly its boxes: the list deliberately has no axis per step, and
  a superset behind a number would contradict it.
