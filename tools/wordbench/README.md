# wordbench — hermetic quality benchmark for composed words

Scores whole COMPOSED words — glyph placement + the generated Übergänge from
`core/shaping.py` + `core/compose.py` — against real connected-writing
specimens of the same hand: all 63 words of Sütterlin's „Ausgangsschrift im
Zusammenhang geschrieben" (Abbildung 19 of the 1922 Leitfaden) plus, as a
SEPARATE set with its own headline, the 33 isolated letter-pair joins of
Abbildung 20 („nicht selbstverständliche Buchstabenverbindungen" — ground
truth for exactly the transitions the composer generates). Word/pair rects +
measured lineature live in `data/sources/suetterlin-1922/words.json` (boxes
proposed by `tools/wordbench/propose_boxes.py`, verified visually per line).
The glyph bench (`tools/glyphbench`) covers derivation quality per glyph;
this bench covers the layer above it: transitions, coupling heights, spacing
rhythm. Metric internals live in `core/word_metric.py` (moved there so the
admin score endpoint serves the SAME frozen ruler — the deployed API image
ships no `tools/`); `tools/wordbench/metric.py` remains the bench's import
path as a re-export shim. Doc + baseline history in
`docs/reference/qualitaetsmetrik.md` §6.

## Quick start

```bash
# 1. One-time (and on explicit re-baseline): snapshot fixtures.
#    The ONLY DB access in this package — read-only SELECTs (template rows +
#    the pooled nib); crops/masks/skeletons come from the committed page bytes.
#    --set words|pairs|all — words and pairs freeze into SIBLING fixture
#    roots (suetterlin-1922 / suetterlin-1922-pairs), so exporting one never
#    regenerates the other.
uv run python -m tools.wordbench.export_fixtures --set all

# 2. Run the bench (no DB, no HTTP — hermetic, deterministic).
#    ONE script per run: --style suetterlin (default) | kurrent | offenbacher.
#    --set words (default) | pairs | all — pairs report their own pair_loss,
#    the two headlines are never averaged.
uv run python -m tools.wordbench.run --style suetterlin
uv run python -m tools.wordbench.run --style suetterlin --set pairs

# Optional: overlay PNGs (specimen skeleton blue, composed centerlines red) + JSON report
uv run python -m tools.wordbench.run --artifacts runs/dev/overlays --json runs/dev/report.json

# Optional: diff word deltas vs a previous --json report
uv run python -m tools.wordbench.run --json runs/dev/new.json --compare runs/dev/old.json

# Optional: compose with pair overrides from a harvest file (redesign R3).
# An override run is its OWN measurement, never comparable to the headline.
uv run python -m tools.wordbench.run --set pairs --overrides temp/pair_harvest.json

# Box proposal / verification sheets for annotating a new plate (no DB):
uv run python -m tools.wordbench.propose_boxes --page words-abb19.png --expect-lines 12 --strips
uv run python -m tools.wordbench.propose_boxes --page words-abb19.png --expect-lines 12 --validate
uv run python -m tools.wordbench.propose_boxes --page pairs-abb20.png --expect-lines 4 --from-sidecar
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

Each scored row also reports `slant <specimen>/<composed>` (redesign R5:
shear-search estimator in `slant.py`, 90 = upright, < 90 = right-leaning),
plus per-block medians — report-only diagnostics, never part of the loss.
- `width` — |log| of the total-ink-width ratio: spacing/rhythm errors that
  per-point chamfer barely sees. For PAIRS this component carries a constant
  positive bias (the plate draws lead-in/lead-out strokes the composed
  isolated pair lacks) — treat `transition` as the pairs signal.
- A word whose composition crashes scores `1.0`. An entry whose template is
  simply NOT AUTHORED yet is frozen `scorable: false` at export and the
  runner SKIPS and reports it by id (`words_skipped_ids:`) — an authoring gap
  must not drown the composition headline, but stays visible.
- Entries are keyed by `id` (unique; repeated plate words carry `-2`/`-3`
  suffixes, e.g. `muß`/`muß-2`/`muß-3`), display keeps the word text.

## Output contract (parsed by the experiment loop — keep stable)

```
word wenn            loss 0.202180  trans 0.148 cover 0.176 width 0.370  (tx=22, ty=1)
---
bench_loss:      0.184426
worst_word:      Einen 0.531559
words_scored:    48
words_skipped:   15
words_failed:    0
words_skipped_ids: Wer,Soldaten,muß,…
--- components (mean penalty, lower better) ---
comp_transition: 0.166240
comp_coverage: 0.185325
comp_width: 0.223770
```

Byte-stable grep anchor: `grep "^bench_loss:" run.log`. The pairs block
(`--set pairs`/`all`) mirrors it with `pair_loss:`, `worst_pair:`,
`pairs_scored/skipped/failed`, `pairs_skipped_ids:` and `pair_comp_*` lines.

## Overlays

`--artifacts DIR` writes one PNG per word: grayscale specimen crop, specimen
skeleton in blue, composed centerlines at the fitted registration in red
(connectors bright red, glyph bodies dark red, diacritics orange). The metric
is a proxy; the overlays are the truth — review them before trusting a "keep".
