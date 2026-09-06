### Added

- **The stranded-anchor repair can be told where the loops are, and it ships
  loop-blind.** The repair asks whether one anchor is a lone excursion and
  answers it from step lengths alone — but inside a tight counter that same
  description fits the apex the loop is MADE of, and chording the apex to its
  neighbours (which lie on the loop's two strands) draws the chord straight
  through the hole. `tools/pairlab/anchors.py` gains `LOOP_AWARE_REPAIR` and a
  `loop_ranges` argument that names the anchor ranges over which the CHART row
  closes a loop (`core.aggregate.loop_ranges`, occurrence-independent — reading
  them per occurrence would make the repair depend on the excursion it is
  judging); with the switch on, a flagged anchor inside such a range is left
  alone. The module still imports nothing project-side: the caller passes the
  ranges. `tools/laufform/harvest.py` wires it to the OCCURRENCE repair only
  (the trace repair works on assembled word strokes, which carry no anchor
  ranges) and exposes it as `--loop-aware-repair`, memoising one loop-range
  computation per glyph key and skipping it entirely while the switch is off.
  Default off, so every stored occurrence stays reproducible.

### Changed

- **The harvest is measured, and it is not where the counters go.** LF13 read
  the step from Kette fit to stored occurrence as a loss of 0.016–0.057 xh of
  aperture and named it the campaign's next lever. Read on ONE chart-anchored
  range at both ends — instead of a raster loop matched to a plate counter at
  one end and the range at the other — the step is 0.0000 to +0.0077 xh over
  the five counter-carrying keys, and 43 of 44 occurrences move by less than
  0.01 xh. The two rulers agree occurrence by occurrence (0.0000 median
  difference at both ends), so the earlier number was a loop-identification
  difference, not a movement: 21 of 39 joined occurrences agree to 0.0011 xh and
  18 disagree by a median of 0.067, in words where a neighbour's loop falls
  inside the 0.45 xh matching window. The one real step inside the harvest is
  the stranded-anchor repair, above.
