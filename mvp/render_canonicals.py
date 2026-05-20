"""Render the M3 Phase A canonicals side-by-side with their Loth-1866 reference.

Top row: the three handmodelled templates (medial ſ, final s, medial e) drawn
from /mvp/canonical/*.json — these are the §9 MVP-Gate-Tragenden.

Bottom row: corresponding crops from data/sources/loth-1866/chart.jpg as
visual reference. The ductus (stroke order, crossing resolution) is *not*
copied from Loth — that's our authored contribution — but the silhouette
should be recognisably the same glyph at first glance.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from mvp import template


REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DIR = REPO_ROOT / "mvp" / "canonical"
LOTH_CHART = REPO_ROOT / "data" / "sources" / "loth-1866" / "chart.jpg"
OUTPUT_DIR = REPO_ROOT / "mvp" / "out"


# Crop windows on chart.jpg (1633x1869) for the three reference glyphs.
# Layout: 9 rows × 3 cols, row height ≈ 170 px; col 3 (s-row) is special in
# that it carries the s-allograph split as four sub-cells
# (printed-s | medial-ſ | final-s | capital-S). Coordinates are (y0, y1, x0, x1).
LOTH_CROPS = {
    "s-medial": (0, 195, 1100, 1380),
    "s-final": (0, 195, 1310, 1520),
    "e-medial": (680, 850, 0, 260),
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        ("s-medial", CANONICAL_DIR / "s-medial_v0.json"),
        ("s-final", CANONICAL_DIR / "s-final_v0.json"),
        ("e-medial", CANONICAL_DIR / "e-medial_v0.json"),
    ]

    chart = np.asarray(Image.open(LOTH_CHART).convert("L"))

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))

    for col, (key, path) in enumerate(files):
        tpl = template.load(path)
        template.render(tpl, ax=axes[0, col])

        y0, y1, x0, x1 = LOTH_CROPS[key]
        axes[1, col].imshow(chart[y0:y1, x0:x1], cmap="gray", vmin=0, vmax=255)
        axes[1, col].set_title(f"Loth 1866 reference  ({key})", fontsize=10)
        axes[1, col].axis("off")

    fig.suptitle("M3 Phase A — canonical templates vs. Loth reference", fontsize=14)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "canonicals-phase-a.png"
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
