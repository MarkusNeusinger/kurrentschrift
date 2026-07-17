"""Image-space refinement: boundary loss, optimised widths, cap extension.

Pins the failure modes the refine step exists for: per-anchor EDT width noise
(quantisation + stair-stepping) surviving into the render, stroke caps left
short of the ink by the skeleton's end erosion, crossing blobs inflating
widths, and — the safety net — the analytic gradient agreeing with finite
differences (a wrong gradient stalls L-BFGS-B silently).
"""

from __future__ import annotations

import numpy as np

from core.fit import WIDTH_FLOOR_PX, refine_template_against_crop
from core.pipeline import canonical_from_path


def _stylus_path(x_global: float = 400.0, y0: float = 200.0, y1: float = 600.0, num: int = 40) -> list[dict]:
    return [
        {"x": float(x_global), "y": float(y0 + (y1 - y0) * i / (num - 1)), "pressure": 0.5, "t": float(i)}
        for i in range(num)
    ]


def _canonical(chart_path, bbox, raw_path=None, refine: bool = True) -> dict:
    return canonical_from_path(
        raw_path=raw_path or _stylus_path(), bbox=bbox, chart_path=chart_path, glyph="l", n_anchors=24, refine=refine
    )


def _refine_inputs(chart_path, bbox, canon):
    """(skel, width_map, placement kwargs) for a direct refine call."""
    from core.chart import crop_with_mask, load_chart_grayscale
    from core.extract import binarize_adaptive, skeleton_and_width

    crop = crop_with_mask(load_chart_grayscale(chart_path), bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, width_map = skeleton_and_width(mask)
    tm = canon["trace_meta"]
    kwargs = {
        "unit_px": float(tm["unit_px"]),
        "baseline_y_px": float(tm["baseline_y"] - bbox["y0"]),
        "x_origin_px": float(tm["pixel_anchors"][0][0] - bbox["x0"]),
        "stroke_starts": tm["stroke_starts"],
        "corner_anchors": tm.get("corner_anchors"),
        "crossing_anchors": tm.get("crossing_anchors"),
    }
    return skel, width_map, kwargs


# ------------------------------------------------------------------ de-noising


def test_refine_denoises_width_profile(synthetic_chart_path, synthetic_bbox):
    """Alternating ±1.5px width noise must be smoothed back to the ink's ~8px.

    This is the waviness fix: the boundary term reads the actual ink edge
    (smooth), the curvature regulariser kills the sample-to-sample ripple that
    the median/box filter lets through.
    """
    canon = _canonical(synthetic_chart_path, synthetic_bbox, refine=False)
    skel, width_map, kwargs = _refine_inputs(synthetic_chart_path, synthetic_bbox, canon)

    anchors = np.asarray(canon["anchors"], dtype=float)
    clean = np.asarray(canon["half_widths"], dtype=float)
    noisy = clean + 0.015 * np.where(np.arange(len(clean)) % 2 == 0, 1.0, -1.0)  # ±1.5px at unit=100

    result = refine_template_against_crop(anchors, noisy, skel, width_map, **kwargs)

    refined_px = result.half_widths * 100.0
    interior = refined_px[2:-2]  # caps legitimately adapt to the bar ends
    assert float(interior.std()) < 0.4
    tv_noisy = float(np.abs(np.diff(noisy * 100.0)).sum())
    tv_refined = float(np.abs(np.diff(refined_px)).sum())
    assert tv_refined < tv_noisy / 4.0
    # The bar is 16px wide: refined widths sit near the true 8px half-width.
    assert abs(float(np.median(interior)) - 8.0) < 1.0
    # Width fixing must not have warped the geometry.
    shift = np.hypot(*(result.anchors - anchors).T)
    assert float(shift.max()) < 0.06


# ------------------------------------------------------------------ gradient


def test_refine_gradient_matches_finite_differences(synthetic_chart_path, synthetic_bbox):
    """The refine objective's analytic gradient must agree with finite differences."""
    from scipy.optimize import minimize as scipy_minimize

    canon = _canonical(synthetic_chart_path, synthetic_bbox, refine=False)
    skel, width_map, kwargs = _refine_inputs(synthetic_chart_path, synthetic_bbox, canon)

    captured: dict = {}
    original = scipy_minimize

    def spy(fun, x0, **opts):
        captured.setdefault("fun", fun)
        captured.setdefault("x0", x0)
        return original(fun, x0, **opts)

    import core.fit as fit_module

    fit_module.minimize, saved = spy, fit_module.minimize
    try:
        refine_template_against_crop(
            np.asarray(canon["anchors"], dtype=float),
            np.asarray(canon["half_widths"], dtype=float),
            skel,
            width_map,
            **kwargs,
        )
    finally:
        fit_module.minimize = saved

    rng = np.random.default_rng(11)
    params = rng.uniform(-0.02, 0.02, size=len(captured["x0"]))
    _, grad = captured["fun"](params)
    eps = 1e-6
    for idx in rng.choice(len(params), size=12, replace=False):
        step = np.zeros_like(params)
        step[idx] = eps
        f_plus, _ = captured["fun"](params + step)
        f_minus, _ = captured["fun"](params - step)
        fd = (f_plus - f_minus) / (2.0 * eps)
        assert abs(fd - grad[idx]) < 1e-3 * max(1.0, abs(fd)), f"param {idx}: fd={fd}, analytic={grad[idx]}"


# ------------------------------------------------------------------ caps


def test_refine_extends_caps_to_stroke_ends(synthetic_chart_path, synthetic_bbox):
    """A trace stopping short of the ink end gets its cap pulled to the true end.

    The skeleton erodes round stroke ends by up to the half-width, so the snap
    leaves end anchors inward; only the cap term of the refine sees the real
    ink boundary there.
    """
    short_path = _stylus_path(y0=220.0, y1=580.0)  # bar ink spans y 200..600
    unrefined = _canonical(synthetic_chart_path, synthetic_bbox, raw_path=short_path, refine=False)
    refined = _canonical(synthetic_chart_path, synthetic_bbox, raw_path=short_path, refine=True)

    def cap_reach(canon) -> tuple[float, float]:
        ay = np.asarray(canon["trace_meta"]["pixel_anchors"], dtype=float)[:, 1]
        hw = np.asarray(canon["trace_meta"]["half_widths_px"], dtype=float)
        return float(ay[0] - hw[0]), float(ay[-1] + hw[-1])

    top_unref, bottom_unref = cap_reach(unrefined)
    top_ref, bottom_ref = cap_reach(refined)
    # Strictly closer to the true ink ends (y=200 top, y=600 bottom)…
    assert top_ref < top_unref
    assert bottom_ref > bottom_unref
    # …and within a few pixels of them.
    assert top_ref < 206.0
    assert bottom_ref > 594.0


# ------------------------------------------------------------------ crossings


def test_refine_keeps_crossing_widths_resolved(synthetic_bbox, tmp_path):
    """Refined widths at a crossing stay near the stroke's own width, not the blob's."""
    from PIL import Image

    img = np.ones((800, 800), dtype=np.float32)
    img[200:600, 388:412] = 0.05  # vertical bar, half-width 12
    img[388:412, 320:480] = 0.05  # crossbar
    path = tmp_path / "cross.png"
    Image.fromarray((img * 255).astype(np.uint8), mode="L").save(path)

    down = [{"x": 400.0, "y": float(200 + 400 * i / 29), "pressure": 0.5, "t": float(i)} for i in range(30)]
    down[-1]["pen_up"] = True
    bar = [{"x": float(325 + 150 * i / 14), "y": 400.0, "pressure": 0.5, "t": float(30 + i)} for i in range(15)]

    canon = canonical_from_path(raw_path=down + bar, bbox=synthetic_bbox, chart_path=str(path), glyph="t", n_anchors=40)
    hw = np.asarray(canon["trace_meta"]["half_widths_px"], dtype=float)
    crossing = canon["trace_meta"]["crossing_anchors"]
    assert crossing  # the crossing was detected
    assert float(np.max(hw[crossing])) < 13.5  # not the ~17px union blob


# ------------------------------------------------------------------ pressure cone


def test_pressure_cone_cap_follows_the_pressure_axis():
    """The physical width cap is maximal along the dominant axis, decays off-axis,
    and stays within [hairline, max] — Spitzfeder mechanics in numbers.
    """
    from core.fit import _pressure_cone_cap

    # Wide vertical downstroke (the pressure axis), a medium 45° diagonal,
    # and a thin horizontal crossbar — three separate pen strokes.
    down = np.column_stack([np.zeros(10), np.linspace(2.0, 0.0, 10)])
    diag = np.column_stack([np.linspace(0.2, 1.2, 10), np.linspace(0.0, 1.0, 10)])
    across = np.column_stack([np.linspace(0.2, 1.2, 10), np.full(10, 1.5)])
    anchors = np.concatenate([down, diag, across])
    w0 = np.concatenate([np.full(10, 0.10), np.full(10, 0.05), np.full(10, 0.02)])

    cap = _pressure_cone_cap(anchors, w0, [0, 10, 20])

    w_hair = float(np.percentile(w0, 10))
    w_max = float(np.percentile(w0, 95)) * 1.1
    # (c) bounded by [hairline, max] everywhere.
    assert float(cap.min()) >= w_hair - 1e-9
    assert float(cap.max()) <= w_max + 1e-9
    # (a) highest on the wide (axis-defining) stroke — near the max cap…
    assert float(cap[:10].min()) > w_hair + 0.75 * (w_max - w_hair)
    # (b) …decaying with misalignment: diagonal below vertical, crossbar near
    # the hairline floor (alignment ≈ 0 for the orthogonal direction).
    assert float(cap[:10].mean()) > float(cap[10:20].mean()) > float(cap[20:].mean())
    assert float(cap[20:].max()) < w_hair + 0.25 * (w_max - w_hair)
    # The cap permits every real (measured) width of the wide stroke.
    assert np.all(cap[:10] >= w0[:10] - 1e-9)


# ------------------------------------------------------------------ degenerates


def test_refine_handles_two_anchor_hairline(synthetic_bbox, tmp_path):
    """A 2-anchor stroke on a 2px hairline must neither NaN nor collapse."""
    from PIL import Image

    img = np.ones((800, 800), dtype=np.float32)
    img[200:600, 399:401] = 0.05  # 2px hairline
    path = tmp_path / "hairline.png"
    Image.fromarray((img * 255).astype(np.uint8), mode="L").save(path)

    from core.chart import crop_with_mask, load_chart_grayscale
    from core.extract import binarize_adaptive, skeleton_and_width

    crop = crop_with_mask(load_chart_grayscale(str(path)), synthetic_bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, width_map = skeleton_and_width(mask)

    anchors = np.array([[0.0, 4.0], [0.0, 0.0]])  # straight down, template units
    widths = np.array([0.01, 0.01])
    result = refine_template_against_crop(
        anchors, widths, skel, width_map, unit_px=100.0, baseline_y_px=500.0, x_origin_px=100.0
    )
    assert np.all(np.isfinite(result.anchors))
    assert np.all(np.isfinite(result.half_widths))
    assert float(result.half_widths.min()) * 100.0 >= WIDTH_FLOOR_PX - 1e-6


# ------------------------------------------------------------------ pipeline meta


def test_canonical_carries_refine_and_quality_meta(synthetic_chart_path, synthetic_bbox):
    canon = _canonical(synthetic_chart_path, synthetic_bbox)
    refine_meta = canon["trace_meta"]["refine"]
    assert refine_meta["applied"] is True
    for key in ("boundary_rmse_px", "boundary_rmse_px_initial", "geo_rmse_px", "width_tv_px", "outer_rounds_used"):
        assert key in refine_meta
    quality = canon["trace_meta"]["quality"]
    assert quality is not None
    assert 0.0 <= quality["score"] <= 100.0
    # The refined silhouette should match the synthetic bar closely.
    assert quality["iou"] > 0.85


def test_refine_can_be_disabled(synthetic_chart_path, synthetic_bbox):
    canon = _canonical(synthetic_chart_path, synthetic_bbox, refine=False)
    assert canon["trace_meta"]["refine"]["applied"] is False
    assert canon["trace_meta"]["quality"] is not None  # quality is scored either way
