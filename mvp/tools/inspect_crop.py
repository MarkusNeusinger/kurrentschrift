"""Per-glyph crop inspector for picking exclude rectangles.

For each glyph in loth_bboxes.json that has a bbox set, renders a high-zoom
PNG showing:
  - the crop content (from chart.jpg, the same source the trace tool uses);
  - a coordinate grid in CHART-GLOBAL pixel coordinates (so values you read
    off the grid go directly into loth_bboxes.json without translation);
  - the current bbox outlined and any current `exclude` sub-rectangles
    drawn as dashed translucent overlays;
  - the current M0 skeleton in red and the resolved walk-start (cyan star);
  - the endpoints of the skeleton (green) and the junctions (red squares),
    each labelled with their crop-local pixel coords;
  - the longest-path trace as a magenta line, plus the anchor positions
    as yellow dots.

Workflow to tighten a crop:
  1. uv run python -m mvp.tools.inspect_crop          # writes one PNG per glyph
  2. Open mvp/out/inspect-<glyph>.png
  3. Identify neighbour-letter ink that isn't part of the target glyph
  4. Read its bounding rectangle off the grid (chart-global coords)
  5. Add it to the glyph's `exclude` list in loth_bboxes.json
  6. uv run python -m mvp.tools.trace_skeleton <glyph>
  7. uv run python -m mvp.render_canonicals   (or re-run inspect to verify)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from mvp.extract import binarize_adaptive, skeleton_and_width
from mvp.tools.loth import OUTPUT_DIR, REPO_ROOT, crop_with_excludes, load_bboxes, load_chart_grayscale
from mvp.tools.trace_skeleton import (
    neighbour_pixels,
    prune_spurs,
    resolve_walk_start,
    snap_to_any_skel_pixel,
    walk_skeleton,
    walk_through_waypoints,
)


GRID_FINE_PX = 10
GRID_HEAVY_PX = 50


def inspect_glyph(glyph_key: str, bbox: dict, chart_gray: np.ndarray) -> Path:
    crop = crop_with_excludes(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop)
    skel_raw, _ = skeleton_and_width(mask)
    skel = prune_spurs(skel_raw)

    # Topology
    ys, xs = np.where(skel)
    counts = np.array([len(neighbour_pixels(int(y), int(x), skel)) for y, x in zip(ys, xs)]) if len(ys) else np.empty(0)
    endpoints = [(int(ys[i]), int(xs[i])) for i in range(len(ys)) if counts[i] == 1]
    junctions = [(int(ys[i]), int(xs[i])) for i in range(len(ys)) if counts[i] >= 3]

    snapped = None
    path: list[tuple[int, int]] = []
    waypoints_local: list[tuple[int, int]] = []
    if bbox.get("start_xy") is not None and len(ys):
        sx_local = bbox["start_xy"][0] - bbox["x0"]
        sy_local = bbox["start_xy"][1] - bbox["y0"]
        if 0 <= sx_local < crop.shape[1] and 0 <= sy_local < crop.shape[0]:
            snapped, comp = resolve_walk_start((sx_local, sy_local), skel)
            wps_chart = bbox.get("waypoints")
            if wps_chart:
                wps_snapped: list[tuple[int, int]] = []
                for wp in wps_chart:
                    wx = wp[0] - bbox["x0"]
                    wy = wp[1] - bbox["y0"]
                    if 0 <= wx < crop.shape[1] and 0 <= wy < crop.shape[0]:
                        wps_snapped.append(snap_to_any_skel_pixel((wx, wy), comp))
                waypoints_local = wps_snapped
                path, _ = walk_through_waypoints(comp, snapped, wps_snapped)
            else:
                path, _ = walk_skeleton(comp, snapped, bbox.get("branch_choices"))

    h, w = crop.shape
    y0, x0 = bbox["y0"], bbox["x0"]
    y1, x1 = bbox["y1"], bbox["x1"]

    # Build a single panel with the crop and chart-global coord ticks.
    fig, ax = plt.subplots(figsize=(max(8, w / 10), max(8, h / 10)))
    ax.imshow(crop, cmap="gray", vmin=0, vmax=1, extent=[x0, x1, y1, y0])

    # Grid lines in chart-global coords (so labels match loth_bboxes.json).
    for gx in range(int(np.ceil(x0 / GRID_FINE_PX) * GRID_FINE_PX), x1 + 1, GRID_FINE_PX):
        ax.axvline(gx, color="cyan", lw=0.4, alpha=0.4)
    for gy in range(int(np.ceil(y0 / GRID_FINE_PX) * GRID_FINE_PX), y1 + 1, GRID_FINE_PX):
        ax.axhline(gy, color="cyan", lw=0.4, alpha=0.4)
    for gx in range(int(np.ceil(x0 / GRID_HEAVY_PX) * GRID_HEAVY_PX), x1 + 1, GRID_HEAVY_PX):
        ax.axvline(gx, color="dodgerblue", lw=0.9, alpha=0.7)
        ax.text(gx, y0 - 2, str(gx), fontsize=9, color="navy", ha="center", va="bottom")
    for gy in range(int(np.ceil(y0 / GRID_HEAVY_PX) * GRID_HEAVY_PX), y1 + 1, GRID_HEAVY_PX):
        ax.axhline(gy, color="dodgerblue", lw=0.9, alpha=0.7)
        ax.text(x0 - 2, gy, str(gy), fontsize=9, color="navy", ha="right", va="center")

    # bbox outline
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, edgecolor="black", facecolor="none", lw=1.2, ls="--"))

    # exclude regions
    for ex in bbox.get("exclude", []):
        ex_rect = Rectangle((ex["x0"], ex["y0"]), ex["x1"] - ex["x0"], ex["y1"] - ex["y0"], edgecolor="orange", facecolor="orange", alpha=0.25, lw=1.5, ls="--")
        ax.add_patch(ex_rect)
        ax.text(ex["x0"], ex["y1"] + 1, f"exclude ({ex['x0']},{ex['y0']}→{ex['x1']},{ex['y1']})", fontsize=8, color="darkorange", style="italic")

    # baseline / midband / start
    if bbox.get("baseline_y") is not None:
        ax.axhline(bbox["baseline_y"], color="red", lw=1.0, ls=":", alpha=0.7)
        ax.text(x1 + 1, bbox["baseline_y"], f"baseline_y={bbox['baseline_y']}", fontsize=9, color="red", va="center")
    if bbox.get("midband_y") is not None:
        ax.axhline(bbox["midband_y"], color="purple", lw=1.0, ls=":", alpha=0.7)
        ax.text(x1 + 1, bbox["midband_y"], f"midband_y={bbox['midband_y']}", fontsize=9, color="purple", va="center")
    if bbox.get("start_xy") is not None:
        ax.plot(bbox["start_xy"][0], bbox["start_xy"][1], "b*", markersize=18, markeredgecolor="black", markeredgewidth=0.8, zorder=8)
        ax.text(bbox["start_xy"][0] + 3, bbox["start_xy"][1], f"start_xy={bbox['start_xy']}", fontsize=9, color="blue")

    # Skeleton (red), endpoints (green), junctions (red squares)
    for (sy, sx) in zip(*np.where(skel)):
        ax.plot(x0 + sx + 0.5, y0 + sy + 0.5, "s", color="red", markersize=2, alpha=0.55, zorder=4)
    for (ly, lx) in endpoints:
        gx_global = x0 + lx
        gy_global = y0 + ly
        ax.plot(gx_global, gy_global, "o", color="lime", markersize=10, markeredgecolor="black", markeredgewidth=0.7, zorder=6)
        ax.annotate(f"({lx},{ly})", (gx_global, gy_global), fontsize=8, color="green", xytext=(4, 4), textcoords="offset points")
    for (ly, lx) in junctions:
        gx_global = x0 + lx
        gy_global = y0 + ly
        ax.plot(gx_global, gy_global, "s", color="red", markersize=10, markeredgecolor="black", markeredgewidth=0.7, zorder=6)

    # Walk path + anchors (if traced)
    if path:
        path_gx = [x0 + p[1] + 0.5 for p in path]
        path_gy = [y0 + p[0] + 0.5 for p in path]
        ax.plot(path_gx, path_gy, "-", color="magenta", lw=2.0, alpha=0.7, zorder=5)
        if snapped is not None:
            ax.plot(x0 + snapped[1] + 0.5, y0 + snapped[0] + 0.5, "*", color="cyan", markersize=20, markeredgecolor="black", markeredgewidth=0.8, zorder=8)
    # Waypoint markers (numbered) — drawn separately so they show even if path is short
    for k, (wy, wx) in enumerate(waypoints_local):
        ax.plot(x0 + wx + 0.5, y0 + wy + 0.5, "P", color="orange", markersize=16, markeredgecolor="black", markeredgewidth=0.8, zorder=9)
        ax.annotate(f"w{k}", (x0 + wx + 0.5, y0 + wy + 0.5), fontsize=10, color="darkorange", weight="bold", xytext=(6, 6), textcoords="offset points")

    ax.set_xlim(x0 - 25, x1 + 50)
    ax.set_ylim(y1 + 15, y0 - 15)  # image y goes down
    ax.set_aspect("equal")
    n_ep = len(endpoints)
    n_j = len(junctions)
    ax.set_title(
        f"{glyph_key}  bbox=({x0},{y0})→({x1},{y1})  exclude={len(bbox.get('exclude', []))}  "
        f"endpoints={n_ep}  junctions={n_j}  path={len(path)}px",
        fontsize=11,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"inspect-{glyph_key}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main() -> None:
    chart_gray = load_chart_grayscale()
    bboxes = load_bboxes()
    for key, bbox in bboxes.items():
        if bbox is None:
            continue
        out = inspect_glyph(key, bbox, chart_gray)
        print(f"wrote {out.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
