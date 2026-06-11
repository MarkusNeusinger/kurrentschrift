"""Trace refinement: medial-axis snap + crossing resolution for the width channel.

The drawn Weg supplies stroke order and crossing resolution (the ductus
prior); the ink supplies the precise geometry. These tests pin the two
refinement steps in `canonical_from_path`:
* hand wobble in the drawn trace is pulled onto the ink's medial axis,
* width readings contaminated by a crossing blob are interpolated away,
* while a retrace (same path down and back up) keeps its measured widths —
  the passes run parallel, the ink there is one real stroke.
"""

from __future__ import annotations

import numpy as np

from core.pipeline import _resolve_crossing_widths, canonical_from_path


# ------------------------------------------------------------------ helpers


def _save_chart(img: np.ndarray, tmp_path, name: str) -> str:
    from PIL import Image

    out = tmp_path / name
    Image.fromarray((img * 255).astype(np.uint8), mode="L").save(out)
    return str(out)


def _cross_chart() -> np.ndarray:
    """Two 24px bars crossing at (400, 400) — a synthetic t-crossbar case."""
    img = np.ones((800, 800), dtype=np.float32)
    img[200:600, 388:412] = 0.05  # vertical bar, center x ≈ 400
    img[388:412, 320:480] = 0.05  # horizontal bar, center y ≈ 400
    return img


def _cross_path(num_v: int = 30, num_h: int = 15) -> list[dict]:
    """Vertical downstroke, pen lift, then a horizontal crossbar through it."""
    down = [{"x": 400.0, "y": float(200 + 400 * i / (num_v - 1)), "pressure": 0.5, "t": float(i)} for i in range(num_v)]
    down[-1]["pen_up"] = True
    bar = [
        {"x": float(325 + 150 * i / (num_h - 1)), "y": 400.0, "pressure": 0.5, "t": float(num_v + i)}
        for i in range(num_h)
    ]
    return down + bar


def _retrace_path(num: int = 30) -> list[dict]:
    """Down the synthetic bar and back up the same path — one stroke, no lift."""
    down = [{"x": 400.0, "y": float(200 + 400 * i / (num - 1)), "pressure": 0.5, "t": float(i)} for i in range(num)]
    up = [
        {"x": 400.0, "y": float(600 - 400 * i / (num - 1)), "pressure": 0.5, "t": float(num + i)} for i in range(1, num)
    ]
    return down + up


def _wobbly_path(num: int = 50) -> list[dict]:
    """4px off-center with ±2px sinusoidal wobble on the 16px synthetic bar."""
    return [
        {
            "x": float(404.0 + 2.0 * np.sin(i * 0.7)),
            "y": float(200 + 400 * i / (num - 1)),
            "pressure": 0.5,
            "t": float(i),
        }
        for i in range(num)
    ]


# --------------------------------------------------- crossing width resolution


def test_crossing_blob_width_is_interpolated(synthetic_bbox, tmp_path):
    """Widths through a crossing stay at the stroke's own width, not the blob's.

    Both bars are 24px wide (half-width 12); the EDT at the crossing center
    measures the union blob (~17px) and inflates several anchors before/after
    the crossing — the flare the admin sees until the second stroke covers it.
    Crossing resolution must bring the profile back to ~12px.
    """
    chart_path = _save_chart(_cross_chart(), tmp_path, "cross.png")
    canon = canonical_from_path(
        raw_path=_cross_path(), bbox=synthetic_bbox, chart_path=chart_path, glyph="t", position="medial", n_anchors=48
    )
    assert canon["trace_meta"]["crossing_anchors"], "the crossing must be detected"
    hw_px = np.asarray(canon["trace_meta"]["half_widths_px"])
    assert float(np.median(hw_px)) > 10.5
    # Without resolution the smoothed profile peaks well above 13.5 at the blob.
    assert float(hw_px.max()) < 13.5


def test_retrace_keeps_measured_widths(synthetic_chart_path, synthetic_bbox):
    """Same path down and back up is NOT a crossing — widths stay measured.

    The two passes run antiparallel over the same ink; interpolating there
    would erase real width. The transversality test must exempt them.
    """
    canon = canonical_from_path(
        raw_path=_retrace_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="i",
        position="initial",
        n_anchors=30,
    )
    assert canon["trace_meta"]["crossing_anchors"] == []
    hw_px = np.asarray(canon["trace_meta"]["half_widths_px"])
    # 16px bar → half-width ≈ 8 on both passes.
    assert float(np.median(hw_px)) > 6.5


