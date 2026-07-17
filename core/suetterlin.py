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
  nearest skeleton pixel reads a half-width well above the nib radius) and the
  two strokes run SIDE BY SIDE — a genuine sustained double, the pen up the left
  edge and back down the right — they must NOT collapse onto the shared
  centerline. Each point is offset from the central skeleton toward its own edge
  by (local half-width − nib radius), the side taken from the drawn trace (the
  ductus prior). The exception is the ſ/t Spitze, where a thin diagonal and the
  stem converge to a sharp tip: edge-splitting the wide tip blob (fed by its
  wandering width) splays the two passes into an unnatural lens, but fully
  collapsing them zips one line over the whole wedge and under-fills the ink. So
  there the offset is DAMPED by the local width excess (`_retrace_offset_scale`):
  ~0 at the apex (a sharp single-nib point, as the crop shows) and easing back to
  the full edge offset as the wedge widens — the two passes splay out of the tip
  in a clean V.
  Single strokes (EDT ≈ nib) snap to the centerline exactly as before; round
  stroke ends (EDT < nib) get no offset.

The drawn Weg therefore only supplies ORDER (and Absetzen): the geometry is
locked to the ink, so a rough trace still yields a clean glyph. The output dict
matches `canonical_from_path` field for field, so storage, the API and the
frontend render contract (`anchors` / `half_widths` / `stroke_starts` /
`outline_paths`) are unchanged — only the derivation is new.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree

from core.chart import crop_with_mask, load_chart_grayscale
from core.extract import binarize_adaptive, skeleton_and_width
from core.geometry import (
    acute_angle_between,
    arc_length,
    detect_crossing_passages,
    fit_line_tls,
    run_is_straight_residual,
    unit_tangents,
)

# Deliberately shared with the pressure pipeline. `_split_raw_strokes` is the
# single source of truth for pen-lift (Absetzen) splitting; `_resample_strokes`
# is the proven even-spacing + corner-knot (Umkehrpunkt) resampler — even
# spacing is what keeps the render's natural cubic spline from overshooting on a
# straight run; `_assemble_canonical_payload` builds the shared wire dict
# (normalisation, entry/exit, raw_path, trace_meta, measurements) so the stored
# shape stays identical across both derivations. Re-implementing any of them
# here would risk silent divergence. The Gleichzug path only swaps in a skeleton
# snap + constant width.
from core.pipeline import (
    DEFAULT_N_ANCHORS,
    _assemble_canonical_payload,
    _detect_corners,
    _resample_strokes,
    _split_raw_strokes,
)
from core.quality_suetterlin import suetterlin_quality_metrics


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

# Retrace (Spitze) — the ſ/t tip where the pen runs up and back down, the two
# anti-parallel passes converging to a sharp point (see the module header and
# `_retrace_offset_scale`). Two parameters shape it:
#   • RETRACE_MAX_RUN_NIB gates WHERE the taper applies — only a short tip/junction
#     bulge (a few nib of anti-parallel overlap) is a Spitze; an n/m/r arch beside
#     its stem (or any long parallel double bar, e.g. the synthetic merged-double
#     test) extends for many nib and keeps its full edge offset, untouched. A
#     straightness gate was tried as the arch-excluder instead and dropped — the
#     tips themselves curve as the two strokes converge, so it wrongly spared them.
#   • RETRACE_TAPER_NIB shapes HOW the tip renders. A binary collapse (offset fully
#     suppressed over the whole run) was tried and rejected: it zips the two passes
#     onto one line for a long stretch and under-fills the widening ink wedge (the
#     crop is one nib ONLY at the very apex). Instead the edge offset is DAMPED by
#     the local width excess: scale = min(1, (hw − nib) / (RETRACE_TAPER_NIB·nib)).
#     At the apex (excess ≈ 0) the passes collapse to a sharp point; as the wedge
#     widens they splay back to the ink edges, reaching full offset at
#     hw = (1 + RETRACE_TAPER_NIB)·nib. The value 1.0 sets that crossover at
#     hw = 2·nib — exactly the width below which two offset nibs (each at ±excess
#     from the centre, where here `nib` is the nib RADIUS) still
#     overlap (no false interior hollow) and above which the crop genuinely hosts a
#     gap: so the damp is precisely the solid-wedge regime and nowhere else. Visually
#     confirmed against the crop (ſ/t): a sharp single-nib tip, then the diagonal and
#     stem part into a clean V high up, matching the chart — neither the binary
#     collapse's long zip nor a premature splay.
RETRACE_MAX_RUN_NIB = 12.0  # nib radii (× r_px below); flagged runs longer than this are a sustained double, not a tip
RETRACE_TAPER_NIB = 1.0  # edge offset reaches full strength once the width excess hits this many nib radii

