"""Tests for the Stage-A chain evaluation harness (`tools/pairlab/chainbench.py`).

Everything here runs WITHOUT fixtures, DB or network: the harness' metric
helpers are pure geometry/statistics over hand-built inputs, and the chain
plumbing is exercised against a hand-built `ChainFit` so the harness is pinned
to `tools/pairlab/chain.py`'s frozen contract rather than to its (separately
implemented) bodies.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from core.fit import CONVERGED_COVERAGE_RMSE_UNITS, CONVERGED_GEO_RMSE_UNITS
from tools.pairlab import analyze
from tools.pairlab.chain import ChainFit, ChainSegment
from tools.pairlab.chainbench import (
    SHAPE_SAMPLES,
    _fill_chain_placement,
    _fill_chain_segments,
    _mad_reference,
    anchor_deltas,
    arc_share,
    attributed_cov_rmse,
    body_stroke_bounds,
    clip_polyline_x,
    common_x_window,
    dconn,
    dconn_matched_arc,
    empty_join_gain,
    gate_failures,
    load_anchor_mad,
    pair_class,
    paired_counts,
    paired_deltas,
    parse_pair_filter,
    per_letter_rates,
    polyline_shape_delta,
    sign_test,
    summarize,
    union_window_points,
)
from tools.wordlab.cases import WordCase
from tools.wordlab.derive import WordDeriveResult


# ----------------------------------------------------- M3: the dconn helper


def _arc(n: int = 30) -> np.ndarray:
    t = np.linspace(0.0, 1.0, n)
    return np.column_stack([t, 0.4 * np.sin(np.pi * t)])


def test_dconn_is_translation_free() -> None:
    """Plan §5.12 — the M3 helper compares SHAPE: a translated copy is zero."""
    a = _arc()
    b = a + np.array([2.5, -1.75])
    assert dconn(a, b) == pytest.approx(0.0, abs=1e-9)


def test_dconn_is_resampling_invariant() -> None:
    """Same curve, different point counts — arc-length resampling makes the two
    comparable (the reason pairmeas resamples before differencing)."""
    assert dconn(_arc(30), _arc(97)) == pytest.approx(0.0, abs=1e-3)


def test_dconn_sees_a_shape_difference() -> None:
    a = _arc()
    b = np.column_stack([a[:, 0], -a[:, 1]])  # mirrored sweep, same endpoints
    assert dconn(a, b) > 0.1


def test_dconn_degenerate_inputs_are_none() -> None:
    assert dconn(np.zeros((1, 2)), _arc()) is None
    assert dconn(_arc(), np.zeros((0, 2))) is None


# ------------------------------------------ M3 arc matching (Stage-B precondition 2)


def test_clip_polyline_x_splits_the_crossing_segments() -> None:
    """A straight run clipped to a band keeps exactly the band's stretch, with
    the two crossings interpolated rather than snapped to a stored point."""
    poly = np.array([[0.0, 1.0], [10.0, 1.0]])
    clipped = clip_polyline_x(poly, 3.0, 7.0)
    assert np.allclose(clipped, [[3.0, 1.0], [7.0, 1.0]])
    # …and on a rising line the y is interpolated with it
    rising = np.array([[0.0, 0.0], [10.0, 10.0]])
    assert np.allclose(clip_polyline_x(rising, 2.0, 4.0), [[2.0, 2.0], [4.0, 4.0]])


def test_clip_polyline_x_handles_reversal_and_empty_bands() -> None:
    """A connector that doubles back (a capital retrace) keeps every piece it has
    inside the band, in traversal order."""
    v = np.array([[0.0, 0.0], [6.0, 0.0], [0.0, 3.0]])  # right, then back left
    clipped = clip_polyline_x(v, 2.0, 4.0)
    assert len(clipped) == 4
    assert clipped[0].tolist() == pytest.approx([2.0, 0.0])
    assert clipped[-1].tolist() == pytest.approx([2.0, 2.0])
    assert len(clip_polyline_x(v, 9.0, 12.0)) == 0  # band outside the curve
    assert len(clip_polyline_x(v, 4.0, 4.0)) == 0  # degenerate band
    assert len(clip_polyline_x(np.zeros((1, 2)), 0.0, 1.0)) == 0


def test_dconn_matched_arc_removes_the_definitional_stub_distance() -> None:
    """Two curves of the SAME shape over their shared x-span, one of which
    additionally owns a stub zone to the left: whole-curve `dconn` charges the
    difference, the arc-matched one does not."""
    shared = np.column_stack([np.linspace(1.0, 2.0, 40), np.zeros(40)])
    stub = np.column_stack([np.linspace(0.0, 1.0, 20), np.linspace(-0.6, 0.0, 20)])
    long_curve = np.vstack([stub, shared])
    assert dconn(long_curve, shared) > 0.05  # the Stage-A comparison
    value, span = dconn_matched_arc(long_curve, shared, 0.0, 9.0)
    assert span == pytest.approx(1.0)  # intersection of the two x-spans
    assert value == pytest.approx(0.0, abs=1e-6)


def test_dconn_matched_arc_reports_none_without_a_shared_arc() -> None:
    a = np.column_stack([np.linspace(0.0, 1.0, 10), np.zeros(10)])
    b = np.column_stack([np.linspace(2.0, 3.0, 10), np.zeros(10)])
    assert dconn_matched_arc(a, b, -9.0, 9.0) == (None, 0.0)
    # a touching letter pair: the "gap" runs backwards, so there is no arc at all
    assert dconn_matched_arc(a, a, 0.8, 0.2) == (None, 0.0)
    assert dconn_matched_arc(np.zeros((1, 2)), a, 0.0, 1.0) == (None, 0.0)


def test_common_x_window_is_the_intersection_of_every_curve() -> None:
    """Generated, chained and ink-read connector are judged on ONE arc, so the
    M3 table stays a comparison instead of three separate measurements."""
    a = np.column_stack([np.linspace(0.0, 3.0, 10), np.zeros(10)])
    b = np.column_stack([np.linspace(0.5, 2.0, 10), np.zeros(10)])
    assert common_x_window([a, b], -1.0, 5.0) == pytest.approx((0.5, 2.0))
    assert common_x_window([a, b], 1.0, 1.5) == pytest.approx((1.0, 1.5))
    assert common_x_window([a, b], 2.5, 5.0) is None  # gap left of b's end
    assert common_x_window([a, np.zeros((1, 2))], 0.0, 1.0) is None


# --------------------------------------------- kill criterion: seam calibration


def test_tail_share_matches_a_known_geometry() -> None:
    """Plan §5.13 — `chain_tail_share`/`chain_head_share` on a hand-built
    connector: a 10 px horizontal run at xh=10 is 1.0 xh of arc, and a split at
    x=3 leaves exactly 0.3 xh left of the left letter's ink edge."""
    poly = np.array([[0.0, 0.0], [10.0, 0.0]])
    assert arc_share(poly, 3.0, keep_left=True, xh=10.0) == pytest.approx(0.3)
    assert arc_share(poly, 7.0, keep_left=False, xh=10.0) == pytest.approx(0.3)
    # Whole polyline on one side.
    assert arc_share(poly, 99.0, keep_left=True, xh=10.0) == pytest.approx(1.0)
    assert arc_share(poly, 99.0, keep_left=False, xh=10.0) == pytest.approx(0.0)


