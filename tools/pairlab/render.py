"""matplotlib panels for a join dissection — the picture next to the numbers.

Two panels per occurrence, built as draw callbacks for glyphlab's generic
``tile`` grid:

* ``overlay_panel`` — the specimen crop with every letter at its INDEPENDENT
  optimal placement (the pair coloured, neighbours grey), the regenerated
  production connector between the two placements (red), the specimen's own
  connecting stroke (blue), and the adaptation zones — the part of A's tail /
  B's head where the specimen has left the template — flagged in orange.
* ``profile_panel`` — the tail/head deviation profiles: specimen distance
  (x-height units) against arc length from the join, with the departure
  threshold and the measured adaptation lengths marked.

matplotlib is a dev/test-only dependency (the ``viz`` extra); it is never
imported by ``core``/``api``.
"""

from __future__ import annotations

from collections.abc import Callable

import matplotlib


matplotlib.use("Agg")  # headless: render to file, never a window (mirrors glyphlab.render)

import numpy as np  # noqa: E402

from tools.glyphlab.render import save, tile  # noqa: E402, F401 (re-exported for callers)

from .analyze import ADAPT_THRESH_UNITS, JoinDissection  # noqa: E402


_SKEL = (90 / 255, 140 / 255, 220 / 255)  # specimen skeleton — blue (bench palette)
_REAL = (25 / 255, 80 / 255, 200 / 255)  # the specimen's own connecting stroke — strong blue
_A = (150 / 255, 30 / 255, 40 / 255)  # first letter at its independent fit — dark red
_B = (25 / 255, 120 / 255, 60 / 255)  # second letter — viridian green
_OTHER = (0.55, 0.55, 0.55)  # the word's remaining letters — grey
_GEN = (235 / 255, 40 / 255, 40 / 255)  # regenerated production connector — bright red
_ADAPT = (230 / 255, 140 / 255, 30 / 255)  # adaptation zone on the glyph's own stroke — orange
_BASELINE = "#e09696"
_MIDBAND = "#84cf84"
_CAPTION = "#222222"


def _fmt_deg(v: float | None) -> str:
    return "—" if v is None else f"{v:+.0f}°"


def _caption(d: JoinDissection) -> str:
    xh = d.result.xh_px
    bound = "  AT BOUND" if (d.a.at_bound or d.b.at_bound) else ""
    lines = [
        f"{d.a.base}→{d.b.base}  [{d.case.id}]{bound}",
        f"A shift {d.a.ddx_px / xh:+.2f},{-d.a.ddy_px / xh:+.2f}  resid {d.a.resid_after:.3f}",
        f"B shift {d.b.ddx_px / xh:+.2f},{-d.b.ddy_px / xh:+.2f}  resid {d.b.resid_after:.3f}",
        f"gen chamfer {d.gen_chamfer:.3f}",
        f"tail adapt  {d.tail_adapt:.2f} xh",
        f"head adapt  {d.head_adapt:.2f} xh",
        f"exit  gen {_fmt_deg(d.exit_deg)} real {_fmt_deg(d.real_exit_deg)}",
        f"entry gen {_fmt_deg(d.entry_deg)} real {_fmt_deg(d.real_entry_deg)}",
    ]
    if d.real_depart_y is not None and d.real_arrive_y is not None:
        lines.append(f"real y {d.real_depart_y:+.2f}→{d.real_arrive_y:+.2f} xh")
    return "\n".join(lines)


def _adapt_segment(profile: np.ndarray, stroke_px: np.ndarray, adapt: float, from_end: bool) -> np.ndarray:
    """The piece of the stroke covered by the adaptation zone (crop px)."""
    if adapt <= 0 or len(profile) == 0:
        return np.zeros((0, 2))
    pts = stroke_px[::-1] if from_end else stroke_px
    n = int(np.searchsorted(profile[:, 0], adapt)) + 1
    return pts[: max(n, 2)]


