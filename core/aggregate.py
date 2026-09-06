"""Per-hand aggregation of stored occurrences (Stufenplan H1/H2, §12 layer 2).

Two levels, the same shape — median form, MAD hull, pooled statistics — always
over the occurrences of ONE hand.

`aggregate_instances` (H1) turns the `instances` rows into one aggregate per
`(glyph_key, variant)`: the per-anchor median (the running form — occurrence
anchors are stored CENTERED onto the chart template, "shapes, not placements",
so the elementwise median over them reproduces the harvested Laufform), the
per-anchor spread as a median absolute deviation hull, and the pooled layer-1
statistics.

`aggregate_pair_instances` (H2) turns the `pair_instances` rows into one
aggregate per `(left_key, right_key)` — the natural transition's distribution
rather than the letters': the median placement offset and the per-point median
of the arc-length-resampled connector centerlines, plus the pooled dissection
QC.

Pure Python/numpy with no DB or HTTP imports, and it lives in `core/` rather
than `tools/` for the same reason `core/word_metric.py` does: the API image
ships no `tools/`, and the admin rebuild endpoint must compute the SAME medians
the laufform harvest prints.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np


# Geometry is stored in normalised template coordinates (baseline = 0,
# midband = 1), so four decimals are well below any measurable difference.
_GEOMETRY_DECIMALS = 4
_STATS_DECIMALS = 3


# The fewest occurrences a per-anchor median may be PROMOTED INTO THE WRITING
# PATH from — the floor `apply-laufform` enforces (`LOW_N` in the SPA's
# `laufformPreview.ts` mirrors it).
#
# Three is not a taste threshold, it is where the median starts working: at
# n = 2 `np.median` returns the MEAN of the two, so a single blown-up fitted
# anchor lands in the result at half its amplitude, and nothing in the chain
# pulls it back — neighbouring anchors are medianed independently. From three
# occurrences on, one bad anchor is outvoted.
#
# The failure is not hypothetical. The Sütterlin capital S was derived from two
# occurrences whose anchor 113 sits 0.357 units apart (its neighbours: 0.01 –
# 0.03); the half of that difference showed up as a visible spike off the top
# right of every written S, while the occurrence that carried it passed its own
# per-glyph fit QC at 1.261 px RMSE. Seeing such a median is still measurement —
# `aggregate_instances` keeps its own, separate `min_n` gate at the caller's
# discretion (the rebuild endpoint deliberately passes 1, issue #273) — but
# writing it is rendering.
LAUFFORM_MIN_OCCURRENCES = 3


def _median_and_mad(stack: np.ndarray) -> tuple[list[list[float]], list[list[float]]]:
    """Per-anchor, per-axis median and median absolute deviation.

    Args:
        stack: Array of shape (n_instances, n_anchors, 2).

    Returns:
        Tuple of (median anchors, MAD per anchor), both as nested lists of
        rounded floats in template coordinates.
    """
    median = np.median(stack, axis=0)
    mad = np.median(np.abs(stack - median), axis=0)
    return (median.round(_GEOMETRY_DECIMALS).tolist(), mad.round(_GEOMETRY_DECIMALS).tolist())


# Spline-basis median (LF11, messjournal.md §14 `sep02`). The degree is
# the lowest one with continuous curvature — and curvature is exactly the
# quantity whose sign changes the smoothness sensor counts, so a lower degree
# would leave the defect representable in the basis meant to exclude it.
SPLINE_MEDIAN_DEGREE = 3


def _stroke_bounds(n_anchors: int, stroke_starts: Sequence[int] | None) -> list[tuple[int, int]]:
    """Half-open [start, end) index ranges of the pen-strokes over `n_anchors`."""
    marks = sorted({0, *(int(s) for s in (stroke_starts or []) if 0 < int(s) < n_anchors), n_anchors})
    return list(zip(marks[:-1], marks[1:], strict=True))


def _knot_vector(arc: np.ndarray, corners: Sequence[int], spacing: float, degree: int) -> np.ndarray:
    """Clamped knot vector over [0, arc[-1]]: evenly spaced interior knots as
    close to `spacing` as a whole number of spans allows, plus every corner as a
    knot of multiplicity `degree`.

    `spacing` is a target, not an exact step. The stroke is divided into
    `round(total / spacing)` equal spans, so the effective step is
    `total / spans` — up to half a span away from what was asked for, and
    furthest on a short stroke (0.4 xh of arc at a target of 0.32 gives one span
    of 0.4). The alternative, laying exact `spacing` steps from one end, leaves a
    stub span at the other whose control point is poorly determined by the few
    samples inside it — an end artefact in the very estimator meant to remove
    one. An even division has no stub, and the ladder is coarse enough
    (§14 LF11) that the rounding never reorders two rungs.

    The corner multiplicity is what lets the basis DRAW a corner instead of
    rounding it off: at multiplicity `degree` a B-spline is only C⁰ there, which
    is what the chart's `corner_anchors` assert the pen did. A uniform knot that
    lands on a corner is dropped rather than added to it — stacking it past
    `degree` would tear the curve apart at that point.
    """
    total = float(arc[-1])
    spans = max(1, int(round(total / spacing)))
    uniform = [total * i / spans for i in range(1, spans)]
    corner_pos = sorted({float(arc[c]) for c in corners if 0 < c < len(arc) - 1})
    # Half a span is the widest a uniform knot may sit from a corner and still be
    # the same knot; closer than that it only crowds the corner's own stack.
    guard = 0.5 * total / spans
    interior = [u for u in uniform if all(abs(u - c) > guard for c in corner_pos)]
    for c in corner_pos:
        interior.extend([c] * degree)
    return np.asarray([0.0] * (degree + 1) + sorted(interior) + [total] * (degree + 1), dtype=float)


def spline_basis_median(
    stack: np.ndarray,
    chart_anchors: Sequence[Sequence[float]],
    stroke_starts: Sequence[int] | None = None,
    corner_anchors: Sequence[int] | None = None,
    *,
    knot_spacing: float,
    degree: int = SPLINE_MEDIAN_DEGREE,
) -> tuple[np.ndarray, list[str]]:
    """The per-anchor median's smooth twin: median in a B-spline basis (LF11).

    `_median_and_mad` medians each of the 120 anchors on its own, and nothing in
    the model couples a neighbour — so the estimator's own noise survives into
    the written row as a wobble the drawn form never had (2–11 curvature
    reversals per x-height against the chart row's zero; the audit of
    2026-09-02, §14 `sep02`). No frozen ruler sees it, because every one of them
    resamples it away before scoring.

    This median lives one level up. Per pen-stroke, the CHART row's cumulative
    arc length is the common parameter — occurrence-independent, so every
    occurrence projects onto one and the same basis, which is what makes a
    median over control points defined at all. Each occurrence is least-squares
    projected onto a clamped B-spline over that parameter (the chart's corners
    entering as knots of multiplicity `degree`, so a corner stays a corner), the
    median is taken per control point, and the result is evaluated back at the
    chart's own anchor parameters — same anchor count, same topology, same
    downstream canonicalisation.

    Occurrences may be stacked because the harvest stores them centered onto the
    chart template ("shapes, not placements") with the chart's anchor count.

    A stroke with no room for the basis — shorter than two spans, fewer anchors
    than the basis has functions, or a degenerate zero-length arc — keeps the
    per-anchor median for its own index range. The map is total either way, and
    every such fallback is named in the returned notes rather than hidden.

    Args:
        stack: Occurrence anchors, shape (n_occurrences, n_anchors, 2).
        chart_anchors: The chart row's anchors, shape (n_anchors, 2) — the
            parameterisation, never a summand.
        stroke_starts: The chart's `trace_meta.stroke_starts`.
        corner_anchors: The chart's `trace_meta.corner_anchors`.
        knot_spacing: Interior knot spacing in x-height units (the one knob).
        degree: B-spline degree.

    Returns:
        Tuple of (median anchors as an (n_anchors, 2) array, fallback notes).
    """
    from scipy.interpolate import BSpline  # noqa: PLC0415 — heavy import, one call site

    if knot_spacing <= 0.0:
        raise ValueError(f"knot_spacing must be positive, got {knot_spacing}")
    pts = np.asarray(stack, dtype=float)
    if pts.ndim != 3 or pts.shape[2] != 2:
        raise ValueError(f"stack must be (n_occurrences, n_anchors, 2), got {pts.shape}")
    chart = np.asarray(chart_anchors, dtype=float).reshape(-1, 2)
    if len(chart) != pts.shape[1]:
        raise ValueError(f"chart has {len(chart)} anchors, occurrences have {pts.shape[1]}")

    out = np.median(pts, axis=0)
    notes: list[str] = []
    corners = [int(c) for c in (corner_anchors or [])]
    for start, end in _stroke_bounds(len(chart), stroke_starts):
        segment = chart[start:end]
        if len(segment) < degree + 2:
            notes.append(f"stroke {start}:{end} kept the anchor median ({len(segment)} anchors)")
            continue
        arc = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(segment, axis=0).T))])
        total = float(arc[-1])
        if total < 2.0 * knot_spacing:
            notes.append(f"stroke {start}:{end} kept the anchor median (arc {total:.3f} xh < 2 knots)")
            continue
        knots = _knot_vector(arc, [c - start for c in corners if start < c < end - 1], knot_spacing, degree)
        n_basis = len(knots) - degree - 1
        if n_basis > len(segment):
            notes.append(f"stroke {start}:{end} kept the anchor median ({n_basis} basis > {len(segment)} anchors)")
            continue
        design = BSpline.design_matrix(arc, knots, degree).toarray()
        # One factorisation for every occurrence and both axes: the basis depends
        # on the chart alone, so they differ only in the right-hand side. Columns
        # run (occurrence, axis); the median is taken per control point after
        # unstacking them.
        rhs = pts[:, start:end, :].transpose(1, 0, 2).reshape(len(segment), -1)
        control, *_ = np.linalg.lstsq(design, rhs, rcond=None)
        out[start:end] = BSpline(knots, np.median(control.reshape(n_basis, len(pts), 2), axis=1), degree)(arc)
    return out, notes


# ----------------------------------------------------------------- loop-faithful median (LF13)

# Arc-length window (x-height units, on the chart stroke) over which a loop's
# alignment shift fades back to nothing outside the loop — the ONE knob of the
# LF13 pre-registration. 0.0 is OFF and returns the stack unchanged, bit for bit,
# which is what keeps this the estimator the LF11/LF12 rows were derived with
# until a passed gate says otherwise (the pattern of `LAUFFORM_END_WINDOW`).
LAUFFORM_LOOP_WINDOW = 0.0

# The fewest anchors a self-crossing must span to count as a loop rather than as
# a sampling artefact of two strands running parallel.
_LOOP_MIN_SPAN = 4


def _segment_crossing(p0: np.ndarray, p1: np.ndarray, q0: np.ndarray, q1: np.ndarray) -> bool:
    """Do the two closed segments cross?"""
    r, s = p1 - p0, q1 - q0
    denom = r[0] * s[1] - r[1] * s[0]
    if abs(denom) < 1e-15:
        return False
    diff = q0 - p0
    t = (diff[0] * s[1] - diff[1] * s[0]) / denom
    u = (diff[0] * r[1] - diff[1] * r[0]) / denom
    return bool(0.0 <= t <= 1.0 and 0.0 <= u <= 1.0)


def _arc_fraction(points: np.ndarray) -> np.ndarray:
    """Cumulative arc length of a polyline, scaled to [0, 1]."""
    acc = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(points, axis=0).T))])
    total = float(acc[-1])
    return acc / total if total > 0.0 else acc


def loop_ranges(
    chart_anchors: Sequence[Sequence[float]],
    half_widths: Sequence[float],
    stroke_starts: Sequence[int] | None = None,
    corner_anchors: Sequence[int] | None = None,
    *,
    min_span: int = _LOOP_MIN_SPAN,
) -> list[tuple[int, int]]:
    """The anchor index ranges `[start, end)` over which the CHART row closes a loop.

    Read off the RENDERED centerline, per pen-stroke, and mapped back to anchors
    by arc length. Two decisions carry it, and both are the same one the spline
    basis makes: the loops are located on the chart row (occurrence-independent,
    so every occurrence is aligned on one and the same range — a range that moved
    per occurrence would not define a median at all), and they are located on the
    drawn spline rather than on the anchor polyline, because a coarse polyline
    misses a loop the renderer closes and the join grammar reads the spline too.

    Arc length, not proximity, carries the map from sample back to anchor: at a
    crossing the two strands are spatially adjacent, so a nearest-sample search
    hands a strand's anchor to the OTHER strand and the loop collapses to a span
    of one. Arc keeps running where space folds back.

    A segment crossed TWICE bounds three regions, not two — the two loops back to
    each crossing plus the strand between them — and the third is a real Kringel
    (the Sütterlin `p` writes one inside the span of its belly), so the pairs of
    crossings that share a partner are emitted as well.

    Args:
        chart_anchors: The chart row's anchors, `[[x, y], …]`.
        half_widths: The chart row's per-anchor half-widths (the sample plan's).
        stroke_starts: The chart's `trace_meta.stroke_starts`.
        corner_anchors: The chart's `trace_meta.corner_anchors`.
        min_span: Fewest anchors a loop must span.

    Returns:
        The ranges in reading order, deduplicated, each `[start, end)` in anchor
        indices of the whole row.
    """
    from core.template import multi_stroke_centerlines  # noqa: PLC0415 — heavy import, one call site

    pts = np.asarray(chart_anchors, dtype=float).reshape(-1, 2)
    if len(pts) < 2:
        return []
    widths = np.asarray(half_widths, dtype=float).reshape(-1)
    if len(widths) != len(pts):
        widths = np.full(len(pts), float(widths.mean()) if len(widths) else 0.05)
    lines = [
        np.asarray(line, dtype=float)
        for line in multi_stroke_centerlines(pts, widths, stroke_starts, 90.0, corner_anchors=corner_anchors)
    ]
    bounds = _stroke_bounds(len(pts), stroke_starts)
    if len(lines) != len(bounds):
        return []

    found: set[tuple[int, int]] = set()
    for (lo, hi), line in zip(bounds, lines, strict=True):
        if len(line) < 4:
            continue
        crossings = [
            (i, j)
            for i in range(len(line) - 1)
            for j in range(i + 2, len(line) - 1)
            if _segment_crossing(line[i], line[i + 1], line[j], line[j + 1])
        ]
        spans = list(crossings)
        for shared, other in ((0, 1), (1, 0)):
            groups: dict[int, list[int]] = {}
            for pair in crossings:
                groups.setdefault(pair[shared], []).append(pair[other])
            for partners in groups.values():
                partners.sort()
                spans.extend(zip(partners[:-1], partners[1:], strict=True))
        at = np.searchsorted(_arc_fraction(line), _arc_fraction(pts[lo:hi])).clip(0, len(line) - 1)
        for i, j in spans:
            start = int(np.searchsorted(at, i, side="left"))
            end = int(np.searchsorted(at, j, side="right")) - 1
            if end - start >= min_span:
                found.add((lo + start, lo + end + 1))

    # Overlapping spans are MERGED, and that is a correctness requirement rather
    # than tidiness: the same loop is reported twice whenever the drawn curve
    # crosses its neighbour at two nearly identical parameters, and a shift
    # applied once per range would compound on the overlap. One loop region, one
    # alignment. Merging also folds a nested pair into its hull — coarser than
    # measuring them apart, but the alignment may only ever move a whole region.
    merged: list[tuple[int, int]] = []
    for start, end in sorted(found):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def align_loops(
    stack: np.ndarray,
    chart_anchors: Sequence[Sequence[float]],
    ranges: Sequence[tuple[int, int]],
    stroke_starts: Sequence[int] | None = None,
    *,
    window: float = LAUFFORM_LOOP_WINDOW,
    scale: bool = True,
) -> np.ndarray:
    """Register every occurrence's loops on the stack's own median loop (LF13).

    An elementwise median over curves that are not congruent CONTRACTS: point `i`
    of the row is the median of point `i` of every occurrence, and where the
    occurrences' loops disagree about where they are or how big they are, that
    median lies further in than any one of them. On a loop the effect is not
    cosmetic — the counter is what survives the pen, and a running form whose
    counter has closed is read as a different letter.

    The repair is to median the FORM instead of form against placement and size.
    Per loop, each occurrence is brought onto the stack's median loop by a
    SIMILARITY — the translation that matches the median loop centroid, and (with
    `scale`) the isotropic factor that matches the median loop radius, the median
    distance of the loop's anchors from their own centroid. Both are applied with
    weight 1 inside the loop and faded linearly to nothing over `window` of arc
    length (on the CHART stroke) on each side, the shape of `blend_stroke_ends`,
    so a registration can never appear as a step mid-stroke.

    What that does and does not guarantee, precisely — because the difference
    was got wrong once and the data says so. The median shift is zero and the
    median factor is one by construction, so the registration introduces no free
    parameter and no target outside the stack: the row keeps its place, and the
    loop keeps the stack's median radius. It does NOT bound the resulting
    APERTURE. Radius is a scalar proxy; the pointwise median that follows can
    still synthesise a hole wider than any single occurrence when the loops
    disagree anisotropically (a round one against a flat one), and on the
    Sütterlin-1922 root that happens — the `Z` row stands 0.034 xh above its
    occurrence median, the `w` 0.024. It happens to the STORED rows too, so it
    is a property of the elementwise median rather than of this step; a
    two-sided bound would have to be enforced on `D0` itself, which needs the
    aperture ruler and is not what this function does.

    `window` of 0 returns the stack unchanged, bit for bit: the switch is off and
    the caller gets the estimator LF11 adopted.

    Args:
        stack: Occurrence anchors, shape (n_occurrences, n_anchors, 2).
        chart_anchors: The chart row's anchors — the arc-length parameter of the
            fade, never a summand.
        ranges: The chart's loop ranges, from `loop_ranges`.
        stroke_starts: The chart's `trace_meta.stroke_starts`.
        window: Fade window in x-height units; 0 disables the registration.
        scale: Register the loop's size as well as its place (the measured
            carrier); False is the translation-only control arm.

    Returns:
        The registered stack, same shape as `stack`.

    Raises:
        ValueError: If the stack and the chart row disagree about the anchor count.
    """
    pts = np.asarray(stack, dtype=float)
    if pts.ndim != 3 or pts.shape[2] != 2:
        raise ValueError(f"stack must be (n_occurrences, n_anchors, 2), got {pts.shape}")
    chart = np.asarray(chart_anchors, dtype=float).reshape(-1, 2)
    if len(chart) != pts.shape[1]:
        raise ValueError(f"chart has {len(chart)} anchors, occurrences have {pts.shape[1]}")
    if window <= 0.0 or not len(ranges):
        return pts

    out = pts.copy()
    for lo, hi in _stroke_bounds(len(chart), stroke_starts):
        segment = chart[lo:hi]
        if len(segment) < 2:
            continue
        arc = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(segment, axis=0).T))])
        for start, end in ranges:
            if not (lo <= start and end <= hi):
                continue
            inside = arc[start - lo : end - lo]
            before, after = float(inside[0]), float(inside[-1])
            weight = np.clip(
                np.minimum((arc - (before - window)) / window, ((after + window) - arc) / window), 0.0, 1.0
            )
            loop = out[:, start:end, :]
            centroids = loop.mean(axis=1)
            target_centre = np.median(centroids, axis=0)
            if scale:
                # The loop's radius: the MEDIAN distance of its anchors from
                # their own centroid, not the mean — one anchor pulled onto a
                # neighbouring stroke by the fit must not resize the loop.
                radii = np.median(np.linalg.norm(loop - centroids[:, None, :], axis=2), axis=1)
                target_radius = float(np.median(radii))
                factor = np.where(radii > 1e-9, target_radius / np.where(radii > 1e-9, radii, 1.0), 1.0)
            else:
                factor = np.ones(len(loop))
            # Where the similarity sends each anchor, as a displacement — so the
            # fade can carry it out of the loop instead of cutting it off.
            moved = centroids[:, None, :] + factor[:, None, None] * (out[:, lo:hi, :] - centroids[:, None, :])
            delta = (moved - out[:, lo:hi, :]) + (target_centre - centroids)[:, None, :]
            out[:, lo:hi, :] += weight[None, :, None] * delta
    return out


def loop_faithful_median(
    stack: np.ndarray,
    chart_anchors: Sequence[Sequence[float]],
    half_widths: Sequence[float],
    stroke_starts: Sequence[int] | None = None,
    corner_anchors: Sequence[int] | None = None,
    *,
    knot_spacing: float,
    window: float = LAUFFORM_LOOP_WINDOW,
    scale: bool = True,
) -> tuple[np.ndarray, list[str]]:
    """`spline_basis_median` over a stack whose loops were registered first (LF13).

    The adopted estimator with one step in front of it, and nothing else changed:
    at `window` 0 it IS `spline_basis_median`, byte for byte, which is what makes
    the switch a switch rather than a fork.
    """
    ranges = loop_ranges(chart_anchors, half_widths, stroke_starts, corner_anchors) if window > 0.0 else []
    aligned = align_loops(stack, chart_anchors, ranges, stroke_starts, window=window, scale=scale)
    median, notes = spline_basis_median(
        aligned, chart_anchors, stroke_starts, corner_anchors, knot_spacing=knot_spacing
    )
    if window > 0.0:
        how = "place and size" if scale else "place only"
        notes = [f"{len(ranges)} loop(s) registered on {how} over a {window} xh window", *notes]
    return median, notes


def _mean_stats(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Pool the layer-1 statistics of one aggregation group.

    Sub-keys whose inputs are missing across the whole group are omitted rather
    than written as nulls — an absent measurement is not a measured zero.

    Args:
        rows: The group's usable instance dicts (`measurements`, `position`).

    Returns:
        Dict with any of `geo_rmse_px` (mean + max), `xh_px_mean`, `positions`
        (histogram of the occurrence positions) and `n_specimens` (distinct
        specimen ids behind the aggregate).
    """
    rmses: list[float] = []
    xhs: list[float] = []
    positions: Counter[str] = Counter()
    specimens: set[str] = set()
    for row in rows:
        measurements = row.get("measurements") or {}
        rmse = measurements.get("geo_rmse_px")
        if isinstance(rmse, (int, float)):
            rmses.append(float(rmse))
        xh = measurements.get("xh_px")
        if isinstance(xh, (int, float)):
            xhs.append(float(xh))
        specimen_id = measurements.get("specimen_id")
        if specimen_id is not None:
            specimens.add(str(specimen_id))
        # Position is an occurrence column, not a measurement — the aggregate
        # keeps it only as a histogram (§3: an observation dimension).
        position = row.get("position")
        if position is not None:
            positions[str(position)] += 1

    stats: dict[str, Any] = {}
    if rmses:
        stats["geo_rmse_px"] = {
            "mean": round(float(np.mean(rmses)), _STATS_DECIMALS),
            "max": round(float(np.max(rmses)), _STATS_DECIMALS),
        }
    if xhs:
        stats["xh_px_mean"] = round(float(np.mean(xhs)), _STATS_DECIMALS)
    if positions:
        stats["positions"] = dict(sorted(positions.items()))
    if specimens:
        stats["n_specimens"] = len(specimens)
    return stats


