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
    CONNECT_GAP,
    GARLAND_MERGE_EPS,
    GARLAND_MIN_DX,
    SWING_DEEP_MAX_RUN,
    SWING_MAX_EXIT_Y,
    SWING_TOP_Y,
    _flank_couple_index,
    _flank_couple_steepest,
    _fused_flank_placement,
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


def test_flank_couple_index_walks_past_a_degenerate_early_crossing() -> None:
    # The line crosses the flank immediately above the foot (no height gained
    # over the exit yet, no rightward progress): the scan walks on and couples
    # at the first sample clearing both guards instead of rejecting outright.
    i = _flank_couple_index(_FLANK, 0.001, (0.0, 0.5), math.tan(math.radians(35.0)))
    assert i > 1  # the immediate crossing at the first sample was skipped …
    assert _FLANK[i][1] >= 0.5 + ALIGN_MIN_RISE  # … for one that gains height
    assert _FLANK[i][0] + 0.001 >= GARLAND_MIN_DX  # … and progresses rightward


def test_flank_couple_index_rejects_when_the_window_ends_before_the_guards() -> None:
    # Same degenerate crossing, but the couple-able window (the flank turns
    # down) ends before any sample clears the progress guard: no coupling.
    short = _FLANK[:5] + [(0.06, 0.53)]
    assert _flank_couple_index(short, 0.001, (0.0, 0.5), math.tan(math.radians(35.0))) == 0


def test_flank_couple_index_leaves_a_foot_on_the_line_alone() -> None:
    # Foot already on/above the rise line: the pass-through placement owns it.
    assert _flank_couple_index(_FLANK, 0.1, (0.0, 0.3), math.tan(math.radians(30.0))) == 0


def test_flank_couple_index_rejects_a_turning_head() -> None:
    # The flank bends over (turns down) just before the line crossing: a real
    # head form, never trimmed — even though a longer flank would cross.
    head = [(0.012 * i, 0.5 + 0.01 * i) for i in range(5)] + [(0.07, 0.53), (0.09, 0.5)]
    assert _flank_couple_index(head, 0.21, (0.0, 0.45), math.tan(math.radians(20.0))) == 0


def test_fused_flank_placement_puts_the_flank_exactly_on_the_line() -> None:
    slope = math.tan(math.radians(40.0))
    fit = _fused_flank_placement(_FLANK, (2.0, 0.53), slope, 0.0)
    assert fit is not None
    place, i = fit
    x, y = _FLANK[i][0] + place, _FLANK[i][1]
    assert math.isclose(y - 0.53, slope * (x - 2.0), abs_tol=1e-9)  # ON the line
    assert y >= 0.53 + ALIGN_MIN_RISE  # the pen gains height
    # Lowest couple-able sample wins — no earlier sample gains the height.
    assert all(_FLANK[j][1] < 0.53 + ALIGN_MIN_RISE for j in range(1, i))


def test_fused_flank_placement_needs_a_couple_able_window() -> None:
    # Exit above the whole flank window: no sample gains height — no fusion.
    assert _fused_flank_placement(_FLANK, (2.0, 0.65), math.tan(math.radians(40.0)), 0.0) is None


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
    # B's trimmed first stroke starts at the connector's geometric arrival —
    # the SECOND-to-last sample: the last one is the CONNECT_OVERLAP
    # extension tucking under B's ink (see _overlap_extend).
    ax, ay = line[-2]
    bx, by = glyph_b["centerline"][0]
    assert math.isclose(bx, ax, abs_tol=1e-9) and math.isclose(by, ay, abs_tol=1e-9)
    assert by > b[0][1]  # the foot sample is gone


def test_fused_composition_continues_the_stroke_slope() -> None:
    # A steep (~54°) lead-in flank behind a flat (~27°) arcade exit: the
    # fused placement is legal (no off-band ink conflict) — the pair is
    # pushed together until the coupling sample sits ON the line through the
    # exit at the FULL mean ink tangent, so the straight connector continues
    # the stroke slope itself (no ALIGN_SLOPE_RATIO flattening — the
    # flattened slant was the user-visible kink).
    from core.compose import _endpoint_tangent

    a = [(0.0, 0.0), (0.1, 0.35), (0.3, 0.45)]  # exit tangent ≈ 26.6°
    step_x = 0.012 / math.tan(math.radians(54.0))
    b = [(step_x * i, 0.44 + 0.012 * i) for i in range(14)] + [(0.2, 0.3), (0.22, 0.0)]
    slots = [
        GlyphSlot(key="n", text="n", position="initial", ligature=False, space=False),
        GlyphSlot(key="m", text="m", position="final", ligature=False, space=False),
    ]
    composed = compose_word(slots, {"n": _payload(a), "m": _payload(b)})
    connector = composed["items"][1]
    line = connector["centerline"]
    (x0, y0), (x1, y1) = line[0], line[-1]
    assert y1 > y0 and x1 > x0
    # The pair is pulled TIGHTER than the plain nested placement …
    assert x1 - x0 < CONNECT_GAP
    # … and the chord continues the full mean-tangent stroke direction.
    exit_deg = _endpoint_tangent(a, at_end=True)
    land_deg = _endpoint_tangent(b, at_end=False)
    expected = math.tan(math.radians((exit_deg + land_deg) / 2))
    assert math.isclose((y1 - y0) / (x1 - x0), expected, rel_tol=1e-9)


