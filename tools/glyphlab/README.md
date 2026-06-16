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

# the LIVE trace from the DB instead of the frozen fixture (read-only)
python -m tools.glyphlab i-initial --live --source suetterlin-1922
```

Output PNGs go to `$GLYPHLAB_OUT`, else the project `temp/` dir (git-ignored);
the path is printed. On WSL, point it at Windows to open the images directly:

```bash
export GLYPHLAB_OUT=/mnt/c/Users/<you>/Desktop/glyphlab
```

`--live` needs `DATABASE_URL`; the repo `.env` is auto-loaded. The live path
issues only SELECTs.

## Library

```python
from tools.glyphlab import fixture_case, live_case_sync, derive, overlay, montage, save

res = derive(fixture_case("i-initial"))           # production canonical + render data
save(overlay(res, title="i"), "i")                # -> temp/i.png

# A/B a change: render the same case before and after editing core/, then montage.
old = overlay(derive(case), title="alt")
new = overlay(derive(case), title="neu")          # after the edit
save(montage([("alt", old), ("neu", new)]), "ab")
```

Key pieces: `cases.py` (`GlyphCase`, fixture/live loaders), `derive.py`
(`derive`, `derive_stages` with a self-check against production), `render.py`
(`overlay`, `overlay_stage`, `montage`, `save`).
