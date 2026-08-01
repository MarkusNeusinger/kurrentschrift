"""Unit tests for the pair-aggregation math (core/aggregate.py, Stufenplan H2).

Pure functions, no DB: the resampling and the median/MAD arithmetic are checked
against values computed by hand, so a numpy behaviour change cannot silently
redefine what „the natural transition" means.
"""

from __future__ import annotations

import numpy as np
import pytest

from core.aggregate import _resample_polyline, aggregate_pair_instances


def _row(offset: list[float], connector: list[list[float]] | None = None, **overrides) -> dict:
    """One clean join occurrence; the connector defaults to the straight line
    from the left exit to the placement offset (the harvest invariant
    connector[-1] == offset, kept so the resampling stays hand-checkable)."""
    row = {
        "left_key": "n",
        "right_key": "e",
        "kind": "word",
        "specimen_id": "wenn",
        "geometry": {"offset": offset, "connector": connector or [[0.0, 0.0], list(offset)]},
        "measurements": {"fit_ok": True},
    }
    row.update(overrides)
    return row


# ------------------------------------------------------------------ resampling


def test_resample_spaces_points_by_arc_length_not_by_index():
    """An unevenly sampled straight line comes back evenly spaced — that is
    what makes two differently-sampled traces of one stroke stackable."""
    out = _resample_polyline(np.asarray([[0.0, 0.0], [1.0, 0.0], [3.0, 0.0]]), 4)
    assert out.tolist() == [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [3.0, 0.0]]


def test_resample_walks_arc_length_and_not_the_x_axis():
    """The pin for the parameterisation itself, on a connector that turns back
    down — the horizontal cases above pass under an x-parameterised resampler
    too, this one does not.

    Segment lengths are hypot(0.1, 0.4) = 0.412310563 and hypot(0.3, 0.4) = 0.5,
    total 0.912310563. The arc-length midpoint (s = 0.456155281) therefore lies
    0.043844718 into the second segment, i.e. at fraction 0.087689437 of it:
    (0.1 + 0.3·f, 0.4 − 0.4·f) = (0.126306831, 0.364924225). An
    x-parameterised implementation would answer (0.2, 0.266666…) here.
    """
    out = _resample_polyline(np.asarray([[0.0, 0.0], [0.1, 0.4], [0.4, 0.0]]), 3)
    assert np.allclose(out, [[0.0, 0.0], [0.126306831, 0.364924225], [0.4, 0.0]])


def test_resample_keeps_both_endpoints_and_the_requested_count():
    points = np.asarray([[0.0, 0.0], [0.2, 0.5], [0.4, 0.1]])
    for n in (2, 3, 24):
        out = _resample_polyline(points, n)
        assert out.shape == (n, 2)
        assert out[0].tolist() == [0.0, 0.0]
        assert out[-1].tolist() == [0.4, 0.1]


def test_resample_of_a_degenerate_polyline_repeats_the_first_point():
    """Zero total length: there is no arc to walk along, so the only honest
    answer is the point itself (and never a division by zero)."""
    out = _resample_polyline(np.asarray([[1.0, 2.0], [1.0, 2.0], [1.0, 2.0]]), 3)
    assert out.tolist() == [[1.0, 2.0]] * 3


# ------------------------------------------------------------------ aggregation


def test_aggregate_computes_offset_and_connector_medians_with_mad_hull():
    """Three occurrences of one transition, resampled to three points each:

    offsets 0.4 / 0.6 / 0.5 → median 0.5, deviations 0.1 / 0.1 / 0.0 → MAD 0.1.
    The straight connectors resample to their midpoints 0.2 / 0.3 / 0.25 →
    median 0.25, MAD 0.05.
    """
    rows = [_row([0.4, 0.0]), _row([0.6, 0.0]), _row([0.5, 0.0])]
    aggregates, skipped = aggregate_pair_instances(rows, connector_points=3)
    assert set(aggregates) == {("n", "e")}
    agg = aggregates[("n", "e")]
    assert agg["offset_center"] == [0.5, 0.0]
    assert agg["connector_center"] == [[0.0, 0.0], [0.25, 0.0], [0.5, 0.0]]
    # The harvest writes connector[-1] == offset and resampling keeps the
    # endpoints, so the two medians agree without being forced to.
    assert agg["connector_center"][-1] == agg["offset_center"]
    assert agg["hull"]["offset_mad"] == [0.1, 0.0]
    assert agg["hull"]["connector_mad"] == [[0.0, 0.0], [0.05, 0.0], [0.1, 0.0]]
    assert agg["n_instances"] == 3
    assert skipped == {"fit_bad": 0, "geometry": 0, "below_min_n": 0}


