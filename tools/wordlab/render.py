"""matplotlib overlays of a composed word over its specimen — the word picture.

`word_panel` builds a per-Axes draw callback for glyphlab's generic `tile` grid
(imported, not re-implemented — one grid core for both tools). Over the faint
specimen crop it draws: the specimen skeleton (blue), the baseline/midband
guides, and the composed centerlines at the FITTED registration, colour-coded
the way the word-bench overlay is — connectors bright red, glyph bodies dark
red, deferred diacritics orange. Each connector gets a callout naming the join
and its penalty (`n→e 1.00`) with a thin arrow, and a monospace caption in a
right-hand margin lists loss/trans/cover/width and the worst segments — so the
picture says WHERE the composition lost points, not just that it did.

`--heatmap` recolours the connectors green→red by penalty instead of a flat
red. A live case (no specimen) drops the crop and draws the composed word in its
own units on white — there is nothing to overlay or score, only the ductus to
look at.

matplotlib is a dev/test-only dependency (the `viz` extra); it is never imported
by `core`/`api`, so it stays out of the production image.
"""

from __future__ import annotations

from collections.abc import Callable

import matplotlib


matplotlib.use("Agg")  # headless: render to file, never a window (mirrors glyphlab.render)

import numpy as np  # noqa: E402

# Reuse glyphlab's grid core + saver + palette anchor — one implementation, two
# tools. Imported after use("Agg") so the shared backend is already set.
from tools.glyphlab.render import GREEN, save, tile  # noqa: E402, F401 (re-exported for callers)

from .derive import WordDeriveResult  # noqa: E402


# The word-bench overlay's colour scheme (tools/wordbench/run.py::_overlay), so a
# wordlab picture and a bench artifact read identically. 0–1 RGB for matplotlib.
_SKEL = (90 / 255, 140 / 255, 220 / 255)  # specimen skeleton — blue
_CONNECTOR = (235 / 255, 40 / 255, 40 / 255)  # generated Übergang — bright red
_GLYPH = (150 / 255, 30 / 255, 40 / 255)  # glyph body stroke — dark red
_DIACRITIC = (230 / 255, 140 / 255, 30 / 255)  # deferred floating mark — orange
_BASELINE = "#e09696"
_MIDBAND = "#84cf84"
_CAPTION = "#222222"

# Heatmap saturation: a connector penalty of 0.5 is the reddest end of the scale
# (word penalties live in [0, 1]; 0.5 is already a bad join).
HEAT_VMAX = 0.5
# Mark a headline component at/above this penalty in the caption (a notable loss).
_SCORE_HI = 0.5


def _short(key: str | None) -> str:
    """Glyph_key → its bare glyph name for a compact label (``e-medial`` → ``e``)."""
    return key.split("-")[0] if key else "?"


def _seg_label(row: dict) -> str:
    """Short writing-order label for a segment row (a join ``a→b`` or a glyph)."""
    if row["kind"] == "connector":
        pair = row.get("pair") or ["?", "?"]
        return f"{_short(pair[0])}→{_short(pair[1])}"
    return _short(row.get("glyph_key"))


def _transform(pts: list, xh: float, tx: float, ty: float, baseline_row: float) -> np.ndarray:
    """Composed template-frame points (x right, y up, baseline 0) → crop pixels.

    The SAME mapping the metric and the bench overlay use, so the drawn
    centerlines land exactly where the score judged them.
    """
    a = np.asarray(pts, dtype=float)
    if a.size == 0:
        return a.reshape(0, 2)
    out = np.empty_like(a)
    out[:, 0] = a[:, 0] * xh + tx
    out[:, 1] = baseline_row - a[:, 1] * xh + ty
    return out


