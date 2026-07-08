"""wordlab — load, compose, render and score whole words for inspection.

The word-level twin of ``tools/glyphlab``: where glyphlab shows one glyph's
ductus over its crop, wordlab shows a COMPOSED word (placement + generated
Übergänge from ``core.shaping`` + ``core.compose``) over its same-hand specimen,
with the word bench's per-connector penalty attribution drawn as callouts. It
wraps the real composer and the frozen ruler (``tools/wordbench``) — it never
re-implements composition or scoring, and it never writes to the database.

    from tools.wordlab import fixture_word_case, derive_word, word_panel
    from tools.glyphlab.render import tile, save

    res = derive_word(fixture_word_case("Einen"))
    save(tile([word_panel(res, title="Einen")], cols=1, panel_size=4.5), "einen")

CLI: ``python -m tools.wordlab Einen zu wenn-2`` (see ``--help``).
"""

from .cases import WordCase, fixture_word_case, iter_fixture_word_cases, live_word_case, live_word_case_sync
from .derive import WordDeriveResult, derive_word
from .render import word_panel


__all__ = [
    "WordCase",
    "fixture_word_case",
    "iter_fixture_word_cases",
    "live_word_case",
    "live_word_case_sync",
    "WordDeriveResult",
    "derive_word",
    "word_panel",
]