def test_tail_share_splits_a_bent_connector_by_arc_not_by_points() -> None:
    poly = np.array([[0.0, 0.0], [4.0, 0.0], [4.0, 3.0]])  # 4 px across, then 3 px up
    assert arc_share(poly, 2.0, keep_left=True, xh=10.0) == pytest.approx(0.2)
    assert arc_share(poly, 2.0, keep_left=False, xh=10.0) == pytest.approx(0.5)


def test_tail_share_of_a_degenerate_polyline_is_zero() -> None:
    assert arc_share(np.zeros((1, 2)), 1.0, keep_left=True, xh=10.0) == 0.0
    assert arc_share(np.array([[0.0, 0.0], [1.0, 0.0]]), 1.0, keep_left=True, xh=0.0) == 0.0


# ----------------------------------------------------- M1/M2 aggregation logic


def _row(pair: str, base: bool | None, chain: bool | None, *, empty: bool, yielded: bool, **extra) -> dict:
    return {
        "pair": pair,
        "base_converged": base,
        "chain_converged": chain,
        "base_empty_join": empty,
        "chain_connector_yielded": yielded,
        **extra,
    }


FAKE_ROWS = [
    _row("d→e", True, True, empty=False, yielded=True),
    _row("d→e", False, True, empty=True, yielded=True),
    _row("o→n", True, False, empty=True, yielded=False),
    _row("o→n", False, False, empty=True, yielded=True),
    _row("o→n", None, True, empty=False, yielded=True),  # unknown baseline gate → not paired
]


