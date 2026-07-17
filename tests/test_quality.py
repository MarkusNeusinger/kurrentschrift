"""Image-space quality metrics: rendered silhouette vs binarized crop."""

from __future__ import annotations

import numpy as np

from core.pipeline import canonical_from_path
from core.quality import (
    chamfer_boundary_stats,
    quality_for_glyph,
    rasterize_silhouette,
    template_quality_metrics,
    width_profile_tv,
)
from core.template import capsule_union_rings


def _vertical_stylus_path(num: int = 40, x_global: int = 400) -> list[dict]:
    """Pen path mimicking a straight downstroke on the synthetic chart."""
    return [
        {"x": float(x_global), "y": float(200 + 400 * i / (num - 1)), "pressure": 0.5, "t": float(i)}
        for i in range(num)
    ]


def _canonical(synthetic_chart_path, synthetic_bbox) -> dict:
    return canonical_from_path(
        raw_path=_vertical_stylus_path(), bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", n_anchors=20
    )


# ------------------------------------------------------------------ rasterize


def test_rasterize_keeps_loop_counter_hole():
    """A closed-loop centerline rasterises as a ring — the counter stays open."""
    theta = np.linspace(0.0, 2.0 * np.pi, 80)
    x = 100.0 + 50.0 * np.cos(theta)
    y = 100.0 + 50.0 * np.sin(theta)
    rings = capsule_union_rings(x, y, np.full_like(x, 8.0), decimals=2)
    assert len(rings) >= 2  # exterior + hole
    mask = rasterize_silhouette([rings], (200, 200))
    assert not mask[100, 100]  # counter (hole) stays empty
    assert mask[100, 150]  # the ring itself is filled
    assert not mask[10, 10]  # outside stays empty


def test_rasterize_ors_strokes_together():
    """Two disjoint strokes both land in the combined mask."""
    a = capsule_union_rings(np.array([20.0, 80.0]), np.array([50.0, 50.0]), np.array([5.0, 5.0]), decimals=2)
    b = capsule_union_rings(np.array([20.0, 80.0]), np.array([150.0, 150.0]), np.array([5.0, 5.0]), decimals=2)
    mask = rasterize_silhouette([a, b], (200, 200))
    assert mask[50, 50]
    assert mask[150, 50]
    assert not mask[100, 50]  # the gap between the strokes stays empty


# ------------------------------------------------------------------ components


def test_chamfer_empty_prediction_scores_worst_case():
    ink = np.zeros((30, 40), dtype=bool)
    ink[10:20, 10:30] = True
    stats = chamfer_boundary_stats(np.zeros_like(ink), ink)
    assert stats["chamfer_mean_px"] == round(float(np.hypot(30, 40)), 3)


def test_chamfer_identical_masks_is_zero():
    ink = np.zeros((30, 40), dtype=bool)
    ink[10:20, 10:30] = True
    stats = chamfer_boundary_stats(ink.copy(), ink)
    assert stats["chamfer_mean_px"] == 0.0
    assert stats["chamfer_p95_px"] == 0.0


def test_width_profile_tv_constant_is_zero():
    assert width_profile_tv(np.full(50, 4.0), [0]) == 0.0


def test_width_profile_tv_never_crosses_pen_lift():
    """The jump between two flat strokes is a pen lift, not waviness."""
    widths = np.concatenate([np.full(10, 2.0), np.full(10, 8.0)])
    assert width_profile_tv(widths, [0, 10]) == 0.0
    # Same profile read as ONE stroke would see the 6px step.
    assert width_profile_tv(widths, [0]) > 0.0


# ------------------------------------------------------------------ end to end


def test_identity_reconstruction_scores_high(synthetic_chart_path, synthetic_bbox):
    """A canonical derived from the crop renders back onto the same ink."""
    canon = _canonical(synthetic_chart_path, synthetic_bbox)
    q = quality_for_glyph(canon, synthetic_bbox, synthetic_chart_path)
    assert q["iou"] > 0.85
    assert q["chamfer_mean_px"] < 1.5
    assert q["geo_rmse_px"] < 2.0
    assert q["score"] > 80.0
    assert q["loss"] < 0.2


def test_inflated_widths_score_strictly_lower(synthetic_chart_path, synthetic_bbox):
    """Monotonicity: widths 1.5x too fat must lower IoU and the aggregate score."""
    canon = _canonical(synthetic_chart_path, synthetic_bbox)
    q_good = quality_for_glyph(canon, synthetic_bbox, synthetic_chart_path)
    fat = {**canon, "trace_meta": {**canon["trace_meta"]}}
    fat["trace_meta"]["half_widths_px"] = [1.5 * w for w in canon["trace_meta"]["half_widths_px"]]
    q_fat = quality_for_glyph(fat, synthetic_bbox, synthetic_chart_path)
    assert q_fat["iou"] < q_good["iou"]
    assert q_fat["score"] < q_good["score"]
    assert q_fat["loss"] > q_good["loss"]


def test_quality_metrics_are_deterministic(synthetic_chart_path, synthetic_bbox):
    canon = _canonical(synthetic_chart_path, synthetic_bbox)
    q1 = quality_for_glyph(canon, synthetic_bbox, synthetic_chart_path)
    q2 = quality_for_glyph(canon, synthetic_bbox, synthetic_chart_path)
    assert q1 == q2


def test_template_quality_metrics_direct_call(synthetic_chart_path, synthetic_bbox):
    """The bench path: score against externally supplied (frozen) references."""
    from core.chart import crop_with_mask, load_chart_grayscale
    from core.extract import binarize_adaptive, skeleton_and_width
    from core.quality import crop_local_anchors

    canon = _canonical(synthetic_chart_path, synthetic_bbox)
    crop = crop_with_mask(load_chart_grayscale(synthetic_chart_path), synthetic_bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, width_map = skeleton_and_width(mask)
    tm = canon["trace_meta"]
    anchors_px = crop_local_anchors(tm["pixel_anchors"], synthetic_bbox)
    q = template_quality_metrics(
        anchors_px,
        np.asarray(tm["half_widths_px"], dtype=float),
        tm["stroke_starts"],
        mask,
        skel,
        width_map,
        unit_px=tm["unit_px"],
        crossing_anchors=tm["crossing_anchors"],
    )
    assert q == quality_for_glyph(canon, synthetic_bbox, synthetic_chart_path)