def aggregate_instances(
    rows: Iterable[dict[str, Any]], min_n: int = 4
) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[str, int]]:
    """Aggregate one hand's glyph occurrences per `(glyph_key, variant)`.

    Rows whose anchor count differs from their group's modal count cannot be
    stacked (a different anchor sampling is a different measurement) and are
    dropped; a group with too few remaining rows is skipped entirely — a median
    over two occurrences is noise, not a form model.

    Args:
        rows: Instance dicts with `glyph_key`, `glyph`, `variant`, `anchors`
            (list of [x, y] in template coordinates) and optionally `position`
            and `measurements`.
        min_n: Minimum usable occurrences a group needs to be aggregated.

    Returns:
        Tuple of (aggregates by `(glyph_key, variant)`, skip counters). Each
        aggregate carries `glyph`, `cluster_center`, `hull` (`anchor_mad`),
        `mean_stats` and `n_instances`. The counters are `anchor_shape` (rows
        dropped for a deviating anchor count) and `below_min_n` (rows in groups
        that never reached `min_n`).
    """
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["glyph_key"]), int(row.get("variant", 0) or 0))
        grouped.setdefault(key, []).append(row)

    aggregates: dict[tuple[str, int], dict[str, Any]] = {}
    skipped = {"anchor_shape": 0, "below_min_n": 0}
    for key, group in sorted(grouped.items()):
        counts = Counter(len(row["anchors"]) for row in group)
        modal_count, _ = counts.most_common(1)[0]
        usable = [row for row in group if len(row["anchors"]) == modal_count]
        skipped["anchor_shape"] += len(group) - len(usable)
        if len(usable) < min_n:
            skipped["below_min_n"] += len(usable)
            continue
        stack = np.asarray([[[float(x), float(y)] for x, y in row["anchors"]] for row in usable], dtype=float)
        cluster_center, anchor_mad = _median_and_mad(stack)
        glyph, _ = Counter(str(row.get("glyph", "")) for row in usable).most_common(1)[0]
        aggregates[key] = {
            "glyph": glyph,
            "cluster_center": cluster_center,
            "hull": {"anchor_mad": anchor_mad},
            "mean_stats": _mean_stats(usable),
            "n_instances": len(usable),
        }
    return aggregates, skipped