# Straighten a through-stroke across a transversal crossing. The wide skeleton
# junction where a loop crosses a stem (f/g/h/j/l/p/ſ) bends the snapped
# centerline a few degrees / a fraction of a nib; the Gleichzug naturalness metric
# reads that residual kink as a collinearity penalty (the stem should continue as
# ONE line through the crossing). Crossings are found exactly as the metric finds
# them — `detect_crossing_passages` (proximity + transversal angle), NOT the
# width-based merge test above (which misses loop-over-stem junctions that are not
# 2× wide). This runs LAST, on the verticalised anchors the metric splines, so the
# straightening it does is not re-bent by a later stage (verticalising a partly-
# straightened stem was what kinked d/k/p in earlier attempts). Mirrors
# `core.quality_suetterlin.crossing_collinearity`.
CROSS_PROX_FLOOR_UNITS = 0.10  # = metric PROX_FLOOR_UNITS
CROSS_PROX_NIB_FACTOR = 3.0  # = metric PROX_NIB_FACTOR
# Wider than the metric's own 0.35u fit window on purpose: over a longer run the
# two approaches of a short straight zone bounded by curves (the d/p bowl-into-
# stem) diverge enough to trip the angle gate below — the metric's finer spline
# reads that case as curved → N/A, so straightening it would forge a scored kink.
# A genuine long stem (f/g/l/ſ) stays under the angle gate over the same window, so
# the loose straightness tol (which the ſ stem, bowed ~0.11 by its top hook, needs)
# can stay; the angle-over-the-wider-window is what separates d from ſ, not the tol.
CROSS_STRAIGHTEN_WINDOW_UNITS = 0.45  # arc each side of the blob fit + straightened
CROSS_STRAIGHTEN_STRAIGHT_TOL = 0.12  # an approach bowed more than this over the window is a curve, not a stem
CROSS_STRAIGHTEN_MAX_ANGLE_DEG = (
    12.0  # approaches meeting at a sharper angle (over the window) are a curve, not one line
)
CROSS_STRAIGHTEN_EASE_UNITS = 0.12  # raised-cosine blend back to the untouched stroke at the window ends


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


def _flag_wide_passes(
    centers: np.ndarray,
    tangents: np.ndarray,
    stroke_id: np.ndarray,
    arc: np.ndarray,
    hw_c: np.ndarray,
    r_px: float,
    accept: Callable[[float, float], bool],
) -> np.ndarray:
    """Flag each wide blob point that has a qualifying OTHER pass nearby.

    The shared scan behind both `_crossing_mask` (transversal) and
    `_retrace_offset_scale` (anti-parallel): for every point whose EDT half-width is well above the nib,
    look for another pass of the trace — a different stroke, or the same stroke far
    enough along its own path that it is not just this point's neighbours — within
    reach of the blob, and accept it by `accept(cross, dot)` where
    `cross = |t_i × t_j|` (the sine of the turning angle) and `dot = t_i · t_j`. The
    caller's predicate picks transversal (cross above the angle threshold) vs.
    anti-parallel (cross below it and opposite heading).
    """
    n = len(centers)
    flagged = np.zeros(n, dtype=bool)
    wide = np.flatnonzero(hw_c - r_px > max(MERGE_EXCESS_MIN_PX, MERGE_EXCESS_FACTOR * r_px))
    if n < 2 or wide.size == 0:
        return flagged
    tree = cKDTree(centers)
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
            if accept(cross, float(tangents[i] @ tangents[j])):
                flagged[i] = True
                break
    return flagged


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
    sin_thr = np.sin(np.deg2rad(CROSSING_MIN_ANGLE_DEG))
    return _flag_wide_passes(centers, tangents, stroke_id, arc, hw_c, r_px, lambda cross, dot: cross > sin_thr)