def test_paired_counts_separates_a_swap_from_a_wash() -> None:
    """M1's point: two identical pooled rates can hide a full swap, so the
    paired cells are the answer — one chain-only win, one baseline-only loss."""
    table = paired_counts(FAKE_ROWS, "base_converged", "chain_converged")
    assert table["n"] == 4  # the row with an unknown baseline gate is excluded
    assert (table["both"], table["chain_only"], table["base_only"], table["neither"]) == (1, 1, 1, 1)
    assert table["base_rate"] == 0.5 and table["chain_rate"] == 0.5


def test_paired_counts_on_an_empty_input() -> None:
    table = paired_counts([], "base_converged", "chain_converged")
    assert table["n"] == 0 and table["base_rate"] is None and table["chain_rate"] is None


def test_empty_join_gain_counts_only_the_empty_denominator() -> None:
    gain = empty_join_gain(FAKE_ROWS)
    assert gain["n_empty"] == 3  # the two non-empty joins never enter M2
    assert gain["n_gained"] == 2
    assert gain["per_pair"] == {"d→e": {"empty": 1, "gained": 1}, "o→n": {"empty": 2, "gained": 1}}


def test_per_letter_rates_count_a_letter_on_both_sides_of_a_join() -> None:
    rows = [
        {
            "chain_l_key": "d",
            "chain_r_key": "e",
            "base_a_converged": True,
            "chain_l_converged": True,
            "base_b_converged": False,
            "chain_r_converged": True,
        },
        {
            "chain_l_key": "e",
            "chain_r_key": "n",
            "base_a_converged": True,
            "chain_l_converged": False,
            "chain_l_converged_local": True,  # the union gate failed, its own window did not
            "base_b_converged": None,  # unknown → the n side is not counted
            "chain_r_converged": True,
        },
    ]
    rates = per_letter_rates(rows)
    # The local column is counted in the same pass over the same denominator; a
    # row without one falls back to its union gate rather than dropping out.
    assert rates["e"] == {"n": 2, "base": 1, "chain": 1, "chain_local": 2}
    assert rates["d"] == {"n": 1, "base": 1, "chain": 1, "chain_local": 1}
    assert "n" not in rates


def test_gate_failures_split_coverage_from_geometry() -> None:
    """The Stage-A diagnosis as a column read: which half of `core.fit`'s gate
    actually fails, per coverage window."""
    xh = 100.0  # thresholds scale with xh, so this makes them round numbers
    geo_bad = CONVERGED_GEO_RMSE_UNITS * xh + 1.0
    geo_ok = CONVERGED_GEO_RMSE_UNITS * xh - 1.0
    cov_bad = CONVERGED_COVERAGE_RMSE_UNITS * xh + 1.0
    cov_ok = CONVERGED_COVERAGE_RMSE_UNITS * xh - 1.0
    rows = [
        {
            "xh_px": xh,
            # left: fails the union gate on COVERAGE only, and its own window clears it
            "chain_l_converged": False,
            "chain_l_converged_local": True,
            "chain_l_geo_rmse_px": geo_ok,
            "chain_l_cov_rmse_px": cov_bad,
            "chain_l_cov_rmse_local_px": cov_ok,
            # right: genuinely off the ink — fails both, under either window
            "chain_r_converged": False,
            "chain_r_converged_local": False,
            "chain_r_geo_rmse_px": geo_bad,
            "chain_r_cov_rmse_px": cov_bad,
            "chain_r_cov_rmse_local_px": cov_bad,
        }
    ]
    union = gate_failures(rows, local=False)
    assert (union["n"], union["cov_only"], union["geo_only"], union["both"]) == (2, 1, 0, 1)
    local = gate_failures(rows, local=True)
    assert (local["n"], local["cov_only"], local["geo_only"], local["both"]) == (1, 0, 0, 1)
    assert gate_failures([{"chain_l_converged": False}], local=False)["n"] == 0  # no xh → not counted


