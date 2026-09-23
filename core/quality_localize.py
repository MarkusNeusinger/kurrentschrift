"""Where the Sütterlin naturalness metric takes its points off — the Abzugs-Linse core.

The Gleichzug metric (`core.quality_suetterlin`) answers "how good is this
letter" with one score and six deductions („Abzüge": Glätte · Senkrechte ·
Ecken · Kreuzungsflucht · Doppelzug · Deckungslücke). It never says WHERE on
the letter a deduction comes from, so the author reads „Ecken 0.17" and has to
guess which corner. This module answers the where, for one stored template
against its chart crop, without touching the ruler:

* the frozen metric is CALLED, unchanged, for the headline numbers — its dict is
  handed through as is, and nothing here feeds back into it;
* the per-location terms are rebuilt from the metric's own building blocks,
  private ones included (`core.quality._sample_and_rings`,
  `core.quality_suetterlin._locally_straight_mask`, the `core.geometry`
  detectors, the constants of `core.quality_suetterlin`), the way
  `core.laufform.row_naturalness` re-reads the naturalness terms without
  editing the frozen files — so a rename in the frozen modules breaks this one,
  and a re-baseline there has to be carried here (one that was not turns the
  drifted categories „ohne Ort", see below, and fails the local fixture sweep
  in `tests/test_quality_localize.py`);
* every located deduction — an Abzugsstelle — carries a value, and the values
  of one category sum to the number the metric shows for it, to its last
  (fourth) digit.

How each category splits, and how honestly:

* **Exact terms.** Ecken and Kreuzungsflucht are means over their corners and
  passages, so each site is literally `(1 − q)/N`. Doppelzug is a recall, so
  each missed ink pixel in the retrace zone is literally `1/denominator`;
  sites are the connected groups of those pixels.
* **Proportional shares.** Glätte sums per-sample `|Δ²κ|` exactly into its
  jerk, but the deduction runs through `1 − exp(−jerk/decay)`, so a sample's
  share is proportional, not marginal; sites are the scored segments between
  stroke ends and corner windows. Senkrechte is shared per run by `L·rms`.
  Deckungslücke (`1 − dice·q_chamfer·q_geo`) is split across its three factors
  in proportion to their log terms, which add exactly. Within its part, Dice
  splits per pixel and the Chamfer per boundary pixel, exactly again (both are
  linear in their pixels); the Geo splits per sample in proportion to its
  squared excess — the RMSE is the root of their mean, so that is a share,
  not a term.
* **Without a place („ohne Ort").** A Dice miss within `RIM_PX` of the other
  mask is the quantised edge of a stroke — it counts in the number but marks no
  spot worth pointing at, so it is reported as one unlocated site instead of a
  thousand one-pixel marks. Should the recomputation here ever disagree with
  the metric's own number (a ruler re-baseline this module did not follow),
  the whole category becomes one unlocated site rather than a wrong map, and
  its context (numbers, windows, zone) goes with the map. In the degenerate
  case of an empty boundary or an empty skeleton, the whole Chamfer or Geo
  part has no place either.

A row whose geometry holds a non-finite number, or whose x-height is not a
positive number, is refused with `UnscorableInputError` before anything is
measured: the metric would hand back NaN components, and a NaN has neither a
place nor four digits to add up to.

Everything is in the metric's own CROP-PIXEL frame (x right, y down, the pixel
in column c and row r centred on (c, r) — `rasterize_silhouette` samples pixel
centres at integer coordinates), because that is where the ruler measured:
the Gleichzug renderer widens round bodies at render time, so marks drawn on
the written glyph would sit beside the ink that was scored.

Each site also carries linearised score points (`points_est`) — the first-order
change of the headline score if that site's deduction vanished — for ranking
the top pins across categories. They are an estimate for ordering and detail,
never the number shown for a category.

Deterministic, no DB, no I/O beyond the chart read of the `_for_glyph` wrapper.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt, find_objects, gaussian_filter1d, label

from core.chart import crop_with_mask, load_chart_grayscale
from core.extract import binarize_adaptive, skeleton_and_width
from core.geometry import (
    acute_angle_between,
    arc_length,
    bilinear,
    detect_crossing_passages,
    detect_retrace_pairs,
    detect_vertical_runs,
    discrete_curvature,
    fit_line_tls,
    point_line_perp_distance,
    run_is_straight_residual,
    stroke_bounds,
)
from core.quality import (
    QUALITY_N_SAMPLES,
    _sample_and_rings,
    chamfer_boundary_stats,
    crop_local_anchors,
    mask_boundary,
    rasterize_silhouette,
)
from core.quality_suetterlin import (
    CHAMFER_DECAY_UNITS,
    CORNER_STRAIGHT_DECAY,
    CORNER_WINDOW_UNITS,
    CROSS_ANG_DECAY,
    CROSS_APPLY_ANGLE_DEG,
    CROSS_APPLY_OFFSET_UNITS,
    CROSS_OFF_DECAY,
    CROSS_STRAIGHT_TOL,
    CROSS_WINDOW_UNITS,
    CROSSING_MIN_ANGLE_DEG,
    CROSSING_MIN_ARC_FACTOR,
    DEAD_BAND_PX,
    GATE_EXPONENT,
    GEO_DECAY_UNITS,
    MIN_RETRACE_PAIRS,
    PROX_FLOOR_UNITS,
    PROX_NIB_FACTOR,
    RETRACE_MAX_GAP_NIB,
    RETRACE_REGION_RADIUS_NIB,
    RETRACE_STEM_STRAIGHT_TOL,
    RETRACE_STEM_WINDOW_UNITS,
    RETRACE_WINDOW_UNITS,
    SMOOTH_DECAY,
    SMOOTH_KAPPA_SIGMA,
    VERT_DECAY,
    VERTICAL_ANGLE_DEG,
    VERTICAL_MIN_LEN_UNITS,
    VERTICAL_STRAIGHT_TOL,
    W_CORNER,
    W_CROSS,
    W_RETRACE,
    W_SMOOTH,
    W_VERT,
    _locally_straight_mask,
    suetterlin_quality_metrics,
)
from core.template import stroke_slices


# The name a payload gives the metric it localizes — there is one, Gleichzug's.
METRIC_NAME = "suetterlin_naturalness"

# The six deductions, in the order the metric returns its `components`.
CATEGORIES: tuple[str, ...] = ("smoothness", "verticality", "corner", "collinearity", "retrace", "coverage")

# The metric's naturalness weights, per category (coverage is the gate, not a term).
_WEIGHTS = {
    "smoothness": W_SMOOTH,
    "verticality": W_VERT,
    "corner": W_CORNER,
    "collinearity": W_CROSS,
    "retrace": W_RETRACE,
}

# Which `applicable` count of the metric says whether a term applies at all;
# smoothness and coverage always apply.
_APPLICABLE_COUNT = {
    "verticality": "vertical_runs",
    "corner": "corners",
    "collinearity": "crossings",
    "retrace": "retrace_pairs",
}

# The scan's quantisation scale, twice the metric's own pixelation dead band.
# A Dice miss this close to the other mask is the quantised edge of a stroke —
# the first ring of pixels around the render (missed ink) or the ink (excess
# render); the chamfer forgives disagreement up to DEAD_BAND_PX on each side,
# Dice cannot, so the rim counts in the number but gets no place. The same
# scale joins pixel evidence into places (`_components`).
RIM_PX = 2.0 * DEAD_BAND_PX

# How far the κ = 0 a stroke end is given (`discrete_curvature`) reaches into
# the Glätte term: the curvature smoothing spreads it over the metric's own
# corner-block radius, and the second difference reaches one sample further.
STROKE_END_REACH = 1 + int(np.ceil(2.0 * SMOOTH_KAPPA_SIGMA)) + 1

# The number of cross-category pins the lens ranks.
PIN_COUNT = 5

# The metric reports `round(1 − q, 4)`, so a recomputation that agrees with it
# lies within half a unit of the fourth place (plus float slack).
SYNC_TOLERANCE = 0.5e-4 + 1e-9

_SHOWN_PLACES = 4
_SHOWN_UNIT = 10**_SHOWN_PLACES
_EIGHT_CONNECTED = np.ones((3, 3), dtype=bool)
_JOIN_REACH = int(np.ceil(RIM_PX))
_JOIN_DISK = np.hypot(*np.mgrid[-_JOIN_REACH : _JOIN_REACH + 1, -_JOIN_REACH : _JOIN_REACH + 1]) <= RIM_PX

Point = tuple[float, float]
Cell = tuple[int, int, int]
Numbers = dict[str, float | int | str | bool | None]


class UnscorableInputError(ValueError):
    """A stored row this module cannot localize: missing fields or non-finite geometry.

    A `ValueError`, so a caller that caught that keeps working; the route maps
    it to 409 like a row without pixel-space trace meta, instead of letting a
    NaN surface as a 500 somewhere downstream.
    """


@dataclass(frozen=True)
class SitePath:
    """A named polyline in crop pixels; `values` (if any) run along its points."""

    role: str
    points: tuple[Point, ...]
    values: tuple[float, ...] = ()


@dataclass(frozen=True)
class PenaltySite:
    """One located deduction (Abzugsstelle), or the honest unlocated rest.

    `value` is the site's part of its category's shown number, apportioned to
    four places so the parts of one category add up to that number exactly;
    `raw` is the unrounded contribution the apportionment started from. `x`/`y`
    are None for a site without a place. `cells` are pixel runs `(x, y, width)`
    in one row each, for the pixel-level categories.
    """

    category: str
    index: int
    kind: str
    value: float
    raw: float
    share: float
    exact: bool
    points_est: float
    x: float | None
    y: float | None
    numbers: Numbers
    paths: tuple[SitePath, ...] = ()
    cells: tuple[Cell, ...] = ()


@dataclass(frozen=True)
class PenaltyCategory:
    """One deduction category: the metric's number and the sites it splits into.

    `value` is the metric's own component (four places, unchanged); `raw` is
    this module's recomputation of it, and `in_sync` says whether the two
    agree. `parts` splits Deckungslücke into its three factors (four places,
    summing to `value`); `context_*` carry what is drawn around the sites
    rather than as one — the Glätte corner windows, the Doppelzug zone. A
    category out of sync keeps only its one unlocated site: `numbers`, `parts`
    and `context_*` are empty, since the recomputation behind them disagreed.
    """

    key: str
    value: float
    raw: float
    applicable: bool
    in_sync: bool
    exact: bool
    points_est: float
    sites: tuple[PenaltySite, ...]
    numbers: Numbers = field(default_factory=dict)
    parts: dict[str, float] = field(default_factory=dict)
    context_paths: tuple[SitePath, ...] = ()
    context_cells: tuple[Cell, ...] = ()


@dataclass(frozen=True)
class PenaltyPin:
    """One of the top sites across all categories, ranked by linearised points."""

    rank: int
    category: str
    index: int
    points_est: float
    x: float
    y: float


@dataclass(frozen=True)
class PenaltyMap:
    """The frozen metric's own result plus where each of its deductions sits."""

    metrics: dict
    width: int
    height: int
    unit_px: float
    centerline: tuple[tuple[Point, ...], ...]
    categories: dict[str, PenaltyCategory]
    pins: tuple[PenaltyPin, ...]


