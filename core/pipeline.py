"""Canonical-extraction + diagnostic pipeline. Pure functions; no DB, no HTTP.

`canonical_from_path` converts a dense stylus path on the source chart into
a normalised canonical-template dict (advance, anchors, half-widths, entry,
exit, raw_path, trace_meta, measurements) ready for upsert into the
`templates` table.

`diagnostic_for_glyph` returns the JSON the frontend needs to draw the
three-column SVG diagnostic (Loth pur | Crop+skeleton+anchors | Canonical
template) — already includes the polygon outline (rendered unsheared; the
traced anchors carry the chart's natural slant) so the TS side only renders.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import median_filter, uniform_filter1d

from core.chart import crop_with_mask, load_chart_grayscale
from core.extract import binarize_adaptive, half_widths_on_medial_axis, skeleton_and_width
from core.template import (
    allocate_samples,
    chord_length,
    multi_stroke_centerlines,
    multi_stroke_silhouettes,
    template_guides,
)


# 50 is the measured jitter knee across the authored glyphs (a, K, r, u): p95
# deviation from the de-jittered trace ≤0.75px for every glyph, while ≥80
# anchors start reproducing hand wobble instead of shape (error vs the smoothed
# reference rises again) and double the fit's parameter count.
DEFAULT_N_ANCHORS = 50


# -------------------------------------------------------------------- helpers


def _resample_polyline(points: np.ndarray, n: int) -> tuple[np.ndarray, float]:
    """Equally-spaced (by chord length) resample of an Mx2 polyline to n points."""
    if len(points) == 0:
        raise ValueError("empty path")
    if len(points) == 1:
        return np.tile(points, (n, 1)), 0.0
    diffs = np.diff(points, axis=0)
    seg = np.hypot(diffs[:, 0], diffs[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(cum[-1])
    if total == 0.0:
        return np.tile(points[:1], (n, 1)), 0.0
    t = np.linspace(0.0, total, n)
    x = np.interp(t, cum, points[:, 0])
    y = np.interp(t, cum, points[:, 1])
    return np.column_stack([x, y]), total


def _split_raw_strokes(raw_path: list[dict]) -> list[list[dict]]:
    """Split a flat stylus path into per-stroke segments at pen-lift markers.

    A point carrying ``pen_up: true`` is the last sample before the pen left the
    paper (German: Absetzen); the next point starts a new stroke. Legacy paths
    carry no markers and yield a single stroke, so old templates re-derive
    identically.
    """
    strokes: list[list[dict]] = []
    current: list[dict] = []
    for p in raw_path:
        current.append(p)
        if p.get("pen_up"):
            strokes.append(current)
            current = []
    if current:
        strokes.append(current)
    return [s for s in strokes if s]


def _resample_strokes(strokes: list[np.ndarray], n: int) -> tuple[np.ndarray, list[int], float]:
    """Resample each pen-stroke independently by chord length and concatenate.

    Returns the concatenated `(N, 2)` anchor array, `stroke_starts` (the anchor
    index where each stroke begins, first is 0), and the summed path length in
    pixels — the pen-lift bridges *between* strokes are excluded, so a u's two
    downstrokes never get joined by a phantom anchor across the gap. `N` equals
    `n` except when `n` is too small to give every stroke two anchors, when it
    grows to `2 * num_strokes`.
    """
    strokes = [s for s in strokes if len(s) >= 1]
    if not strokes:
        raise ValueError("empty path")
    if len(strokes) == 1:
        resampled, length = _resample_polyline(strokes[0], n)
        return resampled, [0], length
    seg_lengths = [chord_length(s) for s in strokes]
    alloc = allocate_samples(seg_lengths, n)
    parts, starts, total, cursor = [], [], 0.0, 0
    for stroke, k, length in zip(strokes, alloc, seg_lengths, strict=True):
        resampled, _ = _resample_polyline(stroke, max(2, k))
        starts.append(cursor)
        parts.append(resampled)
        cursor += len(resampled)
        total += length
    return np.concatenate(parts, axis=0), starts, total


def _smooth_half_widths(hw_px: np.ndarray, stroke_starts: list[int]) -> np.ndarray:
    """Median + box smoothing of the half-width profile, per pen-stroke.

    The per-anchor distance-transform reads are noisy (±1px quantisation) and
    spike at self-crossings, where the transform measures the crossing blob
    instead of the stroke. A short median kills the spikes, the box pass evens
    the survivors; smoothing never crosses a pen lift.
    """
    smoothed = hw_px.astype(float).copy()
    bounds = [*stroke_starts, len(hw_px)]
    for a, b in zip(bounds[:-1], bounds[1:], strict=True):
        seg = smoothed[a:b]
        if len(seg) >= 5:
            seg = median_filter(seg, size=5, mode="nearest")
        if len(seg) >= 3:
            seg = uniform_filter1d(seg, size=3, mode="nearest")
        smoothed[a:b] = seg
    return smoothed


def _measure_slant_from_vertical(anchors_norm: np.ndarray) -> float:
    """Dominant lean of the centerline in degrees FROM VERTICAL (0 = upright).

    PCA on anchor offsets: take the principal axis, convert to angle from
    vertical. Robust to which side the stroke starts on. NOTE: this is the
    complement of the repo-wide `slant_deg` convention (Schräglage, angle to
    the baseline, 90 = upright) — callers must convert before persisting.
    """
    if len(anchors_norm) < 2:
        return 0.0
    centered = anchors_norm - anchors_norm.mean(axis=0)
    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    principal = eigvecs[:, -1]
    # Angle from +y axis (upright = 0°). principal=(dx, dy); dy may be negative.
    if principal[1] < 0:
        principal = -principal
    angle_from_vertical = float(np.degrees(np.arctan2(principal[0], principal[1])))
    return angle_from_vertical


def _measurements(anchors_norm: np.ndarray, half_widths_px: np.ndarray, path_length_px: float, bbox: dict) -> dict:
    """Per-instance derived statistics for the `templates.measurements` JSONB field."""
    width = bbox["x1"] - bbox["x0"]
    height = bbox["y1"] - bbox["y0"]
    return {
        # Stored in the repo-wide Schräglage convention (angle to the baseline,
        # 90 = upright), converted from the PCA's angle-from-vertical.
        "slant_deg": round(90.0 - _measure_slant_from_vertical(anchors_norm), 2),
        "mean_half_width_px": round(float(np.mean(half_widths_px)) if len(half_widths_px) else 0.0, 3),
        "path_length_px": round(float(path_length_px), 1),
        "aspect_ratio": round(width / height, 3) if height else 0.0,
    }


# -------------------------------------------------------------------- public API


def canonical_from_path(
    raw_path: list[dict], bbox: dict, chart_path: str, glyph: str, position: str, n_anchors: int | None = None
) -> dict:
    """Turn a dense stylus path into a canonical-template dict.

    `raw_path` items: `{x, y, pressure?, t?}` in *chart-global* pixel coords.
    `bbox` is a dict carrying y0/y1/x0/x1, mask_strokes, baseline_y, midband_y,
    (optional) n_anchors. `chart_path` is the on-disk path (resolvable via
    `core.chart.resolve_chart_path`). The grading characters identifying the
    glyph (`glyph`, `position`) are passed explicitly because they live on the
    canonical itself, not on the bbox row.

    Steps:
      1. Load chart + crop with eraser mask (M0 input).
      2. Binarize + skeleton + distance-transform on the crop.
      3. Convert raw_path from chart-global → crop-local pixel coords.
      4. Resample the polyline by chord length to N anchors.
      5. Sample half-width per anchor from the distance-transform.
      6. Normalise pixel → template coords (baseline=0, midband=1).
      7. Compute entry/exit tangents from first/last anchor pairs.
      8. Derive per-instance measurements (slant, mean width, path length).
    """
    for required in ("baseline_y", "midband_y", "y0", "y1", "x0", "x1"):
        if bbox.get(required) is None:
            raise ValueError(f"bbox missing required field {required!r}")
    if len(raw_path) < 2:
        raise ValueError("stylus path needs at least 2 points")

    chart_gray = load_chart_grayscale(chart_path)
    crop = crop_with_mask(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, width_map = skeleton_and_width(mask)

    x0, y0 = bbox["x0"], bbox["y0"]
    strokes_local = [
        np.array([(p["x"] - x0, p["y"] - y0) for p in stroke], dtype=float) for stroke in _split_raw_strokes(raw_path)
    ]

    n = int(n_anchors or bbox.get("n_anchors") or DEFAULT_N_ANCHORS)
    # Resample stroke-by-stroke so a pen lift never gets a phantom anchor bridging
    # the gap; `stroke_starts` records where each stroke begins in the anchor list.
    resampled_local, stroke_starts, path_length_px = _resample_strokes(strokes_local, n)

    baseline_y = int(bbox["baseline_y"])
    midband_y = int(bbox["midband_y"])
    unit_px = float(baseline_y - midband_y)
    if unit_px <= 0:
        raise ValueError(f"baseline_y ({baseline_y}) must exceed midband_y ({midband_y})")

    # Snap no farther than a quarter x-height: generous against trace wobble,
    # tight enough not to jump to a neighbouring stroke.
    hw_px = half_widths_on_medial_axis(resampled_local, skel, mask, width_map, snap_cap_px=max(3.0, 0.25 * unit_px))
    hw_px = _smooth_half_widths(hw_px, stroke_starts)

    pixel_global = resampled_local + np.array([x0, y0])
    x_origin = float(pixel_global[0, 0])
    x_norm = (pixel_global[:, 0] - x_origin) / unit_px
    y_norm = (baseline_y - pixel_global[:, 1]) / unit_px
    hw_norm = hw_px / unit_px

    anchors_norm = np.column_stack([x_norm, y_norm])

    entry_xy = [round(float(x_norm[0]), 4), round(float(y_norm[0]), 4)]
    exit_xy = [round(float(x_norm[-1]), 4), round(float(y_norm[-1]), 4)]
    entry_tan = float(np.degrees(np.arctan2(y_norm[1] - y_norm[0], x_norm[1] - x_norm[0])))
    exit_tan = float(np.degrees(np.arctan2(y_norm[-1] - y_norm[-2], x_norm[-1] - x_norm[-2])))
    # Coupling height (where a neighbour joins) is configured per glyph on the
    # bbox guides; default to the baseline when unset.
    entry_coupling = bbox.get("entry_coupling", "baseline")
    exit_coupling = bbox.get("exit_coupling", "baseline")
    advance = float(max(0.1, x_norm.max() - x_norm.min()))

    raw_stored = []
    for p in raw_path:
        item: dict = {
            "x": round(float(p["x"]), 2),
            "y": round(float(p["y"]), 2),
            "pressure": None if p.get("pressure") is None else round(float(p["pressure"]), 4),
            "t": None if p.get("t") is None else round(float(p["t"]), 2),
        }
        # Keep the pen-lift markers sparse (only the last sample of each stroke
        # but the final one) so /resample re-splits the path identically.
        if p.get("pen_up"):
            item["pen_up"] = True
        raw_stored.append(item)

    return {
        "glyph": glyph,
        "position": position,
        "advance": round(advance, 4),
        "anchors": [[round(float(x), 4), round(float(y), 4)] for x, y in anchors_norm],
        "half_widths": [round(float(h), 4) for h in hw_norm],
        "entry": {"xy": entry_xy, "tangent_deg": round(entry_tan, 1), "coupling": entry_coupling},
        "exit_pt": {"xy": exit_xy, "tangent_deg": round(exit_tan, 1), "coupling": exit_coupling},
        "raw_path": raw_stored,
        "trace_meta": {
            "method": "web-stylus",
            "bbox_snapshot": {k: bbox[k] for k in ("y0", "y1", "x0", "x1")},
            "baseline_y": baseline_y,
            "midband_y": midband_y,
            "unit_px": unit_px,
            "n_anchors": len(anchors_norm),
            # Anchor indices where each pen-stroke begins (first is 0). A single
            # entry means one continuous stroke; the diagnostic + fit split here.
            "stroke_starts": stroke_starts,
            "path_length_px": round(path_length_px, 1),
            "pixel_anchors": [[round(float(x), 2), round(float(y), 2)] for x, y in pixel_global],
            "half_widths_px": [round(float(h), 2) for h in hw_px],
        },
        "measurements": _measurements(anchors_norm, hw_px, path_length_px, bbox),
    }


def canonical_from_raw_path_only(glyph_row: dict, bbox: dict, chart_path: str, n_anchors: int) -> dict:
    """Re-derive a canonical from an existing glyph's stored `raw_path` with a new N.

    Used by the /resample endpoint: the user changes n_anchors in the editor
    and we want the new anchor count without re-tracing.
    """
    return canonical_from_path(
        raw_path=glyph_row["raw_path"],
        bbox=bbox,
        chart_path=chart_path,
        glyph=glyph_row["glyph"],
        position=glyph_row["position"],
        n_anchors=n_anchors,
    )


# ------------------------------------------------------------------ diagnostic


def diagnostic_for_glyph(
    glyph_row: dict, bbox: dict, chart_path: str, style_ratio: list[float], slant_deg: float
) -> dict:
    """JSON for the 3-column SVG diagnostic (Loth pur | Crop+skeleton+anchors | Canonical).

    Backend does all the heavy lifting (skeleton extraction, outline polygon
    construction) so the frontend just renders polylines + polygons.
    """
    chart_gray = load_chart_grayscale(chart_path)
    crop = crop_with_mask(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, _ = skeleton_and_width(mask)

    h, w = crop.shape
    ys, xs = np.where(skel)
    skeleton_polyline_px = [[int(x), int(y)] for x, y in zip(xs.tolist(), ys.tolist(), strict=True)]

    anchors_template = np.asarray(glyph_row["anchors"], dtype=float)
    half_widths_template = np.asarray(glyph_row["half_widths"], dtype=float)

    trace_meta = glyph_row.get("trace_meta", {})
    pixel_anchors = trace_meta.get("pixel_anchors") or []
    half_widths_px = trace_meta.get("half_widths_px") or []
    stroke_starts = trace_meta.get("stroke_starts")
    x0, y0 = bbox["x0"], bbox["y0"]
    anchors_px = [[round(px - x0, 2), round(py - y0, 2)] for px, py in pixel_anchors]

    # One outline polygon per pen-stroke so a pen lift reads as a real gap
    # instead of a filled bar bridging the two strokes. Rendered WITHOUT an
    # extra shear (slant 90 = identity): the anchors were traced over the real
    # chart ink and already carry its natural slant — shearing again by the
    # style slant was a double application that rendered glyphs too flat (a
    # 50° Loth downstroke came out at ~37.5°). `core.fit` maps template→pixels
    # unsheared for the same reason; `slant_deg` stays in the payload as the
    # style's nominal Schräglage (metadata, not a render transform).
    # Capsule-union silhouette per stroke (rings: exterior + holes, evenodd):
    # unlike the legacy ±normal ribbon it cannot fold into bowties at tight
    # loops, keeps loop counters open and rounds the stroke ends like a nib.
    outline_paths = multi_stroke_silhouettes(anchors_template, half_widths_template, stroke_starts, 90.0, n=240)
    # Legacy single-polygon fields derived from the rings (first ring of each
    # stroke ≈ the outer contour) so a stale SPA bundle keeps rendering
    # something sensible mid-deploy without paying a second geometry pass.
    outline_polygons = [stroke[0] for stroke in outline_paths if stroke]
    # Matching per-stroke centerlines (same sampling) so the frontend can sweep a
    # wide mask along the ductus and reveal the silhouette in writing order.
    centerlines_template = multi_stroke_centerlines(anchors_template, half_widths_template, stroke_starts, 90.0, n=240)

    return {
        "crop_size": {"w": int(w), "h": int(h)},
        "skeleton_polyline_px": skeleton_polyline_px,
        "anchors_px": anchors_px,
        "half_widths_px": [round(float(v), 2) for v in half_widths_px],
        "anchors_template": [[round(float(x), 4), round(float(y), 4)] for x, y in anchors_template],
        "half_widths_template": [round(float(v), 4) for v in half_widths_template],
        # `outline_polygons` is the stroke-aware list; `outline_polygon` stays as
        # the first polygon for older clients (identical when there is one stroke).
        "outline_polygon": outline_polygons[0] if outline_polygons else [],
        "outline_polygons": outline_polygons,
        # Per-stroke ring lists (exterior + holes) — the preferred render path.
        "outline_paths": outline_paths,
        # Per-stroke centerlines (writing order) for the animated "as written" render.
        "centerlines_template": centerlines_template,
        "baseline_y_crop": int(bbox["baseline_y"]) - y0,
        "midband_y_crop": int(bbox["midband_y"]) - y0,
        "template_guides": template_guides(style_ratio),
        "slant_deg": float(slant_deg),
    }
