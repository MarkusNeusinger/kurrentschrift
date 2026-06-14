"""Sütterlin (Gleichzug) canonical derivation — skeleton-locked, constant nib.

A dedicated geometry path for the fixed-width scripts, separate from the
pressure-driven `core.pipeline.canonical_from_path`. Sütterlin is written with
a ball-tipped Redisfeder: the stroke width is constant (no Schwellzug), so the
whole spline → snap → refine → per-anchor-width apparatus that
`canonical_from_path` needs for a Spitzfeder is not just unnecessary here, it is
the source of the "unnatural" look — every smoothing/fitting stage is another
chance for the rendered silhouette to drift off the ink.

The commitment instead: the geometry IS the crop's medial axis. We skeletonise
the binarised crop (`skeletonize` == the centerline of a constant-width stroke,
by construction), snap the drawn Weg onto that skeleton to recover stroke order
and pen lifts (the ductus prior, architektur.md §2), and stamp a single
constant half-width — the median distance-transform on the skeleton, i.e. the
nib radius. Rendered as a constant-radius capsule union the silhouette hugs the
crop by construction: it cannot drift, because it is literally the skeleton
buffered. Round caps even match the Redisfeder's ball tip.

The drawn Weg therefore only supplies ORDER (and Absetzen): the geometry is
locked to the ink, so a rough trace still yields a clean glyph. The output dict
matches `canonical_from_path` field for field, so storage, the API and the
frontend render contract (`anchors` / `half_widths` / `stroke_starts` /
`outline_paths`) are unchanged — only the derivation is new.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

from core.chart import crop_with_mask, load_chart_grayscale
from core.extract import binarize_adaptive, skeleton_and_width

# Deliberately shared with the pressure pipeline. `_split_raw_strokes` is the
# single source of truth for pen-lift (Absetzen) splitting; `_resample_strokes`
# is the proven even-spacing + corner-knot (Umkehrpunkt) resampler — even
# spacing is what keeps the render's natural cubic spline from overshooting on a
# straight run; `_measurements` keeps the stored per-instance stats identical
# across both derivations. Re-implementing any of them here would risk silent
# divergence. The Gleichzug path only swaps in a skeleton snap + constant width.
from core.pipeline import DEFAULT_N_ANCHORS, _measurements, _resample_strokes, _split_raw_strokes
from core.quality import template_quality_metrics


# Dense resampling of the drawn Weg before snapping: ~1px chord spacing, so every
# skeleton pixel along the path gets a chance to be picked by the nearest-snap.
SNAP_RESAMPLE_PX = 1.0
# Snap cap as a multiple of the nib radius: a Weg drawn on the ink sits within
# ~one half-width of the centerline. Beyond this the nearest skeleton pixel is
# too far to trust as "the stroke this point meant" (it could be a crossing's
# other branch), so the drawn point keeps its position instead of jumping.
SNAP_CAP_RADIUS_FACTOR = 1.5
SNAP_CAP_MIN_PX = 4.0


def _constant_nib_radius(skel: np.ndarray, width_map: np.ndarray, mask: np.ndarray) -> float:
    """Median distance-transform on the skeleton = the Gleichzug half-width (px).

    The EDT equals the half stroke width only on the medial axis, so the median
    over the skeleton is the robust nib radius — robust to the eroded round ends
    (which read low) and the inflated crossings (which read high). Falls back to
    the mask median, then a 1px floor, on an empty skeleton.
    """
    if skel.any():
        vals = width_map[skel]
    elif mask.any():
        vals = width_map[mask]
    else:
        return 1.0
    return float(max(1.0, np.median(vals)))


def _resample_by_arc(points: np.ndarray, spacing_px: float) -> np.ndarray:
    """Resample an Mx2 polyline to ~`spacing_px` chord spacing (≥2 points)."""
    points = np.asarray(points, dtype=float)
    if len(points) < 2:
        return points
    diffs = np.diff(points, axis=0)
    cum = np.concatenate([[0.0], np.cumsum(np.hypot(diffs[:, 0], diffs[:, 1]))])
    total = float(cum[-1])
    if total == 0.0:
        return points[:1]
    n = max(2, int(round(total / max(spacing_px, 1e-3))) + 1)
    t = np.linspace(0.0, total, n)
    return np.column_stack([np.interp(t, cum, points[:, 0]), np.interp(t, cum, points[:, 1])])


def _snap_to_skeleton(points: np.ndarray, skel_xy: np.ndarray, tree: cKDTree, cap_px: float) -> np.ndarray:
    """Pull each point onto the nearest skeleton pixel (within cap); keep beyond-cap as drawn.

    Locks the drawn Weg onto the medial axis, so the geometry is the ink's, not
    the hand's. Beyond the cap the skeleton is too far to trust (a crossing's
    other branch), so the drawn point stands and the later snap-back continues.
    """
    if len(skel_xy) == 0:
        return points
    dist, idx = tree.query(points)
    snapped = skel_xy[idx].astype(float)
    beyond = dist > cap_px
    snapped[beyond] = points[beyond]
    return snapped


def _dedup(points: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Drop consecutive duplicate points (snapping collapses runs onto one pixel)."""
    if len(points) < 2:
        return points
    keep = np.ones(len(points), dtype=bool)
    keep[1:] = np.hypot(np.diff(points[:, 0]), np.diff(points[:, 1])) > eps
    return points[keep]


