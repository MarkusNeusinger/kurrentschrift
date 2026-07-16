---
name: verify-core
description: Test and smoke-run the pure-Python compute layer in core/ — run pytest, run ruff lint/format the way CI does, and call the extraction pipeline directly on a synthetic chart without DB or HTTP. Use when asked to run, test, lint, or verify core/, the pipeline, extraction, template, or fit code.
---

# Verify the core compute layer

`core/` is pure Python (extract → template → pipeline → fit), no DB,
no HTTP. Most PRs here touch one function — the right harness is
direct invocation plus the unit tests, not the running app. All paths
relative to the repo root.

## 1 · Tests (what CI gates)

```bash
uv run --extra test pytest
```

(`--extra test` makes this work on a fresh venv too — pytest and its
async deps live in the `test` extra; in an already-synced checkout
plain `uv run pytest` happens to work.)

Expected: all pass (~350 tests across ~30 modules in well under a
minute; a handful of tool-fixture tests skip when the local-only bench
fixtures are absent — normal). Check "all pass", not an exact count —
the suite grows continuously. The fixtures in `tests/conftest.py` are synthetic (an
800×800 chart with a vertical bar) — no real data, DB, or network is
touched, so pytest is always safe to run.

Lint + format — the same checks CI gates (CI syncs
`--extra dev --extra test --frozen` first and then calls ruff
plainly); locally, route through `--extra dev` so it also works on a
fresh venv:

```bash
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
```

## 2 · Direct invocation (agent path for single-function changes)

The pipeline entry point runs end-to-end on a synthetic chart with no
infrastructure. This heredoc is the smoke harness — adapt the bbox /
`raw_path` to exercise whatever you changed:

```bash
uv run python - <<'EOF'
"""Smoke: dense stylus path -> canonical template dict, no DB/HTTP."""
import numpy as np
from PIL import Image

from core.pipeline import canonical_from_path

# Synthetic 800x800 chart with a 16px-wide vertical bar (like tests/conftest.py)
img = np.full((800, 800), 255, dtype=np.uint8)
img[200:600, 392:408] = 12
Image.fromarray(img, mode="L").save("/tmp/kurrentschrift-smoke-chart.png")

bbox = {"y0": 100, "y1": 700, "x0": 300, "x1": 500, "mask_strokes": [],
        "baseline_y": 600, "midband_y": 500}
raw_path = [{"x": 400.0, "y": float(y)} for y in range(200, 601, 10)]  # downstroke

tpl = canonical_from_path(raw_path, bbox, "/tmp/kurrentschrift-smoke-chart.png",
                          glyph="l", position="medial")
print("keys:", sorted(tpl.keys()))
print("n anchors:", len(tpl["anchors"]), "| slant:", round(tpl["measurements"]["slant_deg"], 1),
      "| mean half-width (template units):", round(float(np.mean(tpl["half_widths"])), 3))
EOF
```

Verified output: keys `['advance', 'anchors', 'entry', 'exit_pt',
'glyph', 'half_widths', 'measurements', 'position', 'raw_path',
'trace_meta']`, 120 anchors (DEFAULT_N_ANCHORS, bench-calibrated),
slant `0.0` for the vertical bar, mean half-width ≈ `0.08` template
units — physically sensible: the bar is 16 px wide (8 px half-width)
and the baseline→midband unit is 100 px.

Sanity-check changed numerics the same way: pick an input whose
expected value you can compute by hand (vertical bar → slant 0,
half-width = bar/2 ÷ unit), not just "it didn't crash".

To check against **real** data instead of synthetic, don't reach for
the DB from Python — the running API already wires DB + chart + core
together; use the `verify-api` skill's `/diagnostic` and `/fit`
endpoints.

## Gotchas

- **One synthetic chart is not a crash sweep.** pytest + the §2 smoke
  run a single clean vertical bar; a per-glyph crash that only real
  geometry triggers (e.g. `CubicSpline: x must be strictly increasing`
  from coincident/non-monotonic anchors on a jagged skeleton — hit on
  `t` initial/medial/final) sails through both and reaches prod, where
  it is NOT swallowed. The glyph bench re-derives every real glyph, so
  it is the crash net: when a change touches `core/extract.py`,
  `core/template.py`, `core/suetterlin.py`, `core/fit.py` or the
  resampling, run it and read the **failure count, not the headline
  loss** — `uv run python -m tools.glyphbench.run --style suetterlin`
  (and `--style kurrent`), then check the printed `glyphs_failed:` line
  (must be `0`) and `worst_glyph:` (a glyph pinned at loss `1.000000`
  is a crash, not a bad score). The bench catches per-glyph exceptions
  and scores them `1.0`, so `bench_loss` stays populated and **there is
  no stdout Traceback** — re-run with `--json /tmp/bench.json` and read
  the crashing glyph's `error` field to see it. The bench reads
  pre-exported fixtures from disk (no live DB/HTTP at run time); a fresh
  checkout needs the one-time read-only
  `uv run python -m tools.glyphbench.export_fixtures` first.
- **Plain `uv run ruff` fails on a fresh venv** with
  `Failed to spawn: ruff` — ruff lives in the `dev` extra, not the
  default deps. After any `--extra dev` sync it silently works (the
  inexact `uv run` sync never prunes it), so the plain form is
  environment-dependent; write `uv run --extra dev ruff …` to be
  deterministic.
- **Template coords convention** (for interpreting smoke output):
  baseline = 0, midband = 1, y grows upward; pixel unit is
  `baseline_y - midband_y` from the bbox.
- **Pen lifts are sacred**: `raw_path` may contain `pen_up` markers;
  resampling is per-stroke (`stroke_starts` in `trace_meta`) and must
  never bridge a lift — if your change touches resampling, add a
  two-stroke path to the smoke and check `stroke_starts` has 2 entries.

## Troubleshooting

- Ruff "Failed to spawn" → use `uv run --extra dev ruff …` (see
  Gotchas).
