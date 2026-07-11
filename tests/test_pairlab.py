"""Tests for the pairlab join-dissection toolkit.

The pure geometry helpers (pair spec parsing, adaptation-length scan, the
column tracker for the specimen's connecting stroke, the connector
regeneration) are tested unconditionally on synthetic inputs; the end-to-end
dissection runs against the word-bench fixtures and skips where they are not
exported (they are DB-derived and gitignored, like the wordlab tests).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from tools.pairlab.analyze import (
    ADAPT_PERSIST_UNITS,
    ADAPT_THRESH_UNITS,
    _adaptation_length,
    _generate_connector,
    _real_join,
    _stub_vs_body_delta,
    dissect_occurrence,
    find_occurrences,
    pair_bases,
    trace_letter_ductus,
)
from tools.wordlab.cases import DEFAULT_FIXTURES_DIR


# ------------------------------------------------------------------ pure units


def test_pair_bases_two_letters() -> None:
    assert pair_bases("re") == ("r", "e")


def test_pair_bases_comma_form() -> None:
    assert pair_bases("longs,a") == ("longs", "a")


def test_pair_bases_rejects_malformed() -> None:
    with pytest.raises(SystemExit):
        pair_bases("abc")
    with pytest.raises(SystemExit):
        pair_bases(",x")


def test_adaptation_length_zero_when_on_template() -> None:
    profile = np.column_stack([np.linspace(0, 1.0, 20), np.full(20, 0.02)])
    assert _adaptation_length(profile) == 0.0


def test_adaptation_length_finds_departure_zone() -> None:
    arcs = np.linspace(0, 1.0, 51)
    devs = np.where(arcs < 0.3, 0.3, 0.02)  # off-template for the first 0.3 xh
    adapt = _adaptation_length(np.column_stack([arcs, devs]))
    assert 0.28 <= adapt <= 0.34


def test_adaptation_length_ignores_single_dip_inside_stub() -> None:
    """One sub-threshold sample inside the deviating zone must not end it."""
    arcs = np.linspace(0, 1.0, 51)
    devs = np.where(arcs < 0.4, 0.3, 0.02)
    dip = np.searchsorted(arcs, 0.2)
    devs[dip] = ADAPT_THRESH_UNITS / 2  # a lone dip, shorter than ADAPT_PERSIST_UNITS
    assert ADAPT_PERSIST_UNITS < 0.2  # the dip's persistence window ends inside the stub
    adapt = _adaptation_length(np.column_stack([arcs, devs]))
    assert adapt >= 0.38


def test_adaptation_length_saturates_when_never_back() -> None:
    profile = np.column_stack([np.linspace(0, 1.2, 20), np.full(20, 0.5)])
    assert _adaptation_length(profile) == pytest.approx(1.2)


def test_generate_connector_hits_endpoints_and_leaves_tangent() -> None:
    p0, p3 = (0.0, 0.4), (0.5, 0.55)
    line = _generate_connector(p0, 35.0, p3, 40.0)
    assert line[0] == pytest.approx(p0)
    assert line[-1] == pytest.approx(p3)
    launch = math.degrees(math.atan2(line[1][1] - line[0][1], line[1][0] - line[0][0]))
    assert launch == pytest.approx(35.0, abs=5.0)  # G1 at the exit (± sampling discretisation)


def test_generate_connector_backward_exit_rescued() -> None:
    """A backward exit tangent (w/v bow) must not loop the connector left."""
    line = _generate_connector((0.0, 0.5), 170.0, (0.4, 0.5), 40.0)
    xs = [p[0] for p in line]
    assert min(xs) >= -0.01  # never travels left of the exit


def test_real_join_tracks_continuous_stroke_not_median() -> None:
    """Two strokes in the gap band (arm above, join below): the tracker must
    follow the one continuous with the seed, not blur them into a median."""
    skel = np.zeros((60, 60), dtype=bool)
    skel[10, 20:40] = True  # a level arm high in the band
    for i, c in enumerate(range(20, 40)):  # the actual join, descending from y=30
        skel[30 + i // 2, c] = True
    pts = _real_join(skel, a_max_x=19.5, b_min_x=40.5, seed_y=30.0, baseline_row=50.0, xh=40.0)
    assert len(pts) == 20
    assert pts[:, 1].min() >= 29.0  # never jumped to the arm at y=10


def test_real_join_empty_when_letters_touch() -> None:
    skel = np.zeros((20, 20), dtype=bool)
    pts = _real_join(skel, a_max_x=10.0, b_min_x=9.0, seed_y=5.0, baseline_row=15.0, xh=10.0)
    assert len(pts) == 0


def test_stub_vs_body_delta_localises_the_moved_stub() -> None:
    """Anchors moved only near the stroke end must show up as a stub delta
    well above the body delta (global-shift component removed)."""
    anchors = np.column_stack([np.linspace(0.0, 2.0, 21), np.zeros(21)])
    fitted = anchors.copy()
    fitted[-3:] += [0.0, 0.3]  # last ~0.3 units of arc pushed up
    stub, body = _stub_vs_body_delta(anchors, fitted, (0, 21), from_end=True)
    assert stub > 3 * max(body, 1e-6)
    stub_head, _ = _stub_vs_body_delta(anchors, fitted, (0, 21), from_end=False)
    assert stub_head < stub  # the entry side did not move


# -------------------------------------------------- fixture-gated end-to-end

fixtures_present = any(DEFAULT_FIXTURES_DIR.rglob("manifest.json"))


@pytest.mark.skipif(not fixtures_present, reason="word-bench fixtures are local-only (gitignored)")
def test_dissect_first_en_occurrence() -> None:
    occurrences = find_occurrences(("e", "n"), sets=("words",))
    assert occurrences, "the Abb.-19 words contain e→n"
    case, slot_a = occurrences[0]
    d = dissect_occurrence(case, slot_a, trace=False)
    assert d is not None
    assert d.a.base == "e" and d.b.base == "n"
    # shifts stay inside the search bounds and the fit never worsens the residual
    assert d.a.resid_after <= d.a.resid_before + 1e-9
    assert d.b.resid_after <= d.b.resid_before + 1e-9
    assert d.gen_chamfer >= 0.0
    assert len(d.tail_profile) and len(d.head_profile)
    assert 0.0 <= d.tail_adapt <= 1.2 and 0.0 <= d.head_adapt <= 1.2
    row_keys = {"id", "pair", "gen_chamfer", "tail_adapt", "head_adapt", "at_bound"}
    from tools.pairlab.analyze import summary_row

    assert row_keys <= set(summary_row(d))


@pytest.mark.skipif(not fixtures_present, reason="word-bench fixtures are local-only (gitignored)")
def test_ductus_trace_follows_the_ink() -> None:
    """The M4-fit trace of one letter must land on the specimen skeleton and
    expose the true coupling geometry (finite end tangents, plausible heights)."""
    occurrences = find_occurrences(("e", "n"), sets=("words",))
    case, slot_a = occurrences[0]
    d = dissect_occurrence(case, slot_a, trace=False)
    t = trace_letter_ductus(case, d.result, d.a, slot_a)
    assert t is not None
    assert len(t.polyline_px) > 10
    assert np.isfinite(t.geo_rmse_px)
    assert -1.5 <= t.exit_xy[1] <= 2.5  # within the writing band (units)
    assert np.isfinite(t.exit_deg) and np.isfinite(t.entry_deg)
    assert t.tail_stub_delta >= 0.0 and t.body_delta >= 0.0