def _snap_strokes_to_skeleton(
    strokes_local: list[np.ndarray], skel: np.ndarray, width_map: np.ndarray, mask: np.ndarray
) -> tuple[list[np.ndarray], float]:
    """Snap each drawn stroke densely onto the skeleton; return strokes + nib radius.

    Each stroke is resampled to ~1px spacing and every sample pulled onto the
    nearest skeleton pixel, so the result is a dense polyline that traces the
    medial axis (including through corners) — the geometry is now the ink's, not
    the hand's. Even resampling + corner detection happen afterwards in the
    shared `_resample_strokes`. Strokes collapsing to <2 points are dropped.
    """
    r_px = _constant_nib_radius(skel, width_map, mask)
    skel_ys, skel_xs = np.where(skel)
    skel_xy = np.column_stack([skel_xs, skel_ys]).astype(float)
    tree = cKDTree(skel_xy) if len(skel_xy) else None
    cap_px = max(SNAP_CAP_MIN_PX, SNAP_CAP_RADIUS_FACTOR * r_px)

    snapped: list[np.ndarray] = []
    for stroke in strokes_local:
        pts = _resample_by_arc(stroke, SNAP_RESAMPLE_PX)
        if tree is not None:
            pts = _snap_to_skeleton(pts, skel_xy, tree, cap_px)
        pts = _dedup(pts)
        if len(pts) >= 2:
            snapped.append(pts)
    return snapped, r_px


