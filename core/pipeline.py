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
from core.fit import fit_template_to_instance, refine_template_against_crop
from core.quality import template_quality_metrics
from core.template import (
    allocate_samples,
    build_sample_plan,
    capsule_union_rings,
    chord_length,
    multi_stroke_centerlines,
    multi_stroke_silhouettes,
    sample_with_sample_plan,
    template_guides,
)
from core.widths import resolve_half_widths


# Anchor-count default, calibrated on the glyph bench (12 authored Loth
# glyphs, image-space loss vs frozen references): 50→0.1488, 80→0.1363,
# 120→0.1339, 160→0.1321, 240→0.1563. The old 50-anchor "jitter knee" no
# longer binds — the boundary refine de-noises anchors and widths, so extra
# anchors buy width-profile and curve fidelity instead of reproducing hand
# wobble (hairline glyphs gain most: u-final 0.204→0.115). Past ~160 quality
# REGRESSES: the 240-sample render stops oversampling the spline and the
# refine's parameter count outgrows its iteration budget. 120 is the knee
# with the best worst-glyph balance.
DEFAULT_N_ANCHORS = 120

# Snapping the drawn Weg onto the ink: per-anchor displacement bound in
# template units (x-height = 1). Generous against hand wobble, far below the
# anchor spacing, so the drawn topology (loop direction, crossing order)
# cannot fold during the snap.
SNAP_MAX_ANCHOR_DELTA = 0.3
# Tikhonov weight for the snap, softer than the M4 default (1.0): with equal
# weights the quadratic equilibrium removes only half the hand wobble. The
# trace already sits on the ink, so the displacement bound carries the
# topology guard and the regulariser only needs to keep the blob-skeleton
# ambiguity at crossings from wiggling the anchors.
SNAP_LAMBDA_REG = 0.25

# Corner-knot detection (German: Umkehrpunkt) on the dense raw trace. A corner
# is a within-stroke reversal — pen stays down, direction changes sharply —
# which a single chord-length spline rounds away. Tangents are estimated over
# an arc-length window in x-height units so stylus jitter cannot fake a corner:
CORNER_WINDOW_UNITS = 0.12
# Turning angle (deviation from straight) above which a point is a corner
# candidate. For a circular arc the deviation over the window is ~window/radius
# radians, so 75° only triggers below radius ≈ 0.09 x-heights — far tighter
# than any Kurrent loop (the small e-eye is ~0.15–0.25) — while true reversals
# (retraces, the Loth K's angular joints) sit at 90–180°.
CORNER_ANGLE_DEG = 75.0
# Non-max suppression separation (in windows) and a per-stroke cap so jitter
# bursts cannot shatter a stroke into sub-arc confetti.
MAX_CORNERS_PER_STROKE = 4

# Crossing detection for the width channel. Two anchors of the trace count as
# a crossing when ALL three hold: another pass comes within this factor of
# their summed half-widths (the ink blobs overlap) …
CROSSING_PROXIMITY_FACTOR = 1.5
# … they are far apart along the path, in the same summed-half-width scale —
# neighbouring anchors on one thick stroke are never their own crossing
# (must exceed the proximity factor, so a straight run cannot self-mark) …
CROSSING_MIN_ARC_FACTOR = 3.0
# … and the passes are transversal. Below this angle they run (anti)parallel:
# a retrace over the same ink, whose measured width is real and must be kept.
CROSSING_MIN_ANGLE_DEG = 15.0


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


