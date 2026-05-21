"""Visual aid for picking MVP-glyph bounding boxes + calibration on the Loth 1866 chart.

Renders chart.svg onto white background and overlays:
  - a coordinate grid (fine cyan every 50 px, heavy every 100 px with labels),
  - the current bboxes from mvp/canonical/loth_bboxes.json as coloured
    rectangles, each labelled with its (glyph, position) name,
  - per-glyph calibration: baseline_y / midband_y as horizontal dashed lines,
    start_xy as a star marker — these feed the trace_skeleton tool.

Workflow:
  1. Run: uv run python -m mvp.tools.annotate_chart
  2. Open mvp/out/loth-bbox-annotated.png; verify that the dashed baseline
     line sits on the chart's lower writing-line and midband on the top of
     the x-height region for each glyph, and that the star sits where you
     intend the stroke to begin.
  3. Edit mvp/canonical/loth_bboxes.json with corrected coordinates.
  4. Re-run this tool to verify, then mvp.tools.trace_skeleton <glyph>
     to actually extract the canonical.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from mvp.tools.loth import OUTPUT_DIR, REPO_ROOT, load_bboxes, rasterise_svg


GRID_FINE = 50
GRID_HEAVY = 100


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    chart = rasterise_svg()
    h, w = chart.shape

    bboxes = load_bboxes()

    fig, ax = plt.subplots(figsize=(18, 21))
    ax.imshow(chart, cmap="gray", vmin=0, vmax=255)

    for y in range(0, h + 1, GRID_FINE):
        ax.axhline(y, color="cyan", lw=0.3, alpha=0.35)
    for x in range(0, w + 1, GRID_FINE):
        ax.axvline(x, color="cyan", lw=0.3, alpha=0.35)
    for y in range(0, h + 1, GRID_HEAVY):
        ax.axhline(y, color="dodgerblue", lw=0.7, alpha=0.65)
        ax.text(-12, y, str(y), fontsize=8, color="navy", ha="right", va="center")
    for x in range(0, w + 1, GRID_HEAVY):
        ax.axvline(x, color="dodgerblue", lw=0.7, alpha=0.65)
        ax.text(x, -12, str(x), fontsize=8, color="navy", ha="center", va="bottom", rotation=0)

    cmap = plt.colormaps["tab10"]
    unset = []
    for i, (name, bbox) in enumerate(bboxes.items()):
        color = cmap(i % 10)
        if bbox is None:
            unset.append(name)
            continue
        y0, y1, x0, x1 = bbox["y0"], bbox["y1"], bbox["x0"], bbox["x1"]
        rect = Rectangle((x0, y0), x1 - x0, y1 - y0, linewidth=2.5, edgecolor=color, facecolor="none", zorder=4)
        ax.add_patch(rect)
        ax.text(x0, y0 - 8, f"{name}  ({x0},{y0})→({x1},{y1})", fontsize=9, color=color, weight="bold", zorder=5)
        for ex in bbox.get("exclude", []):
            ey0, ey1, ex0, ex1 = ex["y0"], ex["y1"], ex["x0"], ex["x1"]
            ex_rect = Rectangle((ex0, ey0), ex1 - ex0, ey1 - ey0, linewidth=1.5, edgecolor=color, facecolor=color, alpha=0.25, linestyle="--", zorder=4)
            ax.add_patch(ex_rect)
            ax.text(ex0, ey1 + 2, "exclude", fontsize=7, color=color, style="italic", zorder=5)

        # v0.2 calibration overlays — drawn only inside the bbox so multiple
        # rows don't all draw long lines across the chart.
        baseline_y = bbox.get("baseline_y")
        midband_y = bbox.get("midband_y")
        if baseline_y is not None:
            ax.plot([x0, x1], [baseline_y, baseline_y], color=color, lw=1.2, ls="--", zorder=5)
            ax.text(x1 + 2, baseline_y, "base", fontsize=7, color=color, va="center", zorder=5)
        if midband_y is not None:
            ax.plot([x0, x1], [midband_y, midband_y], color=color, lw=1.0, ls=":", zorder=5)
            ax.text(x1 + 2, midband_y, "mid", fontsize=7, color=color, va="center", zorder=5)
        start_xy = bbox.get("start_xy")
        if start_xy is not None:
            sx, sy = start_xy
            ax.plot(sx, sy, marker="*", color=color, markersize=14, markeredgecolor="black", markeredgewidth=0.6, zorder=6)

    if unset:
        ax.text(20, h - 20, f"unset (no bbox yet): {', '.join(unset)}", fontsize=11, color="dimgray", style="italic")

    ax.set_xlim(-60, w + 30)
    ax.set_ylim(h + 30, -60)
    ax.set_aspect("equal")
    ax.set_title(f"Loth 1866 chart — coordinate grid (cyan @{GRID_FINE}px, blue @{GRID_HEAVY}px) + MVP glyph bboxes + calibration", fontsize=13)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "loth-bbox-annotated.png"
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")
    print(f"{sum(1 for v in bboxes.values() if v is not None)} bboxes set, {len(unset)} pending")


if __name__ == "__main__":
    main()
