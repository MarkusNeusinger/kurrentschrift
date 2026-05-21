"""Canonical-extraction pipeline — converts a stylus path into the canonical JSON.

This is the API equivalent of mvp.tools.trace_skeleton.trace_glyph(), but
instead of walking the Loth skeleton with longest-path-DFS the input is the
user's dense stylus stroke. The Loth distance-transform is still used to
sample half-widths (so the Schwellzug profile follows the actual ink, not
the user's pen pressure — that lives in `_trace.pen_pressure_raw` for later
M1 use). The output canonical JSON matches the existing schema written by
trace_skeleton so mvp.render_canonicals keeps working unchanged.
"""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from mvp.extract import binarize_adaptive, skeleton_and_width
from mvp.tools.loth import CANONICAL_DIR, crop_with_excludes, load_bboxes, load_chart_grayscale


DEFAULT_N_ANCHORS = 14


def read_bboxes_file(path: Path) -> dict:
    """Raw read of the loth_bboxes.json file."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_bboxes_file(path: Path, data: dict) -> None:
    """Raw write back, pretty-printed."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_bbox(glyph_key: str) -> dict | None:
    """Return the bbox dict for a glyph, or None if not yet set."""
    bboxes = load_bboxes()
    if glyph_key not in bboxes:
        raise KeyError(f"unknown glyph_key {glyph_key!r}")
    return bboxes[glyph_key]


def render_crop_png(bbox: dict) -> bytes:
    """Return a PNG of the chart cropped to the bbox with excludes whited out."""
    chart_gray = load_chart_grayscale()
    crop = crop_with_excludes(chart_gray, bbox, fill=1.0)
    crop_uint8 = (np.clip(crop, 0.0, 1.0) * 255).astype(np.uint8)
    buf = BytesIO()
    Image.fromarray(crop_uint8, mode="L").save(buf, format="PNG")
    return buf.getvalue()


def _resample_polyline(points: np.ndarray, n: int) -> tuple[np.ndarray, float]:
    """Resample a polyline (shape (M, 2)) to n equally-spaced points by chord length."""
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
    """Half-width at (x_local, y_local) — falls back to nearest ink pixel if outside the mask.

    The stylus path may wobble outside the ink (especially at stroke ends or
    when zoomed out). For each anchor we want the half-width *at* that point.
    If the point is inside ink, use width_map directly; otherwise find the
    nearest ink pixel and use that value. Returns 0 only if the mask is empty
    (which would mean binarization failed and the caller has bigger problems).
    """
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