# A join is a short stroke; 24 arc-length samples resolve its curvature well
# below the ink width while keeping every occurrence stackable regardless of how
# many points the dissection happened to emit.
PAIR_CONNECTOR_POINTS = 24


def _resample_polyline(points: np.ndarray, n: int) -> np.ndarray:
    """Resample an open polyline to exactly `n` arc-length-uniform points.

    Connector centerlines come out of the dissection with an arbitrary point
    count, so they can only be stacked into a median after being brought onto a
    common parameterisation. Arc length (not index) is the right parameter: it
    is what makes two differently-sampled traces of the SAME stroke line up.
    Both endpoints are preserved exactly — the last one carries the placement
    offset (see `aggregate_pair_instances`).

    Args:
        points: Array of shape (m, 2) with m >= 2.
        n: Number of output points.

    Returns:
        Array of shape (n, 2). A degenerate polyline (all points equal, i.e.
        zero total length) returns its first point repeated `n` times.
    """
    pts = np.asarray(points, dtype=float)
    steps = np.hypot(*np.diff(pts, axis=0).T)
    cumulative = np.concatenate([[0.0], np.cumsum(steps)])
    total = float(cumulative[-1])
    if total <= 0.0:
        return np.repeat(pts[:1], n, axis=0)
    targets = np.linspace(0.0, total, n)
    return np.column_stack([np.interp(targets, cumulative, pts[:, 0]), np.interp(targets, cumulative, pts[:, 1])])


