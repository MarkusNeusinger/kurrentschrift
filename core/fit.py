"""Fit a canonical ductus template to a glyph instance (the roadmap-M4 step).

Given a canonical template (normalised anchors + half-widths) and an instance
crop (skeleton + distance-transform half-width map), deform the template's
control points so the template centerline lies near the instance skeleton and
its half-width profile matches the measured distance transform — regularised
against excessive deformation so the ductus topology (loop direction, crossing
order) is preserved.

The optimisation surface is built to be smooth and cheap:

* geometry/width residuals come from bilinearly-sampled precomputed fields
  (EDT to the skeleton; half-width propagated from the nearest ink pixel),
  not from per-evaluation nearest-neighbour queries — KD lookups are kinked
  at Voronoi boundaries and piecewise constant in the width term, which made
  L-BFGS-B's line search abort on finite-difference gradients;
* the chord-length spline sampling is frozen at the canonical anchors, which
  makes sampling a fixed linear operator and the analytic gradient exact;
* a coverage term (skeleton → template distance) punishes collapsing onto a
  subset of the skeleton, which the one-sided geometry term cannot see.

Convergence is judged by the residual itself (`fit_meta["converged"]`), not by
scipy's stop status: empirically the optimiser's own flag anti-correlates with
fit quality (evaluation-budget stops on good fits, clean stops on stalled
ones). The scipy status is still reported as `optimizer_*` for debugging.

Coordinate spaces
-----------------
* Template space: baseline ``y = 0``, midband ``y = 1``, ``x`` left-to-right,
  origin at the template's first anchor (same convention as `core.template`).
* Crop-local pixel space: the instance crop, row-major pixels. The mapping is
  ``px = x_origin_px + x_norm * unit_px`` and ``py = baseline_y_px - y_norm *
  unit_px`` where ``unit_px`` is the x-height in pixels.

All optimisation parameters live in template units (global translation
included), so every coordinate of the parameter vector has the same scale and
the Tikhonov weight is dimensionless.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.optimize import minimize
from scipy.spatial import cKDTree

from core.chart import crop_with_mask, load_chart_grayscale
from core.extract import binarize_adaptive, half_widths_on_medial_axis, skeleton_and_width
from core.template import SamplePlan, build_sample_plan, capsule_union_rings, sample_with_sample_plan


DEFAULT_LAMBDA_REG = 1.0
DEFAULT_WIDTH_WEIGHT = 0.15
DEFAULT_COVERAGE_WEIGHT = 0.3
DEFAULT_N_SAMPLES = 120
DEFAULT_MAX_ITER = 300
# Cap per-anchor displacement (in template units) so the fit cannot fold the
# ductus back on itself — a loose topology guard alongside the Tikhonov term.
MAX_ANCHOR_DELTA = 0.75
# A fit counts as converged when BOTH residuals are within tolerance: the
# centerline sits near the skeleton (template→skeleton, RMS) AND the skeleton
# is covered by the template (skeleton→template) — a template collapsed onto a
# subset of the ink has a tiny geometry residual and only the coverage term
# exposes it. Both fractions of the x-height.
CONVERGED_GEO_RMSE_UNITS = 0.08
CONVERGED_COVERAGE_RMSE_UNITS = 0.10
# Skeleton pixels used for the coverage term (subsampled for cost).
MAX_COVERAGE_POINTS = 300
# Smoothing of the optimisation fields. The EDT ridge at the skeleton and the
# steps of the propagated width map are the non-smooth spots; ~1px of Gaussian
# rounds them off without moving the minima visibly.
DIST_FIELD_SIGMA_PX = 1.0
WIDTH_FIELD_SIGMA_PX = 1.5

# ---- refine_template_against_crop constants ----
# The refine is a polish on an already-snapped trace: anchors move at most a
# fraction of the snap bound, widths at most ±50% of their measured value
# (plus half a pixel of absolute headroom so hairlines are not frozen).
REFINE_MAX_ANCHOR_DELTA = 0.15
REFINE_LAMBDA_REG = 0.25
MAX_WIDTH_REL_DELTA = 0.5
# Rendered widths never collapse below this (px): protects hairlines whose
# boundary gradient is too weak to hold them up.
WIDTH_FLOOR_PX = 0.4
# Signed boundary field smoothing: the field is smooth across the ink edge
# itself (its kinks sit on the inner/outer medial axes), 1px rounds those.
BOUNDARY_FIELD_SIGMA_PX = 1.0
DEFAULT_BOUNDARY_WEIGHT = 1.0
# Width-profile second-difference (w''(s), arc-length normalised, template
# units) regulariser. Calibrated on the glyph bench (12 Loth glyphs): 1e-5
# leaves the boundary term tracking edge noise (waviness_ratio up to 1.8 on
# h-final), 1e-3 starts flattening genuine Schwellzug (median IoU drops
# 0.846→0.836); 1e-4 is the knee — best median IoU with the waviness brought
# back near 1. Also pinned by the de-noising test in tests/test_refine.py.
DEFAULT_WIDTH_SMOOTH_WEIGHT = 1e-4
# Small pull of widths toward their measured value — pins stretches where the
# boundary gradient is weak (hairlines); crossing-contaminated anchors are
# exempt (their measurement is an interpolation, not a reading).
DEFAULT_WIDTH_PRIOR_WEIGHT = 0.05
REFINE_OUTER_ROUNDS = 3
REFINE_MAX_ITER = 100
# Early-stop when a frozen-normal round improves the honest residual by less
# than this fraction.
REFINE_EARLY_STOP_REL = 0.02
CONVERGED_BOUNDARY_RMSE_UNITS = 0.06


@dataclass
class FitResult:
    """Outcome of fitting one template to one instance.

    `anchors`/`half_widths` are the fitted instance in *template* coordinates
    (ready for a §3 library entry); the `*_polyline_px` fields are crop-local
    pixels for overlay rendering (Original + Canonical grey + Fit red).
    """

    anchors: np.ndarray  # (K, 2) fitted, template coords
    half_widths: np.ndarray  # (K,) measured along the fit, template coords
    entry: dict
    exit_pt: dict
    advance: float
    fitted_polyline_px: np.ndarray  # (n_samples, 2) crop-local
    canonical_polyline_px: np.ndarray  # (n_samples, 2) crop-local, pre-fit placement
    placement: dict  # {x_origin_px, baseline_y_px, unit_px}
    # Index of each pen-stroke's first sample in the polylines, so a caller can
    # draw the overlay as separate strokes instead of bridging a pen lift.
    polyline_stroke_starts: list[int] = field(default_factory=lambda: [0])
    fit_meta: dict = field(default_factory=dict)
    # Half-width (crop px) measured at every fitted polyline sample — lets the
    # caller build a filled silhouette of the fit for overlay on the crop.
    fitted_sample_half_widths_px: np.ndarray | None = None

    def to_entry(self, glyph: str, position: str) -> dict:
        """Render the fit as a §3 library-entry dict (rounded, JSON-ready)."""
        return {
            "glyph": glyph,
            "position": position,
            "advance": round(float(self.advance), 4),
            "anchors": [[round(float(x), 4), round(float(y), 4)] for x, y in self.anchors],
            "half_widths": [round(float(h), 4) for h in self.half_widths],
            "entry": self.entry,
            "exit_pt": self.exit_pt,
            "fit": self.fit_meta,
        }


# -------------------------------------------------------------------- helpers


def _skeleton_points(skel: np.ndarray) -> np.ndarray:
    """Skeleton pixels as an (M, 2) array of (x, y) crop-local coordinates."""
    ys, xs = np.where(skel)
    return np.column_stack([xs.astype(float), ys.astype(float)])


def bilinear(field_map: np.ndarray, px: np.ndarray, py: np.ndarray) -> np.ndarray:
    """Sample a (H, W) field at float pixel coordinates, clamped to the crop.

    Public shared facility: `core.quality` reads the same EDT interpolant the
    optimiser descends, so "converged" and "high score" agree by construction.
    """
    val, _, _ = _bilinear_with_grad(field_map, px, py)
    return val


def _bilinear_with_grad(
    field_map: np.ndarray, px: np.ndarray, py: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Bilinear sample plus its EXACT spatial derivatives, clamped to the crop.

    The derivatives are those of the interpolant itself (not a resampled
    gradient map) — the optimiser's line search needs function and gradient to
    agree to machine precision, otherwise it aborts on phantom inconsistencies.
    Clamping is per axis: a sample beyond the crop in x has a zero x-derivative
    but keeps its y-derivative along the clamped border row (and vice versa).
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
    val = f00 * (1.0 - fx) * (1.0 - fy) + f01 * fx * (1.0 - fy) + f10 * (1.0 - fx) * fy + f11 * fx * fy
    dx = (f01 - f00) * (1.0 - fy) + (f11 - f10) * fy
    dy = (f10 - f00) * (1.0 - fx) + (f11 - f01) * fx
    inside_x = (px >= 0.0) & (px <= w - 1.0)
    inside_y = (py >= 0.0) & (py <= h - 1.0)
    return val, dx * inside_x, dy * inside_y


def _sampling_operator(template_anchors: np.ndarray, plan: SamplePlan) -> np.ndarray:
    """(n_samples, K) linear operator mapping anchor coords to centerline samples.

    Chord-length cubic-spline sampling (`core.template.sample_with_sample_plan`)
    is linear in the anchor coordinates once the parameterisation is frozen;
    freezing it at the canonical anchors (legitimate — the per-anchor deltas
    are bounded far below the anchor spacing) turns every objective evaluation
    into a matrix product and makes the analytic gradient exact. Duplicated
    corner rows are removed per `plan.drop_rows`, so the operator's output
    matches the rendered sampling row for row.
    """
    k = len(template_anchors)
    n_total = int(sum(plan.alloc))
    op = np.zeros((n_total, k))
    row = 0
    for (a, b), m in zip(plan.slices, plan.alloc, strict=True):
        seg = template_anchors[a:b]
        nn = b - a
        u = np.linspace(0.0, 1.0, m)
        if nn < 2:
            op[row : row + m, a] = 1.0
            row += m
            continue
        diffs = np.diff(seg, axis=0)
        chord = np.hypot(diffs[:, 0], diffs[:, 1])
        t = np.concatenate([[0.0], np.cumsum(chord)])
        if t[-1] == 0:
            op[row : row + m, a] = 1.0
            row += m
            continue
        t = t / t[-1]
        if nn < 3:
            for j in range(nn):
                basis = np.zeros(nn)
                basis[j] = 1.0
                op[row : row + m, a + j] = np.interp(u, t, basis)
        else:
            # One spline construction for the whole identity basis: the natural
            # spline is linear in y, so this is exactly the per-column result.
            op[row : row + m, a:b] = CubicSpline(t, np.eye(nn), bc_type="natural")(u)
        row += m
    return np.delete(op, plan.drop_rows, axis=0) if plan.drop_rows else op


def _width_operator(template_anchors: np.ndarray, plan: SamplePlan) -> np.ndarray:
    """(n_samples, K) linear operator mapping anchor half-widths to sample widths.

    `np.interp` over the frozen chord-length parameterisation is a linear map;
    building it once (identity basis per sub-arc) lets the optimiser treat the
    widths as free parameters with an exact analytic gradient — the same trick
    `_sampling_operator` plays for the coordinates.
    """
    k = len(template_anchors)
    n_total = int(sum(plan.alloc))
    op = np.zeros((n_total, k))
    row = 0
    for (a, b), m in zip(plan.slices, plan.alloc, strict=True):
        seg = template_anchors[a:b]
        nn = b - a
        u = np.linspace(0.0, 1.0, m)
        if nn < 2:
            op[row : row + m, a] = 1.0
            row += m
            continue
        diffs = np.diff(seg, axis=0)
        chord = np.hypot(diffs[:, 0], diffs[:, 1])
        t = np.concatenate([[0.0], np.cumsum(chord)])
        if t[-1] == 0:
            op[row : row + m, a] = 1.0
            row += m
            continue
        t = t / t[-1]
        for j in range(nn):
            basis = np.zeros(nn)
            basis[j] = 1.0
            op[row : row + m, a + j] = np.interp(u, t, basis)
        row += m
    return np.delete(op, plan.drop_rows, axis=0) if plan.drop_rows else op


def _tangent_deg(p0: np.ndarray, p1: np.ndarray) -> float:
    """Angle of the segment p0→p1 in degrees, atan2(dy, dx)."""
    return float(np.degrees(np.arctan2(p1[1] - p0[1], p1[0] - p0[0])))


# -------------------------------------------------------------------- core fit


def fit_template_to_instance(
    template_anchors: np.ndarray,
    template_half_widths: np.ndarray,
    skel: np.ndarray,
    width_map: np.ndarray,
    *,
    unit_px: float,
    baseline_y_px: float,
    x_origin_px: float | None = None,
    stroke_starts: Sequence[int] | None = None,
    corner_anchors: Sequence[int] | None = None,
    n_samples: int = DEFAULT_N_SAMPLES,
    lambda_reg: float = DEFAULT_LAMBDA_REG,
    width_weight: float = DEFAULT_WIDTH_WEIGHT,
    coverage_weight: float = DEFAULT_COVERAGE_WEIGHT,
    max_iter: int = DEFAULT_MAX_ITER,
    max_anchor_delta: float = MAX_ANCHOR_DELTA,
) -> FitResult:
    """Optimise template control points to match one instance skeleton + width.

    Parameters
    ----------
    template_anchors : (K, 2) array in template coords (baseline=0, midband=1).
    template_half_widths : (K,) array in template coords.
    skel : boolean skeleton of the instance crop (crop-local pixels).
    width_map : distance-transform half-width per pixel of the same crop.
    unit_px : x-height in pixels (``baseline_y - midband_y``).
    baseline_y_px : crop-local y of the baseline (``baseline_y - y0``).
    x_origin_px : crop-local x of the template origin; if ``None`` it is placed
        so the template centroid aligns to the skeleton centroid in x.
    stroke_starts : anchor indices where each pen-stroke begins (first is 0); each
        stroke is sampled independently so a pen lift is not bridged. ``None`` =>
        one continuous stroke (legacy).
    corner_anchors : anchor indices on within-stroke reversal corners; sampling
        splits the spline there (matching the corner-aware render), so the fit
        does not fight a kink the renderer keeps. ``None`` => no corners.
    lambda_reg : Tikhonov weight on per-anchor displacement (topology guard).
    width_weight : weight of the half-width residual relative to geometry.
    coverage_weight : weight of the skeleton→template coverage residual.
    max_anchor_delta : per-anchor displacement bound in template units. The
        default suits the M4 instance fit; callers refining a trace that
        already sits on the ink pass a tighter bound.

    Returns
    -------
    FitResult with the fitted instance in template coords plus crop-local
    overlay polylines and a `fit_meta` diagnostic (RMSEs, convergence verdict,
    optimiser status).
    """
    template_anchors = np.asarray(template_anchors, dtype=float)
    template_half_widths = np.asarray(template_half_widths, dtype=float)
    k = len(template_anchors)
    if k < 2:
        raise ValueError("need at least 2 template anchors to fit")
    if unit_px <= 0:
        raise ValueError(f"unit_px must be positive, got {unit_px}")

    skel_pts = _skeleton_points(skel)
    if len(skel_pts) == 0:
        raise ValueError("instance skeleton is empty — nothing to fit to")

    # Precomputed smooth lookup fields (pixel space). `dist_raw` keeps the
    # unsmoothed EDT for honest residual reporting; the smoothed twins (plus
    # their gradient maps) are the optimisation surface.
    dist_raw = distance_transform_edt(~skel).astype(float)
    dist_smooth = gaussian_filter(dist_raw, DIST_FIELD_SIGMA_PX)
    _, ink_idx = distance_transform_edt(~np.asarray(width_map > 0), return_indices=True)
    width_raw = width_map[ink_idx[0], ink_idx[1]].astype(float)
    width_smooth = gaussian_filter(width_raw, WIDTH_FIELD_SIGMA_PX)

    # Coverage targets: evenly subsampled skeleton pixels.
    if len(skel_pts) > MAX_COVERAGE_POINTS:
        cov_pts = skel_pts[np.linspace(0, len(skel_pts) - 1, MAX_COVERAGE_POINTS).astype(int)]
    else:
        cov_pts = skel_pts
    n_cov = len(cov_pts)

    # Auto-place the template origin so its centroid sits on the skeleton's.
    if x_origin_px is None:
        templ_centroid_px = float(np.mean(template_anchors[:, 0])) * unit_px
        x_origin_px = float(skel_pts[:, 0].mean()) - templ_centroid_px

    # Frozen sampling plan + linear operator (anchor count is constant through
    # the fit): each pen stroke is sampled on its own, so no sample lands on a
    # pen-lift bridge and the geometry residual is never inflated by phantom-gap
    # distances. Corner knots split the spline within a stroke, mirroring the
    # corner-aware render path.
    plan = build_sample_plan(template_anchors, stroke_starts, corner_anchors, n_samples)
    sample_starts = plan.sample_starts
    sampling_op = _sampling_operator(template_anchors, plan)
    sw_px = (_width_operator(template_anchors, plan) @ template_half_widths) * unit_px
    n_s = sampling_op.shape[0]

    def to_pixels(params: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        tx, ty = params[0], params[1]
        deltas = params[2:].reshape(k, 2)
        px = x_origin_px + (sampling_op @ (template_anchors[:, 0] + deltas[:, 0]) + tx) * unit_px
        py = baseline_y_px - (sampling_op @ (template_anchors[:, 1] + deltas[:, 1]) + ty) * unit_px
        return px, py

    unit_sq = unit_px**2
    crop_h, crop_w = skel.shape

    def out_of_crop(px: np.ndarray, py: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Signed distance of each sample beyond the crop border (0 inside).

        The lookup fields are clamped at the border, so a sample outside the
        crop would otherwise see a frozen value with zero gradient — it could
        sit there forever and still read a finite, under-stated residual.
        """
        return px - np.clip(px, 0.0, crop_w - 1.0), py - np.clip(py, 0.0, crop_h - 1.0)

    def objective(params: np.ndarray) -> tuple[float, np.ndarray]:
        deltas = params[2:].reshape(k, 2)
        px, py = to_pixels(params)

        d, d_dx, d_dy = _bilinear_with_grad(dist_smooth, px, py)
        e_geo = float(np.mean(d**2)) / unit_sq
        g_px = 2.0 * d * d_dx / (n_s * unit_sq)
        g_py = 2.0 * d * d_dy / (n_s * unit_sq)

        # Out-of-crop pull (geometry-class weight): restores the gradient the
        # clamped fields lose beyond the border.
        ox, oy = out_of_crop(px, py)
        e_geo += float(np.mean(ox**2 + oy**2)) / unit_sq
        g_px = g_px + 2.0 * ox / (n_s * unit_sq)
        g_py = g_py + 2.0 * oy / (n_s * unit_sq)

        wm, w_dx, w_dy = _bilinear_with_grad(width_smooth, px, py)
        wr = wm - sw_px
        e_wid = float(np.mean(wr**2)) / unit_sq
        g_px = g_px + width_weight * 2.0 * wr * w_dx / (n_s * unit_sq)
        g_py = g_py + width_weight * 2.0 * wr * w_dy / (n_s * unit_sq)

        # Coverage: distance from each (subsampled) skeleton pixel to its
        # nearest template sample. The assignment is held fixed for the
        # gradient (exact almost everywhere, ICP-style).
        pts = np.column_stack([px, py])
        cdist, cidx = cKDTree(pts).query(cov_pts)
        e_cov = float(np.mean(cdist**2)) / unit_sq
        g_cov = np.zeros((n_s, 2))
        np.add.at(g_cov, cidx, 2.0 * (pts[cidx] - cov_pts) / (n_cov * unit_sq))
        g_px = g_px + coverage_weight * g_cov[:, 0]
        g_py = g_py + coverage_weight * g_cov[:, 1]

        e_reg = float(np.mean(np.sum(deltas**2, axis=1)))

        f = e_geo + width_weight * e_wid + coverage_weight * e_cov + lambda_reg * e_reg

        # Chain rule through the pixel mapping: dpx/dtx = unit_px,
        # dpy/dty = -unit_px, dpx/dax = unit_px * S, dpy/day = -unit_px * S.
        grad = np.empty_like(params)
        grad[0] = unit_px * float(g_px.sum())
        grad[1] = -unit_px * float(g_py.sum())
        g_anchors = np.column_stack([unit_px * (sampling_op.T @ g_px), -unit_px * (sampling_op.T @ g_py)])
        grad[2:] = (g_anchors + lambda_reg * 2.0 * deltas / k).ravel()
        return f, grad

    def report_energies(params: np.ndarray) -> tuple[float, float, float]:
        """Honest residuals on the UNSMOOTHED fields (geo, width, coverage).

        Samples beyond the crop add their border distance to the clamped field
        value, so a truncated fit cannot report a flattering residual.
        """
        px, py = to_pixels(params)
        ox, oy = out_of_crop(px, py)
        d_eff = bilinear(dist_raw, px, py) + np.hypot(ox, oy)
        e_geo = float(np.mean(d_eff**2)) / unit_sq
        e_wid = float(np.mean((bilinear(width_raw, px, py) - sw_px) ** 2)) / unit_sq
        cdist, _ = cKDTree(np.column_stack([px, py])).query(cov_pts)
        e_cov = float(np.mean(cdist**2)) / unit_sq
        return e_geo, e_wid, e_cov

    n_params = 2 + 2 * k
    x0 = np.zeros(n_params)
    max_shift_units = float(max(crop_h, crop_w)) / unit_px
    bounds = [(-max_shift_units, max_shift_units)] * 2
    bounds += [(-max_anchor_delta, max_anchor_delta)] * (2 * k)

    e_geo0, _, _ = report_energies(x0)
    res = minimize(
        objective,
        x0,
        jac=True,
        method="L-BFGS-B",
        bounds=bounds,
        # maxfun generously above maxiter: with the analytic jacobian each
        # iteration costs a handful of evaluations, so the evaluation budget
        # must never be the binding stop (it used to be, masquerading as
        # "not converged" on perfectly good fits).
        options={"maxiter": max_iter, "maxfun": 50 * max_iter},
    )

    tx, ty = res.x[0], res.x[1]
    deltas = res.x[2:].reshape(k, 2)
    fitted_anchors = template_anchors + deltas

    # Final overlay polylines (crop-local pixels).
    px, py = to_pixels(res.x)
    fitted_polyline_px = np.column_stack([px, py])
    cpx, cpy = to_pixels(x0)
    canonical_polyline_px = np.column_stack([cpx, cpy])

    # Measured half-widths along the fit — projected onto the medial axis,
    # like the canonical sampler: reading the EDT at the raw sample position
    # under-measures by exactly the centerline's off-axis offset (which the
    # converged tolerance explicitly permits).
    mask = width_map > 0
    snap_cap_px = max(3.0, 0.25 * unit_px)
    fitted_sample_hw_px = half_widths_on_medial_axis(fitted_polyline_px, skel, mask, width_map, snap_cap_px)

    # Effective placement after the global translation (template units → px).
    x_origin_fit = float(x_origin_px + tx * unit_px)
    baseline_y_fit = float(baseline_y_px - ty * unit_px)

    # Measured half-widths along the fit, sampled at the K fitted anchors.
    anchor_px = x_origin_fit + fitted_anchors[:, 0] * unit_px
    anchor_py = baseline_y_fit - fitted_anchors[:, 1] * unit_px
    fitted_half_widths = (
        half_widths_on_medial_axis(np.column_stack([anchor_px, anchor_py]), skel, mask, width_map, snap_cap_px)
        / unit_px
    )

    e_geo, e_wid, e_cov = report_energies(res.x)
    e_reg = float(np.mean(np.sum(deltas**2, axis=1)))
    entry = {
        "xy": [round(float(fitted_anchors[0, 0]), 4), round(float(fitted_anchors[0, 1]), 4)],
        "tangent_deg": round(_tangent_deg(fitted_anchors[0], fitted_anchors[1]), 1),
        "coupling": "baseline",
    }
    exit_pt = {
        "xy": [round(float(fitted_anchors[-1, 0]), 4), round(float(fitted_anchors[-1, 1]), 4)],
        "tangent_deg": round(_tangent_deg(fitted_anchors[-2], fitted_anchors[-1]), 1),
        "coupling": "baseline",
    }
    advance = float(max(0.1, fitted_anchors[:, 0].max() - fitted_anchors[:, 0].min()))

    geo_rmse_px = float(np.sqrt(e_geo) * unit_px)
    coverage_rmse_px = float(np.sqrt(e_cov) * unit_px)
    converged = bool(
        geo_rmse_px <= CONVERGED_GEO_RMSE_UNITS * unit_px
        and coverage_rmse_px <= CONVERGED_COVERAGE_RMSE_UNITS * unit_px
    )
    fit_meta = {
        # Residual-based verdict — what the UI should show. `success` mirrors
        # it for older clients; the raw optimiser status moves to optimizer_*.
        "converged": converged,
        "success": converged,
        "optimizer_success": bool(res.success),
        "message": str(res.message),
        "iterations": int(res.nit),
        "n_evaluations": int(res.nfev),
        "geo_rmse_px": round(geo_rmse_px, 3),
        "geo_rmse_px_initial": round(float(np.sqrt(e_geo0) * unit_px), 3),
        "width_rmse_px": round(float(np.sqrt(e_wid) * unit_px), 3),
        "coverage_rmse_px": round(coverage_rmse_px, 3),
        "reg_energy": round(e_reg, 6),
        "max_anchor_delta": round(float(np.max(np.hypot(deltas[:, 0], deltas[:, 1]))), 4),
        "lambda_reg": lambda_reg,
        "width_weight": width_weight,
        "coverage_weight": coverage_weight,
        "n_samples": n_samples,
    }

    return FitResult(
        anchors=fitted_anchors,
        half_widths=fitted_half_widths,
        entry=entry,
        exit_pt=exit_pt,
        advance=advance,
        fitted_polyline_px=fitted_polyline_px,
        canonical_polyline_px=canonical_polyline_px,
        placement={"x_origin_px": x_origin_fit, "baseline_y_px": baseline_y_fit, "unit_px": float(unit_px)},
        polyline_stroke_starts=sample_starts,
        fit_meta=fit_meta,
        fitted_sample_half_widths_px=fitted_sample_hw_px,
    )


