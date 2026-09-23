"""What the strip follower is handed — three opt-in input stages, pure arithmetic.

The Tintenpfad (`tools.pairlab.tintenpfad`, the standard follower since A45)
was tuned on plate crops: no printed text inside the crop, 28–33 px per
x-height, a lineature measured per word. A word box cut out of a written
Streifen differs on all three counts, and the diagnosis of 2026-09-24 found
each of them in the Bahnen it produced: the printed labels ridden as ink, the
pixel-denominated prices acting at 0.44× their plate reach, and the seed laid
on the PRINTED ruling where the hand wrote narrower and higher.

So the decoder stays the plate's and its INPUT is adapted, in three separate
stages that `tools.eigenhand.pfad` switches on one by one (all off is the
standard path, byte for byte):

1. LABEL ZONES. The printed strip id, provenance line and word labels are
   cleared from the binarised mask — after binarisation, so the grey crop is
   never painted and the adaptive threshold does not move — by the plate
   reference's own exclude mechanism (`core.word_metric.clear_excluded`). The
   crop rectangle and the stored frame stay what they were.
2. PLATE SCALE. A crop whose printed x-height lies outside the plate's range
   is resampled to the plate's median px per x-height, and the Bahn is mapped
   back into strip pixels exactly (`CropToStrip`).
3. SEED REGISTRATION, anisotropic: the vertical scale and the baseline from
   the modes of the skeleton's per-column extremes (calibrated against the
   plate, where the same estimator reads a known lineature), the horizontal
   scale from the ink's width against the composed word's. Two numbers, never
   one: a uniform fit absorbs the width and lifts the baseline as a side
   effect, which is how the diagnosis first misread this hand.

Stages 1 and 2 are no-ops on plate input by construction — a plate crop
carries no printed text and lies inside the plate's range. Stage 3 is a
registration and moves every seed it touches.

What is here is the pure half. The composition the third stage needs a width
from lives in `tools`, which `core` must never import, so the caller measures
that width and hands it in.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from core.eigenhand.crop import px_per_mm
from core.eigenhand.pfad import XH_NOMINAL_TOLERANCE


# A rectangle in pixels, [x0, x1) × [y0, y1) — the slice-bound shape
# `core.word_metric.clear_excluded` takes.
Zone = tuple[int, int, int, int]


# --------------------------------------------------------- stage 1: label zones

# The printed text box around a label's baseline, as fractions of its size:
# Helvetica's ascender is 0.718 and its descender 0.207 of the size, both
# rounded up so a glyph's antialiased rim stays inside.
LABEL_ASCENT = 0.75
LABEL_DESCENT = 0.22
# Printer spread and the scan's registration error, on every side.
LABEL_PAD_MM = 0.5


def label_zones_px(
    layout: Mapping[str, Any],
    layout_row: Mapping[str, Any],
    crop_origin_mm: Sequence[float],
    width_px: int,
    height_px: int,
) -> list[Zone]:
    """Every printed text of the Bogen inside this row's Schnittband, in the strip's pixels.

    Read off `core.eigenhand.bogen.page_primitives` — the very call the PDF is
    drawn from — so there is no second copy of where the printer put a label.
    On a written strip that is the strip id, the provenance line beside it and
    the word labels under the boxes.

    A row without a Schnittband has no strip pixels to place a zone in, and
    no box of it can be followed either (`frame_for_box` refuses it), so it
    has no zones rather than a refusal of its own.
    """
    from core.eigenhand.bogen import page_primitives
    from core.eigenhand.pdfgen import helv_width_mm

    cut = layout_row.get("cut_mm") or []
    if len(cut) < 4:
        return []
    _rects, _lines, texts = page_primitives(dict(layout))
    cx0, cy0, cx1, cy1 = (float(v) for v in cut)
    scale = px_per_mm(width_px, cut)
    ox, oy = (float(v) for v in crop_origin_mm[:2])
    zones: list[Zone] = []
    for text in texts:
        x0, x1 = text.x, text.x + helv_width_mm(text.text, text.size_mm)
        y0, y1 = text.y - LABEL_ASCENT * text.size_mm, text.y + LABEL_DESCENT * text.size_mm
        if x1 < cx0 or x0 > cx1 or y1 < cy0 or y0 > cy1:
            continue
        x0, y0, x1, y1 = x0 - LABEL_PAD_MM, y0 - LABEL_PAD_MM, x1 + LABEL_PAD_MM, y1 + LABEL_PAD_MM
        # Rounded OUTWARD: a zone is a slice bound, and a label pixel left on
        # its rim is a stub of foreign ink the skeleton would keep.
        zones.append(
            (
                max(0, math.floor((x0 - ox) * scale)),
                max(0, math.floor((y0 - oy) * scale)),
                min(width_px, math.ceil((x1 - ox) * scale)),
                min(height_px, math.ceil((y1 - oy) * scale)),
            )
        )
    return zones


def zones_in_crop(zones: Iterable[Sequence[int]], rect: Sequence[int]) -> list[Zone]:
    """Strip-pixel zones in a word crop's own pixels. Not clamped — `clear_excluded` clamps."""
    x0, y0 = int(rect[0]), int(rect[1])
    return [(int(a) - x0, int(b) - y0, int(c) - x0, int(d) - y0) for a, b, c, d in zones]


