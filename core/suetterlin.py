"""Sütterlin (Gleichzug) canonical derivation — skeleton-locked, constant nib.

A dedicated geometry path for the fixed-width scripts, separate from the
pressure-driven `core.pipeline.canonical_from_path`. Sütterlin is written with
a ball-tipped Redisfeder: the stroke width is constant (no Schwellzug), so the
whole spline → snap → refine → per-anchor-width apparatus that
`canonical_from_path` needs for a Spitzfeder is not just unnecessary here, it is
the source of the "unnatural" look — every smoothing/fitting stage is another
chance for the rendered silhouette to drift off the ink.

The commitment instead: the geometry is the crop's medial axis, *smoothed into
a flowing pen movement*. We skeletonise the binarised crop (`skeletonize` ==
the centerline of a constant-width stroke, by construction), snap the drawn Weg
onto that skeleton to recover stroke order and pen lifts (the ductus prior,
architektur.md §2), and stamp a single constant half-width — the histogram MODE
of the distance-transform on the skeleton, i.e. the nib radius. Round caps even
match the Redisfeder's ball tip.

The skeleton fixes gross shape, but it is the medial axis of a PIXELATED scan:
it wiggles at ~1px and wanders with the blob width, and a constant round nib
amplifies every such wobble into a visible notch, step or scallop the hand
never made. So after snapping we smooth each stroke along arc length with a
small Gaussian (`_smooth_snapped_strokes`), NEVER across a within-stroke corner
(Umkehrpunkt) or a pen lift — those stay sharp C0. The drawn Sütterlin is one
flowing movement; smoothing recovers it while the snap keeps the shape locked
to the ink. The nib radius is still measured on the un-smoothed skeleton (it is
the ink's width, not the centerline's wobble).

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
from scipy.ndimage import gaussian_filter1d
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
from core.pipeline import DEFAULT_N_ANCHORS, _detect_corners, _measurements, _resample_strokes, _split_raw_strokes
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


# Arc-length Gaussian smoothing of the snapped centerline (Gleichzug only). The
# snapped polyline traces the skeleton of a PIXELATED crop; a constant round nib
# turns its 1px jaggedness into visible notches/steps. Sütterlin is a flowing
# pen movement, so we smooth each stroke along arc length — but never across a
# within-stroke corner or a pen lift, which keeps the Umkehrpunkt a true C0
# reversal. Sigma is in x-height units so it scales with the crop resolution.
SMOOTH_SIGMA_UNITS = 0.07
# A corner-bounded sub-arc shorter than this (px) has too few samples to smooth
# meaningfully (and is usually a tight corner spine) — pass it through untouched.
SMOOTH_MIN_SEGMENT_PX = 4.0


def _smooth_open_segment(pts: np.ndarray, sigma_px: float) -> np.ndarray:
    """Gaussian-smooth an open polyline along arc length; ENDPOINTS preserved.

    Resampled to ~1px first so `sigma_px` is a true arc-length scale, then
    `gaussian_filter1d` with `mode="nearest"` so the round stroke ends are not
    eroded inward. The first/last points are pinned exactly: a stroke end keeps
    its cap position and a shared corner knot does not migrate.
    """
    if len(pts) < 4 or sigma_px <= 0:
        return pts
    resampled = _resample_by_arc(pts, 1.0)
    if len(resampled) < 4:
        return pts
    sx = gaussian_filter1d(resampled[:, 0], sigma_px, mode="nearest")
    sy = gaussian_filter1d(resampled[:, 1], sigma_px, mode="nearest")
    out = np.column_stack([sx, sy])
    out[0], out[-1] = resampled[0], resampled[-1]
    return out


def _smooth_snapped_strokes(strokes: list[np.ndarray], unit_px: float) -> list[np.ndarray]:
    """Smooth each snapped stroke per corner-bounded sub-arc (never across a corner).

    Corners are found with the same detector the resampler uses (`_detect_corners`),
    so smoothing splits exactly where the render's spline will later kink: the
    corner stays a sharp reversal while the flowing runs between corners shed the
    skeleton's pixel jaggedness. Pen lifts already separate the input strokes, so
    a lift is never smoothed across either.
    """
    sigma_px = SMOOTH_SIGMA_UNITS * unit_px
    if sigma_px <= 0:
        return strokes
    out: list[np.ndarray] = []
    for stroke in strokes:
        knots = _detect_corners(stroke, unit_px)
        if not knots:
            sm = _smooth_open_segment(stroke, sigma_px)
            if len(sm) >= 2:
                out.append(sm)
            continue
        seg = np.hypot(*np.diff(stroke, axis=0).T)
        s = np.concatenate([[0.0], np.cumsum(seg)])
        bounds = [0.0, *knots, float(s[-1])]
        pieces: list[np.ndarray] = []
        for a, b in zip(bounds[:-1], bounds[1:], strict=True):
            idx = np.where((s >= a - 1e-9) & (s <= b + 1e-9))[0]
            if len(idx) < 2:
                continue
            piece = stroke[idx]
            if float(s[idx[-1]] - s[idx[0]]) >= SMOOTH_MIN_SEGMENT_PX:
                piece = _smooth_open_segment(piece, sigma_px)
            pieces.append(piece)
        if not pieces:
            out.append(stroke)
            continue
        # Re-join sub-arcs, dropping each piece's leading point — it duplicates
        # the shared corner knot that ended the previous piece.
        merged = [pieces[0], *(p[1:] for p in pieces[1:])]
        joined = np.concatenate(merged, axis=0)
        if len(joined) >= 2:
            out.append(joined)
    return out


# Verticalisation (Gleichzug): the long Sütterlin downstroke should orient to the
# 90° upright convention. A near-vertical run that is ALSO already nearly straight
# (a real downstroke, not a curving loop/arch side — `_run_is_straight` rejects
# the latter) is pulled onto a single x, i.e. a true vertical. The pull uses a
# raised-cosine weight that is 1 over the run core and eases to 0 into the
# adjacent curve, so the round flows TANGENTIALLY into the straight (a smooth
# fillet, no corner). Only x is moved (y is kept), so the glyph keeps its height
# and the run stays connected; far parts of arches/loops are untouched.
VERTICAL_ANGLE_DEG = 15.0  # max angle from vertical for a run to count as a downstroke
VERTICAL_MIN_LEN_UNITS = 0.45  # min run length (x-height units) to verticalise
VERTICAL_STRAIGHT_TOL = 0.10  # max bow (fraction of length) — a curve fails and stays round
VERTICAL_EASE_UNITS = 0.20  # raised-cosine fillet length (x-height units) into the curve
VERTICAL_INSET_UNITS = 0.12  # shrink the perfectly-vertical core by this per end (more curve at the ends)


def _run_is_straight(pts: np.ndarray, tol_frac: float) -> bool:
    """True if a run's max perpendicular deviation from its chord is < tol·length.

    A real downstroke is straight; a loop/arch side that merely passes through
    near-vertical is curved and fails this — so it is never force-straightened.
    """
    chord = pts[-1] - pts[0]
    clen = float(np.hypot(*chord))
    if clen < 1e-6:
        return False
    d = chord / clen
    rel = pts - pts[0]
    along = rel @ d
    perp = rel - np.outer(along, d)
    return float(np.max(np.hypot(perp[:, 0], perp[:, 1]))) <= tol_frac * clen


def _verticalize_downstrokes(anchors: np.ndarray, stroke_starts: list[int], unit_px: float) -> np.ndarray:
    """Pull each long, straight, near-vertical run onto a true vertical (crop px).

    A run is a maximal stretch whose local tangent is within `VERTICAL_ANGLE_DEG`
    of vertical and that passes `_run_is_straight` — a downstroke, never a curving
    loop side. Detected by tangent, so it also catches the long line in a loop
    glyph (b) that has no within-stroke corner. Each run's x is attracted to its
    mean x with a weight 1 across the (inset) core, easing to 0 over
    `VERTICAL_EASE_UNITS` of arc into the neighbouring curve — a tangential fillet,
    not a corner. Never crosses a pen lift (strokes are processed independently).
    """
    bounds_all = [*stroke_starts, len(anchors)]
    out = anchors.astype(float).copy()
    ease_px = max(1e-6, VERTICAL_EASE_UNITS * unit_px)
    inset_px = VERTICAL_INSET_UNITS * unit_px
    for s0, s1 in zip(bounds_all[:-1], bounds_all[1:], strict=True):
        pts = out[s0:s1]
        if len(pts) < 4:
            continue
        tan = np.gradient(pts, axis=0)
        tnorm = np.hypot(tan[:, 0], tan[:, 1])
        tnorm[tnorm == 0] = 1.0
        tan = tan / tnorm[:, None]
        ang = np.degrees(np.arctan2(np.abs(tan[:, 0]), np.abs(tan[:, 1])))  # 0 = vertical, 90 = horizontal
        isvert = ang <= VERTICAL_ANGLE_DEG
        seg = np.hypot(*np.diff(pts, axis=0).T)
        arc = np.concatenate([[0.0], np.cumsum(seg)])
        runs: list[tuple[int, int]] = []
        i = 0
        while i < len(isvert):
            if isvert[i]:
                j = i
                while j + 1 < len(isvert) and isvert[j + 1]:
                    j += 1
                if (arc[j] - arc[i]) / unit_px >= VERTICAL_MIN_LEN_UNITS and _run_is_straight(
                    pts[i : j + 1], VERTICAL_STRAIGHT_TOL
                ):
                    runs.append((i, j))
                i = j + 1
            else:
                i += 1
        for i, j in runs:
            target_x = float(np.mean(pts[i : j + 1, 0]))
            lo, hi = arc[i] + inset_px, arc[j] - inset_px
            if hi <= lo:
                lo = hi = 0.5 * (arc[i] + arc[j])
            gap = np.clip(lo - arc, 0, None) + np.clip(arc - hi, 0, None)
            w = np.where(gap >= ease_px, 0.0, 0.5 * (1.0 + np.cos(np.pi * gap / ease_px)))
            pts[:, 0] = (1.0 - w) * pts[:, 0] + w * target_x
    return out


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

    # Recover the flowing pen movement: smooth the skeleton-snapped centerline
    # along arc length (per corner-bounded sub-arc), shedding the pixel
    # jaggedness a constant round nib would otherwise amplify into notches.
    snapped = _smooth_snapped_strokes(snapped, unit_px)
    if not snapped:
        raise ValueError("no usable strokes after smoothing")

    # Even-spaced anchors with corner knots (shared resampler): even spacing is
    # what keeps the render's natural cubic spline from overshooting on the long
    # straight runs that snapping-then-Douglas-Peucker would leave clustered.
    n = int(n_anchors or bbox.get("n_anchors") or DEFAULT_N_ANCHORS)
    resampled_local, stroke_starts, corner_anchors_idx, path_length_px = _resample_strokes(snapped, n, unit_px)

    # Orient the long downstrokes to the 90° upright convention: pull each
    # near-vertical straight run onto a true vertical, easing the adjacent round
    # tangentially into it (a fillet). Loops/bowls fail the straightness test and
    # stay round. Done on the resampled anchors so the corner-knot indices hold.
    resampled_local = _verticalize_downstrokes(resampled_local, stroke_starts, unit_px)
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
            "snap": {"applied": False, "reason": "gleichzug: geometry is the smoothed skeleton"},
            "refine": {"applied": False, "reason": "gleichzug: constant width, no edge refine"},
            # Arc-length smoothing of the snapped centerline (per corner-bounded
            # sub-arc): turns the pixelated skeleton into a flowing pen movement.
            "smooth": {"applied": True, "method": "gaussian-arclength", "sigma_units": SMOOTH_SIGMA_UNITS},
            # Verticalisation: long near-vertical straight runs pulled to true 90°
            # with a tangential fillet into the adjacent rounds.
            "vertical": {"applied": True, "angle_deg": VERTICAL_ANGLE_DEG, "min_len_units": VERTICAL_MIN_LEN_UNITS},
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
