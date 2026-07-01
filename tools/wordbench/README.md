# wordbench — hermetic quality benchmark for composed words

Scores whole COMPOSED words — glyph placement + the generated Übergänge from
`core/shaping.py` + `core/compose.py` — against real connected-writing
specimens of the same hand (Sütterlin's own „Ausgangsschrift im Zusammenhang
geschrieben", Abbildung 19 of the 1922 Leitfaden; word rects + measured
lineature in `data/sources/suetterlin-1922/words.json`). The glyph bench
(`tools/glyphbench`) covers derivation quality per glyph; this bench covers
the layer above it: transitions, coupling heights, spacing rhythm. Metric
internals live in `tools/wordbench/metric.py`; the doc + baseline history in
`docs/reference/qualitaetsmetrik.md` §6.

## Quick start

```bash
# 1. One-time (and on explicit re-baseline): snapshot fixtures.
#    The ONLY DB access in this package — read-only SELECTs (template rows +
#    the pooled nib); crops/masks/skeletons come from the committed page bytes.
uv run python -m tools.wordbench.export_fixtures

# 2. Run the bench (no DB, no HTTP — hermetic, deterministic).
#    ONE script per run: --style suetterlin (default) | kurrent | offenbacher.
uv run python -m tools.wordbench.run --style suetterlin

# Optional: overlay PNGs (specimen skeleton blue, composed centerlines red) + JSON report
uv run python -m tools.wordbench.run --artifacts runs/dev/overlays --json runs/dev/report.json

# Optional: diff word deltas vs a previous --json report
uv run python -m tools.wordbench.run --json runs/dev/new.json --compare runs/dev/old.json
```

`fixtures/` and `runs/` are gitignored — regenerate at will.

## The frozen-reference rule (extends the glyph bench's)

Everything a run scores against is frozen at export: the binarized +
despeckled word mask, the skeleton + EDT width map, the SHAPED SLOTS (so a
shaping change cannot silently move the inputs), the template rows and the
pooled nib. The code under test per run is composition + rendering
(`compose_word`, `render_payload_for_template`). Registration is part of the
metric and BOUNDED (scale fixed by the measured lineature; translation
±0.6 x-heights / ±4 px, chosen by forward chamfer and reported per word) — an
experiment cannot "improve" by sliding the word around. Re-exporting fixtures
is an explicit human re-baseline; before/after numbers are not comparable
across it.

## Scoring (see metric.py for the precise definitions)

```
loss = 0.45·transition + 0.35·coverage + 0.20·width      (all ∈ [0,1], lower better)
```

- `transition` — the headline: forward chamfer of the GENERATED connector
  samples to the specimen skeleton + reverse chamfer of specimen ink inside
  the connector x-spans. Are the Übergänge where the real pen went?
- `coverage` — symmetric chamfer over all composed centerlines. Also moves
  with per-glyph authoring quality, so it gates rather than decides.
- `width` — |log| of the total-ink-width ratio: spacing/rhythm errors that
  per-point chamfer barely sees.
- A word with a missing template or a compose crash scores `1.0`.

## Output contract (parsed by the experiment loop — keep stable)

```
word wenn            loss 0.263134  trans 0.139 cover 0.287 width 0.700  (tx=12, ty=0)
---
bench_loss:      0.139663
worst_word:      wenn 0.263134
words_scored:    15
words_failed:    0
runtime_s:       0.9
--- components (mean penalty, lower better) ---
comp_transition: 0.104126
comp_coverage:   0.133415
comp_width:      0.230553
```

Byte-stable grep anchor: `grep "^bench_loss:" run.log`.

## Overlays

`--artifacts DIR` writes one PNG per word: grayscale specimen crop, specimen
skeleton in blue, composed centerlines at the fitted registration in red
(connectors bright red, glyph bodies dark red, diacritics orange). The metric
is a proxy; the overlays are the truth — review them before trusting a "keep".
