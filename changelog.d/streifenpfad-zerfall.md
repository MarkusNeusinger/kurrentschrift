### Fixed

- **Following an own-hand strip skipped words the hand actually writes.** Three
  of seven words on the author's own strips were refused as „unauthored", for
  two reasons that both had nothing to do with his ink. A ligature whose
  canonical template is absent now decays into its letters, exactly as
  `/write/word` and the labs already did — `ch` is authored nowhere by design,
  so every word holding it (`gefährlich`, and the author's own
  `Kurrentschrift`) fell out. And the ductus seed now comes from the source's
  LIVE templates instead of the frozen word-bench fixtures: those carry only
  the 34 glyph keys the 63 bench words need, so `immediately` failed on a `y`
  the hand has had all along. A bench word composes frozen because it is scored
  against a frozen reference; a strip is never scored against it, and only the
  style-level constants (`style_ratio`, `width_resolver`, `constant_nib_units`)
  still come off the manifest. The bench paths read the frozen root unchanged.
