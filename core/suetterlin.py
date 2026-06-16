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
constant half-width — the histogram MODE of the distance-transform on the
skeleton, i.e. the nib radius. Rendered as a constant-radius capsule union the
silhouette hugs the crop by construction: it cannot drift, because it is
literally the skeleton buffered. Round caps even match the Redisfeder's ball tip.

Two refinements handle where two strokes run together — a t/s loop, the long
Spitze where an up- and a down-stroke nearly coincide:

* Nib radius from the histogram mode, not the median. The skeleton of a merged
  double stroke is a single central line whose EDT reads ~2x the nib, so its
  width values are a high tail on the histogram. A median is dragged up by that
  tail (worse when several merge depths coexist); the mode is not, because the
  lone single-stroke nib is still the single most-common width across the glyph.
* Edge-following snap. Where the drawn point sits over a merged region (its
  nearest skeleton pixel reads a half-width well above the nib radius) the two
  passes must NOT collapse onto the shared centerline — the pen ran up the left
  edge and back down the right. Each point is offset from the central skeleton
  toward its own edge by (local half-width − nib radius), the side taken from
  the drawn trace (the ductus prior). Single strokes (EDT ≈ nib) snap to the
  centerline exactly as before; round stroke ends (EDT < nib) get no offset.

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
# other branch), so the drawn point keeps its position instead of jumping. In a
# merged region the legitimate drawn position is farther from the central
# skeleton (out at the ink edge), so the cap is raised per point to the local
# ink half-width — `_snap_to_skeleton_edges` widens it where the blob is wide.
SNAP_CAP_RADIUS_FACTOR = 1.5
SNAP_CAP_MIN_PX = 4.0

# Histogram bin (px) for the modal nib radius. 1px matches the EDT quantisation;
# the modal bin is then refined to sub-pixel by its own median.
NIB_HISTOGRAM_BIN_PX = 1.0

# Edge-following snap: a drawn point whose nearest skeleton pixel reads a
# half-width more than MERGE_EXCESS_FACTOR above the nib radius (and at least
# MERGE_EXCESS_MIN_PX px above, so EDT quantisation on a plain single stroke
# never triggers) sits over a merged double stroke and is pushed toward its own
# edge instead of the shared centerline.
MERGE_EXCESS_FACTOR = 0.3
MERGE_EXCESS_MIN_PX = 1.5

# Crossing (Kreuzung) vs. merge discrimination — the wide EDT blob at a
# transversal crossing must NOT be edge-split: the stroke passes straight
# through at one nib thickness, no widening, no lateral shove. A wide point is a
# crossing (offset suppressed) when ANOTHER pass of the trace comes within reach
# of the blob, is far away along the path (not the same stroke's own neighbours),
# AND runs transversally. A parallel/anti-parallel pass (the two sides of a t/s
# loop) is a real merge and keeps its edge offset. Mirrors the width-channel
# crossing test in `core.pipeline._resolve_crossing_widths`.
CROSSING_MIN_ANGLE_DEG = 25.0
CROSSING_MIN_ARC_FACTOR = 3.0


def _modal_half_width(values: np.ndarray) -> float | None:
    """The most-common half-width (histogram mode, sub-pixel-refined), or None.

    The EDT on a constant-width stroke clusters tightly at the nib radius, so on
    a glyph that is mostly single-stroke the nib is the tallest bin. Merged
    double strokes (t/s loops, a Spitze) read ~2x the nib and pile into higher
    bins — a high tail that pulls the *median* up but leaves the *mode* on the
    true nib. Picking the modal 1px bin and taking the median WITHIN it recovers
    the nib to sub-pixel. Returns None when there is no positive width to bin.
    """
    vals = np.asarray(values, dtype=float)
    vals = vals[vals > 0]
    if vals.size == 0:
        return None
    lo = float(np.floor(vals.min()))
    hi = float(np.ceil(vals.max()))
    if hi <= lo:
        return float(vals[0])
    edges = np.arange(lo, hi + NIB_HISTOGRAM_BIN_PX, NIB_HISTOGRAM_BIN_PX)
    counts, edges = np.histogram(vals, bins=edges)
    peak = int(np.argmax(counts))
    in_modal = vals[(vals >= edges[peak]) & (vals < edges[peak + 1])]
    return float(np.median(in_modal)) if in_modal.size else float((edges[peak] + edges[peak + 1]) / 2.0)