def test_aggregate_rejects_occurrences_the_harvest_qc_failed():
    """The pair batch stores every dissection, clean or not — the QC gate that
    the glyph harvest applied at write time lives in the aggregation."""
    rows = [
        _row([0.4, 0.0]),
        _row([0.6, 0.0]),
        _row([9.0, 9.0], measurements={"fit_ok": False}),
        _row([9.0, 9.0], measurements={}),
    ]
    aggregates, skipped = aggregate_pair_instances(rows)
    assert aggregates[("n", "e")]["n_instances"] == 2
    assert skipped["fit_bad"] == 2


def test_aggregate_rejects_unusable_geometry():
    rows = [
        _row([0.4, 0.0]),
        _row([0.4, 0.0, 0.0]),  # not a 2-vector
        _row([0.4, 0.0], connector=[[0.0, 0.0]]),  # not a polyline
        {**_row([0.4, 0.0]), "geometry": {"connector": [[0.0, 0.0], [0.4, 0.0]]}},  # no offset
        {**_row([0.4, 0.0]), "geometry": {"offset": [0.4, 0.0]}},  # no connector
    ]
    aggregates, skipped = aggregate_pair_instances(rows)
    assert aggregates[("n", "e")]["n_instances"] == 1
    assert skipped["geometry"] == 4


def test_aggregate_counts_a_ragged_connector_as_a_geometry_skip():
    """A connector point that is not an [x, y] pair would only fail deep inside
    `np.asarray` — one malformed harvest row must never kill the whole
    rebuild, it is a counted skip like any other unusable geometry."""
    rows = [
        _row([0.4, 0.0]),
        _row([0.4, 0.0], connector=[[0.0, 0.0], [1.0]]),  # short point
        _row([0.4, 0.0], connector=[[0.0, 0.0], 0.4]),  # scalar entry
        {**_row([0.4, 0.0]), "geometry": {"offset": 0.4, "connector": [[0.0, 0.0], [0.4, 0.0]]}},  # scalar offset
        _row([0.4, 0.0], connector=[[0.0, 0.0], ["a", "b"]]),  # non-numeric point
        _row(["a", 0.0]),  # non-numeric offset coordinate
    ]
    aggregates, skipped = aggregate_pair_instances(rows)
    assert aggregates[("n", "e")]["n_instances"] == 1
    assert skipped["geometry"] == 5


def test_aggregate_min_n_gate_reports_the_dropped_rows():
    rows = [_row([0.4, 0.0]), _row([0.6, 0.0]), _row([0.5, 0.0], left_key="e", right_key="n")]
    aggregates, skipped = aggregate_pair_instances(rows, min_n=2)
    assert set(aggregates) == {("n", "e")}
    assert skipped == {"fit_bad": 0, "geometry": 0, "below_min_n": 1}
    # The default gate of 1 keeps the singleton: pairs are sparse, and a single
    # clean dissection is still the only measured truth about that transition.
    aggregates, skipped = aggregate_pair_instances(rows)
    assert set(aggregates) == {("n", "e"), ("e", "n")}
    assert aggregates[("e", "n")]["n_instances"] == 1


