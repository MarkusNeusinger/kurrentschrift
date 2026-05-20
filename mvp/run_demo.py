"""M0 two-channel demo on the Loth 1866 chart.

Pipeline: load → adaptive binarize → skeletonize → distance transform.
Output: a 2x2 panel saved to mvp/out/chart-overlay.png plus a stats
printout relevant to the §5 Binarisierungsfalle observation
(mask coverage, skeleton length, skeleton-component count as a proxy
for fragmentation, half-width percentiles).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import label as connected_components

from mvp.extract import binarize_adaptive, load_grayscale, skeleton_and_width


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = REPO_ROOT / "data" / "sources" / "loth-1866" / "chart.jpg"
OUTPUT_DIR = REPO_ROOT / "mvp" / "out"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    gray = load_grayscale(SOURCE_PATH)
    mask = binarize_adaptive(gray)
    skel, width = skeleton_and_width(mask)

    skel_pixels = int(skel.sum())
    mask_pixels = int(mask.sum())
    # 8-connectivity: a thin skeleton steps diagonally; 4-connectivity would
    # count every diagonal step as a fresh component (false fragmentation).
    labelled, n_components = connected_components(skel, structure=np.ones((3, 3), dtype=np.int8))
    comp_sizes = np.bincount(labelled.ravel())[1:] if n_components else np.empty(0, dtype=np.int64)
    big = int((comp_sizes >= 50).sum())
    tiny = int((comp_sizes <= 3).sum())
    if skel_pixels:
        on_skel = width[skel]
        p5, p50, p95 = np.percentile(on_skel, [5, 50, 95])
        w_max = float(on_skel.max())
    else:
        on_skel = np.empty(0, dtype=np.float32)
        p5 = p50 = p95 = w_max = 0.0

    print(f"image            : {SOURCE_PATH.name}  {gray.shape}")
    print(f"mask coverage    : {mask_pixels / mask.size:6.2%}")
    print(f"skeleton pixels  : {skel_pixels}")
    print(f"skeleton comps   : {n_components}  (big >=50 px: {big}; tiny <=3 px: {tiny})")
    print(f"half-width on skel (px): p5={p5:.2f}  median={p50:.2f}  p95={p95:.2f}  max={w_max:.2f}")

    overlay = np.stack([gray, gray, gray], axis=-1)
    overlay[skel] = [1.0, 0.1, 0.1]

    width_canvas = np.full_like(gray, np.nan, dtype=np.float32)
    width_canvas[skel] = on_skel
    cmap_width = LinearSegmentedColormap.from_list("width", ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"])
    cmap_width.set_bad(color="white")

    fig, axes = plt.subplots(2, 2, figsize=(22, 14))

    axes[0, 0].imshow(gray, cmap="gray", vmin=0, vmax=1)
    axes[0, 0].set_title("(a) Original grayscale")
    axes[0, 0].axis("off")

    axes[0, 1].imshow(mask, cmap="gray_r")
    axes[0, 1].set_title("(b) Adaptive binarization (ink = black)")
    axes[0, 1].axis("off")

    axes[1, 0].imshow(overlay)
    axes[1, 0].set_title("(c) Skeleton overlay (red)")
    axes[1, 0].axis("off")

    im = axes[1, 1].imshow(width_canvas, cmap=cmap_width)
    axes[1, 1].set_title("(d) Half-stroke-width along skeleton (px)")
    axes[1, 1].axis("off")
    fig.colorbar(im, ax=axes[1, 1], fraction=0.046, pad=0.04)

    fig.suptitle(f"M0 two-channel demo — {SOURCE_PATH.name}", fontsize=14)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "chart-overlay.png"
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")

    # Zoom on the 's' row: the §9 anchor allograph. The 's' row sits around
    # row index 0 of the rightmost column in the chart layout; coords below
    # were eyeballed once from chart.jpg and are stable for this PD source.
    y0, y1, x0, x1 = 0, 200, 1100, 1633
    fig2, axes2 = plt.subplots(1, 3, figsize=(18, 5))
    axes2[0].imshow(gray[y0:y1, x0:x1], cmap="gray", vmin=0, vmax=1)
    axes2[0].set_title("zoom: 's' row — original")
    axes2[0].axis("off")
    axes2[1].imshow(overlay[y0:y1, x0:x1])
    axes2[1].set_title("zoom: 's' row — skeleton (red)")
    axes2[1].axis("off")
    im2 = axes2[2].imshow(width_canvas[y0:y1, x0:x1], cmap=cmap_width)
    axes2[2].set_title("zoom: 's' row — half-width (px)")
    axes2[2].axis("off")
    fig2.colorbar(im2, ax=axes2[2], fraction=0.046, pad=0.04)
    fig2.tight_layout()
    zoom_path = OUTPUT_DIR / "chart-zoom-s-row.png"
    fig2.savefig(zoom_path, dpi=160, bbox_inches="tight")
    plt.close(fig2)
    print(f"wrote {zoom_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