def ink_of(crop: np.ndarray, zones: Sequence[Zone] = ()) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Mask, skeleton and half-width map of a crop, with the printed zones cleared.

    The plate reference's order exactly (`core.word_metric.specimen_reference`):
    binarise the UNPAINTED crop, clear the zones — every pixel inside, and every
    component at least half inside whole, so a label's descender poking out of
    its box does not survive as a stub — then despeckle and skeletonise. With no
    zones this is the standard strip mask, bit for bit.
    """
    from core.extract import binarize_adaptive, skeleton_and_width
    from core.word_metric import clear_excluded, despeckle

    mask = despeckle(clear_excluded(binarize_adaptive(np.asarray(crop, dtype=np.float64)), list(zones)))
    skel, width_map = skeleton_and_width(mask)
    return mask, skel, width_map


# --------------------------------------------------------- stage 2: plate scale

# The plate's own resolution, measured over the 63 frozen plate words of root
# c7f2efd9cf37 (`baseline_y − midband_y`): median 31.0, range 28–33. Inside that
# range nothing is resampled — which is what makes the stage a no-op on every
# plate word by construction.
PLATE_XH_PX = 31.0
PLATE_XH_RANGE_PX = (28.0, 33.0)


def plate_factor(xh_px: float) -> float | None:
    """The resampling factor for a crop of this printed x-height, None inside the plate's range."""
    if not xh_px > 0:
        raise ValueError(f"an x-height of {xh_px} px has no scale to resample from")
    lo, hi = PLATE_XH_RANGE_PX
    if lo <= xh_px <= hi:
        return None
    return PLATE_XH_PX / xh_px


def resample_to_plate(crop: np.ndarray, xh_px: float) -> tuple[np.ndarray, float, float] | None:
    """The crop at the plate's px per x-height, with its exact per-axis factors — or None.

    Lanczos on the float plane, clipped back to [0, 1]. The target size is
    rounded per axis, so the two factors the pixels actually moved by
    (`width′/width`, `height′/height`) differ from the nominal one in the
    fourth digit; those are the ones handed back, because they are the ones
    every coordinate has to be mapped with.
    """
    factor = plate_factor(xh_px)
    if factor is None:
        return None
    from PIL import Image

    plane = np.asarray(crop, dtype=np.float64)
    height, width = plane.shape
    width_to, height_to = int(round(width * factor)), int(round(height * factor))
    small = np.asarray(
        Image.fromarray(plane.astype(np.float32)).resize((width_to, height_to), Image.Resampling.LANCZOS),
        dtype=np.float64,
    ).clip(0.0, 1.0)
    return small, width_to / width, height_to / height


def scale_zones(zones: Iterable[Sequence[int]], fx: float, fy: float) -> list[Zone]:
    """Zones in a resampled crop: slice bounds scale as pixel EDGES, rounded outward."""
    return [(math.floor(a * fx), math.floor(b * fy), math.ceil(c * fx), math.ceil(d * fy)) for a, b, c, d in zones]


