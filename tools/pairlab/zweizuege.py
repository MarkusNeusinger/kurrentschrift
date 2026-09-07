"""The two-stroke model: a fused loop is two capsules, not one lump.

Rescue path R3 of the Kringel diagnosis (`docs/notes/
kringel-binnenflaechen-2026-09-06.md`, `tintenfolger.md` §7.9), armed with the
per-loop targets the Kringel catalogue (#556) supplies. The owner's principle
is the whole of it: **follow the ink correctly and the counters stay open** —
the plate's small loops ARE open at the plate nib, so a composed loop that runs
shut has lost something the hand had.

WHY A CORRECTION IS NEEDED AT ALL (H0, measured in #551). Where two pen strokes
run around a small counter they FUSE: between the counter and the outer edge
there is less ink than one pen stroke is thick (median local half width 0.0667
xh against a pen of 0.0968). `skeletonize` then returns the axis of the fused
LUMP rather than the two pen paths, and the medial axis of a lump sits between
the hole and the outer edge — 0.035–0.104 xh too tight in aperture. Every
consumer of that axis inherits the deficit before any fit runs: the Lotse rides
it, the Kette measures itself against it, the Laufform row is harvested from
the Kette. Three quarters of the Kette's own deficit is inherited, not made
(#551 H1: median share 0.75).

WHAT THIS MODULE DOES INSTEAD. The pen width is KNOWN (`w_pen` = 0.0968 xh, the
plate's own nib, frozen in `tools.tracebench.kringel`), so the blob can be
deconvolved rather than thinned. A Gleichzug pen of half width `w` paints the
Minkowski sum of its path with a disc of radius `w`; a point of the plate's
counter is inked exactly when some pen sample lies within `w` of it. Turned
around, that is a hard geometric statement about the pen path:

    **no pen sample may sit closer than `w_pen` to a counter the plate holds
    open** — and the corrected path is the trace pushed just far enough out to
    honour that, along the counter's own distance gradient.

That is the two-capsule union read backwards. Where the trace hugs the lump's
axis, pushing every sample to `w_pen` from the counter separates the two passes
to at least `2·w_pen`, which is exactly the separation a two-capsule union with
a surviving hole requires — and the corrected trace, stroked at `w_pen`, leaves
the WHOLE plate counter uninked by construction. The residual quantity the
model is named for is `stroke_separation`: the ink blob's width across the loop
minus `2·w_pen`, i.e. what is left over for the gap. Where it is not positive
the plate itself carries no two-stroke evidence and this module refuses rather
than inventing one (`REFUSAL_NO_COUNTER`).

WHERE IT IS ALLOWED TO ACT. Only on a counter the frozen catalogue registers as
`offen` in a size class where the INSTRUMENT decides (`klein`, `mittel`).
`wechselnd` and `punkt` loops are untouched — the plate closes those itself —
and so is `gross`, where three quarters of the hole survives any pen and a push
would be movement without a counter to gain. A glyph the catalogue does not
know, a loop rank it has no row for, or an occurrence whose plate shows no hole
gets no correction and a named refusal.

WHY IT SITS AFTER THE SOLVE. The smallest honest insertion point: `follow.py`
applies it to the assembled pen path, after the last round and before the wire
cap. It therefore changes no chain solve (Route A guard rail, §3), touches no
`core/` byte (the golden parity fixture is byte-identical by construction),
reads no Laufform row (so it cannot close the harvest fixed point #553 warns
about — the correction depends on the PLATE and the pen constant, never on the
rows it might later feed), and stays off unless asked. R4 warns in as many
words against writing an opening bonus into the fit loss before the sensor is
frozen; the sensor IS frozen now (#556 catalogue, #558 continuity), so a
post-solve geometric correction measured against it is the honest first step
and a fit term is the follow-up, not the opening move.

Report-only in the strict sense that no ruler changes: nothing here writes to
the DB, to `core/`, to a fixture root or to a rendering path.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

import numpy as np

from tools.tracebench.kringel import (
    PLATE_PEN_HALF_WIDTH_UNITS,
    catalogue_source,
    load_catalogue,
    loop_apertures,
    slot_loop_lines,
)


# The blend, at the two ends of every corrected run: `max(0, w_pen - d)` reaches
# zero with a slope of up to one, so a raw push hands the Knick sensor a tangent
# jump right where it fades out. A smoothstep over this much arc length brings
# the displacement to zero with zero slope as well, i.e. the correction meets
# the untouched path C¹ instead of merely continuously. The length is #558's own
# Knick window (half a nib) — a fade that spreads across the reading window
# cannot concentrate a turn inside it.
#
# It is a RAMP at the run ends rather than an average over the whole run for a
# measured reason: averaging the push against its own neighbours cost two thirds
# of it at the tightest point (`das`/`a`#0 reached 0.2247 of a 0.2581 target over
# three passes), while the ramp leaves the interior exact and only softens where
# the correction was already fading.
TAPER_UNITS = 0.0725

# A short arc-length average ON TOP of the ramp, against the raster: the counter
# is a pixel set at 30–35 px per x-height, so its distance field is bumpy at
# pixel scale and an exact push would copy those bumps into the pen path as
# wobble. Half the Knick window is short enough to leave the peak of the push
# standing and long enough to average two pixels of the plate.
#
# **Both lengths are stated in x-heights and the trace is sampled in points, and
# R3 (`sep07`) measured what that costs:** a Kette trace carries a sample every
# 0.0265 xh, so this window spans 1.37 samples and the ramp above 2.74 — the
# average averages one point and the fade fades over three. The arm failed the
# continuity gate for exactly that reason (1588 new Knick events), which is why
# the follower exposes both as flags: R3b runs them one rung up the same frozen
# ladder, at one nib and two nibs, so the smoothing covers the window the
# continuity sensor itself reads.
SMOOTH_UNITS = 0.0363

# How far a composed loop's centre may sit from the plate counter it is matched
# to. #551's own matching radius; #553 showed a flat window this size grabs the
# NEIGHBOUR's hole, which is why the match here is additionally one-to-one (a
# claimed counter is out) and anchored on the slot's own composed loop.
MATCH_RADIUS_UNITS = 0.45

# Within this much of the counter's centre a measured loop is taken to be THE
# loop around it rather than a neighbour; among those the widest wins, because
# rasterising two nearly touching polylines also produces slivers.
LOOP_CENTRE_TOLERANCE_UNITS = 0.10

# A plate hole below this many pixels is paper grain inside the ink, not a
# counter (#551).
MIN_COUNTER_PX = 3

# Half a pixel, and the reason the module has to name it. A distance transform
# measures from pixel CENTRE to pixel centre, so a hole's raster reading is
# half a pixel generous on each side of its true boundary — and BOTH sides of
# this arm's arithmetic have to be read the same generous way or they would
# miss each other by a pixel of the plate (0.03 xh at 30–35 px per x-height,
# larger than the tolerance the arm is judged at).
#
# The expectation is the catalogue's, verbatim: `D0_Platte = Tinte + 2·w_pen`
# with `Tinte = 2 · max EDT`, the raster reading. To land there, a pen centre
# has to sit at `w_pen + 0.5` px on the counter's own field rather than at
# `w_pen` — that is the level set at which a pen of `w_pen`, stroked on the
# same raster, leaves the hole uncovered including its half-pixel rim. Stated
# before the arm was measured, together with the reading floor it comes from
# (#551: ±0.5 px ≈ ±0.015 xh on the plate).
RASTER_HALF_PIXEL = 0.5

# Below this the trace does not DRAW the loop, and a widening term is the wrong
# instrument: a counter that was never enclosed is a topology loss, the class
# #556 puts BEFORE the aperture question and hands to the medial-axis term
# (R4). The floor is the catalogue's own splinter floor.
COLLAPSED_FLOOR_UNITS = 0.05

# How far a corrected loop may fall below its own starting aperture before the
# push is reverted. Not a tolerance on the RESULT — an acceptance rule on the
# STRUCTURE, in the same spirit as the follower's `structure_guard`: pushing
# the two branches of a loop apart can pull open the self-crossing that closes
# it, and a correction that destroys the loop it was meant to widen has to be
# rejected rather than reported as a widening. One raster step of the aperture
# measurement.
CLOSURE_TOLERANCE_UNITS = 0.0025

# Loop apertures for the REPORT are rasterised at this resolution in a window
# around the counter; the reading floor is 2/800 = 0.0025 xh, an order under the
# 0.02 xh the acceptance gate is stated at. No splinter floor is applied — a
# COLLAPSED loop has to be visible as a small number, not filtered away
# (`kringel-binnenflaechen-2026-09-06.md`, the warning attached to R1).
LOOP_RASTER_PX_PER_UNIT = 800.0

# Passes over the counters. One suffices whenever the counters of a word are
# further apart than a pen width, which is the normal case; the rest exist
# because pushing away from one counter can in principle push into another, and
# the report says how many were actually needed.
MAX_PASSES = 3

# The size classes where the instrument decides whether the loop is open, and
# the state that makes a closure a defect. Both are read off the frozen
# catalogue, never re-derived here.
DEFAULT_SIZE_CLASSES = ("klein", "mittel")
DEFAULT_STATES = ("offen",)

REFUSAL_NO_MASK = "no frozen ink mask on the case"
REFUSAL_FOREIGN_HAND = "the catalogue belongs to another hand"
REFUSAL_NO_COUNTER = "the plate shows no counter at this occurrence"
REFUSAL_CLAIMED = "the nearest plate counter belongs to another loop"
REFUSAL_INSIDE = "a pen sample sits inside the counter — no outward direction"
REFUSAL_NO_SEPARATION = "the blob carries no two-stroke separation"
REFUSAL_COLLAPSED = "the trace draws no loop here — a topology loss, not a narrow one"
REFUSAL_CLOSURE_LOST = "the push pulled the loop's own crossing open — reverted"

_BG_STRUCT = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)


def stroke_separation(blob_width_units: float, half_width_units: float = PLATE_PEN_HALF_WIDTH_UNITS) -> float:
    """What is left of a fused blob's width once both pen capsules are taken out.

    Two Gleichzug strokes of half width `w` at centre distance `s` paint a blob
    of width `s + 2w` across them, so the blob's width minus `2w` IS the
    separation of the two pen paths — and the counter between them is `s - 2w`
    wide, open exactly while `s > 2w`.

    The sign is the whole use of it: positive says the plate's ink is wide
    enough to have been written by two passes, and how far apart they ran; zero
    or negative says this blob is one stroke's worth of ink and there is no
    second pen path to recover. That is the refusal criterion for a lump the
    plate closed — the model never invents a stroke the ink does not carry.
    """
    return float(blob_width_units) - 2.0 * float(half_width_units)


@dataclass(frozen=True)
class ZweiZuegeOptions:
    """One configuration of the arm — frozen, and stamped into every artefact."""

    half_width_units: float = PLATE_PEN_HALF_WIDTH_UNITS
    size_classes: tuple[str, ...] = DEFAULT_SIZE_CLASSES
    states: tuple[str, ...] = DEFAULT_STATES
    taper_units: float = TAPER_UNITS
    smooth_units: float = SMOOTH_UNITS
    match_radius_units: float = MATCH_RADIUS_UNITS
    min_counter_px: int = MIN_COUNTER_PX
    max_passes: int = MAX_PASSES


@dataclass
class LoopCorrection:
    """One catalogue loop of one occurrence, and what the model did to it."""

    slot: int
    glyph: str | None
    loop: int
    size_class: str
    state: str
    counter_units: float | None = None  # the plate counter, read the catalogue's way (2 · max EDT)
    target_d0_units: float | None = None  # counter + 2*w_pen — the catalogue's own pen reconstruction
    # How far apart the two pen paths ran. With a counter that follows from it
    # (`counter + 2*w_pen`); without one it is `stroke_separation` of the lump's
    # measured width, and its sign is the refusal criterion.
    separation_units: float | None = None
    d0_before: float | None = None
    d0_after: float | None = None
    samples_moved: int = 0  # DISTINCT samples, not per-pass work
    passes: int = 0
    max_push_units: float = 0.0
    clamped: int = 0  # samples whose push would have left the ink and was cut short
    reason: str = ""  # empty exactly when the loop was corrected
    # `(stroke, sample)` pairs this loop has moved, so a second pass over the
    # same sample is not a second sample. Bookkeeping, never serialised.
    moved: set[tuple[int, int]] = field(default_factory=set, repr=False, compare=False)

    @property
    def corrected(self) -> bool:
        return not self.reason

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in asdict(self).items():
            if key == "moved":
                continue
            out[key] = round(value, 4) if isinstance(value, float) else value
        return out


@dataclass
class ZweiZuegeReport:
    """What the model did to ONE word — always inspectable, never silent."""

    applied: bool
    options: dict[str, Any]
    passes: int = 0
    samples_moved: int = 0
    reason: str = ""  # why nothing was applied at all
    loops: list[LoopCorrection] = field(default_factory=list)

    @property
    def corrected(self) -> list[LoopCorrection]:
        return [lp for lp in self.loops if lp.corrected]

    def as_dict(self) -> dict[str, Any]:
        return {
            "applied": self.applied,
            "options": self.options,
            "passes": self.passes,
            "samples_moved": self.samples_moved,
            "n_corrected": len(self.corrected),
            "n_refused": len(self.loops) - len(self.corrected),
            "reason": self.reason,
            "loops": [lp.as_dict() for lp in self.loops],
        }


@dataclass(frozen=True)
class PlateCounter:
    """One enclosed hole of the plate's frozen ink mask, in crop pixels."""

    label: int
    aperture_px: float
    cx: float
    cy: float
    area_px: int


