"""Join-geometry guards of the specimen-true connector grammar (PR #177).

Pure-geometry unit tests for ``_garland_centerline`` (the baseline-garland
join) and the ``end_swing`` eligibility guards — the branches a whole-word
composition rarely exercises. No DB, no fixtures beyond a tiny synthetic
payload.
"""

from __future__ import annotations

import math

from core.compose import GARLAND_MERGE_EPS, SWING_MAX_EXIT_Y, SWING_TOP_Y, _garland_centerline, _unit, compose_word
from core.shaping import GlyphSlot


def test_garland_rejects_non_rising_entry() -> None:
    # A falling lead-in (entry tangent pointing down-right) never garlands.
    assert _garland_centerline((0.0, 0.9), _unit(-30.0), (0.5, 0.5), _unit(-40.0)) is None
    # A backward lead-in neither.
    assert _garland_centerline((0.0, 0.9), _unit(-30.0), (0.5, 0.5), _unit(140.0)) is None


def test_garland_rejects_mid_rise_exit() -> None:
    # A sawtooth exit still mid-rise extends its diagonal, it does not dip.
    assert _garland_centerline((0.0, 0.49), _unit(40.0), (0.3, 0.58), _unit(40.0)) is None


def test_garland_rejects_exit_close_to_lead_in_line() -> None:
    # Exit sits almost ON the lead-in line (d_perp below the merge epsilon):
    # the taut cubic's shallow notch is the plates' join there (rb, on).
    p3 = (0.25, 0.55)
    d_in = _unit(45.0)
    p0 = (p3[0] - 0.2 * d_in[0], p3[1] - 0.2 * d_in[1] + GARLAND_MERGE_EPS / 2)
    assert _garland_centerline(p0, _unit(0.0), p3, d_in) is None


def test_garland_rejects_no_horizontal_room() -> None:
    assert _garland_centerline((0.0, 0.9), _unit(0.0), (0.05, 0.5), _unit(45.0)) is None


def test_garland_falls_and_rides_the_lead_in_line() -> None:
    # A deep join (r->e like): high level exit, flat rising entry far right.
    p0, d_out = (0.0, 0.86), _unit(5.0)
    p3, d_in = (0.5, 0.51), _unit(38.0)
    line = _garland_centerline(p0, d_out, p3, d_in)
    assert line is not None
    assert line[0] == p0 and line[-1] == p3
    # The turn dips below the entry (the rounded garland bottom) ...
    assert min(y for _, y in line) < p3[1]
    # ... and the tail rides the lead-in line: collinear with d_in.
    (x1, y1), (x2, y2) = line[-2], line[-1]
    tail_deg = math.degrees(math.atan2(y2 - y1, x2 - x1))
    assert abs(tail_deg - 38.0) < 1.0


def _payload(centerline: list[tuple[float, float]]) -> dict:
    """Minimal render payload: one stroke, no rings, entry at the first sample."""
    return {
        "centerlines_template": [centerline],
        "half_widths_template": [0.05] * len(centerline),
        "entry": {"xy": list(centerline[0])},
        "outline_paths": [],
        "template_guides": {"midband": 1.0},
    }


def _compose_single(centerline: list[tuple[float, float]]) -> dict:
    slot = GlyphSlot(key="x-isolated", text="x", position="isolated", ligature=False, space=False)
    return compose_word([slot], {"x-isolated": _payload(centerline)})


def test_no_swing_after_falling_exit() -> None:
    # The stroke ends falling: no rising flank to continue.
    composed = _compose_single([(0.0, 0.0), (0.2, 0.5), (0.4, 0.3)])
    assert len(composed["items"]) == 1  # the glyph stroke only, no Endstrich


def test_no_swing_when_exit_already_at_swing_top() -> None:
    # Exit between SWING_TOP_Y and SWING_MAX_EXIT_Y: rising, allowed band,
    # but nothing left to rise — the rise <= 0 guard ends the word as-is.
    top = (SWING_TOP_Y + SWING_MAX_EXIT_Y) / 2
    composed = _compose_single([(0.0, 0.0), (0.3, top / 2), (0.6, top)])
    assert len(composed["items"]) == 1


def test_swing_after_rising_mid_height_exit() -> None:
    # The happy path still swings: a sawtooth exit earns its Endstrich.
    composed = _compose_single([(0.0, 0.0), (0.2, 0.53)])
    assert len(composed["items"]) == 2
    swing = composed["items"][1]["centerline"]
    assert swing[-1][1] > 0.53  # rises ...
    assert swing[-1][1] <= SWING_TOP_Y + 1e-9  # ... at most to the target
