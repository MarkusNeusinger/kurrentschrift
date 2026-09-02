"""Laufform derivation rules — the pure half of promoting a median into a
running-form row (templates variant 100).

Doctrine (optimierungs-werkbank.md §3, jul31 split): the chart cell is the
ductus prior, the written words are the form model. The row builder
(`api.routers.templates.build_laufform_canonical`) takes everything but the
anchors from the chart; THIS module owns what happens to the anchors before
they become a row.

End blend (LF5/LF6, qualitaetsmetrik.md §14 `aug29`): the free ends of a
fitted stroke are its least constrained anchors — the fit pulls them toward
neighbouring ink (the t's first anchor toward its Kringel, the K's last anchor
onto the following Anstrich), and a per-anchor median cannot outvote a drift
every occurrence shares. The composer reads its landing/departure tangents from
exactly those ends, so a transverse drift of one nib width flips the join
grammar. The end deviation of a median has two components, and they mean
different things: ALONG the chart's end direction it is the running form's own
extent (a longer lead-in, a longer tail — the hand's width, which the frozen
word ruler confirmed when LF5 cut it away and lost 0.011); ACROSS it is the pull
toward neighbouring ink. The blend therefore keeps the longitudinal component
and fades only the transverse one to zero over an arc-length window from each
free end (LF6, the default); the full cross-fade of LF5 stays reachable for
reproduction. In both modes the chart end piece is attached RIGIDLY to the
Laufform at the window edge, so a uniformly shifted running form is a fixed
point of the blend.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

from core.geometry import TANGENT_WINDOW_UNITS
from core.quality import QUALITY_N_SAMPLES, _sample_and_rings
from core.quality_suetterlin import (
    PROX_FLOOR_UNITS,
    PROX_NIB_FACTOR,
    W_CORNER,
    W_CROSS,
    W_SMOOTH,
    W_VERT,
    centerline_smoothness,
    corner_crispness,
    crossing_collinearity,
    verticality,
)
from core.template import build_sample_plan, multi_stroke_centerlines, sample_with_sample_plan, stroke_slices


Point = tuple[float, float]

# Row gate (LF8, qualitaetsmetrik.md §14 `aug29`): the largest anchor spike
# ratio (`anchor_spike_ratio` — the harvest's own „Anker im leeren Papier"
# detector, measured on the ROW) a running-form row may carry and still be
# written. Data-derived, never hand-set: the worst ratio among the rows the
# doctrine trusts (n ≥ LAUFFORM_MIN_OCCURRENCES) on the Sütterlin-1922 root of
# 2026-08-29, rounded up to 0.01 — the i at 2.9405 (its dot stroke). Over it on
# that root: ue 5.79 · F 5.53 · ae 4.15 · b 3.55 · K 3.16, all n = 1 rows that
# came in through the manual PUT; no trusted row, by construction. None turns
# the gate off. The naturalness GAP of LF7 was measured first and rejected —
# it misses the K — and stays a report column (`row_naturalness`).
LAUFFORM_SPIKE_RATIO_MAX: float | None = 2.95
# Head gate (LF9, qualitaetsmetrik.md §14 `aug29`): how far the direction of a
# running-form row's HEAD — its first stroke's landing over the grammar's own
# arc window (`head_deviation`) — may leave the chart's before the row is
# refused. Doctrine-derived, not data-derived: half the ALIGN band (25–55°) of
# core/compose.py. A head that leaves the chart's direction by more can change
# the join class the grammar decides on its landing (J1, §14) and contradicts
# the one property the canonicalisation promises to keep („the tangents stay":
# the row carries the chart's entry tangent as metadata while its geometry says
# otherwise). On the Sütterlin-1922 root of 2026-08-29 it flags the t (46°,
# n = 4 — the Korb #7 hook: anchor 0 sits right of anchor 1, so the head starts
# at 104° against the chart's 37°) and the E/f/v/k rows; the spike gate cannot
# see a head that turns, and no other trusted row comes near (m 15°, w 14°).
# None turns the gate off.
LAUFFORM_HEAD_DEVIATION_MAX: float | None = 15.0
# Smoothness sensor (LF11, qualitaetsmetrik.md §14 `sep02`): the step the
# rendered centerline is resampled onto before its turn angles are read, and the
# turn below which a sign change is numerical noise rather than a zigzag.
#
# 0.02 xh is a third of the nib radius (0.064 xh on the pooled 1922 nib) — fine
# enough that a wobble the pen could not have drawn still shows, coarse enough
# that the reading is not the sampler's own rounding. 3° is where the audit of
# 2026-09-02 drew the line, and the chart rows confirm it: at that threshold
# their rates sit at or near zero (o 0.00, e 0.00, n 0.46), so the sensor calls
# a drawn form smooth.
ZIGZAG_STEP_UNITS = 0.02
ZIGZAG_TURN_MIN_DEG = 3.0
# Pixel frame the geometry-only naturalness is measured in when the chart row
# carries no `unit_px` of its own (the Sütterlin-1922 rows carry 63–64).
DEFAULT_UNIT_PX = 64.0

# Arc-length window (x-height units, measured on the chart stroke) over which
# each free stroke end is blended back to the chart geometry — the one knob of
# the LF5/LF6 pre-registrations (ladder {0.25, 0.5}). 0.0 disables the blend:
# the pre-LF5 row, anchors verbatim. Adopted only by a passed gate (§14).
LAUFFORM_END_WINDOW = 0.0

_DECIMALS = 4

# Fallback nib radius (template units) for a chart row without usable widths —
# the stand-in shared by the sampler helpers and the form distance (LF10).
_FALLBACK_NIB_RADIUS = 0.05


def _half_widths(chart_row: Any) -> np.ndarray:
    """A chart row's half-widths as a flat float array — empty when the row
    carries none.

    A row's `half_widths` may be NULL (the column is nullable, and an attribute
    view can leave it out), and `np.asarray(None, dtype=float)` is not an empty
    array but a 0-d NaN whose `len()` raises. Missing widths therefore have to
    be caught BEFORE the conversion; they are exactly the case
    `_FALLBACK_NIB_RADIUS` exists for.
    """
    raw = getattr(chart_row, "half_widths", None)
    if raw is None:
        return np.zeros(0, dtype=float)
    return np.asarray(raw, dtype=float).reshape(-1)


def _arc_lengths(points: Sequence[Point]) -> list[float]:
    """Cumulative arc length along a polyline, starting at 0."""
    acc = [0.0]
    for (x0, y0), (x1, y1) in zip(points, points[1:], strict=False):
        acc.append(acc[-1] + math.hypot(x1 - x0, y1 - y0))
    return acc


def _stroke_ranges(n: int, stroke_starts: Sequence[int] | None) -> list[tuple[int, int]]:
    """`[start, end)` anchor ranges per stroke, from the chart's stroke starts."""
    starts = sorted({int(s) for s in (stroke_starts or [0]) if 0 <= int(s) < n})
    if not starts or starts[0] != 0:
        starts.insert(0, 0)
    return [(s, e) for s, e in zip(starts, [*starts[1:], n], strict=False) if e > s]


