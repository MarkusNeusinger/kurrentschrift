"""Render the M3 Phase A canonicals side-by-side with their Loth-1866 reference.

Top row: the three handmodelled templates (medial ſ, final s, medial e) drawn
from /mvp/canonical/*.json — these are the §9 MVP-Gate-Tragenden.

Bottom row: corresponding crops from a cairosvg-rasterised version of
data/sources/loth-1866/chart.svg as visual reference. SVG is preferred over
the JPG here because the vector source has no JPEG artefacts, so the
silhouettes are crisp at any zoom. (The JPG remains the canonical data
source for the pipeline; this script only uses the SVG for visual review.)
"""

from __future__ import annotations

from pathlib import Path

import cairosvg
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from mvp import template


REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DIR = REPO_ROOT / "mvp" / "canonical"
LOTH_SVG = REPO_ROOT / "data" / "sources" / "loth-1866" / "chart.svg"
OUTPUT_DIR = REPO_ROOT / "mvp" / "out"
SVG_RENDER_PATH = OUTPUT_DIR / "chart-svg-render-white.png"


# Crop windows on the 1633x1869 SVG rasterisation. The s-row carries the
# s-allograph split as four sub-cells (printed-s | medial-ſ | final-s | capital-S);
# the e-row has the standard three (printed-e | lowercase-cursive | capital-E).
# Coordinates are (y0, y1, x0, x1).
LOTH_CROPS = {
    "s-medial": (60, 220, 1280, 1430),
    "s-final": (60, 220, 1410, 1540),
    "e-medial": (720, 870, 140, 270),
}


def rasterise_svg() -> np.ndarray:
    """Render chart.svg onto a white background as grayscale; cache to disk."""
    if not SVG_RENDER_PATH.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        # cairosvg renders to RGBA with transparent background; composite onto
        # white so the grayscale conversion produces the expected ink-on-paper.
        cairosvg.svg2png(url=str(LOTH_SVG), write_to=str(SVG_RENDER_PATH), output_width=1633, output_height=1869)
        rgba = Image.open(SVG_RENDER_PATH)
        white = Image.new("RGB", rgba.size, (255, 255, 255))
        white.paste(rgba, mask=rgba.split()[3])
        white.convert("L").save(SVG_RENDER_PATH)
    return np.asarray(Image.open(SVG_RENDER_PATH).convert("L"))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        ("s-medial", CANONICAL_DIR / "s-medial_v0.json"),
        ("s-final", CANONICAL_DIR / "s-final_v0.json"),
        ("e-medial", CANONICAL_DIR / "e-medial_v0.json"),
    ]

    chart = rasterise_svg()

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))

    for col, (key, path) in enumerate(files):
        tpl = template.load(path)
        template.render(tpl, ax=axes[0, col])

        y0, y1, x0, x1 = LOTH_CROPS[key]
        axes[1, col].imshow(chart[y0:y1, x0:x1], cmap="gray", vmin=0, vmax=255)
        axes[1, col].set_title(f"Loth 1866 reference  ({key})", fontsize=10)
        axes[1, col].axis("off")

    fig.suptitle("M3 Phase A — canonical templates vs. Loth reference (SVG)", fontsize=14)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "canonicals-phase-a.png"
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