def plate_counters(mask: np.ndarray, *, min_px: int = MIN_COUNTER_PX) -> tuple[np.ndarray, list[PlateCounter]]:
    """Every enclosed hole of a binarised ink mask, with its inscribed diameter.

    The background is labelled 4-connected so an 8-connected ink boundary really
    closes a hole — the same convention the aperture chain of #551/#556 measures
    with, so a counter read here is the counter the catalogue is stated on.
    """
    from scipy.ndimage import distance_transform_edt  # noqa: PLC0415 — heavy import, few call sites
    from scipy.ndimage import label as cc_label  # noqa: PLC0415

    ink = np.asarray(mask, dtype=bool)
    labels, count = cc_label(~ink, structure=_BG_STRUCT)
    if count == 0:
        return labels, []
    border = set(labels[0, :]) | set(labels[-1, :]) | set(labels[:, 0]) | set(labels[:, -1])
    edt = distance_transform_edt(~ink)
    out: list[PlateCounter] = []
    for i in range(1, count + 1):
        if i in border:
            continue
        sel = labels == i
        area = int(sel.sum())
        if area < min_px:
            continue
        dist = np.where(sel, edt, -1.0)
        idx = int(np.argmax(dist))
        cy, cx = np.unravel_index(idx, dist.shape)
        out.append(
            PlateCounter(label=i, aperture_px=2.0 * float(dist.flat[idx]), cx=float(cx), cy=float(cy), area_px=area)
        )
    return labels, out


