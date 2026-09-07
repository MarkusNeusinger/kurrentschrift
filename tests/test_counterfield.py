"""The Binnenflächen-Bedingung in the solve (`tools.pairlab.counterfield`, R3c).

The load-bearing test is the synthetic one, and it is deliberately the SAME
fixture R3 was measured on (`tests/test_zweizuege.py`): a counter of known width
painted by a pen of known half width, so the radius the solve has to reach is
arithmetic rather than a measurement — a circular centreline of radius `r`
stroked at `w_pen` leaves a counter of radius `r − w_pen`, so a pen that must
stay `w_pen` clear of that counter has to run at radius `r` again.

What separates this arm from R3 is not the target but the machinery, so two
tests carry that: the solved trace has to be smooth WITHOUT a fade being applied
to it (nothing here tapers anything — the anchors do), and the term has to be
bit-identically absent at weight 0, because that is what makes the base arm of
the round an identity rather than a re-derivation.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.optimize import minimize

from tools.pairlab.chain import ChainSegmentSpec, build_chain_problem, gradient_decomposition
from tools.pairlab.counterfield import (
    REFUSAL_NO_MASK,
    REFUSAL_NO_TARGET,
    CounterFieldOptions,
    build_counter_field,
    signed_counter_distance,
)
from tools.pairlab.follow import COUNTER_WEIGHT_LADDER, FollowWeights, _fields_of


XH_PX = 100.0
BASELINE_ROW = 300.0
W_PEN = 0.0968  # the plate's own half width, the module's default
CENTRE_UNITS = (1.0, 0.5)
LOOP_RADIUS = 0.25  # the pen path the synthetic plate was written with
CROP = (400, 250)


def _px(x_units: float, y_units: float) -> tuple[float, float]:
    return x_units * XH_PX, BASELINE_ROW - y_units * XH_PX


def _circle(radius: float, n: int = 260, centre: tuple[float, float] = CENTRE_UNITS) -> np.ndarray:
    """Slightly more than one turn, so the path crosses itself instead of meeting."""
    ang = np.linspace(np.pi, 3.2 * np.pi, n)
    return np.stack([centre[0] + radius * np.cos(ang), centre[1] + radius * np.sin(ang)], axis=1)


def _annulus_mask(loop_radius: float = LOOP_RADIUS, half_width: float = W_PEN) -> np.ndarray:
    """The ink a Gleichzug pen leaves running a circle of `loop_radius`.

    The capsule union of a circular centreline is an annulus whose counter is
    the disc of radius `loop_radius − half_width`, so both the counter and the
    centreline radius the constraint must restore are known in closed form.
    """
    cx, cy = _px(*CENTRE_UNITS)
    yy, xx = np.mgrid[0 : CROP[0], 0 : CROP[1]]
    r = np.hypot(xx - cx, yy - cy)
    return np.abs(r - loop_radius * XH_PX) <= half_width * XH_PX


def _items(glyph: str = "testglyph", radius: float = LOOP_RADIUS) -> list[dict]:
    return [{"slot_index": 0, "glyph_key": glyph, "centerline": _circle(radius).tolist()}]


def _catalogue(glyph: str = "testglyph", size_class: str = "mittel", state: str = "offen") -> dict:
    return {glyph: [{"glyph": glyph, "loop": 0, "size_class": size_class, "state": state}]}


def _field(**kwargs):
    return build_counter_field(
        mask=kwargs.pop("mask", _annulus_mask()),
        composed_items=kwargs.pop("composed_items", _items()),
        catalogue=kwargs.pop("catalogue", _catalogue()),
        xh_px=XH_PX,
        tx=0.0,
        ty=0.0,
        baseline_row=BASELINE_ROW,
        **kwargs,
    )


def _lump_axis_fields(axis_radius: float = 0.20) -> dict:
    """The ink field a fused loop really hands the solve: the LUMP's axis.

    H0 of #551, in closed form. `skeletonize` on the annulus above does not
    return the pen path at radius 0.25 — between counter and outer edge there is
    less ink than one stroke is thick, so the axis it finds runs too tight. This
    stack puts the geometry term exactly there, which is what makes the test a
    test: the ink pulls the trace INTO the counter and the condition holds it
    out, and the two have to be traded off rather than one of them switched off.
    """
    from scipy.ndimage import distance_transform_edt, gaussian_filter

    cx, cy = _px(*CENTRE_UNITS)
    yy, xx = np.mgrid[0 : CROP[0], 0 : CROP[1]]
    axis = np.abs(np.hypot(xx - cx, yy - cy) - axis_radius * XH_PX) <= 0.75
    dist_raw = distance_transform_edt(~axis).astype(float)
    zeros = np.zeros(CROP)
    return {
        "dist_raw": dist_raw,
        "dist_smooth": gaussian_filter(dist_raw, 1.0),
        "width_raw": zeros,
        "width_smooth": zeros,
        # The axis itself, so the coverage term has a well-defined mean; it is
        # priced out of the objective at weight 0 either way.
        "cov_pts": np.column_stack(np.nonzero(axis)[::-1]).astype(float),
        "crop_shape": CROP,
    }


def _problem(radius: float, *, counter=None, weight: float = 0.0, fields=None):
    """One synthetic letter, at the follower's OWN weights except for the width.

    The Tikhonov weight in particular is the shipped 1.0 rather than a token
    value: a closed loop is free to redistribute its anchors along itself, so a
    solve with a weak prior wanders tangentially whatever term is driving it,
    and a smoothness assertion made there would be about the fixture.
    """
    anchors = _circle(radius, n=60)
    spec = ChainSegmentSpec(
        kind="letter", anchors=anchors, slot_index=0, key="testglyph", half_widths=np.full(len(anchors), W_PEN)
    )
    return build_chain_problem(
        [spec],
        unit_px=XH_PX,
        x_origin_px=0.0,
        baseline_y_px=BASELINE_ROW,
        # No width field in this fixture, so its target would be a constant
        # residual with no gradient — priced out rather than left to confuse.
        width_weight=0.0,
        counter_smooth=None if counter is None else counter.field_px,
        counter_target_px=0.0 if counter is None else counter.target_px,
        counter_weight=weight,
        **(fields if fields is not None else _lump_axis_fields()),
    )


def _sample_radii(problem, params) -> np.ndarray:
    px, py = problem.to_pixels(params)
    cx, cy = _px(*CENTRE_UNITS)
    return np.hypot(px - cx, py - cy) / XH_PX


def _max_turn_deg(problem, params) -> float:
    """The sharpest turn between consecutive samples of the solved trace.

    The blunt instrument on purpose: R3's continuity gate failed because a
    point-wise push concentrated a turn between neighbouring support points, so
    the property to pin here is that nothing of the sort happens when the same
    condition is a term — no fade is applied anywhere in this arm.
    """
    px, py = problem.to_pixels(params)
    d = np.diff(np.column_stack([px, py]), axis=0)
    keep = np.hypot(d[:, 0], d[:, 1]) > 1e-9
    ang = np.degrees(np.arctan2(d[keep, 1], d[keep, 0]))
    turn = np.abs((np.diff(ang) + 180.0) % 360.0 - 180.0)
    return float(turn.max()) if len(turn) else 0.0


# ------------------------------------------------------------------ the field


def test_signed_distance_matches_the_unsigned_one_outside() -> None:
    """Outside a counter the field IS R3's, so the two arms aim at one level set."""
    from scipy.ndimage import distance_transform_edt

    mask = np.zeros((40, 40), dtype=bool)
    mask[18:22, 18:22] = True
    phi = signed_counter_distance(mask)
    unsigned = distance_transform_edt(~mask)
    assert np.allclose(phi[~mask], unsigned[~mask])
    # …and inside it carries on rather than refusing, which is the whole
    # addition: a sample that has wandered into the hole gets a force out.
    assert (phi[mask] < 0.0).all()


