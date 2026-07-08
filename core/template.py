"""Canonical ductus template — dataclasses, chord-length sampling, outline polygon.

Coordinate convention (per Loth Kurrent default of 2:1:2 — but the ratio
is *data* on the Source row, not a hardcoded constant; callers pass the
ascender/descender heights when they need guide lines):
    baseline   y = 0           anchor of most glyphs' start/end
    midband    y = 1            top of x-height region
    ascender   y = 1 + a/x       e.g. 3 for [2,1,2] (1 + 2/1)
    descender  y = -d/x          e.g. -2 for [2,1,2]
    x          left-to-right

The matplotlib `render` helper was removed in the refactor — the frontend
draws the canonical preview as SVG from the data this module produces.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import numpy as np
import shapely
from scipy.interpolate import CubicSpline
from shapely.geometry import LineString, MultiPoint, Point

from core.widths import BroadNib


def sample_polyline(
    anchors: np.ndarray, half_widths: np.ndarray, n: int = 200
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample a polyline (chord-length parameterised cubic spline) at `n` points.

    Each anchor pairs with the same parameter t (cumulative chord length,
    normalised). x(t) and y(t) are interpolated independently with
    `scipy.interpolate.CubicSpline` — this handles paths that double back on
    themselves (loops, self-crossings — the medial-e case) without smoothing
    the loop away the way a global B-spline would.

    Returns (x, y, half_width) arrays of length n.
    """
    anchors = np.asarray(anchors, dtype=float)
    widths = np.asarray(half_widths, dtype=float)
    if len(anchors) < 2:
        return anchors[:, 0], anchors[:, 1], widths
    diffs = np.diff(anchors, axis=0)
    chord = np.hypot(diffs[:, 0], diffs[:, 1])
    t = np.concatenate([[0.0], np.cumsum(chord)])
    if t[-1] == 0:
        return np.tile(anchors[:1, 0], n), np.tile(anchors[:1, 1], n), np.tile(widths[:1], n)
    t = t / t[-1]
    if len(anchors) < 3:
        u = np.linspace(0.0, 1.0, n)
        sx = np.interp(u, t, anchors[:, 0])
        sy = np.interp(u, t, anchors[:, 1])
        sw = np.interp(u, t, widths)
        return sx, sy, sw
    cs_x = CubicSpline(t, anchors[:, 0], bc_type="natural")
    cs_y = CubicSpline(t, anchors[:, 1], bc_type="natural")
    u = np.linspace(0.0, 1.0, n)
    return cs_x(u), cs_y(u), np.interp(u, t, widths)