def _retrace_offset_scale(
    centers: np.ndarray, tangents: np.ndarray, stroke_id: np.ndarray, arc: np.ndarray, hw_c: np.ndarray, r_px: float
) -> np.ndarray:
    """Per-point edge-offset SCALE in [0, 1] for a Spitze tip (1.0 = full offset).

    A wide point (EDT well above the nib) is a tip-retrace when ANOTHER pass of the
    trace — a different stroke, or the same stroke far enough along the path — comes
    within reach of the blob and runs ANTI-PARALLEL (turning angle below
    CROSSING_MIN_ANGLE_DEG and opposite heading). There the edge offset is DAMPED
    toward zero so the two passes collapse onto the shared medial line into a sharp
    tip instead of splaying to fake edges — but only near the apex: the damp eases
    off with the local width excess (see `RETRACE_TAPER_NIB`) so the passes splay
    back to the ink edges as the wedge widens, a clean V instead of a long zip. The
    discriminator against a genuine sustained double (an n/m/r arch beside its stem,
    a long parallel double bar) is a per-stroke pass that exempts any flagged run
    longer than `RETRACE_MAX_RUN_NIB` nib radii — it keeps its full edge offset.
    """
    sin_thr = np.sin(np.deg2rad(CROSSING_MIN_ANGLE_DEG))
    flagged = _flag_wide_passes(
        centers, tangents, stroke_id, arc, hw_c, r_px, lambda cross, dot: cross <= sin_thr and dot < 0.0
    )
    # Exempt flagged runs longer than the short-tip cap: a sustained anti-parallel
    # double bar (genuinely two strokes) must keep its full edge offset.
    n = len(centers)
    max_run_px = RETRACE_MAX_RUN_NIB * r_px
    i = 0
    while i < n:
        if not flagged[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and flagged[j + 1] and stroke_id[j + 1] == stroke_id[i]:
            j += 1
        if abs(arc[j] - arc[i]) > max_run_px:
            flagged[i : j + 1] = False
        i = j + 1
    # Damp the offset near the apex (small excess), restore it as the wedge widens.
    scale = np.ones(n, dtype=float)
    taper_px = max(RETRACE_TAPER_NIB * r_px, 1e-6)
    excess = np.maximum(hw_c - r_px, 0.0)
    scale[flagged] = np.clip(excess[flagged] / taper_px, 0.0, 1.0)
    return scale


def _apply_edge_offset(
    points: np.ndarray,
    tangent: np.ndarray,
    centers: np.ndarray,
    hw_c: np.ndarray,
    dist: np.ndarray,
    suppress: np.ndarray,
    offset_scale: np.ndarray,
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
    passes straight through at one nib thickness. `offset_scale` (in [0, 1], 1.0
    everywhere except a Spitze tip) damps the offset toward the apex of a retrace
    so the two passes form a sharp point, not a long zip (`_retrace_offset_scale`).
    Round stroke ends read EDT < nib, so they get no offset. Beyond the (locally
    widened) cap the skeleton is too far to trust, so the drawn point stands.
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
        snapped[merged] = centers[merged] + (excess[merged] * offset_scale[merged])[:, None] * unit

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
    own edge where two strokes have merged side by side (`_apply_edge_offset`),
    straight through where two strokes cross transversally (`_crossing_mask`
    suppresses the offset), and tapered toward the shared medial line at a short
    tight anti-parallel doubled stem (`_retrace_offset_scale` damps the offset to a
    sharp tip — the ſ/t Spitze). The result is a dense polyline tracing the ink (including
    through corners), the geometry now the ink's, not the hand's. Crossing/retrace
    detection needs every stroke at once (one pass can cross or retrace another),
    so the dense snap-to-centre for all strokes happens first, then the offset.
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
        tangent = unit_tangents(pts)
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

    # Pass 2 — across ALL strokes at once, derive the two offset modifiers:
    # `suppress_all` hard-skips the offset at a transversal crossing (Kreuzung —
    # pass straight through), and `scale_all` damps it toward a short tight
    # anti-parallel doubled stem's apex (Spitze tip — a sharp point, then a clean V).
    centers_all = np.vstack([d["centers"] for d in dense])
    tangents_all = np.vstack([d["tangent"] for d in dense])
    hw_all = np.concatenate([d["hw_c"] for d in dense])
    arc_all = np.concatenate([d["arc"] for d in dense])
    sid_all = np.concatenate([np.full(len(d["pts"]), d["sid"]) for d in dense])
    suppress_all = _crossing_mask(centers_all, tangents_all, sid_all, arc_all, hw_all, r_px)
    scale_all = _retrace_offset_scale(centers_all, tangents_all, sid_all, arc_all, hw_all, r_px)

    # Pass 3 — apply the edge offset per stroke (offset in merges, straight in
    # crossings, tapered at a Spitze tip), dedup, and drop strokes that collapse to <2 points.
    snapped: list[np.ndarray] = []
    cursor = 0
    for d in dense:
        k = len(d["pts"])
        suppress = suppress_all[cursor : cursor + k]
        scale = scale_all[cursor : cursor + k]
        cursor += k
        if tree is None:
            pts = d["pts"]
        else:
            pts = _apply_edge_offset(
                d["pts"], d["tangent"], d["centers"], d["hw_c"], d["dist"], suppress, scale, cap_px, r_px
            )
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
# A within-stroke corner (Umkehrpunkt) within this much arc (x-height units)
# beyond a vertical run's end is treated as the run's true endpoint: the
# downstroke runs straight to the reversal (no fillet inset/ease there) and the
# corner anchor is pulled onto the vertical, so the bottom of an i/u/m/n sits
# squarely below the stem instead of hooking off to the side where the skeleton
# pools at the turn. Arc-based (not an anchor count) so it is invariant to anchor
# spacing; sized just above the rounded-end drift (≈ a nib radius) the tangent
# test sheds off the run, well below the distance to any unrelated feature.
VERTICAL_CORNER_GAP_UNITS = 0.15


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


def _verticalize_downstrokes(
    anchors: np.ndarray, stroke_starts: list[int], unit_px: float, corner_anchors: list[int] | None = None
) -> np.ndarray:
    """Pull each long, straight, near-vertical run onto a true vertical (crop px).

    A run is a maximal stretch whose local tangent is within `VERTICAL_ANGLE_DEG`
    of vertical and that passes `_run_is_straight` — a downstroke, never a curving
    loop side. Detected by tangent, so it also catches the long line in a loop
    glyph (b) that has no within-stroke corner. Each run's x is attracted to its
    mean x with a weight 1 across the core, easing to 0 over `VERTICAL_EASE_UNITS`
    of arc into the neighbouring curve — a tangential fillet, not a corner. Never
    crosses a pen lift (strokes are processed independently).

    Corner-aware ends: where a run terminates AT a within-stroke corner (an
    `corner_anchors` index within `VERTICAL_CORNER_GAP` of the run end), that end
    is a true reversal, not a fillet into a curve — the run runs straight to the
    corner (no inset, no ease) and the corner anchor itself is pulled onto the
    vertical, while the weight is zeroed beyond the corner so the next sub-stroke
    (the up-going Aufstrich) is left untouched. This puts the bottom of an
    i/u/m/n squarely below its stem instead of hooking to the side, matching the
    written ductus: down at 90°, stop, away again. A run end that flows into a
    curve (no corner) keeps the easing fillet as before.
    """
    bounds_all = [*stroke_starts, len(anchors)]
    out = anchors.astype(float).copy()
    ease_px = max(1e-6, VERTICAL_EASE_UNITS * unit_px)
    inset_px = VERTICAL_INSET_UNITS * unit_px
    corner_set = {int(c) for c in (corner_anchors or [])}
    for s0, s1 in zip(bounds_all[:-1], bounds_all[1:], strict=True):
        pts = out[s0:s1]
        if len(pts) < 4:
            continue
        local_corners = sorted(c - s0 for c in corner_set if s0 <= c < s1)
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
        gap_px = VERTICAL_CORNER_GAP_UNITS * unit_px
        for i, j in runs:
            target_x = float(np.mean(pts[i : j + 1, 0]))
            top_corner = next((c for c in reversed(local_corners) if c < i and arc[i] - arc[c] <= gap_px), None)
            bot_corner = next((c for c in local_corners if c > j and arc[c] - arc[j] <= gap_px), None)
            i_end = top_corner if top_corner is not None else i
            j_end = bot_corner if bot_corner is not None else j
            lo = arc[i_end] + (0.0 if top_corner is not None else inset_px)
            hi = arc[j_end] - (0.0 if bot_corner is not None else inset_px)
            if hi <= lo:
                lo = hi = 0.5 * (arc[i_end] + arc[j_end])
            gap = np.clip(lo - arc, 0, None) + np.clip(arc - hi, 0, None)
            w = np.where(gap >= ease_px, 0.0, 0.5 * (1.0 + np.cos(np.pi * gap / ease_px)))
            # A corner is a hard reversal, not a fillet: keep the vertical pull
            # from bleeding past it into the adjacent sub-stroke.
            if top_corner is not None:
                w[arc < arc[i_end] - 1e-9] = 0.0
            if bot_corner is not None:
                w[arc > arc[j_end] + 1e-9] = 0.0
            pts[:, 0] = (1.0 - w) * pts[:, 0] + w * target_x
    return out


def _straighten_crossings(anchors: np.ndarray, stroke_starts: list[int], unit_px: float, r_px: float) -> np.ndarray:
    """Pull each straight through-stroke onto ONE line across its transversal crossings.

    Runs on the final, verticalised anchors (crop px) — the geometry the metric
    splines — so nothing re-bends the result. Crossings are located across all
    strokes at once (a stroke can cross another or itself far along its own path)
    with the metric's `detect_crossing_passages`, so exactly the regions
    `crossing_collinearity` scores are touched. For each crossed stroke run the two
    approaches just outside the blob (within `CROSS_STRAIGHTEN_WINDOW_UNITS` of arc)
    must both be straight and meet at a small angle — a genuine straight pass continuing
    through. When they do, one TLS line is fit through both approaches and the blob
    + approaches are projected onto it (raised-cosine-eased back to the untouched
    anchors at the window ends), so the stem runs straight through instead of
    bending into the skeleton's junction node. A curved loop self-crossing fails
    the straight/angle gate and is left untouched, so the coverage gate holds.
    """
    n = len(anchors)
    if n < 5:
        return anchors
    out = anchors.astype(float).copy()
    sample_starts = [int(s) for s in stroke_starts]
    prox_px = max(CROSS_PROX_NIB_FACTOR * r_px, CROSS_PROX_FLOOR_UNITS * unit_px)
    passages = detect_crossing_passages(
        out[:, 0],
        out[:, 1],
        sample_starts,
        prox_px=prox_px,
        min_arc_factor=CROSSING_MIN_ARC_FACTOR,
        min_angle_deg=CROSSING_MIN_ANGLE_DEG,
    )
    if not passages:
        return anchors
    window_px = CROSS_STRAIGHTEN_WINDOW_UNITS * unit_px
    ease_px = max(1e-6, CROSS_STRAIGHTEN_EASE_UNITS * unit_px)
    tol = CROSS_STRAIGHTEN_STRAIGHT_TOL
    max_ang = np.deg2rad(CROSS_STRAIGHTEN_MAX_ANGLE_DEG)
    for a, b, lo, hi, _partner in passages:
        seg = out[a:b]  # a view — writes propagate back to `out`
        arc = arc_length(seg)
        lo_l, hi_l = lo - a, hi - a
        before = seg[(arc < arc[lo_l]) & (arc >= arc[lo_l] - window_px)]
        after = seg[(arc > arc[hi_l]) & (arc <= arc[hi_l] + window_px)]
        if len(before) < 3 or len(after) < 3:
            continue
        if run_is_straight_residual(before) > tol or run_is_straight_residual(after) > tol:
            continue
        if acute_angle_between(fit_line_tls(before)[1], fit_line_tls(after)[1]) > max_ang:
            continue
        centroid, direction = fit_line_tls(np.vstack([before, after]))
        # A near-vertical through-stem is straightened onto a TRUE vertical (what
        # verticalisation wanted), not the slightly-tilted TLS fit — otherwise the
        # projection would un-verticalise the stem (a verticality regression) while
        # fixing collinearity. Off-vertical descenders (g/j) keep the fitted line.
        if np.degrees(np.arctan2(abs(direction[0]), abs(direction[1]))) <= VERTICAL_ANGLE_DEG:
            direction = np.array([0.0, 1.0])
        region_lo, region_hi = arc[lo_l] - window_px, arc[hi_l] + window_px
        for k in np.flatnonzero((arc >= region_lo) & (arc <= region_hi)):
            proj = centroid + ((seg[k] - centroid) @ direction) * direction
            edge = min(arc[k] - region_lo, region_hi - arc[k])
            w = 1.0 if edge >= ease_px else 0.5 * (1.0 - np.cos(np.pi * edge / ease_px))
            seg[k] = (1.0 - w) * seg[k] + w * proj
    return out


def canonical_suetterlin_from_path(
    raw_path: list[dict], bbox: dict, chart_path: str, glyph: str, n_anchors: int | None = None
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
    resampled_local = _verticalize_downstrokes(resampled_local, stroke_starts, unit_px, corner_anchors_idx)

    # Last geometry step: run a straight stem/bar STRAIGHT through each transversal
    # crossing (loop-over-stem in f/g/h/j/l/p/ſ), removing the few-degree kink the
    # skeleton's junction node leaves. After verticalisation so nothing re-bends it.
    resampled_local = _straighten_crossings(resampled_local, stroke_starts, unit_px, r_px)
    hw_px = np.full(len(resampled_local), r_px, dtype=float)

    # Image-space self-check: the Gleichzug naturalness metric (smoothness,
    # verticality, corner crispness, crossing collinearity, retrace) gated by a
    # tolerant coverage of the crop — NOT the Kurrent pixel/Schwellzug metric.
    try:
        quality = suetterlin_quality_metrics(
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

    return _assemble_canonical_payload(
        resampled_local=resampled_local,
        hw_px=hw_px,
        stroke_starts=stroke_starts,
        corner_anchors_idx=corner_anchors_idx,
        # No crossing-width resolution: the width is a single constant.
        crossing_anchors=[],
        path_length_px=path_length_px,
        quality=quality,
        raw_path=raw_path,
        bbox=bbox,
        glyph=glyph,
        baseline_y=baseline_y,
        midband_y=midband_y,
        unit_px=unit_px,
        method="suetterlin-gleichzug",
        extra_trace_meta={
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
        },
    )


def canonical_suetterlin_from_raw_path_only(glyph_row: dict, bbox: dict, chart_path: str, n_anchors: int) -> dict:
    """Re-derive a Sütterlin canonical from an existing glyph's stored `raw_path`.

    The Gleichzug twin of `core.pipeline.canonical_from_raw_path_only`, used by
    the /resample and /quality endpoints for constant-width styles.
    """
    return canonical_suetterlin_from_path(
        raw_path=glyph_row["raw_path"], bbox=bbox, chart_path=chart_path, glyph=glyph_row["glyph"], n_anchors=n_anchors
    )
