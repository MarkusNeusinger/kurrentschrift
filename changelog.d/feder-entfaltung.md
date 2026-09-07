### Added

- **Feder-Entfaltung — the pen taken out of the EVIDENCE at a counter.** The
  ink follower is pulled onto the skeleton of the frozen mask, and around a
  small counter that skeleton is not a pen path: two pen capsules that pass
  within a couple of pixels of each other paint one ribbon whose medial axis
  hugs the hole more tightly than either pass did. Two earlier arms argued
  against that evidence — a post-hoc push off the hole (R3) lost its smoothness,
  and the same condition priced inside the solve (R3c) could not break a
  symmetric configuration, because at a fused spot the ink term itself sits on
  the lump axis. The new `tools/pairlab/counterevidence.py` corrects the
  evidence instead: every skeleton pixel closer to an open catalogue counter
  than the plate's own half width is dropped, and the level set one half width
  outside that counter takes its place, clipped to the ink and reaching only as
  far around the hole as the dropped pixels did. It is a construction rather
  than a fit — every point of that level set lies where a pen leaving the hole
  open must have run — so no fade length has to be chosen: the solver does the
  smoothing.
- **`--counter-evidence` on the ink follower, default off**, with
  `--counter-evidence-half-width` for the pen that is taken out and
  `--counter-evidence-size-classes` for the catalogue classes it corrects. The
  correction replaces the case's skeleton where the K-C ink-evidence mask does,
  so seed windows, solve fields and coverage targets read ONE evidence; the
  bench's frozen `ref_mask.png`/`ref_skel.npz` are untouched, and every consumer
  outside the follower never builds the corrected case, so the harvest is
  byte-identical by construction. Three refusals keep it a mechanism rather than
  a knob — never invent ink, never lose the loop, never widen what is already
  right — and every run stamps the per-loop verdicts into its report, refusals
  included.
- **The raster diagnostic that had to come first.** Before any of the above:
  is the fused lump real ink, or an artefact of a 30-pixel crop? Measured three
  ways on the same counters — the frozen adaptive mask, a global 50 % level set
  of the grey, and that level set on 4x bicubic grey — plus the medial-axis
  indicator at both scales. The crop turns out to be an unscaled slice of the
  committed plate, the grey reads the same counter as the mask at 1x and a
  slightly smaller one at 4x, and the indicator survives the sharper reading.
  The fusion is ink. The numbers and the pre-registered decision rule are in
  `docs/reference/messjournal.md` §14 "Kette R4 Feder-Entfaltung `sep07`".