# ------------------------------- M1's third column: baseline on the union window


def test_union_window_points_repeat_the_chains_own_cut() -> None:
    """The baseline can only be re-graded on the chain's window if it is the
    SAME window — margin, union and subsampling budget included."""
    skel = np.zeros((10, 60), dtype=bool)
    skel[5, :] = True  # one horizontal skeleton row across the whole crop
    a = [np.array([[10.0, 5.0], [14.0, 5.0]])]
    b = [np.array([[30.0, 5.0], [34.0, 5.0]])]
    pts = union_window_points(skel, a, b, xh=10.0, margin=0.5)
    xs = pts[:, 0]
    # union of both letter windows (10-5 … 34+5), hole between them CLOSED
    assert xs.min() == pytest.approx(5.0) and xs.max() == pytest.approx(39.0)
    assert len(xs) == 35
    # the budget subsamples instead of truncating
    assert len(union_window_points(skel, a, b, xh=10.0, margin=0.5, budget=8)) == 8
    assert len(union_window_points(None, a, b, xh=10.0)) == 0


def test_attributed_cov_rmse_uses_the_nearest_sample_rule() -> None:
    """Coverage goes to the polyline holding the nearest sample — the chain's own
    attribution, applied to two independently fitted centerlines."""
    left = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    right = np.array([[10.0, 0.0], [11.0, 0.0], [12.0, 0.0]])
    cov = np.array([[1.0, 3.0], [11.0, 4.0], [11.0, 0.0]])
    (rmse_l, n_l), (rmse_r, n_r) = attributed_cov_rmse(cov, [left, right])
    assert (n_l, n_r) == (1, 2)
    assert rmse_l == pytest.approx(3.0)
    assert rmse_r == pytest.approx(np.sqrt((16.0 + 0.0) / 2))
    # an empty side reports the same (0.0, 0) convention the chain's gate uses
    assert attributed_cov_rmse(np.zeros((0, 2)), [left, right]) == [(0.0, 0), (0.0, 0)]
    assert attributed_cov_rmse(cov, [left, np.zeros((0, 2))])[1] == (0.0, 0)


def test_sign_test_two_sided_probability() -> None:
    st = sign_test([0.1, 0.2, 0.3, -0.1, 0.0])
    assert (st["pos"], st["neg"], st["ties"], st["n"]) == (3, 1, 1, 4)
    assert st["p"] == pytest.approx(0.625)  # 2 * (C(4,0) + C(4,1)) / 2**4
    assert sign_test([])["p"] is None


def test_paired_deltas_skip_missing_sides() -> None:
    rows = [{"c": 0.5, "b": 0.2}, {"c": None, "b": 0.2}, {"c": 0.1, "b": None}]
    assert paired_deltas(rows, "c", "b") == pytest.approx([0.3])


def test_summarize_reports_n_median_mean_p90() -> None:
    s = summarize([1.0, 2.0, 3.0, 10.0])
    assert s["n"] == 4 and s["median"] == 2.5
    assert summarize([])["median"] is None


# ------------------------------------------------------- M4 shape delta helpers


