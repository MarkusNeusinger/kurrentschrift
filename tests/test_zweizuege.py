"""The two-stroke model at the fused loops (`tools.pairlab.zweizuege`).

The load-bearing test is the synthetic one: a counter of KNOWN width painted by
a pen of KNOWN half width, so the aperture the correction has to reach is not a
measurement but arithmetic — `counter + 2·w_pen`. Everything else pins a
refusal, because a correction that quietly does nothing and a correction that
quietly invents a stroke fail in exactly the same silent way.
"""

from __future__ import annotations

import numpy as np
import pytest

from tools.pairlab.zweizuege import (
    REFUSAL_FOREIGN_HAND,
    REFUSAL_NO_COUNTER,
    REFUSAL_NO_MASK,
    REFUSAL_NO_SEPARATION,
    ZweiZuegeOptions,
    correct_word_strokes,
    end_ramp,
    loop_aperture_near,
    plate_counters,
    stroke_separation,
)


XH_PX = 100.0
BASELINE_ROW = 300.0
W_PEN = 0.0968  # the plate's own half width, the module's default
CENTRE_UNITS = (1.0, 0.5)


def _px(x_units: float, y_units: float) -> tuple[float, float]:
    """The frame the correction works in, spelled out once for the fixtures."""
    return x_units * XH_PX, BASELINE_ROW - y_units * XH_PX


def _circle(radius: float, n: int = 260, centre: tuple[float, float] = CENTRE_UNITS) -> np.ndarray:
    """Slightly MORE than one turn, so the path crosses itself instead of meeting.

    A polyline that closes exactly repeats its endpoint, and the two copies then
    take slightly different corrections and pinch the loop at that one point.
    Real pen loops cross; the extra fifth of a turn is what makes this fixture a
    loop of a real stroke rather than a closed curve.
    """
    ang = np.linspace(np.pi, 3.2 * np.pi, n)
    return np.stack([centre[0] + radius * np.cos(ang), centre[1] + radius * np.sin(ang)], axis=1)


def _radial(radius: float, angle: float, outer: float = 0.40) -> np.ndarray:
    rr = np.linspace(outer, radius, 30)
    return np.stack([CENTRE_UNITS[0] + rr * np.cos(angle), CENTRE_UNITS[1] + rr * np.sin(angle)], axis=1)


def _looping_stroke(radius: float) -> list[list[float]]:
    """One open pen stroke: in, once around and a little more, out again."""
    circle = _circle(radius)
    lead_in = _radial(radius, np.pi)
    lead_out = _radial(radius, 1.2 * np.pi)[::-1]
    return [[float(x), float(y)] for x, y in np.vstack([lead_in, circle, lead_out])]


def _annulus_mask(loop_radius: float = 0.25, half_width: float = W_PEN) -> np.ndarray:
    """The ink a Gleichzug pen leaves running a circle of `loop_radius`.

    The capsule union of a circular centreline is an annulus, and its counter is
    the disc of radius `loop_radius - half_width` — so the counter's aperture,
    and therefore the centreline aperture the model must recover, are both known
    in closed form.
    """
    cx, cy = _px(*CENTRE_UNITS)
    yy, xx = np.mgrid[0:400, 0:250]
    r = np.hypot(xx - cx, yy - cy)
    return np.abs(r - loop_radius * XH_PX) <= half_width * XH_PX


def _items(glyph: str = "testglyph", radius: float = 0.25) -> list[dict]:
    return [{"slot_index": 0, "glyph_key": glyph, "centerline": _circle(radius).tolist()}]


def _catalogue(glyph: str = "testglyph", size_class: str = "mittel", state: str = "offen") -> dict:
    return {glyph: [{"glyph": glyph, "loop": 0, "size_class": size_class, "state": state}]}


def _correct(strokes, mask, items, catalogue, **kwargs):
    return correct_word_strokes(
        strokes,
        mask=mask,
        composed_items=items,
        catalogue=catalogue,
        xh_px=XH_PX,
        tx=0.0,
        ty=0.0,
        baseline_row=BASELINE_ROW,
        **kwargs,
    )


