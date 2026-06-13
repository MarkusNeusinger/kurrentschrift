#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow", "numpy", "scipy", "potracer"]
# ///
"""Vectorise the Sütterlin 1922 Ausgangsschrift chart into a crisp SVG.

The public-domain DNB scan (`chart.jpg`, 1614x1300) is fairly low resolution and
shows JPEG block noise, so it looks pixelated when zoomed in the admin chart
view. This script traces it to a resolution-independent SVG that renders sharply
at any zoom while keeping the *exact* 1614x1300 coordinate space (the SVG
`viewBox` equals the JPEG dimensions), so every stored bbox / mask / guide / slant
coordinate stays valid.

The SVG is a purely mechanical reproduction of public-domain geometry (Otsu
threshold + Potrace), so it carries the same PD status as the source scan and
adds no new copyright. It is a *display* asset only: the measurement pipeline
keeps reading the original `chart.jpg` (see `core/chart.py`), so geometry/ink
fidelity stays anchored to the authentic scan.

Sütterlin is a Gleichzug script (uniform stroke width, no Schwellzug), so a flat
binarisation loses no stroke-width information here.

Run from anywhere:  ``uv run data/sources/suetterlin-1922/vectorize_chart.py``
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import potrace
from PIL import Image
from scipy.ndimage import median_filter


HERE = Path(__file__).resolve().parent
SRC = HERE / "chart.jpg"
OUT = HERE / "chart.svg"

# Potrace tuning: turdsize drops specks <= 2px (scan dust), alphamax/opttolerance
# control corner detection and curve optimisation — these defaults reproduce the
# letterforms faithfully without over-smoothing.
TURDSIZE = 2
ALPHAMAX = 1.0
OPTTOLERANCE = 0.2
INK_FILL = "#1a1a1a"  # match the scan's near-black ink, not pure #000


def otsu_threshold(values: np.ndarray) -> int:
    """Classic Otsu between-class-variance threshold over a 0..255 array."""
    hist, _ = np.histogram(values, bins=256, range=(0, 256))
    total = values.size
    sum_all = float(np.dot(np.arange(256), hist))
    w_back = 0.0
    sum_back = 0.0
    best_var = 0.0
    threshold = 127
    for i in range(256):
        w_back += hist[i]
        if w_back == 0:
            continue
        w_fore = total - w_back
        if w_fore == 0:
            break
        sum_back += i * hist[i]
        mean_back = sum_back / w_back
        mean_fore = (sum_all - sum_back) / w_fore
        between = w_back * w_fore * (mean_back - mean_fore) ** 2
        if between > best_var:
            best_var = between
            threshold = i
    return threshold


def trace_to_svg_path(bitmap: np.ndarray) -> str:
    """Trace a boolean bitmap with Potrace and emit one SVG path `d` string."""
    path = potrace.Bitmap(bitmap).trace(turdsize=TURDSIZE, alphamax=ALPHAMAX, opttolerance=OPTTOLERANCE)
    segments: list[str] = []
    for curve in path:
        start = curve.start_point
        d = f"M{start.x:.2f} {start.y:.2f} "
        for seg in curve:
            if seg.is_corner:
                d += f"L{seg.c.x:.2f} {seg.c.y:.2f} L{seg.end_point.x:.2f} {seg.end_point.y:.2f} "
            else:
                d += (
                    f"C{seg.c1.x:.2f} {seg.c1.y:.2f} "
                    f"{seg.c2.x:.2f} {seg.c2.y:.2f} "
                    f"{seg.end_point.x:.2f} {seg.end_point.y:.2f} "
                )
        segments.append(d + "Z")
    return " ".join(segments)


def main() -> None:
    img = Image.open(SRC).convert("L")
    width, height = img.size
    arr = median_filter(np.asarray(img, dtype=np.float32), size=3)  # kill JPEG block speckle
    threshold = otsu_threshold(arr)

    # Potrace fills the complement of its truthy region, so feed it the paper
    # mask (~ink); the resulting filled curves are the ink strokes. Verified by
    # render brightness (correct = mostly white page, ink ~16% coverage).
    paper = arr >= threshold
    d = trace_to_svg_path(paper)

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
        f'<path fill="{INK_FILL}" fill-rule="evenodd" d="{d}"/>'
        "</svg>"
    )
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT} ({len(svg)} bytes) from {SRC.name} {width}x{height}, otsu={threshold}")


if __name__ == "__main__":
    main()
