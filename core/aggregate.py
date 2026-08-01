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
    """True for a usable `[x, y]` pair (list, tuple or array row; a scalar is
    not, and neither is a point with a missing coordinate)."""
    return hasattr(point, "__len__") and len(point) == 2


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
    specimens: set[tuple[Any, str]] = set()
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
            # the same source, so the specimen identity includes the kind — as
            # the RAW value, so a missing kind stays distinct from a "None" one.
            specimens.add((kind, str(specimen_id)))

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
