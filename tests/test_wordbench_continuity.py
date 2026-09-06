"""Acceptance of the Unstetigkeits-Sensor on synthetic curves.

The shape of the suite mirrors tests/test_pairlab_spanmeas.py: positive
properties (P) that the sensor MUST show, and Nullproben (N) on inputs where
it must show nothing. Every case is a hand-built polyline in template units
(1 = x-height), so a failure names a geometric claim rather than a fixture.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from tools.wordbench.continuity import (
    BOW_CHORD_UNITS,
    KINK_THRESHOLD_DEG,
    KINK_WINDOW_UNITS,
    LANDMARK_RADIUS_UNITS,
    continuity,
)


STEP = 0.005  # the composed centreline's own sampling order of magnitude


def _line(length: float, angle_deg: float, start: tuple[float, float] = (0.0, 0.0)) -> np.ndarray:
    n = max(2, int(round(length / STEP)) + 1)
    t = np.linspace(0.0, length, n)
    a = math.radians(angle_deg)
    return np.column_stack([start[0] + t * math.cos(a), start[1] + t * math.sin(a)])


def _arc(radius: float, sweep_deg: float, start_deg: float = 0.0) -> np.ndarray:
    n = max(3, int(round(abs(math.radians(sweep_deg)) * radius / STEP)) + 1)
    a = np.radians(np.linspace(start_deg, start_deg + sweep_deg, n))
    return np.column_stack([radius * np.cos(a), radius * np.sin(a)])


def _glyph(points: np.ndarray, *, lift: bool = False) -> dict:
    """A composed GLYPH item — `rings` is the composer's own body predicate."""
    return {"centerline": [[float(x), float(y)] for x, y in points], "rings": [], "lift": lift}


def _word(*items: dict) -> dict:
    return {"items": list(items), "missing": []}


def _one(points: np.ndarray) -> dict:
    return continuity(_word(_glyph(points)))


# ------------------------------------------------------------------ Nullproben


def test_n1_straight_line_has_no_kink_no_wobble_no_bow():
    """N1 — a perfect line is continuous everywhere."""
    row = _one(_line(3.0, 30.0))
    assert row["n_measured"] > 100
    assert row["kink_count"] == 0
    assert row["kink_max_deg"] == pytest.approx(0.0, abs=1e-6)
    assert row["wobble"] == pytest.approx(0.0, abs=1e-6)
    assert row["bow_median"] == pytest.approx(0.0, abs=1e-6)


def test_n2_circular_arc_has_no_kink_and_no_wobble_at_any_radius():
    """N2 — the owner's sentence, as a test: the radius must not matter.

    A sensor that fired on curvature would flag every loop of the script.
    Each arc is one x-height of travel, so every window has room.
    """
    for radius in (0.2, 0.4, 0.8, 1.6):
        row = _one(_arc(radius, math.degrees(1.0 / radius)))
        assert row["kink_count"] == 0, f"radius {radius} read as a kink"
        assert row["kink_max_deg"] < 1.0, f"radius {radius}: {row['kink_max_deg']}"
        assert row["wobble"] < 0.5, f"radius {radius}: {row['wobble']}"
        # …but the arc DOES bow, which is the order-2 channel doing its job.
        assert row["bow_median"] > 0.005


def test_n4_a_stretch_too_short_for_the_trend_window_reports_no_wobble():
    """N4 — a statistic whose window does not fit is None, never a number."""
    row = _one(_arc(0.15, 150.0))
    assert row["n_measured"] > 0
    assert row["wobble"] is None
    assert row["kink_max_deg"] is not None


def test_n3_translation_and_sampling_density_leave_the_reading_alone():
    """N3 — the sensor reads shape, not placement or point count."""
    pts = np.vstack([_line(1.0, 0.0), _line(1.0, 25.0, (1.0, 0.0))[1:]])
    base = _one(pts)
    moved = _one(pts + np.array([7.5, -2.25]))
    assert moved["kink_max_deg"] == pytest.approx(base["kink_max_deg"], abs=1e-6)
    assert moved["kink_count"] == base["kink_count"]


# ------------------------------------------------------------------ properties


def test_p1_a_single_kink_is_found_at_its_true_angle():
    """P1 — two straight lines meeting at 25° read 25°, once."""
    pts = np.vstack([_line(1.0, 0.0), _line(1.0, 25.0, (1.0, 0.0))[1:]])
    row = _one(pts)
    assert row["kink_count"] == 1
    assert row["kink_max_deg"] == pytest.approx(25.0, abs=1.5)
    assert row["kinks"][0]["at"][0] == pytest.approx(1.0, abs=2.0 * KINK_WINDOW_UNITS)