def stroke_outline(x: np.ndarray, y: np.ndarray, half_width: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Closed polygon outlining a centerline with variable half-width.

    The Schwellzug is rendered by offsetting the centerline by ± half_width
    along the local normal, then closing left-going + right-coming-back into
    one polygon. Caller fills it.
    """
    dx = np.gradient(x)
    dy = np.gradient(y)
    norm = np.hypot(dx, dy)
    norm[norm == 0] = 1.0
    nx = -dy / norm
    ny = dx / norm
    left_x = x + nx * half_width
    left_y = y + ny * half_width
    right_x = x - nx * half_width
    right_y = y - ny * half_width
    poly_x = np.concatenate([left_x, right_x[::-1]])
    poly_y = np.concatenate([left_y, right_y[::-1]])
    return poly_x, poly_y


def apply_slant(x: np.ndarray, y: np.ndarray, slant_deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Shear so that vertical lines make `slant_deg` degrees with the baseline.

    `slant_deg` is the Schräglage (slant angle measured from the baseline, the
    convention used repo-wide): 90 = upright (identity), smaller = stronger
    right lean. Operates in template coordinates (y up, baseline at y=0), so
    x' = x + y*tan(90° - slant_deg) moves points above the baseline right and
    descenders left — Kurrent's right-leaning look.
    """
    if abs(slant_deg - 90.0) < 1e-6:
        return x, y
    theta = np.deg2rad(90.0 - slant_deg)
    return x + y * np.tan(theta), y


# ------------------------------------------------------------- multi-stroke ductus
#
# A glyph's ductus can be several pen-strokes with the pen lifted between them
# (German: Absetzen) — e.g. the two downstrokes of a u. Those strokes must stay
# separate: a single centerline that bridges the lift would draw a spurious line
# (and a filled bar in the outline) across the gap. `stroke_starts` lists the
# anchor index at which each stroke begins (the first is always 0); a falsy /
# single-element value is the legacy single-stroke case, so old templates sample
# and render exactly as before.


def chord_length(points: np.ndarray) -> float:
    """Total polyline length (sum of segment chords) of an Mx2 point array."""
    points = np.asarray(points, dtype=float)
    if len(points) < 2:
        return 0.0
    d = np.diff(points, axis=0)
    return float(np.hypot(d[:, 0], d[:, 1]).sum())


def stroke_slices(n_anchors: int, stroke_starts: Sequence[int] | None) -> list[tuple[int, int]]:
    """`(start, end)` anchor index ranges for each stroke of an n-anchor array.

    Falsy / single-element `stroke_starts` yields one slice spanning the whole
    array (the single-stroke / legacy case).
    """
    if not stroke_starts or len(stroke_starts) <= 1:
        return [(0, n_anchors)]
    starts = sorted({0, *(int(s) for s in stroke_starts if 0 < int(s) < n_anchors)})
    ends = starts[1:] + [n_anchors]
    return list(zip(starts, ends, strict=True))


def allocate_samples(seg_lengths: Sequence[float], n: int) -> list[int]:
    """Distribute `n` samples across segments proportional to length, ≥2 each.

    When `n` is too small to give every segment two samples it grows to
    `2 * len(seg_lengths)`. Any rounding remainder goes to the longest segment so
    the totals always add up.
    """
    k = len(seg_lengths)
    if k == 0:
        return []
    if k == 1:
        return [max(2, n)]
    n = max(n, 2 * k)
    alloc = [2] * k
    remaining = n - 2 * k
    total_len = float(sum(seg_lengths))
    if remaining > 0 and total_len > 0:
        extra = [int(remaining * (length / total_len)) for length in seg_lengths]
        alloc = [a + e for a, e in zip(alloc, extra, strict=True)]
        deficit = n - sum(alloc)
        if deficit > 0:
            longest = max(range(k), key=lambda i: seg_lengths[i])
            alloc[longest] += deficit
    elif remaining > 0:  # all degenerate (zero length): spread evenly
        for i in range(remaining):
            alloc[i % k] += 1
    return alloc


def stroke_sample_plan(
    anchors: np.ndarray, stroke_starts: Sequence[int] | None, n: int
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """Fixed per-stroke sampling plan for a (possibly multi-stroke) anchor set.

    Returns `(slices, alloc, sample_starts)`: the per-stroke anchor ranges, how
    many samples each stroke gets (proportional to chord length, summing to ≥n),
    and the index of each stroke's first sample in the concatenated output.
    Computing the plan once (from the canonical anchors) lets the canonical and a
    fitted variant sample identically — equal length, aligned — even as the fit
    nudges the anchors.
    """
    anchors = np.asarray(anchors, dtype=float)
    slices = stroke_slices(len(anchors), stroke_starts)
    if len(slices) == 1:
        return slices, [max(2, n)], [0]
    seg_lengths = [chord_length(anchors[a:b]) for a, b in slices]
    alloc = allocate_samples(seg_lengths, n)
    sample_starts, cursor = [], 0
    for k in alloc:
        sample_starts.append(cursor)
        cursor += k
    return slices, alloc, sample_starts


def sample_with_plan(
    anchors: np.ndarray, half_widths: np.ndarray, slices: list[tuple[int, int]], alloc: list[int]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample each stroke independently per a `stroke_sample_plan` and concatenate.

    No sample point lands on the pen-lift bridge between strokes, so a centerline
    built from the result skips the gap instead of crossing it.
    """
    anchors = np.asarray(anchors, dtype=float)
    half_widths = np.asarray(half_widths, dtype=float)
    if len(slices) == 1:
        return sample_polyline(anchors, half_widths, n=alloc[0])
    xs, ys, ws = [], [], []
    for (a, b), k in zip(slices, alloc, strict=True):
        sx, sy, sw = sample_polyline(anchors[a:b], half_widths[a:b], n=k)
        xs.append(sx)
        ys.append(sy)
        ws.append(sw)
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(ws)


# ------------------------------------------------------------- corner knots
#
# A corner knot (German: Umkehrpunkt) is a within-stroke reversal — the pen
# stays down but changes direction sharply (e.g. the angular joints of the
# Loth K). A single chord-length spline through such a point rounds it away;
# splitting the spline there (independent natural splines per sub-arc, shared
# corner anchor, C0 but not C2 across) renders a true kink. Corner anchors are
# detected on the dense raw trace (`core.pipeline`), stored as anchor indices
# in `trace_meta["corner_anchors"]`, and consumed here. A missing/empty list
# reproduces the old sampling bit for bit.


@dataclass(frozen=True)
class SamplePlan:
    """Frozen sampling plan over sub-arcs (pen strokes split at corner knots).

    `slices`/`alloc` are the sub-arc anchor ranges and their sample counts;
    consecutive sub-arcs of one stroke SHARE the corner anchor, so the corner
    sample is produced twice — `drop_rows` lists the duplicated rows (pre-drop
    indices) to delete after concatenation. `sample_starts` indexes each PEN
    STROKE's first sample in the post-drop arrays (the animation/outline
    contract stays per stroke — the pen does not lift at a corner), and
    `corner_sample_idx` the surviving sample of each corner.
    """

    slices: list[tuple[int, int]]
    alloc: list[int]
    sample_starts: list[int]
    drop_rows: list[int]
    corner_sample_idx: list[int]


def build_sample_plan(
    anchors: np.ndarray, stroke_starts: Sequence[int] | None, corner_anchors: Sequence[int] | None, n: int
) -> SamplePlan:
    """Sampling plan for a multi-stroke anchor set with optional corner knots.

    Without corners this degenerates to `stroke_sample_plan` exactly (same
    slices, same allocation, no dropped rows). With corners, each stroke is
    split at its interior corner anchors; samples are allocated over all
    sub-arcs proportional to chord length (`n` plus one per corner, so the
    post-drop total is ≈ n).
    """
    anchors = np.asarray(anchors, dtype=float)
    stroke_ranges = stroke_slices(len(anchors), stroke_starts)
    corners = sorted({int(c) for c in (corner_anchors or [])})

    sub_arcs: list[tuple[int, int]] = []
    arc_stroke: list[int] = []  # which pen stroke each sub-arc belongs to
    for s, (a, b) in enumerate(stroke_ranges):
        start = a
        for c in (c for c in corners if a < c < b - 1):
            sub_arcs.append((start, c + 1))
            arc_stroke.append(s)
            start = c
        sub_arcs.append((start, b))
        arc_stroke.append(s)

    n_corner_dups = len(sub_arcs) - len(stroke_ranges)
    if len(sub_arcs) == 1:
        alloc = [max(2, n)]
    else:
        seg_lengths = [chord_length(anchors[p:q]) for p, q in sub_arcs]
        alloc = allocate_samples(seg_lengths, n + n_corner_dups)

    sample_starts: list[int] = []
    drop_rows: list[int] = []
    corner_sample_idx: list[int] = []
    cursor = dropped = 0
    prev_stroke = -1
    for k, s in zip(alloc, arc_stroke, strict=True):
        if s != prev_stroke:
            sample_starts.append(cursor - dropped)
            prev_stroke = s
        else:
            # Same stroke continuing through a corner: the sub-arc's first
            # sample duplicates the previous sub-arc's last (the shared
            # corner anchor) — drop it, remember the surviving corner row.
            drop_rows.append(cursor)
            corner_sample_idx.append(cursor - dropped - 1)
            dropped += 1
        cursor += k
    return SamplePlan(sub_arcs, alloc, sample_starts, drop_rows, corner_sample_idx)


def sample_with_sample_plan(
    anchors: np.ndarray, half_widths: np.ndarray, plan: SamplePlan
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample each sub-arc independently per a `SamplePlan` and concatenate.

    Independent natural splines per sub-arc give a true C0 kink at each corner
    knot; duplicated corner rows are removed per `plan.drop_rows`. Without
    corners the output equals `sample_with_plan` bit for bit.
    """
    anchors = np.asarray(anchors, dtype=float)
    half_widths = np.asarray(half_widths, dtype=float)
    xs, ys, ws = [], [], []
    for (a, b), k in zip(plan.slices, plan.alloc, strict=True):
        if b - a < 2:
            # Degenerate sub-arc: replicate so the plan's row bookkeeping holds.
            xs.append(np.full(k, anchors[a, 0]))
            ys.append(np.full(k, anchors[a, 1]))
            ws.append(np.full(k, half_widths[a] if len(half_widths) > a else 0.0))
            continue
        sx, sy, sw = sample_polyline(anchors[a:b], half_widths[a:b], n=k)
        xs.append(sx)
        ys.append(sy)
        ws.append(sw)
    sx = np.concatenate(xs)
    sy = np.concatenate(ys)
    sw = np.concatenate(ws)
    if plan.drop_rows:
        sx = np.delete(sx, plan.drop_rows)
        sy = np.delete(sy, plan.drop_rows)
        sw = np.delete(sw, plan.drop_rows)
    return sx, sy, sw


def _multi_stroke_samples(
    anchors: np.ndarray,
    half_widths: np.ndarray,
    stroke_starts: Sequence[int] | None,
    slant_deg: float,
    n: int,
    corner_anchors: Sequence[int] | None = None,
) -> Iterator[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Yield `(sx, sy, sw)` slant-applied centerline samples for each pen-stroke.

    Each stroke is sampled on its own (never across a pen lift) via a shared
    `SamplePlan`, so an outline and a centerline derived from the *same* call
    stay point-for-point aligned — the centerline runs down the spine of the
    matching outline polygon. Corner knots split the spline within a stroke
    (true kink) without splitting the yielded stroke itself.
    """
    anchors = np.asarray(anchors, dtype=float)
    half_widths = np.asarray(half_widths, dtype=float)
    if len(anchors) < 2:
        return
    plan = build_sample_plan(anchors, stroke_starts, corner_anchors, n)
    sx, sy, sw = sample_with_sample_plan(anchors, half_widths, plan)
    bounds = [*plan.sample_starts, len(sx)]
    for a, b in zip(bounds[:-1], bounds[1:], strict=True):
        if b - a < 2:
            continue
        x, y = apply_slant(sx[a:b], sy[a:b], slant_deg)
        yield x, y, sw[a:b]


def multi_stroke_outline(
    anchors: np.ndarray,
    half_widths: np.ndarray,
    stroke_starts: Sequence[int] | None,
    slant_deg: float,
    n: int = 240,
    corner_anchors: Sequence[int] | None = None,
) -> list[list[list[float]]]:
    """One closed outline polygon per stroke (slant applied) — never bridging a lift.

    Splitting at the pen-lift boundaries keeps `stroke_outline` from filling a bar
    across the gap between two separate strokes. Returns a list of polygons (each a
    list of `[x, y]`); the legacy single-stroke case returns a one-element list.
    """
    polygons: list[list[list[float]]] = []
    for sx, sy, sw in _multi_stroke_samples(anchors, half_widths, stroke_starts, slant_deg, n, corner_anchors):
        poly_x, poly_y = stroke_outline(sx, sy, sw)
        polygons.append([[round(float(x), 4), round(float(y), 4)] for x, y in zip(poly_x, poly_y, strict=True)])
    return polygons


def capsule_union_rings(
    x: np.ndarray, y: np.ndarray, half_width: np.ndarray, simplify_tol: float = 0.0, decimals: int = 4
) -> list[list[list[float]]]:
    """Silhouette of a variable-width centerline as rings (exterior + holes).

    Builds one round-capped capsule per sample segment (radius = mean of the
    adjacent half-widths) and unions them. Unlike the ±normal ribbon of
    `stroke_outline`, the union cannot self-intersect where the curvature
    radius drops below the half-width (Kurrent loops), it keeps loop counters
    (the e-eye) as real holes, and the stroke ends are round like a lifting
    nib. Returns a flat list of rings as [x, y] lists; render all rings of one
    stroke as a single path with fill-rule evenodd, so exterior/hole pairing
    never needs to be resolved explicitly. `decimals` matches the coordinate
    space: 4 for template units, 2 is plenty for crop pixels.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    hw = np.maximum(np.asarray(half_width, dtype=float), 1e-3)
    if len(x) == 0:
        return []
    if len(x) == 1:
        shapes = [Point(x[0], y[0]).buffer(hw[0])]
    else:
        shapes = [
            LineString([(x[i], y[i]), (x[i + 1], y[i + 1])]).buffer(float((hw[i] + hw[i + 1]) / 2.0))
            for i in range(len(x) - 1)
        ]
    merged = shapely.union_all(shapes)
    if simplify_tol > 0:
        merged = merged.simplify(simplify_tol, preserve_topology=True)
    polygons = merged.geoms if merged.geom_type == "MultiPolygon" else [merged]
    rings: list[list[list[float]]] = []
    for poly in polygons:
        if poly.is_empty:
            continue
        for ring in (poly.exterior, *poly.interiors):
            rings.append([[round(float(px), decimals), round(float(py), decimals)] for px, py in ring.coords])
    return rings


def chisel_union_rings(
    x: np.ndarray, y: np.ndarray, nib: BroadNib, simplify_tol: float = 0.0, decimals: int = 4
) -> list[list[list[float]]]:
    """Silhouette of a broad-nib (Bandzugfeder) stroke as rings.

    The W × t nib rectangle held at the fixed angle alpha is swept along the
    centerline: per segment the Minkowski sum is the convex hull of the
    rectangle stamped at both endpoints; the union over all segments is the
    stroke. Chisel ends fall out as the stamped nib edge (never round caps —
    the nib edge IS the cap), a path moving parallel to the edge pinches to
    the edge thickness t, and loops/reversals are resolved by the union like
    in `capsule_union_rings`. Same ring/evenodd payload contract.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) == 0:
        return []
    hx, hy = nib.half_vector
    ex, ey = nib.edge_vector

    def stamp(px: float, py: float) -> list[tuple[float, float]]:
        return [
            (px + hx + ex, py + hy + ey),
            (px + hx - ex, py + hy - ey),
            (px - hx + ex, py - hy + ey),
            (px - hx - ex, py - hy - ey),
        ]

    if len(x) == 1:
        shapes = [MultiPoint(stamp(x[0], y[0])).convex_hull]
    else:
        shapes = [MultiPoint(stamp(x[i], y[i]) + stamp(x[i + 1], y[i + 1])).convex_hull for i in range(len(x) - 1)]
    merged = shapely.union_all(shapes)
    if simplify_tol > 0:
        merged = merged.simplify(simplify_tol, preserve_topology=True)
    # A degenerate nib (zero width AND edge) collapses the stamps to
    # lines/points and the union to a non-area geometry — extract whatever
    # polygons exist and return [] gracefully for pure-line unions.
    if merged.geom_type in ("MultiPolygon", "GeometryCollection"):
        polygons = list(merged.geoms)
    else:
        polygons = [merged]
    rings: list[list[list[float]]] = []
    for poly in polygons:
        if poly.is_empty or poly.geom_type != "Polygon":
            continue
        for ring in (poly.exterior, *poly.interiors):
            rings.append([[round(float(px), decimals), round(float(py), decimals)] for px, py in ring.coords])
    return rings


def multi_stroke_silhouettes(
    anchors: np.ndarray,
    half_widths: np.ndarray,
    stroke_starts: Sequence[int] | None,
    slant_deg: float,
    n: int = 240,
    corner_anchors: Sequence[int] | None = None,
    nib: BroadNib | None = None,
) -> list[list[list[list[float]]]]:
    """One silhouette (ring list) per pen-stroke, slant applied.

    Same sampling as `multi_stroke_outline`/`multi_stroke_centerlines`, so the
    silhouettes stay aligned with the animated centerline sweep. Default pen
    is the round capsule union; passing a `nib` sweeps the Bandzugfeder
    rectangle instead (broad_nib styles — widths then come from the nib, the
    sampled width channel is ignored). The simplify tolerance is in template
    units (x-height = 1): 0.002 ≈ a fifteenth of a pixel at typical chart
    resolution — invisible, but it halves the payload.
    """
    if nib is not None:
        return [
            chisel_union_rings(sx, sy, nib, simplify_tol=0.002)
            for sx, sy, _sw in _multi_stroke_samples(anchors, half_widths, stroke_starts, slant_deg, n, corner_anchors)
        ]
    return [
        capsule_union_rings(sx, sy, sw, simplify_tol=0.002)
        for sx, sy, sw in _multi_stroke_samples(anchors, half_widths, stroke_starts, slant_deg, n, corner_anchors)
    ]


def multi_stroke_centerlines(
    anchors: np.ndarray,
    half_widths: np.ndarray,
    stroke_starts: Sequence[int] | None,
    slant_deg: float,
    n: int = 240,
    corner_anchors: Sequence[int] | None = None,
) -> list[list[list[float]]]:
    """One slant-applied centerline polyline per pen-stroke, in writing order.

    Sampled identically to `multi_stroke_outline`, so each polyline runs down the
    spine of its outline polygon. The frontend animates "as written" by sweeping a
    wide stroke along these polylines stroke-by-stroke (the ductus), revealing the
    filled silhouette in the order the pen drew it. Returns a list of `[x, y]`
    point lists, one per stroke; the legacy single-stroke case is a one-element list.
    """
    lines: list[list[list[float]]] = []
    for sx, sy, _sw in _multi_stroke_samples(anchors, half_widths, stroke_starts, slant_deg, n, corner_anchors):
        lines.append([[round(float(x), 4), round(float(y), 4)] for x, y in zip(sx, sy, strict=True)])
    return lines


def template_guides(style_ratio: list[float]) -> dict[str, float]:
    """Baseline/midband/ascender/descender y-coords for a given style ratio.

    `style_ratio` is [ascender, x_height, descender]; for Loth's [2,1,2] this
    yields baseline=0, midband=1, ascender=3, descender=-2.
    """
    a, x, d = style_ratio
    return {"baseline": 0.0, "midband": 1.0, "ascender": 1.0 + float(a) / float(x), "descender": -float(d) / float(x)}