def test_polyline_shape_delta_ignores_a_pure_translation() -> None:
    a = _arc(40)
    b = a + np.array([1.0, 1.0])
    mean, p90 = polyline_shape_delta(a, b, xh=10.0)
    assert mean == pytest.approx(0.0, abs=1e-9) and p90 == pytest.approx(0.0, abs=1e-9)


def test_polyline_shape_delta_reports_a_local_bump() -> None:
    a = _arc(40)
    b = a.copy()
    b[20:24, 1] += 2.0
    mean, p90 = polyline_shape_delta(a, b, xh=10.0)
    assert 0.0 < mean < p90
    assert polyline_shape_delta(np.zeros((1, 2)), a, xh=10.0) is None


def test_anchor_deltas_remove_the_residual_global_shift() -> None:
    chart = np.column_stack([np.linspace(0.0, 2.0, 11), np.zeros(11)])
    shifted = chart + np.array([0.3, 0.0])
    assert np.allclose(anchor_deltas(chart, shifted), 0.0)
    bent = shifted.copy()
    bent[-1, 1] += 0.5
    deltas = anchor_deltas(chart, bent)
    # hypot(0.3, 0.5) minus the median displacement (0.3) — the shift is gone,
    # the bend survives.
    assert deltas[-1] == pytest.approx(np.hypot(0.3, 0.5) - 0.3)
    assert deltas[0] == pytest.approx(0.0)
    assert anchor_deltas(chart, chart[:5]) is None


def test_body_stroke_bounds_skip_a_diacritic_stroke() -> None:
    """An i-shaped template: body stroke on the baseline, dot stroke entirely
    above the midband — the stub arc must be cut on the BODY stroke."""
    body = np.column_stack([np.linspace(0.0, 0.4, 6), np.linspace(0.0, 1.0, 6)])
    dot = np.array([[0.2, 1.6], [0.25, 1.65]])
    anchors = np.vstack([body, dot])
    bounds, first_body, last_body = body_stroke_bounds(anchors, [0, 6])
    assert bounds == [0, 6, 8]
    assert (first_body, last_body) == (0, 0)


# --------------------------------------------------- M4: the MAD noise floor


def test_load_anchor_mad_reads_the_aggregate_hull(tmp_path) -> None:
    path = tmp_path / "aggregates.json"
    path.write_text(
        json.dumps(
            [
                {"glyph_key": "d", "variant": 0, "hull": {"anchor_mad": [[0.01, 0.0], [0.0, 0.03]]}},
                {"glyph_key": "d", "variant": 100, "hull": {"anchor_mad": [[9.0, 9.0]]}},  # not a base row
                {"glyph_key": "e", "variant": 0, "hull": {}},  # no hull → no entry
            ]
        )
    )
    table = load_anchor_mad("suetterlin", ("pairs",), path=path)
    assert set(table["by_key"]) == {"d"}
    assert table["by_key"]["d"].shape == (2, 2)
    assert table["pooled"] == pytest.approx(0.02)  # median of hypot(0.01, 0) and hypot(0, 0.03)
    assert table["source"] == str(path)


def test_load_anchor_mad_without_a_file_is_empty(tmp_path) -> None:
    table = load_anchor_mad("suetterlin", ("pairs",), path=tmp_path / "nope.json")
    assert table == {"by_key": {}, "pooled": None, "source": "none"}


def test_mad_reference_labels_a_pooled_fallback(tmp_path) -> None:
    path = tmp_path / "aggregates.json"
    path.write_text(json.dumps([{"glyph_key": "d", "hull": {"anchor_mad": [[0.01, 0.0], [0.03, 0.0]]}}]))
    table = load_anchor_mad("suetterlin", ("pairs",), path=path)
    own, source = _mad_reference(table, "d", 2)
    assert source == "aggregate" and own.tolist() == pytest.approx([0.01, 0.03])
    # A glyph without a row — 49 of 62 authored Sütterlin glyphs — is explicitly
    # labelled rather than silently compared against another glyph's spread.
    pooled, source = _mad_reference(table, "q", 3)
    assert source == "pooled" and len(pooled) == 3
    # A stale row with a different anchor count is not a floor either.
    _, source = _mad_reference(table, "d", 5)
    assert source == "pooled"
    assert _mad_reference({"by_key": {}, "pooled": None}, "d", 2) == (None, "none")


