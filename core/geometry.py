"""Reference-free geometry primitives for the Sütterlin naturalness metric.

Pure ``numpy`` / ``scipy`` — this module imports **nothing** from ``core.*`` so it
can be shared by both ``core.quality_suetterlin`` (the metric) and, if wanted,
``core.suetterlin`` (the generator) without the import cycle that would arise
otherwise (``core.suetterlin`` already imports the quality module for its
self-check). Everything here is deterministic: array math only, no RNG, no time
— two calls on identical inputs return identical results.

The helpers operate on a *rendered* centerline (the concatenated per-stroke
samples the frontend draws), so the features they detect — vertical runs,
within-stroke curvature, transversal crossings, anti-parallel retraces — are
measured on exactly what the user sees, independent of the scanned crop. That
reference-freeness is the point: the scan is pixelated, but "is this run truly
vertical / is this curve smooth / do the two passes stay parallel" are
judgements about the synthesised glyph itself, not about sub-pixel agreement
with a jagged reference.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy.spatial import cKDTree


def unit_tangents(pts: np.ndarray) -> np.ndarray:
    """Unit tangents of an Mx2 polyline via ``np.gradient`` (== suetterlin._unit_tangents)."""
    pts = np.asarray(pts, dtype=float)
    if len(pts) < 2:
        return np.zeros_like(pts)
    tangent = np.gradient(pts, axis=0)
    tnorm = np.hypot(tangent[:, 0], tangent[:, 1])
    tnorm[tnorm == 0] = 1.0
    return tangent / tnorm[:, None]


def bilinear(field_map: np.ndarray, px: np.ndarray, py: np.ndarray) -> np.ndarray:
    """Sample a (H, W) field at float pixel coordinates, clamped to the crop.

    Public shared facility: the fit optimiser descends this same interpolant and
    ``core.quality`` / ``core.quality_suetterlin`` read it back, so "converged"
    and "high score" agree by construction. Lives here (not in ``core.fit``) so
    the quality modules can sample the field without importing the heavy fit
    module (``core.fit._bilinear_with_grad`` is the gradient-carrying twin the
    optimiser uses; this is the value-only sample, identical numerically).
    """
    h, w = field_map.shape
    x = np.clip(px, 0.0, w - 1.0)
    y = np.clip(py, 0.0, h - 1.0)
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    fx = x - x0
    fy = y - y0
    f00 = field_map[y0, x0]
    f01 = field_map[y0, x1]
    f10 = field_map[y1, x0]
    f11 = field_map[y1, x1]
    return f00 * (1.0 - fx) * (1.0 - fy) + f01 * fx * (1.0 - fy) + f10 * (1.0 - fx) * fy + f11 * fx * fy


def arc_length(pts: np.ndarray) -> np.ndarray:
    """Cumulative chord length along an Mx2 polyline (length M, first entry 0)."""
    pts = np.asarray(pts, dtype=float)
    if len(pts) < 2:
        return np.zeros(len(pts))
    seg = np.hypot(*np.diff(pts, axis=0).T)
    return np.concatenate([[0.0], np.cumsum(seg)])


def discrete_curvature(pts: np.ndarray, unit_px: float) -> np.ndarray:
    """Per-point turning rate (curvature) of a polyline, normalised to x-heights.

    The turning angle between consecutive segment directions, divided by the
    mean adjacent segment length and scaled by ``unit_px`` — so it is "turn per
    x-height", dimensionless and comparable across glyph sizes. Endpoints are
    0 (no turn defined). A straight run reads ~0; a clean circular arc reads a
    near-constant value; jaggedness (Zacken) shows up as a *spiky* profile, which
    the smoothness metric scores via the total variation of this array.
    """
    pts = np.asarray(pts, dtype=float)
    m = len(pts)
    kappa = np.zeros(m)
    if m < 3 or unit_px <= 0:
        return kappa
    d = np.diff(pts, axis=0)
    seglen = np.hypot(d[:, 0], d[:, 1])
    safe = np.where(seglen == 0, 1.0, seglen)
    dirs = d / safe[:, None]
    dot = np.clip((dirs[:-1] * dirs[1:]).sum(axis=1), -1.0, 1.0)
    turn = np.arccos(dot)  # interior points 1..m-2
    denom = 0.5 * (seglen[:-1] + seglen[1:])
    denom = np.where(denom == 0, 1.0, denom)
    kappa[1:-1] = (turn / denom) * unit_px
    return kappa


def run_is_straight_residual(pts: np.ndarray) -> float:
    """Max perpendicular deviation from the chord, as a fraction of chord length.

    The continuous twin of ``suetterlin._run_is_straight`` (which thresholds this
    value): 0 = perfectly straight, larger = more bowed. A degenerate run (fewer
    than 2 points or zero chord) returns +inf so it never reads as straight.
    """
    pts = np.asarray(pts, dtype=float)
    if len(pts) < 2:
        return float("inf")
    chord = pts[-1] - pts[0]
    clen = float(np.hypot(*chord))
    if clen < 1e-6:
        return float("inf")
    d = chord / clen
    rel = pts - pts[0]
    along = rel @ d
    perp = rel - np.outer(along, d)
    return float(np.max(np.hypot(perp[:, 0], perp[:, 1])) / clen)


def fit_line_tls(pts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Total-least-squares line through points: returns ``(centroid, unit_dir)``.

    The principal axis (first right-singular vector of the centred points). The
    direction's sign is arbitrary — callers compare lines with
    ``acute_angle_between`` / ``point_line_perp_distance``, both sign-invariant.
    """
    pts = np.asarray(pts, dtype=float)
    centroid = pts.mean(axis=0)
    if len(pts) < 2:
        return centroid, np.array([1.0, 0.0])
    _, _, vt = np.linalg.svd(pts - centroid, full_matrices=False)
    return centroid, vt[0]