def _score_caption(result: WordDeriveResult) -> str | None:
    """Right-margin quality breakdown for a scored specimen, else None.

    Lists the headline (loss + the three penalties, notable ones marked) and the
    worst segments, so the caption reads as "here is where the word lost points".
    Live and unscorable cases have no headline and get their own inline note.
    """
    report = result.report
    if report is None:
        return None
    if report.get("failed"):
        lines = [f"loss   {report['loss']:.3f}", "FAILED"]
        lines += [f" miss {_short(k)}" for k in report.get("missing", [])[:6]]
        return "\n".join(lines)
    lines = [f"loss   {report['loss']:.3f}"]
    for label, key in (("trans", "transition"), ("cover", "coverage"), ("width", "width")):
        val = report[key]
        lines.append(f"{label:<6} {val:.3f}{'  <<' if val >= _SCORE_HI else ''}")
    if result.segments:
        lines.append("--- worst")
        for row in sorted(result.segments, key=lambda r: -r["penalty"])[:4]:
            lines.append(f"{_seg_label(row):<7} {row['penalty']:.2f}")
    return "\n".join(lines)


def _connector_penalties(result: WordDeriveResult) -> dict[tuple, float]:
    """(from_slot, to_slot) → penalty for the scored connectors (empty w/o a score)."""
    if not result.segments:
        return {}
    return {(r["from_slot"], r["to_slot"]): r["penalty"] for r in result.segments if r["kind"] == "connector"}


def _draw_centerlines(ax, result: WordDeriveResult, tf: Callable, heatmap: bool) -> None:
    """The composed word: glyph bodies, connectors, deferred diacritics."""
    cmap = matplotlib.colormaps["RdYlGn_r"]
    conn_pen = _connector_penalties(result) if heatmap else {}
    for it in result.composed["items"]:
        pts = tf(it["centerline"])
        if len(pts) < 2:
            continue
        if "rings" in it:  # a glyph body stroke (same predicate as the metric/overlay)
            color = _DIACRITIC if it.get("diacritic") else _GLYPH
            lw = 1.5
        else:  # a generated connector
            if heatmap:
                pen = conn_pen.get((it.get("from_slot"), it.get("to_slot")), 0.0)
                color = cmap(min(pen / HEAT_VMAX, 1.0))
            else:
                color = _CONNECTOR
            lw = 2.4
        ax.plot(pts[:, 0], pts[:, 1], color=color, lw=lw, solid_capstyle="round", zorder=3)


