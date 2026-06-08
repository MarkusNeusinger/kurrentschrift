"""Fit a canonical ductus template to a glyph instance (M4).

Given a canonical template (normalised anchors + half-widths) and an instance
crop (skeleton + distance-transform half-width map), deform the template's
control points so the template centerline lies near the instance skeleton and
its half-width profile matches the measured distance transform — regularised
against excessive deformation so the ductus topology (loop direction, crossing
order) is preserved.

The optimiser is deliberately simple (`scipy.optimize.minimize` over the
control-point displacements plus a global placement offset, nearest-skeleton
distance via `scipy.spatial.cKDTree`). Per `docs/concepts/mvp-roadmap.md` M4:
the MVP validates the *principle* — that a regularised template fit recovers an
instance without breaking topology — not the optimiser.

Coordinate spaces
-----------------
* Template space: baseline ``y = 0``, midband ``y = 1``, ``x`` left-to-right,
  origin at the template's first anchor (same convention as `core.template`).
* Crop-local pixel space: the instance crop, row-major pixels. The mapping is
  ``px = x_origin_px + x_norm * unit_px`` and ``py = baseline_y_px - y_norm *
  unit_px`` where ``unit_px`` is the x-height in pixels.

All optimisation runs in crop-local pixels (that is where the skeleton lives);
residuals are normalised by ``unit_px`` so geometry, width and regularisation
terms share one scale and the weights are dimensionless.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree

from core.chart import crop_with_mask, load_chart_grayscale
from core.extract import binarize_adaptive, skeleton_and_width
from core.template import sample_with_plan, stroke_sample_plan


DEFAULT_LAMBDA_REG = 1.0
DEFAULT_WIDTH_WEIGHT = 0.15
DEFAULT_N_SAMPLES = 120
DEFAULT_MAX_ITER = 200
# Cap per-anchor displacement (in template units) so the fit cannot fold the
# ductus back on itself — a loose topology guard alongside the Tikhonov term.
MAX_ANCHOR_DELTA = 0.75


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


def _nearest_ink_widths(
    points_px: np.ndarray, width_map: np.ndarray, ink_tree: cKDTree, ink_pts: np.ndarray
) -> np.ndarray:
    """Half-width at each query point, read from the nearest ink pixel.

    Sampling at the nearest ink pixel (rather than the raw pixel under the
    point) avoids a zero whenever the fitted centerline drifts a pixel off the
    stroke — the measured width should be the stroke's, not the background's.
    """
    if len(ink_pts) == 0:
        return np.zeros(len(points_px))
    _, idx = ink_tree.query(points_px)
    cols = ink_pts[idx, 0].astype(int)
    rows = ink_pts[idx, 1].astype(int)
    return width_map[rows, cols].astype(float)


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
    max_iter: int = DEFAULT_MAX_ITER,
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

    Returns
    -------
    FitResult with the fitted instance in template coords plus crop-local
    overlay polylines and a `fit_meta` diagnostic (RMSEs, iterations, success).
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
    skel_tree = cKDTree(skel_pts)

    ink_rows, ink_cols = np.where(width_map > 0)
    ink_pts = np.column_stack([ink_cols.astype(float), ink_rows.astype(float)])
    ink_tree = cKDTree(ink_pts) if len(ink_pts) else skel_tree

    # Auto-place the template origin so its centroid sits on the skeleton's.
    x_norm0 = template_anchors[:, 0]
    if x_origin_px is None:
        templ_centroid_px = float(np.mean(x_norm0)) * unit_px
        x_origin_px = float(skel_pts[:, 0].mean()) - templ_centroid_px

    # Fixed sampling plan (anchor count is constant through the fit): each pen
    # stroke is sampled on its own, so no sample point lands on a pen-lift bridge
    # and the geometry residual is never inflated by phantom-gap distances.
    slices, alloc, sample_starts = stroke_sample_plan(template_anchors, stroke_starts, n_samples)

    def to_pixels(anchors_norm: np.ndarray, tx: float, ty: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        sx_n, sy_n, sw_n = sample_with_plan(anchors_norm, template_half_widths, slices, alloc)
        px = (x_origin_px + tx) + sx_n * unit_px
        py = (baseline_y_px + ty) - sy_n * unit_px
        return px, py, sw_n

    def energies(params: np.ndarray) -> tuple[float, float, float]:
        tx, ty = params[0], params[1]
        deltas = params[2:].reshape(k, 2)
        anchors = template_anchors + deltas
        px, py, sw_n = to_pixels(anchors, tx, ty)
        pts = np.column_stack([px, py])
        dist, _ = skel_tree.query(pts)
        e_geo = float(np.mean((dist / unit_px) ** 2))
        meas_hw = _nearest_ink_widths(pts, width_map, ink_tree, ink_pts)
        e_wid = float(np.mean(((meas_hw - sw_n * unit_px) / unit_px) ** 2))
        e_reg = float(np.mean(np.sum(deltas**2, axis=1)))
        return e_geo, e_wid, e_reg

    def objective(params: np.ndarray) -> float:
        e_geo, e_wid, e_reg = energies(params)
        return e_geo + width_weight * e_wid + lambda_reg * e_reg

    n_params = 2 + 2 * k
    x0 = np.zeros(n_params)
    # Bounds: generous translation, capped per-anchor displacement.
    h, w = skel.shape
    bounds = [(-float(w), float(w)), (-float(h), float(h))]
    bounds += [(-MAX_ANCHOR_DELTA, MAX_ANCHOR_DELTA)] * (2 * k)

    e_geo0, _, _ = energies(x0)
    res = minimize(objective, x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": max_iter})

    tx, ty = res.x[0], res.x[1]
    deltas = res.x[2:].reshape(k, 2)
    fitted_anchors = template_anchors + deltas

    # Final overlay polylines (crop-local pixels).
    px, py, _ = to_pixels(fitted_anchors, tx, ty)
    fitted_polyline_px = np.column_stack([px, py])
    cpx, cpy, _ = to_pixels(template_anchors, 0.0, 0.0)
    canonical_polyline_px = np.column_stack([cpx, cpy])

    # Measured half-widths along the fit, sampled at the K fitted anchors.
    anchor_px = np.column_stack(
        [(x_origin_px + tx) + fitted_anchors[:, 0] * unit_px, (baseline_y_px + ty) - fitted_anchors[:, 1] * unit_px]
    )
    fitted_hw_px = _nearest_ink_widths(anchor_px, width_map, ink_tree, ink_pts)
    fitted_half_widths = fitted_hw_px / unit_px

    e_geo, e_wid, e_reg = energies(res.x)
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

    fit_meta = {
        "success": bool(res.success),
        "message": str(res.message),
        "iterations": int(res.nit),
        "geo_rmse_px": round(float(np.sqrt(e_geo) * unit_px), 3),
        "geo_rmse_px_initial": round(float(np.sqrt(e_geo0) * unit_px), 3),
        "width_rmse_px": round(float(np.sqrt(e_wid) * unit_px), 3),
        "reg_energy": round(e_reg, 6),
        "max_anchor_delta": round(float(np.max(np.hypot(deltas[:, 0], deltas[:, 1]))), 4),
        "lambda_reg": lambda_reg,
        "width_weight": width_weight,
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
        placement={
            "x_origin_px": float(x_origin_px + tx),
            "baseline_y_px": float(baseline_y_px + ty),
            "unit_px": float(unit_px),
        },
        polyline_stroke_starts=sample_starts,
        fit_meta=fit_meta,
    )


# ------------------------------------------------------------- high-level API


def fit_glyph_to_crop(
    glyph_row: dict,
    bbox: dict,
    chart_path: str,
    *,
    lambda_reg: float = DEFAULT_LAMBDA_REG,
    width_weight: float = DEFAULT_WIDTH_WEIGHT,
    n_samples: int = DEFAULT_N_SAMPLES,
    max_iter: int = DEFAULT_MAX_ITER,
) -> dict:
    """Fit a stored canonical (`glyph_row`) to the instance crop of `bbox`.

    Mirrors `core.pipeline.diagnostic_for_glyph`: loads the chart, crops with
    the eraser mask, binarises, extracts skeleton + distance transform, then fits.
    Returns a JSON-ready overlay dict — a filled library entry plus crop-local
    polylines for the three-way visual check (crop · canonical grey · fit red)
    and the skeleton it was fitted to.
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
        n_samples=n_samples,
        max_iter=max_iter,
    )

    # Carry the canonical's coupling labels onto the fitted entry/exit.
    if glyph_row.get("entry", {}).get("coupling"):
        result.entry["coupling"] = glyph_row["entry"]["coupling"]
    if glyph_row.get("exit_pt", {}).get("coupling"):
        result.exit_pt["coupling"] = glyph_row["exit_pt"]["coupling"]

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
        "placement": result.placement,
    }