def scale_index(value: float, factor: float) -> float:
    """A row or column INDEX in a resampled crop — the pixel-centre convention."""
    return (value + 0.5) * factor - 0.5


@dataclass(frozen=True)
class CropToStrip:
    """The follower's crop pixels → the strip's pixels, and back.

    `x_strip = (x + ½)/fx − ½ + x0` — the inverse of the pixel-centre mapping
    the crop was resampled with, then the crop's origin in the strip. Without
    resampling (`fx = fy = 1`) it is the plain offset `_entry` always added,
    computed the same way so the standard path stays byte-identical.
    """

    x0: int
    y0: int
    fx: float = 1.0
    fy: float = 1.0

    @property
    def resampled(self) -> bool:
        return self.fx != 1.0 or self.fy != 1.0

    def to_strip(self, points: Any) -> np.ndarray:
        out = np.asarray(points, dtype=float).reshape(-1, 2).copy()
        if self.resampled:
            out[:, 0] = (out[:, 0] + 0.5) / self.fx - 0.5
            out[:, 1] = (out[:, 1] + 0.5) / self.fy - 0.5
        return out + np.array([self.x0, self.y0], dtype=float)

    def to_crop(self, points: Any) -> np.ndarray:
        out = np.asarray(points, dtype=float).reshape(-1, 2) - np.array([self.x0, self.y0], dtype=float)
        if self.resampled:
            out[:, 0] = scale_index(out[:, 0], self.fx)
            out[:, 1] = scale_index(out[:, 1], self.fy)
        return out

    def stored_frame(
        self, strokes: Sequence[Sequence[Sequence[float]]], registration: Mapping[str, Any], xh_px: float
    ) -> tuple[Sequence[Sequence[Sequence[float]]], dict[str, float], float]:
        """A follower result registered on the crop, re-expressed in the STRIP's frame.

        The stored contract is one x-height for both axes (`px = (u·xh + tx,
        baseline_row − v·xh)`), and a resampled crop moved by two factors that
        differ in the fourth digit. So the vertical one sets the x-height and
        the strokes' x absorbs the rest (`u · fy/fx`): the strip pixels a
        reader maps the stored row to are then exactly the ones the Bahn was
        followed at — no rounding in here; the caller rounds the registration
        the way it always has. Unresampled, the strokes come back untouched.
        """
        tx, ty = float(registration["tx"]), float(registration.get("ty", 0.0))
        baseline = float(registration["baseline_row"])
        if not self.resampled:
            return strokes, {"tx": tx + self.x0, "ty": ty, "baseline_row": baseline + self.y0}, float(xh_px)
        stretch = self.fy / self.fx
        rescaled = [[[float(point[0]) * stretch, float(point[1])] for point in stroke] for stroke in strokes]
        frame = {
            "tx": (tx + 0.5) / self.fx - 0.5 + self.x0,
            "ty": ty / self.fy,
            "baseline_row": (baseline + 0.5) / self.fy - 0.5 + self.y0,
        }
        return rescaled, frame, float(xh_px) / self.fy


# ------------------------------------------------- stage 3: seed registration


@dataclass(frozen=True)
class ModeCalibration:
    """What the mode estimator reads on a lineature that is known to be right.

    `ratio` is the median of (baseline mode − waist mode) / x-height, `offset_xh`
    the median of (baseline mode − true baseline) / x-height. The estimator is
    biased — a pointed hand's bottoms cluster on the baseline, its waist does
    not — so a reading on the hand is divided through by what the same
    estimator reads on the plate.
    """

    ratio: float
    offset_xh: float


# Measured over the 63 frozen plate words of root c7f2efd9cf37 against their
# own lineature (n = 63, no unreadable word): 0.642857… = 9/14 and −0.166…
# = −1/6, i.e. −5.17 px at 31 px per x-height. Recompute with
# `mode_calibration` over `tools.wordlab.cases.iter_fixture_word_cases`; a
# re-exported root that moves these digits moves every stage-3 seed with it.
PLATE_MODE_CALIBRATION = ModeCalibration(ratio=0.6428571428571429, offset_xh=-0.16666666666666666)

