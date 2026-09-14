### Added

- **The Saat-Korrespondenz: a measured way from the decoded path to a
  Laufform anchor set.** `tools/laufform/saatkorrespondenz.py` walks the
  bookkeeping the Tintenpfad already carries — decoder state → seed sample →
  place in the composed letter → chart anchor — so an occurrence can be read
  off a pen path without distributing anchors over its arc length, which is
  the one thing that would silently redefine what a Laufform measures. The
  link `core/compose.py` does not record is not estimated but PROVEN per
  point (exact affine slice identity, residual below 1e-6); an anchor without
  a proof, or without a seed sample on the ink, is uncovered and says so.
  `tools.laufform.harvest --occurrences tintenpfad` is the arm that uses it,
  and `--apply` refuses the arm. At the default `fit` the harvest's drafts,
  occurrences and word records come out byte-identical; the one thing that
  does change there is `--diag-csv`, which gains the three `corr_*` columns —
  empty on every fit row — so a diagnostics file is not byte-comparable across
  this change. Author decision A48, way 1 of the three in `tintenfolger.md`
  §7.11, measured and filed as „Laufform A48 `sep13`" in `messjournal.md` §14.