def lump_width_units(ink_edt: np.ndarray, centre_px: tuple[float, float], *, xh_px: float, radius_px: float) -> float:
    """The fused blob's width where the plate shows NO counter, in x-heights.

    Twice the largest disc that fits inside the ink near `centre_px` — the width
    of the lump across the place a loop should have been. This is the reading
    `stroke_separation` takes the two pen capsules out of, and it is the ONLY
    evidence available once the ink has closed: with no hole there is no
    distance field to deconvolve against, so all the plate can still say is
    whether this much ink could have been written by two passes at all.
    """
    height, width = ink_edt.shape
    cx, cy = centre_px
    x0, x1 = max(0, int(cx - radius_px)), min(width, int(cx + radius_px) + 1)
    y0, y1 = max(0, int(cy - radius_px)), min(height, int(cy + radius_px) + 1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return 2.0 * float(ink_edt[y0:y1, x0:x1].max()) / xh_px


def _to_px(pts: np.ndarray, xh: float, baseline_row: float, tx: float, ty: float) -> np.ndarray:
    """Composed word units (y up, baseline 0) → crop pixels (y down)."""
    pts = np.asarray(pts, dtype=float)
    return np.stack([pts[:, 0] * xh + tx, baseline_row - pts[:, 1] * xh + ty], axis=1)


def _to_units(pts_px: np.ndarray, xh: float, baseline_row: float, tx: float, ty: float) -> np.ndarray:
    return np.stack([(pts_px[:, 0] - tx) / xh, (baseline_row + ty - pts_px[:, 1]) / xh], axis=1)


def _sample(field_2d: np.ndarray, pts_px: np.ndarray) -> np.ndarray:
    """Bilinear read of a pixel field at sub-pixel positions (edge-clamped).

    The plate stands at 30–35 px per x-height, so a pen width is barely three
    pixels: reading the distance field at the nearest pixel would quantise the
    correction to a third of its own size.
    """
    from scipy.ndimage import map_coordinates  # noqa: PLC0415

    return map_coordinates(field_2d, [pts_px[:, 1], pts_px[:, 0]], order=1, mode="nearest")


def _arc_length(pts: np.ndarray) -> np.ndarray:
    return np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])


