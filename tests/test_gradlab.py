"""Unit tests for the pure parts of `tools.pairlab.gradlab`.

The sweep itself needs the frozen fixtures and hours of solving; what is
testable without either is the stranding detector, the sample-window field
read and the stranded-vs-control summary — which is where a silent mistake
would misdirect the whole §11 diagnosis.
"""

from __future__ import annotations

import numpy as np

from tools.pairlab.chain import GRADIENT_TERMS
from tools.pairlab.gradlab import STRANDED_STEP_RATIO, field_at_samples, stranded_anchors, summarize


def _with_forces(row: dict, **overrides: float) -> dict:
    """A summary row carrying every term the objective currently has.

    Derived from `GRADIENT_TERMS` rather than spelled out, so adding a term to
    the objective cannot break these tests for a reason that has nothing to do
    with what they check.
    """
    return {**{f"f_{name}": 0.0 for name in (*GRADIENT_TERMS, "total")}, **row, **overrides}


class _Problem:
    """The three attributes `field_at_samples` reads, and nothing else."""

    def __init__(self, dist: np.ndarray, px: np.ndarray, py: np.ndarray) -> None:
        self.dist_smooth = dist
        self.dist_raw = dist
        self._px, self._py = px, py

    def to_pixels(self, params):  # noqa: ARG002 — the params are already baked in
        return self._px, self._py


def _even_line(k: int = 12) -> np.ndarray:
    return np.column_stack([np.linspace(0.0, 1.0, k), np.zeros(k)])


def test_an_even_chain_has_no_stranding() -> None:
    assert stranded_anchors(_even_line(), [0]) == {}


def test_one_anchor_out_and_back_is_detected_with_both_ratios() -> None:
    """The measured shape of the defect: out one step, back the next."""
    pts = _even_line()
    pts[6, 1] = 1.0  # one anchor leaves the line and the next returns
    marks = stranded_anchors(pts, [0])
    assert set(marks) == {6}
    assert all(r >= STRANDED_STEP_RATIO for r in marks[6])


def test_a_pen_lift_is_never_a_stranding() -> None:
    """A lift is the hand setting down elsewhere, not a discontinuity of a line.

    Same geometry, but the long step declared as a stroke boundary — the rule
    `anchor_spike_ratio` follows, and the reason the term is per stroke.
    """
    left, right = _even_line(8), _even_line(8) + np.array([4.0, 3.0])
    pts = np.vstack([left, right])
    assert stranded_anchors(pts, [0, 8]) == {}
    # …and without the declared lift the same jump is not a one-anchor excursion
    # either: it never comes back, so only ONE of the two ratios is large.
    assert stranded_anchors(pts, [0]) == {}


def test_a_short_stroke_has_no_median_to_judge_against() -> None:
    assert stranded_anchors(np.array([[0.0, 0.0], [1.0, 0.0], [1.1, 0.0]]), [0]) == {}


def test_the_field_is_read_at_the_samples_not_at_a_point() -> None:
    dist = np.zeros((20, 20))
    dist[10, :] = 0.0
    dist[12, :] = 2.0  # a band two rows below the ink
    px = np.array([3.0, 4.0, 5.0, 6.0])
    py = np.array([12.0, 12.0, 12.0, 12.0])
    out = field_at_samples(_Problem(dist, px, py), None, 1, 3)
    assert out["n_samples"] == 2
    assert out["d_smooth_mean_px"] == 2.0
    assert field_at_samples(_Problem(dist, px, py), None, 2, 2) == {"n_samples": 0}


def test_the_summary_separates_the_two_populations() -> None:
    """The comparison IS the finding — a term equal on both sides explains nothing."""
    hot = {"stranded": 1, "delta_units": 0.2, "delta_neighbours_units": 0.05, "d_smooth_mean_px": 3.0}
    cold = {"stranded": 0, "delta_units": 0.02, "delta_neighbours_units": 0.02, "d_smooth_mean_px": 1.0}
    rows = [
        _with_forces(hot, f_geo=4.0),
        _with_forces(hot, f_geo=6.0),
        _with_forces(cold, f_geo=1.0),
        _with_forces(cold, f_geo=1.0),
    ]
    out = summarize(rows)
    assert (out["n_stranded"], out["n_control"]) == (2, 2)
    assert out["terms"]["geo"]["stranded_median"] == 5.0
    assert out["terms"]["geo"]["control_median"] == 1.0
    assert out["stranded_field"]["delta_units"] == 0.2
    assert out["control_field"]["delta_units"] == 0.02


def test_the_summary_survives_a_population_with_no_stranding() -> None:
    """Most solves have none — an empty side must report None, not raise."""
    row = _with_forces({"stranded": 0, "delta_units": 0.01, "delta_neighbours_units": 0.01})
    row.update({f"f_{name}": 1.0 for name in (*GRADIENT_TERMS, "total")})
    out = summarize([row])
    assert out["n_stranded"] == 0
    assert out["terms"]["geo"]["stranded_median"] is None
    assert out["terms"]["geo"]["control_median"] == 1.0
