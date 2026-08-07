"""M4 fit routine: template → instance, on the synthetic chart.

The synthetic glyph is a straight vertical bar (see conftest). A template
traced down that bar should re-fit to its own skeleton with near-zero residual;
a perturbed template should be pulled back toward the skeleton without breaking
topology; and a higher regularisation weight should hold the template closer to
its canonical shape.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

from core.chart import crop_with_mask, load_chart_grayscale
from core.extract import binarize_adaptive, skeleton_and_width
from core.fit import (
    DEFAULT_HINGE_TAU_UNITS,
    _bilinear_with_grad,
    _hinge_term,
    fit_glyph_to_crop,
    fit_template_to_instance,
)
from core.geometry import bilinear
from core.pipeline import canonical_from_path


def _vertical_stylus_path(num: int = 40, x_global: int = 400) -> list[dict]:
    return [
        {"x": float(x_global), "y": float(200 + 400 * i / (num - 1)), "pressure": 0.5, "t": float(i)}
        for i in range(num)
    ]


def _two_stroke_path(num: int = 10) -> list[dict]:
    """Two separate downstrokes on the synthetic bar, pen lifted between them."""
    first = [{"x": 400.0, "y": float(210 + 180 * i / (num - 1)), "pressure": 0.5, "t": float(i)} for i in range(num)]
    first[-1]["pen_up"] = True
    second = [
        {"x": 400.0, "y": float(410 + 180 * i / (num - 1)), "pressure": 0.5, "t": float(num + i)} for i in range(num)
    ]
    return first + second


def _canonical_on_synthetic(chart_path, bbox, n_anchors: int = 16) -> dict:
    return canonical_from_path(
        raw_path=_vertical_stylus_path(), bbox=bbox, chart_path=chart_path, glyph="l", n_anchors=n_anchors
    )


def _crop_skeleton(chart_path, bbox):
    chart_gray = load_chart_grayscale(chart_path)
    crop = crop_with_mask(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, width_map = skeleton_and_width(mask)
    return skel, width_map


def test_identity_refit_has_small_residual(synthetic_chart_path, synthetic_bbox):
    """Fitting a canonical back to the crop it was traced from converges tight."""
    canon = _canonical_on_synthetic(synthetic_chart_path, synthetic_bbox)
    out = fit_glyph_to_crop(canon, synthetic_bbox, synthetic_chart_path)
    # Skeleton of a 16px bar; the traced centerline already sits on it, so the
    # fit's geometry residual must be a small fraction of the x-height (100px).
    assert out["fit"]["geo_rmse_px"] < 3.0
    assert out["fit"]["success"] is True
    # Topology preserved: same anchor count, ordering monotonic in y (the bar
    # goes top→bottom, so template-y is decreasing along the path).
    assert len(out["anchors"]) == len(canon["anchors"])
    ys = [a[1] for a in out["anchors"]]
    assert ys[0] > ys[-1]


def test_perturbed_template_is_pulled_back(synthetic_chart_path, synthetic_bbox):
    """A template shifted off the skeleton fits back toward it (residual drops)."""
    canon = _canonical_on_synthetic(synthetic_chart_path, synthetic_bbox)
    skel, width_map = _crop_skeleton(synthetic_chart_path, synthetic_bbox)

    anchors = np.asarray(canon["anchors"], dtype=float)
    half_widths = np.asarray(canon["half_widths"], dtype=float)
    # Shove every anchor 0.4 x-heights to the right of the real stroke.
    perturbed = anchors.copy()
    perturbed[:, 0] += 0.4

    result = fit_template_to_instance(
        perturbed,
        half_widths,
        skel,
        width_map,
        unit_px=100.0,
        baseline_y_px=synthetic_bbox["baseline_y"] - synthetic_bbox["y0"],
        x_origin_px=0.0,  # disable auto-centroid so the perturbation really bites
        lambda_reg=0.05,
    )
    meta = result.fit_meta
    assert meta["geo_rmse_px"] < meta["geo_rmse_px_initial"]
    # The fit should recover most of the offset — final residual well under the
    # ~40px it started at.
    assert meta["geo_rmse_px"] < 8.0


def test_regularisation_limits_deformation(synthetic_chart_path, synthetic_bbox):
    """Higher lambda_reg holds anchors closer to the canonical (less displacement)."""
    canon = _canonical_on_synthetic(synthetic_chart_path, synthetic_bbox)
    skel, width_map = _crop_skeleton(synthetic_chart_path, synthetic_bbox)
    anchors = np.asarray(canon["anchors"], dtype=float)
    half_widths = np.asarray(canon["half_widths"], dtype=float)
    perturbed = anchors.copy()
    perturbed[:, 0] += 0.4

    common = {
        "skel": skel,
        "width_map": width_map,
        "unit_px": 100.0,
        "baseline_y_px": synthetic_bbox["baseline_y"] - synthetic_bbox["y0"],
        "x_origin_px": 0.0,
    }
    loose = fit_template_to_instance(perturbed, half_widths, lambda_reg=0.01, **common)
    tight = fit_template_to_instance(perturbed, half_widths, lambda_reg=5.0, **common)

    assert tight.fit_meta["reg_energy"] <= loose.fit_meta["reg_energy"]
    # And the loose fit lands closer to the skeleton (lower geometry residual).
    assert loose.fit_meta["geo_rmse_px"] <= tight.fit_meta["geo_rmse_px"] + 1e-6


def _distance_field_to_line(diagonal: bool = False, size: int = 60) -> np.ndarray:
    """EDT to a single skeleton line — a stand-in for the fit's `dist_smooth`.

    A vertical line gives a known pull direction (distance == |x − 30|); the
    diagonal variant is used where the y-component of the gradient has to be
    exercised too, which a y-invariant field cannot do.
    """
    skel = np.zeros((size, size), dtype=bool)
    if diagonal:
        skel[np.arange(size), np.arange(size)] = True
    else:
        skel[:, size // 2] = True
    return distance_transform_edt(~skel).astype(float)


def test_hinge_is_bit_exactly_free_inside_the_band():
    """A sample within tau costs exactly 0.0 — energy AND gradient.

    The whole design rests on this: because a compliant sample contributes a
    HARD zero rather than a small number, `hinge_weight` can be raised until the
    term acts as a constraint on the outliers without taxing an honest fit
    anywhere. A merely tiny contribution would scale with the weight and turn
    the hinge back into the sort of global tax that lost against the measured
    ink (docs/reference/qualitaetsmetrik.md §7).
    """
    field = _distance_field_to_line()
    tau_px = 5.0
    unit_sq = 100.0**2
    px = np.array([27.3, 29.1, 30.0, 31.7, 33.9])
    py = np.array([10.4, 20.6, 30.2, 40.8, 49.1])
    d, d_dx, d_dy = _bilinear_with_grad(field, px, py)
    assert d.max() < tau_px  # precondition of the property under test
    assert np.abs(d_dx).max() > 0.5  # …and the gradient it is multiplied by is NOT zero

    e_hinge, g_px, g_py = _hinge_term(d, d_dx, d_dy, tau_px, unit_sq)
    assert e_hinge == 0.0
    assert np.array_equal(g_px, np.zeros_like(g_px))
    assert np.array_equal(g_py, np.zeros_like(g_py))


def test_hinge_weight_does_not_move_a_compliant_fit(synthetic_chart_path, synthetic_bbox):
    """A fit that never leaves the band is identical at weight 0 and at 1e6.

    The end-to-end form of the zero-cost property: on the synthetic bar the
    template sits on the ink, so every sample stays far inside tau and the term
    must be invisible — not "almost", but to the last bit, because the objective
    and its gradient are bit-identical along the whole L-BFGS-B trajectory.
    """
    canon = _canonical_on_synthetic(synthetic_chart_path, synthetic_bbox)
    skel, width_map = _crop_skeleton(synthetic_chart_path, synthetic_bbox)
    anchors = np.asarray(canon["anchors"], dtype=float)
    half_widths = np.asarray(canon["half_widths"], dtype=float)

    common = {
        "skel": skel,
        "width_map": width_map,
        "unit_px": 100.0,
        "baseline_y_px": synthetic_bbox["baseline_y"] - synthetic_bbox["y0"],
    }
    off = fit_template_to_instance(anchors, half_widths, hinge_weight=0.0, **common)
    on = fit_template_to_instance(anchors, half_widths, hinge_weight=1e6, **common)

    # Precondition: the fitted centerline really is inside the tolerance band.
    edt = distance_transform_edt(~skel).astype(float)
    sample_d = bilinear(edt, off.fitted_polyline_px[:, 0], off.fitted_polyline_px[:, 1])
    assert sample_d.max() < DEFAULT_HINGE_TAU_UNITS * 100.0

    assert np.array_equal(on.anchors, off.anchors)
    assert np.array_equal(on.fitted_polyline_px, off.fitted_polyline_px)
    assert on.fit_meta["geo_rmse_px"] == off.fit_meta["geo_rmse_px"]


def test_hinge_gradient_matches_finite_differences():
    """The hinge's analytic gradient is exact where the term actually bites.

    It enters an L-BFGS-B objective whose line search requires function and
    gradient to agree to machine precision (see the `core.fit` module header);
    an approximate gradient would not fail loudly, it would quietly stall the
    fit. Checked on a mix of violating and compliant samples, so both branches
    of the ``max(0, ·)`` are exercised in one call.
    """
    field = _distance_field_to_line(diagonal=True)
    tau_px = 4.0
    unit_sq = 100.0**2
    px = np.array([12.37, 20.63, 30.41, 41.29, 52.11])
    py = np.array([9.23, 18.47, 29.61, 36.19, 45.83])

    def energy(qx: np.ndarray, qy: np.ndarray) -> float:
        d_, ddx_, ddy_ = _bilinear_with_grad(field, qx, qy)
        return _hinge_term(d_, ddx_, ddy_, tau_px, unit_sq)[0]

    d, d_dx, d_dy = _bilinear_with_grad(field, px, py)
    violating = d > tau_px
    assert violating.any() and not violating.all()
    _, g_px, g_py = _hinge_term(d, d_dx, d_dy, tau_px, unit_sq)

    h = 1e-5
    num_px = np.zeros_like(px)
    num_py = np.zeros_like(py)
    for i in range(len(px)):
        up, down = px.copy(), px.copy()
        up[i] += h
        down[i] -= h
        num_px[i] = (energy(up, py) - energy(down, py)) / (2.0 * h)
        up, down = py.copy(), py.copy()
        up[i] += h
        down[i] -= h
        num_py[i] = (energy(px, up) - energy(px, down)) / (2.0 * h)

    scale = max(float(np.abs(g_px).max()), float(np.abs(g_py).max()))
    assert scale > 0.0
    assert float(np.abs(num_px - g_px).max()) / scale < 1e-6
    assert float(np.abs(num_py - g_py).max()) / scale < 1e-6


def test_hinge_pulls_a_violating_sample_toward_the_ink():
    """The term must MOVE the offender, not merely price it.

    A sample parked in blank paper sees a strictly decreasing energy as it walks
    back toward the skeleton, and a gradient pointing away from the ink (so
    gradient descent walks it back) — until it enters the tolerance band, where
    the term goes silent.
    """
    field = _distance_field_to_line()
    tau_px = 5.0
    unit_sq = 100.0**2
    py = np.array([25.5])

    energies = []
    for offset in (20.0, 15.0, 10.0, 7.0, 5.5):  # px to the right of the line at x = 30
        d, d_dx, d_dy = _bilinear_with_grad(field, np.array([30.0 + offset]), py)
        e_hinge, g_px, _ = _hinge_term(d, d_dx, d_dy, tau_px, unit_sq)
        energies.append(e_hinge)
        # Positive d(e)/d(px) on the right-hand side: descent moves it left, onto the ink.
        assert g_px[0] > 0.0
    assert all(later < earlier for earlier, later in zip(energies[:-1], energies[1:], strict=True))

    d_in, dx_in, dy_in = _bilinear_with_grad(field, np.array([32.5]), py)
    e_in, gx_in, _ = _hinge_term(d_in, dx_in, dy_in, tau_px, unit_sq)
    assert e_in == 0.0
    assert gx_in[0] == 0.0


def test_multi_stroke_fit_carries_stroke_starts(synthetic_chart_path, synthetic_bbox):
    """A two-stroke canonical fits with the strokes kept separate in the overlay."""
    canon = canonical_from_path(
        raw_path=_two_stroke_path(), bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="u", n_anchors=20
    )
    out = fit_glyph_to_crop(canon, synthetic_bbox, synthetic_chart_path)
    # Two strokes → two polyline segments the frontend can draw without bridging.
    assert len(out["polyline_stroke_starts"]) == 2
    assert out["polyline_stroke_starts"][0] == 0
    # Canonical + fitted overlays stay length-aligned so the split lines up.
    assert len(out["fitted_polyline_px"]) == len(out["canonical_polyline_px"]) > 0


def test_fit_returns_library_entry_shape(synthetic_chart_path, synthetic_bbox):
    """The high-level fit yields a §3-schema entry plus overlay polylines."""
    canon = _canonical_on_synthetic(synthetic_chart_path, synthetic_bbox)
    out = fit_glyph_to_crop(canon, synthetic_bbox, synthetic_chart_path)
    for key in ("glyph", "advance", "anchors", "half_widths", "entry", "exit_pt", "fit"):
        assert key in out
    assert out["glyph"] == "l"
    assert len(out["half_widths"]) == len(out["anchors"])
    # Measured half-widths positive and sane (16px bar → half ≈ 8px ≈ 0.08 unit).
    assert min(out["half_widths"]) > 0.0
    assert max(out["half_widths"]) < 0.5
    # Overlay polylines present for the crop · canonical · fit visual check.
    assert len(out["fitted_polyline_px"]) == len(out["canonical_polyline_px"]) > 0
    assert len(out["skeleton_polyline_px"]) > 0