def smooth_along_arc(disp: np.ndarray, s: np.ndarray, window: float) -> np.ndarray:
    """Arc-length moving average of a displacement field over ±`window`/2.

    Against the raster, not against the seam: weighting is by segment length
    rather than by sample count, so a densely sampled patch cannot outvote a
    sparse one, and the window is short enough (see `SMOOTH_UNITS`) that the
    peak of a push survives it.
    """
    n = len(s)
    if window <= 0.0 or n < 3:
        return disp
    half = 0.5 * window
    seg = np.diff(s)
    weight = np.concatenate([[0.0], seg]) * 0.5 + np.concatenate([seg, [0.0]]) * 0.5
    weight = np.maximum(weight, np.finfo(float).tiny)
    inside = np.abs(s[:, None] - s[None, :]) <= half
    w = inside * weight[None, :]
    total = w.sum(axis=1, keepdims=True)
    return (w @ disp) / np.where(total > 0, total, 1.0)


def end_ramp(hot: np.ndarray, s: np.ndarray, taper: float) -> np.ndarray:
    """A C¹ fade over the last `taper` of arc at BOTH ends of every hot run.

    `3t² − 2t³` on the normalised distance from the run's own end: one at the
    heart of the run, zero AND flat where it meets the untouched path. The push
    itself already reaches zero there, so the product leaves with a vanishing
    first derivative — which is exactly what keeps the seam out of the Knick
    sensor's reading while the interior of the run stays uncorrected-for.
    """
    ramp = np.zeros(len(s))
    if not hot.any():
        return ramp
    edges = np.flatnonzero(np.diff(np.concatenate([[False], hot, [False]]).astype(int)))
    for start, stop in zip(edges[::2], edges[1::2], strict=True):
        span = slice(int(start), int(stop))
        s_run = s[span]
        if taper <= 0.0:
            ramp[span] = 1.0
            continue
        t = np.clip(np.minimum(s_run - s_run[0], s_run[-1] - s_run) / taper, 0.0, 1.0)
        ramp[span] = t * t * (3.0 - 2.0 * t)
    return ramp


