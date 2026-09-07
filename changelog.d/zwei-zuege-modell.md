### Added

- **Zwei-Züge-Modell — deconvolve the pen instead of thinning the blob.** Where
  two pen strokes fuse around a small counter, `skeletonize` returns the axis of
  the fused lump rather than the two pen paths, and every consumer of that axis
  inherits an aperture 0.035–0.104 xh too tight before any fit runs. The new
  `tools/pairlab/zweizuege.py` takes the other route: the pen's half width is
  known (0.0968 xh, the plate's own), a Gleichzug pen paints the Minkowski sum
  of its path with a disc of that radius, so **no pen sample may sit closer than
  `w_pen` to a counter the plate holds open** — and the correction pushes the
  samples that do exactly far enough out along the counter's distance field.
  Three rules keep it a mechanism rather than a knob: it acts only on catalogue
  loops the plate holds `offen` in the size classes where the instrument decides
  (`klein`, `mittel`) and only where the plate shows a hole in that very
  occurrence; the displacement fades out C¹ over half a nib of arc so the seam
  carries no kink; and a push that pulls the loop's own self-crossing open is
  reverted rather than reported as a widening.
- **`--zwei-zuege` on the ink follower, default off.** The correction runs after
  the last follower round on the assembled pen path — the smallest insertion
  point that exists: no chain solve changes, no `core/` byte moves, and it reads
  the plate plus one frozen pen constant, never a Laufform row, so it cannot
  close the harvest fixed point. Every run stamps its per-loop verdicts into the
  report, refusals included, because a loop the model declines is as much of a
  reading as one it corrects.

- **Two blend lengths on the follower's command line.** `--zwei-zuege-taper`
  and `--zwei-zuege-smooth` expose the arc lengths of the correction's C¹ fade
  and its anti-raster average, because that is the one length the measurement
  moved: both are stated in x-heights while the trace is sampled in points, and
  at 0.0265 xh per sample the shipped defaults span 2.7 and 1.4 samples.

### Changed

- **A frozen word case carries its ink mask.** `WordCase` gains `mask`, loaded
  from the fixture entry's `ref_mask.png` beside the skeleton it was thinned
  from. The counters of the plate's ink are evidence in their own right, and
  re-binarising the crop to recover them would move goalposts the metric holds
  fixed.
