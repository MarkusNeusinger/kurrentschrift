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
  letters and its chamfer to the specimen skeleton — high values = the
  connector's shape/coupling is wrong even at perfect placement. Since
  2026-09-04 this is `core.compose`'s own join call, recorded during the
  composition and replayed with the two fit shifts (`prodconn.py`); the
  hand-written mirror it replaced had been frozen since 2026-07-11 while the
  join block was rebuilt three times, and differed on 89 of 248 joins (audit
  Befund 18, numbers in `docs/reference/messjournal.md` §14 „Übergänge
  P-Spiegel `sep04`"). `analyze._generate_connector` survives as that frozen
  2026-07-11 curve for the chain solver's initialisation and the parity test —
  it is no longer the production connector and no longer claims to be;
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

## Harvest (redesign R3 Erstbefüllung)

`tools/pairlab/harvest.py` turns the dissections into `glyph_pairs` override
drafts: placement offset from the rigid independent fits, connector centerline
from the specimen's own joining stroke (baseline-locked so it meets the
composed entry), one best occurrence per pair. Needs no viz extra and writes
nothing without `--apply`:

```bash
# dissect all Abb.-20 pairs, report + QC to temp/pair_harvest.json
uv run python -m tools.pairlab.harvest

# import as UNAPPROVED drafts via the local admin API (needs ADMIN_TOKEN)
uv run python -m tools.pairlab.harvest --apply

# additionally approve named pairs in the same write (measured winners only)
uv run python -m tools.pairlab.harvest --apply --approve B:i,I:n,D:u,O:f
```

The stdout QC line compares `gen` (generated connector chamfer at independent
placement) against `harvest` (the stored centerline) — a harvest that scores
worse than the generator should stay a draft. Measure the composed effect with
`tools/wordbench/run.py --set pairs --overrides temp/pair_harvest.json` (an
override run is its own measurement, never the headline). Review + Freigabe
stay in the pair editor (`/admin/uebergaenge`) — the human gate.

## Chain fit (issue #278 Stage A)

Everything above fits the two letters **independently** and reads the join out
of what is left between them. `tools/pairlab/chain.py` is the alternative:
`letter → connector → letter` as ONE problem, the way the pen wrote it.

- **Three segments, one anchor array.** Both letters are the **chart row**
  (variant 0 — never the composed/Laufform geometry, which would make the
  statistics converge on the renderer), the connector is the generated
  exit→entry polyline whose interior points are free anchors with **no form
  regularisation** (regularising them against the generated Bézier would bias
  `gen_chamfer`, the very audit number they exist to feed). Where two letters
  are composed on top of each other the generator's handle floor turns that
  polyline into a cusp of ~0.05 xh carrying every one of its points, and the
  curvature-change term (scale 1/ds²) then blows up by ~10⁷ and eats the whole
  iteration budget — such a connector is re-discretised to the anchor count its
  chord can carry (`regularise_connector_anchors`): same shape, same endpoints,
  nothing above the threshold touched.
- **The seam is a shared anchor index, not a penalty.** The last anchor of the
  left letter's last non-diacritic stroke and the first of the right letter's
  are literally the same parameters as the connector's endpoints, so C0
  continuity holds by construction and the letter/connector boundary stops
  depending on whether the letters happen to touch on this specimen.
- **Placement stays placement.** One unregularised translation block per slot,
  bounded exactly like `analyze._fit_letter`'s grid search; the connector rides
  an arc-length ramp between its neighbours instead of getting a third block.
- **Word-wide, capped coverage.** The skeleton window is the union of both
  letter windows with the hole between them closed, the point budget scales
  with the segment count, and the coverage distance is Huber-capped so foreign
  ink in the pair window has bounded leverage.
- Per-segment residuals and gates (`core.fit`'s own `CONVERGED_*` thresholds),
  so a failed connector still leaves two usable letters. Each letter carries
  **two** coverage gates: the union window it was fitted against and its own
  letter-local window (`ChainSegmentSpec.cov_window_px`) — the window the
  independent M4 trace was always graded in, so „converges at least as often"
  is a like-for-like statement. Only the report differs; the fit is identical.

`tools/pairlab/chainbench.py` runs BOTH paths over the same occurrences of the
same frozen specimens and prints the four Stage-A metrics (convergence · joins
that are empty today · connector shape `dconn` against the ink-read stroke ·
letter shape against the hand's per-anchor MAD) plus the kill-criterion
signals (tail-stub trend · capital partition · seam calibration against the
0.2–0.4 xh stub-replacement zone). M1 prints **three** convergence columns over
the same solves (union gate · letter-local gate · baseline re-graded on the
union window with the same attribution) plus the failure split into coverage
and geometry, and M3 prints the `dconn` medians twice — whole curve and
**arc-matched**: the ink-read connector cut to the specimen's ink gap
(intersected with the curves' own x-spans) and the generated and chained one
trimmed to the same stretch of writing, since the chain connector owns the stub
zones the ink-read one does not have:

```bash
# the Abb.-20 drills — the fast smoke target (34 occurrences, ~30 s)
uv run python -m tools.pairlab.chainbench --set pairs

# the full Stage-A run over words + pairs of the SAME hand (248 occurrences)
uv run python -m tools.pairlab.chainbench --set all --jobs 8 \
    --aggregates temp/aggregates.json \
    --json temp/stage_a.json --csv temp/stage_a.csv

# narrow down while iterating
uv run python -m tools.pairlab.chainbench --set all --pairs de,on,bi --max-occ 4
uv run python -m tools.pairlab.chainbench --set pairs --ids Bi,Du
```

`--set all` means words + pairs and nothing else — the Abb.-22 plates are a
DIFFERENT writer and are never pooled with this hand. `--aggregates` supplies
M4's MAD floor from `GET /hands/{hand_id}/aggregates` (admin-gated, dump the
response to a file); without it M4 reports the deltas and says it has no
measured floor. Fixtures come from `tools/wordbench/export_fixtures.py` (DB) or
`tools/wordbench/fetch_fixtures.py` (deployed API, for sessions with no Cloud
SQL egress).

**Measurement only.** The chain reads frozen fixtures and writes JSON/CSV under
`temp/`; it never touches the DB, the API, `core/` or rendering, and its
connectors are still not allowed into `pair_aggregates` — after the re-measured
Stage-B preconditions the reason is no longer „the number is incomparable" but
the loop-exit class (d, ſ), which is where the chain connector still misses the
ink by +0,17 xh. See `docs/proposals/uebergaenge-befund.md` §5c for the verdict,
the three M1 gates and the arc-matched M3.

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
