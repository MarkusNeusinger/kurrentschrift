"""Canonical ductus template — dataclasses, chord-length sampling, outline polygon.

Coordinate convention (per Loth Kurrent default of 2:1:2 — but the ratio
is *data* on the Source row, not a hardcoded constant; callers pass the
ascender/descender heights when they need guide lines):
    baseline   y = 0           anchor of most glyphs' start/end
    midband    y = 1            top of x-height region
    ascender   y = 1 + a/x       e.g. 3 for [2,1,2] (1 + 2/1)
    descender  y = -d/x          e.g. -2 for [2,1,2]
    x          left-to-right

The matplotlib `render` helper was removed in the refactor — the frontend
draws the canonical preview as SVG from the data this module produces.
"""

from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline


def sample_polyline(
    anchors: np.ndarray, half_widths: np.ndarray, n: int = 200
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample a polyline (chord-length parameterised cubic spline) at `n` points.

    Each anchor pairs with the same parameter t (cumulative chord length,
    normalised). x(t) and y(t) are interpolated independently with
    `scipy.interpolate.CubicSpline` — this handles paths that double back on
    themselves (loops, self-crossings — the medial-e case) without smoothing
    the loop away the way a global B-spline would.

    Returns (x, y, half_width) arrays of length n.
    """
    anchors = np.asarray(anchors, dtype=float)
    widths = np.asarray(half_widths, dtype=float)
    if len(anchors) < 2:
        return anchors[:, 0], anchors[:, 1], widths
    diffs = np.diff(anchors, axis=0)
    chord = np.hypot(diffs[:, 0], diffs[:, 1])
    t = np.concatenate([[0.0], np.cumsum(chord)])
    if t[-1] == 0:
        return np.tile(anchors[:1, 0], n), np.tile(anchors[:1, 1], n), np.tile(widths[:1], n)
    t = t / t[-1]
    if len(anchors) < 3:
        u = np.linspace(0.0, 1.0, n)
        sx = np.interp(u, t, anchors[:, 0])
        sy = np.interp(u, t, anchors[:, 1])
        sw = np.interp(u, t, widths)
        return sx, sy, sw
    cs_x = CubicSpline(t, anchors[:, 0], bc_type="natural")
    cs_y = CubicSpline(t, anchors[:, 1], bc_type="natural")
    u = np.linspace(0.0, 1.0, n)
    return cs_x(u), cs_y(u), np.interp(u, t, widths)


def stroke_outline(x: np.ndarray, y: np.ndarray, half_width: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Closed polygon outlining a centerline with variable half-width.

    The Schwellzug is rendered by offsetting the centerline by ± half_width
    along the local normal, then closing left-going + right-coming-back into
    one polygon. Caller fills it.
    """
    dx = np.gradient(x)
    dy = np.gradient(y)
    norm = np.hypot(dx, dy)
    norm[norm == 0] = 1.0
    nx = -dy / norm
    ny = dx / norm
    left_x = x + nx * half_width
    left_y = y + ny * half_width
    right_x = x - nx * half_width
    right_y = y - ny * half_width
    poly_x = np.concatenate([left_x, right_x[::-1]])
    poly_y = np.concatenate([left_y, right_y[::-1]])
    return poly_x, poly_y


def apply_slant(x: np.ndarray, y: np.ndarray, slant_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Shear so that vertical lines lean by `slant_deg` from upright.

    Slant 0 = upright, positive = leaning right (top moves right of bottom),
    matching Kurrent's right-leaning style. The transform is x' = x + y*tan(theta),
    where theta = 90° - slant_deg so that slant_deg=0 leaves x unchanged.
    """
    if abs(slant_deg) < 1e-6:
        return x, y
    theta = np.deg2rad(90.0 - slant_deg)
    return x + y * np.tan(theta), y


def template_guides(style_ratio: list[float]) -> dict[str, float]:
    """Baseline/midband/ascender/descender y-coords for a given style ratio.

    `style_ratio` is [ascender, x_height, descender]; for Loth's [2,1,2] this
    yields baseline=0, midband=1, ascender=3, descender=-2.
    """
    a, x, d = style_ratio
    return {"baseline": 0.0, "midband": 1.0, "ascender": 1.0 + float(a) / float(x), "descender": -float(d) / float(x)}
