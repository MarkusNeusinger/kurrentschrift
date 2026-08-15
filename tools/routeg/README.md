# routeg — the prior-free control of the Tintenfolger duel (measurement only)

Recovers a writing order from the ink alone — skeleton → segment graph →
good-continuation traversal — and turns it into a `tools/tracebench` candidate.
This is route G of `docs/proposals/tintenfolger.md` §4b.

Its role is **not "competitor" but control.** It guesses order and branch choice
*without the ductus prior*, so the difference between it and the chain fit on the
same ten words is the first measured number for what the prior actually buys
(`architektur.md` §2 as a measurement instead of an architectural belief). If the
chain fit does **not** beat it clearly, that is a finding of the first order.

**Nothing here is production code.** The recovered geometry stays in the
measurement layer: it never enters `core/`, the database or rendering, and it is
never a ductus source — stroke order and crossing resolution remain the prior's
job. `.gitignore` keeps `.venv/`, `vendor/` and `out/` out of the repo.

## Why the reference implementation is not what runs here

Route G names a specific paper and a specific repository:

* **Paper:** Moises Diaz, Gioele Crispo, Antonio Parziale, Angelo Marcelli,
  Miguel A. Ferrer, *"Writing Order Recovery in Complex and Long Static
  Handwriting"*, IJIMAI Vol. 7 No. 4 (2022), pp. 171–184; preprint
  [arXiv:2406.03194](https://arxiv.org/abs/2406.03194).
* **Code:** <https://github.com/gioelecrispo/wor> — **MIT License, Copyright (c)
  2020 Gioele Crispo** (a real `LICENSE` file at the repo root; GitHub reports
  `spdx_id: MIT`). Checked 2026-08-14. The license is therefore **not** the
  blocker.

The blocker is the runtime. Findings of the 2026-08-14 survey, all from the
repository itself:

| | |
|---|---|
| Language | **MATLAB** — 234 `.m` files, zero Python. No `setup.py`, no `pyproject.toml`, nothing on PyPI (`pypi.org/pypi/wor/json` → 404), so `pip install git+…` cannot work. |
| Requirement | *"You must have Matlab version 2016.a or major to run this code."* Plus the **Image Processing Toolbox** on the `wor()` path (`imbinarize`, `bwmorph`, `bwconncomp`, `rgb2gray`). |
| Octave | No compatibility claim, and it would be a real port: `classdef` with `persistent`-backed static setters, `+logging` package folders. |
| Maintenance | Last commit **2022-10-06**; 2 stars; one open PR untouched for ~4 years; no releases, no tags. |
| Extra bytes | `src/Utils/skeletonUtils/SalernoSkeletonization.jar` is a committed binary with **no stated license or provenance** — off the `wor()` path, but a reason on its own not to vendor the tree (`quellen-und-rechte.md`: the license of the bytes follows the bytes). |

Neither MATLAB nor Octave exists in this environment or in CI, so a route-G
candidate produced by `wor()` could not be reproduced by anyone running this
repository's gates. Rather than fake a dependency or leave the control slot
empty, the slot is filled by the **minimal own implementation** described below
— which is what `docs/proposals/tintenfolger.md` §4b asks for in this case, and
which is honest about being a reduction rather than a reimplementation.

Vendoring is legally fine (MIT) should someone with a MATLAB licence want the
real number later, and this package deliberately leaves that door open:
`prepare.py` writes exactly the input `wor()` documents — a pre-thinned,
8-connected, two-valued PNG with ink at 0 — so only stage 2 would have to be
swapped. What `wor()` returns would then need converting for `to_candidate.py`:
`[x, y]` are **row and column** indices (1-based MATLAB, not cartesian), dense
one entry per traced pixel, and **pen lifts are not in `x`/`y` at all** — they
have to be reconstructed from `wor_result.starters`/`.enders`/`.components`.

### What the reference does that this does not

Named so the gap is a documented reduction rather than a silent one:

* **cluster resolution.** The paper classifies each branch-point cluster by its
  rank and sub-type (T-pattern, retraced, coupled/"married", brotherhoods of
  merged clusters), pairs branches by a weighted good-continuity score
  `π_ij = ω_ext·|α_i−α_j| + ω_int·|β_i−β_j| + ω_cur·C_ij`, and then routes the
  pen *through* the cluster with Dijkstra on the cluster's own adjacency
  weighted so straight steps beat oblique ones. Here: one dot product.
* **a learned start-point prior** (`statisticalInitialPointComputed.mat`, a 2-D
  Gaussian fitted on SigComp2009 **signatures**). Here: none — deliberately,
  since a control that borrows a learned table is no longer prior-free. The
  reference's own fallback, the leftmost end point, is what this uses always.
* **retracing.** The reference models retraced ink; this walks every edge once.

Also worth knowing before anyone invests in the MATLAB path: the published
tuning and evaluation are entirely on **signature** databases, and the paper's
own conclusion names thinning quality as the limiting factor. Connected German
cursive is harder than anything it was measured on.

### Alternatives that were considered and rejected

* **`LingDong-/skeleton-tracing`** (MIT, actively usable, C + Python bindings) —
  turns a skeleton into polylines, but has no start-point model, no pen-down
  ordering and no crossing resolution by continuity. It solves vectorisation,
  not writing order, so it cannot answer route G's question.
* **`AyanKumarBhunia/Handwriting-Trajectory-Recovery`**, **`ChenZhounan/PEN-Net`**,
  **`MengLi-l1/StrokeExtraction`** — all carry **no license file at all**, i.e.
  all rights reserved. Not usable, regardless of technical fit. (PEN-Net is
  nevertheless where AIoU and LDTW are defined; the metric definitions are
  already in `docs/reference/glossar.md`.)

## The method that does run

Three stages, and the middle one is fifteen lines of decision:

| stage | script | what it does |
|---|---|---|
| 1 | `prepare.py` | frozen fixture entries → thinned PNGs (WOR's own input format) + `frames.json` |
| 2 | `recover.py` (over `graph.py`) | frozen skeleton → segment graph → good-continuation traversal → ordered pen runs in crop px |
| 3 | `to_candidate.py` | crop px → the stored `word_instances` trace frame → one candidate file |

`graph.py` builds the graph every writing-order paper builds: skeleton pixels of
degree ≠ 2 are nodes (endpoints and branch points), the degree-2 chains between
them are edges, **adjacent branch pixels are merged into one node** (an X rarely
thins to a single pixel — that merge is the paper's "cluster"), and a component
with no node at all is a closed loop that gets broken at its leftmost pixel.

`recover.py` then makes exactly three decisions, each the cheapest geometric
thing available where the ductus prior would have something to say:

1. **where the pen starts** — the leftmost endpoint of the leftmost component;
2. **which branch continues** — at a node, the unvisited edge whose direction
   best continues the incoming one (a single dot product over a 5-point window);
3. **when the pen lifts** — when the current node has no unvisited edge left.

The one assumption about writing it makes is that Latin script runs left to
right (it starts leftmost, and breaks a first-step tie towards +x). That is an
assumption about the *script's direction*, not about any letter's ductus.

Stated limits, so a bad number is read as the method's ceiling and not as a bug:
it never retraces an edge it has already walked (a doubled downstroke is written
once), it has no model of delayed marks (an i-dot is written when its
x-position comes up, not after the word), and it cannot know that two ink
components belong to one pen run.

## Running it

```bash
# 1. Frozen entries → thinned inputs + frames.json (default ids = the frozen
#    tracebench dev set: die · laden · linken · mit · muß · und · unter · Wer ·
#    will · zwei).
uv run python -m tools.routeg.prepare

# 2. The traversal. Pure numpy/scipy, no venv, ~0.7 s for all ten words.
uv run python -m tools.routeg.recover

# 3. Ordered crop pixels → candidate file
uv run python -m tools.routeg.to_candidate

# 4. Score it
cp tools/routeg/out/candidates/routeg-graph.json temp/routeg-t0.json
uv run python -m tools.tracebench.run --candidate file \
    --candidate-file temp/routeg-t0.json --label routeg-t0 \
    --json temp/tb-routeg-t0.json

# 5. …and look at it beside the hand reference (the duel page reads this
#    candidate like any other; add --candidate chain=… for the third layer)
uv run python -m tools.tracebench.view --split dev \
    --candidate routeg-t0=temp/routeg-t0.json \
    --rows routeg-t0=temp/tb-routeg-t0.json --out temp/duell-routeg.html
```

The fixture roots are gitignored, so a fresh git worktree has none: run the
three stages with `--fixtures-root` pointing at the checkout that holds them
(and `tracebench` with `--fixtures`), or symlink
`tools/wordbench/fixtures` there.

Stage 2 needs **no isolated venv**: the whole method is numpy plus
`scipy.ndimage.label`, both already runtime dependencies. The `tools/inksight`
three-stage split exists because TensorFlow pins a whole interpreter; here the
split is kept only because it is the shape the candidate contract expects (and
because it is where a MATLAB `wor()` would slot in), not because a dependency
crosses.

`recover.py` reads the frozen `ref_skel.npz` array directly rather than decoding
stage 1's PNG — same bits, no image round-trip. The PNG exists because it is
what an external recovery tool would consume.

## Frames and the candidate contract

`to_candidate.py` converts crop pixels into the stored `word_instances` trace
frame through **`_px_to_word_units`** — the same function the harvest and the
follower use, deliberately imported rather than re-implemented. It comes from
its definition site `tools.pairlab.trace` rather than the
`tools.laufform.harvest` re-export the InkSight stage imports, because that
module pulls `tools.wordlab` and with it matplotlib.

Registration is `{tx: 0, ty: 0, baseline_row: baseline_y - rect[1]}` with
`xh = baseline_y - midband_y`, both read from the frozen fixture `word.json`.
`tx = 0` is not a placeholder: stored `(u, v)` labels are *not* canonical (the
composer's grid search moves `tx`, the word editor folds `ty` into
`baseline_row` — tintenfolger.md §2.1), while a recovered trace is positioned in
the crop. The crop's own frame is therefore the honest registration, and it is
the one the bench re-expresses every trace in.

Output: `out/candidates/routeg-graph.json` — named for what produced the
geometry, **not** `routeg-wor`, because a candidate file that claims a method it
did not use is the one label error a measurement archive cannot recover from.

```json
{"tool": "routeg-graph", "label": "routeg-graph", "version": "2026-08-14",
 "style": "suetterlin", "source_id": "suetterlin-1922", "set": "words",
 "frame": "word_registration",
 "rows": [{"kind": "word", "specimen_id": "die", "word": "die",
           "registration_px": {"tx": 0, "ty": 0, "baseline_row": 72.0},
           "xh_px": 31.0, "strokes": [[[0.61, 0.05], [0.63, 0.91]]],
           "status": "ok",
           "meta": {"skeleton_px": 348, "nodes": 14, "edges": 14,
                    "components": 2, "strokes": 6, "points": 333}}]}
```

**Strokes are exactly what the traversal produced** — no cleanup, no resampling,
no merging, no dropping of degenerate runs. The only judgement applied is the
wire contract of `api.schemas.WordInstanceItem` (1..128 strokes, 2..4096 points
each, |coordinate| ≤ 100); a row that violates it keeps its geometry and is
stamped `status: "failed"` with the reason in `meta.detail`. A word the recovery
crashes on travels as a failed row too, because a control that silently covered
nine of ten words would report a better median for the nine. Consumers must
respect `status` — the bench does not read the field, but it re-validates every
row against the SAME bounds (`tools/tracebench/candidates.py::wire_violation`,
pinned equal by a test), so its verdict and this one agree by construction
rather than by luck.

## Tests

`tests/test_routeg_pipeline.py` (repo env, no network, no venv, no fixture root)
pins the parts a wrong answer would hide in: the graph built from hand-drawn
synthetic skeletons (a plain line, a fork, an X whose adjacent branch pixels
must merge into ONE node, a bare ring), the traversal's three decisions
(good continuation through a crossing, the leftmost start, a lift on a dead
end), every edge walked exactly once, and the candidate contract (frame literal,
wire bounds, `status` on violation, the registration derived from a frozen
entry).

## Measured on the dev split (2026-08-14)

Ten words, `--split dev`, `--resample-step 0.02`, against the author's hand
re-tracings. Numbers and reading in `docs/reference/qualitaetsmetrik.md` §14;
the short version is that the control does exactly what a control should:

* `aiou_median` **0.833** — *higher* than the hand references score against
  themselves (0.685), because the traversal rides the skeleton by construction.
  Being on the ink is not the same as writing it.
* `dtw_xh_median` **0.820** against the chain fit's 0.062 — the path through
  that ink is far from the hand's. That ratio is what route G exists to
  produce, and it is a LOWER bound on the gap: the reference implementation
  also models retracing, which is one of the two rows this control loses
  hardest on.
* `cross_missing` **15**, `retrace_missing` **15**, `lift_delta_total` **+90** —
  it loses most crossings, never retraces, and lifts about nine extra times per
  word (the hand writes these words in 1–2 pen strokes; the control needs
  6–18). Those are the co-primary structure gates, and they are where a
  prior-free method fails.

**End-to-end frame check.** Converted back to crop pixels, the candidate's ink
box sits inside the mask's on every edge by roughly half a stroke width — e.g.
`die` `x 10..143 / y 9..72` against the mask's `x 7..146 / y 8..75` — which is
exactly the inset a skeleton has. That says the registration and the
`_px_to_word_units` chain are right; it says nothing about trace QUALITY, which
is the bench's job.