def test_resolve_crossing_widths_interpolates_at_intersection():
    """Unit-level: a perpendicular crossing's inflated readings are replaced."""
    ys = np.linspace(-50.0, 50.0, 21)
    vertical = np.column_stack([np.zeros(21), ys])
    horizontal = np.column_stack([ys.copy(), np.zeros(21)])
    anchors = np.vstack([vertical, horizontal])
    hw = np.full(42, 8.0)
    for idx in (9, 10, 11, 30, 31, 32):  # blob readings near the intersection
        hw[idx] = 12.0
    resolved, indices = _resolve_crossing_widths(anchors, hw, [0, 21])
    assert indices, "perpendicular passes within reach must be detected"
    assert np.allclose(resolved, 8.0, atol=0.5)


def test_resolve_crossing_widths_exempts_parallel_retrace():
    """Unit-level: an antiparallel retrace is left untouched (genuine widths)."""
    ys = np.linspace(0.0, 100.0, 21)
    down = np.column_stack([np.zeros(21), ys])
    up = np.column_stack([np.zeros(20), ys[::-1][1:]])
    anchors = np.vstack([down, up])
    hw = np.full(41, 8.0)
    hw[5] = 9.5  # genuine local variation must survive
    resolved, indices = _resolve_crossing_widths(anchors, hw, [0])
    assert indices == []
    assert np.array_equal(resolved, hw)


def test_fully_contaminated_stroke_keeps_measured_widths():
    """A stroke contaminated end-to-end (dot on a stroke) keeps its readings —
    there are no clean neighbours to interpolate from."""
    ys = np.linspace(-50.0, 50.0, 21)
    vertical = np.column_stack([np.zeros(21), ys])
    dot = np.array([[0.0, 0.0], [3.0, 0.0]])
    anchors = np.vstack([vertical, dot])
    hw = np.full(23, 8.0)
    hw[21:] = 11.0
    resolved, _ = _resolve_crossing_widths(anchors, hw, [0, 21])
    assert np.allclose(resolved[21:], 11.0)


# ------------------------------------------------------------ medial-axis snap


def test_wobbly_trace_snaps_to_stroke_center(synthetic_chart_path, synthetic_bbox):
    """An off-center, wobbly trace lands on the bar's medial axis (x ≈ 399.5)."""
    canon = canonical_from_path(
        raw_path=_wobbly_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=24,
    )
    assert canon["trace_meta"]["snap"]["applied"] is True
    xs = np.asarray(canon["trace_meta"]["pixel_anchors"], dtype=float)[:, 0]
    # Interior anchors (ends are biased by the skeleton's eroded caps).
    assert float(np.abs(xs[2:-2] - 399.5).max()) < 2.0


def test_snap_to_ink_can_be_disabled(synthetic_chart_path, synthetic_bbox):
    """`snap_to_ink=False` keeps the drawn trace as authored."""
    canon = canonical_from_path(
        raw_path=_wobbly_path(),
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="l",
        position="initial",
        n_anchors=24,
        snap_to_ink=False,
    )
    assert canon["trace_meta"]["snap"]["applied"] is False
    xs = np.asarray(canon["trace_meta"]["pixel_anchors"], dtype=float)[:, 0]
    # The 4px offset (±2px wobble) survives untouched.
    assert float(np.abs(xs - 399.5).mean()) > 2.5


def test_snap_preserves_stroke_split(synthetic_chart_path, synthetic_bbox):
    """Snapping never bridges a pen lift — stroke_starts survive unchanged."""
    num = 10
    first = [{"x": 404.0, "y": float(210 + 180 * i / (num - 1)), "pressure": 0.5, "t": float(i)} for i in range(num)]
    first[-1]["pen_up"] = True
    second = [
        {"x": 404.0, "y": float(410 + 180 * i / (num - 1)), "pressure": 0.5, "t": float(num + i)} for i in range(num)
    ]
    canon = canonical_from_path(
        raw_path=first + second,
        bbox=synthetic_bbox,
        chart_path=synthetic_chart_path,
        glyph="u",
        position="medial",
        n_anchors=20,
    )
    starts = canon["trace_meta"]["stroke_starts"]
    assert len(starts) == 2
    assert len(canon["anchors"]) == 20
    # Both strokes snapped onto the bar center despite the 4px offset.
    xs = np.asarray(canon["trace_meta"]["pixel_anchors"], dtype=float)[:, 0]
    assert float(np.abs(xs[2:-2] - 399.5).max()) < 2.5
