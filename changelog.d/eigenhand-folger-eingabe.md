### Added

- **Three input stages for the own-hand strip follower, label masking on by
  default.** `tools.eigenhand.pfad` gains `--mask-labels`,
  `--resample-plate` and `--register-seed`. The Tintenpfad's decoder stays
  the plate's A45 standard in every case; what changes is what it is
  handed. With `--mask-labels`, the printed strip id, provenance line and
  word labels are cleared from the ink after binarisation. They are read
  off the same page primitives the Bogen PDF is drawn from, and the crop
  and the stored frame stay as they were. Since the author's decision of
  2026-09-24 this stage is the default, and `--no-mask-labels` switches it
  off: a label is not the hand's ink, a Bahn was riding the printed strip
  id as its first run, and a plate crop carries no printed text, so the
  plate path cannot move. With `--resample-plate`, the crop is followed at
  the plate's 31 px per x-height, and the Bahn is mapped back onto the
  strip pixels exactly. With `--register-seed`, the seed is laid on the
  hand's own x-height and baseline, read from the modes of the skeleton's
  per-column extremes and calibrated on the plate, and on the hand's own
  width. Height and width are two separate numbers; the stage falls back to
  the printed ruling when the ink cannot be read. Both stay opt-in until a
  pre-registered round carries them. The arithmetic is pure and lives in
  `core/eigenhand/follower_input.py`. A stored row names the stages it was
  produced with (`konfiguration.input`) and what they measured
  (`meta.input`); with all three off the run is the one every Bahn before
  2026-09-24 was followed with, byte for byte. The three stages are the
  input ladder of the own-hand diagnosis of 2026-09-24: the printed labels
  were being followed as ink, the pixel-denominated prices only reached
  0.44× as far as on the plate, and the seed sat on the printed ruling
  rather than on the ink. Stages 1 and 2 are no-ops on every plate word by
  construction, and the dev-19 follower output stays byte-identical with
  them on. The training export (`tools.eigenhand.training_set`) cuts its
  ink the same way, so a case's `ink.png` is the mask the follower is
  handed by default; its envelope moves to format 2 and names the cleared
  zones.