def _blend_window(hot: np.ndarray, s: np.ndarray, taper: float) -> tuple[int, int]:
    """The index slice the correction has to see: the hot samples plus one window.

    Working on the whole stroke would be quadratic in its length for a
    correction that touches a few samples — and would be the same answer,
    because a sample more than one window from every hot sample averages zeros.
    """
    idx = np.flatnonzero(hot)
    lo = int(np.searchsorted(s, s[idx[0]] - taper, side="left"))
    hi = int(np.searchsorted(s, s[idx[-1]] + taper, side="right"))
    return lo, min(hi, len(s))


def _clamp_into_ink(pts_px: np.ndarray, disp: np.ndarray, ink: np.ndarray) -> tuple[np.ndarray, int]:
    """Shorten a push that would leave the plate's ink, and count the cuts.

    The ink is the evidence: a pen path outside it is invention, so where the
    blob is thinner than the model needs, the correction stops at the last point
    the plate actually wrote. Bisection rather than a formula because the ink
    boundary is a raster, not a curve.
    """
    height, width = ink.shape

    def inside(p: np.ndarray) -> np.ndarray:
        yy = np.clip(np.rint(p[:, 1]).astype(int), 0, height - 1)
        xx = np.clip(np.rint(p[:, 0]).astype(int), 0, width - 1)
        return ink[yy, xx]

    bad = inside(pts_px) & ~inside(pts_px + disp)
    n_clamped = int(bad.sum())
    if not n_clamped:
        return disp, 0
    lo = np.zeros(len(pts_px))
    hi = np.ones(len(pts_px))
    for _ in range(6):
        mid = 0.5 * (lo + hi)
        ok = inside(pts_px + disp * mid[:, None])
        lo = np.where(bad & ok, mid, lo)
        hi = np.where(bad & ~ok, mid, hi)
    return disp * np.where(bad, lo, 1.0)[:, None], n_clamped


