"""Render the M3 Phase A canonicals side-by-side with their Loth-1866 reference.

Per-glyph rows (one glyph per row, three columns):
  - Col 1: Loth chart crop pure — the original ink as the reference.
  - Col 2: Loth crop + M0 skeleton (red) + the canonical's pixel anchors
    (gold dots, connected by a thin line). Diagnoses whether the captured
    stroke actually follows the ink.
  - Col 3: the rendered canonical template (centerline + Schwellzug).
    What the trace produced as a geometric primitive.

Reading left-to-right per row gives "original → measurement → result",
making it easy to localise where things went wrong: bad crop, bad
anchor placement, or a clean trace.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from mvp import template
from mvp.extract import binarize_adaptive, skeleton_and_width
from mvp.tools.loth import CANONICAL_DIR, OUTPUT_DIR, REPO_ROOT, crop_with_excludes, load_bboxes, load_chart_grayscale


def _draw_loth_pure(ax, crop: np.ndarray, key: str) -> None:
    ax.imshow(crop, cmap="gray", vmin=0, vmax=1)
    ax.set_title(f"Loth 1866 — {key}", fontsize=10)
    ax.axis("off")


def _draw_loth_with_anchors(ax, crop: np.ndarray, bbox: dict, canonical_path: Path, key: str) -> None:
    mask = binarize_adaptive(crop)
    skel, _ = skeleton_and_width(mask)
    overlay = np.stack([crop, crop, crop], axis=-1)
    overlay[skel] = [1.0, 0.1, 0.1]
    ax.imshow(overlay)
    ax.set_title(f"Skelett (rot) + Anker (gold) — {key}", fontsize=10)
    ax.axis("off")

    if not canonical_path.exists():
        return
    data = json.loads(canonical_path.read_text(encoding="utf-8"))
    trace = data.get("_trace")
    if trace is None or "pixel_anchors" not in trace:
        return
    anchors_global = np.array(trace["pixel_anchors"])
    anchors_local = anchors_global - np.array([bbox["x0"], bbox["y0"]])
    ax.plot(anchors_local[:, 0], anchors_local[:, 1], "-", color="gold", lw=0.8, alpha=0.7, zorder=4)
    ax.plot(anchors_local[:, 0], anchors_local[:, 1], "o", color="gold", markersize=6, markeredgecolor="black", markeredgewidth=0.6, zorder=5)


def _draw_canonical(ax, canonical_path: Path, key: str) -> None:
    if not canonical_path.exists():
        ax.text(0.5, 0.5, f"kein Canonical für {key}", ha="center", va="center", fontsize=10, color="gray", transform=ax.transAxes)
        ax.axis("off")
        return
    tpl = template.load(canonical_path)
    template.render(tpl, ax=ax)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        ("s-medial", CANONICAL_DIR / "s-medial_v0.json"),
        ("s-final", CANONICAL_DIR / "s-final_v0.json"),
        ("e-medial", CANONICAL_DIR / "e-medial_v0.json"),
    ]

    chart_gray = load_chart_grayscale()
    bboxes = load_bboxes()

    n_rows = len(files)
    fig, axes = plt.subplots(n_rows, 3, figsize=(15, 4.5 * n_rows))
    if n_rows == 1:
        axes = np.array([axes])  # normalise to 2D indexing

    for row, (key, path) in enumerate(files):
        bbox = bboxes.get(key)
        if bbox is None:
            for col in range(3):
                axes[row, col].text(0.5, 0.5, f"keine Bbox für {key}", ha="center", va="center", fontsize=10, color="gray", transform=axes[row, col].transAxes)
                axes[row, col].axis("off")
            continue

        crop = crop_with_excludes(chart_gray, bbox, fill=1.0)
        _draw_loth_pure(axes[row, 0], crop, key)
        _draw_loth_with_anchors(axes[row, 1], crop, bbox, path, key)
        _draw_canonical(axes[row, 2], path, key)

    fig.suptitle("Canonicals-Vorschau — pro Glyph: Loth pur · Skelett+Anker · Canonical", fontsize=13)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "canonicals-phase-a.png"
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
