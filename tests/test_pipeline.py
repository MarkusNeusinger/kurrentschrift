"""End-to-end pipeline: synthetic chart → canonical dict."""

from __future__ import annotations

import numpy as np

from core.pipeline import canonical_from_path, diagnostic_for_glyph


def _vertical_stylus_path(num: int = 40, x_global: int = 400) -> list[dict]:
    """Pen path mimicking a straight downstroke on the synthetic chart."""
    return [{"x": float(x_global), "y": float(200 + 400 * i / (num - 1)), "pressure": 0.5, "t": float(i)} for i in range(num)]


def test_canonical_from_path_produces_expected_shape(synthetic_chart_path, synthetic_bbox):
    raw_path = _vertical_stylus_path()
    canon = canonical_from_path(
        raw_path=raw_path,
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=20,
    )
    assert canon["glyph"] == "l"
    assert canon["position"] == "initial"
    assert len(canon["anchors"]) == 20
    assert len(canon["half_widths"]) == 20
    # Half-widths should be positive — the synthetic glyph is 16px wide,
    # half = 8px, and unit_px = baseline_y - midband_y = 100, so half-width
    # in template coords ≈ 0.08.
    assert min(canon["half_widths"]) > 0.0
    assert max(canon["half_widths"]) < 0.5
    # Entry should be at the top of the path (positive y in template coords
    # because baseline=0, midband=1, ascender>0).
    assert canon["entry"]["xy"][1] > canon["exit_pt"]["xy"][1]


def test_canonical_contains_measurements(synthetic_chart_path, synthetic_bbox):
    canon = canonical_from_path(
        raw_path=_vertical_stylus_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=20,
    )
    m = canon["measurements"]
    for key in ("slant_deg", "mean_half_width_px", "path_length_px", "aspect_ratio"):
        assert key in m
    # Vertical downstroke → slant ≈ 0°.
    assert abs(m["slant_deg"]) < 5.0


def test_raw_path_is_preserved(synthetic_chart_path, synthetic_bbox):
    raw = _vertical_stylus_path(num=80)
    canon = canonical_from_path(
        raw_path=raw, bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", position="initial", n_anchors=10
    )
    assert len(canon["raw_path"]) == 80


def test_diagnostic_contains_render_fields(synthetic_chart_path, synthetic_bbox):
    canon = canonical_from_path(
        raw_path=_vertical_stylus_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=20,
    )
    glyph_row = {
        "anchors": canon["anchors"],
        "half_widths": canon["half_widths"],
        "trace_meta": canon["trace_meta"],
    }
    diag = diagnostic_for_glyph(
        glyph_row=glyph_row,
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        style_ratio=[2, 1, 2],
        slant_deg=65.0,
    )
    assert diag["crop_size"] == {"w": 200, "h": 600}
    assert diag["template_guides"]["ascender"] == 3.0
    assert diag["template_guides"]["descender"] == -2.0
    assert len(diag["anchors_template"]) == 20
    assert len(diag["outline_polygon"]) > 0
    assert diag["slant_deg"] == 65.0