# ----------------------------------------------------------------- refinement


def _unit_tangents_normals(
    px: np.ndarray, py: np.ndarray, sample_starts: Sequence[int], corner_sample_idx: Sequence[int]
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Per-sample unit tangents + normals, per pen-stroke, corner-aware.

    Tangents come from central differences within each stroke; the corner
    samples get the bisector of their two adjacent chord normals (a 180° cusp
    has no defined normal — the gradient normal stays, the round cap covers it).
    """
    n_s = len(px)
    tx = np.zeros(n_s)
    ty = np.zeros(n_s)
    bounds = [*sample_starts, n_s]
    for a, b in zip(bounds[:-1], bounds[1:], strict=True):
        if b - a < 2:
            tx[a:b] = 1.0
            continue
        gx = np.gradient(px[a:b])
        gy = np.gradient(py[a:b])
        norm = np.hypot(gx, gy)
        norm[norm == 0] = 1.0
        tx[a:b] = gx / norm
        ty[a:b] = gy / norm
    nx = -ty.copy()
    ny = tx.copy()
    for c in corner_sample_idx:
        if not 0 < c < n_s - 1:
            continue
        d_in = np.array([px[c] - px[c - 1], py[c] - py[c - 1]])
        d_out = np.array([px[c + 1] - px[c], py[c + 1] - py[c]])
        normals = []
        for d in (d_in, d_out):
            length = float(np.hypot(d[0], d[1]))
            if length > 0:
                normals.append(np.array([-d[1], d[0]]) / length)
        if len(normals) == 2:
            bisector = normals[0] + normals[1]
            length = float(np.hypot(bisector[0], bisector[1]))
            if length > 1e-9:
                nx[c], ny[c] = bisector / length
    return tx, ty, nx, ny


def _width_curvature_operator(
    anchors: np.ndarray, stroke_starts: Sequence[int] | None, corner_anchors: Sequence[int] | None
) -> np.ndarray:
    """(m, K) operator whose rows are the arc-length-normalised second
    differences w''(s) of the half-width profile, per smoothness chain.

    Chains break at pen lifts AND at corner anchors: a true Umkehrpunkt has a
    width-profile kink (pressure released into the turn) that must not be
    penalised. Returns a (0, K) matrix when no chain is long enough.
    """
    k = len(anchors)
    d = np.diff(anchors, axis=0)
    ds = np.hypot(d[:, 0], d[:, 1])
    ds[ds <= 0] = 1e-6
    stroke_bounds = sorted({0, *(int(s) for s in (stroke_starts or []) if 0 < int(s) < k), k})
    corners = sorted({int(c) for c in (corner_anchors or [])})
    rows: list[np.ndarray] = []
    for a, b in zip(stroke_bounds[:-1], stroke_bounds[1:], strict=True):
        cuts = [c for c in corners if a < c < b - 1]
        for s_, e_ in zip([a, *cuts], [*[c + 1 for c in cuts], b], strict=True):
            for j in range(s_ + 1, e_ - 1):
                row = np.zeros(k)
                scale = 2.0 / (ds[j - 1] + ds[j])
                row[j - 1] = scale / ds[j - 1]
                row[j] = -scale * (1.0 / ds[j - 1] + 1.0 / ds[j])
                row[j + 1] = scale / ds[j]
                rows.append(row)
    return np.array(rows) if rows else np.zeros((0, k))


@dataclass
class _RefineContext:
    """Static inputs of one refine run, shared by all frozen-normal rounds."""

    template_anchors: np.ndarray
    w0: np.ndarray
    k: int
    stroke_starts: Sequence[int] | None
    corner_anchors: Sequence[int] | None
    n_samples: int
    unit_px: float
    unit_sq: float
    x_origin_px: float
    baseline_y_px: float
    crop_h: int
    crop_w: int
    dist_raw: np.ndarray
    dist_smooth: np.ndarray
    sgn_raw: np.ndarray
    sgn_smooth: np.ndarray
    cov_pts: np.ndarray
    crossing_wide: np.ndarray  # crossing-contaminated anchor indices ±1, sorted
    c_prior: np.ndarray  # per-anchor width-prior mask (0 on crossing anchors)
    boundary_weight: float
    coverage_weight: float
    lambda_reg: float
    width_smooth_weight: float
    width_prior_weight: float

    def out_of_crop(self, px: np.ndarray, py: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Signed distance of each sample beyond the crop border (0 inside)."""
        return px - np.clip(px, 0.0, self.crop_w - 1.0), py - np.clip(py, 0.0, self.crop_h - 1.0)


class _RefineRound:
    """One frozen-normal outer round of `refine_template_against_crop` (ICP-style).

    Freezes the sampling/width operators, tangents/normals, sample weights and
    the width-curvature operator at the given anchors; `objective` then sees an
    exactly analytic gradient — function and gradient agree to machine
    precision, as L-BFGS-B's line search requires (`core.fit` module header) —
    and `honest` reports residuals on the UNSMOOTHED fields.
    """

    def __init__(self, ctx: _RefineContext, current_anchors: np.ndarray) -> None:
        self.ctx = ctx
        self.plan = build_sample_plan(current_anchors, ctx.stroke_starts, ctx.corner_anchors, ctx.n_samples)
        self.s_op = _sampling_operator(current_anchors, self.plan)
        self.w_op = _width_operator(current_anchors, self.plan)
        self.n_s = self.s_op.shape[0]

        base_px = ctx.x_origin_px + (self.s_op @ current_anchors[:, 0]) * ctx.unit_px
        base_py = ctx.baseline_y_px - (self.s_op @ current_anchors[:, 1]) * ctx.unit_px
        self.tdx, self.tdy, self.nx, self.ny = _unit_tangents_normals(
            base_px, base_py, self.plan.sample_starts, self.plan.corner_sample_idx
        )

        # Sample weights: u for the boundary term (zero on crossing-contaminated
        # stretches — there the ink edge belongs to the union blob), v for the
        # geometry term (zero on stroke-end samples — the skeleton erodes ends;
        # the cap term owns them instead).
        anchor_px = np.column_stack(
            [
                ctx.x_origin_px + current_anchors[:, 0] * ctx.unit_px,
                ctx.baseline_y_px - current_anchors[:, 1] * ctx.unit_px,
            ]
        )
        _, nearest = cKDTree(anchor_px).query(np.column_stack([base_px, base_py]))
        self.u = np.where(np.isin(nearest, ctx.crossing_wide), 0.0, 1.0)
        self.v = np.ones(self.n_s)
        cap_rows: list[int] = []
        cap_signs: list[float] = []
        sample_bounds = [*self.plan.sample_starts, self.n_s]
        for a, b in zip(sample_bounds[:-1], sample_bounds[1:], strict=True):
            self.v[a] = 0.0
            self.v[b - 1] = 0.0
            cap_rows += [a, b - 1]
            cap_signs += [-1.0, 1.0]
        self.cap_rows = np.array(cap_rows, dtype=int)
        self.cap_signs = np.array(cap_signs)
        self.n_v = max(1.0, float(self.v.sum()))
        self.norm_b = max(1.0, 2.0 * float(self.u.sum()) + float(len(cap_rows)))

        self.d2 = _width_curvature_operator(current_anchors, ctx.stroke_starts, ctx.corner_anchors)
        self.m_d2 = max(1, self.d2.shape[0])

    def to_pixels(self, p: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Centerline samples (px) + pixel half-widths for a parameter vector."""
        ctx = self.ctx
        k = ctx.k
        da = p[2 : 2 + 2 * k].reshape(k, 2)
        dw = p[2 + 2 * k :]
        px = ctx.x_origin_px + (self.s_op @ (ctx.template_anchors[:, 0] + da[:, 0]) + p[0]) * ctx.unit_px
        py = ctx.baseline_y_px - (self.s_op @ (ctx.template_anchors[:, 1] + da[:, 1]) + p[1]) * ctx.unit_px
        h = (self.w_op @ (ctx.w0 + dw)) * ctx.unit_px
        return px, py, h

    def _edge_points(self, px: np.ndarray, py: np.ndarray, h: np.ndarray, sign: float) -> tuple[np.ndarray, np.ndarray]:
        return px + sign * h * self.nx, py + sign * h * self.ny

    def _cap_points(self, px: np.ndarray, py: np.ndarray, h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        rows, signs = self.cap_rows, self.cap_signs
        return px[rows] + signs * h[rows] * self.tdx[rows], py[rows] + signs * h[rows] * self.tdy[rows]

    def _boundary_eval(
        self, field: np.ndarray, qx: np.ndarray, qy: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Per-point boundary energy + its exact d/dq (border pull included)."""
        val, gx, gy = _bilinear_with_grad(field, qx, qy)
        oxq, oyq = self.ctx.out_of_crop(qx, qy)
        return val**2 + oxq**2 + oyq**2, 2.0 * (val * gx + oxq), 2.0 * (val * gy + oyq)

    def objective(self, p: np.ndarray) -> tuple[float, np.ndarray]:
        ctx = self.ctx
        k = ctx.k
        unit_sq = ctx.unit_sq
        da = p[2 : 2 + 2 * k].reshape(k, 2)
        dw = p[2 + 2 * k :]
        px, py, h = self.to_pixels(p)

        g_px = np.zeros(self.n_s)
        g_py = np.zeros(self.n_s)
        g_h = np.zeros(self.n_s)

        # Geometry: centerline on the skeleton (v-weighted, ends excluded).
        d, ddx, ddy = _bilinear_with_grad(ctx.dist_smooth, px, py)
        ox, oy = ctx.out_of_crop(px, py)
        e_geo = float((self.v * (d**2 + ox**2 + oy**2)).sum()) / (self.n_v * unit_sq)
        g_px += self.v * 2.0 * (d * ddx + ox) / (self.n_v * unit_sq)
        g_py += self.v * 2.0 * (d * ddy + oy) / (self.n_v * unit_sq)

        # Boundary: edge points q± on the ink edge (u-weighted)…
        bw = ctx.boundary_weight
        e_bnd_sum = 0.0
        for sign in (1.0, -1.0):
            energy, dqx, dqy = self._boundary_eval(ctx.sgn_smooth, *self._edge_points(px, py, h, sign))
            e_bnd_sum += float((self.u * energy).sum())
            g_px += bw * self.u * dqx / (self.norm_b * unit_sq)
            g_py += bw * self.u * dqy / (self.norm_b * unit_sq)
            g_h += bw * sign * self.u * (dqx * self.nx + dqy * self.ny) / (self.norm_b * unit_sq)
        # …and round caps pulled to the true stroke ends.
        energy, dqx, dqy = self._boundary_eval(ctx.sgn_smooth, *self._cap_points(px, py, h))
        e_bnd_sum += float(energy.sum())
        rows, signs = self.cap_rows, self.cap_signs
        np.add.at(g_px, rows, bw * dqx / (self.norm_b * unit_sq))
        np.add.at(g_py, rows, bw * dqy / (self.norm_b * unit_sq))
        np.add.at(g_h, rows, bw * signs * (dqx * self.tdx[rows] + dqy * self.tdy[rows]) / (self.norm_b * unit_sq))
        e_bnd = e_bnd_sum / (self.norm_b * unit_sq)

        # Coverage: skeleton → template (ICP-frozen assignment).
        pts = np.column_stack([px, py])
        cdist, cidx = cKDTree(pts).query(ctx.cov_pts)
        n_cov = len(ctx.cov_pts)
        e_cov = float(np.mean(cdist**2)) / unit_sq
        g_cov = np.zeros((self.n_s, 2))
        np.add.at(g_cov, cidx, 2.0 * (pts[cidx] - ctx.cov_pts) / (n_cov * unit_sq))
        g_px += ctx.coverage_weight * g_cov[:, 0]
        g_py += ctx.coverage_weight * g_cov[:, 1]

        # Regularisers: anchor Tikhonov, width-profile curvature, width prior.
        e_reg = float(np.mean(np.sum(da**2, axis=1)))
        r = self.d2 @ (ctx.w0 + dw)
        e_wsm = float((r**2).sum()) / self.m_d2
        e_wpr = float((ctx.c_prior * dw**2).mean())

        f = (
            e_geo
            + bw * e_bnd
            + ctx.coverage_weight * e_cov
            + ctx.lambda_reg * e_reg
            + ctx.width_smooth_weight * e_wsm
            + ctx.width_prior_weight * e_wpr
        )

        grad = np.empty_like(p)
        grad[0] = ctx.unit_px * float(g_px.sum())
        grad[1] = -ctx.unit_px * float(g_py.sum())
        g_anchors = np.column_stack([ctx.unit_px * (self.s_op.T @ g_px), -ctx.unit_px * (self.s_op.T @ g_py)])
        grad[2 : 2 + 2 * k] = (g_anchors + ctx.lambda_reg * 2.0 * da / k).ravel()
        grad[2 + 2 * k :] = (
            ctx.unit_px * (self.w_op.T @ g_h)
            + ctx.width_smooth_weight * 2.0 * (self.d2.T @ r) / self.m_d2
            + ctx.width_prior_weight * 2.0 * ctx.c_prior * dw / k
        )
        return f, grad

    def honest(self, p: np.ndarray) -> tuple[float, float, float]:
        """(geo, boundary, coverage) RMSE in px on the UNSMOOTHED fields."""
        ctx = self.ctx
        px, py, h = self.to_pixels(p)
        ox, oy = ctx.out_of_crop(px, py)
        d_eff = bilinear(ctx.dist_raw, px, py) + np.hypot(ox, oy)
        geo = float((self.v * d_eff**2).sum() / self.n_v)
        bnd_sum = 0.0
        for sign in (1.0, -1.0):
            energy, _, _ = self._boundary_eval(ctx.sgn_raw, *self._edge_points(px, py, h, sign))
            bnd_sum += float((self.u * energy).sum())
        energy, _, _ = self._boundary_eval(ctx.sgn_raw, *self._cap_points(px, py, h))
        bnd_sum += float(energy.sum())
        cdist, _ = cKDTree(np.column_stack([px, py])).query(ctx.cov_pts)
        cov = float(np.mean(cdist**2))
        return float(np.sqrt(geo)), float(np.sqrt(bnd_sum / self.norm_b)), float(np.sqrt(cov))


def refine_template_against_crop(
    template_anchors: np.ndarray,
    template_half_widths: np.ndarray,
    skel: np.ndarray,
    width_map: np.ndarray,
    *,
    unit_px: float,
    baseline_y_px: float,
    x_origin_px: float,
    stroke_starts: Sequence[int] | None = None,
    corner_anchors: Sequence[int] | None = None,
    crossing_anchors: Sequence[int] | None = None,
    n_samples: int = DEFAULT_N_SAMPLES,
    boundary_weight: float = DEFAULT_BOUNDARY_WEIGHT,
    coverage_weight: float = DEFAULT_COVERAGE_WEIGHT,
    lambda_reg: float = REFINE_LAMBDA_REG,
    width_smooth_weight: float = DEFAULT_WIDTH_SMOOTH_WEIGHT,
    width_prior_weight: float = DEFAULT_WIDTH_PRIOR_WEIGHT,
    max_anchor_delta: float = REFINE_MAX_ANCHOR_DELTA,
    max_width_rel_delta: float = MAX_WIDTH_REL_DELTA,
    outer_rounds: int = REFINE_OUTER_ROUNDS,
    max_iter: int = REFINE_MAX_ITER,
) -> FitResult:
    """Polish a snapped template — anchors AND half-widths — against the ink itself.

    The snap puts the centerline on the skeleton; the widths are then read
    point-by-point from the EDT, which is noisy (integer quantisation,
    binarization stair-stepping on slanted edges, tilted readings on tapers).
    This refinement makes the *rendered silhouette boundary* the target
    instead: the edge points ``q± = p ± w·n`` of every centerline sample must
    lie on the ink edge (signed-distance field ``S = EDT_inside − EDT_outside``
    is zero there), which averages the per-point noise over the whole edge.
    Round caps are pulled to the true stroke ends the same way (the skeleton
    erodes ends, so the snap alone leaves caps short). A per-chain second-
    difference regulariser keeps the width profile smooth — it replaces the
    post-hoc median/box filter as the final arbiter (the filter remains as
    initialisation) — and a small prior pins widths where the boundary signal
    is weak. Crossing-contaminated stretches are excluded from the boundary
    term (their ink edge belongs to the union blob of both passes).

    Optimised jointly per frozen-normal outer round (ICP-style): the sampling/
    width operators, normals, weights and curvature operator are rebuilt at the
    current anchors between rounds, while the inner L-BFGS-B sees an exactly
    analytic gradient (the same frozen-operator trick as the M4 fit — a numeric
    gradient for 2+3K parameters would re-introduce the evaluation-budget
    failure mode and break line-search consistency). The best round by honest
    (unsmoothed-field) residual wins.

    Returns a FitResult whose ``half_widths`` are the OPTIMISED values (not
    re-measured) and whose ``anchors`` carry the folded global translation, so
    ``placement`` keeps the caller's original origin/baseline.
    """
    template_anchors = np.asarray(template_anchors, dtype=float)
    w0 = np.asarray(template_half_widths, dtype=float)
    k = len(template_anchors)
    if k < 2:
        raise ValueError("need at least 2 template anchors to refine")
    if unit_px <= 0:
        raise ValueError(f"unit_px must be positive, got {unit_px}")
    skel_pts = _skeleton_points(skel)
    if len(skel_pts) == 0:
        raise ValueError("instance skeleton is empty — nothing to refine against")

    # ---- fields (precomputed once; smoothed twins are the optimisation surface)
    mask = width_map > 0
    dist_raw = distance_transform_edt(~skel).astype(float)
    dist_smooth = gaussian_filter(dist_raw, DIST_FIELD_SIGMA_PX)
    # Signed distance to the ink boundary: positive inside (the EDT-to-
    # background IS width_map), negative outside, zero on the edge.
    sgn_raw = width_map.astype(float) - distance_transform_edt(mask == 0).astype(float)
    sgn_smooth = gaussian_filter(sgn_raw, BOUNDARY_FIELD_SIGMA_PX)

    if len(skel_pts) > MAX_COVERAGE_POINTS:
        cov_pts = skel_pts[np.linspace(0, len(skel_pts) - 1, MAX_COVERAGE_POINTS).astype(int)]
    else:
        cov_pts = skel_pts

    crop_h, crop_w = skel.shape
    unit_sq = unit_px**2
    crossing_set = {int(c) for c in (crossing_anchors or [])}
    # Down-weight the crossing anchors AND their direct neighbours — the blob
    # edge extends a little beyond the geometric overlap.
    crossing_wide = crossing_set | {c + 1 for c in crossing_set} | {c - 1 for c in crossing_set}

    # ---- parameter bounds (fixed, relative to the ORIGINAL anchors/widths)
    max_shift_units = float(max(crop_h, crop_w)) / unit_px
    floor_units = WIDTH_FLOOR_PX / unit_px
    dw_low = np.maximum(floor_units, (1.0 - max_width_rel_delta) * w0) - w0
    dw_high = max_width_rel_delta * w0 + 0.5 / unit_px
    dw_high = np.maximum(dw_high, dw_low)  # degenerate w0 < floor: allow growth to the floor
    bounds = [(-max_shift_units, max_shift_units)] * 2
    bounds += [(-max_anchor_delta, max_anchor_delta)] * (2 * k)
    bounds += list(zip(dw_low, dw_high, strict=True))

    ctx = _RefineContext(
        template_anchors=template_anchors,
        w0=w0,
        k=k,
        stroke_starts=stroke_starts,
        corner_anchors=corner_anchors,
        n_samples=n_samples,
        unit_px=float(unit_px),
        unit_sq=unit_sq,
        x_origin_px=float(x_origin_px),
        baseline_y_px=float(baseline_y_px),
        crop_h=crop_h,
        crop_w=crop_w,
        dist_raw=dist_raw,
        dist_smooth=dist_smooth,
        sgn_raw=sgn_raw,
        sgn_smooth=sgn_smooth,
        cov_pts=cov_pts,
        crossing_wide=np.array(sorted(crossing_wide), dtype=int),
        c_prior=np.array([0.0 if j in crossing_set else 1.0 for j in range(k)]),
        boundary_weight=boundary_weight,
        coverage_weight=coverage_weight,
        lambda_reg=lambda_reg,
        width_smooth_weight=width_smooth_weight,
        width_prior_weight=width_prior_weight,
    )

    params = np.zeros(2 + 3 * k)
    best_params = params.copy()
    best_honest = np.inf
    honest_initial: tuple[float, float, float] | None = None
    rounds_used = 0
    rnd: _RefineRound | None = None

    for round_idx in range(outer_rounds):
        # Freeze the linearisation at the current point (translation does not
        # affect chord lengths, so the plan/operators ignore tx/ty).
        da_prev = params[2 : 2 + 2 * k].reshape(k, 2)
        rnd = _RefineRound(ctx, template_anchors + da_prev)
        if honest_initial is None:
            honest_initial = rnd.honest(np.zeros_like(params))

        res = minimize(
            rnd.objective,
            params,
            jac=True,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": max_iter, "maxfun": 50 * max_iter},
        )
        rounds_used = round_idx + 1

        geo_r, bnd_r, cov_r = rnd.honest(res.x)
        honest_score = geo_r**2 + boundary_weight * bnd_r**2 + coverage_weight * cov_r**2
        improved = honest_score < best_honest * (1.0 - REFINE_EARLY_STOP_REL)
        if honest_score < best_honest:
            best_honest = honest_score
            best_params = res.x.copy()
        params = res.x
        if not improved:
            break

    # ---- final state from the best round (translation folded into the anchors)
    tx, ty = best_params[0], best_params[1]
    da = best_params[2 : 2 + 2 * k].reshape(k, 2)
    dw = best_params[2 + 2 * k :]
    fitted_anchors = template_anchors + da + np.array([tx, ty])
    fitted_widths = w0 + dw

    final_plan = build_sample_plan(fitted_anchors, stroke_starts, corner_anchors, n_samples)
    sx, sy, sw = sample_with_sample_plan(fitted_anchors, fitted_widths, final_plan)
    fitted_polyline_px = np.column_stack([x_origin_px + sx * unit_px, baseline_y_px - sy * unit_px])
    init_plan = build_sample_plan(template_anchors, stroke_starts, corner_anchors, n_samples)
    cx, cy, _ = sample_with_sample_plan(template_anchors, w0, init_plan)
    canonical_polyline_px = np.column_stack([x_origin_px + cx * unit_px, baseline_y_px - cy * unit_px])

    # Honest residuals of the chosen state, reported with the LAST round's
    # frozen weights/normals (that freeze was built at the point the chosen
    # state equals, so the evaluation is consistent).
    geo_rmse_px, boundary_rmse_px, coverage_rmse_px = rnd.honest(best_params)

    def _anchor_tv(widths: np.ndarray) -> float:
        bounds_a = sorted({0, *(int(s) for s in (stroke_starts or []) if 0 < int(s) < k), k})
        total = 0.0
        for a, b in zip(bounds_a[:-1], bounds_a[1:], strict=True):
            if b - a >= 2:
                total += float(np.abs(np.diff(widths[a:b])).sum())
        return total * unit_px

    converged = bool(
        geo_rmse_px <= CONVERGED_GEO_RMSE_UNITS * unit_px
        and coverage_rmse_px <= CONVERGED_COVERAGE_RMSE_UNITS * unit_px
        and boundary_rmse_px <= CONVERGED_BOUNDARY_RMSE_UNITS * unit_px
    )
    fit_meta = {
        "converged": converged,
        "geo_rmse_px": round(geo_rmse_px, 3),
        "boundary_rmse_px": round(boundary_rmse_px, 3),
        "boundary_rmse_px_initial": round(honest_initial[1], 3) if honest_initial else None,
        "coverage_rmse_px": round(coverage_rmse_px, 3),
        "width_tv_px_initial": round(_anchor_tv(w0), 2),
        "width_tv_px": round(_anchor_tv(fitted_widths), 2),
        "max_anchor_shift": round(float(np.max(np.hypot(da[:, 0] + tx, da[:, 1] + ty))), 4),
        "outer_rounds_used": rounds_used,
        "boundary_weight": boundary_weight,
        "width_smooth_weight": width_smooth_weight,
        "width_prior_weight": width_prior_weight,
        "lambda_reg": lambda_reg,
        "n_samples": n_samples,
    }

    entry = {
        "xy": [round(float(fitted_anchors[0, 0]), 4), round(float(fitted_anchors[0, 1]), 4)],
        "tangent_deg": round(_tangent_deg(fitted_anchors[0], fitted_anchors[1]), 1),
        "coupling": "baseline",
    }
    exit_pt = {
        "xy": [round(float(fitted_anchors[-1, 0]), 4), round(float(fitted_anchors[-1, 1]), 4)],
        "tangent_deg": round(_tangent_deg(fitted_anchors[-2], fitted_anchors[-1]), 1),
        "coupling": "baseline",
    }

    return FitResult(
        anchors=fitted_anchors,
        half_widths=fitted_widths,
        entry=entry,
        exit_pt=exit_pt,
        advance=float(max(0.1, fitted_anchors[:, 0].max() - fitted_anchors[:, 0].min())),
        fitted_polyline_px=fitted_polyline_px,
        canonical_polyline_px=canonical_polyline_px,
        placement={"x_origin_px": float(x_origin_px), "baseline_y_px": float(baseline_y_px), "unit_px": float(unit_px)},
        polyline_stroke_starts=final_plan.sample_starts,
        fit_meta=fit_meta,
        fitted_sample_half_widths_px=sw * unit_px,
    )


# ------------------------------------------------------------- high-level API


def fit_glyph_to_crop(
    glyph_row: dict,
    bbox: dict,
    chart_path: str,
    *,
    lambda_reg: float = DEFAULT_LAMBDA_REG,
    width_weight: float = DEFAULT_WIDTH_WEIGHT,
    coverage_weight: float = DEFAULT_COVERAGE_WEIGHT,
    n_samples: int = DEFAULT_N_SAMPLES,
    max_iter: int = DEFAULT_MAX_ITER,
) -> dict:
    """Fit a stored canonical (`glyph_row`) to the instance crop of `bbox`.

    Mirrors `core.pipeline.diagnostic_for_glyph`: loads the chart, crops with
    the eraser mask, binarises, extracts skeleton + distance transform, then fits.
    Returns a JSON-ready overlay dict — a filled library entry plus crop-local
    polylines for the three-way visual check (crop · canonical grey · fit red),
    the skeleton it was fitted to, and the fitted silhouette (`fitted_outline_px`,
    per-stroke ring lists) for a filled match-the-ink overlay.
    """
    for required in ("baseline_y", "midband_y", "y0", "y1", "x0", "x1"):
        if bbox.get(required) is None:
            raise ValueError(f"bbox missing required field {required!r}")

    chart_gray = load_chart_grayscale(chart_path)
    crop = crop_with_mask(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel, width_map = skeleton_and_width(mask)

    baseline_y = int(bbox["baseline_y"])
    midband_y = int(bbox["midband_y"])
    unit_px = float(baseline_y - midband_y)
    if unit_px <= 0:
        raise ValueError(f"baseline_y ({baseline_y}) must exceed midband_y ({midband_y})")
    baseline_y_px = baseline_y - int(bbox["y0"])

    result = fit_template_to_instance(
        np.asarray(glyph_row["anchors"], dtype=float),
        np.asarray(glyph_row["half_widths"], dtype=float),
        skel,
        width_map,
        unit_px=unit_px,
        baseline_y_px=baseline_y_px,
        # Accept stroke_starts/corner_anchors either top-level (router) or nested
        # in trace_meta (a raw canonical dict straight from the pipeline).
        stroke_starts=glyph_row.get("stroke_starts") or glyph_row.get("trace_meta", {}).get("stroke_starts"),
        corner_anchors=glyph_row.get("corner_anchors") or glyph_row.get("trace_meta", {}).get("corner_anchors"),
        lambda_reg=lambda_reg,
        width_weight=width_weight,
        coverage_weight=coverage_weight,
        n_samples=n_samples,
        max_iter=max_iter,
    )

    # Carry the canonical's coupling labels onto the fitted entry/exit.
    if glyph_row.get("entry", {}).get("coupling"):
        result.entry["coupling"] = glyph_row["entry"]["coupling"]
    if glyph_row.get("exit_pt", {}).get("coupling"):
        result.exit_pt["coupling"] = glyph_row["exit_pt"]["coupling"]

    # Filled silhouette of the fit, one ring list per pen-stroke, in crop px —
    # lets the UI overlay the fitted ink (with its measured Schwellzug) on the
    # original for a direct does-it-match check.
    starts = [*result.polyline_stroke_starts, len(result.fitted_polyline_px)]
    fitted_outline_px = [
        capsule_union_rings(
            result.fitted_polyline_px[a:b, 0],
            result.fitted_polyline_px[a:b, 1],
            result.fitted_sample_half_widths_px[a:b],
            simplify_tol=0.2,
            decimals=2,
        )
        for a, b in zip(starts[:-1], starts[1:], strict=True)
    ]

    h, w = crop.shape
    entry = result.to_entry(glyph_row["glyph"], glyph_row["position"])
    skel_pts = _skeleton_points(skel)
    return {
        **entry,
        "half_widths_px": [round(float(h_), 2) for h_ in result.half_widths * unit_px],
        "crop_size": {"w": int(w), "h": int(h)},
        "skeleton_polyline_px": [[int(x), int(y)] for x, y in skel_pts],
        "fitted_polyline_px": [[round(float(x), 2), round(float(y), 2)] for x, y in result.fitted_polyline_px],
        "canonical_polyline_px": [[round(float(x), 2), round(float(y), 2)] for x, y in result.canonical_polyline_px],
        "polyline_stroke_starts": result.polyline_stroke_starts,
        "fitted_outline_px": fitted_outline_px,
        "placement": result.placement,
    }