def test_the_field_is_built_for_an_offen_counter() -> None:
    counter = _field()
    assert counter.active
    assert counter.target_px == pytest.approx(W_PEN * XH_PX + 0.5)
    row = next(r for r in counter.rows if r.get("target_d0_units") is not None)
    # The plate counter is the disc of radius `loop - w_pen`, so its aperture is
    # twice that, and the expectation the catalogue states adds the pen back.
    assert row["counter_units"] == pytest.approx(2.0 * (LOOP_RADIUS - W_PEN), abs=0.02)
    assert row["target_d0_units"] == pytest.approx(2.0 * LOOP_RADIUS, abs=0.02)


@pytest.mark.parametrize("state", ["wechselnd", "punkt"])
def test_a_loop_the_catalogue_does_not_hold_open_is_out_of_scope(state: str) -> None:
    """Only `offen` binds — the plate closes the other two itself."""
    counter = _field(catalogue=_catalogue(state=state))
    assert not counter.active
    assert counter.reason == REFUSAL_NO_TARGET


def test_a_glyph_outside_the_catalogue_is_untouched() -> None:
    counter = _field(catalogue=_catalogue(glyph="someotherglyph"))
    assert not counter.active
    assert counter.rows == []


def test_a_gross_loop_is_out_of_scope_by_default() -> None:
    """R3's own two classes, and the calibration probe of `sep07` is why.

    A large counter is not satisfied at the base either, so it binds — hardest
    of all, because it is the widest — while buying nothing: three quarters of a
    large hole survives any pen. Reachable as its own arm, not part of this one.
    """
    assert CounterFieldOptions().size_classes == ("klein", "mittel")
    assert not _field(catalogue=_catalogue(size_class="gross")).active
    wider = _field(
        catalogue=_catalogue(size_class="gross"), options=CounterFieldOptions(size_classes=("klein", "mittel", "gross"))
    )
    assert wider.active


