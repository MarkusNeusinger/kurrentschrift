### Added

- **A word mode for the human judgement pass, on the authenticity question.**
  `tools/humanbench/build.py --word-arms BASE CANDIDATE` builds a round that
  shows one whole specimen word from a frozen word-bench fixture root with two
  compositions drawn over it as INK — filled silhouettes for the letter
  bodies, capsules of their own width for the generated connectors — and
  `page.py --question authentic` asks „Welche Zeile sieht echter geschrieben
  aus?“ instead of the accuracy question. It is the only instrument in the
  project that can see the three defects every frozen ruler resamples away or
  never measured: the anchor-median zigzag of a Laufform row, the too-thin
  stroke, and the kink at a connector's seam. Until it existed, every
  improvement to the ductus was unprovable and every adoption a matter of
  taste (`docs/reference/menschliche-bewertung.md` §8a).
- **A pre-registered decision for paired rounds, written before the first one
  was run.** `analyse.py` gained the five-step paired plan — side reliability
  from the mirrored repeats, side balance, the verdict, the per-class split,
  drift — and adopts a candidate only at ≥ 60 % of the decided screens with
  ≤ 25 % „kein Unterschied", and only when the repeats show the judge was not
  answering by position. Both denominators are printed, because the two
  conditions ask different questions and putting the ties in both would count
  the same fact twice.
- **`tools/humanbench/wordarm.py`, the reference producer of the arm files.**
  It composes one arm from the frozen fixtures by importing the word bench's
  own composition and placement, so a human verdict and the automatic ruler
  can never be about different pixels; `--laufform` feeds a candidate running
  form, `--nib` a different pen, `--registration-from` pins the placement so a
  systematically shifted arm cannot become a tell. The builder composes
  nothing itself — an instrument that computed its own candidate could drift
  away from the ruler that has to confirm it.

### Changed

- **The paired page carries its question into the result file's header.** A
  round on the accuracy question is tagged `VERGLEICH/n`, one on the
  authenticity question `ECHTHEIT/n`. The two measure different properties and
  their rounds are not comparable, so a text whose analysis plan is lost can
  still be filed under the right question.