# --------------------------------------------------------------- the arithmetic


def test_stroke_separation_is_the_blob_minus_both_capsules():
    # Two strokes 0.30 apart, each 0.0968 half wide, paint 0.30 + 2*0.0968 across.
    assert stroke_separation(0.30 + 2 * W_PEN, W_PEN) == pytest.approx(0.30)


def test_stroke_separation_is_not_positive_for_one_stroke_of_ink():
    """A blob no wider than the pen carries no evidence of a second pass."""
    assert stroke_separation(2 * W_PEN, W_PEN) == pytest.approx(0.0)
    assert stroke_separation(0.15, W_PEN) < 0.0


def test_end_ramp_leaves_and_arrives_flat():
    s = np.linspace(0.0, 1.0, 2001)
    hot = (s > 0.3) & (s < 0.7)
    ramp = end_ramp(hot, s, 0.0725)
    assert ramp[~hot].max() == 0.0
    assert ramp.max() == pytest.approx(1.0, abs=1e-6)
    # C¹ at the seam: the ramp reaches zero with a vanishing first difference —
    # the whole reason it is a smoothstep and not a straight line. A linear
    # ramp would rise by ds/taper here, two orders more.
    edge = np.flatnonzero(hot)[0]
    step = float(s[1] - s[0])
    assert ramp[edge] == 0.0
    assert (ramp[edge + 1] - ramp[edge]) < 0.05 * step / 0.0725


def test_plate_counters_reads_the_hole_and_ignores_the_paper():
    mask = _annulus_mask()
    _labels, counters = plate_counters(mask)
    assert len(counters) == 1
    # The counter is the centreline loop eroded by the pen: 2*(0.25 - 0.0968) xh.
    assert counters[0].aperture_px / XH_PX == pytest.approx(2 * (0.25 - W_PEN), abs=0.02)


def _far_counter(mask: np.ndarray) -> np.ndarray:
    """A second, tiny hole far from the loop, so the WORD has a counter.

    Without it a mask with nothing enclosed leaves early with a word-level
    refusal, and the per-loop branch under test is never reached.
    """
    out = mask.copy()
    out[340:370, 200:230] = True
    out[350:360, 210:220] = False
    return out


def _disc(centre_units: tuple[float, float], radius_units: float) -> np.ndarray:
    cx, cy = _px(*centre_units)
    yy, xx = np.mgrid[0:400, 0:250]
    return np.hypot(xx - cx, yy - cy) <= radius_units * XH_PX


# --------------------------------------------------- the fused blob, recovered


def test_a_tight_trace_is_pushed_to_the_counter_plus_two_pen_widths():
    """The load-bearing case: a known counter, a known pen, an arithmetic target."""
    mask = _annulus_mask()
    strokes = [_looping_stroke(0.18)]
    before = loop_aperture_near(strokes, CENTRE_UNITS)
    corrected, report = _correct(strokes, mask, _items(), _catalogue())

    assert report.applied
    (loop,) = report.loops
    assert loop.corrected, loop.reason
    assert loop.target_d0_units == pytest.approx(2 * 0.25, abs=0.02)
    assert loop.separation_units == pytest.approx(loop.target_d0_units)
    assert before == pytest.approx(2 * 0.18, abs=0.02)
    assert loop.d0_before == pytest.approx(before)
    assert loop.d0_after == pytest.approx(loop.target_d0_units, abs=0.02)
    # And what the whole exercise is for: at the plate's pen the counter is open.
    assert loop.d0_after - 2 * W_PEN > 0.0
    assert loop_aperture_near(corrected, CENTRE_UNITS) == pytest.approx(loop.d0_after)


def test_a_trace_that_already_clears_the_counter_is_left_alone():
    """The d-loop case (#556: „keine Baustelle") — no push where none is due."""
    mask = _annulus_mask()
    strokes = [_looping_stroke(0.27)]
    corrected, report = _correct(strokes, mask, _items(radius=0.27), _catalogue())
    assert not report.applied
    assert report.samples_moved == 0
    assert np.allclose(np.asarray(corrected[0]), np.asarray(strokes[0]))


