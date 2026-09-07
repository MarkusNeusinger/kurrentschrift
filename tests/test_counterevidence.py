"""Pen deconvolution at a counter (`tools.pairlab.counterevidence`, R4).

The load-bearing test is the synthetic one, and it is deliberately the SAME
fixture R3 and R3c were measured on (`tests/test_zweizuege.py`,
`tests/test_counterfield.py`): a counter of known width painted by a pen of
known half width, so the radius the corrected evidence has to carry is
arithmetic rather than a measurement. A circular centreline of radius `r`
stroked at `w_pen` leaves a counter of radius `r − w_pen`, and the level set one
pen half width outside that counter is the circle of radius `r` again — so the
correction has a closed-form answer and the test does not have to trust an
implementation to state one.

What separates this arm from R3c is the CHANNEL, so the identity tests carry
that: the arm off is the very same case object, and a skeleton that already
keeps its distance is returned untouched.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from tools.pairlab.counterevidence import (
    REFUSAL_ALREADY_CLEAR,
    REFUSAL_NO_BAND,
    REFUSAL_NO_MASK,
    REFUSAL_NO_TARGET,
    REFUSAL_NOTHING_CORRECTED,
    CounterEvidenceOptions,
    counter_evidence_case,
    unfold_case_evidence,
    unfold_pen_at_counter,
)


XH_PX = 100.0
BASELINE_ROW = 300.0
W_PEN = 0.0968  # the plate's own half width, the module's default
CENTRE_UNITS = (1.0, 0.5)
LOOP_RADIUS = 0.25  # the pen path the synthetic plate was written with
LUMP_AXIS_RADIUS = 0.20  # what `skeletonize` finds instead — H0 of #551
CROP = (400, 250)


def _px(x_units: float, y_units: float) -> tuple[float, float]:
    return x_units * XH_PX, BASELINE_ROW - y_units * XH_PX


def _radius_map() -> np.ndarray:
    cx, cy = _px(*CENTRE_UNITS)
    yy, xx = np.mgrid[0 : CROP[0], 0 : CROP[1]]
    return np.hypot(xx - cx, yy - cy)


def _circle(radius: float, n: int = 260) -> np.ndarray:
    """Slightly more than one turn, so the path crosses itself instead of meeting."""
    ang = np.linspace(np.pi, 3.2 * np.pi, n)
    return np.stack([CENTRE_UNITS[0] + radius * np.cos(ang), CENTRE_UNITS[1] + radius * np.sin(ang)], axis=1)


def _annulus_mask(loop_radius: float = LOOP_RADIUS, half_width: float = W_PEN) -> np.ndarray:
    """The ink a Gleichzug pen leaves running a circle of `loop_radius`."""
    return np.abs(_radius_map() - loop_radius * XH_PX) <= half_width * XH_PX


def _ring_skeleton(radius: float) -> np.ndarray:
    """A one-pixel ring at `radius` x-heights — the axis the mask hands the fit."""
    return np.abs(_radius_map() - radius * XH_PX) <= 0.75


def _items(glyph: str = "testglyph", radius: float = LOOP_RADIUS) -> list[dict]:
    return [{"slot_index": 0, "glyph_key": glyph, "centerline": _circle(radius).tolist()}]


def _catalogue(glyph: str = "testglyph", size_class: str = "mittel", state: str = "offen") -> dict:
    return {glyph: [{"glyph": glyph, "loop": 0, "size_class": size_class, "state": state}]}


def _unfold(**kwargs):
    return unfold_case_evidence(
        skel=kwargs.pop("skel", _ring_skeleton(LUMP_AXIS_RADIUS)),
        mask=kwargs.pop("mask", _annulus_mask()),
        composed_items=kwargs.pop("composed_items", _items()),
        catalogue=kwargs.pop("catalogue", _catalogue()),
        xh_px=XH_PX,
        tx=0.0,
        ty=0.0,
        baseline_row=BASELINE_ROW,
        **kwargs,
    )


def _corrected_radii(skel: np.ndarray, before: np.ndarray) -> np.ndarray:
    """Radii (in x-heights) of the pixels the correction ADDED."""
    return _radius_map()[skel & ~before] / XH_PX


# --------------------------------------------------------------- the geometry


def test_the_level_set_restores_the_pen_radius() -> None:
    """The whole point: the corrected evidence sits where the pen must have run.

    Closed form — counter radius `r − w`, level set one `w` outside it, so the
    added pixels lie on the circle of radius `r` (plus the declared half pixel
    of the raster convention, 0.005 xh at this scale).
    """
    before = _ring_skeleton(LUMP_AXIS_RADIUS)
    skel, report = _unfold(skel=before)
    assert report.applied
    assert [lp.reason for lp in report.loops] == [""]
    radii = _corrected_radii(np.asarray(skel), before)
    assert radii.size > 0
    assert radii.min() == pytest.approx(LOOP_RADIUS, abs=0.02)
    assert radii.max() == pytest.approx(LOOP_RADIUS, abs=0.02)


def test_the_pinched_axis_is_gone_from_the_evidence() -> None:
    """A correction that only ADDED would leave the lump axis pulling as before."""
    before = _ring_skeleton(LUMP_AXIS_RADIUS)
    skel, _report = _unfold(skel=before)
    assert not (np.asarray(skel) & before).any()


def test_the_corrected_evidence_still_encloses_the_counter() -> None:
    """The survival guard's own subject: a band of width one pixel closes.

    Four-connected neighbours of a Euclidean distance field differ by at most
    one, so a background path from inside the counter to the outside has to land
    on the `|φ − target| ≤ ½` band. The guard exists for the cases where the ink
    clip or the radial shadow punches a hole in it, not for this one.
    """
    from tools.pairlab.zweizuege import plate_counters

    skel, report = _unfold()
    assert report.applied
    _labels, holes = plate_counters(np.asarray(skel), min_px=1)
    assert holes, "the corrected skeleton lost its loop"
    cx, cy = _px(*CENTRE_UNITS)
    assert min(np.hypot(h.cx - cx, h.cy - cy) for h in holes) < 2.0


def test_a_skeleton_that_keeps_its_distance_is_untouched() -> None:
    """Inert where it has nothing to say — the third rule, measured."""
    clear = _ring_skeleton(LOOP_RADIUS + 0.12)
    skel, report = _unfold(skel=clear)
    assert not report.applied
    assert [lp.reason for lp in report.loops] == [REFUSAL_ALREADY_CLEAR]
    assert report.reason == REFUSAL_NOTHING_CORRECTED
    assert np.array_equal(np.asarray(skel), clear)


def test_the_ink_runs_out_before_the_pen_path_and_the_loop_says_so() -> None:
    """Never invent ink: a ribbon too thin to carry the pen path refuses, loudly.

    The plate's own ribbon reads locally thinner than a full pen at the tightest
    counters (#551's H0), so this is the failure the clip exists for — and it
    has to name itself rather than quietly leave the evidence half corrected.
    """
    thin = np.abs(_radius_map() - LOOP_RADIUS * XH_PX) <= 0.3 * W_PEN * XH_PX
    before = _ring_skeleton(LOOP_RADIUS) & thin
    skel, report = _unfold(skel=before, mask=thin)
    assert [lp.reason for lp in report.loops] == [REFUSAL_NO_BAND]
    assert report.reason == REFUSAL_NOTHING_CORRECTED
    assert np.array_equal(np.asarray(skel), before)


def test_only_the_pinched_arc_moves() -> None:
    """The radial shadow: the tight side of an eccentric loop moves, the wide one not.

    The skeleton runs at `25 + 8·cos θ` pixels, so it crosses the target level
    smoothly instead of jumping — an arc that jumps would break its own loop and
    be reverted by the guard, which is a different reading than this one.
    """
    cx, cy = _px(*CENTRE_UNITS)
    yy, xx = np.mgrid[0 : CROP[0], 0 : CROP[1]]
    r = np.hypot(xx - cx, yy - cy)
    theta = np.arctan2(yy - cy, xx - cx)
    before = np.abs(r - (25.0 + 8.0 * np.cos(theta))) <= 0.75
    skel, report = _unfold(skel=before)
    assert report.applied
    moved = np.asarray(skel) != before
    # cos θ ≥ 0.1 is the wide side: there the skeleton already runs at 25.8 px
    # or more, past the 10.18 px level the correction aims at.
    assert moved[np.cos(theta) < 0.0].any()
    assert not moved[np.cos(theta) > 0.2].any()


def test_the_raw_geometry_needs_no_catalogue() -> None:
    """`unfold_pen_at_counter` is pure raster geometry — a synthetic blob calls it."""
    ink = _annulus_mask()
    counter = _radius_map() < (LOOP_RADIUS - W_PEN) * XH_PX
    before = _ring_skeleton(LUMP_AXIS_RADIUS)
    out, dropped, added, clipped = unfold_pen_at_counter(before, ink, counter, target_px=W_PEN * XH_PX + 0.5)
    assert dropped == int(before.sum())
    assert added > 0
    assert clipped == 0
    assert _corrected_radii(out, before).mean() == pytest.approx(LOOP_RADIUS, abs=0.02)


# ------------------------------------------------------------ scope, refusals


@pytest.mark.parametrize(
    ("field_name", "value"),
    [("states", ("offen", "gelegentlich")), ("size_classes", ("mitel",)), ("states", ()), ("size_classes", ())],
)
def test_an_unknown_or_empty_class_fails_instead_of_narrowing_silently(field_name: str, value: tuple) -> None:
    with pytest.raises(ValueError):
        CounterEvidenceOptions(**{field_name: value})


def test_a_loop_the_catalogue_does_not_hold_open_is_out_of_scope() -> None:
    for state in ("wechselnd", "punkt"):
        skel, report = _unfold(catalogue=_catalogue(state=state))
        assert not report.applied
        assert report.reason == REFUSAL_NO_TARGET
        assert np.array_equal(np.asarray(skel), _ring_skeleton(LUMP_AXIS_RADIUS))


def test_a_large_counter_is_out_of_scope() -> None:
    """R3's classes, kept — so this converts the placement and not the scope."""
    _skel, report = _unfold(catalogue=_catalogue(size_class="gross"))
    assert report.reason == REFUSAL_NO_TARGET


def test_no_mask_is_a_refusal_and_not_a_crash() -> None:
    skel, report = _unfold(mask=None)
    assert skel is None or np.array_equal(np.asarray(skel), _ring_skeleton(LUMP_AXIS_RADIUS))
    assert report.reason == REFUSAL_NO_MASK


# --------------------------------------------------------------- the identity


@dataclass
class _Case:
    skel: np.ndarray | None
    mask: np.ndarray | None
    origin: str = "fixture:suetterlin-1922"


@dataclass
class _Result:
    composed: dict
    xh_px: float
    baseline_row: float
    registration: dict


def test_the_arm_off_is_the_same_object() -> None:
    """`options=None` is the identity every default follower run relies on."""
    case = _Case(skel=_ring_skeleton(LUMP_AXIS_RADIUS), mask=_annulus_mask())
    result = _Result(
        composed={"items": _items()}, xh_px=XH_PX, baseline_row=BASELINE_ROW, registration={"tx": 0.0, "ty": 0.0}
    )
    out, report = counter_evidence_case(case, result, None)
    assert out is case
    assert report is None


def test_a_case_from_another_hand_is_refused_by_name() -> None:
    case = _Case(skel=_ring_skeleton(LUMP_AXIS_RADIUS), mask=_annulus_mask(), origin="fixture:loth-1866")
    result = _Result(
        composed={"items": _items()}, xh_px=XH_PX, baseline_row=BASELINE_ROW, registration={"tx": 0.0, "ty": 0.0}
    )
    out, report = counter_evidence_case(case, result, CounterEvidenceOptions())
    assert out is case
    assert "another hand" in report.reason