@dataclass
class _Draft:
    """A site before its category is finalised (raw value, geometry, numbers)."""

    kind: str
    raw: float
    x: float | None
    y: float | None
    numbers: Numbers
    paths: tuple[SitePath, ...] = ()
    cells: tuple[Cell, ...] = ()


# ----------------------------------------------------------------- small helpers


def _num(value: float | int | bool | str | None, places: int = 4) -> float | int | bool | str | None:
    """A JSON-safe number: numpy scalars unwrapped, floats rounded, ±inf/NaN → None."""
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, (int, np.integer)):
        return int(value)
    as_float = float(value)
    if not math.isfinite(as_float):
        return None
    return round(as_float, places)


def _pt(x: float, y: float) -> Point:
    return (round(float(x), 2), round(float(y), 2))


def _path(role: str, pts: np.ndarray, values: Sequence[float] | None = None) -> SitePath:
    points = tuple(_pt(x, y) for x, y in np.asarray(pts, dtype=float).reshape(-1, 2))
    vals = tuple(round(float(v), 6) for v in values) if values is not None else ()
    return SitePath(role=role, points=points, values=vals)


def _cells(mask: np.ndarray) -> tuple[Cell, ...]:
    """Row-wise pixel runs `(x, y, width)` of a boolean mask — compact and drawable as rects."""
    out: list[Cell] = []
    for y in np.flatnonzero(mask.any(axis=1)):
        edges = np.diff(np.concatenate([[0], mask[y].astype(np.int8), [0]]))
        starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
        out.extend((int(s), int(y), int(e - s)) for s, e in zip(starts, ends, strict=True))
    return tuple(out)


def _runs(flags: np.ndarray) -> list[tuple[int, int]]:
    """Inclusive `(lo, hi)` index ranges of the True runs of a 1-D boolean array."""
    edges = np.diff(np.concatenate([[0], np.asarray(flags, dtype=np.int8), [0]]))
    return [(int(s), int(e) - 1) for s, e in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1), strict=True)]