def _is_number(value: Any) -> bool:
    """True for a real measured number — bool is an int subclass, and a flag is
    never a distance."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_xy(point: Any) -> bool:
    """True for a usable `[x, y]` pair of real numbers (list, tuple or array
    row; a scalar is not, and neither is a missing or non-numeric coordinate —
    a bad point must land in the geometry skip, not abort the rebuild inside
    the float conversion)."""
    if not hasattr(point, "__len__") or len(point) != 2:
        return False
    try:
        x, y = point[0], point[1]
    except (TypeError, KeyError):
        return False
    return _is_number(x) and _is_number(y)


def _pair_mean_stats(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Pool the dissection QC of one pair group.

    Same convention as `_mean_stats`: a sub-key whose input is missing across
    the whole group is omitted rather than written as a null.

    Args:
        rows: The group's usable pair-occurrence dicts (`kind`, `specimen_id`,
            `measurements`).

    Returns:
        Dict with any of `gen_chamfer` / `harvest_chamfer` (mean + max, in
        x-height units — how far the generated resp. harvested connector sat
        from the specimen skeleton), `resid` (mean + max of the two letters'
        fit residuals), `gap_ink_share` (share of occurrences that showed real
        ink between the letters), `kinds` (histogram over the word plates vs.
        the pair drills) and `n_specimens` (distinct specimens).
    """
    gen: list[float] = []
    harvest: list[float] = []
    resids: list[float] = []
    gaps: list[float] = []
    kinds: Counter[str] = Counter()
    specimens: set[tuple[str | None, str]] = set()
    for row in rows:
        measurements = row.get("measurements") or {}
        for key, bucket in (("gen_chamfer", gen), ("harvest_chamfer", harvest)):
            value = measurements.get(key)
            if _is_number(value):
                bucket.append(float(value))
        # The worse of the two letters' dissection fits: this is the quantity
        # the harvest's fit_ok gate thresholds (MAX_FIT_RESID_UNITS = 0.14 in
        # tools/pairlab/harvest.py), so pooling it gives the marginality signal
        # for the n_instances == 1 pairs that min_n = 1 deliberately admits
        # (the H1 twin pools geo_rmse_px the same way).
        a_resid, b_resid = measurements.get("a_resid"), measurements.get("b_resid")
        if _is_number(a_resid) and _is_number(b_resid):
            resids.append(max(float(a_resid), float(b_resid)))
        gap_ink = measurements.get("gap_ink")
        if isinstance(gap_ink, bool):
            gaps.append(float(gap_ink))
        kind = row.get("kind")
        if kind is not None:
            kinds[str(kind)] += 1
        specimen_id = row.get("specimen_id")
        if specimen_id is not None:
            # The word plates and the pair drills are separate id namespaces of
            # the same source, so the specimen identity includes the kind — a
            # missing kind stays None (distinct from a written "None"), any
            # other value is stringified so a malformed row cannot abort the
            # rebuild with an unhashable key.
            specimens.add((str(kind) if kind is not None else None, str(specimen_id)))

    stats: dict[str, Any] = {}
    for key, bucket in (("gen_chamfer", gen), ("harvest_chamfer", harvest), ("resid", resids)):
        if bucket:
            stats[key] = {
                "mean": round(float(np.mean(bucket)), _STATS_DECIMALS),
                "max": round(float(np.max(bucket)), _STATS_DECIMALS),
            }
    if gaps:
        stats["gap_ink_share"] = round(float(np.mean(gaps)), _STATS_DECIMALS)
    if kinds:
        stats["kinds"] = dict(sorted(kinds.items()))
    if specimens:
        stats["n_specimens"] = len(specimens)
    return stats


