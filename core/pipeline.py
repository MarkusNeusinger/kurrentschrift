"""Canonical-extraction + diagnostic pipeline. Pure functions; no DB, no HTTP.

`canonical_from_path` converts a dense stylus path on the source chart into
a normalised canonical-template dict (advance, anchors, half-widths, entry,
exit, raw_path, trace_meta, measurements) ready for upsert into the `glyphs`
table.

`diagnostic_for_glyph` returns the JSON the frontend needs to draw the
three-column SVG diagnostic (Loth pur | Crop+skeleton+anchors | Canonical
template) — already includes the slant-shear and the polygon outline so the
TS side only renders.
"""

from __future__ import annotations

import numpy as np

from core.chart import crop_with_excludes, load_chart_grayscale
from core.extract import binarize_adaptive, skeleton_and_width
from core.template import apply_slant, sample_polyline, stroke_outline, template_guides


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


def _sample_width_at(x_local: float, y_local: float, mask: np.ndarray, width_map: np.ndarray) -> float:
    """Half-width at (x_local, y_local) on the crop. Falls back to nearest ink pixel."""
    h, w = mask.shape
    ix = int(np.clip(round(x_local), 0, w - 1))
    iy = int(np.clip(round(y_local), 0, h - 1))
    if mask[iy, ix]:
        return float(width_map[iy, ix])
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return 0.0
    d2 = (xs - x_local) ** 2 + (ys - y_local) ** 2
    k = int(np.argmin(d2))
    return float(width_map[ys[k], xs[k]])


def _measure_slant(anchors_norm: np.ndarray) -> float:
    """Dominant slant of the centerline in degrees (0 = upright, positive = leaning right).

    PCA on anchor offsets: take the principal axis, convert to angle from
    vertical. Robust to which side the stroke starts on.
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
    """Per-instance derived statistics for the `glyphs.measurements` JSONB field."""
    width = bbox["x1"] - bbox["x0"]
    height = bbox["y1"] - bbox["y0"]
    return {
        "slant_deg": round(_measure_slant(anchors_norm), 2),
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
    `bbox` is a dict carrying y0/y1/x0/x1, excludes, baseline_y, midband_y,
    (optional) n_anchors. `chart_path` is the on-disk path (resolvable via
    `core.chart.resolve_chart_path`). The grading characters identifying the
    glyph (`glyph`, `position`) are passed explicitly because they live on the
    canonical itself, not on the bbox row.

    Steps:
      1. Load chart + crop with excludes (M0 input).
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
    crop = crop_with_excludes(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    _, width_map = skeleton_and_width(mask)

    x0, y0 = bbox["x0"], bbox["y0"]
    local = np.array([(p["x"] - x0, p["y"] - y0) for p in raw_path], dtype=float)

    n = int(n_anchors or bbox.get("n_anchors") or DEFAULT_N_ANCHORS)
    resampled_local, path_length_px = _resample_polyline(local, n)

    hw_px = np.array(
        [_sample_width_at(float(rx), float(ry), mask, width_map) for rx, ry in resampled_local], dtype=float
    )

    baseline_y = int(bbox["baseline_y"])
    midband_y = int(bbox["midband_y"])
    unit_px = float(baseline_y - midband_y)
    if unit_px <= 0:
        raise ValueError(f"baseline_y ({baseline_y}) must exceed midband_y ({midband_y})")

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
    advance = float(max(0.1, x_norm.max() - x_norm.min()))

    raw_stored = [
        {
            "x": round(float(p["x"]), 2),
            "y": round(float(p["y"]), 2),
            "pressure": None if p.get("pressure") is None else round(float(p["pressure"]), 4),
            "t": None if p.get("t") is None else round(float(p["t"]), 2),
        }
        for p in raw_path
    ]

    return {
        "glyph": glyph,
        "position": position,
        "advance": round(advance, 4),
        "anchors": [[round(float(x), 4), round(float(y), 4)] for x, y in anchors_norm],
        "half_widths": [round(float(h), 4) for h in hw_norm],
        "entry": {"xy": entry_xy, "tangent_deg": round(entry_tan, 1), "coupling": "baseline"},
        "exit_pt": {"xy": exit_xy, "tangent_deg": round(exit_tan, 1), "coupling": "baseline"},
        "raw_path": raw_stored,
        "trace_meta": {
            "method": "web-stylus",
            "bbox_snapshot": {k: bbox[k] for k in ("y0", "y1", "x0", "x1")},
            "baseline_y": baseline_y,
            "midband_y": midband_y,
            "unit_px": unit_px,
            "n_anchors": n,
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

    Backend does all the heavy lifting (skeleton extraction, outline-with-slant
    polygon construction) so the frontend just renders polylines + polygons.
    """
    chart_gray = load_chart_grayscale(chart_path)
    crop = crop_with_excludes(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, _ = skeleton_and_width(mask)

    h, w = crop.shape
    ys, xs = np.where(skel)
    skeleton_polyline_px = [[int(x), int(y)] for x, y in zip(xs.tolist(), ys.tolist(), strict=True)]

    anchors_template = np.asarray(glyph_row["anchors"], dtype=float)
    half_widths_template = np.asarray(glyph_row["half_widths"], dtype=float)

    pixel_anchors = glyph_row.get("trace_meta", {}).get("pixel_anchors") or []
    half_widths_px = glyph_row.get("trace_meta", {}).get("half_widths_px") or []
    x0, y0 = bbox["x0"], bbox["y0"]
    anchors_px = [[round(px - x0, 2), round(py - y0, 2)] for px, py in pixel_anchors]

    # Outline polygon in template coords, slant applied.
    if len(anchors_template) >= 2:
        sx, sy, sw = sample_polyline(anchors_template, half_widths_template, n=240)
        sx, sy = apply_slant(sx, sy, slant_deg)
        poly_x, poly_y = stroke_outline(sx, sy, sw)
        outline_polygon = [[round(float(x), 4), round(float(y), 4)] for x, y in zip(poly_x, poly_y, strict=True)]
    else:
        outline_polygon = []

    return {
        "crop_size": {"w": int(w), "h": int(h)},
        "skeleton_polyline_px": skeleton_polyline_px,
        "anchors_px": anchors_px,
        "half_widths_px": [round(float(v), 2) for v in half_widths_px],
        "anchors_template": [[round(float(x), 4), round(float(y), 4)] for x, y in anchors_template],
        "half_widths_template": [round(float(v), 4) for v in half_widths_template],
        "outline_polygon": outline_polygon,
        "baseline_y_crop": int(bbox["baseline_y"]) - y0,
        "midband_y_crop": int(bbox["midband_y"]) - y0,
        "template_guides": template_guides(style_ratio),
        "slant_deg": float(slant_deg),
    }
