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

import json
from pathlib import Path

import cairosvg
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from mvp import template


REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DIR = REPO_ROOT / "mvp" / "canonical"
LOTH_SVG = REPO_ROOT / "data" / "sources" / "loth-1866" / "chart.svg"
BBOXES_JSON = CANONICAL_DIR / "loth_bboxes.json"
OUTPUT_DIR = REPO_ROOT / "mvp" / "out"
SVG_RENDER_PATH = OUTPUT_DIR / "chart-svg-render-white.png"


def load_bboxes() -> dict[str, tuple[int, int, int, int] | None]:
    """Read the editable bbox table; missing/null entries become None."""
    data = json.loads(BBOXES_JSON.read_text(encoding="utf-8"))
    out: dict[str, tuple[int, int, int, int] | None] = {}
    for name, bbox in data["bboxes"].items():
        if bbox is None:
            out[name] = None
        else:
            out[name] = (bbox["y0"], bbox["y1"], bbox["x0"], bbox["x1"])
    return out


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
    bboxes = load_bboxes()

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))

    for col, (key, path) in enumerate(files):
        tpl = template.load(path)
        template.render(tpl, ax=axes[0, col])

        bbox = bboxes.get(key)
        if bbox is None:
            axes[1, col].text(0.5, 0.5, f"no bbox for {key}\nedit mvp/canonical/loth_bboxes.json", ha="center", va="center", fontsize=10, color="gray", transform=axes[1, col].transAxes)
        else:
            y0, y1, x0, x1 = bbox
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
