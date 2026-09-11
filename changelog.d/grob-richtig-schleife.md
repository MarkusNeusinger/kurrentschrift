### Added

- **Seven follower switches from the night loop on fechten · kann · unter.**
  The author refused to judge round 11 („die Buchstaben folgen nicht der
  Tinte, die springen wild hin und her") and asked for three bad candidates
  to build on until the ink runs roughly right. Each switch names one defect
  and is off by default, so every default fit is byte-identical:
  `--bar-bridge` plans the t's crossbar pen-down as `compose_word` draws it
  (the chain lifted at the t's foot — the author's own find);
  `--chain-seed grid-scale` searches a letter's WIDTH as well as its place,
  with a symmetric cost over the ink that letter owns, and `--seed-ramp`
  carries the scaled exit into the next connector so no chord runs through
  the paper; `--paper-weight` is the Tinten-Klammer, a steep hinge past one
  pen width from the skeleton; `--soll-source ink` lets the topology guard
  demand a crossing only where the ink has a branch point (the chart's `e`
  has a loop, this hand's `e` is a hairpin); `--kink-weight` is the
  Unstetigkeits-Preis, the author's 2026-09-06 Leitsatz as a term with an
  exact gradient (corners and lifts exempt); `--seed-form laufform`,
  `--no-init-terms` and `--seed-min-gain` are the loop's controls;
  `--letter-smooth` (Formglätte, second differences of a letter's
  displacement from its seed) is the loop's measured negative, kept as the
  control it was; `--chain-seed affine` is the Gauß-Verschiebung
  (`tools/pairlab/affinereg.py`): per letter an affine map — shift, x/y
  scale, rotation, shear — registered on the blurred ink image coarse to
  fine, the author's own picture of two signals laid over each other until
  their difference is minimal, and the first seed with which fechten and
  unter follow the plate without one excursion into the paper. The numbers of the loop stay on its progress page until a
  §14 entry books them — the author's own condition.
- **`tools.tracebench.reversals` prints the Papier-Strecke beside the
  reversal count.** A straight chord through the paper reverses nowhere and
  counted zero; its length in x-heights (`paper_len_xh`, the path walked at
  one pixel over the sensor's own paper test) is the second sensor the loop
  needed, and the one that caught the seed chords.
