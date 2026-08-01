"""Per-hand aggregation of stored glyph occurrences (Stufenplan H1, §12 layer 2).

Turns the `instances` rows of ONE hand into one aggregate per
`(glyph_key, variant)`: the per-anchor median (the running form — occurrence
anchors are stored CENTERED onto the chart template, "shapes, not placements",
so the elementwise median over them reproduces the harvested Laufform), the
per-anchor spread as a median absolute deviation hull, and the pooled layer-1
statistics.

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