def _detect_corners(stroke_px: np.ndarray, unit_px: float) -> list[float]:
    """Arc-length positions of within-stroke reversal corners on a dense stroke.

    For each point, the incoming/outgoing tangents are chords spanning
    CORNER_WINDOW_UNITS of arc on either side; the turning angle between them
    (deviation from straight) marks a corner when it exceeds CORNER_ANGLE_DEG.
    Candidates within a window of either stroke end are excluded by
    construction (no full window fits), greedy non-max suppression keeps the
    sharpest candidate per 2-window neighbourhood, and MAX_CORNERS_PER_STROKE
    caps the result. Returns sorted arc positions (px) for knot-forced
    resampling.
    """
    stroke_px = np.asarray(stroke_px, dtype=float)
    if len(stroke_px) < 3:
        return []
    seg = np.hypot(*np.diff(stroke_px, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(s[-1])
    window = max(3.0, CORNER_WINDOW_UNITS * unit_px)
    if total < 2.0 * window:
        return []

    # Chord endpoints one window of arc behind/ahead of each point.
    idx_in = np.searchsorted(s, s - window, side="left")
    idx_out = np.searchsorted(s, s + window, side="left")
    valid = (s >= window) & (s <= total - window) & (idx_out < len(s))
    k = np.where(valid)[0]
    if len(k) == 0:
        return []
    v_in = stroke_px[k] - stroke_px[idx_in[k]]
    v_out = stroke_px[np.minimum(idx_out[k], len(s) - 1)] - stroke_px[k]
    norms = np.hypot(v_in[:, 0], v_in[:, 1]) * np.hypot(v_out[:, 0], v_out[:, 1])
    norms[norms == 0] = 1.0
    cos_theta = np.clip((v_in * v_out).sum(axis=1) / norms, -1.0, 1.0)
    theta_deg = np.degrees(np.arccos(cos_theta))

    candidates = [
        (float(theta_deg[i]), float(s[k[i]])) for i in np.argsort(-theta_deg) if theta_deg[i] >= CORNER_ANGLE_DEG
    ]
    accepted: list[float] = []
    for _, arc in candidates:
        if len(accepted) >= MAX_CORNERS_PER_STROKE:
            break
        if all(abs(arc - a) >= 2.0 * window for a in accepted):
            accepted.append(arc)
    return sorted(accepted)


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


def _point_at_arc(points: np.ndarray, s: np.ndarray, arc: float) -> np.ndarray:
    """Point on a polyline at cumulative arc length `arc` (linear interpolation)."""
    j = int(np.clip(np.searchsorted(s, arc, side="right"), 1, len(points) - 1))
    span = s[j] - s[j - 1]
    t = 0.0 if span == 0 else (arc - s[j - 1]) / span
    return points[j - 1] + t * (points[j] - points[j - 1])


def _resample_polyline_with_knots(points: np.ndarray, n: int, knots_s: list[float]) -> tuple[np.ndarray, list[int]]:
    """Chord-length resample with an anchor forced EXACTLY at each knot arc position.

    The polyline is split at the knots, each segment resampled independently
    (allocation proportional to length, ≥2 each), and the duplicated knot
    points of the trailing segments dropped — so the total stays `n` and every
    knot owns exactly one anchor. Returns `(anchors, local knot indices)`.
    Without knots this is `_resample_polyline` unchanged.
    """
    if not knots_s:
        resampled, _ = _resample_polyline(points, n)
        return resampled, []
    seg = np.hypot(*np.diff(points, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    bounds_s = [0.0, *sorted(knots_s), float(s[-1])]
    alloc = allocate_samples(np.diff(bounds_s).tolist(), n + len(knots_s))
    parts: list[np.ndarray] = []
    knot_indices: list[int] = []
    count = 0
    for i, (a, b, k) in enumerate(zip(bounds_s[:-1], bounds_s[1:], alloc, strict=True)):
        inner = points[(s > a) & (s < b)]
        sub = np.vstack([_point_at_arc(points, s, a), *inner, _point_at_arc(points, s, b)])
        resampled, _ = _resample_polyline(sub, max(2, k))
        if i > 0:
            resampled = resampled[1:]  # the knot point already ends the previous segment
            knot_indices.append(count - 1)
        parts.append(resampled)
        count += len(resampled)
    return np.concatenate(parts, axis=0), knot_indices


def _resample_strokes(
    strokes: list[np.ndarray], n: int, unit_px: float
) -> tuple[np.ndarray, list[int], list[int], float]:
    """Resample each pen-stroke independently by chord length and concatenate.

    Returns the concatenated `(N, 2)` anchor array, `stroke_starts` (the anchor
    index where each stroke begins, first is 0), the global indices of detected
    corner-knot anchors (within-stroke reversals get an anchor exactly on the
    corner), and the summed path length in pixels — the pen-lift bridges
    *between* strokes are excluded, so a u's two downstrokes never get joined
    by a phantom anchor across the gap. `N` equals `n` except when `n` is too
    small to give every stroke two anchors, when it grows to `2 * num_strokes`.
    """
    strokes = [s for s in strokes if len(s) >= 1]
    if not strokes:
        raise ValueError("empty path")
    seg_lengths = [chord_length(s) for s in strokes]
    alloc = [n] if len(strokes) == 1 else allocate_samples(seg_lengths, n)
    parts, starts, corner_anchors, total, cursor = [], [], [], 0.0, 0
    for stroke, k, length in zip(strokes, alloc, seg_lengths, strict=True):
        knots = _detect_corners(stroke, unit_px)
        resampled, local_knots = _resample_polyline_with_knots(stroke, max(2, k), knots)
        starts.append(cursor)
        corner_anchors.extend(cursor + c for c in local_knots)
        parts.append(resampled)
        cursor += len(resampled)
        total += length
    return np.concatenate(parts, axis=0), starts, corner_anchors, total


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


def _snap_anchors_to_ink(
    anchors_local: np.ndarray,
    stroke_starts: list[int],
    skel: np.ndarray,
    width_map: np.ndarray,
    unit_px: float,
    baseline_y_local: float,
    corner_anchors: list[int] | None = None,
) -> tuple[np.ndarray, dict]:
    """Pull the resampled trace anchors onto the ink's medial axis (crop px).

    The drawn Weg is the ductus prior — stroke order, pen lifts, crossing
    resolution (architektur.md §2); the precise geometry belongs to the ink.
    Reuses the regularised M4 fit against the trace's own crop: on clean
    stretches the EDT field pulls the anchors onto the skeleton centerline and
    hand wobble disappears; at a crossing the field is flat and ambiguous, so
    the Tikhonov term lets the drawn path win — exactly where the drawing is
    more trustworthy than the skeleton blob. Per-stroke sampling never bridges
    a pen lift, and a retrace (same path down and back up) simply pulls both
    passes onto the same centerline. Known bias: `skeletonize` erodes round
    stroke ends by up to the half-width, so end anchors get pulled slightly
    inward — the displacement bound and the regulariser keep it mild.

    Returns the snapped crop-local anchors plus a meta dict for `trace_meta`.
    """
    if not bool(skel.any()):
        return anchors_local, {"applied": False, "reason": "empty skeleton"}
    x_origin_px = float(anchors_local[0, 0])
    template_anchors = np.column_stack(
        [(anchors_local[:, 0] - x_origin_px) / unit_px, (baseline_y_local - anchors_local[:, 1]) / unit_px]
    )
    result = fit_template_to_instance(
        template_anchors,
        np.zeros(len(template_anchors)),
        skel,
        width_map,
        unit_px=unit_px,
        baseline_y_px=baseline_y_local,
        x_origin_px=x_origin_px,
        stroke_starts=stroke_starts,
        corner_anchors=corner_anchors,
        # Geometry-only refinement: half-widths are measured AFTER the snap
        # (on the medial axis the anchors now sit on), so the width residual
        # would only chase its own input here.
        width_weight=0.0,
        lambda_reg=SNAP_LAMBDA_REG,
        max_anchor_delta=SNAP_MAX_ANCHOR_DELTA,
    )
    # Fold the fit's global translation back into pixel coordinates via the
    # effective placement — the snapped positions are exact regardless of how
    # the optimiser split the movement between translation and anchor deltas.
    snapped = np.column_stack(
        [
            result.placement["x_origin_px"] + result.anchors[:, 0] * unit_px,
            result.placement["baseline_y_px"] - result.anchors[:, 1] * unit_px,
        ]
    )
    shift_px = np.hypot(snapped[:, 0] - anchors_local[:, 0], snapped[:, 1] - anchors_local[:, 1])
    meta = {
        "applied": True,
        "geo_rmse_px": result.fit_meta["geo_rmse_px"],
        "coverage_rmse_px": result.fit_meta["coverage_rmse_px"],
        "max_shift_px": round(float(shift_px.max()), 2),
        "mean_shift_px": round(float(shift_px.mean()), 2),
    }
    return snapped, meta


def _resolve_crossing_widths(
    anchors_px: np.ndarray, hw_px: np.ndarray, stroke_starts: list[int]
) -> tuple[np.ndarray, list[int]]:
    """Crossing resolution for the width channel — interpolate across blobs.

    At a crossing the distance transform measures the union blob of both
    passes, not the stroke the anchor belongs to: the width profile flares
    out before/after the crossing (and only *looks* repaired once the second
    pass visually covers the flare — the stored value stays wrong). The
    ductus prior resolves this like it resolves the geometry: an anchor's
    width reading is contaminated when another pass of the trace is proximate
    (CROSSING_PROXIMITY_FACTOR), far away along the path
    (CROSSING_MIN_ARC_FACTOR) and transversal (CROSSING_MIN_ANGLE_DEG — a
    retrace runs parallel and its measured width is real ink). Note the
    retrace caveat for a Spitzfeder: the measured value is the UNION of both
    passes, i.e. the wide downstroke; a hairline pass underneath is invisible
    in the static image. Both passes get the union width, which renders
    identically — separating them needs a direction-dependent width prior
    aggregated across glyphs (post-MVP style analysis, architektur.md §12).
    Contaminated runs
    are replaced by linear interpolation from the clean widths on either
    side, per pass through the crossing; a stroke contaminated end-to-end
    keeps its measured widths rather than inventing values. A merged tight
    loop (filled counter) reads as parallel and is deliberately kept — the
    blob there is what the eye sees.

    Returns the resolved widths plus the contaminated anchor indices.
    """
    n = len(anchors_px)
    if n < 3:
        return hw_px, []
    bounds = [*stroke_starts, n]
    stroke_id = np.empty(n, dtype=int)
    arc = np.zeros(n)
    tangents = np.zeros((n, 2))
    for s, (a, b) in enumerate(zip(bounds[:-1], bounds[1:], strict=True)):
        stroke_id[a:b] = s
        seg = anchors_px[a:b]
        if len(seg) < 2:
            continue
        d = np.diff(seg, axis=0)
        arc[a:b] = np.concatenate([[0.0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))])
        t = np.gradient(seg, axis=0)
        norm = np.hypot(t[:, 0], t[:, 1])
        norm[norm == 0] = 1.0
        tangents[a:b] = t / norm[:, None]

    # All-pairs tests — anchor counts are ~50, brute force beats a KD-tree.
    diff = anchors_px[:, None, :] - anchors_px[None, :, :]
    dist = np.hypot(diff[..., 0], diff[..., 1])
    hw_sum = hw_px[:, None] + hw_px[None, :]
    proximate = dist < CROSSING_PROXIMITY_FACTOR * hw_sum
    same_stroke = stroke_id[:, None] == stroke_id[None, :]
    arc_sep = np.abs(arc[:, None] - arc[None, :])
    far_on_path = ~same_stroke | (arc_sep > CROSSING_MIN_ARC_FACTOR * hw_sum)
    cross = np.abs(tangents[:, None, 0] * tangents[None, :, 1] - tangents[:, None, 1] * tangents[None, :, 0])
    transversal = cross > np.sin(np.deg2rad(CROSSING_MIN_ANGLE_DEG))
    contaminated = (proximate & far_on_path & transversal).any(axis=1)

    resolved = hw_px.astype(float).copy()
    indices: list[int] = []
    for a, b in zip(bounds[:-1], bounds[1:], strict=True):
        seg = contaminated[a:b].copy()
        if not seg.any():
            continue
        # The blob inflates the reading a little beyond the geometric overlap
        # — widen each run by one anchor on both sides (within its stroke).
        seg[:-1] |= contaminated[a + 1 : b]
        seg[1:] |= contaminated[a : b - 1]
        if seg.all():
            continue
        pos = np.arange(b - a)
        resolved[a:b][seg] = np.interp(pos[seg], pos[~seg], resolved[a:b][~seg])
        indices.extend(int(i) for i in (a + pos[seg]))
    return resolved, indices


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
    raw_path: list[dict],
    bbox: dict,
    chart_path: str,
    glyph: str,
    position: str,
    n_anchors: int | None = None,
    snap_to_ink: bool = True,
    refine: bool = True,
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
      4. Resample the polyline by chord length to N anchors (per pen-stroke).
      5. Snap the anchors onto the ink's medial axis (regularised fit): the
         drawn Weg keeps stroke order + crossing resolution, the ink supplies
         the precise geometry. `snap_to_ink=False` keeps the raw trace.
      6. Sample half-width per anchor from the distance-transform; resolve
         crossing-blob readings by interpolating across detected crossings.
      7. Refine anchors AND half-widths against the ink edge itself
         (`refine_template_against_crop`): the rendered silhouette boundary is
         pulled onto the binarized ink edge, averaging out the per-point EDT
         noise (quantisation, stair-stepping on slanted strokes, tilted
         readings on tapers) that the point measurements cannot avoid.
         `refine=False` keeps the measured values.
      8. Score the result against the crop (`trace_meta["quality"]`).
      9. Normalise pixel → template coords (baseline=0, midband=1).
      10. Compute entry/exit tangents from first/last anchor pairs.
      11. Derive per-instance measurements (slant, mean width, path length).
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
    strokes_local = [
        np.array([(p["x"] - x0, p["y"] - y0) for p in stroke], dtype=float) for stroke in _split_raw_strokes(raw_path)
    ]

    baseline_y = int(bbox["baseline_y"])
    midband_y = int(bbox["midband_y"])
    unit_px = float(baseline_y - midband_y)
    if unit_px <= 0:
        raise ValueError(f"baseline_y ({baseline_y}) must exceed midband_y ({midband_y})")

    n = int(n_anchors or bbox.get("n_anchors") or DEFAULT_N_ANCHORS)
    # Resample stroke-by-stroke so a pen lift never gets a phantom anchor bridging
    # the gap; `stroke_starts` records where each stroke begins in the anchor list,
    # `corner_anchors` which anchors sit exactly on detected within-stroke reversals.
    resampled_local, stroke_starts, corner_anchors_idx, path_length_px = _resample_strokes(strokes_local, n, unit_px)

    snap_meta: dict = {"applied": False}
    if snap_to_ink:
        resampled_local, snap_meta = _snap_anchors_to_ink(
            resampled_local, stroke_starts, skel, width_map, unit_px, float(baseline_y - y0), corner_anchors_idx
        )
        if snap_meta["applied"]:
            seg_bounds = [*stroke_starts, len(resampled_local)]
            path_length_px = sum(
                chord_length(resampled_local[a:b]) for a, b in zip(seg_bounds[:-1], seg_bounds[1:], strict=True)
            )

    # Snap no farther than a quarter x-height: generous against trace wobble,
    # tight enough not to jump to a neighbouring stroke.
    hw_px = half_widths_on_medial_axis(resampled_local, skel, mask, width_map, snap_cap_px=max(3.0, 0.25 * unit_px))
    hw_px, crossing_anchors = _resolve_crossing_widths(resampled_local, hw_px, stroke_starts)
    # Median/box smoothing stays as INITIALISATION; the refine's per-chain
    # curvature regulariser is the final arbiter of the width profile.
    hw_px = _smooth_half_widths(hw_px, stroke_starts)

    # Refine is stage 2 of "fit the drawing to the ink": it only runs when the
    # snap ran — a caller that disables snapping wants the drawn geometry kept.
    refine_meta: dict = {"applied": False}
    if refine and snap_meta.get("applied") and bool(skel.any()):
        baseline_y_local = float(baseline_y - y0)
        x_origin_local = float(resampled_local[0, 0])
        refine_anchors = np.column_stack(
            [(resampled_local[:, 0] - x_origin_local) / unit_px, (baseline_y_local - resampled_local[:, 1]) / unit_px]
        )
        try:
            refined = refine_template_against_crop(
                refine_anchors,
                hw_px / unit_px,
                skel,
                width_map,
                unit_px=unit_px,
                baseline_y_px=baseline_y_local,
                x_origin_px=x_origin_local,
                stroke_starts=stroke_starts,
                corner_anchors=corner_anchors_idx,
                crossing_anchors=crossing_anchors,
            )
        except ValueError as exc:
            refine_meta = {"applied": False, "reason": str(exc)}
        else:
            resampled_local = np.column_stack(
                [x_origin_local + refined.anchors[:, 0] * unit_px, baseline_y_local - refined.anchors[:, 1] * unit_px]
            )
            hw_px = refined.half_widths * unit_px
            seg_bounds = [*stroke_starts, len(resampled_local)]
            path_length_px = sum(
                chord_length(resampled_local[a:b]) for a, b in zip(seg_bounds[:-1], seg_bounds[1:], strict=True)
            )
            refine_meta = {"applied": True, **refined.fit_meta}

    # Image-space self-check: how well does the rendered silhouette match the
    # binarized crop (IoU/Dice, chamfer, centerline RMSE, waviness, score)?
    try:
        quality = template_quality_metrics(
            resampled_local,
            hw_px,
            stroke_starts,
            mask,
            skel,
            width_map,
            unit_px=unit_px,
            crossing_anchors=crossing_anchors,
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
            # Medial-axis snap of the drawn Weg (applied flag + residuals/shift).
            "snap": snap_meta,
            # Image-space refinement of anchors+widths against the ink edge
            # (applied flag + residuals; see refine_template_against_crop).
            "refine": refine_meta,
            # Image-space quality of the stored result vs the binarized crop.
            "quality": quality,
            # Anchor indices whose width reading was crossing-contaminated and
            # replaced by interpolation (diagnostic visibility, not geometry).
            "crossing_anchors": crossing_anchors,
            # Anchor indices sitting exactly on detected within-stroke reversal
            # corners (Umkehrpunkte) — sampling splits the spline there so the
            # rendered centerline keeps a true kink instead of rounding it.
            "corner_anchors": corner_anchors_idx,
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


def written_preview_for_canonical(
    canonical: dict, style_ratio: list[float], slant_deg: float, width_resolver: str = "pressure"
) -> dict:
    """DiagnosticData-shaped render payload for a NOT-yet-stored canonical.

    Lets the wizard's Optimieren step show "as written" previews (raw vs
    refined derivation) before anything is persisted — same outline/centerline
    geometry as `diagnostic_for_glyph`, minus the crop/skeleton columns (the
    skeleton recompute is wasted on a pure render). The style's
    `width_resolver` is applied to the measured widths before rendering
    (architektur.md §5) — the canonical dict itself stays the measurement.

    The image-space `quality` and `refine` meta ride along for the score
    comparison; they are computed in `canonical_from_path` from the MEASURED
    profile, not the resolved one (the metric is frozen and measurement-based,
    qualitaetsmetrik.md). Raw vs refined stays apples-to-apples — both sides
    score the same way — and on Gleichzug ink the measured profile is already
    near-constant, so score and rendered silhouette barely diverge.
    """
    anchors = np.asarray(canonical["anchors"], dtype=float)
    half_widths = resolve_half_widths(np.asarray(canonical["half_widths"], dtype=float), width_resolver)
    trace_meta = canonical["trace_meta"]
    stroke_starts = trace_meta.get("stroke_starts")
    corner_anchors = trace_meta.get("corner_anchors") or []
    snapshot = trace_meta["bbox_snapshot"]
    x0, y0 = snapshot["x0"], snapshot["y0"]

    outline_paths = multi_stroke_silhouettes(
        anchors, half_widths, stroke_starts, 90.0, n=240, corner_anchors=corner_anchors
    )
    outline_polygons = [stroke[0] for stroke in outline_paths if stroke]
    centerlines = multi_stroke_centerlines(
        anchors, half_widths, stroke_starts, 90.0, n=240, corner_anchors=corner_anchors
    )

    # Crop-pixel silhouette (per pen-stroke capsule-union rings) for the overlay:
    # the wizard draws these over the crop image to show WHERE the rendering
    # deviates from the ink — same space as `core.fit.fit_glyph_to_crop`'s
    # `fitted_outline_px`, here from the canonical's own pixel anchors.
    anchors_px_local = np.array([[px - x0, py - y0] for px, py in trace_meta["pixel_anchors"]], dtype=float)
    hw_px = resolve_half_widths(np.asarray(trace_meta["half_widths_px"], dtype=float), width_resolver)
    silhouette_px: list[list[list[list[float]]]] = []
    if len(anchors_px_local) >= 2:
        plan = build_sample_plan(anchors_px_local, stroke_starts, corner_anchors, 240)
        sx, sy, sw = sample_with_sample_plan(anchors_px_local, hw_px, plan)
        bounds = [*plan.sample_starts, len(sx)]
        silhouette_px = [
            capsule_union_rings(sx[a:b], sy[a:b], sw[a:b], simplify_tol=0.2, decimals=2)
            for a, b in zip(bounds[:-1], bounds[1:], strict=True)
        ]

    return {
        "crop_size": {"w": int(snapshot["x1"] - x0), "h": int(snapshot["y1"] - y0)},
        "skeleton_polyline_px": [],
        "anchors_px": [[round(px - x0, 2), round(py - y0, 2)] for px, py in trace_meta["pixel_anchors"]],
        # Resolved widths (not the stored measurement) so every displayed width
        # matches the silhouettes drawn from them.
        "half_widths_px": [round(float(v), 2) for v in hw_px],
        # Per-stroke ring lists in crop pixels (exterior + holes, evenodd).
        "silhouette_px": silhouette_px,
        "anchors_template": canonical["anchors"],
        "half_widths_template": [round(float(v), 4) for v in half_widths],
        "outline_polygon": outline_polygons[0] if outline_polygons else [],
        "outline_polygons": outline_polygons,
        "outline_paths": outline_paths,
        "centerlines_template": centerlines,
        "baseline_y_crop": int(trace_meta["baseline_y"]) - y0,
        "midband_y_crop": int(trace_meta["midband_y"]) - y0,
        "template_guides": template_guides(style_ratio),
        "slant_deg": float(slant_deg),
        "corner_anchors": [int(c) for c in corner_anchors],
        "quality": trace_meta.get("quality"),
        "refine": trace_meta.get("refine"),
    }


# ------------------------------------------------------------------ diagnostic


def diagnostic_for_glyph(
    glyph_row: dict,
    bbox: dict,
    chart_path: str,
    style_ratio: list[float],
    slant_deg: float,
    width_resolver: str = "pressure",
    constant_nib_units: float | None = None,
) -> dict:
    """JSON for the 3-column SVG diagnostic (Loth pur | Crop+skeleton+anchors | Canonical).

    Backend does all the heavy lifting (skeleton extraction, outline polygon
    construction) so the frontend just renders polylines + polygons. The
    style's `width_resolver` is applied to the stored measured widths before
    rendering (architektur.md §5: `pressure` keeps the Schwellzug profile,
    `constant` renders Gleichzug) — the stored template is never mutated.

    `constant_nib_units` is the source-wide pooled nib radius (x-height units,
    architektur.md §5: "mean width per source") supplied by the caller for a
    `constant` style: every Sütterlin glyph of a source then renders at ONE
    round-nib thickness instead of each glyph's own measured constant, so a word
    set in the script keeps a uniform pen. Ignored for non-constant resolvers
    and when None (falls back to the per-glyph resolved width).
    """
    chart_gray = load_chart_grayscale(chart_path)
    crop = crop_with_mask(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop, fill_holes_max_area=int(bbox.get("fill_holes_max_area") or 0))
    skel, _ = skeleton_and_width(mask)

    h, w = crop.shape
    ys, xs = np.where(skel)
    skeleton_polyline_px = [[int(x), int(y)] for x, y in zip(xs.tolist(), ys.tolist(), strict=True)]

    anchors_template = np.asarray(glyph_row["anchors"], dtype=float)
    half_widths_template = resolve_half_widths(np.asarray(glyph_row["half_widths"], dtype=float), width_resolver)

    trace_meta = glyph_row.get("trace_meta", {})
    pixel_anchors = trace_meta.get("pixel_anchors") or []
    half_widths_px = resolve_half_widths(
        np.asarray(trace_meta.get("half_widths_px") or [], dtype=float), width_resolver
    )
    # Source-pooled constant nib (Gleichzug): override both width arrays with the
    # single pooled thickness so every glyph of the source renders at one pen.
    if width_resolver == "constant" and constant_nib_units is not None:
        unit_px = float(trace_meta.get("unit_px") or (int(bbox["baseline_y"]) - int(bbox["midband_y"])))
        half_widths_template = np.full(len(half_widths_template), float(constant_nib_units))
        half_widths_px = np.full(len(half_widths_px), float(constant_nib_units) * unit_px)
    stroke_starts = trace_meta.get("stroke_starts")
    corner_anchors = trace_meta.get("corner_anchors") or []
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
    outline_paths = multi_stroke_silhouettes(
        anchors_template, half_widths_template, stroke_starts, 90.0, n=240, corner_anchors=corner_anchors
    )
    # Legacy single-polygon fields derived from the rings (first ring of each
    # stroke ≈ the outer contour) so a stale SPA bundle keeps rendering
    # something sensible mid-deploy without paying a second geometry pass.
    outline_polygons = [stroke[0] for stroke in outline_paths if stroke]
    # Matching per-stroke centerlines (same sampling) so the frontend can sweep a
    # wide mask along the ductus and reveal the silhouette in writing order.
    centerlines_template = multi_stroke_centerlines(
        anchors_template, half_widths_template, stroke_starts, 90.0, n=240, corner_anchors=corner_anchors
    )

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
        # Anchor indices on within-stroke reversal corners (for distinct markers).
        "corner_anchors": [int(c) for c in corner_anchors],
    }
