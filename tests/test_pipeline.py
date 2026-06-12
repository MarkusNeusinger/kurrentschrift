"""End-to-end pipeline: synthetic chart → canonical dict."""

from __future__ import annotations

from core.pipeline import canonical_from_path, diagnostic_for_glyph


def _vertical_stylus_path(num: int = 40, x_global: int = 400) -> list[dict]:
    """Pen path mimicking a straight downstroke on the synthetic chart."""
    return [
        {"x": float(x_global), "y": float(200 + 400 * i / (num - 1)), "pressure": 0.5, "t": float(i)}
        for i in range(num)
    ]


def _two_stroke_path(num: int = 10) -> list[dict]:
    """Two separate downstrokes on the synthetic bar with the pen lifted between.

    Both strokes sit on the 16px-wide ink bar (x≈400); the gap in y and the
    `pen_up` marker on the first stroke's last sample mimic a u's two abstrokes.
    """
    first = [{"x": 400.0, "y": float(210 + 180 * i / (num - 1)), "pressure": 0.5, "t": float(i)} for i in range(num)]
    first[-1]["pen_up"] = True
    second = [
        {"x": 400.0, "y": float(410 + 180 * i / (num - 1)), "pressure": 0.5, "t": float(num + i)} for i in range(num)
    ]
    return first + second


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
    # Vertical downstroke → Schräglage ≈ 90° (angle to the baseline, 90 = upright).
    assert abs(m["slant_deg"] - 90.0) < 5.0


def test_coupling_defaults_to_baseline(synthetic_chart_path, synthetic_bbox):
    canon = canonical_from_path(
        raw_path=_vertical_stylus_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=20,
    )
    assert canon["entry"]["coupling"] == "baseline"
    assert canon["exit_pt"]["coupling"] == "baseline"


def test_coupling_height_from_bbox(synthetic_chart_path, synthetic_bbox):
    bbox = {**synthetic_bbox, "entry_coupling": "midband", "exit_coupling": "ascender"}
    canon = canonical_from_path(
        raw_path=_vertical_stylus_path(),
        bbox=bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=20,
    )
    assert canon["entry"]["coupling"] == "midband"
    assert canon["exit_pt"]["coupling"] == "ascender"


def test_raw_path_is_preserved(synthetic_chart_path, synthetic_bbox):
    raw = _vertical_stylus_path(num=80)
    canon = canonical_from_path(
        raw_path=raw, bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="l", position="initial", n_anchors=10
    )
    assert len(canon["raw_path"]) == 80


def test_pen_up_splits_path_into_strokes(synthetic_chart_path, synthetic_bbox):
    """A pen_up marker yields two strokes; stroke_starts records the boundary."""
    canon = canonical_from_path(
        raw_path=_two_stroke_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="u",
        position="medial",
        n_anchors=20,
    )
    starts = canon["trace_meta"]["stroke_starts"]
    assert len(starts) == 2
    assert starts[0] == 0
    # The second stroke begins partway through the concatenated anchor list…
    assert 0 < starts[1] < len(canon["anchors"])
    # …and the requested anchor count is honoured (≥2 per stroke).
    assert len(canon["anchors"]) == 20
    assert len(canon["half_widths"]) == len(canon["anchors"])


def test_pen_up_marker_preserved_in_raw_path(synthetic_chart_path, synthetic_bbox):
    """The single pen lift survives into the stored raw_path so /resample re-splits."""
    canon = canonical_from_path(
        raw_path=_two_stroke_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="u",
        position="medial",
        n_anchors=20,
    )
    assert sum(1 for p in canon["raw_path"] if p.get("pen_up")) == 1
    # Markers are stored sparsely — the final stroke's points carry none.
    assert not canon["raw_path"][-1].get("pen_up")


def test_single_stroke_has_one_segment(synthetic_chart_path, synthetic_bbox):
    """A path without markers re-derives as one stroke (legacy compatibility)."""
    canon = canonical_from_path(
        raw_path=_vertical_stylus_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=20,
    )
    assert canon["trace_meta"]["stroke_starts"] == [0]


def test_diagnostic_has_one_outline_polygon_per_stroke(synthetic_chart_path, synthetic_bbox):
    """The diagnostic emits a separate outline polygon for each pen-stroke."""
    canon = canonical_from_path(
        raw_path=_two_stroke_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="u",
        position="medial",
        n_anchors=20,
    )
    glyph_row = {"anchors": canon["anchors"], "half_widths": canon["half_widths"], "trace_meta": canon["trace_meta"]}
    diag = diagnostic_for_glyph(
        glyph_row=glyph_row, bbox=synthetic_bbox, chart_path=synthetic_chart_path, style_ratio=[2, 1, 2], slant_deg=65.0
    )
    # Preferred silhouettes: one ring list per pen-stroke (exterior + holes).
    assert len(diag["outline_paths"]) == 2
    assert all(len(stroke) >= 1 and len(stroke[0]) >= 4 for stroke in diag["outline_paths"])
    # Legacy fields derived from the rings: one outer contour per stroke.
    assert len(diag["outline_polygons"]) == 2
    assert diag["outline_polygon"] == diag["outline_polygons"][0]
    # One centerline per stroke, each the spine of its silhouette.
    assert len(diag["centerlines_template"]) == 2


def test_diagnostic_contains_render_fields(synthetic_chart_path, synthetic_bbox):
    canon = canonical_from_path(
        raw_path=_vertical_stylus_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=20,
    )
    glyph_row = {"anchors": canon["anchors"], "half_widths": canon["half_widths"], "trace_meta": canon["trace_meta"]}
    diag = diagnostic_for_glyph(
        glyph_row=glyph_row, bbox=synthetic_bbox, chart_path=synthetic_chart_path, style_ratio=[2, 1, 2], slant_deg=65.0
    )
    assert diag["crop_size"] == {"w": 200, "h": 600}
    assert diag["template_guides"]["ascender"] == 3.0
    assert diag["template_guides"]["descender"] == -2.0
    assert len(diag["anchors_template"]) == 20
    assert len(diag["outline_polygon"]) > 0
    assert diag["slant_deg"] == 65.0


def test_diagnostic_constant_resolver_renders_uniform_widths(synthetic_chart_path, synthetic_bbox):
    """`width_resolver='constant'` (Gleichzug, architektur.md §5) collapses the
    rendered width profile to one value; the stored canonical stays untouched
    and the default 'pressure' path is byte-identical to no argument."""
    canon = canonical_from_path(
        raw_path=_vertical_stylus_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=20,
    )
    glyph_row = {"anchors": canon["anchors"], "half_widths": canon["half_widths"], "trace_meta": canon["trace_meta"]}
    hw_before = [float(v) for v in canon["half_widths"]]
    common = {"bbox": synthetic_bbox, "chart_path": synthetic_chart_path, "style_ratio": [1, 1, 1], "slant_deg": 90.0}
    constant = diagnostic_for_glyph(glyph_row=glyph_row, width_resolver="constant", **common)
    assert len(set(constant["half_widths_template"])) == 1
    assert len(set(constant["half_widths_px"])) == 1
    # The measurement in the canonical is NOT mutated by rendering.
    assert [float(v) for v in canon["half_widths"]] == hw_before
    # Default == explicit 'pressure' == the measured profile.
    default = diagnostic_for_glyph(glyph_row=glyph_row, **common)
    pressure = diagnostic_for_glyph(glyph_row=glyph_row, width_resolver="pressure", **common)
    assert default["half_widths_template"] == pressure["half_widths_template"]
    assert default["outline_paths"] == pressure["outline_paths"]
    assert constant["anchors_template"] == default["anchors_template"]
