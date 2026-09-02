"""Unit tests for the seam-angle report column (tools/wordbench/seam.py).

Synthetic joins whose turn angles are known by construction — a straight pen
path turns 0°, a 30° kink reads 30° — so a geometry or numpy change cannot
silently redefine what ``seam_deg`` means. The column is report-only; pinning
it matters because a class rule (the "Austritts-Kollinearität" arm) is meant
to be judged by the number it moves.

Sign convention under test, once for both ends: the turn is always OUTGOING
minus INCOMING in travel order, so a positive value means the pen turns
counter-clockwise at the seam.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from core.compose import CONNECT_OVERLAP, _overlap_extend
from core.shaping import GlyphSlot
from tools.wordbench.seam import SEAM_WINDOW, direction_deg, seam_angles, strip_overlap


def _slots(*keys: str) -> list[GlyphSlot]:
    return [GlyphSlot(key=k, text=k, position=None, ligature=False, space=False) for k in keys]


def _ray(start: tuple[float, float], deg: float, length: float, n: int = 12) -> list[list[float]]:
    """A straight polyline of ``n`` segments from ``start`` heading ``deg``."""
    dx, dy = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [[start[0] + dx * length * i / n, start[1] + dy * length * i / n] for i in range(n + 1)]


def _tip(start: tuple[float, float], deg: float, length: float) -> tuple[float, float]:
    return (start[0] + math.cos(math.radians(deg)) * length, start[1] + math.sin(math.radians(deg)) * length)


def _composed(left: list, connector: list, right: list, **extra) -> dict:
    """A minimal provenance-tagged composition: body stroke, connector, body stroke."""
    item = {"centerline": connector, "pair": ["a", "b"], "from_slot": 0, "to_slot": 1, "exit": list(connector[0])}
    item.update(extra)
    return {"items": [{"slot_index": 0, "centerline": left}, item, {"slot_index": 1, "centerline": right}]}


def test_a_straight_pen_path_has_no_seam():
    # Letter, connector and letter all run along +x: nothing turns anywhere.
    composed = _composed(_ray((-1.0, 0.0), 0.0, 1.0), _ray((0.0, 0.0), 0.0, 1.0), _ray((1.0, 0.0), 0.0, 1.0))

    result = seam_angles(composed, _slots("a", "b"))

    assert (result["n_joins"], result["n_matched"], result["excluded_retrace"]) == (1, 1, 0)
    assert result["joins"][0]["pair"] == ["a", "b"]
    assert result["joins"][0]["dep_deg"] == pytest.approx(0.0, abs=1e-6)
    assert result["joins"][0]["arr_deg"] == pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize("kink", [30.0, -30.0])
def test_a_kink_at_the_departure_reads_as_that_angle(kink: float):
    # The letter ends running along +x, the connector leaves at `kink`. The
    # right letter continues the connector's own heading, so ONLY the
    # departure turns and the arrival has to stay 0.
    composed = _composed(
        _ray((-1.0, 0.0), 0.0, 1.0), _ray((0.0, 0.0), kink, 1.0), _ray(_tip((0.0, 0.0), kink, 1.0), kink, 1.0)
    )

    join = seam_angles(composed, _slots("a", "b"))["joins"][0]

    assert join["dep_deg"] == pytest.approx(kink, abs=0.01)
    assert join["arr_deg"] == pytest.approx(0.0, abs=0.01)


@pytest.mark.parametrize("kink", [30.0, -30.0])
def test_a_kink_at_the_arrival_reads_as_that_angle(kink: float):
    # Mirror case: the connector runs into the letter along +x and the letter
    # starts off at `kink` — outgoing minus incoming again.
    composed = _composed(_ray((-1.0, 0.0), 0.0, 1.0), _ray((0.0, 0.0), 0.0, 1.0), _ray((1.0, 0.0), kink, 1.0))

    join = seam_angles(composed, _slots("a", "b"))["joins"][0]

    assert join["dep_deg"] == pytest.approx(0.0, abs=0.01)
    assert join["arr_deg"] == pytest.approx(kink, abs=0.01)


def test_the_turn_is_wrapped_into_the_half_turn_band():
    # A reversal (the ſ/w/r loop and descender turnarounds) must read as ±180,
    # never as the 300° an unwrapped subtraction would produce.
    composed = _composed(_ray((0.0, 0.0), -170.0, 1.0), _ray((0.0, 0.0), 10.0, 1.0), _ray((1.0, 0.0), 10.0, 1.0))

    join = seam_angles(composed, _slots("a", "b"))["joins"][0]

    assert abs(join["dep_deg"]) == pytest.approx(180.0, abs=0.01)


def test_the_direction_is_read_over_one_seam_window_of_arc():
    assert SEAM_WINDOW == 0.05
    # A bend BEYOND the window is invisible …
    assert direction_deg([[0.0, 0.0], [0.06, 0.0], [0.06, 1.0]], at_end=False) == pytest.approx(0.0, abs=1e-9)
    # … a bend INSIDE it is not: the window reaches the sample past the corner.
    assert direction_deg([[0.0, 0.0], [0.04, 0.0], [0.04, 1.0]], at_end=False) == pytest.approx(87.71, abs=0.01)
    # Same walk from the far end, in travel order.
    assert direction_deg([[0.0, 1.0], [0.0, 0.06], [1.0, 0.06]], at_end=True) == pytest.approx(0.0, abs=1e-9)
    # A polyline shorter than the window contributes its whole length.
    assert direction_deg([[0.0, 0.0], [0.01, 0.01]], at_end=False) == pytest.approx(45.0, abs=1e-9)
    # Degenerate input is None, never an exception.
    assert direction_deg([[0.0, 0.0]], at_end=False) is None
    assert direction_deg([[0.0, 0.0], [0.0, 0.0]], at_end=True) is None


def test_the_overlap_tuck_is_removed_before_measuring():
    # _overlap_extend is what the composer emits; strip_overlap is its inverse.
    line = _ray((0.0, 0.0), 20.0, 1.0)
    extended = _overlap_extend([tuple(p) for p in line])

    assert len(extended) == len(line) + 2
    assert math.dist(extended[0], extended[1]) == pytest.approx(CONNECT_OVERLAP)
    assert np.allclose(strip_overlap(extended), line)
    # A line the composer never extended keeps every sample.
    assert np.allclose(strip_overlap(line), line)


def test_a_capital_retrace_join_is_excluded_and_counted():
    # The composer prefixes a capital's ornament retrace onto the connector
    # item, so the stated `exit` is no longer the item's first sample. Such a
    # "departure" is a designed turnaround, not a seam.
    composed = _composed(
        _ray((-1.0, 0.0), 0.0, 1.0), _ray((-0.5, 0.0), 0.0, 1.5), _ray((1.0, 0.0), 0.0, 1.0), exit=[0.0, 0.0]
    )

    result = seam_angles(composed, _slots("a", "b"))

    assert (result["n_joins"], result["n_matched"], result["excluded_retrace"]) == (1, 0, 1)
    assert result["dep_median"] is None and result["arr_median"] is None


def test_diacritics_and_the_endstrich_are_not_part_of_a_seam():
    composed = _composed(
        _ray((-1.0, 0.0), 0.0, 1.0), _ray((0.0, 0.0), 30.0, 1.0), _ray(_tip((0.0, 0.0), 30.0, 1.0), 30.0, 1.0)
    )
    # An i-dot on the left slot must not become "the letter's last stroke",
    # and the word-final Endstrich (pair[1] is None) is not a join at all.
    composed["items"].append({"slot_index": 0, "centerline": _ray((-0.5, 2.0), 0.0, 0.1), "diacritic": True})
    composed["items"].append({"centerline": _ray((2.0, 0.0), 0.0, 0.5), "pair": ["b", None], "from_slot": 1})

    result = seam_angles(composed, _slots("a", "b"))

    assert result["n_joins"] == 1
    assert result["joins"][0]["dep_deg"] == pytest.approx(30.0, abs=0.01)


def test_a_composition_without_provenance_bodies_matches_nothing():
    composed = {
        "items": [
            {"centerline": _ray((-1.0, 0.0), 0.0, 1.0)},
            {"centerline": _ray((0.0, 0.0), 30.0, 1.0), "pair": ["a", "b"], "from_slot": 0, "to_slot": 1},
            {"centerline": _ray((1.0, 0.0), 0.0, 1.0)},
        ]
    }

    result = seam_angles(composed, _slots("a", "b"))

    assert (result["n_joins"], result["n_matched"]) == (1, 0)
    assert result["arr_median"] is None


def test_a_degenerate_connector_is_skipped_without_crashing():
    composed = _composed(_ray((-1.0, 0.0), 0.0, 1.0), [[0.0, 0.0], [0.0, 0.0]], _ray((1.0, 0.0), 0.0, 1.0))

    result = seam_angles(composed, _slots("a", "b"))

    assert (result["n_joins"], result["n_matched"]) == (1, 0)


def test_the_per_entry_medians_are_signed():
    # Two joins departing +20° and -20°: the signed median is 0. An accidental
    # abs() aggregation would report 20 and hide exactly the systematic tilt
    # the column exists to measure.
    a_body = _ray((-1.0, 0.0), 0.0, 1.0)  # ends at (0, 0), heading 0
    up = _ray((0.0, 0.0), 20.0, 1.0)  # dep +20
    b_tip = _tip((0.0, 0.0), 20.0, 1.0)
    b_body = _ray(b_tip, 0.0, 1.0)  # arr -20, ends heading 0
    down = _ray(_tip(b_tip, 0.0, 1.0), -20.0, 1.0)  # dep -20
    c_body = _ray(_tip(_tip(b_tip, 0.0, 1.0), -20.0, 1.0), -20.0, 1.0)  # arr 0
    composed = {
        "items": [
            {"slot_index": 0, "centerline": a_body},
            {"centerline": up, "pair": ["a", "b"], "from_slot": 0, "to_slot": 1, "exit": up[0]},
            {"slot_index": 1, "centerline": b_body},
            {"centerline": down, "pair": ["b", "c"], "from_slot": 1, "to_slot": 2, "exit": down[0]},
            {"slot_index": 2, "centerline": c_body},
        ]
    }

    result = seam_angles(composed, _slots("a", "b", "c"))

    assert result["n_matched"] == 2
    assert sorted(j["dep_deg"] for j in result["joins"]) == pytest.approx([-20.0, 20.0], abs=0.01)
    assert result["dep_median"] == pytest.approx(0.0, abs=0.01)
    assert result["arr_median"] == pytest.approx(-10.0, abs=0.01)
