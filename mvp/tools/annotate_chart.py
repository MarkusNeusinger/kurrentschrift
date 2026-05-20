"""Visual aid for picking MVP-glyph bounding boxes on the Loth 1866 chart.

Renders data/sources/loth-1866/chart.svg onto white background and overlays:
  - a coordinate grid (fine cyan every 50 px, heavy every 100 px with labels),
  - the current bboxes from mvp/canonical/loth_bboxes.json as coloured
    rectangles, each labelled with its (glyph, position) name.

Workflow:
  1. Run: uv run python -m mvp.tools.annotate_chart
  2. Open mvp/out/loth-bbox-annotated.png and read off y0/y1/x0/x1 for any
     glyph that's missing or off (cyan grid lines are spaced every 50 px,
     labelled every 100 px).
  3. Edit mvp/canonical/loth_bboxes.json with the corrected coordinates.
  4. Re-run this tool to verify, then mvp.render_canonicals to update the
     side-by-side review.
"""

from __future__ import annotations

import json
from pathlib import Path

import cairosvg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOTH_SVG = REPO_ROOT / "data" / "sources" / "loth-1866" / "chart.svg"
BBOXES_JSON = REPO_ROOT / "mvp" / "canonical" / "loth_bboxes.json"
OUTPUT_DIR = REPO_ROOT / "mvp" / "out"
SVG_RENDER_PATH = OUTPUT_DIR / "chart-svg-render-white.png"
GRID_FINE = 50
GRID_HEAVY = 100


def rasterise_svg() -> np.ndarray:
    """Render chart.svg onto a white background as grayscale; cache to disk."""
    if not SVG_RENDER_PATH.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(url=str(LOTH_SVG), write_to=str(SVG_RENDER_PATH), output_width=1633, output_height=1869)
        rgba = Image.open(SVG_RENDER_PATH)
        white = Image.new("RGB", rgba.size, (255, 255, 255))
        white.paste(rgba, mask=rgba.split()[3])
        white.convert("L").save(SVG_RENDER_PATH)
    return np.asarray(Image.open(SVG_RENDER_PATH).convert("L"))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    chart = rasterise_svg()
    h, w = chart.shape

    data = json.loads(BBOXES_JSON.read_text(encoding="utf-8"))
    bboxes = data["bboxes"]

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

    if unset:
        ax.text(20, h - 20, f"unset (no bbox yet): {', '.join(unset)}", fontsize=11, color="dimgray", style="italic")

    ax.set_xlim(-60, w + 30)
    ax.set_ylim(h + 30, -60)
    ax.set_aspect("equal")
    ax.set_title(f"Loth 1866 chart — coordinate grid (cyan @{GRID_FINE}px, blue @{GRID_HEAVY}px) + MVP glyph bboxes", fontsize=13)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "loth-bbox-annotated.png"
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")
    print(f"{sum(1 for v in bboxes.values() if v is not None)} bboxes set, {len(unset)} pending")


if __name__ == "__main__":
    main()
