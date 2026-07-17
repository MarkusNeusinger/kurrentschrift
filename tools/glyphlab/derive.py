"""Re-derive a `GlyphCase` through the real `core` pipeline, plus stage capture.

`derive` runs the exact production derivation (`canonical_suetterlin_from_path`
for Gleichzug, `canonical_from_path` otherwise) and bundles it with the crop,
binarised mask, skeleton and the crop-local anchors/widths needed to draw an
overlay. Nothing here re-implements geometry — the numbers are what the API
would store.

`derive_stages` (Gleichzug only) additionally re-runs the internal steps
(snap → smooth → resample+corners → verticalize) so each intermediate can be
visualised. It mirrors `canonical_suetterlin_from_path`'s body and self-checks
its last stage against the production result, so any future drift is caught
loudly instead of silently lying.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from core.chart import crop_with_mask, load_chart_grayscale
from core.extract import binarize_adaptive, skeleton_and_width

from .cases import GlyphCase


@dataclass
class DeriveResult:
    """Production derivation of one case + the image data to render it."""

    case: GlyphCase
    crop: np.ndarray  # float [0,1], shape (H, W)
    mask: np.ndarray  # bool
    skel: np.ndarray  # bool
    unit_px: float
    baseline_local: float  # y in crop pixels
    midband_local: float
    anchors_px: np.ndarray  # (N, 2) crop-local pixels (== admin overlay)
    half_widths_px: np.ndarray  # (N,)
    stroke_starts: list[int]
    corner_anchors: list[int]
    canon: dict  # full production canonical dict


@dataclass
class Stage:
    """One intermediate of the Gleichzug derivation, ready to draw."""

    name: str
    strokes: list[np.ndarray]  # crop-local polylines, one per pen-stroke
    style: str  # "line" (dense) | "dots" (anchor set)
    corner_pts: list[list[float]] = field(default_factory=list)  # crop-local xy


def _crop_stack(case: GlyphCase) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    bbox = case.bbox
    chart = load_chart_grayscale(case.chart_path)
    crop = crop_with_mask(chart, bbox, fill=1.0)
    mask = binarize_adaptive(crop, fill_holes_max_area=int(bbox.get("fill_holes_max_area") or 0))
    skel, width_map = skeleton_and_width(mask)
    return crop, mask, skel, {"width_map": width_map}


def derive(case: GlyphCase, n_anchors: int | None = None) -> DeriveResult:
    """Run the production canonical derivation and bundle render data."""
    from core.pipeline import DEFAULT_N_ANCHORS, canonical_from_path  # noqa: PLC0415
    from core.suetterlin import canonical_suetterlin_from_path  # noqa: PLC0415

    n = int(n_anchors or case.bbox.get("n_anchors") or DEFAULT_N_ANCHORS)
    common = {
        "raw_path": case.raw_path,
        "bbox": case.bbox,
        "chart_path": case.chart_path,
        "glyph": case.glyph,
        "n_anchors": n,
    }
    canon = canonical_suetterlin_from_path(**common) if case.is_constant else canonical_from_path(**common)

    crop, mask, skel, _ = _crop_stack(case)
    tm = canon["trace_meta"]
    x0, y0 = case.bbox["x0"], case.bbox["y0"]
    anchors_px = np.array([[px - x0, py - y0] for px, py in tm["pixel_anchors"]], dtype=float)
    return DeriveResult(
        case=case,
        crop=crop,
        mask=mask,
        skel=skel,
        unit_px=float(tm["unit_px"]),
        baseline_local=float(case.bbox["baseline_y"] - y0),
        midband_local=float(case.bbox["midband_y"] - y0),
        anchors_px=anchors_px,
        half_widths_px=np.asarray(tm["half_widths_px"], dtype=float),
        stroke_starts=list(tm["stroke_starts"]),
        corner_anchors=list(tm.get("corner_anchors") or []),
        canon=canon,
    )


def derive_stages(case: GlyphCase, n_anchors: int | None = None) -> list[Stage]:
    """Capture snap → smooth → resample → verticalize for a Gleichzug glyph.

    Mirrors `canonical_suetterlin_from_path`; raises for non-constant styles.
    """
    if not case.is_constant:
        raise ValueError(f"stage capture is Gleichzug-only; {case.key} is {case.width_resolver!r}")
    from core.pipeline import DEFAULT_N_ANCHORS, _resample_strokes, _split_raw_strokes  # noqa: PLC0415
    from core.suetterlin import (  # noqa: PLC0415
        _smooth_snapped_strokes,
        _snap_strokes_to_skeleton,
        _verticalize_downstrokes,
    )

    crop, mask, skel, aux = _crop_stack(case)
    width_map = aux["width_map"]
    x0, y0 = case.bbox["x0"], case.bbox["y0"]
    baseline_y, midband_y = int(case.bbox["baseline_y"]), int(case.bbox["midband_y"])
    unit_px = float(baseline_y - midband_y)
    n = int(n_anchors or case.bbox.get("n_anchors") or DEFAULT_N_ANCHORS)

    strokes_local = [
        np.array([(p["x"] - x0, p["y"] - y0) for p in s], dtype=float) for s in _split_raw_strokes(case.raw_path)
    ]
    snapped, _ = _snap_strokes_to_skeleton(strokes_local, skel, width_map, mask)
    smoothed = _smooth_snapped_strokes(snapped, unit_px)
    resampled, starts, corners, _ = _resample_strokes(smoothed, n, unit_px)
    final = _verticalize_downstrokes(resampled, starts, unit_px, corners)

    def split(anchors: np.ndarray) -> list[np.ndarray]:
        bounds = [*starts, len(anchors)]
        return [anchors[a:b] for a, b in zip(bounds[:-1], bounds[1:], strict=True)]

    corner_pts = [list(final[c]) for c in corners]
    stages = [
        Stage("1 snapped", snapped, "line"),
        Stage("2 smoothed", smoothed, "line"),
        Stage("3 resampled", split(resampled), "dots", [list(resampled[c]) for c in corners]),
        Stage("4 verticalized", split(final), "dots", corner_pts),
    ]

    # Honesty check: the captured final must match the production anchors — warn
    # on a shape mismatch too, else the guard silently no-ops when it matters most.
    prod = derive(case, n_anchors=n).anchors_px
    if prod.shape != final.shape:
        print(
            f"  [glyphlab] WARN: stage capture shape {final.shape} != production {prod.shape} — derive_stages out of sync"
        )
    elif not np.allclose(prod, final, atol=0.05):
        max_d = float(np.max(np.hypot(*(prod - final).T)))
        print(f"  [glyphlab] WARN: stage capture drifted from production ({max_d:.2f}px) — keep derive_stages in sync")
    return stages