def _constant_nib_radius(skel: np.ndarray, width_map: np.ndarray, mask: np.ndarray) -> float:
    """Histogram mode of the distance-transform on the skeleton = the nib radius (px).

    The EDT equals the half stroke width only on the medial axis. The modal
    width (see `_modal_half_width`) is the robust nib radius: robust to the
    eroded round ends (which read low) and, crucially, to merged double strokes
    (which read ~2x and would drag a median up). Falls back to the mask values,
    then a 1px floor, on an empty skeleton.
    """
    if skel.any():
        modal = _modal_half_width(width_map[skel])
    elif mask.any():
        modal = _modal_half_width(width_map[mask])
    else:
        modal = None
    return float(max(1.0, modal)) if modal is not None else 1.0


def _resample_by_arc(points: np.ndarray, spacing_px: float) -> np.ndarray:
    """Resample an Mx2 polyline to ~`spacing_px` chord spacing.

    A non-degenerate polyline resamples to ≥2 points. Degenerate inputs are
    passed through unchanged: fewer than 2 points returns the input as-is, and a
    zero-length polyline collapses to its single distinct point. The caller
    (`_snap_strokes_to_skeleton`) drops any stroke left with <2 points.
    """
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


def _unit_tangents(points: np.ndarray) -> np.ndarray:
    """Unit tangents of a densely-ordered (~1px) polyline via np.gradient."""
    tangent = np.gradient(points, axis=0)
    tnorm = np.hypot(tangent[:, 0], tangent[:, 1])
    tnorm[tnorm == 0] = 1.0
    return tangent / tnorm[:, None]


def _crossing_mask(
    centers: np.ndarray, tangents: np.ndarray, stroke_id: np.ndarray, arc: np.ndarray, hw_c: np.ndarray, r_px: float
) -> np.ndarray:
    """Per-point flag: a wide blob here is a transversal crossing, not a merge.

    A wide point (EDT well above the nib) is a crossing when ANOTHER pass of the
    trace — a different stroke, or the same stroke far enough along the path that
    it is not just this point's own neighbours — comes within reach of the blob
    AND runs transversally (turning angle above CROSSING_MIN_ANGLE_DEG). The two
    anti-parallel sides of a t/s loop fail the angle test and stay a merge, so
    their edge offset is kept; an X- or +-crossing trips it and is suppressed so
    the stroke passes straight through at one nib thickness.
    """
    n = len(centers)
    flagged = np.zeros(n, dtype=bool)
    excess = hw_c - r_px
    wide = np.flatnonzero(excess > max(MERGE_EXCESS_MIN_PX, MERGE_EXCESS_FACTOR * r_px))
    if n < 2 or wide.size == 0:
        return flagged
    tree = cKDTree(centers)
    sin_thr = np.sin(np.deg2rad(CROSSING_MIN_ANGLE_DEG))
    arc_scale = CROSSING_MIN_ARC_FACTOR * 2.0 * r_px
    for i in wide:
        radius = max(2.0 * r_px, hw_c[i] + r_px)
        for j in tree.query_ball_point(centers[i], radius):
            if j == i:
                continue
            other_pass = stroke_id[j] != stroke_id[i] or abs(arc[i] - arc[j]) > arc_scale
            if not other_pass:
                continue
            cross = abs(tangents[i, 0] * tangents[j, 1] - tangents[i, 1] * tangents[j, 0])
            if cross > sin_thr:
                flagged[i] = True
                break
    return flagged


