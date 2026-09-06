### Added

- **A report-only continuity sensor for the composed word centreline.** The
  word bench and the trace tools all measure how FAR a path sits from a
  reference; none of them asks whether the path is continuous with itself, so
  a kink and a smooth bow through the same endpoints score alike. The new
  `cont_*` columns measure the missing quantity — the tangent jump at a point
  that is not a ductus event, the mid-stroke direction wobble, and the
  Pfeilhöhe over a two-nib chord — with every window derived from the pen
  rather than from a round, and with crossings, retrace zones, pen lifts and
  reversal corners exempt and counted. Frozen and report-only: the headline
  `bench_loss` and `pair_loss` stay byte-identical, and `core/word_metric.py`
  is untouched.
