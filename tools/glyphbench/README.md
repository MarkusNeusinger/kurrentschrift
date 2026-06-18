# glyphbench — hermetic quality benchmark for the glyph pipeline

Measures how well the extraction/rendering pipeline reproduces each authored
glyph: the canonical is re-derived from the committed chart bytes + the
snapshotted raw stylus trace with the **current** code, rendered as the
capsule-union silhouette (exactly like the diagnostic/animation), and scored
against a **frozen** binarized reference of the crop. Metric internals live in
`core/quality.py`; this package only orchestrates.

## Quick start

```bash
# 1. One-time (and on explicit re-baseline): snapshot fixtures from the DB.
#    The ONLY DB access in this package — read-only SELECTs.
uv run python -m tools.glyphbench.export_fixtures

# 2. Run the bench (no DB, no HTTP — hermetic, deterministic).
#    ONE script per run: --style suetterlin (default) or --style kurrent.
uv run python -m tools.glyphbench.run --style suetterlin

# Optional: per-glyph overlay PNGs + full JSON report
uv run python -m tools.glyphbench.run --artifacts runs/dev/overlays --json runs/dev/report.json

# Optional: diff component/glyph deltas vs a previous --json report
uv run python -m tools.glyphbench.run --json runs/dev/new.json --compare runs/dev/old.json
```

Kurrent and Sütterlin use different writing instruments (Spitzfeder/Schwellzug
vs. Redisfeder/Gleichzug) and so **different quality metrics** — the bench runs
exactly one script per invocation and there is no combined `bench_loss`. Sütterlin
(`width_resolver == "constant"`) is scored by the intrinsic-naturalness metric
(`core.quality_suetterlin`); Kurrent (`pressure`) by the Schwellzug pixel/width
metric (`core.quality.template_quality_metrics`).

`fixtures/` and `runs/` are gitignored — regenerate at will.

## The frozen-reference rule

The pipeline under test recomputes **everything** per run (crop, binarize,
skeleton, snap, widths) from `chart.jpg` + `bbox.json` + `raw_path` — so
extraction-code changes show up in the numbers. The scoring target
(`ref_mask.png`, `ref_skel.npz`) is frozen at export time — so an experiment
cannot "improve" the metric by degrading the binarization and moving the
goalposts. If you believe the *reference itself* is wrong (bad binarization of
a faded stroke), stop and re-export deliberately: that is a human re-baseline,
and before/after numbers are not comparable across it.

## Fixture layout

```
fixtures/<style_id>/<source_id>/
  manifest.json            # export stamp, chart sha256, glyph index (+ updated_at
                           #  per glyph for staleness checks against the DB)
  <glyph_key>/
    template.json          # full template row (anchors, half_widths, raw_path, trace_meta, ...)
    bbox.json              # crop rect, eraser mask, baseline/midband, n_anchors, locked
    crop.png               # grayscale crop with eraser applied (overlay background)
    ref_mask.png           # FROZEN binarized scoring reference
    ref_skel.npz           # FROZEN skeleton (bool `skel`) + EDT half-width map (`width_map`)
```

Export defaults: locked glyphs only (`--include-unlocked` to widen), identical
positional fan-out copies deduped to one entry (`--no-dedupe` to keep all —
the wizard writes the same authored form across initial/medial/final).

## Output contract (parsed by the experiment loop — keep stable)

Per-glyph lines (metric-aware), then a `---` footer block:

```
# Sütterlin: per-component penalties (lower better)
glyph n-medial       loss 0.180986  smooth 0.087 vert 0.000 corner 0.089 cross 0.000 retr 0.000 cover 0.243 nat 0.058
# Kurrent: the Schwellzug line
glyph a-medial       loss 0.082653  iou 0.883  chamfer_px 0.96  geo_rmse_px 0.46  waviness 0.96
---
bench_loss:      0.209687
median_iou:      0.864800
worst_glyph:     t-final 0.277721
glyphs_scored:   60
glyphs_failed:   0
runtime_s:       4.8
--- components (mean penalty, lower better) ---   # Sütterlin only
comp_smoothness: 0.126200
comp_verticality: 0.045970
comp_corner:     0.076310
comp_collinearity: 0.194445
comp_retrace:    0.058615
comp_coverage:   0.191655
comp_naturalness: 0.120765
```

- `bench_loss` — **the headline**: mean per-glyph `loss` (lower is better); a
  glyph whose pipeline run raises counts as `1.0`, so one regressed glyph
  always moves the number. Byte-stable grep anchor: `grep "^bench_loss:" run.log`.
- The `comp_<name>:` footer lines (Sütterlin) are the mean per-component penalty
  over scored glyphs — also greppable, for tracking which category moved.
- Sütterlin `loss = 1 - score/100`, `score = 100·Tor^0.5·Natürlichkeit` (see
  `core/quality_suetterlin.py` and `docs/reference/qualitaetsmetrik.md` §5).
  Kurrent `score` weighs Dice (0.45) / chamfer (0.25) / geo-RMSE (0.20) /
  waviness (0.10) — see `core/quality.py`.

## Overlays

`--artifacts DIR` writes one PNG per glyph: crop grayscale background, the
rendered silhouette blended in red, the frozen ink boundary in blue. The
metric is a proxy; the overlays are the truth — review them before trusting
a "keep".
