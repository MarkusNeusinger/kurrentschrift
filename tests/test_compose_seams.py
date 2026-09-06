"""Seam-negotiation guards („Übergänge J6", core.compose SEAM_NEGOTIATE_CAP_DEG).

Pure geometry on a synthetic two-stroke join: a letter that leaves at 30° and a
letter that is entered at 40° — the author's own example — plus the guards that
keep the rule from doing anything else. No DB, no fixtures.
"""

from __future__ import annotations

import math

import pytest

from core.compose import (
    SEAM_MAX_JUMP_DEG,
    SEAM_NEGOTIATE_BLEND,
    SEAM_NEGOTIATE_CAP_DEG,
    SEAM_NEGOTIATE_WINDOW,
    _seam_blend_weight,
    _seam_shares,
    _start_direction,
    _turn_seam_item,
    _twist_about_seam,
    _window_direction,
    _wrap_deg,
    compose_word,
)
from core.shaping import GlyphSlot


def _ramp(start: tuple[float, float], deg: float, length: float, n: int = 25) -> list[tuple[float, float]]:
    """A straight run of ``length`` at ``deg``, sampled ``n`` times."""
    d = (math.cos(math.radians(deg)), math.sin(math.radians(deg)))
    return [(start[0] + d[0] * length * i / n, start[1] + d[1] * length * i / n) for i in range(n + 1)]


# The author's example, drawn: A descends to the baseline and leaves its last
# 0.6 xh at 30°; B is entered on a lead-in that rises at 40°, high enough that
# the join really climbs into it. Both runs are longer than the blend, so both
# letters may take part in the negotiation.
_EXIT_30 = [(0.0, 0.95), (0.06, 0.5), (0.12, 0.05), *_ramp((0.12, 0.05), 30.0, 0.6)]
_ENTRY_40 = [*_ramp((0.0, 0.30), 40.0, 0.6), (0.52, 0.72), (0.58, 0.2)]


def _payload(centerline: list[tuple[float, float]], *, rings: bool = False) -> dict:
    body: dict = {
        "centerlines_template": [centerline],
        "half_widths_template": [0.05] * len(centerline),
        "entry": {"xy": list(centerline[0])},
        "outline_paths": [],
        "template_guides": {"midband": 1.0},
    }
    if rings:
        body["outline_paths"] = [
            [[[x, y - 0.05] for x, y in centerline] + [[x, y + 0.05] for x, y in centerline[::-1]]]
        ]
    return body


def _compose(
    *,
    seam_negotiation: bool = False,
    entry: list[tuple[float, float]] | None = None,
    max_jump: float = SEAM_MAX_JUMP_DEG,
    rings: bool = False,
) -> dict:
    slots = [
        GlyphSlot(key="e", text="e", position="initial", ligature=False, space=False),
        GlyphSlot(key="n", text="n", position="final", ligature=False, space=False),
    ]
    return compose_word(
        slots,
        {"e": _payload(_EXIT_30, rings=rings), "n": _payload(entry or _ENTRY_40, rings=rings)},
        provenance=True,
        seam_negotiation=seam_negotiation,
        seam_negotiation_max_jump_deg=max_jump,
    )


def _seam_jumps(composed: dict) -> tuple[float, float]:
    """(departure, arrival) turn in degrees, read the way the sensor reads them."""
    glyph_a = [tuple(p) for p in composed["items"][0]["centerline"]]
    conn = [tuple(p) for p in composed["items"][1]["centerline"]][1:-1]  # drop the overlap tucks
    glyph_b = [tuple(p) for p in composed["items"][2]["centerline"]]
    dep = _wrap_deg(
        _start_direction(conn, SEAM_NEGOTIATE_WINDOW)
        - _window_direction(glyph_a, len(glyph_a) - 1, SEAM_NEGOTIATE_WINDOW)
    )
    arr = _wrap_deg(
        _start_direction(glyph_b, SEAM_NEGOTIATE_WINDOW) - _window_direction(conn, len(conn) - 1, SEAM_NEGOTIATE_WINDOW)
    )
    return dep, arr


def test_seam_negotiation_is_off_by_default() -> None:
    # The switch defaults to off, and the fixture really does exercise the rule
    # — otherwise every assertion below would pass vacuously.
    assert _compose() == compose_word(
        [
            GlyphSlot(key="e", text="e", position="initial", ligature=False, space=False),
            GlyphSlot(key="n", text="n", position="final", ligature=False, space=False),
        ],
        {"e": _payload(_EXIT_30), "n": _payload(_ENTRY_40)},
        provenance=True,
    )
    assert _compose(seam_negotiation=True) != _compose()


