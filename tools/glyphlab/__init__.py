"""glyphlab — load, derive, render and compare glyph canonicals for inspection.

A small reusable toolkit so checking "does this glyph's ductus look right?" is a
few lines (or one CLI call) instead of a throwaway script every time. It wraps
the real `core` derivation; it never re-implements geometry and never writes to
the database.

    from tools.glyphlab import fixture_case, derive, overlay, save

    res = derive(fixture_case("i-initial"))
    save(overlay(res, title="i"), "i")

CLI: ``python -m tools.glyphlab i-initial u-initial`` (see ``--help``).
"""

from .cases import GlyphCase, fixture_case, iter_fixture_cases, live_case, live_case_sync
from .derive import DeriveResult, Stage, derive, derive_stages
from .render import GREEN, RED, Panel, figure, overlay, panel, save, stage_panels


__all__ = [
    "GlyphCase",
    "fixture_case",
    "iter_fixture_cases",
    "live_case",
    "live_case_sync",
    "DeriveResult",
    "Stage",
    "derive",
    "derive_stages",
    "Panel",
    "panel",
    "figure",
    "overlay",
    "stage_panels",
    "save",
    "GREEN",
    "RED",
]