# -------------------------------------------------------------- CLI + classes


def test_pair_class_follows_the_befund_exit_classes() -> None:
    assert pair_class("d") == "loop_exit"
    assert pair_class("longs") == "loop_exit"
    assert pair_class("r") == "deckstrich_arm"
    assert pair_class("o") == "deckstrich_arm"
    assert pair_class("B") == "capital"
    assert pair_class("e") == "arcade_diagonal"


def test_parse_pair_filter_accepts_both_forms() -> None:
    assert parse_pair_filter("de,on") == {("d", "e"), ("o", "n")}
    assert parse_pair_filter("longs:t, de") == {("longs", "t"), ("d", "e")}
    with pytest.raises(SystemExit):
        parse_pair_filter("abc")
    with pytest.raises(SystemExit):
        parse_pair_filter(":x")


# ------------------------------------------ the frozen ChainFit contract seam


def _segment(
    kind: str, *, converged: bool, slot: int | None = None, key: str | None = None, local: bool | None = None
) -> ChainSegment:
    return ChainSegment(
        kind=kind,
        slot_index=slot,
        key=key,
        anchor_slice=(0, 4),
        sample_slice=(0, 8),
        fitted_anchors=None,
        polyline_px=np.array([[0.0, 0.0], [1.0, 0.0]]),
        geo_rmse_px=1.5,
        cov_rmse_px=2.0,
        n_cov=17,
        cov_rmse_local_px=1.2,
        n_cov_local=11,
        converged=converged,
        converged_local=converged if local is None else local,
        max_anchor_delta=0.21,
    )


def _chain_fit() -> ChainFit:
    return ChainFit(
        case=None,
        slot_a=0,
        segments=[
            # The left letter fails the UNION gate but clears the letter-local
            # one — the exact asymmetry Stage-B precondition 1 is about.
            _segment("letter", converged=False, local=True, slot=0, key="d"),
            _segment("connector", converged=False),
            _segment("letter", converged=True, slot=1, key="e"),
        ],
        slot_shift_units={0: (0.10, -0.05), 1: (-0.20, 0.0)},
        slot_at_bound={0: False, 1: True},
        global_shift_units=(0.02, 0.01),
        cut_indices=(5, 0),
        connector_units=np.array([[0.0, 0.5], [0.3, 0.6]]),
        converged=False,
        converged_local=True,
        # exactly the keys `chain.fit_pair_chain` writes — the export used to read
        # a "status" key that never existed, so the termination reason and the
        # x0-vs-x* energies were silently empty on every row.
        fit_meta={
            "optimizer_success": False,
            "message": "STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT",
            "iterations": 300,
            "n_evaluations": 322,
            "n_params": 530,
            "energies": {"f": 0.0866, "e_geo": 0.0096, "e_smooth": 7374.08},
            "energies_initial": {"f": 250.406, "e_geo": 0.0096, "e_smooth": 25039309.76},
        },
    )


def test_fill_chain_segments_reads_the_contract_by_kind() -> None:
    row: dict = {}
    left, conn, right = _fill_chain_segments(row, _chain_fit())
    assert (left.key, right.key) == ("d", "e") and conn.kind == "connector"
    assert row["chain_l_converged"] is False and row["chain_c_converged"] is False
    assert row["chain_c_n_cov"] == 17 and row["chain_r_geo_rmse_px"] == 1.5
    # The connector's own gate is reported separately from the chain's verdict.
    assert row["chain_converged"] is False
    assert row["chain_connector_yielded"] is False


