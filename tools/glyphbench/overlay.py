"""Rendered-vs-crop overlay PNGs — the human eye check behind the bench numbers.

The metric is a proxy; these composites are the truth: crop grayscale as
background, the rendered silhouette blended in red, the frozen reference
ink boundary drawn in blue. A good glyph shows red filling the letterform
with the blue edge hugging the red region's border.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from core.quality import mask_boundary


SILHOUETTE_RGB = np.array([220.0, 40.0, 40.0], dtype=np.float32)  # rendered template (blended 50%)
INK_BOUNDARY_RGB = np.array([40.0, 90.0, 220.0], dtype=np.float32)  # frozen reference edge (opaque)


def write_overlay_png(path: Path | str, crop: np.ndarray, pred_mask: np.ndarray, ref_mask: np.ndarray) -> None:
    """Composite one glyph's bench result into a reviewable PNG."""
    base = (np.clip(crop, 0.0, 1.0) * 255.0).astype(np.float32)
    rgb = np.repeat(base[:, :, None], 3, axis=2)
    rgb[pred_mask] = 0.5 * rgb[pred_mask] + 0.5 * SILHOUETTE_RGB
    rgb[mask_boundary(ref_mask)] = INK_BOUNDARY_RGB
    Image.fromarray(rgb.astype(np.uint8), mode="RGB").save(path)
