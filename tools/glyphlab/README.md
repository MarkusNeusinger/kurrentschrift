# glyphlab

A small toolkit for **inspecting** glyph canonicals: load a glyph's derivation
inputs, run the real `core` pipeline, and render an overlay over its crop so you
can see whether the ductus (stroke order, corners, verticals) looks right.

It exists so checking a glyph is one command (or a few lines) instead of a fresh
throwaway script each time. It **wraps** the production derivation — it never
re-implements geometry — and it **never writes to the database**.

Not to be confused with `tools/glyphbench`, which *scores* the pipeline against
frozen references. glyphbench answers "did the number move?"; glyphlab answers
"what does it actually look like?" — and the bench is deliberately blind to
sub-pixel centerline shifts, so ductus changes must be judged here, visually.

## CLI

```bash
# final overlay (centerline + silhouette + corners) for a few fixtures
python -m tools.glyphlab i-initial u-initial n-initial

# every fixture form, anchor-dot style (what the admin Weg step shows)
python -m tools.glyphlab --all --style dots

# the derivation stages of one glyph (snap → smooth → resample → verticalize)
python -m tools.glyphlab i-initial --stages

# error map: the rendered ink (what the metric scores) vs the crop ink, zoomed
# to the tip region — gray = correct, blue = under-fill, red = over-splay. The
# title carries the under/over pixel counts. Tips render at the TOP, so --zoom-top
# FRAC keeps the top FRAC of the bbox height where centerline views hide defects.
python -m tools.glyphlab longs-final t-final --fill-diff --zoom-top 0.4

# sweep ONE module constant across values for a single glyph (one column each),
# so a tuning constant's effect is visible at a glance. The constant is patched
# in place, the glyph re-derived, then the original value always restored.
python -m tools.glyphlab longs-final --sweep core.suetterlin.RETRACE_TAPER_NIB=0.5,1.0,1.5

# the LIVE trace from the DB instead of the frozen fixture (read-only)
python -m tools.glyphlab i-initial --live --source suetterlin-1922
```

`--fill-diff` and `--zoom-top` compose with each other and with the default
centerline/silhouette overlay. `--sweep` takes exactly one glyph key and
honours `--fill-diff`/`--zoom-top` for its columns.

Output PNGs go to `$GLYPHLAB_OUT`, else the project `temp/` dir (git-ignored);
the path is printed. On WSL, point it at Windows to open the images directly:

```bash
export GLYPHLAB_OUT=/mnt/c/Users/<you>/Desktop/glyphlab
```

`--live` needs `DATABASE_URL`; the repo `.env` is auto-loaded. The live path
issues only SELECTs.

## Library

```python
from tools.glyphlab import fixture_case, derive, panel, figure, overlay, save

res = derive(fixture_case("i-initial"))           # production canonical + render data
save(overlay(res, title="i"), "i")                # one-panel figure -> temp/i.png

# Several glyphs (or variants) in one labelled grid figure:
cases = [fixture_case(k) for k in ("i-initial", "u-initial", "n-initial")]
save(figure([panel(derive(c), title=c.key) for c in cases]), "row")

# A/B a code change: render to one file, edit core/, render to another, compare.
# (Each figure() call is a grid; combine panels from both runs to see them together.)
```

Key pieces: `cases.py` (`GlyphCase`, `fixture_case` / `iter_fixture_cases` /
`live_case_sync`), `derive.py` (`derive`, `derive_stages` with a self-check
against production), `render.py` (`panel`, `figure`, `overlay`, `stage_panels`,
`save`).
