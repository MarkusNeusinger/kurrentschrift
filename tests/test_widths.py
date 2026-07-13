"""Direct unit tests for the width-profile resolver + pen models (core/widths.py).

Complements the broad-nib coverage in test_tri_script.py with focused, table-driven
checks of the BroadNib geometry, the per-stroke tangent helper, and every branch of
`resolve_half_widths` (constant collapse, broad-nib regeneration, and the passthrough
fallbacks). Pure deterministic math — no DB, no HTTP (issue #185).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from core.widths import (
    BROAD_NIB_ANGLE_DEG,
    BroadNib,
    PenStyle,
    _per_stroke_tangents_deg,
    broad_nib_half_widths,
    resolve_half_widths,
)


# ---------------------------------------------------------------- BroadNib math


def test_broad_nib_edge_units_and_extremes():
    nib = BroadNib(width_units=0.2, angle_deg=15.0, edge_fraction=0.25)
    assert nib.edge_units == pytest.approx(0.05)
    # Along the nib edge (φ == α): only the edge thickness writes.
    assert nib.half_width_at(15.0) == pytest.approx(0.5 * nib.edge_units)
    # Perpendicular to the edge (φ == α + 90): the full nib width writes.
    assert nib.half_width_at(105.0) == pytest.approx(0.5 * nib.width_units)


def test_broad_nib_half_width_is_180_periodic():
    nib = BroadNib(width_units=0.2, angle_deg=15.0, edge_fraction=0.25)
    for phi in (0.0, 33.0, 79.0, 150.0):
        assert nib.half_width_at(phi) == pytest.approx(nib.half_width_at(phi + 180.0))


def test_broad_nib_half_and_edge_vectors():
    nib = BroadNib(width_units=0.2, angle_deg=15.0, edge_fraction=0.25)
    r = math.radians(15.0)
    hx, hy = nib.half_vector
    assert (hx, hy) == pytest.approx((0.5 * 0.2 * math.cos(r), 0.5 * 0.2 * math.sin(r)))
    ex, ey = nib.edge_vector
    assert (ex, ey) == pytest.approx((-0.5 * 0.05 * math.sin(r), 0.5 * 0.05 * math.cos(r)))
    # The edge vector is perpendicular to the half (nib) vector.
    assert hx * ex + hy * ey == pytest.approx(0.0, abs=1e-12)


def test_broad_nib_defaults_use_koch_angle():
    assert BroadNib().angle_deg == BROAD_NIB_ANGLE_DEG == 15.0


# ------------------------------------------------------- _per_stroke_tangents_deg


def test_per_stroke_tangents_axis_aligned():
    horiz = np.column_stack([np.linspace(0.0, 4.0, 5), np.zeros(5)])
    assert np.allclose(_per_stroke_tangents_deg(horiz, None), 0.0)
    vert = np.column_stack([np.zeros(5), np.linspace(0.0, 4.0, 5)])
    assert np.allclose(_per_stroke_tangents_deg(vert, None), 90.0)


def test_per_stroke_tangents_never_bridge_a_lift():
    horiz = np.column_stack([np.linspace(0.0, 4.0, 5), np.zeros(5)])
    vert = np.column_stack([np.full(5, 9.0), np.linspace(0.0, 4.0, 5)])
    pts = np.vstack([horiz, vert])
    tangents = _per_stroke_tangents_deg(pts, [5])
    assert np.allclose(tangents[:5], 0.0)  # first stroke stays horizontal
    assert np.allclose(tangents[5:], 90.0)  # second stroke stays vertical (no bridge)


# ------------------------------------------------------- broad_nib_half_widths


def test_broad_nib_half_widths_vertical_stroke():
    nib = BroadNib(width_units=0.2, angle_deg=15.0, edge_fraction=0.1)
    pts = np.column_stack([np.zeros(6), np.linspace(0.0, 1.0, 6)])  # vertical
    hw = broad_nib_half_widths(pts, nib)
    assert np.allclose(hw, nib.half_width_at(90.0))


# --------------------------------------------------------- resolve_half_widths


def test_resolve_constant_collapses_to_median():
    measured = np.array([1.0, 2.0, 3.0, 10.0])
    resolved = resolve_half_widths(measured, "constant")
    assert np.allclose(resolved, np.median(measured))  # 2.5, robust to the outlier


def test_resolve_constant_empty_passes_through():
    empty = np.array([])
    assert resolve_half_widths(empty, "constant").size == 0


def test_resolve_pressure_resolver_is_passthrough():
    # "pressure" has no special branch in resolve_half_widths (the measured
    # profile IS the Schwellzug), so it returns the measurement unchanged — the
    # same passthrough any resolver other than constant/broad_nib takes.
    measured = np.array([0.03, 0.05, 0.04])
    assert np.allclose(resolve_half_widths(measured, "pressure"), measured)


def test_resolve_broad_nib_regenerates_from_geometry():
    measured = np.array([0.05, 0.05, 0.05, 0.05])
    pts = np.column_stack([np.zeros(4), np.linspace(0.0, 1.2, 4)])  # vertical
    nib = BroadNib(width_units=0.2, angle_deg=15.0, edge_fraction=0.1)
    resolved = resolve_half_widths(measured, "broad_nib", points=pts, nib=nib)
    assert np.allclose(resolved, nib.half_width_at(90.0))


def test_resolve_broad_nib_without_geometry_falls_back():
    measured = np.array([0.05, 0.06, 0.05, 0.06])
    assert np.allclose(resolve_half_widths(measured, "broad_nib"), measured)


def test_resolve_broad_nib_length_mismatch_falls_back():
    measured = np.array([0.05, 0.06, 0.05, 0.06])
    pts = np.column_stack([np.zeros(3), np.linspace(0.0, 1.0, 3)])  # 3 != 4
    assert np.allclose(resolve_half_widths(measured, "broad_nib", points=pts), measured)


def test_resolve_broad_nib_too_short_falls_back():
    measured = np.array([0.05])
    pts = np.array([[0.0, 0.0]])
    assert np.allclose(resolve_half_widths(measured, "broad_nib", points=pts), measured)


# ------------------------------------------------------------------- PenStyle


def test_pen_style_defaults():
    pen = PenStyle(kind="pressure")
    assert pen.kind == "pressure"
    assert pen.nib is None and pen.hairline_half is None