def _draw_callouts(ax, result: WordDeriveResult, tf: Callable, head: float) -> None:
    """Per-connector callouts in the header band: ``a→b penalty`` + a thin arrow.

    Labels sit ABOVE the word (in the band opened by extending the y-limit), so
    they never cover the ink; two vertical lanes stagger neighbouring joins. The
    arrow is tinted green→red by penalty so severity reads at a glance while the
    text stays dark and legible.
    """
    cmap = matplotlib.colormaps["RdYlGn_r"]
    rows = {(r["from_slot"], r["to_slot"]): r for r in result.segments if r["kind"] == "connector"}
    lanes = (-0.10 * head, -0.24 * head)  # header band opens upward to -head (y inverted)
    lane = 0
    for it in result.composed["items"]:
        if "rings" in it:
            continue
        row = rows.get((it.get("from_slot"), it.get("to_slot")))
        if row is None:
            continue
        pts = tf(it["centerline"])
        if len(pts) < 2:
            continue
        mid = pts[len(pts) // 2]
        color = cmap(min(row["penalty"] / HEAT_VMAX, 1.0))
        ax.annotate(
            f"{_seg_label(row)} {row['penalty']:.2f}",
            xy=(float(mid[0]), float(mid[1])),
            xytext=(float(mid[0]), lanes[lane % len(lanes)]),
            fontsize=6.5,
            ha="center",
            va="bottom",
            color=_CAPTION,
            zorder=6,
            arrowprops={"arrowstyle": "->", "color": color, "lw": 0.8},
        )
        lane += 1


def _draw_specimen(ax, result: WordDeriveResult, *, callouts: bool, heatmap: bool, skeleton: bool) -> None:
    case = result.case
    tf = lambda pts: _transform(  # noqa: E731 — a tiny per-panel closure over the fit
        pts, result.xh_px, result.registration["tx"], result.registration["ty"], result.baseline_row
    )
    crop = np.clip(case.crop, 0, 1)
    H, W = crop.shape
    caption = _score_caption(result)
    margin = 0.5 * W if caption else 0.0
    head = 0.34 * H if (callouts and result.segments) else 0.0

    faint = crop * 0.6 + 0.4  # lighten the ink so the overlay reads on top
    ax.imshow(faint, cmap="gray", vmin=0, vmax=1, extent=(0, W, H, 0), interpolation="nearest", zorder=0)
    ax.set_xlim(0, W + margin)
    ax.set_ylim(H, -head)  # inverted (image convention); the band above holds callouts
    ax.set_aspect("equal")
    ax.axis("off")

    if skeleton:
        ys, xs = np.where(case.skel)
        ax.scatter(xs, ys, s=1.0, c=[_SKEL], linewidths=0, zorder=1)
    guide_xmax = W / (W + margin)  # keep the guides over the glyph, not the caption margin
    ax.axhline(result.baseline_row, xmax=guide_xmax, color=_BASELINE, lw=0.8, zorder=1)
    ax.axhline(case.midband_y - case.rect[1], xmax=guide_xmax, color=_MIDBAND, lw=0.8, zorder=1)

    # Heatmap only when segments exist (same gate as the live path): an
    # unscored case must not paint its connectors penalty-0 green.
    _draw_centerlines(ax, result, tf, heatmap and bool(result.segments))
    if callouts and result.segments:
        _draw_callouts(ax, result, tf, head)
    if caption:
        ax.text(
            W + 0.04 * W,
            -head,
            caption,
            va="top",
            ha="left",
            fontsize=6.5,
            family="monospace",
            color=_CAPTION,
            zorder=6,
        )


def _draw_live(ax, result: WordDeriveResult, *, heatmap: bool) -> None:
    """No specimen: the composed word in its own units on white."""
    tf = lambda pts: _transform(pts, result.xh_px, 0.0, 0.0, result.baseline_row)  # noqa: E731
    ax.set_facecolor("white")

    drawn = [tf(it["centerline"]) for it in result.composed["items"] if len(it["centerline"]) >= 2]
    if drawn:
        stacked = np.vstack(drawn)
        xmin, ymin = stacked.min(axis=0)
        xmax, ymax = stacked.max(axis=0)
    else:
        xmin, ymin, xmax, ymax = 0.0, -result.xh_px, result.xh_px, result.xh_px
    pad = 0.2 * result.xh_px
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.set_ylim(ymax + pad, ymin - pad)  # inverted so ascenders sit up top
    ax.set_aspect("equal")
    ax.axis("off")

    guides = result.composed.get("guides") or {}
    ax.axhline(result.baseline_row, color=_BASELINE, lw=0.8, zorder=1)
    if "midband" in guides:
        ax.axhline(result.baseline_row - guides["midband"] * result.xh_px, color=_MIDBAND, lw=0.8, zorder=1)

    _draw_centerlines(ax, result, tf, heatmap and bool(result.segments))
    note = f"live · {result.case.origin}"
    if result.composed["missing"]:
        note += "  missing: " + " ".join(_short(k) for k in result.composed["missing"][:6])
    # Footer below the drawing (y is inverted, so ymax+pad is the bottom edge) —
    # the top-left corner belongs to the panel title.
    ax.text(xmin - pad, ymax + pad, note, va="top", ha="left", fontsize=6.5, family="monospace", color=_CAPTION)


def word_panel(
    result: WordDeriveResult,
    *,
    title: str | None = None,
    callouts: bool = True,
    heatmap: bool = False,
    skeleton: bool = True,
) -> Callable:
    """A draw callback for glyphlab's `tile` — one composed word over its specimen.

    `callouts` annotates each connector with its penalty; `heatmap` recolours the
    connectors green→red by penalty; `skeleton` toggles the blue specimen
    skeleton. A live case (no specimen) ignores the specimen-only toggles and
    draws on white in composed units.
    """

    def draw(ax) -> None:
        if result.case.has_specimen:
            _draw_specimen(ax, result, callouts=callouts, heatmap=heatmap, skeleton=skeleton)
        else:
            _draw_live(ax, result, heatmap=heatmap)
        ax.set_title(title or result.case.id, fontsize=8.5)

    return draw
