"""matplotlib overlays of a derivation over its crop — the picture I keep redrawing.

A `Panel` describes one thing to draw: a derivation, optionally with an
overridden anchor set (a stage, or an A/B variant). Several layers are toggleable
(`skeleton`, `silhouette`, `scores`); the rest — faint crop, baseline/midband
guides, centerline (per `style`), corner rings — are always drawn. `figure` tiles
panels into a labelled grid; `overlay` is the
one-panel shortcut; `stage_panels` turns captured stages into panels; `save`
writes a PNG to the output dir (`$GLYPHLAB_OUT`, else the project `temp/`).

matplotlib is a dev/test-only dependency (the `viz` extra) — it is never
imported by `core`/`api`, so it stays out of the production image.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib


matplotlib.use("Agg")  # headless: render to file, never a window

import matplotlib.pyplot as plt  # noqa: E402 — after use("Agg")
import numpy as np  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402

from core.template import build_sample_plan, capsule_union_rings, sample_with_sample_plan  # noqa: E402

from .cases import REPO_ROOT  # noqa: E402
from .derive import DeriveResult, Stage  # noqa: E402


GREEN = "#1f9e1f"
RED = "#d22828"
_SKEL = "#5aa0ff"
_BASELINE = "#e09696"
_MIDBAND = "#84cf84"
_CORNER = "#000000"


def _default_out_dir() -> Path:
    env = os.environ.get("GLYPHLAB_OUT")
    return Path(env) if env else REPO_ROOT / "temp"


@dataclass
class Panel:
    """One overlay to draw — a derivation plus what to show on top of it."""

    result: DeriveResult
    title: str = ""
    anchors: np.ndarray | None = None  # override the production anchors (a stage / variant)
    half_widths: np.ndarray | None = None
    stroke_starts: list[int] | None = None
    corner_anchors: list[int] | None = None  # indices into the anchor set
    corner_pts: list | None = None  # explicit crop-local xy (for stages, where there are no indices)
    style: str = "spline"  # "spline" | "dots" | "line"
    silhouette: bool = True
    skeleton: bool = True
    scores: bool = True  # draw the per-component quality breakdown (where the points went)
    color: str = GREEN
    annotate: list[tuple[float, float, str]] = field(default_factory=list)  # (x, y, text) callouts


def panel(result: DeriveResult, **kwargs) -> Panel:
    """Convenience builder for a `Panel` (keyword args mirror the dataclass)."""
    return Panel(result=result, **kwargs)


# Component → short label, in the bench's stdout order. The caption sorts by
# penalty so the biggest deduction is on top — "where did this glyph lose points".
_COMPONENT_LABELS = [
    ("smoothness", "smooth"),
    ("verticality", "vert"),
    ("corner", "corner"),
    ("collinearity", "cross"),
    ("retrace", "retr"),
    ("coverage", "cover"),
]
_SCORE_HI = 0.15  # mark a component at/above this penalty as a notable deduction


def _score_caption(canon: dict | None) -> str | None:
    """Multi-line quality breakdown for a panel, or None if the glyph has no score.

    Sütterlin glyphs carry the naturalness `components` (penalty per category,
    lower = better); the lines are sorted worst-first and the notable ones marked
    so it reads as "here is where the points went". Kurrent glyphs fall back to
    the Schwellzug headline numbers.
    """
    quality = (canon or {}).get("trace_meta", {}).get("quality")
    if not quality:
        return None
    lines = [f"loss   {quality['loss']:.3f}"]
    components = quality.get("components")
    if components:
        rows = sorted(
            ((label, components[key]) for key, label in _COMPONENT_LABELS if key in components), key=lambda kv: -kv[1]
        )
        lines += [f"{label:<6} {val:.3f}{'  <<' if val >= _SCORE_HI else ''}" for label, val in rows]
    else:  # Kurrent / Schwellzug metric
        lines += [f"{k[:6]:<6} {quality[k]:.3f}" for k in ("iou", "chamfer_mean_px", "geo_rmse_px") if k in quality]
    return "\n".join(lines)


def _polylines(anchors: np.ndarray, stroke_starts: list[int]) -> list[np.ndarray]:
    bounds = [*stroke_starts, len(anchors)]
    return [anchors[a:b] for a, b in zip(bounds[:-1], bounds[1:], strict=True)]


def _silhouette_patch(rings: list, color: str):
    """A single PathPatch from capsule-union rings (shapely winding → even-odd holes)."""
    verts: list[list[float]] = []
    codes: list[int] = []
    for ring in rings:
        if len(ring) < 3:
            continue
        verts.extend(ring)
        codes.append(MplPath.MOVETO)
        codes.extend([MplPath.LINETO] * (len(ring) - 1))
        codes[-(len(ring))] = MplPath.MOVETO  # ensure first of this ring is MOVETO
    if not verts:
        return None
    path = MplPath(np.asarray(verts), codes)
    return PathPatch(path, facecolor=color, edgecolor="none", alpha=0.22, zorder=2)


def _draw(ax, p: Panel) -> None:
    res = p.result
    A = res.anchors_px if p.anchors is None else np.asarray(p.anchors, dtype=float)
    SS = res.stroke_starts if p.stroke_starts is None else p.stroke_starts
    CA = res.corner_anchors if p.corner_anchors is None else p.corner_anchors
    if p.half_widths is not None:
        HW = np.asarray(p.half_widths, dtype=float)
    elif p.anchors is None:
        HW = res.half_widths_px  # production anchors → production widths
    else:
        HW = None  # an overridden anchor set has no matching width profile

    H, W = res.crop.shape
    # The score caption goes in a blank right-hand margin so it NEVER covers the
    # glyph; the crop image still occupies only [0, W].
    caption = _score_caption(res.canon) if p.scores else None
    margin = 0.5 * W if caption else 0.0
    faint = np.clip(res.crop, 0, 1) * 0.6 + 0.4  # lighten the ink so overlays read on top
    ax.imshow(faint, cmap="gray", vmin=0, vmax=1, extent=(0, W, H, 0), interpolation="nearest", zorder=0)
    ax.set_xlim(0, W + margin)
    ax.set_ylim(H, 0)
    ax.set_aspect("equal")
    ax.axis("off")

    if p.skeleton:
        ys, xs = np.where(res.skel)
        ax.scatter(xs, ys, s=1.2, c=_SKEL, linewidths=0, zorder=1)
    guide_xmax = W / (W + margin)  # keep the baseline/midband guides over the glyph, not the caption margin
    ax.axhline(res.baseline_local, xmax=guide_xmax, color=_BASELINE, lw=0.8, zorder=1)
    ax.axhline(res.midband_local, xmax=guide_xmax, color=_MIDBAND, lw=0.8, zorder=1)

    have_widths = HW is not None and len(HW) == len(A)
    if p.silhouette and have_widths and len(A) >= 2:
        plan = build_sample_plan(A, SS, CA, 240)
        sx, sy, sw = sample_with_sample_plan(A, HW, plan)
        bounds = [*plan.sample_starts, len(sx)]
        for a, b in zip(bounds[:-1], bounds[1:], strict=True):
            if b - a < 2:
                continue
            patch = _silhouette_patch(
                capsule_union_rings(sx[a:b], sy[a:b], sw[a:b], simplify_tol=0.0, decimals=2), p.color
            )
            if patch is not None:
                ax.add_patch(patch)

    if p.style == "spline" and have_widths and len(A) >= 2:
        plan = build_sample_plan(A, SS, CA, 240)
        sx, sy, _ = sample_with_sample_plan(A, HW, plan)
        bounds = [*plan.sample_starts, len(sx)]
        for a, b in zip(bounds[:-1], bounds[1:], strict=True):
            if b - a >= 2:
                ax.plot(sx[a:b], sy[a:b], color=p.color, lw=2.2, solid_capstyle="round", zorder=3)
    elif p.style == "line":
        for poly in _polylines(A, SS):
            if len(poly) >= 2:
                ax.plot(poly[:, 0], poly[:, 1], color=p.color, lw=1.4, solid_capstyle="round", zorder=3)
    else:  # dots
        for poly in _polylines(A, SS):
            if len(poly) >= 2:
                ax.plot(poly[:, 0], poly[:, 1], color=p.color, lw=0.7, alpha=0.6, zorder=3)
        ax.scatter(A[:, 0], A[:, 1], s=12, c=p.color, linewidths=0, zorder=4)

    corner_xy = [list(A[c]) for c in CA if 0 <= c < len(A)] if p.corner_pts is None else list(p.corner_pts)
    if corner_xy:
        cx, cy = np.asarray(corner_xy).T
        ax.scatter(cx, cy, s=85, facecolors="none", edgecolors=_CORNER, linewidths=1.3, zorder=5)

    for x, y, text in p.annotate:
        ax.annotate(
            text,
            xy=(x, y),
            xytext=(x + 0.32 * W, y),
            fontsize=7,
            color=_CORNER,
            va="center",
            arrowprops={"arrowstyle": "->", "color": _CORNER, "lw": 1.0},
        )
    if caption:
        ax.text(
            W + 0.04 * W, 0.0, caption, va="top", ha="left", fontsize=6.5, family="monospace", color=_CORNER, zorder=6
        )
    if p.title:
        ax.set_title(p.title, fontsize=8.5)


def figure(panels: list[Panel], *, cols: int | None = None, panel_size: float = 3.2, dpi: int = 160):
    """Tile `panels` into a labelled grid figure (row-major). Returns the Figure.

    Defaults are sized so each panel is ~510px: a 3-wide montage lands near
    1550px wide, which survives downscaling readable (a wide single row would
    shrink each panel to an illegible strip). For close inspection render fewer
    keys per call or raise `dpi`.
    """
    if not panels:
        raise ValueError("no panels")
    n = len(panels)
    cols = cols or n
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * panel_size, rows * panel_size), dpi=dpi, squeeze=False)
    for i, ax in enumerate(axes.flat):
        if i < n:
            _draw(ax, panels[i])
        else:
            ax.axis("off")
    fig.tight_layout(pad=0.4)
    return fig


def overlay(result: DeriveResult, **kwargs):
    """One-panel figure shortcut: `figure([panel(result, **kwargs)])`."""
    return figure([panel(result, **kwargs)])


def stage_panels(result: DeriveResult, stages: list[Stage]) -> list[Panel]:
    """Turn captured derivation stages into drawable panels (one per stage)."""
    out: list[Panel] = []
    for st in stages:
        flat = np.concatenate(st.strokes) if st.strokes else np.zeros((0, 2))
        starts, cursor = [], 0
        for s in st.strokes:
            starts.append(cursor)
            cursor += len(s)
        out.append(
            Panel(
                result=result,
                title=f"{result.case.key} · {st.name}",
                anchors=flat,
                stroke_starts=starts,
                corner_anchors=[],
                corner_pts=st.corner_pts,
                style=st.style,
                silhouette=False,
                scores=False,  # the score is the FINAL glyph's, not a per-stage value
            )
        )
    return out


def save(fig, name: str, out_dir: Path | None = None) -> Path:
    """Write `fig` as a PNG into the output dir; close it; return the path."""
    out_dir = out_dir or _default_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / (name if name.endswith(".png") else f"{name}.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path
