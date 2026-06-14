"""Sütterlin (Gleichzug) derivation: skeleton-locked geometry, constant nib.

The headline claim of `core.suetterlin` is that a constant-width glyph is the
crop's skeleton buffered by one radius, so the rendered silhouette hugs the ink
by construction. These tests assert exactly that on synthetic constant-width
charts: the width is genuinely constant, the silhouette scores a high IoU
against the crop, pen lifts split strokes, and sharp turns become corner knots.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from core.suetterlin import canonical_suetterlin_from_path, canonical_suetterlin_from_raw_path_only


def _save(img: np.ndarray, tmp_path, name: str = "chart.png") -> str:
    out = tmp_path / name
    Image.fromarray((img * 255).astype(np.uint8), mode="L").save(out)
    return str(out)


@pytest.fixture
def l_shape_chart_path(tmp_path) -> str:
    """A constant-width (16px) right-angle 'L': a downstroke into a footstroke.

    Vertical bar x∈[392,408), y∈[200,600); horizontal bar y∈[584,600),
    x∈[392,700). The 90° corner at the bottom-left is the kink the derivation
    must keep crisp.
    """
    img = np.ones((800, 800), dtype=np.float32)
    img[200:600, 392:408] = 0.05
    img[584:600, 392:700] = 0.05
    return _save(img, tmp_path)


@pytest.fixture
def l_shape_bbox() -> dict:
    return {
        "y0": 150,
        "y1": 650,
        "x0": 300,
        "x1": 750,
        "mask_strokes": [],
        "baseline_y": 600,
        "midband_y": 500,
        "n_anchors": 40,
    }


def _vertical_path(num: int = 40, x_global: int = 400) -> list[dict]:
    """A rough downstroke on the synthetic vertical bar."""
    return [{"x": float(x_global), "y": float(205 + 390 * i / (num - 1))} for i in range(num)]


def _l_shape_path(num: int = 30) -> list[dict]:
    """Down the stem, then right along the foot — one continuous pen-stroke."""
    down = [{"x": 400.0, "y": float(210 + 382 * i / (num - 1))} for i in range(num)]
    foot = [{"x": float(400 + 290 * i / (num - 1)), "y": 592.0} for i in range(num)]
    return down + foot


def test_width_is_constant(synthetic_chart_path, synthetic_bbox):
    canon = canonical_suetterlin_from_path(
        raw_path=_vertical_path(), bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", position="initial"
    )
    hw = canon["half_widths"]
    assert len(hw) == len(canon["anchors"])
    # Gleichzug: every half-width is the same stamped nib radius.
    assert max(hw) - min(hw) < 1e-9
    assert hw[0] > 0.0
    assert canon["trace_meta"]["method"] == "suetterlin-gleichzug"
    assert canon["trace_meta"]["nib_radius_px"] > 0.0


def test_silhouette_hugs_the_crop(synthetic_chart_path, synthetic_bbox):
    canon = canonical_suetterlin_from_path(
        raw_path=_vertical_path(), bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", position="initial"
    )
    quality = canon["trace_meta"]["quality"]
    assert quality is not None
    # The silhouette is the skeleton buffered by one radius — it overlaps the
    # 16px ink bar almost perfectly (round caps cost a sliver at the ends).
    assert quality["iou"] > 0.85


def test_anchors_lock_to_the_skeleton(synthetic_chart_path, synthetic_bbox):
    # A deliberately sloppy Weg, drifting up to ~5px off the bar centre, must
    # still snap back onto the medial axis (x≈400 in chart coords).
    rng = np.random.default_rng(0)
    raw = [{"x": 400.0 + rng.uniform(-5, 5), "y": float(205 + 390 * i / 39)} for i in range(40)]
    canon = canonical_suetterlin_from_path(
        raw_path=raw, bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", position="initial"
    )
    xs = np.array([px for px, _ in canon["trace_meta"]["pixel_anchors"]])
    # The bar's medial axis sits at x≈399–400; snapped anchors hug it tightly
    # despite the ±5px hand wobble in the drawn path.
    assert np.abs(xs - 399.5).max() < 2.0


def test_pen_lift_splits_strokes(synthetic_chart_path, synthetic_bbox):
    first = [{"x": 400.0, "y": float(210 + 180 * i / 9)} for i in range(10)]
    first[-1]["pen_up"] = True
    second = [{"x": 400.0, "y": float(410 + 180 * i / 9)} for i in range(10)]
    canon = canonical_suetterlin_from_path(
        raw_path=first + second, bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="u", position="initial"
    )
    assert len(canon["trace_meta"]["stroke_starts"]) == 2


def test_sharp_corner_becomes_a_knot(l_shape_chart_path, l_shape_bbox):
    canon = canonical_suetterlin_from_path(
        raw_path=_l_shape_path(), bbox=l_shape_bbox, chart_path=l_shape_chart_path, glyph="L", position="initial"
    )
    # The 90° turn at the foot is a within-stroke reversal → at least one corner.
    assert len(canon["trace_meta"]["corner_anchors"]) >= 1
    # And the cornered silhouette still hugs the L-shaped ink.
    assert canon["trace_meta"]["quality"]["iou"] > 0.8


def test_from_raw_path_only_roundtrip(synthetic_chart_path, synthetic_bbox):
    canon = canonical_suetterlin_from_path(
        raw_path=_vertical_path(), bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", position="initial"
    )
    again = canonical_suetterlin_from_raw_path_only(
        glyph_row={"raw_path": canon["raw_path"], "glyph": "l", "position": "initial"},
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        n_anchors=40,
    )
    assert again["glyph"] == "l"
    assert again["trace_meta"]["method"] == "suetterlin-gleichzug"
    assert len(again["anchors"]) >= 2