def _components(mask: np.ndarray) -> list[tuple[np.ndarray, tuple[int, int]]]:
    """The places of a pixel mask: `(component mask, (row0, col0) offset)` in raster order.

    Pixels at most three pixels apart per axis are one place, and the join
    chains on: each pixel is dilated by the `RIM_PX` disk (in effect a 3×3
    block) and dilated pixels that touch, 8-connected, belong together — a
    staircase break of one scan edge is not two sites. Measured on the 62
    frozen fixtures, this join takes the Chamfer edge sites from a median 81 to
    29 per glyph and raises what the five largest carry from 50 % to 69 % of
    the part, while a site stays local (median extent 6 px); dilating by twice
    the radius chains whole strokes into one site (p90 extent 131 px).
    """
    joined = binary_dilation(mask, structure=_JOIN_DISK) if mask.any() else mask
    labels, _count = label(joined, structure=_EIGHT_CONNECTED)
    out: list[tuple[np.ndarray, tuple[int, int]]] = []
    for k, box in enumerate(find_objects(labels), start=1):
        if box is None:
            continue
        comp = (labels[box] == k) & mask[box]
        if comp.any():
            out.append((comp, (box[0].start, box[1].start)))
    return out


def _component_cells(comp: np.ndarray, offset: tuple[int, int]) -> tuple[Cell, ...]:
    row0, col0 = offset
    return tuple((x + col0, y + row0, w) for x, y, w in _cells(comp))


def _central_pixel(comp: np.ndarray, offset: tuple[int, int]) -> Point:
    """The component's pixel nearest its centroid — a point ON the component, even a curved one."""
    rows, cols = np.nonzero(comp)
    k = int(np.argmin((rows - rows.mean()) ** 2 + (cols - cols.mean()) ** 2))
    return _pt(cols[k] + offset[1], rows[k] + offset[0])


def _peak_deviation(pts: np.ndarray) -> Point | None:
    """The point `run_is_straight_residual` measures: the farthest one from the chord."""
    if len(pts) < 2:
        return None
    chord = pts[-1] - pts[0]
    clen = float(np.hypot(*chord))
    if clen < 1e-6:
        return None
    d = chord / clen
    rel = pts - pts[0]
    perp = rel - np.outer(rel @ d, d)
    k = int(np.argmax(np.hypot(perp[:, 0], perp[:, 1])))
    return _pt(pts[k, 0], pts[k, 1])


def _line_segment(pts: np.ndarray, centroid: np.ndarray, direction: np.ndarray) -> np.ndarray:
    """The fitted line drawn over the span its points project onto."""
    along = (pts - centroid) @ direction
    return np.vstack([centroid + along.min() * direction, centroid + along.max() * direction])


def _apportion(raws: Sequence[float], target_units: int) -> list[int]:
    """Split `target_units` over `raws` in proportion, as integers that sum exactly.

    Largest-remainder rounding: floor every proportional part, then hand the
    missing units to the largest fractional remainders (ties to the larger raw
    value, then the earlier site). Applied to four-place units, this is what
    makes the shown site values of a category add up to the shown category
    number to its last digit.
    """
    total = float(sum(raws))
    if target_units <= 0 or total <= 0.0:
        return [0] * len(raws)
    exact = [r * target_units / total for r in raws]
    floors = [math.floor(e) for e in exact]
    missing = target_units - sum(floors)
    order = sorted(range(len(raws)), key=lambda i: (-(exact[i] - floors[i]), -raws[i], i))
    for i in order[:missing]:
        floors[i] += 1
    return floors


def _interior_corner_anchors(
    n_anchors: int, stroke_starts: Sequence[int] | None, corner_anchors: Sequence[int] | None
) -> list[int]:
    """The anchor number of each entry of `SamplePlan.corner_sample_idx`, in the same order.

    `build_sample_plan` splits a stroke only at its INTERIOR corner anchors
    (`a < c < b − 1`), stroke by stroke in sorted order, and records one corner
    sample per split — so a corner anchor on a stroke's first or last row is a
    Landmarken corner but not a scored Ecke, and positional indices of the two
    lists differ. Each corner site carries its anchor number so a consumer
    joins on that, never on the index.
    """
    corners = sorted({int(c) for c in (corner_anchors or [])})
    out: list[int] = []
    for a, b in stroke_slices(n_anchors, stroke_starts):
        out.extend(c for c in corners if a < c < b - 1)
    return out


# ------------------------------------------------------------- the categories


def _smoothness_sites(
    pts: np.ndarray, sample_starts: Sequence[int], corner_sample_idx: Sequence[int], unit_px: float
) -> tuple[float, list[_Draft], Numbers, tuple[SitePath, ...]]:
    """Glätte: per-sample |Δ²κ| shares, grouped into the scored segments.

    Mirrors `centerline_smoothness` float for float (the per-stroke sums are
    accumulated in the same order) so the recomputed deduction matches.
    """
    corners = {int(c) for c in corner_sample_idx}
    block_radius = 1 + int(np.ceil(2.0 * SMOOTH_KAPPA_SIGMA))
    total_abs, n_steps = 0.0, 0
    contrib = np.zeros(len(pts))
    scored: list[tuple[int, int, int, np.ndarray]] = []  # stroke no., stroke lo, stroke hi, valid per interior sample
    for stroke_no, (a, b) in enumerate(stroke_bounds(len(pts), sample_starts)):
        seg = pts[a:b]
        if len(seg) < 4:
            continue
        kappa = gaussian_filter1d(discrete_curvature(seg, unit_px), SMOOTH_KAPPA_SIGMA, mode="nearest")
        block = np.zeros(len(seg), dtype=bool)
        for c in corners:
            if a <= c < b:
                lc = c - a
                block[max(0, lc - block_radius) : min(len(seg), lc + block_radius + 1)] = True
        d2 = np.abs(np.diff(kappa, n=2))
        valid = ~(block[:-2] | block[1:-1] | block[2:])
        total_abs += float(d2[valid].sum())
        n_steps += int(valid.sum())
        contrib[a + 1 : b - 1] = np.where(valid, d2, 0.0)
        scored.append((stroke_no, a, b, valid))
    jerk = total_abs / n_steps if n_steps else 0.0
    value = 1.0 - float(np.exp(-jerk / SMOOTH_DECAY))

    mass = float(contrib.sum())
    drafts: list[_Draft] = []
    windows: list[SitePath] = []
    end_mass = 0.0
    for stroke_no, a, b, valid in scored:
        for lo, hi in _runs(~valid):
            windows.append(_path("corner_window", pts[a + 1 + lo : a + 2 + hi]))
        for lo, hi in _runs(valid):
            g_lo, g_hi = a + 1 + lo, a + 1 + hi
            part = contrib[g_lo : g_hi + 1]
            local = np.arange(lo + 1, hi + 2)  # sample index within the stroke
            near_end = (local <= STROKE_END_REACH) | (local >= (b - a - 1) - STROKE_END_REACH)
            part_mass = float(part.sum())
            at_end = float(part[near_end].sum())
            end_mass += at_end
            per_sample = value * part / mass if mass > 0.0 else np.zeros_like(part)
            peak = g_lo + int(np.argmax(part))
            px, py = _pt(*pts[peak])
            drafts.append(
                _Draft(
                    kind="segment",
                    raw=float(per_sample.sum()),
                    x=px,
                    y=py,
                    numbers={
                        "stroke": stroke_no,
                        "from": g_lo,
                        "to": g_hi,
                        "samples": g_hi - g_lo + 1,
                        "peak_sample": peak,
                        "stroke_end_share": _num(at_end / part_mass if part_mass > 0.0 else 0.0),
                    },
                    paths=(_path("segment", pts[g_lo : g_hi + 1], per_sample),),
                )
            )
    numbers: Numbers = {
        "jerk": _num(jerk, 6),
        "scored_samples": n_steps,
        "stroke_end_share": _num(end_mass / mass if mass > 0.0 else 0.0),
    }
    return value, drafts, numbers, tuple(windows)