def test_a_thirty_forty_join_comes_out_without_a_step() -> None:
    # The author's rule, measured: leaving one letter at 30° and entering the
    # next at 40° must produce no step the eye can read at either seam.
    dep_off, arr_off = _seam_jumps(_compose())
    assert max(abs(dep_off), abs(arr_off)) > 3.0  # the fixture has real seams
    dep_on, arr_on = _seam_jumps(_compose(seam_negotiation=True))
    assert abs(dep_on) < 0.05
    assert abs(arr_on) < 0.05


def test_both_letters_give_something_and_neither_gives_more_than_the_cap() -> None:
    turns = [it["seam_turns"] for it in _compose(seam_negotiation=True)["items"] if it.get("seam_turns")]
    assert len(turns) == 1
    # Both letters take part — the author's preferred half of the rule ("in der
    # letzten Kurve wird etwas weiter gedreht oder im Eingang") — and neither
    # gives more than the cap.
    for side in ("exit", "entry"):
        letter, _connector = turns[0][side]
        assert 0.0 < abs(letter) <= SEAM_NEGOTIATE_CAP_DEG + 1e-9
    # They turn TOWARD each other: the exit turns up, the entry turns down.
    assert turns[0]["exit"][0] > 0 > turns[0]["entry"][0]


def test_the_seam_points_and_the_placement_do_not_move() -> None:
    # The pre-registered control, and the difference to the P3 entry rules: a
    # turn about the seam point can move neither the coupling points nor the
    # right glyph's placement.
    off, on = _compose(), _compose(seam_negotiation=True)
    for key in ("exit", "entry"):
        assert off["items"][1][key] == pytest.approx(on["items"][1][key], abs=1e-12)
    assert off["items"][2]["centerline"][0] == pytest.approx(on["items"][2]["centerline"][0], abs=1e-12)
    assert off["items"][0]["centerline"][-1] == pytest.approx(on["items"][0]["centerline"][-1], abs=1e-12)


def test_the_blend_leaves_the_body_of_the_letter_alone() -> None:
    # Everything farther from the seam than the blend is untouched, sample for
    # sample — the turn is the last curve, never the letterform.
    off = [tuple(p) for p in _compose()["items"][0]["centerline"]]
    on = [tuple(p) for p in _compose(seam_negotiation=True)["items"][0]["centerline"]]
    seam = off[-1]
    assert len(off) == len(on)
    far = [i for i, p in enumerate(off) if math.dist(p, seam) > SEAM_NEGOTIATE_BLEND]
    assert far  # the fixture reaches past the blend
    for i in far:
        assert on[i] == pytest.approx(off[i], abs=1e-12)


def test_the_blend_adds_no_kink_where_it_fades_out() -> None:
    # The whole point of the decaying turn: the turned piece must meet the
    # untouched stroke without a second step. Measured on a stretch that runs
    # dead straight in the base, so every degree of turn in the arm is the
    # rule's own — the turn must be SPREAD, not spent at one vertex.
    def turns(line: list[tuple[float, float]]) -> list[float]:
        return [
            _wrap_deg(
                math.degrees(math.atan2(line[i + 1][1] - line[i][1], line[i + 1][0] - line[i][0]))
                - math.degrees(math.atan2(line[i][1] - line[i - 1][1], line[i][0] - line[i - 1][0]))
            )
            for i in range(1, len(line) - 1)
        ]

    off = turns([tuple(p) for p in _compose()["items"][0]["centerline"]])
    on = turns([tuple(p) for p in _compose(seam_negotiation=True)["items"][0]["centerline"]])
    added = [a - b for a, b in zip(on, off, strict=True)]
    total = abs(sum(added))
    assert total > 1.0  # the rule really did turn this stroke
    # No vertex carries more than a modest share of it, and the two ends of the
    # blend taper away — a step would put nearly all of it on one vertex.
    assert max(abs(d) for d in added) < 0.6 * total
    touched = [i for i, d in enumerate(added) if abs(d) > 1e-9]
    assert abs(added[touched[0]]) < 0.15 * total
    assert abs(added[touched[-1]]) < 0.15 * total


def test_a_ductus_turnaround_is_left_alone() -> None:
    # An exit whose last stretch runs BACKWARDS is an event the hand writes (the
    # w/v bow curl, the ſ return), not a seam that got away: the connector has
    # to leave on the forward chord, and past SEAM_MAX_JUMP_DEG the rule keeps
    # its hands off that seam. The other one is still judged on its own.
    curl = [*_EXIT_30, (0.62, 0.36), (0.56, 0.38)]
    slots = [
        GlyphSlot(key="v", text="v", position="initial", ligature=False, space=False),
        GlyphSlot(key="n", text="n", position="final", ligature=False, space=False),
    ]
    payloads = {"v": _payload(curl), "n": _payload(_ENTRY_40)}
    on = compose_word(slots, payloads, provenance=True, seam_negotiation=True)
    off = compose_word(slots, payloads, provenance=True)
    turns = [it["seam_turns"] for it in on["items"] if it.get("seam_turns")]
    assert turns and turns[0]["exit"] is None
    assert on["items"][0]["centerline"] == off["items"][0]["centerline"]


