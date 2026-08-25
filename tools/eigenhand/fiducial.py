"""Passmarken detection — find the four corner squares in a scan or photo.

scikit-image only (OpenCV is deliberately not a dependency,
docs/reference/styleanalyse.md): Gaussian blur → Otsu threshold → connected
components → per-quadrant scoring by squareness, solidity and darkness. The
top-left mark carries a punched hole (donut), detected via the region's
Euler number — that one anchors page orientation, so an upside-down scan or
an arbitrarily rotated photo still registers correctly.

Fails loudly (with a diagnostic overlay the caller can write) when fewer
than four confident marks are found — a silent mis-registration would file
every strip of the sheet wrongly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from skimage import filters, measure


# A fiducial candidate must look like a filled square and be big enough to be
# printed geometry rather than ink: bounds relative to the image so no DPI
# knowledge is needed. A frame-filling capture puts the 8 mm square at
# (8/210)·(8/297) ≈ 1.5e-3 of the image area; the floor sits ~70× below that
# ON PURPOSE, tolerating photos where the sheet covers only a fraction of the
# frame. The ceiling rejects sheet-sized dark blobs (shadows, covers).
MIN_AREA_FRACTION = 0.2e-4
MAX_AREA_FRACTION = 60e-4
MIN_EXTENT = 0.55  # filled area / bbox area (donut hole lowers it below a solid square's)
MAX_ASPECT = 1.8


@dataclass(frozen=True)
class Mark:
    center: tuple[float, float]  # (x, y) image pixels, intensity-weighted
    area: float
    has_hole: bool
    width: float = 0.0  # bounding box, image pixels
    height: float = 0.0


class FiducialError(SystemExit):
    """Detection failed — message names what was found per quadrant."""


def _candidates(gray: np.ndarray) -> list[Mark]:
    blurred = filters.gaussian(gray, sigma=1.5)
    threshold = filters.threshold_otsu(blurred)
    dark = blurred < threshold
    labels = measure.label(dark)
    image_area = gray.shape[0] * gray.shape[1]
    marks: list[Mark] = []
    for region in measure.regionprops(labels, intensity_image=1.0 - blurred):
        area_fraction = region.area / image_area
        if not (MIN_AREA_FRACTION <= area_fraction <= MAX_AREA_FRACTION):
            continue
        height, width = region.bbox[2] - region.bbox[0], region.bbox[3] - region.bbox[1]
        aspect = max(height, width) / max(1, min(height, width))
        if aspect > MAX_ASPECT or region.extent < MIN_EXTENT:
            continue
        cy, cx = region.centroid_weighted
        marks.append(
            Mark((float(cx), float(cy)), float(region.area), region.euler_number <= 0, float(width), float(height))
        )
    return marks


def check_mark_size(corners: dict[str, Mark], expected_px: float, tolerance: float = 0.08) -> list[str]:
    """Complaints about marks that are not the size they were printed at.

    The one printer failure the rest of the chain cannot see. A page printed on
    a device whose unprintable margin eats into a Passmarke yields a mark that
    is still square and still solid — it passes every shape test above — but
    smaller, with its centroid pulled toward the page centre. The rectification
    then maps four pulled-in centroids onto their nominal millimetres and
    stretches the whole sheet, silently, for as long as that printer is used.

    What makes it detectable is that the mark SIZE and the mark SPACING are
    printed by the same device: their ratio is fixed by the layout and survives
    any uniform scaling of the page. So `expected_px` is derived from the
    measured spacing, and a mark that comes out materially smaller than that
    was clipped rather than merely photographed small.

    A uniformly scaled print (a driver's "fit to printable area") is NOT
    visible here and cannot be — every distance shrinks together. Only a ruler
    on the paper catches that one, which is why the sheet's README asks for it.
    """
    complaints = []
    for corner, mark in sorted(corners.items()):
        for axis, measured in (("width", mark.width), ("height", mark.height)):
            ratio = measured / expected_px if expected_px else 1.0
            if ratio < 1 - tolerance:
                complaints.append(
                    f"{corner} Passmarke {axis} {measured:.0f} px is {100 * (1 - ratio):.0f}% under the "
                    f"{expected_px:.0f} px its spacing implies — the print was probably clipped by the "
                    "printer's unprintable margin"
                )
    return complaints


def _quadrant(mark: Mark, shape: tuple[int, ...]) -> str:
    x, y = mark.center
    return ("t" if y < shape[0] / 2 else "b") + ("l" if x < shape[1] / 2 else "r")


def detect_fiducials(gray: np.ndarray) -> dict[str, Mark]:
    """The best mark per image quadrant, keyed tl/tr/bl/br in IMAGE orientation."""
    per_quadrant: dict[str, Mark] = {}
    for mark in _candidates(gray):
        quadrant = _quadrant(mark, gray.shape)
        best = per_quadrant.get(quadrant)
        if best is None or mark.area > best.area:
            per_quadrant[quadrant] = mark
    missing = [q for q in ("tl", "tr", "bl", "br") if q not in per_quadrant]
    if missing:
        raise FiducialError(
            f"fiducial detection failed — no confident mark in quadrant(s) {', '.join(missing)}; "
            "check lighting/contrast or crop the capture closer to the sheet"
        )
    return per_quadrant


def orient_corners(per_quadrant: dict[str, Mark]) -> dict[str, Mark]:
    """Rotate the corner assignment so the donut lands on the layout's tl.

    The four image-quadrant marks form the page corners in SOME rotation
    (0/90/180/270° — a flipped photo or a sheet fed upside down). Exactly one
    mark carries the hole; relabeling by rotation puts it top-left.
    """
    holes = [q for q, mark in per_quadrant.items() if mark.has_hole]
    if len(holes) != 1:
        raise FiducialError(
            f"orientation ambiguous — {len(holes)} donut mark(s) detected (expected exactly 1); "
            "the top-left Passmarke with the punched hole must be visible"
        )
    rotations = {
        "tl": ("tl", "tr", "bl", "br"),  # donut already top-left: identity
        "tr": ("tr", "br", "tl", "bl"),  # page rotated 90° cw in the image
        "br": ("br", "bl", "tr", "tl"),  # upside down
        "bl": ("bl", "tl", "br", "tr"),  # 90° ccw
    }[holes[0]]
    return {page: per_quadrant[image_q] for page, image_q in zip(("tl", "tr", "bl", "br"), rotations, strict=True)}