def _verticality_sites(
    sx: np.ndarray, sy: np.ndarray, pts: np.ndarray, sample_starts: Sequence[int], unit_px: float
) -> tuple[float, int, list[_Draft], Numbers]:
    """Senkrechte: each detected run's share `L·rms / Σ L·rms` of the deduction."""
    runs = detect_vertical_runs(
        sx,
        sy,
        sample_starts,
        unit_px,
        angle_deg=VERTICAL_ANGLE_DEG,
        min_len_units=VERTICAL_MIN_LEN_UNITS,
        straight_tol=VERTICAL_STRAIGHT_TOL,
    )
    if not runs:
        return 0.0, 0, [], {}
    num, den = 0.0, 0.0
    measured: list[tuple[int, int, float, float, float]] = []
    for lo, hi in runs:
        seg = pts[lo : hi + 1]
        x = seg[:, 0]
        x_mean = float(x.mean())
        rms = float(np.sqrt(np.mean((x - x_mean) ** 2))) / unit_px
        length = float(arc_length(seg)[-1])
        num += length * rms
        den += length
        measured.append((lo, hi, rms, length, x_mean))
    residual = num / den if den else 0.0
    value = 1.0 - float(np.exp(-residual / VERT_DECAY))

    drafts: list[_Draft] = []
    for lo, hi, rms, length, x_mean in measured:
        seg = pts[lo : hi + 1]
        dev = seg[:, 0] - x_mean
        px, py = _pt(*seg[int(np.argmax(np.abs(dev)))])
        _, direction = fit_line_tls(seg)
        drafts.append(
            _Draft(
                kind="run",
                raw=value * length * rms / num if num > 0.0 else 0.0,
                x=px,
                y=py,
                numbers={
                    "from": lo,
                    "to": hi,
                    "rms_px": _num(rms * unit_px),
                    "rms_units": _num(rms, 5),
                    "length_units": _num(length / unit_px),
                    "max_dev_px": _num(float(np.abs(dev).max())),
                    "lean_deg": _num(np.degrees(acute_angle_between(direction, np.array([0.0, 1.0]))), 3),
                    "x_ideal": _num(x_mean, 2),
                },
                paths=(_path("run", seg, dev), _path("ideal", np.array([[x_mean, seg[0, 1]], [x_mean, seg[-1, 1]]]))),
            )
        )
    return value, len(runs), drafts, {"residual_units": _num(residual, 6)}


def _corner_sites(
    pts: np.ndarray,
    sample_starts: Sequence[int],
    corner_sample_idx: Sequence[int],
    corner_anchor_ids: Sequence[int],
    unit_px: float,
) -> tuple[float, int, list[_Draft]]:
    """Ecken: each scored corner is exactly `(1 − q_c)/N` of the mean deduction."""
    corners = [int(c) for c in corner_sample_idx]
    if not corners:
        return 0.0, 0, []
    window_px = max(3.0, CORNER_WINDOW_UNITS * unit_px)
    bounds = stroke_bounds(len(pts), sample_starts)
    scored: list[tuple[int, int, float, float, float, np.ndarray, np.ndarray]] = []
    for k, c in enumerate(corners):
        owner = next(((a, b) for a, b in bounds if a <= c < b), None)
        if owner is None:
            continue
        a, b = owner
        seg = pts[a:b]
        arc = arc_length(seg)
        cl = c - a
        left = seg[(arc < arc[cl]) & (arc >= arc[cl] - window_px)]
        right = seg[(arc > arc[cl]) & (arc <= arc[cl] + window_px)]
        s_in = run_is_straight_residual(left) if len(left) >= 3 else 0.0
        s_out = run_is_straight_residual(right) if len(right) >= 3 else 0.0
        q = float(np.exp(-(s_in + s_out) / CORNER_STRAIGHT_DECAY))
        anchor = corner_anchor_ids[k] if k < len(corner_anchor_ids) else -1
        scored.append((c, anchor, s_in, s_out, q, left, right))
    if not scored:
        return 0.0, 0, []
    value = 1.0 - float(np.mean([row[4] for row in scored]))
    n = len(scored)
    drafts: list[_Draft] = []
    for c, anchor, s_in, s_out, q, left, right in scored:
        paths = [_path("approach_in", left), _path("approach_out", right)]
        for role, side in (("in", left), ("out", right)):
            if len(side) >= 3:
                paths.append(_path(f"chord_{role}", side[[0, -1]]))
                peak = _peak_deviation(side)
                if peak is not None:
                    paths.append(SitePath(role=f"peak_{role}", points=(peak,)))
        px, py = _pt(*pts[c])
        drafts.append(
            _Draft(
                kind="corner",
                raw=(1.0 - q) / n,
                x=px,
                y=py,
                numbers={
                    "anchor": int(anchor),
                    "sample": int(c),
                    "s_in": _num(s_in),
                    "s_out": _num(s_out),
                    "q": _num(q),
                },
                paths=tuple(paths),
            )
        )
    return value, n, drafts


