"""Wordbench ruler — thin re-export of `core.word_metric`.

The implementation moved to core so the admin score endpoint can serve the
SAME frozen metric the bench runs (the deployed API image does not ship
tools/). This module keeps the historical import path for the bench, wordlab
and the tests; the freeze rule of `/optimize-glyphs` covers the core module
through this shim.
"""

from core.word_metric import (
    CHAMFER_SAT_UNITS,
    TX_RANGE_UNITS,
    TY_RANGE_PX,
    W_COVERAGE,
    W_TRANSITION,
    W_WIDTH,
    WIDTH_SAT_LOG,
    score_word,
    score_word_segments,
)


__all__ = [
    "CHAMFER_SAT_UNITS",
    "TX_RANGE_UNITS",
    "TY_RANGE_PX",
    "WIDTH_SAT_LOG",
    "W_COVERAGE",
    "W_TRANSITION",
    "W_WIDTH",
    "score_word",
    "score_word_segments",
]
