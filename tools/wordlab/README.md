# wordlab

A small toolkit for **inspecting** composed words: shape a word, render its
glyphs, lay them out with the generated Übergänge (`core.shaping` +
`core.compose`), and draw the result over its same-hand specimen — with the word
bench's per-connector penalty attribution called out — so you can see whether a
join sits where the real pen went.

It is the word-level twin of `tools/glyphlab`. glyphlab shows one glyph's ductus
over its crop; wordlab shows a whole word's placement + connectors over its
specimen. It **wraps** the production composer and the frozen ruler
(`tools/wordbench`) — it never re-implements composition or scoring — and it
**never writes to the database**.

Not to be confused with `tools/wordbench`, which *scores* composition against
frozen references. wordbench answers "did the number move?"; wordlab answers
"what does it actually look like, and which join lost the points?" The bench
number is the metric, but the overlay is the truth.

## CLI

```bash
# three words over their specimens, each connector's penalty called out
python -m tools.wordlab Einen zu wenn-2

# a letter-pair from Abb. 20 (the isolated-join set)
python -m tools.wordlab bs on --set pairs

# colour the connectors green→red by penalty instead of a flat red
python -m tools.wordlab Einen --heatmap

# join close-up: crop the view to a horizontal fraction of the crop (the
# caption margin is dropped — the zoom is about the geometry)
python -m tools.wordlab wenn kann --zoom-x 0.35,0.95 --no-callouts

# every word of the set, one per row (filter with ids)
python -m tools.wordlab --all

# sweep ONE compose constant across values for a single word (one column each),
# so a tuning constant's effect on the joins is visible at a glance. The
# constant is patched in place, the word re-composed, then always restored.
python -m tools.wordlab Einen --sweep core.compose.INK_CLEARANCE=0.10,0.14,0.18

# compose LIVE from the DB (read-only) — any text, one letter is fine; there is
# no specimen to overlay, so it draws the ductus on white in composed units.
python -m tools.wordlab "unser Haus" --live --source suetterlin-1922
python -m tools.wordlab e --live
```

`--sweep` takes exactly one word id and honours `--heatmap`/`--no-callouts`.
`--live` needs `DATABASE_URL`; the repo `.env` is auto-loaded. The live path
issues only SELECTs.

Word crops are wide (~5:1), so a montage stacks more than two words in a single
column (each gets the full panel width); one or two sit side by side, and a
`--sweep` uses one column per swept value. Override with `--cols`.

Output PNGs go to `$WORDLAB_OUT`, else the project `temp/` dir (git-ignored);
the path is printed. On WSL, point it at Windows to open the images directly:

```bash
export WORDLAB_OUT=/mnt/c/Users/<you>/Desktop/wordlab
```

## Colour legend

- **blue** — the specimen skeleton (where the real pen went)
- **bright red** — a generated connector (Übergang)
- **dark red** — a glyph body stroke
- **orange** — a deferred floating mark (i-/j-dot, umlaut, u-bow)
- pink/green hairlines — the baseline / midband guides
- callout `a→b 0.81` — this join's transition penalty (arrow tinted green→red)
- right margin — loss + trans/cover/width and the worst segments

Same scheme as the word-bench overlay (`tools/wordbench/run.py`), so a wordlab
picture and a bench artifact read identically.

## Library

```python
from tools.wordlab import fixture_word_case, derive_word, word_panel
from tools.glyphlab.render import tile, save

res = derive_word(fixture_word_case("Einen"))     # compose + score against the specimen
save(tile([word_panel(res, title="Einen")], cols=1, panel_size=4.5), "einen")

# Several words in one grid, or a heatmap variant:
cases = [fixture_word_case(i) for i in ("Einen", "zu", "wenn-2")]
draws = [word_panel(derive_word(c), heatmap=True) for c in cases]
save(tile(draws, cols=1, panel_size=4.5), "worst")
```

Fixtures come from `tools/wordbench/export_fixtures` (the same frozen snapshot
the bench scores); they are gitignored, so regenerate them locally with
`uv run python -m tools.wordbench.export_fixtures --set all`.

Key pieces: `cases.py` (`WordCase`, `fixture_word_case` /
`iter_fixture_word_cases` / `live_word_case_sync`), `derive.py` (`derive_word` —
compose with provenance + score with the frozen ruler), `render.py`
(`word_panel`; the grid `tile` / `save` are reused from glyphlab).
