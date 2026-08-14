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
| `reference.py` | The scored-against side: the frozen `word_instances.json` + each entry's `word.json` → one `BenchFrame`, the stored row and the lazily read ink mask per specimen. `frame_stale` and entry-less rows are excluded AND counted; the provenance filter is the caller's. |
| `candidates.py` | What is graded: `Candidate` (literally a `word_instances` row, wire-bounds validated) plus the four providers — `chain` (through the harvest's own `chain_word_strokes`), `authored` (the identity gate), `traced`, `file` (mandatory literal `"frame": "word_registration"`). A provider failure is a row, never an exception. |
| `summary.py` | The §14 columns per word (`score_word`), the run's block (`summarize`), the identity gate and the paired `compare` — whose sign test is IMPORTED from `tools.pairlab.chainbench`, never restated. |
| `run.py` | The CLI: fixture-root discovery, the frozen split with its startup assertion, the providers, `--jobs` (order-preserving), `--json`/`--csv`/`--compare`. |

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

## Running it

```
uv run python -m tools.tracebench.run --candidate chain --split dev
uv run python -m tools.tracebench.run --candidate authored          # the identity gate
uv run python -m tools.tracebench.run --candidate file --candidate-file follow.json \
    --label follow-v1 --json follow.json.report --compare chain.report
```

`--split dev` is the ten frozen words, `--split confirm` the held-out reserve
(refused under five words), `--split all` prints that a combined number is not a
held-out number. Every run starts by asserting that all ten development words
are present as `authored`, non-`frame_stale` rows — a ruler that lost a word
would report a better number for the rest.

## Status

Stage C: the harness is complete and the ruler is testable end to end. The first
BASELINE table — and with it the freeze declaration of
`docs/reference/qualitaetsmetrik.md` §14 — is written from a run over the real
fixture roots, which are gitignored and therefore never CI's business.
