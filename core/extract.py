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
from scipy.ndimage import binary_fill_holes, distance_transform_edt, label
from scipy.spatial import cKDTree
from skimage.filters import threshold_local
from skimage.morphology import skeletonize


def load_grayscale(path: Path | str) -> np.ndarray:
    """Load an image as float32 in [0, 1], grayscale."""
    img = Image.open(path).convert("L")
    return np.asarray(img, dtype=np.float32) / 255.0


def binarize_adaptive(
    gray: np.ndarray, block_size: int = 51, offset: float = 0.03, fill_holes_max_area: int = 0
) -> np.ndarray:
    """Adaptive local threshold; True where the pixel is ink (darker than local).

    block_size is in pixels and forced odd. Higher offset is more conservative
    (only clearly-darker-than-local pixels count as ink) — useful on clean
    scans, dangerous on faded strokes.

    `fill_holes_max_area > 0` additionally fills interior background specks up to
    that area (per-glyph opt-in; see `fill_small_holes`); 0 leaves the mask as-is.
    """
    block = block_size if block_size % 2 == 1 else block_size + 1
    threshold = threshold_local(gray, block_size=block, method="gaussian", offset=offset)
    mask = gray < threshold
    return fill_small_holes(mask, fill_holes_max_area)


def fill_small_holes(mask: np.ndarray, max_area: int) -> np.ndarray:
    """Fill interior background specks (holes fully enclosed by ink) up to
    `max_area` px², leaving genuine counters (loops) open.

    A scanned solid stroke often carries paper-coloured pinholes — a faded fleck
    in an otherwise uniformly black letter. Each punches a spurious loop into the
    skeleton and, because the distance transform then reads the hole as nearby
    background, locally *under*-measures the stroke width there. Filling only the
    small enclosed holes removes the specks while a real counter (hundreds of px)
    stays open. `max_area <= 0` is a no-op, so the default pipeline is unchanged.
    """
    if max_area <= 0:
        return mask
    holes = binary_fill_holes(mask) & ~mask
    if not holes.any():
        return mask
    lbl, _ = label(holes)
    sizes = np.bincount(lbl.ravel())
    # label 0 is the (huge) non-hole region; fill components at/below the cap.
    small = np.flatnonzero(sizes <= max_area)
    small = small[small != 0]
    if small.size == 0:
        return mask
    out = mask.copy()
    out[np.isin(lbl, small)] = True
    return out


def skeleton_and_width(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Skeleton (boolean medial axis) + half-stroke-width map.

    `distance_transform_edt(mask)` returns the distance from each ink pixel
    to the nearest background pixel; on the skeleton that equals the half
    stroke width at that point.
    """
    skel = skeletonize(mask)
    width = distance_transform_edt(mask).astype(np.float32)
    return skel, width


def half_widths_on_medial_axis(
    points: np.ndarray, skel: np.ndarray, mask: np.ndarray, width_map: np.ndarray, snap_cap_px: float
) -> np.ndarray:
    """Half-width per query point, measured on the skeleton (medial axis).

    The distance transform equals the half stroke width only ON the medial
    axis; reading it at an arbitrary point under-measures by however far the
    point sits off the stroke center, and a point off the ink entirely
    degenerates to a ~1px boundary value. Snapping each point to the nearest
    skeleton pixel (within `snap_cap_px`, so a badly misaligned point cannot
    grab a different stroke across the glyph) measures the stroke the point
    meant. Points with no skeleton within the cap fall back to the nearest
    ink pixel's value rather than inventing a width.

    Known limitation: each point snaps independently (no continuity along the
    path), so a run of points straying into a loop counter can read the
    neighbouring hairline instead of the intended downstroke — a trace that
    stays on the ink always snaps to its own stroke.
    """
    points = np.asarray(points, dtype=float)
    ys, xs = np.where(skel)
    if len(ys) == 0:
        return np.zeros(len(points))
    skel_tree = cKDTree(np.column_stack([xs, ys]))
    dist, idx = skel_tree.query(points)
    hw = width_map[ys[idx], xs[idx]].astype(float)

    beyond = dist > snap_cap_px
    if np.any(beyond):
        ink_ys, ink_xs = np.where(mask)
        if len(ink_ys):
            ink_tree = cKDTree(np.column_stack([ink_xs, ink_ys]))
            _, ink_idx = ink_tree.query(points[beyond])
            hw[beyond] = width_map[ink_ys[ink_idx], ink_xs[ink_idx]]
        else:
            hw[beyond] = 0.0
    return hw