def _collinearity_sites(
    sx: np.ndarray, sy: np.ndarray, pts: np.ndarray, sample_starts: Sequence[int], prox_px: float, unit_px: float
) -> tuple[float, int, list[_Draft]]:
    """Kreuzungsflucht: each applicable passage is exactly `(1 − q_p)/N` of the mean."""
    passages = detect_crossing_passages(
        sx,
        sy,
        sample_starts,
        prox_px=prox_px,
        min_arc_factor=CROSSING_MIN_ARC_FACTOR,
        min_angle_deg=CROSSING_MIN_ANGLE_DEG,
    )
    if not passages:
        return 0.0, 0, []
    window_px = max(3.0, CROSS_WINDOW_UNITS * unit_px)
    straight = _locally_straight_mask(pts, sample_starts, max(3.0, RETRACE_WINDOW_UNITS * unit_px), CROSS_STRAIGHT_TOL)
    scored: list[tuple[int, int, int, float, float, float, np.ndarray, np.ndarray, tuple]] = []
    for a, b, lo, hi, partner in passages:
        if partner < 0 or not straight[partner]:
            continue
        seg = pts[a:b]
        arc = arc_length(seg)
        before = seg[(arc < arc[lo - a]) & (arc >= arc[lo - a] - window_px)]
        after = seg[(arc > arc[hi - a]) & (arc <= arc[hi - a] + window_px)]
        if len(before) < 3 or len(after) < 3:
            continue
        if (
            run_is_straight_residual(before) > CROSS_STRAIGHT_TOL
            or run_is_straight_residual(after) > CROSS_STRAIGHT_TOL
        ):
            continue
        c1, u1 = fit_line_tls(before)
        c2, u2 = fit_line_tls(after)
        dtheta = acute_angle_between(u1, u2)
        ddist = point_line_perp_distance(c2, c1, u1) / unit_px
        if dtheta > np.deg2rad(CROSS_APPLY_ANGLE_DEG) or ddist > CROSS_APPLY_OFFSET_UNITS:
            continue
        q = float(np.exp(-dtheta / CROSS_ANG_DECAY)) * float(np.exp(-ddist / CROSS_OFF_DECAY))
        lines = (_line_segment(before, c1, u1), _line_segment(after, c2, u2))
        scored.append((lo, hi, partner, dtheta, ddist, q, before, after, lines))
    if not scored:
        return 0.0, 0, []
    value = 1.0 - float(np.mean([row[5] for row in scored]))
    n = len(scored)
    drafts: list[_Draft] = []
    for lo, hi, partner, dtheta, ddist, q, before, after, (line_before, line_after) in scored:
        px, py = _pt(*pts[(lo + hi) // 2])
        drafts.append(
            _Draft(
                kind="passage",
                raw=(1.0 - q) / n,
                x=px,
                y=py,
                numbers={
                    "from": int(lo),
                    "to": int(hi),
                    "partner": int(partner),
                    "dtheta_deg": _num(np.degrees(dtheta), 3),
                    "ddist_units": _num(ddist, 5),
                    "ddist_px": _num(ddist * unit_px, 3),
                    "q": _num(q),
                },
                paths=(
                    _path("before", before),
                    _path("after", after),
                    _path("line_before", line_before),
                    _path("line_after", line_after),
                    _path("blob", pts[lo : hi + 1]),
                ),
            )
        )
    return value, n, drafts


def _retrace_sites(
    sx: np.ndarray,
    sy: np.ndarray,
    pts: np.ndarray,
    sample_starts: Sequence[int],
    prox_px: float,
    unit_px: float,
    r_px: float,
    mask: np.ndarray,
    pred_mask: np.ndarray,
) -> tuple[float, int, list[_Draft], Numbers, tuple[Cell, ...]]:
    """Doppelzug: every missed ink pixel in the retrace zone is exactly `1/denominator`."""
    idx, partner = detect_retrace_pairs(
        sx,
        sy,
        sample_starts,
        prox_px=prox_px,
        min_arc_factor=CROSSING_MIN_ARC_FACTOR,
        max_angle_deg=CROSSING_MIN_ANGLE_DEG,
    )
    if len(idx) < MIN_RETRACE_PAIRS:
        return 0.0, 0, [], {}, ()
    straight = _locally_straight_mask(
        pts, sample_starts, max(3.0, RETRACE_STEM_WINDOW_UNITS * unit_px), RETRACE_STEM_STRAIGHT_TOL
    )
    gaps = np.hypot(*(pts[idx] - pts[partner]).T)
    keep = straight[idx] & straight[partner] & (gaps <= RETRACE_MAX_GAP_NIB * max(r_px, 1e-6))
    idx, partner = idx[keep], partner[keep]
    if len(idx) < MIN_RETRACE_PAIRS:
        return 0.0, 0, [], {}, ()
    h, w = mask.shape
    sample_pts = np.unique(np.concatenate([idx, partner]))
    ys = np.clip(np.rint(pts[sample_pts, 1]).astype(int), 0, h - 1)
    xs = np.clip(np.rint(pts[sample_pts, 0]).astype(int), 0, w - 1)
    seed = np.zeros((h, w), dtype=bool)
    seed[ys, xs] = True
    region = distance_transform_edt(~seed) <= RETRACE_REGION_RADIUS_NIB * max(r_px, 1e-6)
    crop_here = mask & region
    denom = int(crop_here.sum())
    if denom == 0:
        return 0.0, 0, [], {}, ()
    recall = int((crop_here & pred_mask).sum()) / denom
    value = 1.0 - float(recall)
    missed = crop_here & ~pred_mask
    drafts: list[_Draft] = []
    for comp, offset in _components(missed):
        cx, cy = _central_pixel(comp, offset)
        drafts.append(
            _Draft(
                kind="missed_ink",
                raw=int(comp.sum()) / denom,
                x=cx,
                y=cy,
                numbers={"pixels": int(comp.sum())},
                cells=_component_cells(comp, offset),
            )
        )
    numbers: Numbers = {"zone_ink_px": denom, "missed_px": int(missed.sum()), "recall": _num(recall)}
    return value, int(len(idx)), drafts, numbers, _cells(crop_here)


def _coverage_sites(
    sx: np.ndarray,
    sy: np.ndarray,
    sample_starts: Sequence[int],
    half_widths_px: np.ndarray,
    mask: np.ndarray,
    skel: np.ndarray,
    width_map: np.ndarray,
    pred_mask: np.ndarray,
    unit_px: float,
) -> tuple[float, dict[str, list[_Draft]], Numbers]:
    """Deckungslücke: log split over Dice · Chamfer · Geo, then per pixel or sample.

    `1 − G` with `G = dice · q_chamfer · q_geo`, whose log adds exactly:
    `−ln G = −ln dice + chamfer/(0.05u) + geo/(0.08u)`. Each factor's part is
    its log term's share of `1 − G`; below that, Dice splits per missed/excess
    pixel (`1 − dice = (|FP| + |FN|)/(|pred| + |mask|)` exactly) and the
    Chamfer per boundary pixel (the mean is a sum) — terms, both; the Geo
    splits per sample in proportion to its squared excess, a share: the RMSE is
    the root of their mean, so a sample's share is not its marginal effect.
    """
    h, w = mask.shape
    worst_px = float(np.hypot(h, w))
    intersection = int(np.logical_and(pred_mask, mask).sum())
    area_sum = int(pred_mask.sum()) + int(mask.sum())
    dice = 2.0 * intersection / area_sum if area_sum else 1.0
    chamfer = chamfer_boundary_stats(pred_mask, mask, dead_band_px=DEAD_BAND_PX)
    excess: np.ndarray | None = None
    nearest: tuple[np.ndarray, np.ndarray] | None = None
    if skel.any():
        edt_to_skel, (iy, ix) = distance_transform_edt(~skel, return_indices=True)
        d_skel = bilinear(edt_to_skel.astype(float), sx, sy)
        nib_px = float(np.median(half_widths_px)) if len(half_widths_px) else 1.0
        local_db = np.maximum(DEAD_BAND_PX, bilinear(width_map[iy, ix].astype(float), sx, sy) - nib_px)
        excess = np.maximum(0.0, d_skel - local_db)
        geo = float(np.sqrt(np.mean(excess**2)))
        rows = np.clip(np.rint(sy).astype(int), 0, h - 1)
        cols = np.clip(np.rint(sx).astype(int), 0, w - 1)
        nearest = (ix[rows, cols].astype(float), iy[rows, cols].astype(float))
    else:
        geo = worst_px
    q_chamfer = float(np.exp(-chamfer["chamfer_mean_px"] / (CHAMFER_DECAY_UNITS * unit_px)))
    q_geo = float(np.exp(-geo / (GEO_DECAY_UNITS * unit_px)))
    gate = dice * q_chamfer * q_geo
    value = 1.0 - gate

    fp = pred_mask & ~mask
    fn = mask & ~pred_mask
    numbers: Numbers = {
        "dice": _num(dice),
        "chamfer_mean_px": _num(chamfer["chamfer_mean_px"], 3),
        "geo_db_rmse_px": _num(geo, 3),
        "missed_px": int(fn.sum()),
        "excess_px": int(fp.sum()),
    }
    drafts: dict[str, list[_Draft]] = {"dice": [], "chamfer": [], "geo": []}
    if value <= 0.0:
        return value, drafts, numbers

    log_terms = {
        "dice": -math.log(dice) if dice > 0.0 else math.inf,
        "chamfer": chamfer["chamfer_mean_px"] / (CHAMFER_DECAY_UNITS * unit_px),
        "geo": geo / (GEO_DECAY_UNITS * unit_px),
    }
    if math.isinf(log_terms["dice"]):
        parts = {"dice": value, "chamfer": 0.0, "geo": 0.0}
    else:
        total = sum(log_terms.values())
        parts = {k: value * t / total for k, t in log_terms.items()}

    # Dice: every wrong pixel is one equal piece of 1 − dice; the rim has no place.
    n_wrong = int(fp.sum()) + int(fn.sum())
    if parts["dice"] > 0.0 and n_wrong:
        per_pixel = parts["dice"] / n_wrong
        rim_fn = fn & (distance_transform_edt(~pred_mask) <= RIM_PX) if pred_mask.any() else np.zeros_like(fn)
        rim_fp = fp & (distance_transform_edt(~mask) <= RIM_PX) if mask.any() else np.zeros_like(fp)
        for kind, deep in (("missed_ink", fn & ~rim_fn), ("excess_render", fp & ~rim_fp)):
            for comp, offset in _components(deep):
                cx, cy = _central_pixel(comp, offset)
                drafts["dice"].append(
                    _Draft(
                        kind=kind,
                        raw=per_pixel * int(comp.sum()),
                        x=cx,
                        y=cy,
                        numbers={"pixels": int(comp.sum())},
                        cells=_component_cells(comp, offset),
                    )
                )
        n_rim = int(rim_fn.sum()) + int(rim_fp.sum())
        if n_rim:
            drafts["dice"].append(
                _Draft(
                    kind="rim",
                    raw=per_pixel * n_rim,
                    x=None,
                    y=None,
                    numbers={"missed_px": int(rim_fn.sum()), "excess_px": int(rim_fp.sum()), "rim_px": RIM_PX},
                )
            )

    # Chamfer: the symmetric mean is a sum over both boundaries' dead-banded distances.
    if parts["chamfer"] > 0.0:
        b_pred, b_ink = mask_boundary(pred_mask), mask_boundary(mask)
        if b_pred.any() and b_ink.any():
            weight = np.zeros(mask.shape)
            offset_px = np.zeros(mask.shape)
            d_pred = np.maximum(0.0, distance_transform_edt(~b_ink)[b_pred] - DEAD_BAND_PX)
            d_ink = np.maximum(0.0, distance_transform_edt(~b_pred)[b_ink] - DEAD_BAND_PX)
            weight[b_pred] += d_pred / (2.0 * len(d_pred))
            weight[b_ink] += d_ink / (2.0 * len(d_ink))
            offset_px[b_pred] = np.maximum(offset_px[b_pred], d_pred)
            offset_px[b_ink] = np.maximum(offset_px[b_ink], d_ink)
            mass = float(weight.sum())
            for comp, (row0, col0) in _components(weight > 0.0):
                box = (slice(row0, row0 + comp.shape[0]), slice(col0, col0 + comp.shape[1]))
                comp_weight = np.where(comp, weight[box], 0.0)
                rows, cols = np.nonzero(comp)
                k = int(np.argmax(comp_weight[rows, cols]))
                px, py = _pt(cols[k] + col0, rows[k] + row0)
                drafts["chamfer"].append(
                    _Draft(
                        kind="edge",
                        raw=parts["chamfer"] * float(comp_weight.sum()) / mass,
                        x=px,
                        y=py,
                        numbers={
                            "render_px": int((comp & b_pred[box]).sum()),
                            "ink_px": int((comp & b_ink[box]).sum()),
                            "max_offset_px": _num(float(np.where(comp, offset_px[box], 0.0).max()), 3),
                        },
                        cells=_component_cells(comp, (row0, col0)),
                    )
                )
        else:
            drafts["chamfer"].append(
                _Draft(kind="edge", raw=parts["chamfer"], x=None, y=None, numbers={"reason": "empty_boundary"})
            )

    # Geo: the RMSE's square is a mean over samples of the dead-banded off-skeleton
    # distance, so each sample takes the part in proportion to its square — a share.
    if parts["geo"] > 0.0:
        if excess is not None and nearest is not None:
            sq = excess**2
            mass = float(sq.sum())
            pts = np.column_stack([sx, sy])
            for a, b in stroke_bounds(len(pts), sample_starts):
                for lo, hi in _runs(excess[a:b] > 0.0):
                    g_lo, g_hi = a + lo, a + hi
                    per_sample = parts["geo"] * sq[g_lo : g_hi + 1] / mass
                    peak = g_lo + int(np.argmax(excess[g_lo : g_hi + 1]))
                    px, py = _pt(*pts[peak])
                    whiskers = tuple(
                        _path("whisker", np.array([[sx[i], sy[i]], [nearest[0][i], nearest[1][i]]]))
                        for i in range(g_lo, g_hi + 1)
                    )
                    drafts["geo"].append(
                        _Draft(
                            kind="off_skeleton",
                            raw=float(per_sample.sum()),
                            x=px,
                            y=py,
                            numbers={
                                "from": g_lo,
                                "to": g_hi,
                                "samples": g_hi - g_lo + 1,
                                "max_offset_px": _num(float(excess[peak]), 3),
                            },
                            paths=(_path("run", pts[g_lo : g_hi + 1], per_sample), *whiskers),
                        )
                    )
        else:
            drafts["geo"].append(
                _Draft(kind="off_skeleton", raw=parts["geo"], x=None, y=None, numbers={"reason": "empty_skeleton"})
            )
    return value, drafts, numbers


# ------------------------------------------------------------------- assembly


def _points_rates(metrics: dict) -> dict[str, float]:
    """Linearised score points per unit of each category's deduction.

    `score = 100 · G^0.5 · N`, `N = Σ w_k·Q_k / W` over the applicable terms:
    a naturalness deduction costs `100·√G·w_k/W` points per unit, the coverage
    deduction `50·N/√G` (the derivative of `G^0.5`). First order only — good
    for ranking sites across categories, not a number to show as the category's.
    """
    gate = float(metrics["gate"])
    naturalness = float(metrics["naturalness"])
    applicable = metrics["applicable"]
    weight_sum = W_SMOOTH + sum(
        _WEIGHTS[key] for key, count_key in _APPLICABLE_COUNT.items() if applicable.get(count_key)
    )
    root = gate**GATE_EXPONENT
    rates = {key: 100.0 * root * weight / weight_sum for key, weight in _WEIGHTS.items()}
    rates["coverage"] = 100.0 * GATE_EXPONENT * naturalness / root if root > 0.0 else 100.0 * naturalness
    return rates


def _finalise(
    key: str,
    component: float,
    recomputed: float,
    groups: dict[str, list[_Draft]],
    *,
    applicable: bool,
    in_sync: bool,
    exact: bool,
    rate: float,
    numbers: Numbers | None = None,
    context_paths: tuple[SitePath, ...] = (),
    context_cells: tuple[Cell, ...] = (),
) -> PenaltyCategory:
    """Apportion one category's sites to its shown number and freeze them.

    `groups` holds the drafts per part (one part for every category but
    Deckungslücke, which splits into Dice · Chamfer · Geo first); the shown
    number is apportioned over the parts, then each part over its sites, so
    both levels add up exactly. Located sites come first, the unlocated rest last.
    """
    target = round(component * _SHOWN_UNIT)
    part_names = list(groups)
    part_raws = [sum(d.raw for d in groups[name]) for name in part_names]
    part_units = _apportion(part_raws, target) if len(part_names) > 1 else [target]
    total_raw = float(sum(part_raws))
    sites: list[PenaltySite] = []
    parts: dict[str, float] = {}
    ordered: list[tuple[_Draft, int]] = []
    for name, units in zip(part_names, part_units, strict=True):
        drafts = groups[name]
        if len(part_names) > 1:
            parts[name] = units / _SHOWN_UNIT
        for draft, site_units in zip(drafts, _apportion([d.raw for d in drafts], units), strict=True):
            ordered.append((draft, site_units))
    ordered.sort(key=lambda pair: pair[0].x is None)  # stable: located first, in their own order
    for index, (draft, site_units) in enumerate(ordered):
        sites.append(
            PenaltySite(
                category=key,
                index=index,
                kind=draft.kind,
                value=round(site_units / _SHOWN_UNIT, _SHOWN_PLACES),
                raw=float(draft.raw),
                share=round(draft.raw / total_raw, 4) if total_raw > 0.0 else 0.0,
                exact=exact,
                points_est=round(draft.raw * rate, 2),
                x=draft.x,
                y=draft.y,
                numbers=draft.numbers,
                paths=draft.paths,
                cells=draft.cells,
            )
        )
    return PenaltyCategory(
        key=key,
        value=component,
        raw=recomputed,
        applicable=applicable,
        in_sync=in_sync,
        exact=exact,
        points_est=round(component * rate, 2),
        sites=tuple(sites),
        numbers=numbers or {},
        parts=parts,
        context_paths=context_paths,
        context_cells=context_cells,
    )


def _drift_group(component: float) -> dict[str, list[_Draft]]:
    """The whole category as one unlocated site — when the map would not match the number."""
    return {"all": [_Draft(kind="unlocated", raw=component, x=None, y=None, numbers={"reason": "recomputation_drift"})]}


def _require_finite(anchors_px: np.ndarray, half_widths_px: np.ndarray, unit_px: float) -> None:
    """Refuse geometry the metric would turn into NaN components.

    The frozen metric does not raise on a NaN anchor or half-width, it returns
    NaN components — which then have no place and no digits to apportion. A
    JSONB column cannot store a NaN, so a prod row reaches this mostly through
    a zero or negative x-height; the pure callers (tools, tests) can hand
    either. Both get a clear refusal instead of a crash in the apportionment.
    """
    if not (math.isfinite(unit_px) and unit_px > 0.0):
        raise UnscorableInputError(f"unit_px must be a positive finite number, got {unit_px!r}")
    for name, values in (("anchors_px", anchors_px), ("half_widths_px", half_widths_px)):
        finite = np.isfinite(values)
        if not finite.all():
            rows = np.flatnonzero(~finite.reshape(len(values), -1).all(axis=1))
            raise UnscorableInputError(f"{name} holds non-finite values (rows {rows[:5].tolist()})")


def suetterlin_penalty_sites(
    anchors_px: np.ndarray,
    half_widths_px: np.ndarray,
    stroke_starts: Sequence[int] | None,
    mask: np.ndarray,
    skel: np.ndarray,
    width_map: np.ndarray,
    *,
    unit_px: float,
    corner_anchors: Sequence[int] | None = None,
    n: int = QUALITY_N_SAMPLES,
) -> PenaltyMap:
    """Score a Sütterlin template with the frozen metric and locate every deduction.

    Same arguments as `suetterlin_quality_metrics`, which is called unchanged;
    its dict comes back as `PenaltyMap.metrics`. The sites are rebuilt from the
    same sampling plan and the same detectors, in crop pixels. Raises
    `UnscorableInputError` for non-finite geometry or a non-positive `unit_px`,
    and for a metric result with a non-finite component.
    """
    anchors_px = np.asarray(anchors_px, dtype=float)
    half_widths_px = np.asarray(half_widths_px, dtype=float)
    unit_px = float(unit_px)
    _require_finite(anchors_px, half_widths_px, unit_px)
    metrics = suetterlin_quality_metrics(
        anchors_px,
        half_widths_px,
        stroke_starts,
        mask,
        skel,
        width_map,
        unit_px=unit_px,
        corner_anchors=corner_anchors,
        n=n,
    )
    h, w = mask.shape
    sx, sy, _sw, sample_starts, corner_sample_idx, stroke_rings = _sample_and_rings(
        anchors_px, half_widths_px, stroke_starts, n, corner_anchors
    )
    pred_mask = rasterize_silhouette(stroke_rings, (h, w))
    sx = np.asarray(sx, dtype=float)
    sy = np.asarray(sy, dtype=float)
    pts = np.column_stack([sx, sy])
    r_px = float(np.median(half_widths_px)) if len(half_widths_px) else 1.0
    prox_px = max(PROX_NIB_FACTOR * r_px, PROX_FLOOR_UNITS * unit_px)
    corner_anchor_ids = _interior_corner_anchors(len(anchors_px), stroke_starts, corner_anchors)

    components = metrics["components"]
    applicable = metrics["applicable"]
    non_finite = [key for key in CATEGORIES if not math.isfinite(float(components[key]))]
    if non_finite:
        raise UnscorableInputError(f"the metric returned non-finite components {non_finite}")
    rates = _points_rates(metrics)

    smooth_value, smooth_drafts, smooth_numbers, windows = _smoothness_sites(
        pts, sample_starts, corner_sample_idx, unit_px
    )
    vert_value, n_vert, vert_drafts, vert_numbers = _verticality_sites(sx, sy, pts, sample_starts, unit_px)
    corner_value, n_corner, corner_drafts = _corner_sites(
        pts, sample_starts, corner_sample_idx, corner_anchor_ids, unit_px
    )
    cross_value, n_cross, cross_drafts = _collinearity_sites(sx, sy, pts, sample_starts, prox_px, unit_px)
    retrace_value, n_retrace, retrace_drafts, retrace_numbers, zone = _retrace_sites(
        sx, sy, pts, sample_starts, prox_px, unit_px, r_px, mask, pred_mask
    )
    cover_value, cover_groups, cover_numbers = _coverage_sites(
        sx, sy, sample_starts, half_widths_px, mask, skel, width_map, pred_mask, unit_px
    )

    recomputed = {
        "smoothness": (smooth_value, None, {"all": smooth_drafts}, smooth_numbers, windows, ()),
        "verticality": (vert_value, n_vert, {"all": vert_drafts}, vert_numbers, (), ()),
        "corner": (corner_value, n_corner, {"all": corner_drafts}, {}, (), ()),
        "collinearity": (cross_value, n_cross, {"all": cross_drafts}, {}, (), ()),
        "retrace": (retrace_value, n_retrace, {"all": retrace_drafts}, retrace_numbers, (), zone),
        "coverage": (cover_value, None, cover_groups, cover_numbers, (), ()),
    }
    categories: dict[str, PenaltyCategory] = {}
    for key in CATEGORIES:
        value, count, groups, numbers, paths, cells = recomputed[key]
        component = float(components[key])
        count_key = _APPLICABLE_COUNT.get(key)
        is_applicable = count_key is None or bool(applicable.get(count_key))
        in_sync = abs(value - component) <= SYNC_TOLERANCE and (
            count_key is None or int(count or 0) == int(applicable.get(count_key, 0))
        )
        if not in_sync:
            # The context was measured by the same recomputation the map was
            # dropped for, so it goes too — no windows around sites nobody trusts.
            groups = _drift_group(component)
            numbers, paths, cells = {}, (), ()
        categories[key] = _finalise(
            key,
            component,
            value,
            groups,
            applicable=is_applicable,
            in_sync=in_sync,
            exact=key in ("corner", "collinearity", "retrace"),
            rate=rates[key],
            numbers=numbers,
            context_paths=paths,
            context_cells=cells,
        )

    # `value`, not `raw`: a site whose share rounds to zero is not drawn, and a
    # pin on it would number a mark the reader cannot find — the list would
    # then show fewer discs than the image offers sites to pin.
    located = [
        site
        for key in CATEGORIES
        for site in categories[key].sites
        if site.x is not None and site.y is not None and site.value > 0.0
    ]
    located.sort(key=lambda s: (-s.raw * rates[s.category], CATEGORIES.index(s.category), s.index))
    pins = tuple(
        PenaltyPin(rank=i + 1, category=s.category, index=s.index, points_est=s.points_est, x=s.x, y=s.y)
        for i, s in enumerate(located[:PIN_COUNT])
        if s.x is not None and s.y is not None
    )
    centerline = tuple(
        tuple(_pt(x, y) for x, y in pts[a:b]) for a, b in stroke_bounds(len(pts), sample_starts) if b > a
    )
    return PenaltyMap(
        metrics=metrics,
        width=int(w),
        height=int(h),
        unit_px=float(unit_px),
        centerline=centerline,
        categories=categories,
        pins=pins,
    )


def suetterlin_penalty_sites_for_glyph(glyph_row: dict, bbox: dict, chart_path: str) -> PenaltyMap:
    """Locate the deductions of a STORED Sütterlin template against its own crop.

    The same end-to-end load as `suetterlin_quality_for_glyph` (chart → crop
    with eraser/ink mask → binarize → skeleton/EDT), so the headline numbers
    are exactly the re-score the `/quality` route's `stored` half reports.
    """
    for required in ("baseline_y", "midband_y", "y0", "y1", "x0", "x1"):
        if bbox.get(required) is None:
            raise UnscorableInputError(f"bbox missing required field {required!r}")
    trace_meta = glyph_row.get("trace_meta") or {}
    pixel_anchors = trace_meta.get("pixel_anchors")
    half_widths_px = trace_meta.get("half_widths_px")
    if not pixel_anchors or not half_widths_px:
        raise UnscorableInputError("template lacks trace_meta.pixel_anchors / half_widths_px")

    chart_gray = load_chart_grayscale(chart_path)
    crop = crop_with_mask(chart_gray, bbox, fill=1.0)
    mask = binarize_adaptive(crop, fill_holes_max_area=int(bbox.get("fill_holes_max_area") or 0))
    skel, width_map = skeleton_and_width(mask)

    anchors_px = crop_local_anchors(pixel_anchors, bbox)
    unit_px = float(trace_meta.get("unit_px") or (int(bbox["baseline_y"]) - int(bbox["midband_y"])))
    return suetterlin_penalty_sites(
        anchors_px,
        np.asarray(half_widths_px, dtype=float),
        trace_meta.get("stroke_starts"),
        mask,
        skel,
        width_map,
        unit_px=unit_px,
        corner_anchors=trace_meta.get("corner_anchors"),
    )
