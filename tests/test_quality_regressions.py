"""Regression tests for the canonical-quality + fit-robustness diagnosis.

Each test pins one previously-observed failure mode:
* width sampled at the trace point instead of the medial axis (systematic
  thinning, 1px boundary floor when the trace leaves the ink),
* the ±normal ribbon outline folding on loops / losing loop counters,
* the optimiser's evaluation budget masquerading as "not converged",
* a placement offset being unrecoverable because the global translation
  parameter lived on a different scale than the anchor deltas.
"""

from __future__ import annotations

import numpy as np

from core.fit import fit_glyph_to_crop, fit_template_to_instance
from core.pipeline import canonical_from_path
from core.template import capsule_union_rings


def _stylus_path(x_global: float, num: int = 40) -> list[dict]:
    """Straight vertical stylus trace down the synthetic bar at a given x."""
    return [
        {"x": float(x_global), "y": float(200 + 400 * i / (num - 1)), "pressure": 0.5, "t": float(i)}
        for i in range(num)
    ]


def _canonical(chart_path, bbox, x_global: float) -> dict:
    return canonical_from_path(
        raw_path=_stylus_path(x_global), bbox=bbox, chart_path=chart_path, glyph="l", position="initial", n_anchors=24
    )


# ------------------------------------------------------------- width channel


def test_off_center_trace_still_measures_full_width(synthetic_chart_path, synthetic_bbox):
    """A trace 4px off the stroke center must not thin the measured width.

    The bar is 16px wide (half-width 8). Reading the distance transform at the
    trace point would yield ~4px here; projecting onto the medial axis
    recovers the true ~8px.
    """
    canon = _canonical(synthetic_chart_path, synthetic_bbox, x_global=404.0)
    hw_px = np.asarray(canon["trace_meta"]["half_widths_px"])
    assert float(np.median(hw_px)) > 6.5


def test_trace_off_the_ink_does_not_floor_at_boundary(synthetic_chart_path, synthetic_bbox):
    """A trace just outside the ink must not collapse to the ~1px boundary EDT.

    The old nearest-ink fallback returned the EDT of a boundary pixel (~1px)
    for every off-ink anchor — 70% of a real glyph's widths sat exactly on
    that floor. Snapping to the medial axis recovers the stroke's width.
    """
    canon = _canonical(synthetic_chart_path, synthetic_bbox, x_global=412.0)
    hw_px = np.asarray(canon["trace_meta"]["half_widths_px"])
    assert float(np.median(hw_px)) > 6.5


# --------------------------------------------------------------- silhouettes


def test_capsule_union_keeps_loop_counter_open():
    """A closed loop's silhouette must carry a hole ring (the loop counter)."""
    theta = np.linspace(0.0, 2.0 * np.pi, 80)
    rings = capsule_union_rings(np.cos(theta), np.sin(theta), np.full(80, 0.15))
    # Exterior + interior hole; the naive ribbon offset produced one
    # self-intersecting polygon that filled the counter solid.
    assert len(rings) == 2


def test_capsule_union_survives_tight_curvature():
    """Curvature radius below the half-width must not fold into bowties."""
    theta = np.linspace(0.0, np.pi, 40)
    # Radius 0.5 arc drawn with half-width 0.8 — the inner offset of the old
    # ribbon would cross itself; the capsule union is a single valid polygon.
    rings = capsule_union_rings(0.5 * np.cos(theta), 0.5 * np.sin(theta), np.full(40, 0.8))
    assert len(rings) >= 1
    exterior = np.asarray(rings[0])
    assert len(exterior) > 8


# ----------------------------------------------------------------- fit