def _apply_edge_offset(
    points: np.ndarray,
    tangent: np.ndarray,
    centers: np.ndarray,
    hw_c: np.ndarray,
    dist: np.ndarray,
    suppress: np.ndarray,
    cap_px: float,
    r_px: float,
) -> np.ndarray:
    """Snap onto the medial axis, offsetting to the EDGE in (non-crossing) merges.

    On a single stroke the nearest skeleton pixel reads a half-width ≈ the nib
    radius and the point snaps straight onto the centerline (the geometry is the
    ink's, not the hand's). Where two strokes run together the nearest skeleton
    pixel is the SHARED central line of the merged blob and reads a half-width
    well above the nib; collapsing both passes onto it would draw one stroke down
    the middle. Instead the point is offset from that centerline toward its own
    edge by (local half-width − nib radius): the side comes from the drawn trace
    (its lateral position relative to the centerline, the ductus prior), the
    magnitude from the ink. `suppress` marks transversal crossings — there the
    blob is a Kreuzung, not a merge, so the offset is skipped and the stroke
    passes straight through at one nib thickness. Round stroke ends read EDT <
    nib, so they get no offset. Beyond the (locally widened) cap the skeleton is
    too far to trust, so the drawn point stands.
    """
    rel = points - centers
    along = (rel * tangent).sum(axis=1)
    lateral = rel - along[:, None] * tangent
    lat_norm = np.hypot(lateral[:, 0], lateral[:, 1])

    excess = hw_c - r_px
    merged = (excess > max(MERGE_EXCESS_MIN_PX, MERGE_EXCESS_FACTOR * r_px)) & (lat_norm > 1e-3) & (~suppress)

    snapped = centers.copy()
    if merged.any():
        unit = lateral[merged] / lat_norm[merged, None]
        snapped[merged] = centers[merged] + excess[merged, None] * unit

    # In a merged region the legitimate drawn point sits out at the ink edge,
    # i.e. up to one local half-width from the central skeleton — raise the cap
    # there so a well-drawn edge trace is not rejected as "too far".
    cap_local = np.maximum(cap_px, hw_c + 1.0)
    beyond = dist > cap_local
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
    medial axis — straight onto the centerline on a single stroke, out to its
    own edge where two strokes have merged (`_apply_edge_offset`), straight
    through where two strokes cross transversally (`_crossing_mask` suppresses
    the offset). The result is a dense polyline tracing the ink (including
    through corners), the geometry now the ink's, not the hand's. Crossing
    detection needs every stroke at once (one pass can cross another), so the
    dense snap-to-centre for all strokes happens first, then the offset.
    Even resampling + corner detection happen afterwards in the shared
    `_resample_strokes`. Strokes collapsing to <2 points are dropped.
    """
    r_px = _constant_nib_radius(skel, width_map, mask)
    skel_ys, skel_xs = np.where(skel)
    skel_xy = np.column_stack([skel_xs, skel_ys]).astype(float)
    skel_w = width_map[skel_ys, skel_xs].astype(float)
    tree = cKDTree(skel_xy) if len(skel_xy) else None
    cap_px = max(SNAP_CAP_MIN_PX, SNAP_CAP_RADIUS_FACTOR * r_px)

    # Pass 1 — dense resample per stroke, snap each sample to the NEAREST
    # skeleton centre, and gather the per-point geometry the crossing test and
    # the edge offset both need (centre, local half-width, drawn tangent, arc).
    dense: list[dict] = []
    for sid, stroke in enumerate(strokes_local):
        pts = _resample_by_arc(stroke, SNAP_RESAMPLE_PX)
        if len(pts) < 2:
            continue
        tangent = _unit_tangents(pts)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        arc = np.concatenate([[0.0], np.cumsum(seg)])
        if tree is not None:
            dist, idx = tree.query(pts)
            centers = skel_xy[idx].astype(float)
            hw_c = skel_w[idx]
        else:
            centers, hw_c, dist = pts.copy(), np.full(len(pts), r_px), np.zeros(len(pts))
        dense.append(
            {"pts": pts, "tangent": tangent, "centers": centers, "hw_c": hw_c, "dist": dist, "arc": arc, "sid": sid}
        )

    if not dense:
        return [], r_px

    # Pass 2 — flag transversal crossings across ALL strokes at once, so the
    # offset is suppressed exactly where the wide blob is a Kreuzung.
    centers_all = np.vstack([d["centers"] for d in dense])
    tangents_all = np.vstack([d["tangent"] for d in dense])
    hw_all = np.concatenate([d["hw_c"] for d in dense])
    arc_all = np.concatenate([d["arc"] for d in dense])
    sid_all = np.concatenate([np.full(len(d["pts"]), d["sid"]) for d in dense])
    suppress_all = _crossing_mask(centers_all, tangents_all, sid_all, arc_all, hw_all, r_px)

    # Pass 3 — apply the edge offset per stroke (offset in merges, straight in
    # crossings), dedup, and drop strokes that collapse to <2 points.
    snapped: list[np.ndarray] = []
    cursor = 0
    for d in dense:
        k = len(d["pts"])
        suppress = suppress_all[cursor : cursor + k]
        cursor += k
        if tree is None:
            pts = d["pts"]
        else:
            pts = _apply_edge_offset(d["pts"], d["tangent"], d["centers"], d["hw_c"], d["dist"], suppress, cap_px, r_px)
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
