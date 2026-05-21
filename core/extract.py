"""Two-channel ink extraction: skeleton (geometry) + half-width (Schwellzug).

Width is measured on the binarized mask via distance transform — independent
of darkness, robust to fading. The grayscale intensity channel (ink quantity
from the dip-pen refill cycle) is kept separately by callers; the routines
here operate on the binarized geometry.

See `docs/concepts/architektur.md` §5 for the two-channel separation rationale.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from skimage.filters import threshold_local
from skimage.morphology import skeletonize


def load_grayscale(path: Path | str) -> np.ndarray:
    """Load an image as float32 in [0, 1], grayscale."""
    img = Image.open(path).convert("L")
    return np.asarray(img, dtype=np.float32) / 255.0


def binarize_adaptive(gray: np.ndarray, block_size: int = 51, offset: float = 0.03) -> np.ndarray:
    """Adaptive local threshold; True where the pixel is ink (darker than local).

    block_size is in pixels and forced odd. Higher offset is more conservative
    (only clearly-darker-than-local pixels count as ink) — useful on clean
    scans, dangerous on faded strokes.
    """
    block = block_size if block_size % 2 == 1 else block_size + 1
    threshold = threshold_local(gray, block_size=block, method="gaussian", offset=offset)
    return gray < threshold


def skeleton_and_width(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Skeleton (boolean medial axis) + half-stroke-width map.

    `distance_transform_edt(mask)` returns the distance from each ink pixel
    to the nearest background pixel; on the skeleton that equals the half
    stroke width at that point.
    """
    skel = skeletonize(mask)
    width = distance_transform_edt(mask).astype(np.float32)
    return skel, width