# A registered x-height or width outside these factors of the printed one is
# not a hand this Bogen could have been written in: the API refuses an x-height
# past the same tolerance (`core.eigenhand.pfad.XH_NOMINAL_TOLERANCE`), so a
# seed moved that far would produce a Bahn nobody can store. Such a reading
# falls back to the identity — never clamped, because a clamped registration is
# a number nothing measured.
SEED_SCALE_BOUNDS = (1.0 / XH_NOMINAL_TOLERANCE, XH_NOMINAL_TOLERANCE)


def skeleton_modes(skel: np.ndarray, xh_px: float, baseline_row: float) -> tuple[float, float]:
    """Baseline and waist as the MODES of the skeleton's per-column lowest and highest pixel.

    A pointed hand's bottoms are the lowest skeleton pixel of their column and
    cluster on one row; columns whose lowest pixel sits on a diagonal spread
    over a band. A histogram peak therefore reads the baseline where a median
    does not, and the same holds for the waist on the highest pixel.

    Columns are the inked ones, trimmed to their 5–95 % range (the entry and
    exit strokes are not the body). The baseline is looked for within ±0.4 xh
    of `baseline_row`, the waist between 1.4 and 0.4 xh above it (ascenders
    excluded); both histograms are smoothed by σ = max(1, 0.03·xh) px. A window
    holding fewer than five columns reads NaN — unreadable, not zero.

    `baseline_row` and the returned rows are the crop's own.
    """
    from scipy.ndimage import gaussian_filter1d

    cols = np.nonzero(skel.any(axis=0))[0]
    lo, hi = np.percentile(cols, [5, 95]).astype(int)
    cols = cols[(cols >= lo) & (cols <= hi)]
    bottoms = np.array([np.nonzero(skel[:, c])[0].max() for c in cols])
    tops = np.array([np.nonzero(skel[:, c])[0].min() for c in cols])

    def peak(values: np.ndarray, win_lo: float, win_hi: float) -> float:
        inside = values[(values >= win_lo) & (values <= win_hi)]
        if len(inside) < 5:
            return float("nan")
        hist = np.bincount(inside - int(win_lo), minlength=int(win_hi - win_lo) + 1).astype(float)
        hist = gaussian_filter1d(hist, max(1.0, 0.03 * xh_px))
        return float(np.argmax(hist) + int(win_lo))

    baseline = peak(bottoms, baseline_row - 0.4 * xh_px, baseline_row + 0.4 * xh_px)
    waist = peak(tops, baseline_row - 1.4 * xh_px, baseline_row - 0.4 * xh_px)
    return baseline, waist


def mode_calibration(samples: Iterable[tuple[np.ndarray, float, float]]) -> tuple[ModeCalibration, int, int]:
    """The estimator's reading over words whose lineature is right: (calibration, n, unreadable).

    `samples` are (skeleton, x-height px, baseline row in the skeleton's frame).
    NaN readings are left out of the medians and counted.
    """
    ratios: list[float] = []
    offsets: list[float] = []
    for skel, xh_px, baseline_row in samples:
        baseline, waist = skeleton_modes(np.asarray(skel, dtype=bool), float(xh_px), float(baseline_row))
        ratios.append((baseline - waist) / xh_px)
        offsets.append((baseline - baseline_row) / xh_px)
    unreadable = int(np.isnan(ratios).sum() + np.isnan(offsets).sum())
    return ModeCalibration(float(np.nanmedian(ratios)), float(np.nanmedian(offsets))), len(ratios), unreadable


@dataclass(frozen=True)
class SeedRegistration:
    """Where stage 3 puts the seed: the case's lineature rows and the composition's x scale.

    `applied` False is the identity — the rows handed in and `x_scale` 1 — with
    `reason` saying why; `readings` carries what was measured either way.
    """

    baseline_y: int
    midband_y: int
    x_scale: float
    applied: bool
    reason: str | None = None
    readings: dict[str, float] = field(default_factory=dict)


