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
| `view.py` | The duel: one self-contained HTML page per round — every method's trace over the crop beside the hand reference, toggleable, with the attached `--json` numbers and a writing-order animation (`stroke-dashoffset`, constant pen speed, pen lifts as pauses). Geometry through `BenchFrame`, bytes deterministic. |
| `chronik.py` | The create-only round history: `snapshot --label … --files …` files the artifacts of one round outside the working tree and appends one `INDEX.md` line. Never rewrites, never deletes (the `tools/dbsnapshot` discipline). |

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

## Seeing it, and keeping what was seen

```
uv run python -m tools.tracebench.view --split dev \
    --candidate chain=chain.json --candidate follow-v1=follow.json \
    --rows chain=chain.report --rows follow-v1=follow.report \
    --title "arm1-prox01 · 2026-08-14" --out temp/duell.html

uv run python -m tools.tracebench.chronik snapshot --label arm1-prox01 \
    --files temp/duell.html follow.json follow.report --note "λ_prox = λ_chain/4"
uv run python -m tools.tracebench.chronik list
```

The page opens on the FINISHED trace of every method over the plate, with the
hand re-tracing painted last so nothing can cover it; „Schreiben abspielen"
writes all switched-on methods at once in writing order. Both halves of the
question — what it looks like and how it came about — are answered on one
screen, and the chronik keeps that screen after the next round overwrites
`temp/duell.html`. Its root lies OUTSIDE the working tree (`--root` /
`KS_CHRONIK_ROOT`, else the `tracebench-chronik` sibling of the
`KURRENTSCHRIFT_ARCHIVE` clone): a round archived under `temp/` disappears with
the next `git clean -xfd`, and the pages carry traced geometry, which the
open-core reservation keeps out of the repository.

## Status

Stage C: the harness is complete and the ruler is testable end to end. The first
BASELINE table — and with it the freeze declaration of
`docs/reference/qualitaetsmetrik.md` §14 — is written from a run over the real
fixture roots, which are gitignored and therefore never CI's business.
