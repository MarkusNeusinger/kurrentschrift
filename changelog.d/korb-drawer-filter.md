### Added

- **Filters in the Auftragskorb drawer.** Three selects — Status, Ebene and
  Stufe — narrow the basket the admin already holds, and the grouping stays
  the one by status with the handed-back rows on top. Grouping BY Stufe was
  the obvious alternative and cannot work: the API asks for a stage only when
  a row closes, so the whole live queue carries none and would fall into one
  bucket. The counts in the title and the header badge keep reading the
  unfiltered rows — a filter that changed them would let the workbench claim
  work was finished by hiding it. Choosing „Erledigt" reveals the archive on
  its own, so the filter and the „erledigte anzeigen" switch never contradict
  each other, and an empty list now says which of the three silences it is.
