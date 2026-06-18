"""Image-space quality metrics: rendered template silhouette vs the crop's ink.

The fit residuals (geo/width/coverage in `core.fit`) measure the template
against the *skeleton* and the *EDT field* — both derived signals. What the
user actually sees is the filled silhouette next to the chart crop, and until
now nothing compared those two images. This module closes that loop: it
rasterises the capsule-union silhouette exactly as the frontend renders it
(per-stroke rings, evenodd fill) and scores it against the binarized crop —
region overlap (IoU/Dice), boundary agreement (symmetric chamfer), centerline
adherence (EDT-to-skeleton RMSE) and width-profile waviness relative to the
ink's own profile.

The aggregate `score`/`loss` is the headline number for the glyph bench
(`tools/glyphbench`) and the keep/discard criterion of the experiment loop.
Everything here is deterministic — no RNG, no time — so two runs on the same
inputs produce identical dicts.

Sampling happens at QUALITY_N_SAMPLES = 240, matching the diagnostic/animation
render (`core.pipeline.diagnostic_for_glyph`), not the fit's internal 120:
the metric must measure what the user sees.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt, gaussian_filter1d
from scipy.spatial import cKDTree
from skimage.draw import polygon2mask

from core.chart import crop_with_mask, load_chart_grayscale
from core.extract import binarize_adaptive, half_widths_on_medial_axis, skeleton_and_width

# Bilinear field sampling shared with the fit — the metric reads the same EDT
# interpolant the optimiser descends, so "converged" and "high score" agree.
from core.fit import bilinear
from core.template import build_sample_plan, capsule_union_rings, sample_with_sample_plan


# Sample count for silhouette + centerline — what the diagnostic/animation
# renders (the fit's internal 120 is an optimisation detail, not the visual).
QUALITY_N_SAMPLES = 240

# Aggregate score weights (sum to 1.0). Dice carries the headline because it
# is the closest proxy for "looks like the crop"; the exponential terms decay
# with the same tolerances the fit's convergence verdict uses
# (CONVERGED_GEO_RMSE_UNITS = 0.08), so a converged fit also scores well.
SCORE_DICE_WEIGHT = 0.45
SCORE_CHAMFER_WEIGHT = 0.25
SCORE_GEO_WEIGHT = 0.20
SCORE_WAVINESS_WEIGHT = 0.10
CHAMFER_DECAY_UNITS = 0.05
GEO_DECAY_UNITS = 0.08

# Width-waviness reference: the ink's own profile along the rendered path,
# Gaussian-smoothed (in samples) so EDT quantisation noise does not count as
# "real" waviness of the ink. Epsilon guards hairline glyphs whose profiles
# are nearly flat on both sides.
INK_WIDTH_SMOOTH_SIGMA = 3.0
WAVINESS_EPS_PX = 0.01

# Geometry simplification of the rasterised silhouette, in the coordinate
# space of the anchors (crop pixels here): far below a pixel, so the metric
# matches the unsimplified union while keeping shapely output small.
RASTER_SIMPLIFY_PX = 0.05


def rasterize_silhouette(
    stroke_rings: Sequence[Sequence[Sequence[Sequence[float]]]], shape: tuple[int, int]
) -> np.ndarray:
    """Boolean mask of per-stroke ring lists (exterior + holes) at `shape`.

    `stroke_rings` is the `multi_stroke_silhouettes` format: one list of rings
    per pen-stroke, each ring a list of `[x, y]` points. XOR of per-ring
    containment is exactly the evenodd fill rule the frontend uses, so loop
    counters (the e-eye) stay open; strokes are OR-ed together like stacked
    `<path>` elements.
    """
    out = np.zeros(shape, dtype=bool)
    for rings in stroke_rings:
        stroke_mask = np.zeros(shape, dtype=bool)
        for ring in rings:
            if len(ring) < 3:
                continue
            poly_rc = np.asarray([[p[1], p[0]] for p in ring], dtype=float)  # (row, col)
            stroke_mask ^= polygon2mask(shape, poly_rc)
        out |= stroke_mask
    return out


def _sample_and_rings(
    anchors_px: np.ndarray,
    half_widths_px: np.ndarray,
    stroke_starts: Sequence[int] | None,
    n: int,
    corner_anchors: Sequence[int] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[int], list[int], list[list[list[list[float]]]]]:
    """Shared sampling: centerline samples + per-stroke capsule-union rings.

    One `SamplePlan` (corner-aware, like the diagnostic render) drives both the
    rasterised silhouette and the centerline/width measurements, so every
    metric scores the same geometry. Also returns `plan.corner_sample_idx` (the
    surviving sample of each within-stroke corner knot) so a caller can exclude
    intentional reversals from a smoothness measurement.
    """
    plan = build_sample_plan(anchors_px, stroke_starts, corner_anchors, n)
    sx, sy, sw = sample_with_sample_plan(anchors_px, half_widths_px, plan)
    bounds = [*plan.sample_starts, len(sx)]
    rings = [
        capsule_union_rings(sx[a:b], sy[a:b], sw[a:b], simplify_tol=RASTER_SIMPLIFY_PX, decimals=2)
        for a, b in zip(bounds[:-1], bounds[1:], strict=True)
    ]
    return sx, sy, sw, plan.sample_starts, plan.corner_sample_idx, rings


def silhouette_mask(
    anchors_px: np.ndarray,
    half_widths_px: np.ndarray,
    stroke_starts: Sequence[int] | None,
    shape: tuple[int, int],
    n: int = QUALITY_N_SAMPLES,
    corner_anchors: Sequence[int] | None = None,
) -> np.ndarray:
    """Rasterised silhouette of a pixel-space template — the metric's pred mask.

    Public so overlay tooling can render exactly what the metric scored.
    """
    anchors_px = np.asarray(anchors_px, dtype=float)
    half_widths_px = np.asarray(half_widths_px, dtype=float)
    *_, rings = _sample_and_rings(anchors_px, half_widths_px, stroke_starts, n, corner_anchors)
    return rasterize_silhouette(rings, shape)


def mask_boundary(mask: np.ndarray) -> np.ndarray:
    """One-pixel boundary of a boolean mask (border pixels count as boundary).

    Public: overlay tooling draws the same edge the chamfer scores.
    """
    if not mask.any():
        return np.zeros_like(mask)
    return mask & ~binary_erosion(mask, border_value=False)


def crop_local_anchors(pixel_anchors: Sequence[Sequence[float]], bbox: dict) -> np.ndarray:
    """Chart-global pixel anchors (`trace_meta.pixel_anchors`) → crop-local px."""
    return np.asarray(pixel_anchors, dtype=float) - np.array([bbox["x0"], bbox["y0"]], dtype=float)


def chamfer_boundary_stats(pred_mask: np.ndarray, ink_mask: np.ndarray, *, dead_band_px: float = 0.0) -> dict:
    """Symmetric boundary chamfer (px): how far the rendered edge sits from the ink edge.

    Boundary pixels of each mask are measured against the EDT of the other
    side's boundary; reported as the symmetric mean and the worse of the two
    95th percentiles (a localised miss — one corner cut off — must not vanish
    in the mean). An empty side scores the crop diagonal: the worst honest
    answer, never a flattering one.

    `dead_band_px` (default 0.0, so existing callers are byte-identical) is a
    pixelation tolerance: each per-pixel boundary distance is reduced by this
    much (floored at 0) *before* averaging, so disagreement within the scan's
    own ~1px quantisation costs nothing while a real, several-pixel miss still
    does. Used by the Sütterlin metric, whose credo is "indistinguishable from
    a pen", not "pixel-identical to a jagged scan".
    """
    h, w = pred_mask.shape
    worst = float(np.hypot(h, w))
    b_pred = mask_boundary(pred_mask)
    b_ink = mask_boundary(ink_mask)
    if not b_pred.any() or not b_ink.any():
        return {"chamfer_mean_px": round(worst, 3), "chamfer_p95_px": round(worst, 3)}
    d_pred_to_ink = distance_transform_edt(~b_ink)[b_pred]
    d_ink_to_pred = distance_transform_edt(~b_pred)[b_ink]
    if dead_band_px > 0.0:
        d_pred_to_ink = np.maximum(0.0, d_pred_to_ink - dead_band_px)
        d_ink_to_pred = np.maximum(0.0, d_ink_to_pred - dead_band_px)
    return {
        "chamfer_mean_px": round(float((d_pred_to_ink.mean() + d_ink_to_pred.mean()) / 2.0), 3),
        "chamfer_p95_px": round(float(max(np.percentile(d_pred_to_ink, 95), np.percentile(d_ink_to_pred, 95))), 3),
    }


def width_profile_tv(widths: np.ndarray, sample_starts: Sequence[int]) -> float:
    """Mean absolute width change per sample step, never across a pen lift.

    Total variation normalised by segment count — a per-step "wiggle rate" in
    the widths' own unit, comparable across glyphs with different sample
    counts and stroke splits.
    """
    widths = np.asarray(widths, dtype=float)
    bounds = [*sample_starts, len(widths)]
    total, n_seg = 0.0, 0
    for a, b in zip(bounds[:-1], bounds[1:], strict=True):
        if b - a >= 2:
            total += float(np.abs(np.diff(widths[a:b])).sum())
            n_seg += b - a - 1
    return total / n_seg if n_seg else 0.0


def _ink_width_reference(
    samples: np.ndarray,
    sample_starts: Sequence[int],
    anchors_px: np.ndarray,
    crossing_anchors: Sequence[int] | None,
    skel: np.ndarray,
    mask: np.ndarray,
    width_map: np.ndarray,
    unit_px: float,
) -> np.ndarray:
    """The ink's own half-width profile along the rendered path (smoothed, px).

    Crossing-contaminated stretches (the EDT reads the union blob of both
    passes) are interpolated from clean neighbours before smoothing — same
    rationale as `core.pipeline._resolve_crossing_widths`, mapped from anchor
    flags to samples via nearest anchor.
    """
    ink_w = half_widths_on_medial_axis(samples, skel, mask, width_map, snap_cap_px=max(3.0, 0.25 * unit_px))
    bounds = [*sample_starts, len(samples)]
    if crossing_anchors:
        _, nearest = cKDTree(anchors_px).query(samples)
        flagged = np.isin(nearest, np.asarray(list(crossing_anchors), dtype=int))
        for a, b in zip(bounds[:-1], bounds[1:], strict=True):
            seg = flagged[a:b]
            if seg.any() and not seg.all():
                pos = np.arange(b - a)
                ink_w[a:b][seg] = np.interp(pos[seg], pos[~seg], ink_w[a:b][~seg])
    for a, b in zip(bounds[:-1], bounds[1:], strict=True):
        if b - a >= 3:
            ink_w[a:b] = gaussian_filter1d(ink_w[a:b], INK_WIDTH_SMOOTH_SIGMA, mode="nearest")
    return ink_w


def template_quality_metrics(
    anchors_px: np.ndarray,
    half_widths_px: np.ndarray,
    stroke_starts: Sequence[int] | None,
    mask: np.ndarray,
    skel: np.ndarray,
    width_map: np.ndarray,
    *,
    unit_px: float,
    crossing_anchors: Sequence[int] | None = None,
    corner_anchors: Sequence[int] | None = None,
    n: int = QUALITY_N_SAMPLES,
) -> dict:
    """Score a template (crop-local pixel anchors + half-widths) against its crop.

    Renders the silhouette exactly like the diagnostic (per-stroke capsule
    union at `n` samples), rasterises it, and compares against the binarized
    ink `mask` / `skel` / `width_map` of the same crop. Returns a flat dict of
    rounded metrics plus the aggregate `score` (0–100, higher better) and
    `loss` (lower better) — the bench headline.
    """
    anchors_px = np.asarray(anchors_px, dtype=float)
    half_widths_px = np.asarray(half_widths_px, dtype=float)
    if len(anchors_px) < 2:
        raise ValueError("need at least 2 anchors to render a silhouette")
    if unit_px <= 0:
        raise ValueError(f"unit_px must be positive, got {unit_px}")

    h, w = mask.shape
    worst_px = float(np.hypot(h, w))

    sx, sy, sw, sample_starts, _corner_sample_idx, stroke_rings = _sample_and_rings(
        anchors_px, half_widths_px, stroke_starts, n, corner_anchors
    )
    pred_mask = rasterize_silhouette(stroke_rings, (h, w))

    # Region overlap.
    intersection = int(np.logical_and(pred_mask, mask).sum())
    union = int(np.logical_or(pred_mask, mask).sum())
    area_sum = int(pred_mask.sum()) + int(mask.sum())
    iou = intersection / union if union else 1.0
    dice = 2.0 * intersection / area_sum if area_sum else 1.0

    # Boundary agreement.
    chamfer = chamfer_boundary_stats(pred_mask, mask)

    # Centerline adherence — "follows the crop while writing".
    if skel.any():
        d_skel = distance_transform_edt(~skel)
        geo_rmse_px = float(np.sqrt(np.mean(bilinear(d_skel, sx, sy) ** 2)))
    else:
        geo_rmse_px = worst_px

    # Width waviness vs the ink's own profile.
    samples = np.column_stack([sx, sy])
    ink_w = _ink_width_reference(samples, sample_starts, anchors_px, crossing_anchors, skel, mask, width_map, unit_px)
    tv_rendered = width_profile_tv(sw, sample_starts)
    tv_ink = width_profile_tv(ink_w, sample_starts)
    waviness_ratio = (tv_rendered + WAVINESS_EPS_PX) / (tv_ink + WAVINESS_EPS_PX)

    score = 100.0 * (
        SCORE_DICE_WEIGHT * dice
        + SCORE_CHAMFER_WEIGHT * float(np.exp(-chamfer["chamfer_mean_px"] / (CHAMFER_DECAY_UNITS * unit_px)))
        + SCORE_GEO_WEIGHT * float(np.exp(-geo_rmse_px / (GEO_DECAY_UNITS * unit_px)))
        + SCORE_WAVINESS_WEIGHT * float(np.exp(-max(0.0, waviness_ratio - 1.0)))
    )

    return {
        "iou": round(iou, 4),
        "dice": round(dice, 4),
        **chamfer,
        "geo_rmse_px": round(geo_rmse_px, 3),
        "width_tv_rendered_px": round(tv_rendered, 4),
        "width_tv_ink_px": round(tv_ink, 4),
        "waviness_ratio": round(waviness_ratio, 3),
        "pred_area_px": int(pred_mask.sum()),
        "ink_area_px": int(mask.sum()),
        "score": round(score, 2),
        "loss": round(1.0 - score / 100.0, 6),
        "n_samples": int(n),
    }


def quality_for_glyph(glyph_row: dict, bbox: dict, chart_path: str) -> dict:
    """Score a stored template against its own crop (chart + bbox), end to end.

    Mirrors `core.fit.fit_glyph_to_crop`'s loading: chart → crop with eraser
    mask → binarize → skeleton/EDT, then scores the template's pixel-space
    trace (`trace_meta.pixel_anchors` / `half_widths_px`). The glyph bench
    scores against *frozen* reference masks instead — this helper is the
    live-DB convenience for the API/diagnostics path.
    """
    for required in ("baseline_y", "midband_y", "y0", "y1", "x0", "x1"):
        if bbox.get(required) is None:
            raise ValueError(f"bbox missing required field {required!r}")
    trace_meta = glyph_row.get("trace_meta") or {}
    pixel_anchors = trace_meta.get("pixel_anchors")
    half_widths_px = trace_meta.get("half_widths_px")
    if not pixel_anchors or not half_widths_px:
        raise ValueError("template lacks trace_meta.pixel_anchors / half_widths_px")

    chart_gray = load_chart_grayscale(chart_path)
    crop = crop_with_mask(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop, fill_holes_max_area=int(bbox.get("fill_holes_max_area") or 0))
    skel, width_map = skeleton_and_width(mask)

    anchors_px = crop_local_anchors(pixel_anchors, bbox)
    unit_px = float(trace_meta.get("unit_px") or (int(bbox["baseline_y"]) - int(bbox["midband_y"])))

    return template_quality_metrics(
        anchors_px,
        np.asarray(half_widths_px, dtype=float),
        trace_meta.get("stroke_starts"),
        mask,
        skel,
        width_map,
        unit_px=unit_px,
        crossing_anchors=trace_meta.get("crossing_anchors"),
        corner_anchors=trace_meta.get("corner_anchors"),
    )
