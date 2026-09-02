### Fixed

- **Jumped-to headings hid under the taller mobile header.** #504 grew the phone
  bar from 82 to 121px when its two nav rows took the 44px touch floor, but the
  fragment targets kept a 100px scroll margin — so a jump-list entry on
  /schriftkunde, or a `?g=` deep link into the Tafel, could land its heading
  behind the sticky bar. The margins now clear the real bar and switch at `sm`,
  where the nav collapses to one row, instead of at `md` (#506).
- **The touch sweep claimed more coverage than it had.** Four holes, each of
  which let a real violation pass unseen: it skipped every `opacity: 0` element,
  which is exactly how MUI lays a native input over a Switch; it measured the
  quiz only mid-round, so the setup chips and the whole results screen were
  never seen; it excused any interactive SVG group as the known Schreibtafel
  shortfall rather than the tiled letter cells alone; and it treated every
  underlined link as running prose, which silently exempted the Schriftkunde
  jump list — navigation, not prose. Closing them raised the swept population
  from 217 to 255 and turned up 18 controls under the floor (#506).
- **Eighteen more controls were under the 44px floor**, found once the sweep
  stopped lying to itself: the fourteen jump-list entries on /schriftkunde, the
  two quiz setup chips, the worksheet's switch rows and the results screen's
  confusion pills. The jump list and the switch rows grew real height — an
  invisible target would have overlapped the row above in a wrapping list, and a
  switch is tapped by its label; the rest keep their drawing and take the floor
  from `hitArea()` (#506).
- **The run could contradict itself in its last two lines**, printing the count
  of known shortfalls and then „all reach the floor". It now says all *other*
  targets do (#506).

### Changed

- **A control wrapped in a `<label>` is measured at the label.** That is where
  the tap lands, and it is what makes MUI's transparent Switch and Checkbox
  inputs measurable at all instead of reporting the geometry of an invisible
  overlay. `MuiFormControlLabel` carries the floor as `minHeight`, so the
  control's own drawing stays untouched (#506).
