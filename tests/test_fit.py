"""M4 fit routine: template → instance, on the synthetic chart.

The synthetic glyph is a straight vertical bar (see conftest). A template
traced down that bar should re-fit to its own skeleton with near-zero residual;
a perturbed template should be pulled back toward the skeleton without breaking
topology; and a higher regularisation weight should hold the template closer to
its canonical shape.
"""

from __future__ import annotations

import numpy as np

from core.chart import crop_with_mask, load_chart_grayscale
from core.extract import binarize_adaptive, skeleton_and_width
from core.fit import fit_glyph_to_crop, fit_template_to_instance
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