def test_p2_the_threshold_separates_visible_from_invisible():
    """P2 — the pre-registered θ is the line between counted and not."""
    below = _one(np.vstack([_line(1.0, 0.0), _line(1.0, KINK_THRESHOLD_DEG - 4.0, (1.0, 0.0))[1:]]))
    above = _one(np.vstack([_line(1.0, 0.0), _line(1.0, KINK_THRESHOLD_DEG + 4.0, (1.0, 0.0))[1:]]))
    assert below["kink_count"] == 0
    assert above["kink_count"] == 1


def test_p3_a_bow_that_became_a_chord_shows_up_as_curv_loss():
    """P3 — bow · chord · bow: the flat middle is the finding.

    A plain bow must NOT read as a loss. The bracket sits one chord out on
    both sides, so what this channel sees is a flat spot up to about
    2·``BOW_CHORD_UNITS`` long; a longer straight stretch between two curves is
    an ordinary stem, and the join-scoped ``bow_join`` is what reads a whole
    lead-in that was pulled straight.
    """
    arc_a = _arc(0.35, 150.0, 190.0)
    flat = _line(BOW_CHORD_UNITS, 20.0, tuple(arc_a[-1]))
    arc_b = _arc(0.35, 150.0, 190.0) + (flat[-1] - _arc(0.35, 150.0, 190.0)[0])
    with_flat = _one(np.vstack([arc_a, flat[1:], arc_b[1:]]))
    pure_bow = _one(_arc(0.35, 340.0))
    assert with_flat["curv_loss"] > 0.01
    assert pure_bow["curv_loss"] < with_flat["curv_loss"] / 2.0


def test_p4_a_wobbling_line_reads_as_wobble_without_reading_as_a_bow():
    """P4 — Wackler and Bogen are different channels."""
    length = 3.0
    n = int(length / STEP) + 1
    x = np.linspace(0.0, length, n)
    amplitude = 0.01  # well under the ink width, still a visible tremor
    wobbly = np.column_stack([x, amplitude * np.sin(2.0 * math.pi * x / (2.0 * BOW_CHORD_UNITS))])
    row = _one(wobbly)
    straight = _one(_line(length, 0.0))
    assert row["wobble"] > 5.0 * max(straight["wobble"], 1e-6)
    assert row["wobble"] > 1.0


# ------------------------------------------------------------------ exemptions


def test_p5_a_reversal_corner_is_exempt_but_a_shallow_kink_beside_it_is_not():
    """P5 — the landmark exemption is narrow: it takes reversals, not kinks."""
    out = _line(1.0, 90.0)
    back = _line(1.0, -90.0, (0.02, 1.0))
    reversal = _one(np.vstack([out, back]))
    assert reversal["kink_count"] == 0, "a within-stroke reversal is ductus, not a defect"

    kinked = np.vstack([out, back, _line(1.0, -60.0, (0.02, 0.0))[1:]])
    assert _one(kinked)["kink_count"] == 1, "a 30° turn away from the corner must survive"


def test_p6_a_lift_is_never_read_as_a_kink():
    """P6 — two pen strokes meeting at an angle are two strokes, not a kink."""
    first = _glyph(_line(1.0, 0.0))
    second = _glyph(_line(1.0, 60.0, (1.0, 0.0)), lift=True)
    row = continuity(_word(first, second))
    assert row["kink_count"] == 0


def test_p7_samples_inside_the_end_margin_are_never_measured():
    """P7 — no measurement window may run off the end of a stroke."""
    row = _one(_line(4.0 * LANDMARK_RADIUS_UNITS, 0.0))
    assert row["n_measured"] > 0
    assert row["n_measured"] < row["n_samples"]
    assert row["excluded"]["lift"] > 0


def test_p8_a_word_shorter_than_the_margins_reports_none_not_zero():
    """P8 — a fabricated zero would read as a perfect word."""
    row = _one(_line(0.5 * LANDMARK_RADIUS_UNITS, 0.0))
    assert row["n_measured"] == 0
    assert row["kink_max_deg"] is None
    assert row["wobble"] is None
    assert row["kink_count"] == 0


def test_p9_the_join_bow_reads_the_connector_neighbourhood_only():
    """P9 — `bow_join` is the Pfeilhöhe §7.9 asks for, at the joins."""
    left = _glyph(_line(1.0, 0.0))
    connector = {"centerline": [[float(x), float(y)] for x, y in _arc(0.3, 60.0, 300.0) + np.array([1.0, 0.26])]}
    right = _glyph(_line(1.0, 0.0, (1.45, 0.26)))
    row = continuity(_word(left, connector, right))
    assert row["bow_join"] is not None
    # The straight letters bow not at all, the connector does — so the join
    # reading must sit above the word-wide median.
    assert row["bow_join"] > row["bow_median"]