def register_seed(
    skel: np.ndarray,
    baseline_y: int,
    midband_y: int,
    row_offset: int,
    composed_width_units: float,
    calibration: ModeCalibration = PLATE_MODE_CALIBRATION,
    bounds: tuple[float, float] | None = SEED_SCALE_BOUNDS,
) -> SeedRegistration:
    """Stage 3: the hand's own lineature and width, measured off its ink.

    `baseline_y` / `midband_y` are the case's rows (the printed ruling) and
    `row_offset` is where the skeleton's row 0 lies in that frame (a strip
    crop: 0; a plate crop: its rectangle's top). `composed_width_units` is the
    x-extent of the composed seed in x-heights — measured by the caller, the
    composer lives in `tools`.

    sy: x-height = (baseline mode − waist mode) / `calibration.ratio`, baseline
    = baseline mode − `calibration.offset_xh` · x-height. sx: k = ink width /
    (composed width · registered x-height) — the factor the composition's x has
    to be multiplied by for the seed to span the ink.

    Falls back to the identity where the modes are unreadable (too few columns
    in a window, no ink, a waist at or below the baseline), and — with
    `bounds` — where sy or k leaves them. `bounds=None` applies any reading.
    """
    xh_printed = float(baseline_y - midband_y)
    baseline_crop = float(baseline_y - row_offset)
    ink = np.asarray(skel, dtype=bool)

    def identity(reason: str, **readings: float) -> SeedRegistration:
        return SeedRegistration(baseline_y, midband_y, 1.0, False, reason, dict(readings))

    if xh_printed <= 0 or not ink.any():
        return identity("no ink or no lineature to register against")
    baseline_mode, waist_mode = skeleton_modes(ink, xh_printed, baseline_crop)
    if not (math.isfinite(baseline_mode) and math.isfinite(waist_mode)):
        return identity("modes unreadable", baseline_mode=baseline_mode, waist_mode=waist_mode)
    if baseline_mode - waist_mode <= 0:
        return identity("waist mode at or below the baseline mode", baseline_mode=baseline_mode, waist_mode=waist_mode)
    xh_hand = (baseline_mode - waist_mode) / calibration.ratio
    baseline_hand = baseline_mode - calibration.offset_xh * xh_hand
    registered_baseline = int(round(baseline_hand + row_offset))
    registered_midband = int(round(baseline_hand - xh_hand + row_offset))
    xh_registered = float(registered_baseline - registered_midband)
    cols = np.nonzero(ink.any(axis=0))[0]
    ink_width = float(cols.max() - cols.min())
    readings = {
        "baseline_mode": baseline_mode,
        "waist_mode": waist_mode,
        "xh_printed": xh_printed,
        "xh_hand": xh_hand,
        "baseline_hand": baseline_hand,
        "xh_registered": xh_registered,
        "sy": xh_registered / xh_printed,
        "baseline_shift_px": float(registered_baseline - baseline_y),
        "ink_width_px": ink_width,
        "composed_width_units": float(composed_width_units),
    }
    if xh_registered <= 0 or ink_width <= 0 or not composed_width_units > 0:
        return identity("no width to scale by", **readings)
    k = ink_width / (composed_width_units * xh_registered)
    readings["k"] = k
    if bounds is not None:
        lo, hi = bounds
        if not (lo <= readings["sy"] <= hi and lo <= k <= hi):
            return identity(f"sy {readings['sy']:.3f} or k {k:.3f} outside [{lo:g}, {hi:g}]", **readings)
    return SeedRegistration(registered_baseline, registered_midband, k, True, None, readings)


def scale_composed_x(composed: Mapping[str, Any], k: float) -> dict[str, Any]:
    """A composed word with every x multiplied by `k` about the unit origin — stage 3's sx.

    Applied AFTER composition, so the generated joins keep the shape the
    composer gave them and are only stretched with their letters. Every drawn
    coordinate moves (`centerline`, `rings`) together with the horizontal
    bounds; nothing else in the payload is an x the seed reads.
    """
    items = []
    for item in composed["items"]:
        item = dict(item)
        if item.get("centerline") is not None:
            item["centerline"] = [[float(x) * k, float(y)] for x, y in item["centerline"]]
        if item.get("rings") is not None:
            item["rings"] = [[[float(x) * k, float(y)] for x, y in ring] for ring in item["rings"]]
        items.append(item)
    bounds = dict(composed.get("bounds") or {})
    for key in ("min_x", "max_x"):
        if key in bounds:
            bounds[key] = bounds[key] * k
    return {**composed, "items": items, "bounds": bounds}
