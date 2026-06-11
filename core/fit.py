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
from core.template import capsule_union_rings, stroke_sample_plan


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


def _bilinear(field_map: np.ndarray, px: np.ndarray, py: np.ndarray) -> np.ndarray:
    """Sample a (H, W) field at float pixel coordinates, clamped to the crop."""
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


def _sampling_operator(template_anchors: np.ndarray, slices: list[tuple[int, int]], alloc: list[int]) -> np.ndarray:
    """(n_samples, K) linear operator mapping anchor coords to centerline samples.

    Chord-length cubic-spline sampling (`core.template.sample_with_plan`) is
    linear in the anchor coordinates once the parameterisation is frozen;
    freezing it at the canonical anchors (legitimate — the per-anchor deltas
    are bounded far below the anchor spacing) turns every objective evaluation
    into a matrix product and makes the analytic gradient exact.
    """
    k = len(template_anchors)
    n_total = int(sum(alloc))
    op = np.zeros((n_total, k))
    row = 0
    for (a, b), m in zip(slices, alloc, strict=True):
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
    return op


def _sample_widths_fixed(
    template_anchors: np.ndarray, half_widths: np.ndarray, slices: list[tuple[int, int]], alloc: list[int]
) -> np.ndarray:
    """Template half-widths at the frozen sample parameters (linear interp)."""
    parts = []
    for (a, b), m in zip(slices, alloc, strict=True):
        seg = template_anchors[a:b]
        widths = half_widths[a:b]
        u = np.linspace(0.0, 1.0, m)
        if b - a < 2:
            parts.append(np.full(m, widths[0] if len(widths) else 0.0))
            continue
        diffs = np.diff(seg, axis=0)
        chord = np.hypot(diffs[:, 0], diffs[:, 1])
        t = np.concatenate([[0.0], np.cumsum(chord)])
        if t[-1] == 0:
            parts.append(np.full(m, widths[0]))
            continue
        parts.append(np.interp(u, t / t[-1], widths))
    return np.concatenate(parts)


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
    # distances.
    slices, alloc, sample_starts = stroke_sample_plan(template_anchors, stroke_starts, n_samples)
    sampling_op = _sampling_operator(template_anchors, slices, alloc)
    sw_px = _sample_widths_fixed(template_anchors, template_half_widths, slices, alloc) * unit_px
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
        d_eff = _bilinear(dist_raw, px, py) + np.hypot(ox, oy)
        e_geo = float(np.mean(d_eff**2)) / unit_sq
        e_wid = float(np.mean((_bilinear(width_raw, px, py) - sw_px) ** 2)) / unit_sq
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
        # Accept stroke_starts either top-level (router) or nested in trace_meta
        # (a raw canonical dict straight from the pipeline).
        stroke_starts=glyph_row.get("stroke_starts") or glyph_row.get("trace_meta", {}).get("stroke_starts"),
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
