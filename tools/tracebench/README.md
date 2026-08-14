# tracebench — the measuring stand for automatic word tracing

Grades an automatic tracing of a specimen word (a "Tintenfolger") against the
hand-made reference tracings of the same plate. The candidate today is the
Stage-B chain fit (`tools/pairlab/chain.py` through
`tools/laufform/harvest.py --path chain`), which was built as a MEASURING fit —
its regularisation deliberately pulls towards the template form — and was never
meant to follow ink. A candidate cannot be its own measure, so on 2026-08-13 the
author re-traced ten Abb.-19 words by hand in the word editor; those rows
(`word_instances`, `provenance: "authored"`) are the reference set.

Plan, routes and the pre-registered acceptance criteria live in
`docs/proposals/tintenfolger.md`; baseline tables live in
`docs/reference/qualitaetsmetrik.md` §14.

## What this package is, and what it is not

* It **measures**. No DB, no API, no `core/` mutation, no rendering, no writes
  anywhere. Everything it reads comes from the frozen wordbench fixture roots
  (`word.json`, `crop.png`, `ref_mask.png`, `word_instances.json`).
* It **never** feeds the writing path. Nothing here changes a template, a
  Laufform, a pair override or a composition; a follower's output reaching the
  database at all is a separate PR with its own owner go.
* It is a **ruler**, so it is frozen the moment the first baseline table is
  committed. Changing a metric module after that is a dated re-baseline, not a
  bug fix (`docs/proposals/tintenfolger.md` §2.4).

## Module map

| Module | What it owns |
|---|---|
| `metric.py` | The distances: `resample_by_step`, `dtw` (the `dtw_xh` headline — unconstrained, path-length normalised, forward only), `aiou` (paper-faithful, against the ink mask), `chamfer` (both directions, unaveraged), `rasterise_strokes`. **Zero project imports** — numpy and scipy only, pinned by a test. |
| `frames.py` | The comparison frame (`BenchFrame`: crop pixels re-expressed in x-heights, derived only from the frozen entry) plus the stroke bookkeeping around it — `classify_strokes` (marks vs. body), `concat_body`, `lift_stats`, `match_marks`, and the shared `match_points` refusal contract. |
| `counters.py` | The structure counters at the hard places: `count_crossings` (over `tools.pairlab.landmarks`) and `count_retraces` (over `core.geometry.detect_retrace_pairs`), both detected on BOTH sides at one common discretisation and matched with refusal. |
| `sets.py` | `TRACEBENCH_DEV_IDS` — the ten hand-traced development words, append-never. |

## Why the frame is not the stored coordinates

Stored `(u, v)` trace coordinates are not canonical: `tx` comes from the
composer's grid search and moves when the composer moves, and the word editor
folds its `ty` into `baseline_row`. Comparing two traces in their own labels
would report registration bookkeeping as tracing error. Every path therefore
travels through its OWN registration back to crop pixels, and from there into
the frame the frozen `word.json` defines (`xh = baseline_y − midband_y`,
`baseline_row = baseline_y − rect[1]`). Two registrations describing the same
crop pixels land on identical bench points — the property the frame test pins.

## Why several numbers instead of one loss

A weight between "0.02 xh of body error" and "one missing i-dot" is a number
nobody has measured, so there is no folded `trace_loss`. `dtw_xh` is the
headline; missing marks and lost crossings are co-primary GATES that a distance
gain cannot buy back; `aiou`, both chamfer halves and `retrace_arc_ratio` are
cost watchdogs. A structure defect vetoes any distance win.

## Status

Stage B of the ladder: the measurement modules only. The harness
(`run.py`), the candidate providers (`chain`, `authored` as the identity gate,
`traced`, `file`), the split handling and the first baseline table arrive with
stage C.
