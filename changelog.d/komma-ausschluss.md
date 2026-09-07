### Changed

- **The plate's commas leave the reference ink, and the word bench is
  re-baselined on the root that produces.** Four word specimens — `Gewehr`,
  `Zügel`, `streiten` and, in the cross-hand abb22 set, `a22-dank` — carried
  the comma that follows them on the plate inside their reference crop, so
  the frozen ruler measured ink no letter can produce and every arm inherited
  the penalty for exactly those words. Each comma was verified on the frozen
  mask first (its own connected component, 31–94 px, 0.41–0.83 x-heights clear
  of any letter ink, fused with none) and then excluded through the mechanism
  the fixture format already has: an `exclude` rect in
  `data/sources/suetterlin-1922/words.json`, the same remedy `regieren` has
  carried since `aug31`. Darkness cannot do this job — the commas sit at
  `rel` 0.13–0.23, deep inside the ink-evidence mask's real-ink class — which
  is why the fix belongs in the reference definition rather than in the fit's
  filter. Words 0.109026 → **0.108153** on the new root `ccb036a5eb20…`
  (`Zügel` −0.028918, `Gewehr` −0.014439, `streiten` −0.011649, the other 60
  bit-identical); pairs stay **byte-identical** because their root was
  deliberately not rebuilt. Both followers are provably untouched: 63 of 63
  Kette rows stroke-identical, 63 of 63 Lotse rows byte-identical, dev-19
  digit-for-digit unchanged. The one word that gets worse is the finding, not
  the flaw: cross-hand `a22-dank` loses 0.039863 because the comma had been
  carrying its registration.
