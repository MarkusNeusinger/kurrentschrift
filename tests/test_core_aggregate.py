"""Unit tests for the per-hand aggregation math (core/aggregate.py, Stufenplan H1).

Pure functions, no DB: the median/MAD arithmetic is checked against values
computed by hand, so a numpy behaviour change cannot silently redefine the
aggregate.
"""

from __future__ import annotations

import pytest

from core.aggregate import aggregate_instances, laufform_deviation


def _row(anchors: list[list[float]], **overrides) -> dict:
    row = {
        "glyph_key": "n",
        "glyph": "n",
        "variant": 0,
        "anchors": anchors,
        "position": "medial",
        "measurements": {"specimen_id": "wenn", "geo_rmse_px": 1.0, "xh_px": 30.0},
    }
    row.update(overrides)
    return row


def test_aggregate_computes_elementwise_median_and_mad():
    """Four occurrences of one anchor pair: the median is the mean of the two
    middle values per axis, the MAD the median of the absolute deviations."""
    rows = [
        _row([[0.0, 0.0], [1.0, 1.0]]),
        _row([[0.0, 0.0], [3.0, 1.0]]),
        _row([[0.0, 0.0], [5.0, 4.0]]),
        _row([[0.0, 0.0], [7.0, 4.0]]),
    ]
    aggregates, skipped = aggregate_instances(rows, min_n=4)
    assert set(aggregates) == {("n", 0)}
    agg = aggregates[("n", 0)]
    # x: median of 1,3,5,7 = 4 ; y: median of 1,1,4,4 = 2.5
    assert agg["cluster_center"] == [[0.0, 0.0], [4.0, 2.5]]
    # |x - 4| = 3,1,1,3 → median 2 ; |y - 2.5| = 1.5 four times → 1.5
    assert agg["hull"] == {"anchor_mad": [[0.0, 0.0], [2.0, 1.5]]}
    assert agg["n_instances"] == 4
    assert agg["glyph"] == "n"
    assert skipped == {"anchor_shape": 0, "below_min_n": 0}


def test_aggregate_skips_rows_with_a_deviating_anchor_count():
    """A different anchor sampling is a different measurement — it cannot be
    stacked into the median and is reported instead."""
    rows = [_row([[0.0, 0.0], [1.0, 1.0]]) for _ in range(4)]
    rows.append(_row([[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]]))
    aggregates, skipped = aggregate_instances(rows, min_n=4)
    assert aggregates[("n", 0)]["n_instances"] == 4
    assert skipped["anchor_shape"] == 1


def test_aggregate_min_n_gate_reports_the_dropped_rows():
    rows = [_row([[0.0, 0.0], [1.0, 1.0]]) for _ in range(3)]
    aggregates, skipped = aggregate_instances(rows, min_n=4)
    assert aggregates == {}
    assert skipped == {"anchor_shape": 0, "below_min_n": 3}
    # The same rows aggregate once the gate allows them.
    aggregates, _ = aggregate_instances(rows, min_n=3)
    assert aggregates[("n", 0)]["n_instances"] == 3


def test_aggregate_groups_per_glyph_key_and_variant():
    rows = [
        *[_row([[0.0, 0.0], [1.0, 1.0]]) for _ in range(4)],
        *[_row([[0.0, 0.0], [2.0, 1.0]], variant=1) for _ in range(4)],
        *[_row([[0.0, 0.0], [3.0, 1.0]], glyph_key="e", glyph="e") for _ in range(4)],
    ]
    aggregates, _ = aggregate_instances(rows, min_n=4)
    assert set(aggregates) == {("n", 0), ("n", 1), ("e", 0)}
    assert aggregates[("e", 0)]["glyph"] == "e"


def test_mean_stats_pools_measurements_positions_and_specimens():
    rows = [
        _row([[0.0, 0.0], [1.0, 1.0]], measurements={"specimen_id": "wenn", "geo_rmse_px": 1.0, "xh_px": 30.0}),
        _row([[0.0, 0.0], [1.0, 1.0]], measurements={"specimen_id": "wenn", "geo_rmse_px": 2.0, "xh_px": 32.0}),
        _row([[0.0, 0.0], [1.0, 1.0]], position="final", measurements={"specimen_id": "denen", "geo_rmse_px": 3.0}),
        _row([[0.0, 0.0], [1.0, 1.0]], position="final", measurements={}),
    ]
    aggregates, _ = aggregate_instances(rows, min_n=4)
    stats = aggregates[("n", 0)]["mean_stats"]
    assert stats["geo_rmse_px"] == {"mean": 2.0, "max": 3.0}
    assert stats["xh_px_mean"] == 31.0
    assert stats["positions"] == {"final": 2, "medial": 2}
    assert stats["n_specimens"] == 2


def test_mean_stats_omits_missing_inputs_instead_of_writing_nulls():
    rows = [_row([[0.0, 0.0], [1.0, 1.0]], position=None, measurements={}) for _ in range(4)]
    aggregates, _ = aggregate_instances(rows, min_n=4)
    assert aggregates[("n", 0)]["mean_stats"] == {}


def test_aggregate_empty_input():
    assert aggregate_instances([]) == ({}, {"anchor_shape": 0, "below_min_n": 0})


@pytest.mark.parametrize(
    ("median", "laufform", "expected"),
    [
        # (3,4) and (0,0) offsets → distances 5 and 0 → mean 2.5
        ([[3.0, 4.0], [1.0, 1.0]], [[0.0, 0.0], [1.0, 1.0]], 2.5),
        ([[1.0, 1.0]], [[1.0, 1.0]], 0.0),
    ],
)
def test_laufform_deviation_exact_values(median, laufform, expected):
    assert laufform_deviation(median, laufform) == expected


def test_laufform_deviation_none_on_shape_mismatch_or_empty():
    assert laufform_deviation([[0.0, 0.0]], [[0.0, 0.0], [1.0, 1.0]]) is None
    assert laufform_deviation([], []) is None