def test_the_push_only_moves_what_would_ink_the_counter():
    mask = _annulus_mask()
    strokes = [_looping_stroke(0.18)]
    corrected, report = _correct(strokes, mask, _items(), _catalogue())
    moved = np.linalg.norm(np.asarray(corrected[0]) - np.asarray(strokes[0]), axis=1)
    cx, cy = CENTRE_UNITS
    radius = np.hypot(np.asarray(strokes[0])[:, 0] - cx, np.asarray(strokes[0])[:, 1] - cy)
    # Everything further from the counter than a pen width is untouched.
    assert moved[radius > (0.25 - W_PEN) + W_PEN + 0.02].max() < 1e-9
    assert report.samples_moved == int((moved > 1e-9).sum())


# ------------------------------------------------------------- the refusals


def test_a_lump_without_a_counter_is_measured_and_refused():
    """No hole means no distance field to deconvolve — and no invented ductus."""
    strokes = [_looping_stroke(0.18)]
    # A solid blob where the loop is: wide enough for two passes, but the plate
    # closed it, so nothing says which side each pass ran on.
    mask = _far_counter(_disc(CENTRE_UNITS, 0.30))
    corrected, report = _correct(strokes, mask, _items(), _catalogue())
    (loop,) = report.loops
    assert loop.reason == REFUSAL_NO_COUNTER
    assert loop.separation_units is not None
    assert loop.separation_units == pytest.approx(2 * 0.30 - 2 * W_PEN, abs=0.05)
    assert not report.applied
    assert np.allclose(np.asarray(corrected[0]), np.asarray(strokes[0]))


def test_a_lump_thinner_than_the_pen_is_refused_as_one_stroke():
    strokes = [_looping_stroke(0.18)]
    # 0.08 xh of ink across: less than the pen is wide, so not two passes.
    mask = _far_counter(_disc(CENTRE_UNITS, 0.04))
    _corrected, report = _correct(strokes, mask, _items(), _catalogue())
    (loop,) = report.loops
    assert loop.reason == REFUSAL_NO_SEPARATION
    assert loop.separation_units is not None and loop.separation_units <= 0.0


@pytest.mark.parametrize(
    "catalogue",
    [
        {},  # the catalogue does not know the glyph
        _catalogue(state="punkt"),  # a Punktkringel is closed by construction
        _catalogue(state="wechselnd"),  # the plate itself closes it sometimes
        _catalogue(size_class="gross"),  # three quarters of the hole survives any pen
    ],
    ids=["unknown", "punkt", "wechselnd", "gross"],
)
def test_a_loop_outside_the_registered_scope_is_untouched(catalogue):
    mask = _annulus_mask()
    strokes = [_looping_stroke(0.18)]
    corrected, report = _correct(strokes, mask, _items(), catalogue)
    assert report.loops == []
    assert not report.applied
    assert np.allclose(np.asarray(corrected[0]), np.asarray(strokes[0]))


def test_without_a_frozen_mask_the_correction_refuses_rather_than_guesses():
    strokes = [_looping_stroke(0.18)]
    corrected, report = _correct(strokes, None, _items(), _catalogue())
    assert report.reason == REFUSAL_NO_MASK
    assert not report.applied
    assert corrected == strokes


def test_a_foreign_hand_is_refused_by_name():
    """One catalogue, one hand: the sensor's rule, and a correction's all the more."""
    from tools.pairlab.zweizuege import correct_case_strokes

    class _Case:
        origin = "fixture:some-other-hand"
        mask = None

    strokes = [_looping_stroke(0.18)]
    corrected, report = correct_case_strokes(_Case(), None, strokes)
    assert REFUSAL_FOREIGN_HAND in report.reason
    assert not report.applied
    assert corrected == strokes


def test_the_options_ride_into_the_report():
    """A number is only readable next to the configuration that produced it."""
    mask = _annulus_mask()
    opts = ZweiZuegeOptions(half_width_units=0.05)
    _corrected, report = _correct([_looping_stroke(0.18)], mask, _items(), _catalogue(), options=opts)
    assert report.as_dict()["options"]["half_width_units"] == 0.05
