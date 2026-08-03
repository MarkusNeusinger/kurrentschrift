"""Unit tests for `tools/pairlab/connector_qc.py` — the §5c connector-degeneracy
detector.

Every geometry here is hand-built rather than taken from a fixture: the point of
the module is that a *shape* is wrong, so the tests state the shape. Each of the
four signals gets one polyline that trips it and the healthy set gets three that
must stay silent — a normal short join, a genuine loop exit with real (but
sub-threshold) backward arc, and a connector sitting exactly on the seam-share
threshold, because a `>` that is secretly a `>=` would flag every honest join
that uses its full stub zone.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from tools.pairlab.connector_qc import (
    DEFAULTS,
    QcThresholds,
    connector_degenerate,
    connector_signals,
    degenerate_reason,
)


# The two letters' facing ink edges used by most cases: the left letter ends at
# x = 0, the right one starts at x = 1 — a one-x-height ink gap, which is the
# ordinary Sütterlin spacing the detector is calibrated around.
A_MAX_X, B_MIN_X = 0.0, 1.0

# A connector that arrives, but by ploughing 0.8 xh through each letter.
SEAM_RUNAWAY = [(-0.80, 0.40), (0.0, 0.40), (0.50, 0.75), (1.00, 0.40), (1.80, 0.40)]


def _arc(pts) -> float:
    p = np.asarray(pts, dtype=float)
    return float(np.hypot(*(p[1:] - p[:-1]).T).sum())


# ------------------------------------------------------------ the four signals


def test_seam_share_fires_when_the_connector_reaches_into_both_letters():
    """0.8 xh of arc left of the left letter's ink and 0.8 right of the right
    one's — 1.6 xh total against the calibrated 1.3 xh budget. Bowed in the middle
    so the straightness rule cannot be what is really being observed."""
    conn = SEAM_RUNAWAY
    sig = connector_signals(conn, A_MAX_X, B_MIN_X)
    assert sig is not None
    assert sig.seam_left_units == pytest.approx(0.8)
    assert sig.seam_right_units == pytest.approx(0.8)
    assert sig.seam_total_units > DEFAULTS.max_seam_total_units
    assert sig.forward_ratio > DEFAULTS.min_forward_ratio  # it does arrive …
    assert connector_degenerate(conn, A_MAX_X, B_MIN_X) == "seam_share"  # … but through both letters


def test_backward_arc_fires_on_a_connector_that_never_arrives():
    """The §5c failure in miniature: instead of crossing the gap the connector
    slides near-vertically down the left letter's own stem and ends to the LEFT of
    where it started. Inside the gap throughout, so seam share is clean and this
    is the signal being tested."""
    conn = [(0.70, 1.00), (0.62, 0.78), (0.50, 0.58), (0.36, 0.38), (0.20, 0.20)]
    sig = connector_signals(conn, A_MAX_X, B_MIN_X)
    assert sig is not None
    assert sig.seam_total_units == pytest.approx(0.0)  # nothing outside the gap
    assert sig.net_dx_units < 0.0
    assert sig.forward_ratio < DEFAULTS.min_forward_ratio
    assert connector_degenerate(conn, A_MAX_X, B_MIN_X) == "backward_arc"


def test_arc_vs_gap_fires_on_a_detour_that_stays_inside_the_gap():
    """Nine zig-zags inside the gap: no seam, always advancing (so the forward
    rule stays silent), but ~3.7 xh of arc spent crossing 1 xh of gap."""
    xs = np.linspace(0.05, 0.95, 10)
    conn = [(float(x), 0.20 if i % 2 else -0.20) for i, x in enumerate(xs)]
    sig = connector_signals(conn, A_MAX_X, B_MIN_X)
    assert sig is not None
    assert sig.seam_total_units == pytest.approx(0.0)
    assert sig.backward_frac == pytest.approx(0.0)  # x never decreases
    assert sig.forward_ratio > DEFAULTS.min_forward_ratio
    assert sig.arc_vs_gap > DEFAULTS.max_arc_vs_gap
    assert connector_degenerate(conn, A_MAX_X, B_MIN_X) == "arc_vs_gap"


def test_straight_long_fires_only_when_straight_AND_long():
    """The §5c phenomenon: a long straight diagonal. Straightness alone does not
    fire (the short twin of the same line is silent), length alone does not
    either (the bowed twin of the same span is silent)."""
    long_straight = [(0.0, 0.0), (1.2, 0.45)]
    assert _arc(long_straight) >= DEFAULTS.min_straight_arc_units
    assert connector_degenerate(long_straight, A_MAX_X, 1.2) == "straight_long"

    # same direction, a third of the length — straight but short
    short_straight = [(0.0, 0.0), (0.4, 0.15)]
    assert connector_degenerate(short_straight, A_MAX_X, 0.4) is None

    # same span, bowed — long but not straight
    bowed = [(0.0, 0.0), (0.4, 0.45), (0.8, 0.55), (1.2, 0.45)]
    sig = connector_signals(bowed, A_MAX_X, 1.2)
    assert sig is not None and sig.straightness > DEFAULTS.max_straight_ratio
    assert connector_degenerate(bowed, A_MAX_X, 1.2) is None


# -------------------------------------------------------------- healthy curves


def test_normal_short_connector_is_silent():
    """An ordinary arcade join: a shallow bow from just inside the left letter to
    just inside the right one, claiming ~0.15 xh of each stub zone."""
    conn = [(-0.15, 0.10), (0.15, 0.35), (0.55, 0.40), (0.85, 0.25), (1.15, 0.10)]
    sig = connector_signals(conn, A_MAX_X, B_MIN_X)
    assert sig is not None
    assert sig.seam_total_units < DEFAULTS.max_seam_total_units
    assert sig.backward_frac == pytest.approx(0.0)
    assert sig.arc_vs_gap < DEFAULTS.max_arc_vs_gap
    assert connector_degenerate(conn, A_MAX_X, B_MIN_X) is None


def test_genuine_loop_exit_with_sub_threshold_backward_arc_is_silent():
    """A d-Schleife leaves its form above the midband and dips back left before it
    turns down into the next letter. That backward stretch is real writing, not a
    defect — it has to stay under the threshold."""
    conn = [(-0.10, 1.05), (0.18, 0.95), (0.10, 0.72), (0.45, 0.45), (0.80, 0.28), (1.10, 0.15)]
    sig = connector_signals(conn, A_MAX_X, B_MIN_X)
    assert sig is not None
    assert sig.backward_frac > 0.0  # it really does run backwards for a stretch …
    assert sig.forward_ratio > DEFAULTS.min_forward_ratio  # … but it arrives
    assert connector_degenerate(conn, A_MAX_X, B_MIN_X) is None


def test_connector_exactly_at_the_seam_threshold_is_silent():
    """Seam share exactly at the budget (0.65 xh per side) must pass — the rule is
    `>`, not `>=`, or the calibrated budget would be unusable by an honest join."""
    # level arc inside each letter, a bowed crossing in between (bowed so the case
    # tests the seam rule and not, incidentally, the straightness one)
    conn = [(-0.65, 0.30), (0.0, 0.30), (0.50, 0.62), (1.00, 0.30), (1.65, 0.30)]
    sig = connector_signals(conn, A_MAX_X, B_MIN_X)
    assert sig is not None
    assert sig.seam_total_units == pytest.approx(DEFAULTS.max_seam_total_units)
    assert sig.straightness > DEFAULTS.max_straight_ratio
    assert connector_degenerate(conn, A_MAX_X, B_MIN_X) is None


# ------------------------------------------------------------------ mechanics


def test_thresholds_are_overridable_in_both_directions():
    """The dataclass is the calibration surface: tightening flags a healthy curve,
    loosening clears a flagged one — without touching the geometry."""
    healthy = [(-0.15, 0.10), (0.15, 0.35), (0.55, 0.40), (0.85, 0.25), (1.15, 0.10)]
    assert connector_degenerate(healthy, A_MAX_X, B_MIN_X) is None
    strict = dataclasses.replace(DEFAULTS, max_seam_total_units=0.1)
    assert connector_degenerate(healthy, A_MAX_X, B_MIN_X, thresholds=strict) == "seam_share"

    never_arrives = [(0.70, 1.00), (0.62, 0.78), (0.50, 0.58), (0.36, 0.38), (0.20, 0.20)]
    assert connector_degenerate(never_arrives, A_MAX_X, B_MIN_X) == "backward_arc"
    lax = dataclasses.replace(DEFAULTS, min_forward_ratio=-9.0, max_arc_vs_gap=99.0)
    assert connector_degenerate(never_arrives, A_MAX_X, B_MIN_X, thresholds=lax) is None
    assert QcThresholds().min_forward_ratio == DEFAULTS.min_forward_ratio  # DEFAULTS unmutated


def test_priority_order_is_fixed_so_a_row_is_counted_once():
    """A curve that trips several signals reports the seam one — the reason code
    has to be stable, or the report's per-reason histogram double-counts."""
    runaway = [(1.8, 1.0), (1.4, 0.6), (-0.8, 0.1)]
    sig = connector_signals(runaway, A_MAX_X, B_MIN_X)
    assert sig is not None
    assert sig.seam_total_units > DEFAULTS.max_seam_total_units
    assert sig.forward_ratio < DEFAULTS.min_forward_ratio  # would fire too
    assert degenerate_reason(sig) == "seam_share"