def test_fill_chain_segments_reports_both_coverage_gates() -> None:
    """Stage-B precondition 1: the union gate and the letter-local one travel in
    the SAME row, so the like-for-like M1 column is a read, not a re-run."""
    row: dict = {}
    _fill_chain_segments(row, _chain_fit())
    assert row["chain_l_converged"] is False and row["chain_l_converged_local"] is True
    assert row["chain_l_cov_rmse_px"] == 2.0 and row["chain_l_cov_rmse_local_px"] == 1.2
    assert row["chain_l_n_cov"] == 17 and row["chain_l_n_cov_local"] == 11
    assert row["chain_converged"] is False and row["chain_converged_local"] is True


def test_fill_chain_placement_maps_the_two_slot_blocks() -> None:
    row: dict = {}
    _fill_chain_placement(row, _chain_fit(), slot_a=0)
    assert (row["chain_l_dx"], row["chain_l_dy"]) == (0.1, -0.05)
    assert (row["chain_r_dx"], row["chain_r_dy"]) == (-0.2, 0.0)
    assert row["chain_l_at_bound"] is False and row["chain_r_at_bound"] is True
    assert row["chain_at_bound"] is True
    assert (row["chain_cut_l"], row["chain_cut_r"]) == (5, 0)
    assert row["chain_n_params"] == 530


def test_fill_chain_placement_exports_the_optimizer_termination() -> None:
    """The stalled-solve instrumentation: WHY the solve stopped and whether it
    moved at all have to be readable from the row, not inferred from zeros."""
    row: dict = {}
    _fill_chain_placement(row, _chain_fit(), slot_a=0)
    assert row["chain_status_msg"] == "STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT"
    assert row["chain_optimizer_success"] is False
    assert row["chain_iterations"] == 300 and row["chain_n_evaluations"] == 322
    assert row["chain_f_initial"] == 250.406 and row["chain_f_final"] == 0.0866
    assert row["chain_e_smooth_initial"] == 25039309.76
    assert row["chain_e_geo_initial"] == row["chain_e_geo_final"] == 0.0096  # nothing moved
    assert row["chain_energies_initial_finite"] is True
    # terms the meta does not carry come out as None, not as a fabricated 0.0
    assert row["chain_e_cov_initial"] is None


# ------------------------------ the additive `result=` kwarg on dissect_occurrence


def _stub_case() -> WordCase:
    """The smallest case that passes `has_specimen` — the dissection never gets
    past the composition gate, which is exactly what these tests check."""
    return WordCase(
        id="stub",
        word="de",
        kind="word",
        slots=[],
        templates={},
        style_ratio=[1, 1, 1],
        width_resolver="constant",
        nib_units=0.07,
        rect=[0, 0, 4, 4],
        baseline_y=3,
        midband_y=1,
        crop=np.zeros((4, 4)),
        skel=np.zeros((4, 4), dtype=bool),
    )


def _stub_result(case: WordCase) -> WordDeriveResult:
    """A composition with a hole — `dissect_occurrence` returns None on it."""
    return WordDeriveResult(
        case=case,
        payloads={},
        composed={"missing": ["d"], "items": []},
        report=None,
        segments=None,
        xh_px=2.0,
        baseline_row=3.0,
        registration={"tx": 0.0, "ty": 0.0, "xh_px": 2.0},
    )


def test_dissect_occurrence_reuses_a_passed_in_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """The harness composes each case ONCE — a word with five joins must not
    run `derive_word` five times."""

    def _boom(_case):
        raise AssertionError("derive_word must not run when a result is passed in")

    monkeypatch.setattr(analyze, "derive_word", _boom)
    case = _stub_case()
    assert analyze.dissect_occurrence(case, 0, trace=False, result=_stub_result(case)) is None


def test_dissect_occurrence_derives_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default `result=None` keeps the old behaviour — and every old caller."""
    calls: list[WordCase] = []

    def _record(case):
        calls.append(case)
        return _stub_result(case)

    monkeypatch.setattr(analyze, "derive_word", _record)
    case = _stub_case()
    assert analyze.dissect_occurrence(case, 0, trace=False) is None
    assert calls == [case]


def test_shape_samples_is_a_sane_resampling_budget() -> None:
    assert SHAPE_SAMPLES >= 24
