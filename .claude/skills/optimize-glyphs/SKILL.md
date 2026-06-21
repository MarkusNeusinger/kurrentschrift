---
name: optimize-glyphs
description: Autonomous keep/discard experiment loop on the glyph extraction/rendering pipeline — snapshot DB fixtures once, then hypothesize, edit core/, run the glyph bench, log results.tsv, keep on improvement or git-reset. Never writes to the DB. Use when asked to optimize glyph rendering, improve template quality, run the glyph bench, or start an experiment loop.
---

# Optimize the glyph pipeline (experiment loop)

Iteratively improve the extraction/rendering code in `core/` against a
fixed, fast, deterministic benchmark (`tools/glyphbench`, see its
README for fixture format and output contract). The experiment
protocol is modeled on Andrej Karpathy's autoresearch
(<https://github.com/karpathy/autoresearch>); only the workflow idea is
ported, no code was copied — this credit is attribution courtesy, not
a license obligation. The loop: one hypothesis → one
commit → one bench run → keep if the metric improved, revert if not →
loop. The bench re-derives every glyph from the committed chart bytes
+ snapshotted raw traces with the CURRENT code and scores the rendered
silhouette against FROZEN reference masks, so code changes move the
numbers but never the goalposts.

## 0 · Hard rules (read first)

- **Never touch the DB.** The loop runs only on local fixtures; the
  one-time export is the single read-only DB access; write-back to
  templates is a separate explicit admin action in the UI — never part
  of this loop.
- **Frozen during a run:** `tools/glyphbench/**`, `core/quality.py`,
  `core/quality_suetterlin.py`, `core/geometry.py`, `tests/**`. The loop
  edits only `core/pipeline.py`, `core/extract.py`, `core/template.py`,
  `core/fit.py`, `core/suetterlin.py` (the Gleichzug derivation). The
  metric lives in `core/quality.py` (Kurrent/Schwellzug) and
  `core/quality_suetterlin.py` (Sütterlin naturalness, on the shared
  `core/geometry.py` primitives) — all frozen, since editing the metric
  or a test to make a keep pass is forbidden. If a test is genuinely
  wrong, stop the loop and surface it.
- **Never on `main`.** Branch `optimize/<tag>` first.
- **Frozen-reference rule:** changes to `binarize_adaptive` etc.
  change the pipeline input but NOT the scoring target. If you believe
  the reference itself is wrong (bad binarization of a faded stroke),
  stop and flag for a human re-export — that is a re-baseline, and
  numbers across it are not comparable.
- **Sütterlin: the bench now rewards the ductus directly.** The
  naturalness metric scores smoothness, verticality, corner crispness
  and crossing collinearity, so a centerline/corner shift DOES move
  `bench_loss` (unlike the old silhouette-only Kurrent metric). Chase
  the worst component (the `comp_<name>:` footer lines, and
  `--compare prev.json` for per-glyph deltas). Still *look* though —
  `python -m tools.glyphlab <key> [--live] [--stages]` annotates each
  panel with its per-category penalty (where the points went; writes to
  `temp/`, `uv run --extra viz`) — the number says how much, the overlay
  says why. The remaining silhouette-coverage gate is still a proxy; a
  keep that looks worse is a discard.

## 1 · Setup (once per run)

```bash
git checkout -b optimize/<tag>        # e.g. optimize/jun12
# Fixtures present + fresh? manifest.json carries per-glyph updated_at;
# if missing or stale vs the DB, export ONCE (read-only):
uv run python -m tools.glyphbench.export_fixtures
mkdir -p tools/glyphbench/runs/<tag>
printf 'commit\tbench_loss\tmedian_iou\tworst_glyph\truntime_s\tstatus\tdescription\n' \
  > tools/glyphbench/runs/<tag>/results.tsv
```

Baseline first: run the bench on the unchanged code and record the
first row with status `keep` and description `baseline`.

## 2 · The loop (repeat until stopped)

1. **Hypothesize** — one concrete, falsifiable change (a constant, a
   smoothing kernel, a sampling rule). Prefer simple over clever: a
   small improvement that adds complexity is not worth it; deletions
   that hold the metric are always wins.
2. **Edit** the allowed `core/` files.
3. **Commit before running**: `git add -A && git commit -m "bench: <hypothesis>"`
   — stage everything (`-am` misses newly added files; an uncommitted
   file influencing the bench survives the discard-revert and poisons
   later runs).
4. **Run** (one script per run — `--style suetterlin` default, `--style kurrent`
   for the pressure pipeline; never both, the metrics differ):
   `uv run python -m tools.glyphbench.run --style suetterlin > tools/glyphbench/runs/<tag>/run.log 2>&1`
5. **Parse**: `grep "^bench_loss:" tools/glyphbench/runs/<tag>/run.log`
   — empty grep = crash → `tail -n 50` the log. Fix obvious typos and
   re-run (amend the commit); skip genuinely broken ideas (record
   `crash`, revert).
6. **Side gates on every keep candidate** (a lower loss never excuses
   a red gate):
   `uv run --extra test pytest && uv run --extra dev ruff check . && uv run --extra dev ruff format --check .`
   Red gate → revert, even if bench_loss improved.
7. **Record** a results.tsv row:
   `commit  bench_loss  median_iou  worst_glyph  runtime_s  status  description`
   (status: `keep` | `discard` | `crash`).
8. **Decide**: bench_loss strictly lower than the best kept row → keep
   the commit; otherwise `git reset --hard HEAD~1 && git clean -fd` —
   the clean removes untracked leftovers that would leak into the next
   iteration (gitignored paths like `runs/` and `fixtures/` are not
   touched by `clean -fd`).

Run autonomously — do not stop to ask between iterations. Stop when
the user interrupts, when ideas are exhausted (several discards in a
row across different mechanisms), or when a frozen-reference doubt
comes up (rule 0).

## 3 · Visual spot-check (every ~5 keeps)

```bash
uv run python -m tools.glyphbench.run --style suetterlin --artifacts tools/glyphbench/runs/<tag>/overlays
python -m tools.glyphlab t-medial l-medial b-medial g-medial   # annotated per-category breakdown
```

Eyeball the worst glyphs from the footer/`worst_glyph` — for Sütterlin
the loop-over-stem crossings (`l`, `b`, `g`, `h`, `f`) were largely fixed
by `_straighten_crossings` (run `jun19-suet`, bench_loss 0.2126→0.1983),
so the current weak ones are the **retrace** (`ſ`, `t` — the doubled stem's
two passes drift apart, not yet straightened) and `B`. The bench overlays show coverage;
`glyphlab` annotates each panel with its per-category penalty, so the
metric (how much) and the picture (why) agree. A keep that looks worse
than its predecessor is a discard, log it as such.

## 4 · Ending a run

- Summarize results.tsv (kept hypotheses, net bench_loss delta) and
  confirm the best commit is HEAD.
- Tuned constants whose values are justified in comments/docs must
  have the justification updated to the new value before shipping.
- Hand off to `/open-pr` — quote baseline vs final footer block in the
  PR body. `runs/` and `fixtures/` are gitignored and stay untracked.
- Write-back to the DB (refreshing stored templates with the improved
  code) happens after merge via the admin UI, per glyph — never here.

## Gotchas

- **Read bench results from the printed footer / `--compare`, not by
  indexing the run JSON.** The headline numbers are the footer lines
  the loop already greps (`bench_loss:`, `median_iou:`, `worst_glyph:`,
  `glyphs_failed:`, `runtime_s:`, `comp_<name>:`); per-glyph and
  per-component deltas come from `--compare prev.json`. Do NOT hand-roll
  `python -c "json.load(open('runs/.../x.json'))['<key>']"` to
  re-derive them — the run dict is not a pinned contract and bare key
  access throws `KeyError` (hit on `'sweep'`) when a run's shape
  differs. If you genuinely need a `--json` field, read it with
  `.get(...)` defensively; to see *why* a glyph lost points use
  `glyphlab`, not a JSON dump. (`tools/glyphbench/**` is frozen mid-run,
  so don't "fix" this by adding a footer line during a loop.)
- **The bench must be deterministic**: two runs on identical code
  produce bit-identical `bench_loss`. If they don't, your change
  introduced nondeterminism (RNG, dict ordering into geometry) — that
  is itself a bug; revert.
- **`bench_loss` is a mean** — chase the worst glyphs
  (`worst_glyph:` line), not micro-gains on already-good ones; a
  change that helps the median but regresses the worst glyph usually
  reads as no-op in the headline.
- **Runtime creep**: the footer's `runtime_s` should stay in seconds.
  An optimization that triples runtime makes the loop itself slower —
  log it in the description and weigh it.
- **One mechanism per commit.** Two coupled changes that improve
  together cannot be attributed; the next discard will throw away the
  good half too.
