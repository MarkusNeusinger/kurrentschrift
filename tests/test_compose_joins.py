"""Join-geometry guards of the specimen-true connector grammar.

Pure-geometry unit tests for ``_garland_centerline`` (the baseline-garland
join) and the ``end_swing`` eligibility guards — the branches a whole-word
composition rarely exercises. No DB, no fixtures beyond a tiny synthetic
payload.
"""

from __future__ import annotations

import math

from core.compose import (
    ALIGN_MAX_ENTRY_Y,
    ALIGN_MIN_RISE,
    GARLAND_MERGE_EPS,
    SWING_DEEP_MAX_RUN,
    SWING_MAX_EXIT_Y,
    SWING_TOP_Y,
    _flank_couple_index,
    _flank_couple_placement,
    _flank_couple_steepest,
    _garland_centerline,
    _unit,
    compose_word,
)
from core.shaping import GlyphSlot


def test_garland_rejects_non_rising_entry() -> None:
    # A falling lead-in (entry tangent pointing down-right) never garlands.
    assert _garland_centerline((0.0, 0.9), _unit(-30.0), (0.5, 0.5), _unit(-40.0)) is None
    # A backward lead-in neither.
    assert _garland_centerline((0.0, 0.9), _unit(-30.0), (0.5, 0.5), _unit(140.0)) is None


def test_garland_rejects_mid_rise_exit() -> None:
    # A sawtooth exit still mid-rise extends its diagonal, it does not dip.
    assert _garland_centerline((0.0, 0.49), _unit(40.0), (0.3, 0.58), _unit(40.0)) is None


def test_garland_rejects_descender_exit() -> None:
    # A descender return-upstroke (long-s, x) rises into the entry — it never
    # dips again, even with an artificially shallow launch.
    assert _garland_centerline((0.0, -0.9), _unit(10.0), (3.0, 0.55), _unit(40.0)) is None


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


# A rising ~40° lead-in flank like a Sütterlin arcade/loop letter's Anstrich:
# foot at half height, diagonal-banded all the way to the cap.
_FLANK = [(0.012 * i, 0.5 + 0.01 * i) for i in range(13)]


def test_flank_couple_index_finds_the_line_crossing() -> None:
    # Exit below the foot's line: the ~40° flank crosses the 25° rise line
    # partway up — the coupling index is the first sample on/above it.
    slope = math.tan(math.radians(25.0))
    i = _flank_couple_index(_FLANK, 0.2, (0.0, 0.45), slope)
    assert i > 0
    x, y = _FLANK[i][0] + 0.2, _FLANK[i][1]
    assert y - 0.45 >= slope * x - 1e-9  # on/above the line
    assert _FLANK[i - 1][1] - 0.45 < slope * (_FLANK[i - 1][0] + 0.2)  # first such sample


def test_flank_couple_index_leaves_a_foot_on_the_line_alone() -> None:
    # Foot already on/above the rise line: the pass-through placement owns it.
    assert _flank_couple_index(_FLANK, 0.1, (0.0, 0.3), math.tan(math.radians(30.0))) == 0


def test_flank_couple_index_rejects_a_turning_head() -> None:
    # The flank bends over (turns down) just before the line crossing: a real
    # head form, never trimmed — even though a longer flank would cross.
    head = [(0.012 * i, 0.5 + 0.01 * i) for i in range(5)] + [(0.07, 0.53), (0.09, 0.5)]
    assert _flank_couple_index(head, 0.21, (0.0, 0.45), math.tan(math.radians(20.0))) == 0


def test_flank_couple_placement_puts_the_flank_exactly_on_the_line() -> None:
    slope = math.tan(math.radians(33.0))
    fit = _flank_couple_placement(_FLANK, (2.0, 0.53), slope, 0.0, -math.inf)
    assert fit is not None
    place, i = fit
    x, y = _FLANK[i][0] + place, _FLANK[i][1]
    assert math.isclose(y - 0.53, slope * (x - 2.0), abs_tol=1e-9)  # ON the line
    assert y >= 0.53 + ALIGN_MIN_RISE  # the pen gains height


def test_flank_couple_placement_respects_the_ink_floor() -> None:
    slope = math.tan(math.radians(33.0))
    unbounded = _flank_couple_placement(_FLANK, (2.0, 0.53), slope, 0.0, -math.inf)
    assert unbounded is not None
    # A floor just above the unbounded fit forces a higher coupling sample …
    floored = _flank_couple_placement(_FLANK, (2.0, 0.53), slope, 0.0, unbounded[0] + 0.005)
    assert floored is not None and floored[1] > unbounded[1]
    # … and an unreachable floor yields no fit at all.
    assert _flank_couple_placement(_FLANK, (2.0, 0.53), slope, 0.0, 10.0) is None


def test_flank_couple_steepest_takes_the_top_of_the_window() -> None:
    i = _flank_couple_steepest(_FLANK, 0.2, (0.0, 0.5))
    assert i > 0
    assert _FLANK[i][1] <= ALIGN_MAX_ENTRY_Y
    # No later candidate exists inside the cap.
    assert all(_FLANK[j][1] > ALIGN_MAX_ENTRY_Y for j in range(i + 1, len(_FLANK) - 1))


def test_flank_coupled_connector_is_straight_and_trims_the_stub() -> None:
    # Two sawtooth letters whose entry foot sits just BELOW the previous
    # exit (the "ne" case): the composed connector must be a straight line
    # onto B's flank and B's first stroke must start at the coupling point.
    a = [(0.0, 0.0), (0.15, 0.3), (0.3, 0.42)]  # arcade exit rising ~39°
    b = [(0.012 * i, 0.4 + 0.01 * i) for i in range(13)] + [(0.16, 0.63), (0.17, 0.3), (0.18, 0.0)]
    slots = [
        GlyphSlot(key="n", text="n", position="initial", ligature=False, space=False),
        GlyphSlot(key="m", text="m", position="final", ligature=False, space=False),
    ]
    composed = compose_word(slots, {"n": _payload(a), "m": _payload(b)})
    assert len(composed["items"]) >= 3
    connector, glyph_b = composed["items"][1], composed["items"][2]
    line = connector["centerline"]
    # Straight: every interior sample lies on the chord.
    (x0, y0), (x1, y1) = line[0], line[-1]
    span = math.hypot(x1 - x0, y1 - y0)
    assert span > 0
    for x, y in line:
        assert abs(-(y1 - y0) * (x - x0) + (x1 - x0) * (y - y0)) / span < 1e-9
    assert y1 > y0  # the join rises
    # B's trimmed first stroke starts at the connector's arrival (the stub
    # below the coupling point is absorbed by the join).
    bx, by = glyph_b["centerline"][0]
    assert math.isclose(bx, x1, abs_tol=1e-9) and math.isclose(by, y1, abs_tol=1e-9)
    assert by > b[0][1]  # the foot sample is gone


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


def test_deep_exit_swing_respects_its_run_cap() -> None:
    # An exit below the baseline (x's under-loop) flicks only briefly; the
    # interpolated cap point guarantees the stroke never passes the cap even
    # when the sample step is coarse.
    exit_pt = (0.4, -0.5)
    composed = _compose_single([(0.0, 0.5), (0.2, -0.6), exit_pt])
    assert len(composed["items"]) == 2
    swing = composed["items"][1]["centerline"]
    assert max(x for x, _ in swing) <= exit_pt[0] + SWING_DEEP_MAX_RUN + 1e-9