def overlay_panel(d: JoinDissection, *, title: str | None = None, zoom: bool = True) -> Callable:
    """Draw callback: the dissected join over its specimen crop.

    ``zoom`` (default) crops the view to the pair's neighbourhood (±0.8 xh
    around the two letters); ``zoom=False`` shows the whole word. The metric
    caption sits in a right-hand margin either way.
    """

    def draw(ax) -> None:
        case = d.case
        crop = np.clip(case.crop, 0, 1)
        H, W = crop.shape
        caption = _caption(d)
        if zoom:
            pts = np.vstack([*d.a.body_px, *d.b.body_px])
            pad = 0.8 * d.result.xh_px
            x0, x1 = pts[:, 0].min() - pad, pts[:, 0].max() + pad
            y0, y1 = max(0.0, pts[:, 1].min() - pad), min(float(H), pts[:, 1].max() + pad)
        else:
            x0, x1, y0, y1 = 0.0, float(W), 0.0, float(H)
        margin = 0.62 * (x1 - x0)
        faint = crop * 0.6 + 0.4
        ax.imshow(faint, cmap="gray", vmin=0, vmax=1, extent=(0, W, H, 0), interpolation="nearest", zorder=0)

        ys, xs = np.where(case.skel)
        ax.scatter(xs, ys, s=1.0, c=[_SKEL], linewidths=0, zorder=1)
        guide_xmax = (x1 - x0) / (x1 - x0 + margin)
        ax.axhline(d.result.baseline_row, xmax=guide_xmax, color=_BASELINE, lw=0.8, zorder=1)
        ax.axhline(case.midband_y - case.rect[1], xmax=guide_xmax, color=_MIDBAND, lw=0.8, zorder=1)

        # Every letter at its INDEPENDENT fit: the pair coloured, the rest grey.
        for i, fit in d.fits.items():
            color = _A if i == d.slot_a else _B if i == d.slot_a + 1 else _OTHER
            lw = 2.0 if i in (d.slot_a, d.slot_a + 1) else 1.1
            for stroke in fit.body_px:
                ax.plot(stroke[:, 0], stroke[:, 1], color=color, lw=lw, solid_capstyle="round", zorder=3)

        # Regenerated production connector between the independent placements.
        ax.plot(d.gen_px[:, 0], d.gen_px[:, 1], color=_GEN, lw=2.2, ls=(0, (4, 2)), zorder=4)
        # The specimen's own connecting stroke.
        if len(d.real_px) >= 2:
            ax.plot(d.real_px[:, 0], d.real_px[:, 1], color=_REAL, lw=2.6, zorder=4)

        # Adaptation zones on the glyphs' own strokes.
        for profile, fit_stroke, adapt, from_end in (
            (d.tail_profile, d.a.body_px[-1], d.tail_adapt, True),
            (d.head_profile, d.b.body_px[0], d.head_adapt, False),
        ):
            seg = _adapt_segment(profile, fit_stroke, adapt, from_end)
            if len(seg) >= 2:
                ax.plot(seg[:, 0], seg[:, 1], color=_ADAPT, lw=3.4, alpha=0.9, zorder=5)

        ax.scatter(*d.exit_px, s=26, c=[_A], edgecolors="white", linewidths=0.6, zorder=6)
        ax.scatter(*d.entry_px, s=26, c=[_B], edgecolors="white", linewidths=0.6, zorder=6)

        ax.set_xlim(x0, x1 + margin)
        ax.set_ylim(y1, y0)
        ax.text(
            x1 + 0.03 * (x1 - x0), y0, caption, va="top", ha="left", fontsize=6.2, family="monospace", color=_CAPTION
        )
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title or f"{d.a.base}→{d.b.base} · {case.id}", fontsize=8.5)

    return draw


def profile_panel(d: JoinDissection, *, title: str | None = None) -> Callable:
    """Draw callback: tail/head deviation against arc distance from the join."""

    def draw(ax) -> None:
        if len(d.tail_profile):
            ax.plot(d.tail_profile[:, 0], d.tail_profile[:, 1], color=_A, lw=1.8, label=f"{d.a.base} tail")
        if len(d.head_profile):
            ax.plot(d.head_profile[:, 0], d.head_profile[:, 1], color=_B, lw=1.8, label=f"{d.b.base} head")
        ax.axhline(ADAPT_THRESH_UNITS, color=_CAPTION, lw=0.8, ls=":")
        for adapt, color in ((d.tail_adapt, _A), (d.head_adapt, _B)):
            if adapt > 0:
                ax.axvline(adapt, color=color, lw=0.9, ls="--", alpha=0.7)
        ax.set_xlabel("arc from join (xh)", fontsize=7)
        ax.set_ylabel("specimen distance (xh)", fontsize=7)
        ax.tick_params(labelsize=6.5)
        ax.legend(fontsize=6.5, frameon=False)
        ax.set_title(title or f"adaptation · {d.case.id}", fontsize=8.5)

    return draw
