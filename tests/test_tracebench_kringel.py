"""Tests for the Kringel landmark (`tools.tracebench.kringel`).

The catalogue itself is measured on a frozen root and cannot be built in a
unit test, so what is pinned here is everything the catalogue is READ with: the
two classification rules, the raster loop finder on synthetic loops whose
aperture is known in closed form, the slot grouping that decides which strokes
a letter's loops are measured on, and the report contract — `punkt` exempt,
`wechselnd` counted apart, a missing catalogue a warning rather than a failure.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from tools.tracebench.kringel import (
    PLATE_PEN_WIDTH_UNITS,
    SIZE_CLASSES,
    SIZE_MEDIUM_MAX_UNITS,
    SIZE_SMALL_MAX_UNITS,
    SPLITTER_FLOOR_UNITS,
    STATES,
    UNATTESTED,
    kringel_by_word,
    kringel_row_fields,
    load_catalogue,
    loop_apertures,
    loop_state,
    size_class,
    slot_loop_lines,
    word_kringel,
)


def _circle(radius: float, *, cx: float = 0.0, cy: float = 0.0, n: int = 720) -> list[list[float]]:
    """A closed polygon whose inscribed diameter is `2 * radius` to O(1/n^2)."""
    pts = [[cx + radius * math.cos(2 * math.pi * i / n), cy + radius * math.sin(2 * math.pi * i / n)] for i in range(n)]
    return [*pts, pts[0]]


# ---------------------------------------------------------------- the two rules


def test_the_size_classes_are_counted_in_widths_of_the_plate_pen() -> None:
    # The cuts are 2 and 4 pen widths; they are a property of the instrument,
    # not of the sample, and moving them would reclassify the whole catalogue.
    assert SIZE_SMALL_MAX_UNITS == pytest.approx(2 * PLATE_PEN_WIDTH_UNITS)
    assert SIZE_MEDIUM_MAX_UNITS == pytest.approx(4 * PLATE_PEN_WIDTH_UNITS)
    assert size_class(0.0) == "klein"
    assert size_class(SIZE_SMALL_MAX_UNITS - 1e-9) == "klein"
    assert size_class(SIZE_SMALL_MAX_UNITS) == "mittel"
    assert size_class(SIZE_MEDIUM_MAX_UNITS - 1e-9) == "mittel"
    assert size_class(SIZE_MEDIUM_MAX_UNITS) == "gross"
    assert size_class(3.0) == "gross"


def test_the_state_reads_only_how_often_the_plate_holds_the_loop_open() -> None:
    assert loop_state(10, 10) == "offen"
    assert loop_state(10, 8) == "offen"  # exactly the majority is still offen
    assert loop_state(10, 7) == "wechselnd"
    assert loop_state(10, 3) == "wechselnd"
    assert loop_state(10, 2) == "punkt"  # a Punktkringel: the plate never opens it
    assert loop_state(10, 0) == "punkt"
    assert loop_state(1, 1) == "offen"
    assert loop_state(1, 0) == "punkt"


def test_the_state_refuses_an_empty_population() -> None:
    with pytest.raises(ValueError):
        loop_state(0, 0)


# ------------------------------------------------------- the raster loop finder


def test_a_circle_reports_its_own_diameter() -> None:
    loops = loop_apertures([_circle(0.25)])
    assert len(loops) == 1
    assert loops[0].d0 == pytest.approx(0.5, abs=0.005)
    assert loops[0].cx == pytest.approx(0.0, abs=0.01)


def test_an_open_curve_encloses_nothing() -> None:
    assert loop_apertures([[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]]) == []


def test_loops_come_back_in_reading_order() -> None:
    loops = loop_apertures([_circle(0.2, cx=1.0), _circle(0.3, cx=0.0)])
    assert [round(lp.cx) for lp in loops] == [0, 1]
    assert loops[0].d0 == pytest.approx(0.6, abs=0.005)
    assert loops[1].d0 == pytest.approx(0.4, abs=0.005)


def test_a_loop_under_the_splinter_floor_is_dropped() -> None:
    small = SPLITTER_FLOOR_UNITS / 4
    assert loop_apertures([_circle(small)]) == []
    assert len(loop_apertures([_circle(small)], floor=0.0)) == 1


def test_the_ink_aperture_is_the_erosion_by_the_half_width() -> None:
    loop = loop_apertures([_circle(0.25)])[0]
    assert loop.ink_aperture(0.1) == pytest.approx(loop.d0 - 0.2)
    # A pen wider than the loop runs it shut, and the sensor sees a negative.
    assert loop.ink_aperture(0.4) < 0.0


# --------------------------------------------------------------- slot grouping


def _item(points: list[list[float]], *, slot: int | None = None, key: str | None = None) -> dict[str, object]:
    out: dict[str, object] = {"centerline": points, "slot_index": slot}
    if key is not None:
        out["glyph_key"] = key
    return out


def test_a_slot_is_read_with_the_connector_on_each_side() -> None:
    items = [
        _item([[0.0, 0.0], [0.5, 0.0]]),  # leading connector
        _item([[0.5, 0.0], [1.0, 0.0]], slot=0, key="e"),
        _item([[1.0, 0.0], [1.5, 0.0]]),  # connector between 0 and 1
        _item([[1.5, 0.0], [2.0, 0.0]], slot=1, key="r"),
    ]
    grouped = slot_loop_lines(items)
    assert grouped[0][0] == "e"
    assert len(grouped[0][1]) == 3  # the letter plus both connectors
    assert len(grouped[1][1]) == 2  # the letter plus the connector before it


def test_a_foreign_letter_is_never_dragged_into_a_slot() -> None:
    items = [_item([[0.0, 0.0], [1.0, 0.0]], slot=0, key="a"), _item([[1.0, 0.0], [2.0, 0.0]], slot=1, key="o")]
    grouped = slot_loop_lines(items)
    assert len(grouped[0][1]) == 1
    assert len(grouped[1][1]) == 1


# ------------------------------------------------------------ the report fields

_CATALOGUE = {
    "o": [{"glyph": "o", "loop": 0, "size_class": "klein", "state": "offen"}],
    "g": [{"glyph": "g", "loop": 0, "size_class": "klein", "state": "wechselnd"}],
    "n": [{"glyph": "n", "loop": 0, "size_class": "klein", "state": "punkt"}],
}


def _word(keys: list[str], radius: float) -> list[dict[str, object]]:
    return [_item(_circle(radius, cx=2.0 * i), slot=i, key=key) for i, key in enumerate(keys)]


def test_an_offen_loop_that_runs_shut_is_the_only_thing_counted_as_lost() -> None:
    # radius 0.15 -> D0 0.30, so a half width of 0.2 closes every loop.
    fields = kringel_row_fields(_word(["o", "g", "n"], 0.15), _CATALOGUE, 0.2)
    assert fields["kringel_loops"] == 3
    assert fields["kringel_offen"] == 1
    assert fields["kringel_lost"] == 1
    assert fields["kringel_lost_at"] == "o#0"
    assert fields["kringel_wechselnd_zu"] == 1  # counted, never a loss
    assert fields["kringel_punkt"] == 1  # exempt by construction
    assert fields["kringel_unbekannt"] == 0


def test_a_pen_the_loops_survive_loses_nothing() -> None:
    fields = kringel_row_fields(_word(["o", "g", "n"], 0.15), _CATALOGUE, 0.05)
    assert fields["kringel_offen"] == 1
    assert fields["kringel_lost"] == 0
    assert fields["kringel_wechselnd_zu"] == 0
    assert fields["kringel_lost_at"] == ""


def test_a_punkt_loop_never_carries_a_verdict() -> None:
    rows = word_kringel(_word(["n"], 0.15), _CATALOGUE, 0.2)
    assert [r["state"] for r in rows] == ["punkt"]
    assert rows[0]["honoured"] is None


def test_a_glyph_the_catalogue_does_not_know_is_counted_apart() -> None:
    fields = kringel_row_fields(_word(["x"], 0.15), _CATALOGUE, 0.2)
    assert fields["kringel_unbekannt"] == 1
    assert fields["kringel_offen"] == 0
    assert fields["kringel_lost"] == 0


# ----------------------------------------------------------- catalogue loading


def test_the_catalogue_loads_in_loop_order(tmp_path: Path) -> None:
    path = tmp_path / "cat.json"
    path.write_text(
        json.dumps(
            {
                "loops": [
                    {"glyph": "a", "loop": 1, "size_class": "mittel", "state": "offen"},
                    {"glyph": "a", "loop": 0, "size_class": "klein", "state": "punkt"},
                ]
            }
        )
    )
    assert [row["loop"] for row in load_catalogue(path)["a"]] == [0, 1]


def test_a_catalogue_with_a_hole_in_its_loop_numbering_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "cat.json"
    path.write_text(json.dumps({"loops": [{"glyph": "a", "loop": 1, "size_class": "klein", "state": "offen"}]}))
    with pytest.raises(ValueError):
        load_catalogue(path)


def test_a_word_outside_the_vocabulary_is_refused(tmp_path: Path) -> None:
    # An unknown state would read as "no expectation" — indistinguishable from a
    # Punktkringel, and a whole class of loops would go unwatched.
    path = tmp_path / "cat.json"
    path.write_text(json.dumps({"loops": [{"glyph": "a", "loop": 0, "size_class": "klein", "state": "halboffen"}]}))
    with pytest.raises(ValueError, match="state"):
        load_catalogue(path)
    path.write_text(json.dumps({"loops": [{"glyph": "a", "loop": 0, "size_class": "winzig", "state": "offen"}]}))
    with pytest.raises(ValueError, match="size class"):
        load_catalogue(path)


def test_a_missing_catalogue_degrades_to_a_warning(tmp_path: Path) -> None:
    out, warnings = kringel_by_word(
        ["die"],
        which="words",
        style="suetterlin",
        fixtures_root=tmp_path,
        half_width=0.097,
        catalogue_path=tmp_path / "nope.json",
    )
    assert out == {}
    assert len(warnings) == 1
    assert "Kringel-Landmarke" in warnings[0]


def test_a_root_without_cases_degrades_to_a_warning(tmp_path: Path) -> None:
    out, warnings = kringel_by_word(
        ["die"], which="words", style="suetterlin", fixtures_root=tmp_path, half_width=0.097
    )
    assert out == {}
    assert len(warnings) == 1
    assert "Kringel-Landmarke" in warnings[0]


def test_the_shipped_catalogue_is_readable_and_uses_the_declared_vocabulary() -> None:
    catalogue = load_catalogue()
    assert catalogue, "the frozen catalogue must ship with the sensor"
    for glyph, loops in catalogue.items():
        for row in loops:
            assert row["size_class"] in {*SIZE_CLASSES, UNATTESTED}, glyph
            assert row["state"] in {*STATES, UNATTESTED}, glyph
            # Reserved dataset: apertures and classes only, never geometry.
            assert "anchors" not in row and "centerline" not in row, glyph
