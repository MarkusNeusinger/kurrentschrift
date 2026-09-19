### Added

- **Filters in the Auftragskorb drawer.** Three selects — Status, Ebene and
  Stufe — narrow the basket the admin already holds, and the grouping stays
  the one by status with the handed-back rows on top. Grouping BY Stufe was
  the obvious alternative and cannot work: a stage is a diagnosis written by a
  transition, so a freshly filed row carries none — the bulk of the queue —
  and all of them would fall into one nameless bucket, while the handed-back
  rows could no longer stay on top. The counts in the title and the header
  badge keep reading the unfiltered rows — a filter that changed them would
  let the workbench claim work was finished by hiding it. Choosing „Erledigt"
  reveals the archive on its own, so the filter and the „erledigte anzeigen"
  switch never contradict each other, and an empty list now says which of the
  three silences it is — and only names the switch when flipping it would
  really bring a row back.

### Fixed

- **Dropdown options meet the touch floor above the phone breakpoint.** MUI's
  own 48px minimum for a menu option stops at `sm`, which left the admin's
  selects at about 42px on a tablet — under the binding 44px of
  design-system.md §9.3, on the device most likely to be touched. The floor
  now sits in the theme, so every select inherits it.