def canonical_suetterlin_from_path(
    raw_path: list[dict], bbox: dict, chart_path: str, glyph: str, position: str, n_anchors: int | None = None
) -> dict:
    """Turn a dense stylus path into a canonical-template dict — Gleichzug variant.

    Same inputs and output shape as `core.pipeline.canonical_from_path`, but the
    geometry is the crop's skeleton (not a fitted spline) and the width is a
    single constant (not a measured profile). `n_anchors` is the even-resampling
    target (defaulting like the pressure pipeline); the geometry is locked to
    the skeleton regardless of the count.

    Steps:
      1. Load chart + crop with eraser/ink mask; binarize; skeleton + EDT.
      2. Split the raw path into pen-strokes (Absetzen) → crop-local pixels.
      3. Per stroke: resample densely, snap each sample onto the skeleton, dedup.
      4. Even-resample to `n` anchors with corner knots (shared `_resample_strokes`),
         so sharp turns render as kinks and straight runs do not overshoot.
      5. Stamp the constant nib radius (median EDT on the skeleton).
      6. Score the result against the crop (`trace_meta["quality"]`).
      7. Normalise pixel → template coords; derive entry/exit + measurements.
    """
    for required in ("baseline_y", "midband_y", "y0", "y1", "x0", "x1"):
        if bbox.get(required) is None:
            raise ValueError(f"bbox missing required field {required!r}")
    if len(raw_path) < 2:
        raise ValueError("stylus path needs at least 2 points")

    chart_gray = load_chart_grayscale(chart_path)
    crop = crop_with_mask(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop, fill_holes_max_area=int(bbox.get("fill_holes_max_area") or 0))
    skel, width_map = skeleton_and_width(mask)

    x0, y0 = bbox["x0"], bbox["y0"]
    baseline_y = int(bbox["baseline_y"])
    midband_y = int(bbox["midband_y"])
    unit_px = float(baseline_y - midband_y)
    if unit_px <= 0:
        raise ValueError(f"baseline_y ({baseline_y}) must exceed midband_y ({midband_y})")

    strokes_local = [
        np.array([(p["x"] - x0, p["y"] - y0) for p in stroke], dtype=float) for stroke in _split_raw_strokes(raw_path)
    ]
    snapped, r_px = _snap_strokes_to_skeleton(strokes_local, skel, width_map, mask)
    if not snapped:
        raise ValueError("no usable strokes after snapping to skeleton")

    # Even-spaced anchors with corner knots (shared resampler): even spacing is
    # what keeps the render's natural cubic spline from overshooting on the long
    # straight runs that snapping-then-Douglas-Peucker would leave clustered.
    n = int(n_anchors or bbox.get("n_anchors") or DEFAULT_N_ANCHORS)
    resampled_local, stroke_starts, corner_anchors_idx, path_length_px = _resample_strokes(snapped, n, unit_px)
    hw_px = np.full(len(resampled_local), r_px, dtype=float)

    # Image-space self-check: how well does the rendered silhouette match the crop?
    try:
        quality = template_quality_metrics(
            resampled_local,
            hw_px,
            stroke_starts,
            mask,
            skel,
            width_map,
            unit_px=unit_px,
            corner_anchors=corner_anchors_idx,
        )
    except ValueError:
        quality = None

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
            "method": "suetterlin-gleichzug",
            "bbox_snapshot": {k: bbox[k] for k in ("y0", "y1", "x0", "x1")},
            "baseline_y": baseline_y,
            "midband_y": midband_y,
            "unit_px": unit_px,
            "n_anchors": len(anchors_norm),
            "stroke_starts": stroke_starts,
            # The Gleichzug nib radius (px) the constant half-width was stamped from.
            "nib_radius_px": round(r_px, 3),
            # Snap/refine are pressure-pipeline stages; recorded as not-applicable
            # so the diagnostic/preview reads a uniform trace_meta shape.
            "snap": {"applied": False, "reason": "gleichzug: skeleton is the centerline"},
            "refine": {"applied": False, "reason": "gleichzug: constant width, no edge refine"},
            "quality": quality,
            # No crossing-width resolution: the width is a single constant.
            "crossing_anchors": [],
            "corner_anchors": corner_anchors_idx,
            "path_length_px": round(path_length_px, 1),
            "pixel_anchors": [[round(float(x), 2), round(float(y), 2)] for x, y in pixel_global],
            "half_widths_px": [round(float(h), 2) for h in hw_px],
        },
        "measurements": _measurements(anchors_norm, hw_px, path_length_px, bbox),
    }


def canonical_suetterlin_from_raw_path_only(glyph_row: dict, bbox: dict, chart_path: str, n_anchors: int) -> dict:
    """Re-derive a Sütterlin canonical from an existing glyph's stored `raw_path`.

    The Gleichzug twin of `core.pipeline.canonical_from_raw_path_only`, used by
    the /resample and /quality endpoints for constant-width styles.
    """
    return canonical_suetterlin_from_path(
        raw_path=glyph_row["raw_path"],
        bbox=bbox,
        chart_path=chart_path,
        glyph=glyph_row["glyph"],
        position=glyph_row["position"],
        n_anchors=n_anchors,
    )