def loop_aperture_near(
    strokes_units: Sequence[Sequence[Sequence[float]]],
    centre_units: tuple[float, float],
    *,
    radius_units: float = MATCH_RADIUS_UNITS,
) -> float | None:
    """Aperture of the centreline loop around `centre_units`, or None.

    Measured in a window around the counter rather than over the whole word: the
    quantity is local, and a word-wide raster at this resolution costs a hundred
    times as much for the same number. Among the loops that sit on the counter's
    centre the WIDEST wins — two nearly touching polylines also raster into
    slivers, and the loop meant here is the one that encloses the hole.
    """
    cx, cy = centre_units
    window: list[np.ndarray] = []
    for line in strokes_units:
        pts = np.asarray(line, dtype=float)
        if len(pts) < 2:
            continue
        if np.any((np.abs(pts[:, 0] - cx) <= radius_units) & (np.abs(pts[:, 1] - cy) <= radius_units)):
            window.append(pts)
    if not window:
        return None
    loops = loop_apertures(window, px_per_unit=LOOP_RASTER_PX_PER_UNIT, floor=0.0)
    if not loops:
        return None
    on_centre = [lp for lp in loops if np.hypot(lp.cx - cx, lp.cy - cy) <= LOOP_CENTRE_TOLERANCE_UNITS]
    if on_centre:
        return float(max(on_centre, key=lambda lp: lp.d0).d0)
    best = min(loops, key=lambda lp: (lp.cx - cx) ** 2 + (lp.cy - cy) ** 2)
    if np.hypot(best.cx - cx, best.cy - cy) > radius_units:
        return None
    return float(best.d0)


def catalogue_targets(
    composed_items: Sequence[dict[str, Any]],
    catalogue: dict[str, list[dict[str, Any]]],
    counters: Sequence[PlateCounter],
    ink_edt: np.ndarray,
    *,
    xh_px: float,
    tx: float,
    ty: float,
    baseline_row: float,
    options: ZweiZuegeOptions,
) -> tuple[list[tuple[PlateCounter, LoopCorrection, tuple[float, float]]], list[LoopCorrection]]:
    """Which catalogue loops of this word have a plate counter to deconvolve.

    The loop identity is the catalogue's: the n-th loop of a slot's glyph IN
    READING ORDER, measured on the letter WITH its connectors, exactly as
    `tools.tracebench.kringel` builds it. Everything the catalogue does not
    register in scope is skipped without a row; everything in scope gets a row
    either way, so a refusal is as visible as a correction.

    Two branches, and only one of them corrects. With a counter the separation
    of the two pen paths follows from the hole (`counter + 2·w_pen`) and the
    hole's own distance field is the constraint. Without one — the plate closed
    this occurrence — all that is left is the lump's width, and
    `stroke_separation` says whether it could have been written by two passes at
    all. Even where it could, this arm refuses: with no hole there is nothing
    that says WHICH side of the lump each pass ran on, and choosing would be
    ductus invented at measurement time. The reading is recorded so a later arm
    can start from it.
    """
    radius_px = options.match_radius_units * xh_px
    claimed: set[int] = set()
    targets: list[tuple[PlateCounter, LoopCorrection, tuple[float, float]]] = []
    rows_out: list[LoopCorrection] = []
    for slot, (key, lines) in sorted(slot_loop_lines(composed_items).items()):
        rows = catalogue.get(key or "", [])
        for rank, loop in enumerate(loop_apertures(lines)):
            row = rows[rank] if rank < len(rows) else None
            if row is None or row["state"] not in options.states or row["size_class"] not in options.size_classes:
                continue
            entry = LoopCorrection(
                slot=int(slot), glyph=key, loop=rank, size_class=row["size_class"], state=row["state"]
            )
            rows_out.append(entry)
            cx_px, cy_px = _to_px(np.array([[loop.cx, loop.cy]]), xh_px, baseline_row, tx, ty)[0]
            near = sorted(counters, key=lambda c: (c.cx - cx_px) ** 2 + (c.cy - cy_px) ** 2)
            hit = next((c for c in near if np.hypot(c.cx - cx_px, c.cy - cy_px) <= radius_px), None)
            if hit is not None and hit.label in claimed:
                entry.reason = REFUSAL_CLAIMED
            elif hit is None:
                lump = lump_width_units(ink_edt, (cx_px, cy_px), xh_px=xh_px, radius_px=radius_px)
                entry.separation_units = stroke_separation(lump, options.half_width_units)
                entry.reason = REFUSAL_NO_COUNTER if entry.separation_units > 0.0 else REFUSAL_NO_SEPARATION
            else:
                claimed.add(hit.label)
                entry.counter_units = hit.aperture_px / xh_px
                entry.target_d0_units = entry.counter_units + 2.0 * options.half_width_units
                entry.separation_units = entry.target_d0_units
                targets.append((hit, entry, (float(loop.cx), float(loop.cy))))
    return targets, rows_out


