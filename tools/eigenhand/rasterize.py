"""Rasterize a Bogen layout sidecar to a PIL image (grayscale, given DPI).

Not a print path — the PDF is what printers get. This exists for the
synthetic round-trip tests (render → distort → detect → rectify) and for
quick visual checks without a PDF rasterizer: it draws the same mm numbers
the PDF draws, straight from ``layout.json``, so what the importer registers
against is exactly what gets exercised.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from tools.eigenhand import geometry


def mm_to_px(mm: float, dpi: float) -> float:
    return mm * dpi / 25.4


def rasterize_layout(layout: dict, dpi: float = 300.0, ink: int = 40, paper: int = 255) -> Image.Image:
    """Draw fiducials, guide lines and box edges of a layout at the given DPI."""
    width = round(mm_to_px(layout["page_mm"]["width"], dpi))
    height = round(mm_to_px(layout["page_mm"]["height"], dpi))
    image = Image.new("L", (width, height), paper)
    draw = ImageDraw.Draw(image)

    def px(mm: float) -> float:
        return mm_to_px(mm, dpi)

    fid = layout["fiducials"]
    half = fid["size_mm"] / 2
    for corner, (cx, cy) in fid["centers_mm"].items():
        draw.rectangle([px(cx - half), px(cy - half), px(cx + half), px(cy + half)], fill=0)
        if corner == fid["donut"]:
            hole = fid["hole_mm"] / 2
            draw.rectangle([px(cx - hole), px(cy - hole), px(cx + hole), px(cy + hole)], fill=paper)

    for row in layout["rows"]:
        band = row["band_mm"]
        for box in row["boxes"]:
            x0, x1 = box["x0_mm"], box["x1_mm"]
            top = band["asc_top"] - geometry.BOX_OVERHANG_MM
            bot = band["desc_bot"] + geometry.BOX_OVERHANG_MM
            for y in (band["asc_top"], band["waist"], band["baseline"], band["desc_bot"]):
                draw.line([px(x0), px(y), px(x1), px(y)], fill=ink, width=max(1, round(px(0.25))))
            for x in (x0, x1):
                draw.line([px(x), px(top), px(x), px(bot)], fill=ink, width=max(1, round(px(0.18))))
    return image