def test_xh_units_rescales_a_pixel_frame_to_the_same_verdict():
    """The px caller (`xh_units=xh_px`) and the composed-units caller must agree —
    the detector's thresholds are in x-heights, not in whatever frame it is fed."""
    conn_units = np.array(SEAM_RUNAWAY)
    xh = 37.5
    conn_px = conn_units * xh + np.array([120.0, 4.0])  # scaled AND translated
    assert connector_degenerate(conn_units, A_MAX_X, B_MIN_X) == "seam_share"
    assert connector_degenerate(conn_px, A_MAX_X * xh + 120.0, B_MIN_X * xh + 120.0, xh) == "seam_share"


def test_the_size_gate_silences_a_stub_that_would_otherwise_trip():
    """The calibrated `min_chord_units` gate: the SAME wrong-way shape scaled down
    to a stub is not a verdict, it is noise. Scaled up past the gate it is."""
    shape = np.array([(0.70, 1.00), (0.62, 0.78), (0.50, 0.58), (0.36, 0.38), (0.20, 0.20)])
    centre = shape.mean(axis=0)
    stub = (shape - centre) * 0.2 + centre  # same direction, a fifth of the size
    assert connector_signals(stub, A_MAX_X, B_MIN_X).forward_ratio < DEFAULTS.min_forward_ratio
    assert connector_signals(stub, A_MAX_X, B_MIN_X).chord_units < DEFAULTS.min_chord_units
    assert connector_degenerate(stub, A_MAX_X, B_MIN_X) is None
    assert connector_degenerate(shape, A_MAX_X, B_MIN_X) == "backward_arc"
    # and the gate is a threshold, not a hard-coded exemption
    open_gate = dataclasses.replace(DEFAULTS, min_chord_units=0.0)
    assert connector_degenerate(stub, A_MAX_X, B_MIN_X, thresholds=open_gate) == "backward_arc"


def test_a_curve_too_short_to_measure_is_not_flagged():
    """`None` means "nothing to say", not "healthy" — an absent connector is the
    chain's own `n_cov` gate's business, not this detector's."""
    assert connector_signals([(0.3, 0.2)], A_MAX_X, B_MIN_X) is None
    assert connector_signals([], A_MAX_X, B_MIN_X) is None
    assert connector_signals([(0.3, 0.2), (0.3, 0.2)], A_MAX_X, B_MIN_X) is None  # zero arc
    assert connector_degenerate([(0.3, 0.2)], A_MAX_X, B_MIN_X) is None