def correct_word_strokes(
    strokes_units: Sequence[Sequence[Sequence[float]]],
    *,
    mask: np.ndarray | None,
    composed_items: Sequence[dict[str, Any]],
    catalogue: dict[str, list[dict[str, Any]]],
    xh_px: float,
    tx: float,
    ty: float,
    baseline_row: float,
    options: ZweiZuegeOptions | None = None,
) -> tuple[list[list[list[float]]], ZweiZuegeReport]:
    """Push the pen path off every catalogue counter it would ink, and say so.

    Returns the corrected strokes and the per-loop report. With nothing to
    correct — no mask, no counter, no catalogue loop in scope, or a push that
    rounds to nothing — the caller gets the input strokes back unchanged, so
    „switched on but nothing applied" is byte-identical to switched off.
    """
    from scipy.ndimage import distance_transform_edt  # noqa: PLC0415

    opts = options or ZweiZuegeOptions()
    report = ZweiZuegeReport(applied=False, options=asdict(opts))
    if mask is None:
        report.reason = REFUSAL_NO_MASK
        return list(strokes_units), report
    ink = np.asarray(mask, dtype=bool)
    labels, counters = plate_counters(ink, min_px=opts.min_counter_px)
    if not counters:
        report.reason = REFUSAL_NO_COUNTER
        return list(strokes_units), report

    targets, report.loops = catalogue_targets(
        composed_items,
        catalogue,
        counters,
        distance_transform_edt(ink),
        xh_px=xh_px,
        tx=tx,
        ty=ty,
        baseline_row=baseline_row,
        options=opts,
    )
    if not targets:
        return list(strokes_units), report

    strokes = [np.asarray(line, dtype=float) for line in strokes_units]
    # The field reads centre-to-centre, so a pen centre that leaves the raster
    # hole uncovered sits half a pixel further out (see RASTER_HALF_PIXEL).
    w_px = opts.half_width_units * xh_px + RASTER_HALF_PIXEL

    # ONE loop at a time, each with its own before/after and its own verdict.
    # Not because the loops interact much — they rarely do — but because the
    # acceptance rule below can only revert what it can attribute.
    for counter, entry, centre in targets:
        entry.d0_before = loop_aperture_near(strokes, centre, radius_units=opts.match_radius_units)
        if entry.d0_before is None or entry.d0_before < COLLAPSED_FLOOR_UNITS:
            entry.reason = REFUSAL_COLLAPSED
            entry.d0_after = entry.d0_before
            continue
        edt = distance_transform_edt(labels != counter.label)
        gy, gx = np.gradient(edt)
        snapshot = {i: line.copy() for i, line in enumerate(strokes)}
        for _pass in range(max(1, opts.max_passes)):
            entry.passes += 1
            moved_this_pass = 0
            for i, pts in enumerate(strokes):
                pts_px = _to_px(pts, xh_px, baseline_row, tx, ty)
                need = w_px - _sample(edt, pts_px)
                hot = need > 1e-9
                if not hot.any():
                    continue
                s = _arc_length(pts_px) / xh_px
                lo, hi = _blend_window(hot, s, opts.taper_units)
                sub_px, sub_need, sub_hot = pts_px[lo:hi], need[lo:hi], hot[lo:hi]
                if np.any(_sample(edt, sub_px)[sub_hot] <= 1e-9):
                    # A sample INSIDE the counter has no outward direction: the
                    # loop is a topology problem there, not an aperture one, and
                    # a guessed direction would be the knob instead of the model.
                    entry.reason = REFUSAL_INSIDE
                    break
                ux, uy = _sample(gx, sub_px), _sample(gy, sub_px)
                norm = np.hypot(ux, uy)
                unit = np.stack(
                    [
                        np.divide(ux, norm, out=np.zeros_like(ux), where=norm > 1e-9),
                        np.divide(uy, norm, out=np.zeros_like(uy), where=norm > 1e-9),
                    ],
                    axis=1,
                )
                push = np.maximum(np.where(sub_hot, sub_need, 0.0), 0.0)
                disp = (push * end_ramp(sub_hot, s[lo:hi], opts.taper_units))[:, None] * unit
                disp = smooth_along_arc(disp, s[lo:hi], opts.smooth_units)
                disp, n_clamped = _clamp_into_ink(sub_px, disp, ink)
                mag = np.hypot(disp[:, 0], disp[:, 1])
                if not np.any(mag > 1e-9):
                    continue
                moved_px = pts_px.copy()
                moved_px[lo:hi] = sub_px + disp
                strokes[i] = _to_units(moved_px, xh_px, baseline_row, tx, ty)
                entry.moved.update((i, lo + int(j)) for j in np.flatnonzero(mag > 1e-9))
                moved_this_pass += int((mag > 1e-9).sum())
                entry.clamped += n_clamped
                entry.max_push_units = max(entry.max_push_units, float(mag.max()) / xh_px)
            if entry.reason or not moved_this_pass:
                break
        entry.samples_moved = len(entry.moved)
        entry.d0_after = loop_aperture_near(strokes, centre, radius_units=opts.match_radius_units)
        # The acceptance rule. Pushing the two branches of a loop apart can pull
        # open the very self-crossing that closes it — the loop then has no
        # enclosed region at all, and the widening has destroyed what it was
        # meant to widen. That is rejected the way `structure_guard` rejects a
        # round, by reverting rather than by reporting.
        lost = entry.d0_after is None or entry.d0_after < entry.d0_before - CLOSURE_TOLERANCE_UNITS
        if entry.reason or (entry.samples_moved and lost):
            for i, line in snapshot.items():
                strokes[i] = line
            entry.reason = entry.reason or REFUSAL_CLOSURE_LOST
            entry.d0_after = entry.d0_before
            entry.samples_moved = 0
            entry.moved.clear()

    report.samples_moved = sum(entry.samples_moved for _c, entry, _p in targets)
    report.passes = max((entry.passes for _c, entry, _p in targets), default=0)
    report.applied = report.samples_moved > 0
    if not report.applied:
        return list(strokes_units), report
    return [[[float(x), float(y)] for x, y in line] for line in strokes], report


