"""Tests for the shared ductus target (`tools.tracebench.soll`).

The real computation runs over the frozen fixture cases and the compose stack,
so what a unit test can pin is the contract around it: a root without
composition data degrades to a warning instead of a failure, and the flat
report fields are exactly the Soll pair, letters and composition apart.
"""

from __future__ import annotations

from pathlib import Path

from tools.tracebench.soll import SollRow, ductus_soll, soll_row_fields


def test_a_root_without_cases_degrades_to_a_warning(tmp_path: Path) -> None:
    out, warnings = ductus_soll(["die"], which="words", style="suetterlin", fixtures_root=tmp_path)
    assert out == {}
    assert len(warnings) == 1
    assert "Duktus-Soll" in warnings[0]


def test_soll_row_fields_keep_letters_and_composition_apart() -> None:
    letters = SollRow(label="Σ", strokes=None, crossings=3, zones=1, touches=2, overlaps=0)
    comp = SollRow(label="Komp", strokes=2, crossings=4, zones=2, touches=1, overlaps=1)
    assert soll_row_fields((letters, comp)) == {
        "soll_cross_letters": 3,
        "soll_zones_letters": 1,
        "soll_cross": 4,
        "soll_zones": 2,
        "soll_touch": 1,
        "soll_overlap": 1,
    }
