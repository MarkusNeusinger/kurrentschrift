"""Render the M3 Phase A canonicals side-by-side with their Loth-1866 reference.

3x3 layout:
  - Row 1: handmodelled/traced canonical (mvp/canonical/<glyph>_v0.json)
    rendered via mvp.template.render.
  - Row 2: Loth chart crop with the M0 skeleton overlaid in red and the
    canonical's pixel anchors (from the _trace block written by
    mvp.tools.trace_skeleton) plotted on top in yellow — sanity-checks
    that the anchors actually sit on the ink.
  - Row 3: Loth chart crop pure — visual reference for eyeballing whether
    the canonical (row 1) recreates what the chart (row 3) shows.

The bottom-row reference uses the JPG source (same as the trace pipeline)
rather than the SVG render, so what you see is exactly what trace_skeleton
processed.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from mvp import template
from mvp.extract import binarize_adaptive, skeleton_and_width
from mvp.tools.loth import CANONICAL_DIR, OUTPUT_DIR, REPO_ROOT, crop_with_excludes, load_bboxes, load_chart_grayscale


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        ("s-medial", CANONICAL_DIR / "s-medial_v0.json"),
        ("s-final", CANONICAL_DIR / "s-final_v0.json"),
        ("e-medial", CANONICAL_DIR / "e-medial_v0.json"),
    ]

    chart_gray = load_chart_grayscale()
    bboxes = load_bboxes()

    fig, axes = plt.subplots(3, 3, figsize=(15, 13))

    for col, (key, path) in enumerate(files):
        # Row 1: canonical template render
        tpl = template.load(path)
        template.render(tpl, ax=axes[0, col])

        bbox = bboxes.get(key)
        if bbox is None:
            for row in (1, 2):
                axes[row, col].text(0.5, 0.5, f"no bbox for {key}", ha="center", va="center", fontsize=10, color="gray", transform=axes[row, col].transAxes)
                axes[row, col].axis("off")
            continue

        crop = crop_with_excludes(chart_gray, bbox, fill=1.0)

        # Row 2: Loth crop + skeleton overlay + anchor markers (if trace exists)
        mask = binarize_adaptive(crop)
        skel, _ = skeleton_and_width(mask)
        overlay = np.stack([crop, crop, crop], axis=-1)  # float [0,1] RGB
        overlay[skel] = [1.0, 0.1, 0.1]
        axes[1, col].imshow(overlay)
        axes[1, col].set_title(f"Loth crop + skeleton + anchors  ({key})", fontsize=10)
        axes[1, col].axis("off")

        # Anchor markers from the trace block of the canonical JSON
        data = json.loads(path.read_text(encoding="utf-8"))
        trace = data.get("_trace")
        if trace is not None and "pixel_anchors" in trace:
            anchors_global = np.array(trace["pixel_anchors"])
            anchors_local = anchors_global - np.array([bbox["x0"], bbox["y0"]])
            axes[1, col].plot(anchors_local[:, 0], anchors_local[:, 1], "o", color="gold", markersize=6, markeredgecolor="black", markeredgewidth=0.6, zorder=5)
            # connect with a thin line so the stroke order is visible
            axes[1, col].plot(anchors_local[:, 0], anchors_local[:, 1], "-", color="gold", lw=0.8, alpha=0.7, zorder=4)

        # Row 3: Loth crop pure
        axes[2, col].imshow(crop, cmap="gray", vmin=0, vmax=1)
        axes[2, col].set_title(f"Loth 1866 reference (pure)  ({key})", fontsize=10)
        axes[2, col].axis("off")

    fig.suptitle("M3 Phase A v0.2 — traced canonical (row 1) vs. Loth crop with skeleton + anchors (row 2) vs. Loth pure (row 3)", fontsize=13)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "canonicals-phase-a.png"
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