def acute_angle_between(u1: np.ndarray, u2: np.ndarray) -> float:
    """Acute angle (radians, in [0, π/2]) between two (un)signed line directions."""
    dot = float(np.clip(abs(np.dot(u1, u2)), 0.0, 1.0))
    return float(np.arccos(dot))


def point_line_perp_distance(pt: np.ndarray, centroid: np.ndarray, unit_dir: np.ndarray) -> float:
    """Perpendicular distance of ``pt`` from the line ``(centroid, unit_dir)``."""
    rel = np.asarray(pt, dtype=float) - centroid
    along = float(rel @ unit_dir)
    perp = rel - along * unit_dir
    return float(np.hypot(perp[0], perp[1]))


def stroke_bounds(n: int, sample_starts: Sequence[int] | None) -> list[tuple[int, int]]:
    """`(start, end)` sample ranges per pen-stroke in a concatenated sample array."""
    if not sample_starts:
        return [(0, n)]
    starts = sorted({0, *(int(s) for s in sample_starts if 0 < int(s) < n)})
    ends = [*starts[1:], n]
    return list(zip(starts, ends, strict=True))


def detect_vertical_runs(
    sx: np.ndarray,
    sy: np.ndarray,
    sample_starts: Sequence[int] | None,
    unit_px: float,
    *,
    angle_deg: float = 15.0,
    min_len_units: float = 0.45,
    straight_tol: float = 0.10,
) -> list[tuple[int, int]]:
    """Maximal near-vertical, straight, long-enough runs on the rendered centerline.

    Mirrors the run detector inside ``suetterlin._verticalize_downstrokes`` (same
    thresholds), but recomputed on the rendered samples so the metric rewards
    exactly what generation aims to produce. Returns global ``(lo, hi)`` inclusive
    sample-index ranges; a curving loop/bowl side fails the straightness test and
    is excluded (it is not a downstroke).
    """
    sx = np.asarray(sx, dtype=float)
    sy = np.asarray(sy, dtype=float)
    pts_all = np.column_stack([sx, sy])
    runs: list[tuple[int, int]] = []
    for a, b in stroke_bounds(len(pts_all), sample_starts):
        seg = pts_all[a:b]
        if len(seg) < 4:
            continue
        t = unit_tangents(seg)
        ang = np.degrees(np.arctan2(np.abs(t[:, 0]), np.abs(t[:, 1])))  # 0 = vertical
        arc = arc_length(seg)
        isv = ang <= angle_deg
        i = 0
        while i < len(isv):
            if not isv[i]:
                i += 1
                continue
            j = i
            while j + 1 < len(isv) and isv[j + 1]:
                j += 1
            long_enough = (arc[j] - arc[i]) >= min_len_units * unit_px
            if long_enough and run_is_straight_residual(seg[i : j + 1]) <= straight_tol:
                runs.append((a + i, a + j))
            i = j + 1
    return runs


def _per_sample_geometry(
    pts: np.ndarray, sample_starts: Sequence[int] | None
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[tuple[int, int]]]:
    """Per-sample stroke id, arc-within-stroke, unit tangent + the stroke bounds."""
    n = len(pts)
    bounds = stroke_bounds(n, sample_starts)
    stroke_id = np.zeros(n, dtype=int)
    arc = np.zeros(n)
    tang = np.zeros((n, 2))
    for s, (a, b) in enumerate(bounds):
        stroke_id[a:b] = s
        if b - a >= 2:
            arc[a:b] = arc_length(pts[a:b])
            tang[a:b] = unit_tangents(pts[a:b])
    return stroke_id, arc, tang, bounds