def test_no_mask_is_a_refusal_not_a_crash() -> None:
    counter = _field(mask=None)
    assert counter.reason == REFUSAL_NO_MASK


def test_a_plate_without_a_hole_refuses_and_says_so() -> None:
    """A closed lump has no distance field to state the condition against."""
    counter = _field(mask=np.ones(CROP, dtype=bool))
    assert not counter.active
    assert counter.reason == REFUSAL_NO_TARGET


# -------------------------------------------------------------------- the term


def test_at_weight_zero_the_term_is_bit_identically_absent() -> None:
    """The base arm of the round is an identity, not a re-derivation."""
    counter = _field()
    with_field = _problem(0.20, counter=counter, weight=0.0)
    without = _problem(0.20)
    x = np.full_like(with_field.x0, 0.003)
    assert with_field.energy_terms(x) == without.energy_terms(x)
    assert np.array_equal(with_field.objective(x)[1], without.objective(x)[1])


def test_the_gradient_is_the_objectives_own() -> None:
    """L-BFGS-B aborts silently when f and g disagree; check both ways."""
    problem = _problem(0.20, counter=_field(), weight=64.0)
    x = np.full_like(problem.x0, 0.002)
    assert problem.energy_terms(x)["e_counter"] > 0.0
    # The decomposition asserts internally that the split re-adds to the total.
    decomposition = gradient_decomposition(problem, x)
    assert np.any(decomposition["terms"]["counter"] != 0.0)
    f0, grad = problem.objective(x)
    step = 1e-6
    for i in (0, 1, len(x) // 2, len(x) - 1):
        bumped = x.copy()
        bumped[i] += step
        numeric = (problem.objective(bumped)[0] - f0) / step
        assert numeric == pytest.approx(grad[i], rel=2e-3, abs=1e-9)


def test_the_solve_keeps_the_trace_off_the_counter_and_smooth() -> None:
    """The synthetic fused blob: the constraint alone restores the pen radius.

    The trace starts on the lump's axis at radius 0.20 — only 0.047 xh from the
    counter, i.e. violating the condition by half a pen width all the way round
    — and the ink term wants to keep it there. The condition has to win that
    argument by the width of a pen and stop, and it has to get there without a
    fade, an average or a revert, because this arm has none of the three.
    """
    counter = _field()
    fields = _lump_axis_fields()
    base = _problem(0.20, fields=fields)
    arm = _problem(0.20, counter=counter, weight=256.0, fields=fields)
    before = _sample_radii(base, base.x0)
    assert before.max() < LOOP_RADIUS  # the start really does violate everywhere

    solved = {
        name: minimize(p.objective, p.x0, jac=True, method="L-BFGS-B", bounds=p.bounds)
        for name, p in (("base", base), ("arm", arm))
    }
    # The ink alone leaves the trace on the axis it was handed — the deficit
    # every consumer of the skeleton inherits.
    assert _sample_radii(base, solved["base"].x).max() < LOOP_RADIUS - 0.02

    after = _sample_radii(arm, solved["arm"].x)
    # With the condition on, every sample sits at least `w_pen` (plus the
    # declared half pixel) from the counter — for this fixture, back out at the
    # pen's own radius.
    target_units = (counter.target_px - 0.5) / XH_PX + (LOOP_RADIUS - W_PEN)
    assert after.min() > target_units - 0.01
    # …and no further: a constraint stops where it is satisfied. Only a push
    # keeps going, and it is the ink term it stops against, not a cap.
    assert after.max() < target_units + 0.01
    # …and the curve is still a curve — the whole claim of the arm. R3's
    # point-wise push of this size put 147 deg into the continuity sensor; here
    # the displacement is carried by the anchors, so the sharpest turn of the
    # corrected trace does not exceed the base solve's own.
    assert _max_turn_deg(arm, solved["arm"].x) < _max_turn_deg(base, solved["base"].x) + 5.0


def test_a_satisfied_condition_costs_nothing() -> None:
    """A trace already clear of the counter feels no force at all.

    Not a convenience: it is what makes the term a CONSTRAINT rather than a
    pull. Where the condition holds, the objective is the one the base solved,
    down to the packed gradient — so the arm can only ever be about the samples
    that violate it.
    """
    fields = _lump_axis_fields()
    on = _problem(LOOP_RADIUS + 0.05, counter=_field(), weight=256.0, fields=fields)
    off = _problem(LOOP_RADIUS + 0.05, fields=fields)
    assert on.energy_terms(on.x0)["e_counter"] == 0.0
    assert on.energy_terms(on.x0) == off.energy_terms(off.x0)
    assert np.array_equal(on.objective(on.x0)[1], off.objective(off.x0)[1])


# ------------------------------------------------------------- the plumbing


def test_the_field_rides_into_every_round() -> None:
    """`_fields_of` carries the condition forward, so round 2 sees it too."""
    counter = _field()
    problem = _problem(0.20, counter=counter, weight=16.0)
    carried = _fields_of(problem)
    assert carried["counter_target_px"] == pytest.approx(counter.target_px)
    assert np.array_equal(carried["counter_smooth"], problem.counter_smooth)


def test_the_arm_is_off_by_default() -> None:
    weights = FollowWeights()
    assert weights.counter_constraint is False
    assert weights.counter_half_width == pytest.approx(W_PEN)
    assert weights.counter_weight in COUNTER_WEIGHT_LADDER


def test_the_pen_is_the_plates_and_not_a_knob() -> None:
    """A wider pen states a stricter condition — the level set moves with it."""
    wide = _field(options=CounterFieldOptions(half_width_units=2.0 * W_PEN))
    assert wide.target_px == pytest.approx(2.0 * W_PEN * XH_PX + 0.5)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"size_classes": ("mitel",)},  # a typo silently narrows the scope
        {"size_classes": ()},  # an empty list makes the whole arm inert
        {"states": ("offe",)},
        {"states": ()},
    ],
)
def test_an_unknown_class_fails_instead_of_measuring_nothing(kwargs: dict) -> None:
    """The scope is checked, not trusted.

    `catalogue_targets` filters by membership, so an unknown value costs the
    experiment its scope while the artefact still says the counter arm ran — a
    measurement that quietly measures nothing is worse than one that fails.
    """
    with pytest.raises(ValueError):
        CounterFieldOptions(**kwargs)