def test_fit_gradient_matches_finite_differences(synthetic_chart_path, synthetic_bbox):
    """The analytic jacobian must agree with finite differences.

    Wrong gradients would not crash the optimiser — they would silently stall
    it, which is exactly the failure class this rework removes.
    """
    from scipy.optimize import check_grad  # noqa: F401
    from scipy.optimize import minimize as scipy_minimize

    from core.chart import crop_with_mask, load_chart_grayscale
    from core.extract import binarize_adaptive, skeleton_and_width

    canon = _canonical(synthetic_chart_path, synthetic_bbox, x_global=400.0)
    chart_gray = load_chart_grayscale(synthetic_chart_path)
    crop = crop_with_mask(chart_gray, synthetic_bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, width_map = skeleton_and_width(mask)

    captured: dict = {}
    original = scipy_minimize

    def spy(fun, x0, **kwargs):
        captured["fun"] = fun
        captured["x0"] = x0
        return original(fun, x0, **kwargs)

    import core.fit as fit_module

    fit_module.minimize, saved = spy, fit_module.minimize
    try:
        fit_template_to_instance(
            np.asarray(canon["anchors"], dtype=float),
            np.asarray(canon["half_widths"], dtype=float),
            skel,
            width_map,
            unit_px=100.0,
            baseline_y_px=synthetic_bbox["baseline_y"] - synthetic_bbox["y0"],
            x_origin_px=0.0,
        )
    finally:
        fit_module.minimize = saved

    rng = np.random.default_rng(7)
    params = rng.uniform(-0.05, 0.05, size=len(captured["x0"]))
    f0, grad = captured["fun"](params)
    eps = 1e-6
    for idx in rng.choice(len(params), size=10, replace=False):
        step = np.zeros_like(params)
        step[idx] = eps
        f_plus, _ = captured["fun"](params + step)
        f_minus, _ = captured["fun"](params - step)
        fd = (f_plus - f_minus) / (2.0 * eps)
        assert abs(fd - grad[idx]) < 1e-3 * max(1.0, abs(fd)), f"param {idx}: fd={fd}, analytic={grad[idx]}"


def test_translation_perturbation_recovered_by_global_shift(synthetic_chart_path, synthetic_bbox):
    """A pure placement offset is absorbed by tx/ty, not by anchor deformation.

    With the old pixel-scaled translation parameter the optimiser pushed the
    offset into the regularised per-anchor deltas (or stalled); now the
    translation lives in template units and carries no regularisation.
    """
    from core.chart import crop_with_mask, load_chart_grayscale
    from core.extract import binarize_adaptive, skeleton_and_width

    canon = _canonical(synthetic_chart_path, synthetic_bbox, x_global=400.0)
    chart_gray = load_chart_grayscale(synthetic_chart_path)
    crop = crop_with_mask(chart_gray, synthetic_bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, width_map = skeleton_and_width(mask)

    anchors = np.asarray(canon["anchors"], dtype=float)
    perturbed = anchors.copy()
    perturbed[:, 0] += 0.4  # 40px placement error at unit_px=100

    result = fit_template_to_instance(
        perturbed,
        np.asarray(canon["half_widths"], dtype=float),
        skel,
        width_map,
        unit_px=100.0,
        baseline_y_px=synthetic_bbox["baseline_y"] - synthetic_bbox["y0"],
        x_origin_px=0.0,
        # Deliberately the production default — the old code only passed this
        # test at lambda_reg=0.05.
    )
    meta = result.fit_meta
    assert meta["converged"] is True
    assert meta["geo_rmse_px"] < 3.0
    # The offset went into the unregularised global translation: the shape
    # itself barely deformed.
    assert meta["max_anchor_delta"] < 0.15


def test_default_anchor_count_does_not_exhaust_budget(synthetic_chart_path, synthetic_bbox):
    """A 100-anchor fit must converge — the eval budget is no longer binding.

    With finite-difference gradients, 202 parameters exhausted scipy's default
    maxfun=15000 after ~45 iterations and every production fit reported
    "not converged" regardless of its residual.
    """
    canon = canonical_from_path(
        raw_path=_stylus_path(400.0, num=120),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=100,
    )
    out = fit_glyph_to_crop(canon, synthetic_bbox, synthetic_chart_path)
    assert out["fit"]["converged"] is True
    assert out["fit"]["geo_rmse_px"] < 3.0


def test_uncovered_ink_blocks_converged_verdict(synthetic_bbox, tmp_path):
    """A fit that leaves real ink uncovered must not report 'converged'.

    The one-sided geometry residual is blind to this (every template sample
    sits on skeleton); only the coverage residual exposes it — and it must
    gate the verdict, not just be reported.
    """
    import numpy as np
    from PIL import Image

    chart = np.ones((800, 800), dtype=np.float32)
    chart[200:600, 392:408] = 0.05  # the traced bar
    chart[250:550, 460:476] = 0.05  # a second, untraced bar inside the bbox
    path = tmp_path / "two_bars.png"
    Image.fromarray((chart * 255).astype(np.uint8), mode="L").save(path)

    canon = _canonical(str(path), synthetic_bbox, x_global=400.0)
    out = fit_glyph_to_crop(canon, synthetic_bbox, str(path))
    meta = out["fit"]
    # Geometry alone looks fine — the template tracks the first bar's skeleton —
    # but half the ink is uncovered, so the verdict must be negative.
    assert meta["coverage_rmse_px"] > meta["geo_rmse_px"]
    assert meta["converged"] is False


def test_fit_payload_carries_silhouette_and_verdict(synthetic_chart_path, synthetic_bbox):
    """The fit overlay ships the filled silhouette and the honest verdict."""
    canon = _canonical(synthetic_chart_path, synthetic_bbox, x_global=400.0)
    out = fit_glyph_to_crop(canon, synthetic_bbox, synthetic_chart_path)
    meta = out["fit"]
    for key in ("converged", "optimizer_success", "coverage_rmse_px", "n_evaluations"):
        assert key in meta
    # One ring list per pen-stroke, rings hold ≥4 points each.
    assert len(out["fitted_outline_px"]) == len(out["polyline_stroke_starts"])
    assert all(len(ring) >= 4 for stroke in out["fitted_outline_px"] for ring in stroke)