def test_fused_clearance_conflict_falls_back_to_the_steepest_line() -> None:
    # Same sawtooth pair, but A carries low ink far right and B low ink left
    # (below the fusion band): the height-aware guard rejects the fused
    # placement, and the join falls back to the steepest straight line at
    # the column floor instead.
    a_strokes = [
        [(0.1, -0.12), (0.6, -0.08)],  # low sweep, blocks the fused tuck
        [(0.0, 0.0), (0.15, 0.3), (0.3, 0.42)],  # arcade exit ≈ 39°
    ]
    b = [(0.012 * i, 0.4 + 0.01 * i) for i in range(13)] + [(0.16, 0.63), (0.17, 0.3), (0.19, -0.1)]
    slots = [
        GlyphSlot(key="n", text="n", position="initial", ligature=False, space=False),
        GlyphSlot(key="m", text="m", position="final", ligature=False, space=False),
    ]
    payload_a = {
        "centerlines_template": a_strokes,
        "half_widths_template": [0.05] * 5,
        "entry": {"xy": [0.1, -0.12]},
        "outline_paths": [],
        "template_guides": {"midband": 1.0},
    }
    composed = compose_word(slots, {"n": payload_a, "m": _payload(b)})
    connector = next(it for it in composed["items"] if "stroke_width" in it)
    line = connector["centerline"]
    (x0, y0), (x1, y1) = line[0], line[-1]
    span = math.hypot(x1 - x0, y1 - y0)
    assert span > 0
    for x, y in line:  # still a straight line …
        assert abs(-(y1 - y0) * (x - x0) + (x1 - x0) * (y - y0)) / span < 1e-9
    assert y1 > y0  # … and still rising
    # But NOT fused: the placement respects the column floor past A's low ink.
    assert x1 - x0 > CONNECT_GAP  # no tuck under the exit


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


# ------------------------------------------------------- Kringel-stub departure
# A synthetic b-like ending: rise, small closing loop (the Kringel) whose
# stub crosses the loop's own entry flank on the way out, tip rising above
# the knot. Knot at ~(0.67, 0.74), loop top 0.9, stub tip 0.95.
_KRINGEL_STROKE = [(0.0, 0.0), (0.7, 0.7), (0.55, 0.9), (0.4, 0.8), (0.55, 0.62), (0.9, 0.95)]


def _compose_pair(centerline: list[tuple[float, float]], base: str) -> dict:
    slots = [
        GlyphSlot(key=base, text=base, position="initial", ligature=False, space=False),
        GlyphSlot(key="n", text="n", position="final", ligature=False, space=False),
    ]
    payloads = {base: _payload(centerline), "n": _payload([(0.0, 0.1), (0.15, 0.4), (0.3, 0.7)])}
    return compose_word(slots, payloads)


def test_kringel_stub_is_cut_in_bound_context() -> None:
    composed = _compose_pair(_KRINGEL_STROKE, "b")
    glyph = composed["items"][0]["centerline"]
    # The stub after the knot is table form: the stroke now ends AT the
    # loop's self-crossing, below the loop top — the tip at 0.95 is gone.
    assert glyph[-1][1] < 0.8
    assert max(y for _, y in glyph) < 0.95 - 1e-6
    assert math.isclose(glyph[-1][1], 0.736, abs_tol=0.02)


def test_kringel_stub_survives_word_finally() -> None:
    slot = GlyphSlot(key="b", text="b", position="final", ligature=False, space=False)
    composed = compose_word([slot], {"b": _payload(_KRINGEL_STROKE)})
    glyph = composed["items"][0]["centerline"]
    # Unbound, the chart form keeps its finishing stub (like LOOP_EXIT).
    assert glyph[-1][1] > 0.9


def test_kringel_cut_rejects_a_low_bowl_crossing() -> None:
    low = [(x, y - 0.45) for x, y in _KRINGEL_STROKE]
    composed = _compose_pair(low, "b")
    glyph = composed["items"][0]["centerline"]
    # Knot below KRINGEL_CROSS_MIN_Y: a bowl form, not a Kringel — no cut.
    assert math.isclose(glyph[-1][1], 0.5, abs_tol=1e-6)


def test_kringel_cut_only_for_the_enumerated_bases() -> None:
    composed = _compose_pair(_KRINGEL_STROKE, "m")
    glyph = composed["items"][0]["centerline"]
    # Same geometry under a non-Kringel base keeps its stroke untouched.
    assert glyph[-1][1] > 0.9


def test_kringel_cut_applies_to_the_capital_b() -> None:
    """B closes its lower bowl in the same Kringel (Korb #8 follow-up): bound,
    the stub is cut at the knot exactly like b's, so the join departs level
    instead of cresting a wave off the ~49° chart stub."""
    composed = _compose_pair(_KRINGEL_STROKE, "B")
    glyph = composed["items"][0]["centerline"]
    assert glyph[-1][1] < 0.8
    assert max(y for _, y in glyph) < 0.95 - 1e-6
    assert math.isclose(glyph[-1][1], 0.736, abs_tol=0.02)


def test_kringel_stub_survives_word_finally_on_the_capital_b() -> None:
    slot = GlyphSlot(key="B", text="B", position="final", ligature=False, space=False)
    composed = compose_word([slot], {"B": _payload(_KRINGEL_STROKE)})
    glyph = composed["items"][0]["centerline"]
    # Unbound, the capital keeps its full chart form like the lowercase bases.
    assert glyph[-1][1] > 0.9
