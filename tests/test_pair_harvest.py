"""The pair harvest importer (redesign R3 Erstbefüllung): geometry construction.

Pure-math coverage — the fixture-driven dissection itself needs the gitignored
wordbench fixtures and stays a local tool; what CI pins is the PairGeometry
construction (splice, clipping, baseline-lock correction, downsampling) and
that a harvested entry passes the admin API's schema validation.
"""

import numpy as np

from api.schemas import GlyphPairIn
from core.shaping import GlyphSlot
from tools.pairlab.harvest import MAX_CONNECTOR_POINTS, connector_points
from tools.wordbench.run import _slot_overrides


def test_touching_letters_yield_direct_segment() -> None:
    pts = connector_points((0.5, 1.0), (1.5, 0.6), np.zeros((0, 2)))
    assert pts == [[0.0, 0.0], [1.0, -0.4]]


def test_real_stroke_is_spliced_and_clipped() -> None:
    real = np.array([[0.4, 1.0], [0.75, 0.8], [1.0, 0.7], [1.6, 0.6]])  # first/last outside
    pts = connector_points((0.5, 1.0), (1.5, 0.6), real)
    assert pts[0] == [0.0, 0.0]
    assert pts[-1] == [1.0, -0.4]
    # Only the strictly-between real points survive (plus the two endpoints).
    assert len(pts) == 4


def test_end_dy_correction_is_spread_by_progress() -> None:
    real = np.array([[1.0, 0.8]])
    pts = connector_points((0.5, 1.0), (1.5, 0.6), real, end_dy=0.2)
    assert pts[0] == [0.0, 0.0]  # start never moves
    assert pts[-1][1] == -0.2  # -0.4 specimen delta + 0.2 baseline-lock correction
    # The midpoint (x-progress 0.5) picks up half the correction; smoothing has
    # already averaged the raw y before the shear applies.
    mid = pts[1]
    assert abs(mid[0] - 0.5) < 1e-6
    assert abs(mid[1] - (-0.2 + 0.1)) < 0.06


def test_long_strokes_downsample_with_endpoints_kept() -> None:
    xs = np.linspace(0.51, 1.49, 400)
    real = np.column_stack([xs, np.full_like(xs, 0.8)])
    pts = connector_points((0.5, 1.0), (1.5, 0.6), real)
    assert len(pts) == MAX_CONNECTOR_POINTS
    assert pts[0] == [0.0, 0.0]
    assert pts[-1] == [1.0, -0.4]


def test_harvested_entry_passes_api_schema() -> None:
    geometry = {
        "offset": [0.42, -0.03],
        "connector": connector_points((0.5, 1.0), (0.92, 0.97), np.array([[0.7, 0.9]])),
    }
    validated = GlyphPairIn(geometry=geometry, provenance="harvested", specimen_id="Bi")
    assert validated.approved is False


def _slot(key: str, position: str | None) -> GlyphSlot:
    return GlyphSlot(key=key, text=key[0], position=position, ligature=False, space=False)


def test_slot_overrides_map_bases_onto_raw_slot_keys() -> None:
    # Frozen pre-R2 fixture slots carry position suffixes; the harvest file is
    # keyed by bare registry bases — the mapping must reunite them per word.
    slots = [_slot("B-initial", "initial"), _slot("i-final", "final")]
    geometry = {"offset": [0.4, 0.0], "connector": [[0.0, 0.0], [0.4, 0.0]]}
    mapped = _slot_overrides(slots, {("B", "i"): geometry})
    assert mapped == {("B-initial", "i-final"): geometry}
    # Bare post-R2 slots map through unchanged.
    slots = [_slot("B", None), _slot("i", None)]
    assert _slot_overrides(slots, {("B", "i"): geometry}) == {("B", "i"): geometry}
    # No override for the pair -> empty mapping.
    assert _slot_overrides(slots, {("D", "u"): geometry}) == {}
