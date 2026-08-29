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


Point = tuple[float, float]

# Arc-length window (x-height units, measured on the chart stroke) over which
# each free stroke end is blended back to the chart geometry — the one knob of
# the LF5/LF6 pre-registrations (ladder {0.25, 0.5}). 0.0 disables the blend:
# the pre-LF5 row, anchors verbatim. Adopted only by a passed gate (§14).
LAUFFORM_END_WINDOW = 0.0

_DECIMALS = 4


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