def test_max_jump_narrows_the_class() -> None:
    # The J6b knob: a ceiling below this fixture's seam gap switches the rule
    # off for it, one above leaves it firing.
    assert _compose(seam_negotiation=True, max_jump=0.5) == _compose()
    assert _compose(seam_negotiation=True, max_jump=SEAM_MAX_JUMP_DEG) == _compose(seam_negotiation=True)


def test_the_turn_takes_the_silhouette_with_the_centerline() -> None:
    # Ink and centerline must move as one, or the letter renders with a torn
    # outline — which is a worse defect than the seam the rule smooths.
    on = _compose(seam_negotiation=True, rings=True)["items"][0]
    line = [tuple(p) for p in on["centerline"]]
    for ring in on["rings"]:
        for x, y in ring:
            assert min(math.dist((x, y), p) for p in line) < 0.08


def test_seam_shares_split_the_gap_and_cap_the_letter() -> None:
    # Inside twice the cap both sides meet exactly in the middle …
    letter, connector = _seam_shares(30.0, 40.0, True, True, SEAM_MAX_JUMP_DEG)
    assert letter == pytest.approx(5.0)
    assert connector == pytest.approx(-5.0)
    # … past it the letter stops at the cap and the connector closes the rest …
    letter, connector = _seam_shares(0.0, 40.0, True, True, SEAM_MAX_JUMP_DEG)
    assert letter == pytest.approx(SEAM_NEGOTIATE_CAP_DEG)
    assert connector == pytest.approx(SEAM_NEGOTIATE_CAP_DEG - 40.0)
    # … a letter too short to turn about one end gives nothing and the
    # connector takes the whole gap …
    assert _seam_shares(30.0, 40.0, False, True, SEAM_MAX_JUMP_DEG) == (0.0, -10.0)
    # … a connector too short to hold a turn leaves the whole gap to the
    # letter, still capped …
    assert _seam_shares(35.0, 40.0, True, False, SEAM_MAX_JUMP_DEG) == (5.0, 0.0)
    assert _seam_shares(0.0, 40.0, True, False, SEAM_MAX_JUMP_DEG) == (SEAM_NEGOTIATE_CAP_DEG, 0.0)
    # … neither side able to move is no negotiation …
    assert _seam_shares(30.0, 40.0, False, False, SEAM_MAX_JUMP_DEG) is None
    # … and a ductus event is not a negotiation at all.
    assert _seam_shares(30.0, 120.0, True, True, SEAM_MAX_JUMP_DEG) is None


def test_blend_weight_is_rigid_at_the_seam_and_flat_at_its_edge() -> None:
    hold, length = SEAM_NEGOTIATE_WINDOW, SEAM_NEGOTIATE_BLEND
    # Rigid over the arc the seam direction is READ on, so the direction there
    # turns by exactly the negotiated angle.
    assert _seam_blend_weight(0.0, hold, length) == 1.0
    assert _seam_blend_weight(hold, hold, length) == 1.0
    assert _seam_blend_weight(length, hold, length) == 0.0
    assert _seam_blend_weight(length + 1.0, hold, length) == 0.0
    # Monotone in between, and flat at both ends of the decay (no step).
    steps = [_seam_blend_weight(hold + (length - hold) * i / 40, hold, length) for i in range(41)]
    assert all(b <= a + 1e-12 for a, b in zip(steps, steps[1:], strict=False))
    assert abs(steps[1] - steps[0]) < abs(steps[20] - steps[19])
    assert abs(steps[-1] - steps[-2]) < abs(steps[20] - steps[19])
    # It is the QUINTIC, not the cubic smoothstep: a tenth of the way in the
    # weight has dropped by ~0.009, where a cubic would already have spent
    # 0.028. That third vanishing derivative is what keeps the CURVATURE step
    # away as well, which is half of the perceptual rule this arm serves.
    tenth = _seam_blend_weight(hold + (length - hold) * 0.1, hold, length)
    assert 1.0 - tenth < 0.015


