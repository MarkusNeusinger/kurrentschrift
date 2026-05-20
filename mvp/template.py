"""Canonical ductus templates: schema, JSON I/O, sampling, rendering.

A canonical template is the *normative* shape for one (glyph, position, variant)
combination — handmodelled, not extracted from a scan (architektur.md §2, §3).
It carries the stroke order, control anchors, entry/exit coupling, and a
half-width profile (the Schwellzug — architektur.md §5). Per-instance fits
deform from the canonical; the deformation is captured separately.

Coordinate convention:
    baseline   y = 0       (anchor of most glyphs' start/end)
    midband    y = 1       (top of x-height region)
    ascender   y = 2       (top of l, h, ſ, ...)
    descender  y = -1      (bottom of g, p, ...)
    x          left-to-right, glyph spans roughly [0, advance].

Half-widths are in the same units as xy. A typical Schwellzug downstroke is
~0.18, an upstroke hairline ~0.05.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import CubicSpline


Position = Literal["initial", "medial", "final"]
Coupling = Literal["baseline", "midband", "ascender", "descender"]


@dataclass
class CouplingPoint:
    xy: tuple[float, float]
    tangent_deg: float
    coupling: Coupling


@dataclass
class Stroke:
    anchors: list[tuple[float, float]]
    half_widths: list[float]
    curve_type: Literal["bspline"] = "bspline"


@dataclass
class CanonicalTemplate:
    glyph: str
    position: Position
    variant: int
    advance: float
    entry: CouplingPoint
    exit: CouplingPoint
    strokes: list[Stroke] = field(default_factory=list)


def load(path: Path | str) -> CanonicalTemplate:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return _from_dict(data)


def _from_dict(data: dict) -> CanonicalTemplate:
    return CanonicalTemplate(
        glyph=data["glyph"],
        position=data["position"],
        variant=data["variant"],
        advance=float(data["advance"]),
        entry=_coupling_from_dict(data["entry"]),
        exit=_coupling_from_dict(data["exit"]),
        strokes=[
            Stroke(
                anchors=[tuple(a) for a in s["anchors"]],
                half_widths=list(s["half_widths"]),
                curve_type=s.get("curve_type", "bspline"),
            )
            for s in data["strokes"]
        ],
    )


def _coupling_from_dict(data: dict) -> CouplingPoint:
    return CouplingPoint(
        xy=tuple(data["xy"]),
        tangent_deg=float(data["tangent_deg"]),
        coupling=data["coupling"],
    )


def sample_stroke(stroke: Stroke, n: int = 200) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample the stroke into n points along a chord-length-parameterised cubic spline.

    Each anchor is paired with the same parameter t (cumulative chord length,
    normalised to [0, 1]); x(t) and y(t) are interpolated independently with
    scipy.interpolate.CubicSpline. This handles paths that double back on
    themselves (loops, self-crossings — the medial-e Kreuzungsfall) without
    smoothing the loop away, which the global B-spline in splprep tended to do.

    Returns (x, y, half_width) arrays of length n.
    """
    anchors = np.asarray(stroke.anchors, dtype=float)
    widths = np.asarray(stroke.half_widths, dtype=float)
    if len(anchors) < 2:
        return anchors[:, 0], anchors[:, 1], widths
    diffs = np.diff(anchors, axis=0)
    chord = np.hypot(diffs[:, 0], diffs[:, 1])
    t = np.concatenate([[0.0], np.cumsum(chord)])
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
    sx = cs_x(u)
    sy = cs_y(u)
    sw = np.interp(u, t, widths)
    return sx, sy, sw


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


def render(template: CanonicalTemplate, ax=None, show_guides: bool = True, show_coupling: bool = True) -> None:
    """Render the template onto a matplotlib axes (creates one if not given)."""
    if ax is None:
        _, ax = plt.subplots(figsize=(4, 5))

    if show_guides:
        for y, style, label in [
            (2.0, ":", "ascender"),
            (1.0, "--", "midband"),
            (0.0, "-", "baseline"),
            (-1.0, ":", "descender"),
        ]:
            ax.axhline(y, color="lightgray", lw=0.5, ls=style, zorder=1)
            ax.text(-0.25, y, label, fontsize=6, color="lightgray", va="center", ha="right")

    for stroke in template.strokes:
        x, y, w = sample_stroke(stroke, n=300)
        poly_x, poly_y = stroke_outline(x, y, w)
        ax.fill(poly_x, poly_y, color="black", zorder=3)

    if show_coupling:
        for cp, color, label in [(template.entry, "tab:green", "in"), (template.exit, "tab:red", "out")]:
            cx, cy = cp.xy
            ax.plot(cx, cy, "o", color=color, markersize=8, zorder=5, mfc="white", mew=1.5)
            theta = np.deg2rad(cp.tangent_deg)
            dx_arrow = 0.25 * np.cos(theta)
            dy_arrow = 0.25 * np.sin(theta)
            ax.annotate(
                "",
                xy=(cx + dx_arrow, cy + dy_arrow),
                xytext=(cx, cy),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.5),
                zorder=5,
            )
            ax.text(cx + 0.08, cy + 0.08, label, fontsize=8, color=color, zorder=5)

    ax.set_aspect("equal", "box")
    ax.set_title(f"{template.glyph}  ({template.position}, v{template.variant})", fontsize=12)
    ax.set_xlim(-0.4, template.advance + 0.4)
    ax.set_ylim(-1.3, 2.4)
