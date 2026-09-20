### Added

- **Der Span-Zuordner: letter boundaries for a Bahn nobody decoded.** A
  followed Bahn gets its boundaries for free — every emitted sample inherits
  the slot of the seed sample that put it there, so the assignment IS the
  alignment. A Bahn the author DREW has no decode behind it, and until now it
  reached the Streifen-Editor with no seam to drag: every boundary would have
  had to be placed by hand on a box the machine could have labelled. The new
  mode `tools.eigenhand.pfad --spans` assigns them, over
  `tools/eigenhand/spans.py`: the same composed seed the follower decodes
  against, and a monotone match from the drawn samples onto it. It follows
  nothing — the run reads the stored list, labels the Bahnen it holds and puts
  every path back untouched, so it cannot move one coordinate of anyone's
  drawing. A box whose boundaries the author corrected is left alone WHOLE and
  named, because a boundary is only meaningful next to the ones beside it;
  `--replace-authored` is refused beside the mode, since there is nothing here
  to give up.
- **Measured before it was trusted, and the limit of the measurement is in the
  entry.** Over the 63 frozen Sütterlin words, with the follower's own
  assignment as the reference and BLAS pinned: the monotone rule agrees on
  99.5 % of samples and puts its worst boundary 0.34 x-heights off, while the
  order-free control drifts to 2.16 — a whole letter, and in the editor a seam
  the author would re-place rather than correct. So the monotone rule is the
  default. The entry says plainly what the number cannot prove: the reference
  Bahn was produced by decoding against this very seed, which makes the
  agreement an upper bound, and the measurement that breaks that circle runs
  on the author's own drawn Bahnen and owes its own pre-registration
  (`messjournal.md` §14 „Span-Zuordner `sep20`").

### Changed

- **A followed path now stores its own letter boundaries.** They were computed
  on every run and then dropped on the wire, because format 2 keeps them in a
  checked field and the tool still wrote the free-meta copy. They go into the
  checked field now, and they are dropped where the DELIVERED strokes cannot
  carry them — `cap_word_strokes` thins a Bahn past 128 runs and downsamples
  past 4096 points, after which every index is still well-formed and points at
  ink that was re-cut underneath it, which is the one failure the server's
  check cannot see.
- **`werkzeuge.md` splits the Eigenhand chain in two.** The capture — plan,
  Bogen, scan, Siebung, storage — keeps its section; what sits ON a stored
  strip (Bahn, boundaries, training set, report, archive) gets its own. Whoever
  reads up on `pfad` no longer loads the whole capture chain with it, which is
  what the section budget asks for rather than a raised number.
