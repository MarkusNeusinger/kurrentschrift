# pairlab — independent-fit dissection of letter joins

Answers ONE question the word bench cannot: is a bad Übergang caused by the
**connector's shape** or by the **letters' placement** — and does the real
pen reshape the **letters' own first/last piece** for the join? The bench
scores the composed placement, so those three failure modes are entangled;
pairlab removes the placement confound by re-fitting every letter of a real
specimen word INDEPENDENTLY (bounded translation grid against the frozen
skeleton) before judging the join between two of them.

Per occurrence of a pair (in the Abb.-19 words and the Abb.-20 isolated
pairs) it reports and draws:

- the per-letter shifts the independent fit needed (units of x-height) —
  large values = the composition put the letter in the wrong place, not the
  connector;
- the production connector REGENERATED between the two independently placed
  letters (`_generate_connector` mirrors `core.compose`'s join block — same
  constants and guards) and its chamfer to the specimen skeleton — high
  values = the connector's shape/coupling is wrong even at perfect placement;
- the specimen's own connecting stroke (skeleton tracked column-by-column
  through the inter-letter gap) with its end tangents;
- **tail/head adaptation**: deviation of A's last / B's first stroke from the
  specimen as a function of arc distance from the join — how far into each
  glyph the real pen departs from the template before the join begins (the
  chart-cell coupling stubs are the usual suspect);
- **ductus traces** (default on, `--no-trace` skips): both templates WARPED
  onto the specimen ink along their known ductus (`core.fit.
  fit_template_to_instance` against a letter-local skeleton window). The
  fitted pair is the occurrence's ground-truth target: its end point/tangent
  are the true coupling geometry the generator should reproduce, and the
  stub-region anchor displacement (`stub d` in the caption) says how far the
  fit had to bend each coupling stub to reach real ink.

Findings + solution options live in
`docs/proposals/uebergaenge-befund.md`. Diagnostics only: nothing here is
production code or part of the frozen bench metric.

## Quick start

```bash
# fixtures must exist (once): uv run python -m tools.wordbench.export_fixtures --set all

# every real occurrence of r→e, join close-ups + deviation profiles
uv run --extra viz python -m tools.pairlab re

# several pairs, JSON dump for aggregation
uv run --extra viz python -m tools.pairlab de on bi --max-occ 4 --json temp/pairs.json

# multi-char glyph bases comma-separated (long s, umlauts)
uv run --extra viz python -m tools.pairlab longs,a ue,b

# whole-word overlays instead of the pair close-up
uv run --extra viz python -m tools.pairlab re --full-word
```

One PNG per pair (rows = occurrences, columns = overlay + profile) into
`$PAIRLAB_OUT` (else `temp/`). Overlay colours: first letter dark red, second
green, other letters grey — all at their INDEPENDENT placements; the ductus
traces (the templates warped onto the real ink) purple; regenerated connector
bright red dashed; the specimen's own connecting stroke strong blue;
adaptation zones (template ink the specimen does not corroborate) orange;
specimen skeleton light blue.

## Reading the numbers

```
re: 4 occurrence(s)
  regieren   [word]  A +0.13,+0.07  B +0.00,+0.03  gen 0.107  tail 0.00  head 0.23  exit +29°/-72°  entry +38°/-27°
```

- `A/B ±x,±y` — the letter's independent-fit shift (xh units, on top of the
  word-level registration). `!` after `[kind]` = a fit hit the search bound
  (`FIT_DX_UNITS`/`FIT_DY_UNITS`) — distrust that row.
- `gen` — mean skeleton distance of the regenerated connector (xh units).
  ≤ ~0.07 lies on the ink; ≥ ~0.1 visibly misses it.
- `tail`/`head` — adaptation length (xh of arc) at A's end / B's start where
  the specimen deviates > `ADAPT_THRESH_UNITS` from the template stroke.
- `exit`/`entry` — generated vs. specimen tangent (`—` = the letters touch,
  no gap to track).
- `fit exit/entry y…@…°` — the ductus trace's fitted endpoint geometry (the
  target coupling for a well-behaved diagonal join). On the stub-replacement
  classes read it TOGETHER with `real y`: a fitted endpoint far above the
  tracked join departure (d→e: fit exit ~1.3–1.5 vs. real y ~0.8) means the
  fit absorbed the exit stub into the loop flank — the stub has no ink of its
  own, which is precisely the trim signal. `(FAIL)` = a fit did not converge;
  distrust that row's fit numbers.

A pair spec is two glyph-key BASES: `re` = r→e; positions are matched by the
slots, Schluss-s is `s`, long s is `longs` (the Abb.-20 `sa` is written ſa —
query `longs,a`).