def detect_crossing_passages(
    sx: np.ndarray,
    sy: np.ndarray,
    sample_starts: Sequence[int] | None,
    *,
    prox_px: float,
    min_arc_factor: float = 3.0,
    min_angle_deg: float = 25.0,
) -> list[tuple[int, int, int, int, int]]:
    """Locate transversal crossings; return one passage per crossed stroke run.

    A sample is "at a crossing" when another pass of the trace — a different pen
    stroke, or the same stroke far enough along its own path — comes within
    ``prox_px`` *and* runs transversally (turning angle above ``min_angle_deg``,
    i.e. ``|t_i × t_j| > sin``). Contiguous flagged samples on one stroke are one
    passage. Each passage is ``(stroke_lo, stroke_hi, blank_lo, blank_hi,
    partner)``: the through-stroke's full sample slice ``[stroke_lo, stroke_hi)``,
    the inclusive flagged range ``[blank_lo, blank_hi]`` to blank out (the blob),
    and ``partner`` — a representative sample index of the OTHER pass, so a caller
    can require that pass to be straight too (a genuine "two straight lines cross"
    rather than a curve cutting across a loop).
    """
    sx = np.asarray(sx, dtype=float)
    sy = np.asarray(sy, dtype=float)
    pts = np.column_stack([sx, sy])
    n = len(pts)
    if n < 2 or prox_px <= 0:
        return []
    stroke_id, arc, tang, bounds = _per_sample_geometry(pts, sample_starts)
    tree = cKDTree(pts)
    arc_sep = float(min_arc_factor) * float(prox_px)
    sin_thr = float(np.sin(np.deg2rad(min_angle_deg)))
    flagged = np.zeros(n, dtype=bool)
    matched = np.full(n, -1, dtype=int)
    for i in range(n):
        for j in sorted(tree.query_ball_point(pts[i], prox_px)):
            if j == i:
                continue
            other_pass = stroke_id[j] != stroke_id[i] or abs(arc[i] - arc[j]) > arc_sep
            if not other_pass:
                continue
            cross = abs(tang[i, 0] * tang[j, 1] - tang[i, 1] * tang[j, 0])
            if cross > sin_thr:
                flagged[i] = True
                matched[i] = j
                break
    passages: list[tuple[int, int, int, int, int]] = []
    for a, b in bounds:
        i = a
        while i < b:
            if not flagged[i]:
                i += 1
                continue
            j = i
            while j + 1 < b and flagged[j + 1]:
                j += 1
            passages.append((a, b, i, j, int(matched[(i + j) // 2])))
            i = j + 1
    return passages


def detect_retrace_pairs(
    sx: np.ndarray,
    sy: np.ndarray,
    sample_starts: Sequence[int] | None,
    *,
    prox_px: float,
    min_arc_factor: float = 3.0,
    max_angle_deg: float = 25.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Match anti-parallel retrace samples (pen out and back the near-same path).

    The inverse of a crossing: another pass comes within ``prox_px``, far along
    the path, but runs (anti)parallel (turning angle at or below ``max_angle_deg``
    and opposite heading, ``t_i · t_j < 0``) — the two limbs of an ``s``/``f``/``t``
    loop. Returns ``(idx, partner)`` int arrays of matched sample indices (the
    nearest qualifying partner per flagged sample), for measuring parallelism and
    even spacing. Empty arrays when there is no retrace.
    """
    sx = np.asarray(sx, dtype=float)
    sy = np.asarray(sy, dtype=float)
    pts = np.column_stack([sx, sy])
    n = len(pts)
    if n < 2 or prox_px <= 0:
        return np.empty(0, dtype=int), np.empty(0, dtype=int)
    stroke_id, arc, tang, _ = _per_sample_geometry(pts, sample_starts)
    tree = cKDTree(pts)
    arc_sep = float(min_arc_factor) * float(prox_px)
    sin_thr = float(np.sin(np.deg2rad(max_angle_deg)))
    idx: list[int] = []
    partner: list[int] = []
    for i in range(n):
        best_j, best_d = -1, float("inf")
        for j in tree.query_ball_point(pts[i], prox_px):
            if j == i:
                continue
            other_pass = stroke_id[j] != stroke_id[i] or abs(arc[i] - arc[j]) > arc_sep
            if not other_pass:
                continue
            cross = abs(tang[i, 0] * tang[j, 1] - tang[i, 1] * tang[j, 0])
            anti = float(tang[i] @ tang[j]) < 0.0
            if cross <= sin_thr and anti:
                d = float(np.hypot(*(pts[i] - pts[j])))
                if d < best_d or (d == best_d and j < best_j):
                    best_j, best_d = j, d
        if best_j >= 0:
            idx.append(i)
            partner.append(best_j)
    return np.asarray(idx, dtype=int), np.asarray(partner, dtype=int)