def aggregate_pair_instances(
    rows: Iterable[dict[str, Any]], min_n: int = 1, connector_points: int = PAIR_CONNECTOR_POINTS
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, int]]:
    """Aggregate one hand's letter-join occurrences per `(left_key, right_key)`.

    The pair twin of `aggregate_instances` (Stufenplan H2): every clean
    dissection of an adjacent joined pair contributes its placement offset and
    its connector centerline — both in the `glyph_pairs` frame, i.e. template
    units relative to the LEFT glyph's exit. The offset is condensed to a
    per-axis median, the connector to a per-point median over arc-length-uniform
    resamplings, each with a MAD hull.

    `kind` is POOLED: an Abb.-19 word join and an Abb.-20 pair drill are the
    same hand writing the same transition, so splitting them would halve an
    already thin sample; the `kinds` histogram keeps the provenance visible.

    `min_n` defaults to 1, unlike the glyph aggregation's 4: pairs are sparse
    (87 occurrences over 45 distinct pairs on the 1922 plates), so a gate of 4
    would discard most of the material. A single clean dissection is still the
    only MEASURED truth about that transition — the aggregate reports
    `n_instances` so every consumer can weigh it.

    Args:
        rows: Pair-occurrence dicts with `left_key`, `right_key`, `kind`,
            `specimen_id`, `geometry` (`{"offset": [dx, dy], "connector":
            [[x, y], ...]}`) and `measurements` (the dissection QC).
        min_n: Minimum usable occurrences a pair needs to be aggregated.
        connector_points: Samples per resampled connector.

    Returns:
        Tuple of (aggregates by `(left_key, right_key)`, skip counters). Each
        aggregate carries `offset_center`, `connector_center`, `hull`
        (`offset_mad` + `connector_mad`), `mean_stats` and `n_instances`. The
        counters are `fit_bad` (the harvest's own QC rejected the dissection),
        `geometry` (offset or connector unusable) and `below_min_n`.
    """
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    skipped = {"fit_bad": 0, "geometry": 0, "below_min_n": 0}
    for row in rows:
        # The pair batch stores every dissection, clean or not (the glyph
        # harvest filtered at write time) — so the QC gate lives here.
        if not (row.get("measurements") or {}).get("fit_ok"):
            skipped["fit_bad"] += 1
            continue
        geometry = row.get("geometry") or {}
        offset = geometry.get("offset")
        connector = geometry.get("connector")
        # A ragged connector (an entry that is not an [x, y] pair) would only
        # blow up deep inside `np.asarray` — check it here so the row is a
        # counted geometry skip instead of an exception that kills the rebuild.
        if (
            not _is_xy(offset)
            or not hasattr(connector, "__len__")
            or len(connector) < 2
            or not all(_is_xy(point) for point in connector)
        ):
            skipped["geometry"] += 1
            continue
        grouped.setdefault((str(row["left_key"]), str(row["right_key"])), []).append(row)

    aggregates: dict[tuple[str, str], dict[str, Any]] = {}
    for key, group in sorted(grouped.items()):
        if len(group) < min_n:
            skipped["below_min_n"] += len(group)
            continue
        offsets = np.asarray([[[float(v) for v in row["geometry"]["offset"]]] for row in group], dtype=float)
        offset_center, offset_mad = _median_and_mad(offsets)
        connectors = np.asarray(
            [
                _resample_polyline(np.asarray(row["geometry"]["connector"], dtype=float), connector_points)
                for row in group
            ],
            dtype=float,
        )
        # The harvest writes connector[-1] == offset (both are baseline-locked
        # and the connector ends at the right glyph's entry); resampling keeps
        # the endpoints, so connector_center[-1] == offset_center falls out of
        # the same medians. Stated, not enforced — a divergence would mean the
        # occurrences disagree about the frame, which is worth seeing.
        connector_center, connector_mad = _median_and_mad(connectors)
        aggregates[key] = {
            "offset_center": offset_center[0],
            "connector_center": connector_center,
            "hull": {"offset_mad": offset_mad[0], "connector_mad": connector_mad},
            "mean_stats": _pair_mean_stats(group),
            "n_instances": len(group),
        }
    return aggregates, skipped


def laufform_deviation(
    cluster_center: Sequence[Sequence[float]], laufform_anchors: Sequence[Sequence[float]]
) -> float | None:
    """Mean anchor distance between an aggregate median and a stored Laufform.

    The H1 Prüfstein (docs/proposals/handmodell-stufenplan.md §4): the median
    recomputed from the persisted occurrences must reproduce the Laufform that
    the harvest wrote as template variant 100. Mirrors the harvest's own
    `median-vs-chart` diagnostic.

    Args:
        cluster_center: The aggregate's per-anchor median, [[x, y], ...].
        laufform_anchors: The stored variant-100 anchors, [[x, y], ...].

    Returns:
        Mean Euclidean anchor distance in template x-height units, or None when
        the two anchor lists have different lengths (not comparable).
    """
    if len(cluster_center) != len(laufform_anchors) or not cluster_center:
        return None
    a = np.asarray(cluster_center, dtype=float)
    b = np.asarray(laufform_anchors, dtype=float)
    return round(float(np.hypot(*(a - b).T).mean()), _GEOMETRY_DECIMALS)