def correct_case_strokes(
    case: Any,
    result: Any,
    strokes_units: Sequence[Sequence[Sequence[float]]],
    *,
    options: ZweiZuegeOptions | None = None,
) -> tuple[list[list[list[float]]], ZweiZuegeReport]:
    """`correct_word_strokes` for a `WordCase` + its derivation — the caller's door.

    Two refusals live here rather than in the geometry: a catalogue that cannot
    be read, and a catalogue read off ANOTHER hand. The Kringel catalogue is one
    hand with one pen — `tools.tracebench.kringel.kringel_by_word` omits its own
    column on the same mismatch rather than publishing Sütterlin-1922
    expectations under a foreign name, and a correction has all the more reason
    to. Neither costs the caller its run; both cost the correction and say why.
    """
    opts = options or ZweiZuegeOptions()
    try:
        catalogue = load_catalogue()
        source = catalogue_source()
    except (OSError, ValueError) as exc:  # noqa: BLE001 — a missing catalogue is a refusal, not a crash
        return list(strokes_units), ZweiZuegeReport(
            applied=False, options=asdict(opts), reason=f"catalogue unavailable ({type(exc).__name__}: {exc})"
        )
    measured_on = str((source.get("measured_on") or [{}])[0].get("name", ""))
    origin = str(getattr(case, "origin", "") or "").split(":", 1)[-1]
    if measured_on != origin:
        return list(strokes_units), ZweiZuegeReport(
            applied=False,
            options=asdict(opts),
            reason=f"{REFUSAL_FOREIGN_HAND}: catalogue on {measured_on or '?'}, case from {origin or '?'}",
        )
    return correct_word_strokes(
        strokes_units,
        mask=getattr(case, "mask", None),
        composed_items=result.composed["items"],
        catalogue=catalogue,
        xh_px=float(result.xh_px),
        tx=float(result.registration["tx"]),
        ty=float(result.registration["ty"]),
        baseline_row=float(result.baseline_row),
        options=opts,
    )