def _end_weight(dist: float, window: float) -> float:
    """Blend weight of the Laufform: 0 at the free end, 1 from the window edge on."""
    if window <= 0.0:
        return 1.0
    return min(1.0, max(0.0, dist / window))


def _edge_index(arc: Sequence[float], indices: Sequence[int], window: float) -> int:
    """First index (walking away from a free end) whose arc distance reaches the window.

    `arc` holds the distance of every anchor from THAT end; `indices` walks the
    stroke from the end inward. Falls back to the far end for a stroke shorter
    than the window — its whole length is then the blend zone.
    """
    for i in indices:
        if arc[i] >= window:
            return i
    return indices[-1]


def _offset(chart: Sequence[Point], lauf: Sequence[Point], index: int) -> Point:
    """Laufform-minus-chart offset at one anchor — the rigid attach of a chart end piece."""
    return (lauf[index][0] - chart[index][0], lauf[index][1] - chart[index][1])


def _unit(a: Point, b: Point) -> Point | None:
    """Unit vector from `a` to `b`, None for coincident points."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    norm = math.hypot(dx, dy)
    if norm <= 1e-12:
        return None
    return (dx / norm, dy / norm)


def _blend_point(chart_p: Point, lauf_p: Point, t: Point, w: float, direction: Point | None) -> Point:
    """One anchor of an end zone: the chart point at the rigid attach `t`, plus
    the residual — kept along `direction` (LF6) or faded entirely (LF5 when
    `direction` is None), the transverse part fading with `w`."""
    base = (chart_p[0] + t[0], chart_p[1] + t[1])
    res = (lauf_p[0] - base[0], lauf_p[1] - base[1])
    if direction is None:
        return (base[0] + w * res[0], base[1] + w * res[1])
    along = res[0] * direction[0] + res[1] * direction[1]
    par = (along * direction[0], along * direction[1])
    perp = (res[0] - par[0], res[1] - par[1])
    return (base[0] + par[0] + w * perp[0], base[1] + par[1] + w * perp[1])


def blend_stroke_ends(
    chart: Sequence[Sequence[float]],
    anchors: Sequence[Sequence[float]],
    stroke_starts: Sequence[int] | None = None,
    window: float = LAUFFORM_END_WINDOW,
    *,
    transverse_only: bool = True,
) -> list[list[float]]:
    """Blend a Laufform's stroke ends back to the chart geometry (LF5/LF6).

    Per stroke (`stroke_starts` from the chart's `trace_meta`, default one
    stroke) and per free end, the anchors within `window` of arc length (on the
    chart stroke) are rebuilt from the chart point attached at `T` — the
    Laufform-minus-chart offset AT the window edge, so the chart end piece rides
    rigidly on the Laufform — plus the Laufform's residual against that:

    * `transverse_only=True` (LF6, default): the residual's component along
      the chart's end direction (window edge → end) is kept in full — the
      running form's own extent — and only the transverse component fades,
      with weight `w` rising linearly from 0 at the end to 1 at the edge.
    * `transverse_only=False` (LF5): the whole residual fades with `w` — a
      full cross-fade to the chart shape.

    A stroke shorter than two windows has no interior to speak of: it becomes
    the chart shape at the Laufform's mean placement in both modes.

    Args:
        chart: The chart row's anchors (the ductus prior).
        anchors: The median/draft anchors, same count as `chart`.
        stroke_starts: Anchor indices where the chart's strokes begin.
        window: Arc-length window in x-height units; `0` returns `anchors`
            unchanged and unrounded (the pre-blend row, bit for bit).
        transverse_only: LF6 (True) or the LF5 full cross-fade (False).

    Returns:
        The blended anchors as `[[x, y], …]`, rounded to 4 decimals.

    Raises:
        ValueError: If the two anchor lists differ in length.
    """
    if len(chart) != len(anchors):
        raise ValueError(f"anchor count {len(anchors)} != chart row's {len(chart)}")
    chart_pts: list[Point] = [(float(x), float(y)) for x, y in chart]
    lauf_pts: list[Point] = [(float(x), float(y)) for x, y in anchors]
    if window <= 0.0:
        # Blend off: the pre-blend row bit for bit — no rounding pass either,
        # so a stored row re-submitted at window 0 reproduces itself exactly.
        return [[x, y] for x, y in lauf_pts]
    out: list[Point] = list(lauf_pts)
    n = len(chart_pts)
    if n:
        for start, end in _stroke_ranges(n, stroke_starts):
            seg = chart_pts[start:end]
            if len(seg) < 2:
                continue
            arc = _arc_lengths(seg)
            total = arc[-1]
            if total < 2.0 * window:
                # Too short for two independent end zones: the whole stroke is
                # the chart shape, attached at the Laufform's mean placement.
                k = len(seg)
                t_mean = (
                    sum(lauf_pts[start + i][0] - chart_pts[start + i][0] for i in range(k)) / k,
                    sum(lauf_pts[start + i][1] - chart_pts[start + i][1] for i in range(k)) / k,
                )
                for i in range(k):
                    cx, cy = chart_pts[start + i]
                    out[start + i] = (cx + t_mean[0], cy + t_mean[1])
                continue
            forward = list(range(len(seg)))
            # Distances from the start end and from the finish end; with
            # total >= 2 * window the two zones never overlap.
            from_start = arc
            from_end = [total - a for a in arc]
            edge_start = _edge_index(from_start, forward, window)
            edge_end = _edge_index(from_end, forward[::-1], window)
            t_start = _offset(chart_pts, lauf_pts, start + edge_start)
            t_end = _offset(chart_pts, lauf_pts, start + edge_end)
            # The chart's end directions: window edge → free end, on the chart
            # stroke (the ductus prior says where the pen arrives from / leaves to).
            d_start = _unit(seg[edge_start], seg[0]) if transverse_only else None
            d_end = _unit(seg[edge_end], seg[-1]) if transverse_only else None
            for i in range(len(seg)):
                w_start = _end_weight(from_start[i], window)
                w_end = _end_weight(from_end[i], window)
                if w_start < 1.0:
                    w, t, d = w_start, t_start, d_start
                elif w_end < 1.0:
                    w, t, d = w_end, t_end, d_end
                else:
                    continue
                out[start + i] = _blend_point(chart_pts[start + i], lauf_pts[start + i], t, w, d)
    return [[round(x, _DECIMALS), round(y, _DECIMALS)] for x, y in out]


def row_naturalness(
    anchors: Sequence[Sequence[float]],
    half_widths: Sequence[float],
    stroke_starts: Sequence[int] | None,
    corner_anchors: Sequence[int] | None,
    unit_px: float = DEFAULT_UNIT_PX,
) -> dict[str, Any]:
    """Geometry-only naturalness of one template row (the §5 terms without the scan).

    The Sütterlin quality metric (`core.quality_suetterlin`) scores a row as
    `gate^0.5 · naturalness`: the gate needs the crop, the naturalness terms
    need only the rendered centerline. A running-form row has no crop of its
    own — it is a median over word occurrences — so this is the part of the
    metric that CAN be asked of it: smoothness (no jags), verticality of the
    straight downstrokes, crispness of the within-stroke corners and
    collinearity through a straight crossing, weighted like §5 over the
    applicable terms. Retrace fidelity (ink recall) is left out — it needs the
    mask. Stroke starts and corner anchors come from the chart row (the ductus
    prior), so a Laufform row and its chart row are sampled with one plan and
    the two numbers compare.

    Args:
        anchors: Template-unit anchors (x-height units, y up).
        half_widths: Per-anchor half-widths in the same units.
        stroke_starts: The chart's stroke starts (`trace_meta.stroke_starts`).
        corner_anchors: The chart's corner anchors (`trace_meta.corner_anchors`).
        unit_px: Pixels per x-height of the measurement frame.

    Returns:
        `naturalness` (0–1) plus the 0–1 `components` (1 − quality, like §5's
        `components`) and the per-term applicability counts.
    """
    pts = np.asarray([[float(x), float(y)] for x, y in anchors], dtype=float)
    if len(pts) < 2:
        raise ValueError("need at least 2 anchors")
    # Pixel frame: y down like a crop; every term is invariant to the flip.
    anchors_px = np.column_stack([pts[:, 0] * unit_px, -pts[:, 1] * unit_px])
    hw = np.asarray([float(h) for h in half_widths], dtype=float) * unit_px
    if len(hw) != len(pts):
        hw = np.full(len(pts), float(hw.mean()) if len(hw) else 0.05 * unit_px)
    sx, sy, _sw, sample_starts, corner_sample_idx, _rings = _sample_and_rings(
        anchors_px, hw, stroke_starts, QUALITY_N_SAMPLES, corner_anchors
    )
    r_px = float(np.median(hw)) if len(hw) else 1.0
    prox_px = max(PROX_NIB_FACTOR * r_px, PROX_FLOOR_UNITS * unit_px)
    q_smooth = centerline_smoothness(sx, sy, sample_starts, corner_sample_idx, unit_px)
    q_vert, n_vert = verticality(sx, sy, sample_starts, unit_px)
    q_corner, n_corner = corner_crispness(sx, sy, sample_starts, corner_sample_idx, unit_px)
    q_cross, n_cross = crossing_collinearity(sx, sy, sample_starts, prox_px, unit_px)
    applicable = [(W_SMOOTH, q_smooth)]
    if n_vert:
        applicable.append((W_VERT, q_vert))
    if n_corner:
        applicable.append((W_CORNER, q_corner))
    if n_cross:
        applicable.append((W_CROSS, q_cross))
    naturalness = sum(w * q for w, q in applicable) / sum(w for w, _ in applicable)
    return {
        "naturalness": round(float(naturalness), 4),
        "components": {
            "smoothness": round(1.0 - float(q_smooth), 4),
            "verticality": round(1.0 - float(q_vert), 4),
            "corner": round(1.0 - float(q_corner), 4),
            "collinearity": round(1.0 - float(q_cross), 4),
        },
        "applicable": {"vertical_runs": int(n_vert), "corners": int(n_corner), "crossings": int(n_cross)},
    }


def naturalness_gap(chart_row: Any, anchors: Sequence[Sequence[float]]) -> dict[str, Any]:
    """The row gate's quantity: N(chart) − N(candidate) for one glyph (LF7).

    `chart_row` is the variant-0 template (ORM row or an attribute view with
    `anchors`, `half_widths`, `trace_meta`); `anchors` the candidate row's
    anchors, same count. Both are measured in the chart's own pixel frame
    with the chart's stroke starts and corner anchors. Positive = the
    candidate is less natural than its own chart form.
    """
    meta = getattr(chart_row, "trace_meta", None) or {}
    unit_px = float(meta.get("unit_px") or DEFAULT_UNIT_PX)
    starts = meta.get("stroke_starts")
    corners = meta.get("corner_anchors")
    chart = row_naturalness(chart_row.anchors, chart_row.half_widths, starts, corners, unit_px)
    cand = row_naturalness(anchors, chart_row.half_widths, starts, corners, unit_px)
    return {"gap": round(chart["naturalness"] - cand["naturalness"], 4), "chart": chart, "candidate": cand}


def anchor_spike_ratio(anchors: Sequence[Sequence[float]], stroke_starts: Sequence[int] | None) -> float:
    """The anchor spike ratio of an anchor chain — an anchor that left the
    stroke for empty paper and came back („Anker im leeren Papier", the
    glossary term).

    The largest step between consecutive anchors, measured against the median
    step OF ITS OWN pen-stroke, maximised over the strokes. Numerator and
    denominator share a stroke and a unit, so the ratio is scale-free and
    comparable across glyphs — the 120-anchor capitals and the 6-anchor
    punctuation alike. PER STROKE, not pooled, because strokes differ in scale
    by ~1.5x (an i's body against its dot): a pooled median is dominated by the
    long body stroke and understates a spike inside a short one.

    Pen lifts never count: a stroke boundary is the hand setting the pen down
    somewhere else, not a discontinuity of the line. A two-anchor stroke yields
    one step (ratio 1.0) and a three-anchor stroke caps near 2 — such strokes
    are structurally exempt (the shortest stroke today is a ue umlaut dot at 10
    anchors). Returns 0.0 when there is nothing to judge and `inf` when a
    stroke's median step is zero while some step in it is not.

    The ONE detector: the harvest's chain gate scores every single fit with it
    (`tools/laufform/harvest.py`, `MAX_ANCHOR_SPIKE_RATIO` = 8 — calibrated
    for needles), and the row gate (LF8) scores the ROW that is about to be
    written with it against `LAUFFORM_SPIKE_RATIO_MAX` — an n = 1 draft IS its
    single fit and carries every spike straight into the writing path.
    """
    pts = np.asarray(anchors, dtype=float).reshape(-1, 2)
    if len(pts) < 2:
        return 0.0
    bounds = sorted({0, *(int(s) for s in (stroke_starts or []) if 0 < int(s) < len(pts)), len(pts)})
    worst = 0.0
    for start, end in zip(bounds[:-1], bounds[1:], strict=True):
        stroke = pts[start:end]
        if len(stroke) < 2:
            continue
        steps = np.hypot(*(stroke[1:] - stroke[:-1]).T)
        largest, median = float(steps.max()), float(np.median(steps))
        if median <= 0.0:
            if largest > 0.0:
                return float("inf")
            continue
        worst = max(worst, largest / median)
    return worst


def spike_gate(chart_row: Any, anchors: Sequence[Sequence[float]]) -> dict[str, Any]:
    """The row gate (LF8) for one candidate row: its spike ratio over the chart's
    stroke starts, the gate value and whether it is exceeded (False while the
    gate is off, `LAUFFORM_SPIKE_RATIO_MAX` None)."""
    meta = getattr(chart_row, "trace_meta", None) or {}
    ratio = round(anchor_spike_ratio(anchors, meta.get("stroke_starts")), 4)
    limit = LAUFFORM_SPIKE_RATIO_MAX
    return {"ratio": ratio, "max": limit, "exceeded": limit is not None and ratio > limit}


def _landing_direction_deg(points: np.ndarray, window: float) -> float | None:
    """Landing direction of a polyline's start, degrees (y up): from its first
    point to the first point at least ``window`` of arc away — the grammar's
    own rule (`core.compose._endpoint_tangent`, TANGENT_WINDOW_UNITS), so the
    gate judges the direction the join will actually be built on — or to the
    last point of a shorter line. None when nothing to judge (fewer than two
    distinct points)."""
    if len(points) < 2:
        return None
    acc = 0.0
    far = points[-1]
    for i in range(1, len(points)):
        acc += float(math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]))
        far = points[i]
        if acc >= window:
            break
    dx, dy = float(far[0] - points[0][0]), float(far[1] - points[0][1])
    if dx == 0.0 and dy == 0.0:
        return None
    return math.degrees(math.atan2(dy, dx))


def _rendered_strokes(chart_row: Any, anchors: Sequence[Sequence[float]]) -> list[np.ndarray]:
    """Every pen-stroke's centerline as the renderer draws it — the chart's
    sample plan (stroke starts, corner knots, widths) over the given anchors,
    the same spline the join grammar reads its tangents off. Empty when there
    is nothing to sample."""
    pts = np.asarray(anchors, dtype=float).reshape(-1, 2)
    if len(pts) < 2:
        return []
    meta = getattr(chart_row, "trace_meta", None) or {}
    half_widths = _half_widths(chart_row)
    if len(half_widths) != len(pts):
        half_widths = np.full(len(pts), float(half_widths.mean()) if len(half_widths) else _FALLBACK_NIB_RADIUS)
    lines = multi_stroke_centerlines(
        pts,
        half_widths,
        meta.get("stroke_starts"),
        90.0,
        n=QUALITY_N_SAMPLES,
        corner_anchors=meta.get("corner_anchors"),
    )
    return [np.asarray(line, dtype=float) for line in lines]


def _rendered_first_stroke(chart_row: Any, anchors: Sequence[Sequence[float]]) -> np.ndarray:
    """The first pen-stroke's rendered centerline, or an empty array."""
    lines = _rendered_strokes(chart_row, anchors)
    return lines[0] if lines else np.zeros((0, 2))


def head_deviation(chart_row: Any, anchors: Sequence[Sequence[float]]) -> float:
    """How far a candidate row's HEAD turns away from the chart's, in degrees
    (0–180): the landing direction of the first pen-stroke — over
    TANGENT_WINDOW_UNITS of arc, the window the join grammar lands with, on
    the RENDERED centerline (the chart's sample plan over each anchor set;
    the anchor polyline itself misreads the dense, curling capital heads by
    up to 33°, §14 LF9) — of the row against the chart's. The Korb #7 t: the
    fitted head starts up-left where the chart rises at 37°, the grammar
    reads a landing of 87° and never couples. 0.0 when either head is
    degenerate — nothing to judge, never a refusal."""
    a = _landing_direction_deg(_rendered_first_stroke(chart_row, chart_row.anchors), TANGENT_WINDOW_UNITS)
    b = _landing_direction_deg(_rendered_first_stroke(chart_row, anchors), TANGENT_WINDOW_UNITS)
    if a is None or b is None:
        return 0.0
    return abs((b - a + 180.0) % 360.0 - 180.0)


def head_gate(chart_row: Any, anchors: Sequence[Sequence[float]]) -> dict[str, Any]:
    """The head gate (LF9) for one candidate row: its head deviation from the
    chart row, the gate value and whether it is exceeded (False while the gate
    is off, `LAUFFORM_HEAD_DEVIATION_MAX` None)."""
    deviation = round(head_deviation(chart_row, anchors), 2)
    limit = LAUFFORM_HEAD_DEVIATION_MAX
    return {"deviation": deviation, "max": limit, "exceeded": limit is not None and deviation > limit}


# ----------------------------------------------------------------- smoothness sensor (LF11)


def _resample_uniform(points: np.ndarray, step: float) -> np.ndarray:
    """Resample an open polyline onto uniform arc-length steps of `step`.

    Unlike the aggregation's `_resample_polyline`, which asks for a fixed COUNT,
    this asks for a fixed SPACING: the sensor below counts turns per unit of arc,
    so every stroke of every glyph has to be read on the same ruler — a fixed
    count would measure a long stroke more coarsely than a short one and make
    the rates incomparable. The final point is kept, so the last step may be
    shorter. Returns fewer than three points when there is nothing to turn on.
    """
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(pts) < 2 or step <= 0.0:
        return pts
    steps = np.hypot(*np.diff(pts, axis=0).T)
    cumulative = np.concatenate([[0.0], np.cumsum(steps)])
    total = float(cumulative[-1])
    if total <= 0.0:
        return pts[:1]
    targets = np.arange(0.0, total, step)
    if targets[-1] < total:
        targets = np.append(targets, total)
    return np.column_stack([np.interp(targets, cumulative, pts[:, 0]), np.interp(targets, cumulative, pts[:, 1])])


def zigzag_rate(chart_row: Any, anchors: Sequence[Sequence[float]]) -> float:
    """How often the rendered row reverses its curvature, per x-height of arc.

    The Glätte-Sensor of LF11 (qualitaetsmetrik.md §14 `sep02`) and the one
    quantity that names the defect the audit of 2026-09-02 put first: a stored
    running form wanders left-right-left along its own path 2–11 times per
    x-height where the chart row it was derived from wanders zero times, and
    every bound word renders it. No frozen ruler sees it — both the word bench
    and the ink follower resample the wobble away before they score — so it
    needed a sensor of its own before it could be moved.

    Measured on the RENDERED centerline (the chart's sample plan over the given
    anchors, exactly as `head_deviation` reads its landing) rather than on the
    anchor polyline: what a reader sees is the drawn spline, and the anchors are
    only its control net. Each pen-stroke is resampled onto `ZIGZAG_STEP_UNITS`
    of arc, the turn angle at each interior sample is taken, and a sign change
    between consecutive turns counts when at least one of the two exceeds
    `ZIGZAG_TURN_MIN_DEG` — a stroke's genuine inflections (an `e`'s loop into
    its exit) are few and large, while the median jitter is many and small, and
    the threshold is what separates them from the sampler's own rounding.

    Pen lifts never count, as in `anchor_spike_ratio`: strokes are read one at a
    time and their counts and arcs pooled, so the jump from an i's body to its
    dot is not a reversal. Returns 0.0 when there is no arc to judge.
    """
    total_arc = 0.0
    reversals = 0
    for line in _rendered_strokes(chart_row, anchors):
        pts = _resample_uniform(line, ZIGZAG_STEP_UNITS)
        if len(pts) < 3:
            continue
        deltas = np.diff(pts, axis=0)
        arc = float(np.hypot(*deltas.T).sum())
        if arc <= 0.0:
            continue
        total_arc += arc
        headings = np.arctan2(deltas[:, 1], deltas[:, 0])
        turns = np.degrees((np.diff(headings) + np.pi) % (2.0 * np.pi) - np.pi)
        if len(turns) < 2:
            continue
        a, b = turns[:-1], turns[1:]
        loud = np.maximum(np.abs(a), np.abs(b)) > ZIGZAG_TURN_MIN_DEG
        reversals += int(np.count_nonzero((a * b < 0.0) & loud))
    return 0.0 if total_arc <= 0.0 else reversals / total_arc


def smoothness_gap(chart_row: Any, anchors: Sequence[Sequence[float]]) -> dict[str, Any]:
    """The sensor's reading for one candidate row beside its own chart row.

    `gap` is candidate − chart, in reversals per x-height: positive means the
    row wobbles more than the drawn form it was derived from. That difference,
    not the absolute rate, is the comparable quantity — a curly capital turns
    more often than an `l` for reasons that are ductus, not defect.
    """
    chart = round(zigzag_rate(chart_row, chart_row.anchors), 4)
    candidate = round(zigzag_rate(chart_row, anchors), 4)
    return {"chart": chart, "candidate": candidate, "gap": round(candidate - chart, 4)}


# ----------------------------------------------------------------- form distance (LF10)


def _sampled_strokes(chart_row: Any, anchors: Sequence[Sequence[float]]) -> list[np.ndarray]:
    """Every pen-stroke's centerline as the renderer samples it, in the
    template frame (no slant). One `(k, 2)` array per stroke of
    `stroke_slices`, in writing order; a stroke the plan cannot sample falls
    back to its own anchor polyline, so the list always lines up with the
    anchor ranges and no stroke is ever empty.

    What the CHART ROW supplies is the plan's structure — stroke starts,
    corner knots, widths, QUALITY_N_SAMPLES — while the plan's chord-length
    allocation across sub-arcs follows the anchors actually passed in. That
    asymmetry is deliberate and does not reach the measurement: the sample
    count only sets how densely the SAME spline is discretised, and LF10
    measures a distance to the resulting polyline, not sample against sample.
    Probed on a sub-arc split flipped from 55/186 to 180/61 samples: the p90
    moved by 0.000000 nib radii.
    """
    pts = np.asarray(anchors, dtype=float).reshape(-1, 2)
    meta = getattr(chart_row, "trace_meta", None) or {}
    starts = meta.get("stroke_starts")
    ranges = stroke_slices(len(pts), starts)
    raw = [pts[a:b] for a, b in ranges]
    if len(pts) < 2:
        return raw
    half_widths = _half_widths(chart_row)
    if len(half_widths) != len(pts):
        half_widths = np.full(len(pts), float(half_widths.mean()) if len(half_widths) else _FALLBACK_NIB_RADIUS)
    plan = build_sample_plan(pts, starts, meta.get("corner_anchors"), QUALITY_N_SAMPLES)
    sx, sy, _sw = sample_with_sample_plan(pts, half_widths, plan)
    bounds = [*plan.sample_starts, len(sx)]
    sampled = [np.column_stack([sx[a:b], sy[a:b]]) for a, b in zip(bounds[:-1], bounds[1:], strict=True)]
    if len(sampled) != len(raw):
        return raw
    return [line if len(line) >= 2 else raw[i] for i, line in enumerate(sampled)]


def _distances_to_polyline(points: np.ndarray, line: np.ndarray) -> np.ndarray:
    """Exact distance of every point to a polyline — the nearest point on any
    of its segments, not merely the nearest vertex."""
    if len(line) == 0:
        return np.full(len(points), np.inf)
    if len(line) == 1:
        return np.linalg.norm(points - line[0], axis=1)
    a, b = line[:-1], line[1:]
    ab = b - a
    ab2 = np.einsum("ij,ij->i", ab, ab)
    ab2 = np.where(ab2 > 0.0, ab2, 1.0)
    ap = points[:, None, :] - a[None, :, :]
    t = np.clip(np.einsum("kmj,mj->km", ap, ab) / ab2[None, :], 0.0, 1.0)
    foot = a[None, :, :] + t[..., None] * ab[None, :, :]
    return np.linalg.norm(points[:, None, :] - foot, axis=2).min(axis=1)


def _summary(values: np.ndarray) -> dict[str, Any]:
    return {
        "median": round(float(np.median(values)), 4),
        "p90": round(float(np.percentile(values, 90)), 4),
        "max": round(float(np.max(values)), 4),
        "argmax": int(np.argmax(values)),
        "values": [round(float(v), 4) for v in values],
    }


def form_distance(
    chart_row: Any, anchors: Sequence[Sequence[float]], *, same_stroke: bool = True, rendered: bool = True
) -> dict[str, Any]:
    """The form distance of a candidate row to its chart row (LF10,
    qualitaetsmetrik.md §14 `sep01`): how far the running form leaves the
    chart's path, per anchor, in chart nib radii.

    Both rows are rendered with the chart's sample plan (`_sampled_strokes`,
    the renderer's own sampler — the anchor polyline misreads the dense
    capital heads, §14 LF9). Per anchor of the ROW the distance to the chart's
    rendered centerline of THE SAME stroke (the row shares the chart's stroke
    starts), and per anchor of the CHART the distance to the row's rendered
    centerline of the same stroke — two directions, reported separately
    (tracebench practice: no symmetric mean). Both in nib radii of the chart,
    `r` = median of its `half_widths` — `_FALLBACK_NIB_RADIUS` when the row
    carries no widths at all (NULL or empty) or none of them is positive, so a
    width-less row is measured rather than refused. The gate quantity is the
    worse directional p90: a form defect is LOCAL (a segment, a stroke, a bow — a
    minority of the anchors) while the hand's legitimate deviation is GLOBAL
    and smooth (width, a head angle), so p90 sees the one and not the other;
    the median and the maximum ride along as the pre-registered sensitivity
    checks, as does the index-wise `correspondence` distance |row_i − chart_i|
    (it carries the longitudinal extent LF5/LF6 found to be the hand's own).

    No rigid registration beforehand: the fit keeps the global translation in
    the placement (`core/fit.py`, `fitted_anchors = template_anchors +
    deltas`), so the row's anchors already live in the chart's frame and any
    shift in them IS form or width.

    Args:
        chart_row: The variant-0 template (ORM row or an attribute view with
            `anchors`, `half_widths`, `trace_meta`).
        anchors: The candidate row's anchors, same count as the chart's.
        same_stroke: Measure against the same stroke (default); False takes
            the nearest point of ANY stroke (sensitivity check e).
        rendered: Measure against the rendered centerline (default); False
            uses the bare anchor polylines (sensitivity check f).

    Returns:
        `nib_radius`, `row_to_chart` and `chart_to_row` (each with `median`,
        `p90`, `max`, `argmax` and the per-anchor `values`), the worse-direction
        `median` / `p90` / `max` at the top level with `p90_direction`, and
        `correspondence` (index-wise, same summary shape).

    Raises:
        ValueError: If the two anchor lists differ in length.
    """
    chart_pts = np.asarray(chart_row.anchors, dtype=float).reshape(-1, 2)
    row_pts = np.asarray(anchors, dtype=float).reshape(-1, 2)
    if len(chart_pts) != len(row_pts):
        raise ValueError(f"anchor count {len(row_pts)} != chart row's {len(chart_pts)}")
    if len(chart_pts) == 0:
        raise ValueError("need at least 1 anchor")
    half_widths = _half_widths(chart_row)
    radius = float(np.median(half_widths)) if len(half_widths) else 0.0
    if not radius > 0.0:  # also catches a NaN median
        radius = _FALLBACK_NIB_RADIUS
    meta = getattr(chart_row, "trace_meta", None) or {}
    ranges = stroke_slices(len(chart_pts), meta.get("stroke_starts"))
    if rendered:
        chart_lines = _sampled_strokes(chart_row, chart_pts)
        row_lines = _sampled_strokes(chart_row, row_pts)
    else:
        chart_lines = [chart_pts[a:b] for a, b in ranges]
        row_lines = [row_pts[a:b] for a, b in ranges]

    def one_direction(points: np.ndarray, lines: list[np.ndarray]) -> np.ndarray:
        if same_stroke:
            out = np.zeros(len(points))
            for (a, b), line in zip(ranges, lines, strict=True):
                out[a:b] = _distances_to_polyline(points[a:b], line)
            return out / radius
        return np.min(np.stack([_distances_to_polyline(points, line) for line in lines]), axis=0) / radius

    row_to_chart = one_direction(row_pts, chart_lines)
    chart_to_row = one_direction(chart_pts, row_lines)
    correspondence = np.linalg.norm(row_pts - chart_pts, axis=1) / radius
    a, b = _summary(row_to_chart), _summary(chart_to_row)
    worse = "row_to_chart" if a["p90"] >= b["p90"] else "chart_to_row"
    return {
        "nib_radius": round(radius, 4),
        "row_to_chart": a,
        "chart_to_row": b,
        "median": max(a["median"], b["median"]),
        "p90": max(a["p90"], b["p90"]),
        "max": max(a["max"], b["max"]),
        "p90_direction": worse,
        "correspondence": _summary(correspondence),
    }
