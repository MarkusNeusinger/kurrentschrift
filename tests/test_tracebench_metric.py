"""Tests for the trace bench's distance measures (`tools.tracebench.metric`).

Pure geometry in, pure geometry out — no fixtures, no DB, no network. The suite
is built around the properties the bench's conclusions rest on rather than
around lines of code: the headline must be a per-point distance (independent of
how long the word is and of how densely it was sampled), the AIoU must react to
a defect that a per-point error cannot see, and the two chamfer halves must stay
apart so a missing stroke shows up in exactly one of them.
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import binary_dilation

from tools.tracebench import metric
from tools.tracebench.metric import aiou, chamfer, dtw, rasterise_strokes, resample_by_step


def _line(n: int, x0: float = 0.0, x1: float = 1.0, y: float = 0.0) -> np.ndarray:
    return np.column_stack([np.linspace(x0, x1, n), np.full(n, y)])


def _naive_dtw_cost(a: np.ndarray, b: np.ndarray) -> float:
    """The textbook nested-loop DP — the reference the vectorised row must match."""
    n, m = len(a), len(b)
    d = np.full((n, m), np.inf)
    for i in range(n):
        for j in range(m):
            local = float(np.hypot(*(a[i] - b[j])))
            if i == 0 and j == 0:
                d[i, j] = local
            elif i == 0:
                d[i, j] = local + d[i, j - 1]
            elif j == 0:
                d[i, j] = local + d[i - 1, j]
            else:
                d[i, j] = local + min(d[i - 1, j], d[i, j - 1], d[i - 1, j - 1])
    return float(d[-1, -1])


# ------------------------------------------------------------ the purity clause


def test_the_ruler_imports_nothing_from_the_engine_it_grades() -> None:
    """`metric.py` may import numpy and scipy and NOTHING of this project.

    A ruler that imports `core` could be changed by a change to the thing it
    measures. Parsing the file is the only check that cannot be satisfied by a
    lazy import inside a function.
    """
    tree = ast.parse(Path(metric.__file__).read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "no relative imports either — the module stands alone"
            roots.add((node.module or "").split(".")[0])
    assert roots <= {"__future__", "dataclasses", "numpy", "scipy"}
    assert not roots & {"core", "api", "app", "tools"}


# --------------------------------------------------------------- the resampling


def test_resampling_keeps_the_endpoints_exactly() -> None:
    pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [3.0, 1.0]])
    out = resample_by_step(pts, 0.25)
    assert out[0] == pytest.approx(pts[0], abs=0.0)
    assert out[-1] == pytest.approx(pts[-1], abs=0.0)
    assert len(out) == 4 / 0.25 + 1  # total arc 4.0
    steps = np.hypot(*np.diff(out, axis=0).T)
    assert steps.max() - steps.min() < 1e-9  # …and the spacing is uniform


def test_a_degenerate_polyline_resamples_to_its_two_endpoints() -> None:
    """Zero arc: a stray tap, or a stroke whose points all round onto one place."""
    assert resample_by_step(np.array([[1.0, 2.0], [1.0, 2.0], [1.0, 2.0]]), 0.1).tolist() == [[1.0, 2.0], [1.0, 2.0]]
    assert resample_by_step(np.array([[4.0, 5.0]]), 0.1).tolist() == [[4.0, 5.0], [4.0, 5.0]]


# ---------------------------------------------------------------------- the DTW


def test_a_trace_against_itself_costs_nothing() -> None:
    """The identity gate in miniature — if this moves, no other number is readable."""
    a = np.column_stack([np.linspace(0.0, 2.0, 60), np.sin(np.linspace(0.0, 3.0, 60))])
    result = dtw(a, a)
    assert result.mean_xh == pytest.approx(0.0, abs=1e-12)
    assert result.path_len == len(a)  # the diagonal, one pair per point
    assert result.max_absorption == 1


def test_a_pure_translation_costs_exactly_its_own_distance() -> None:
    """Offset perpendicular to the path, so no along-path shift can undercut it.

    Every local distance is then at least `d`, with equality only on the
    diagonal: the optimal path is the diagonal, its length is the point count,
    and the normalised cost is the offset itself. That is the whole claim of the
    headline's unit — `dtw_xh` is a distance in x-heights, not a sum.
    """
    a = _line(200)
    d = 0.07
    result = dtw(a, a + np.array([0.0, d]))
    assert result.mean_xh == pytest.approx(d, abs=1e-12)


def test_the_vectorised_row_reproduces_the_textbook_dp() -> None:
    """The running-minimum unroll is an optimisation, not a different metric."""
    rng = np.random.default_rng(7)
    a, b = rng.normal(size=(37, 2)), rng.normal(size=(53, 2))
    result = dtw(a, b)
    assert result.mean_xh * result.path_len == pytest.approx(_naive_dtw_cost(a, b), rel=1e-12)


def test_the_headline_does_not_move_with_the_sampling_density() -> None:
    """Same geometry, same defect, 100 points and 4000 points — same number.

    Length normalisation by the warping path is what buys this: a denser
    sampling lengthens the path and the cost in the same proportion.
    """
    coarse, dense = _line(100), _line(4000)
    d = 0.05
    sparse_result = dtw(coarse, coarse + np.array([0.0, d]))
    dense_result = dtw(dense, dense + np.array([0.0, d]))
    assert sparse_result.mean_xh == pytest.approx(dense_result.mean_xh, abs=1e-6)
    assert dense_result.path_len > 10 * sparse_result.path_len  # …while the SUM grew 40-fold


def test_a_longer_word_with_the_same_error_reports_the_same_headline() -> None:
    """Twice the word at the same per-point error: mean flat, accumulated cost doubled.

    Constructed rather than asserted in the abstract — the short and the long
    path are sampled at the identical step, so the only difference is how much
    word there is.
    """
    step, d = 0.01, 0.04
    short = resample_by_step(_line(2, 0.0, 1.0), step)
    long = resample_by_step(_line(2, 0.0, 2.0), step)
    short_result = dtw(short, short + np.array([0.0, d]))
    long_result = dtw(long, long + np.array([0.0, d]))
    assert short_result.mean_xh == pytest.approx(long_result.mean_xh, abs=1e-9)
    accumulated = (short_result.mean_xh * short_result.path_len, long_result.mean_xh * long_result.path_len)
    assert accumulated[1] == pytest.approx(2.0 * accumulated[0], rel=0.01)  # up to the shared endpoint


def test_absorption_names_the_singularity_it_is_there_to_watch() -> None:
    """One point of one side swallowing an excursion of the other.

    A DTW that matches an entire loop onto a single reference point reports a
    small distance for a large defect; `max_absorption` is the column that says
    so, and it must count the WORST such absorption on either side.
    """
    flat = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    excursion = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 0.4], [1.0, 0.8], [1.0, 0.4], [1.0, 0.0], [2.0, 0.0]])
    assert dtw(flat, excursion).max_absorption == 5
    assert dtw(excursion, flat).max_absorption == 5  # symmetric: over BOTH sides
    assert dtw(flat, flat).max_absorption == 1


# --------------------------------------------------------------------- the AIoU


def test_a_stroke_covers_its_own_rasterisation_completely() -> None:
    stroke = np.column_stack([np.linspace(5.0, 60.0, 200), 20.0 + 8.0 * np.sin(np.linspace(0.0, 3.0, 200))])
    ink = rasterise_strokes([stroke], (40, 70))
    result = aiou([stroke], ink)
    assert result.value == pytest.approx(1.0)
    assert result.k == 0  # already perfect, so the sweep stops before dilating
    assert result.iou_k0 == pytest.approx(1.0)


def test_ink_the_candidate_never_reaches_scores_zero() -> None:
    stroke = _line(120, 10.0, 90.0, 10.0)
    ink = rasterise_strokes([stroke], (140, 100))
    far = aiou([stroke + np.array([0.0, 120.0])], ink)
    assert far.value == 0.0  # 64 dilations cannot bridge 120 px
    assert far.iou_k0 == 0.0


def test_the_rasteriser_never_bridges_a_pen_lift() -> None:
    """Two strokes with a gap: the line between them was not written and is not drawn."""
    left = _line(30, 5.0, 20.0, 10.0)
    right = _line(30, 40.0, 55.0, 10.0)
    drawn = rasterise_strokes([left, right], (20, 60))
    assert drawn[10, 5:21].all() and drawn[10, 40:56].all()
    assert not drawn[10, 22:39].any()
    assert rasterise_strokes([np.vstack([left, right])], (20, 60))[10, 22:39].all()  # …one stroke would


def test_aiou_sees_a_defect_that_a_per_point_error_cannot(  # noqa: D401 - the recipe IS the test
) -> None:
    """PEN-Net's Fig. 1 argument, reproduced synthetically.

    Recipe: rasterise a smooth stroke and dilate it once — that mask is the
    "ink". The candidate starts as the very same polyline (AIoU 1.0). Then
    displace its SECOND HALF bodily by a fixed magnitude at eight different
    angles. By construction the per-point RMSE between original and distorted is
    identical for every angle (the same points move by the same amount), so a
    point-wise error is blind to which distortion happened — while the AIoU
    drops by half and drops DIFFERENTLY per angle, because leaving the ink
    sideways and sliding along it are not the same defect.
    """
    t = np.linspace(0.0, 1.0, 240)
    base = np.column_stack([20.0 + 160.0 * t, 45.0 + 22.0 * np.sin(2.0 * np.pi * t)])
    ink = binary_dilation(rasterise_strokes([base], (90, 200)), structure=np.ones((3, 3), dtype=bool))
    assert aiou([base], ink).value == pytest.approx(1.0)

    half = len(base) // 2
    values, errors = [], []
    for degrees in range(0, 360, 45):
        shift = 5.0 * np.array([np.cos(np.radians(degrees)), np.sin(np.radians(degrees))])
        distorted = base.copy()
        distorted[half:] += shift
        values.append(aiou([distorted], ink).value)
        errors.append(float(np.sqrt(np.mean(np.sum((distorted - base) ** 2, axis=1)))))

    assert max(errors) - min(errors) < 1e-12  # the per-point error is constant BY CONSTRUCTION
    assert max(values) < 0.8  # …and every distortion costs the AIoU more than 20 %
    assert max(values) - min(values) > 0.1  # …by an amount the point-wise error cannot see


# ------------------------------------------------------------------ the chamfer


def test_identical_point_sets_have_no_chamfer_in_either_direction() -> None:
    pts = np.column_stack([np.linspace(0.0, 1.0, 40), np.zeros(40)])
    assert chamfer(pts, pts) == (0.0, 0.0)


def test_a_missing_branch_inflates_exactly_one_half() -> None:
    """The i-dot case: the reference has a stroke the candidate never wrote.

    Recall (reference -> candidate) must rise, precision (candidate ->
    reference) must not — which is precisely what a symmetric mean would hide,
    and precisely what the mark gate needs to stay readable.
    """
    body = np.column_stack([np.linspace(0.0, 1.0, 40), np.zeros(40)])
    dot = np.column_stack([np.full(5, 0.5), np.full(5, 1.5)])
    reference = np.vstack([body, dot])
    precision, recall = chamfer(body, reference)
    assert precision == pytest.approx(0.0)
    assert recall > 0.15
