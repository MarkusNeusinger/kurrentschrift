### Added

- **Three opt-in input stages for the own-hand strip follower.**
  `tools.eigenhand.pfad` gains `--mask-labels`, `--resample-plate` and
  `--register-seed`, each off by default, so a run without them follows
  exactly as before. The Tintenpfad's decoder stays the plate's A45
  standard in every case; what changes is what it is handed. With
  `--mask-labels`, the printed strip id, provenance line and word labels
  are cleared from the ink after binarisation. They are read off the same
  page primitives the Bogen PDF is drawn from, and the crop and the stored
  frame stay as they were. With `--resample-plate`, the crop is followed at
  the plate's 31 px per x-height, and the Bahn is mapped back onto the
  strip pixels exactly. With `--register-seed`, the seed is laid on the
  hand's own x-height and baseline, read from the modes of the skeleton's
  per-column extremes and calibrated on the plate, and on the hand's own
  width. Height and width are two separate numbers; the stage falls back to
  the printed ruling when the ink cannot be read. The arithmetic is pure
  and lives in `core/eigenhand/follower_input.py`. A stored row names the
  stages it was produced with (`konfiguration.input`) and what they
  measured (`meta.input`). The three stages are the input ladder of the
  own-hand diagnosis of 2026-09-24: the printed labels were being followed
  as ink, the pixel-denominated prices only reached 0.44× as far as on the
  plate, and the seed sat on the printed ruling rather than on the ink.
  Stages 1 and 2 are no-ops on every plate word by construction, and the
  dev-19 follower output stays byte-identical with them on.