def test_the_twist_pins_the_seam_point_and_releases_the_far_field() -> None:
    pivot = (1.0, 1.0)
    pts = [pivot, (1.0 + SEAM_NEGOTIATE_WINDOW, 1.0), (1.0 + SEAM_NEGOTIATE_BLEND + 0.1, 1.0)]
    out = _twist_about_seam(pts, pivot, 10.0, SEAM_NEGOTIATE_BLEND)
    assert out[0] == pivot  # the coupling point never moves
    assert out[2] == pts[2]  # past the blend nothing moves
    # Inside the rigid disc the turn is the full angle.
    assert math.degrees(math.atan2(out[1][1] - pivot[1], out[1][0] - pivot[0])) == pytest.approx(10.0)


def test_turn_seam_item_moves_rings_and_centerline_together() -> None:
    line = [(0.02 * i, 0.0) for i in range(31)]
    item = {
        "centerline": [list(p) for p in line],
        "rings": [[[x, y + 0.05] for x, y in line] + [[x, y - 0.05] for x, y in line[::-1]]],
    }
    before = [list(p) for p in item["rings"][0]]
    _turn_seam_item(item, 8.0, at_end=True, blend=SEAM_NEGOTIATE_BLEND)
    assert item["centerline"][-1] == [line[-1][0], line[-1][1]]  # the seam point holds
    assert item["centerline"][0] == [line[0][0], line[0][1]]  # the far end holds
    # The ring points inside the rigid seam disc really moved — a silhouette
    # left behind is the defect this function exists to prevent, and it would
    # otherwise pass the proximity check below unnoticed.
    seam = tuple(line[-1])
    inside = [(a, b) for a, b in zip(before, item["rings"][0], strict=True) if math.dist(a, seam) <= 0.05]
    assert inside
    assert all(math.dist(a, b) > 1e-6 for a, b in inside if math.dist(a, seam) > 1e-9)
    # … and the ink still sits a half-width off the TURNED centerline.
    turned = [tuple(p) for p in item["centerline"]]
    for x, y in item["rings"][0]:
        assert min(math.dist((x, y), p) for p in turned) < 0.06


# A glyph whose stroke loops back near its own lead-in, so the twist — which
# reaches by DISTANCE, not along the stroke — moves its EXIT while turning its
# entry: the stroke ends well inside SEAM_NEGOTIATE_BLEND of the coupling
# sample it is turned about.
_LOOPING = [*_ramp((0.0, 0.30), 40.0, 0.35, 12), (0.32, 0.95), (0.12, 1.10), (0.02, 0.80), (0.16, 0.45), (0.10, 0.25)]


def test_a_looped_glyph_hands_on_the_exit_it_actually_drew() -> None:
    # The twist reaches by distance, so turning this glyph's ENTRY also moves
    # its exit — and everything the next slot reads off it (endpoint, tangent,
    # the join that departs there) has to follow, or the third letter's join
    # starts on a point that is no longer on any ink.
    slots = [
        GlyphSlot(key="e", text="e", position="initial", ligature=False, space=False),
        GlyphSlot(key="n", text="n", position="medial", ligature=False, space=False),
        GlyphSlot(key="i", text="i", position="final", ligature=False, space=False),
    ]
    payloads = {"e": _payload(_EXIT_30), "n": _payload(_LOOPING), "i": _payload(_ENTRY_40)}
    off = compose_word(slots, payloads, provenance=True)
    on = compose_word(slots, payloads, provenance=True, seam_negotiation=True)

    def body_of(composed: dict, slot_index: int) -> list:
        return [it for it in composed["items"] if it.get("slot_index") == slot_index][-1]["centerline"]

    def join_from(composed: dict, slot_index: int) -> dict:
        return next(it for it in composed["items"] if it.get("from_slot") == slot_index and it.get("to_slot"))

    # The fixture really does exercise it: the looped glyph's exit MOVED.
    assert math.dist(body_of(off, 1)[-1], body_of(on, 1)[-1]) > 1e-6
    # … and the join to the third letter departs from exactly that new point.
    assert join_from(on, 1)["exit"] == pytest.approx(body_of(on, 1)[-1], abs=1e-12)


def test_seam_negotiation_max_jump_must_narrow_the_class() -> None:
    # A negative ceiling would silently disable the rule while the caller
    # believes it asked for a narrower one; one ABOVE the pre-registered class
    # would widen it while every report still calls the run the narrowed arm.
    # Both CLIs refuse the same range.
    with pytest.raises(ValueError, match="must lie between"):
        _compose(seam_negotiation=True, max_jump=-1.0)
    with pytest.raises(ValueError, match="must lie between"):
        _compose(seam_negotiation=True, max_jump=SEAM_MAX_JUMP_DEG + 1.0)
    with pytest.raises(ValueError, match="must lie between"):
        _compose(seam_negotiation=True, max_jump=float("nan"))