def canonical_from_path(
    glyph_key: str,
    raw_path: list[dict],
    n_anchors: int | None = None,
) -> dict:
    """Build a canonical JSON dict from a user-drawn stylus path on the Loth chart.

    `raw_path` is the dense, sample-rate path captured from PointerEvents.
    Each entry: {x, y, pressure, t} in chart-global pixel coords. The full
    path is stored in the canonical's `_trace.raw_path` so callers can
    later re-sample with a different `n_anchors` (POST /resample) without
    the user needing to re-draw.

    Steps:
      1. Crop the chart with bbox + excludes (mvp.tools.loth.crop_with_excludes)
      2. Run M0 (binarize → skeleton → distance-transform) on the crop
      3. Convert each path point from chart-global to crop-local pixel coords
      4. Resample the polyline to N equally-spaced anchors by chord length
      5. Sample half-width for each anchor from the distance-transform
      6. Normalise pixel coords to template coords (baseline=0, midband=1)
      7. Compute entry/exit tangents from first/last anchor pair
      8. Merge with any existing canonical to preserve _note + coupling enums
      9. Persist the dense raw_path inside _trace for future resampling
    """
    bbox = get_bbox(glyph_key)
    if bbox is None:
        raise ValueError(f"{glyph_key}: bbox not yet set in loth_bboxes.json")
    for required in ("baseline_y", "midband_y"):
        if bbox.get(required) is None:
            raise ValueError(f"{glyph_key}: missing calibration field '{required}'")
    if len(raw_path) < 2:
        raise ValueError("stylus path needs at least 2 points")

    chart_gray = load_chart_grayscale()
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
        raise ValueError(f"{glyph_key}: baseline_y ({baseline_y}) must exceed midband_y ({midband_y})")

    pixel_global = resampled_local + np.array([x0, y0])
    x_origin = float(pixel_global[0, 0])
    x_norm = (pixel_global[:, 0] - x_origin) / unit_px
    y_norm = (baseline_y - pixel_global[:, 1]) / unit_px
    hw_norm = hw_px / unit_px

    entry_xy = [round(float(x_norm[0]), 4), round(float(y_norm[0]), 4)]
    exit_xy = [round(float(x_norm[-1]), 4), round(float(y_norm[-1]), 4)]
    entry_tan = float(np.degrees(np.arctan2(y_norm[1] - y_norm[0], x_norm[1] - x_norm[0])))
    exit_tan = float(np.degrees(np.arctan2(y_norm[-1] - y_norm[-2], x_norm[-1] - x_norm[-2])))
    advance = float(max(0.1, x_norm.max() - x_norm.min()))

    canonical_path = CANONICAL_DIR / f"{glyph_key}_v0.json"
    if canonical_path.exists():
        prev = json.loads(canonical_path.read_text(encoding="utf-8"))
    else:
        prev = {}
    glyph_name = prev.get("glyph") or _default_glyph_name(glyph_key)
    position = prev.get("position") or glyph_key.split("-")[-1]
    entry_coupling = (prev.get("entry") or {}).get("coupling", "baseline")
    exit_coupling = (prev.get("exit") or {}).get("coupling", "baseline")
    note = prev.get("_note", "")

    # Persist the dense raw path so a later /resample call can re-derive
    # anchors with a different n_anchors without the user redrawing.
    raw_stored = [
        {
            "x": round(float(p["x"]), 2),
            "y": round(float(p["y"]), 2),
            "pressure": None if p.get("pressure") is None else round(float(p["pressure"]), 4),
            "t": None if p.get("t") is None else round(float(p["t"]), 2),
        }
        for p in raw_path
    ]

    canonical = {
        "version": "v0",
        "glyph": glyph_name,
        "position": position,
        "variant": int(prev.get("variant", 0)),
        "advance": round(advance, 4),
        "_note": note,
        "_trace": {
            "source": "loth-1866",
            "method": "web-stylus",
            "chart_size": [1633, 1869],
            "bbox": {k: bbox[k] for k in ("y0", "y1", "x0", "x1")},
            "baseline_y": baseline_y,
            "midband_y": midband_y,
            "unit_px": unit_px,
            "n_anchors": n,
            "path_length_px": round(path_length_px, 1),
            "pixel_anchors": [[round(float(x), 2), round(float(y), 2)] for x, y in pixel_global],
            "half_widths_px": [round(h, 2) for h in hw_px.tolist()],
            "raw_path": raw_stored,
        },
        "entry": {
            "xy": entry_xy,
            "tangent_deg": round(entry_tan, 1),
            "coupling": entry_coupling,
        },
        "exit": {
            "xy": exit_xy,
            "tangent_deg": round(exit_tan, 1),
            "coupling": exit_coupling,
        },
        "strokes": [
            {
                "curve_type": "bspline",
                "anchors": [[round(float(x), 4), round(float(y), 4)] for x, y in zip(x_norm, y_norm, strict=True)],
                "half_widths": [round(float(h), 4) for h in hw_norm],
            }
        ],
    }
    canonical_path.write_text(json.dumps(canonical, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return canonical


def _default_glyph_name(glyph_key: str) -> str:
    """Best-effort glyph character for a brand-new canonical."""
    base = glyph_key.split("-")[0]
    return "ſ" if glyph_key == "s-medial" else base


def read_canonical(glyph_key: str) -> dict | None:
    """Return the canonical JSON for a glyph, or None if not yet traced."""
    path = CANONICAL_DIR / f"{glyph_key}_v0.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