def test_aggregate_pools_kinds_and_counts_distinct_specimens():
    """A word-plate join and a pair-drill join are the same hand writing the
    same transition — pooled into one group, with the provenance kept as a
    histogram. The specimen identity spans (kind, specimen_id): the two plate
    sets are separate id namespaces."""
    rows = [_row([0.4, 0.0]), _row([0.6, 0.0], specimen_id="denen"), _row([0.5, 0.0], kind="pair", specimen_id="wenn")]
    aggregates, _ = aggregate_pair_instances(rows)
    stats = aggregates[("n", "e")]["mean_stats"]
    assert aggregates[("n", "e")]["n_instances"] == 3
    assert stats["kinds"] == {"pair": 1, "word": 2}
    assert stats["n_specimens"] == 3


def test_specimen_identity_keeps_a_missing_kind_distinct_from_a_written_one():
    """A row without a `kind` still has a specimen: it must not be folded into
    a literal "None" namespace, and it contributes no `kinds` bucket."""
    rows = [_row([0.4, 0.0], kind=None), _row([0.6, 0.0])]
    stats = aggregate_pair_instances(rows)[0][("n", "e")]["mean_stats"]
    assert stats["n_specimens"] == 2  # (None, "wenn") and ("word", "wenn")
    assert stats["kinds"] == {"word": 1}


def test_specimen_identity_survives_an_unhashable_kind():
    """A malformed row with a list/dict `kind` must not abort the rebuild on
    the set insert — any written kind is stringified for the identity."""
    rows = [_row([0.4, 0.0], kind=["word"]), _row([0.6, 0.0])]
    stats = aggregate_pair_instances(rows)[0][("n", "e")]["mean_stats"]
    assert stats["n_specimens"] == 2  # ("['word']", "wenn") and ("word", "wenn")
    assert stats["kinds"] == {"['word']": 1, "word": 1}


def test_mean_stats_pools_the_dissection_qc():
    rows = [
        _row([0.4, 0.0], measurements={"fit_ok": True, "gen_chamfer": 0.2, "harvest_chamfer": 0.1, "gap_ink": True}),
        _row([0.6, 0.0], measurements={"fit_ok": True, "gen_chamfer": 0.3, "harvest_chamfer": 0.2, "gap_ink": True}),
        _row([0.5, 0.0], measurements={"fit_ok": True, "gen_chamfer": 0.4, "gap_ink": False}),
    ]
    stats = aggregate_pair_instances(rows)[0][("n", "e")]["mean_stats"]
    assert stats["gen_chamfer"] == {"mean": 0.3, "max": 0.4}
    assert stats["harvest_chamfer"] == {"mean": 0.15, "max": 0.2}
    assert stats["gap_ink_share"] == pytest.approx(0.667)


def test_mean_stats_pools_the_worse_letter_fit_residual():
    """`resid` is the quantity the harvest's own fit_ok gate thresholds — the
    marginality signal for the singleton pairs min_n = 1 admits. Per row the
    WORSE of the two letters (max), pooled to mean 0.11 / max 0.12; a row that
    carries only one of the two keys measures no join and is left out."""
    rows = [
        _row([0.4, 0.0], measurements={"fit_ok": True, "a_resid": 0.1, "b_resid": 0.05}),
        _row([0.5, 0.0], measurements={"fit_ok": True, "a_resid": 0.04, "b_resid": 0.12}),
        _row([0.6, 0.0], measurements={"fit_ok": True, "a_resid": 0.08}),
        _row([0.6, 0.0], measurements={"fit_ok": True, "a_resid": True, "b_resid": True}),
    ]
    stats = aggregate_pair_instances(rows)[0][("n", "e")]["mean_stats"]
    assert stats["resid"] == {"mean": 0.11, "max": 0.12}

    # A group whose rows never measured it omits the key rather than claiming 0.
    assert "resid" not in aggregate_pair_instances([_row([0.4, 0.0])])[0][("n", "e")]["mean_stats"]


def test_mean_stats_omits_missing_inputs_instead_of_writing_nulls():
    rows = [{**_row([0.4, 0.0]), "kind": None, "specimen_id": None} for _ in range(2)]
    assert aggregate_pair_instances(rows)[0][("n", "e")]["mean_stats"] == {}


def test_aggregate_empty_input():
    assert aggregate_pair_instances([]) == ({}, {"fit_bad": 0, "geometry": 0, "below_min_n": 0})
