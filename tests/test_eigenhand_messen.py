"""The readings of a hand-drawn Bahn (`tools.eigenhand.messen`, V21).

Two things are pinned here. The drawing's reading of the two decode counts —
which strands a Bahn travels, and which of its lifts the composition does not
sanction — on synthetic strands where the right answer is known. And that the
strands are the FOLLOWER's own, built by the same code on the same ink-evidence
case, so a measured drawing and a followed Bahn are held against one ink. The
wiring into `pfad --messen` is tested beside the other modes, in
`tests/test_eigenhand_pfad.py::TestMessen`.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from tools.eigenhand import messen


def _strand(points: list[list[float]]) -> SimpleNamespace:
    """A strand as far as the readings look at one: its points and its length."""
    pts = np.asarray(points, dtype=float)
    return SimpleNamespace(points=pts, length=float(np.hypot(*np.diff(pts, axis=0).T).sum()))


# Two parallel strokes 40 px apart, each 100 px long — at xh = 40 px the
# tolerance is 4 px, so neither can be travelled by riding the other.
LEFT = _strand([[10.0, float(y)] for y in range(0, 101)])
RIGHT = _strand([[50.0, float(y)] for y in range(0, 101)])


class TestDensify:
    def test_no_step_is_longer_than_asked_and_the_vertices_stay(self):
        dense = messen.densify([[0.0, 0.0], [10.0, 0.0], [10.0, 3.0]], step_px=0.5)
        assert np.hypot(*np.diff(dense, axis=0).T).max() <= 0.5 + 1e-9
        for vertex in ([0.0, 0.0], [10.0, 0.0], [10.0, 3.0]):
            assert np.hypot(*(dense - vertex).T).min() < 1e-9

    def test_a_single_point_comes_back_as_it_went_in(self):
        assert messen.densify([[3.0, 4.0]]).tolist() == [[3.0, 4.0]]


class TestUnvisitedShare:
    def test_a_bahn_along_one_of_two_equal_strokes_leaves_half_the_ink(self):
        drawn = [np.array([[11.0, 0.0], [11.0, 100.0]])]  # a pixel beside the skeleton, on the ink
        assert messen.unvisited_share([LEFT, RIGHT], drawn, tol_px=4.0) == 0.5

    def test_a_bahn_along_both_leaves_nothing(self):
        drawn = [np.array([[10.0, 0.0], [10.0, 100.0]]), np.array([[50.0, 100.0], [50.0, 0.0]])]
        assert messen.unvisited_share([LEFT, RIGHT], drawn, tol_px=4.0) == 0.0

    def test_crossing_a_strand_does_not_travel_it(self):
        # The case proximity alone gets wrong: a Bahn that passes over a stroke
        # for a moment comes within any tolerance of it.
        across = [np.array([[0.0, 50.0], [60.0, 50.0]])]
        assert messen.unvisited_share([LEFT, RIGHT], across, tol_px=4.0) == 1.0

    def test_sparse_pointer_samples_still_ride_the_strand_between_them(self):
        # The editor stores pointer samples, not a pixel chain; the strand
        # pixels between two of them are ridden all the same.
        drawn = [np.array([[10.0, 0.0], [10.0, 50.0], [10.0, 100.0]])]
        assert messen.unvisited_share([LEFT], drawn, tol_px=4.0) == 0.0

    def test_no_ink_skeleton_is_no_reading_rather_than_the_best_one(self):
        # 0 is the best share there is; „nothing to measure against" is not a
        # reading at all, and the follower gives up on such a box.
        assert messen.unvisited_share([], [np.array([[0.0, 0.0], [1.0, 1.0]])], tol_px=4.0) is None

    def test_a_bahn_with_no_samples_travels_nothing(self):
        assert messen.unvisited_share([LEFT], [], tol_px=4.0) == 1.0


class TestLifts:
    @pytest.mark.parametrize(
        ("runs", "seed_lifts", "expected"),
        [
            (1, 0, 0),  # one run, a word the script joins whole
            (2, 1, 0),  # body + i-dot, where the seed lifts for the dot too
            (3, 1, 1),  # one lift the composition does not sanction
            (1, 2, 0),  # the hand joined where the seed lifts: zero, never negative
        ],
    )
    def test_only_the_lifts_the_composition_does_not_sanction_count(self, runs, seed_lifts, expected):
        assert messen.lifts_beyond_seed(runs, seed_lifts) == expected


class TestDrawnReadings:
    def test_the_block_carries_every_key_the_follower_stores(self):
        # The projection `pfad.STORED_SENSORS` is a fixed list; a key missing
        # here would reach the database as absent and read as never measured.
        from tools.eigenhand.pfad import FOLLOWER_SENSORS

        readings = messen.drawn_readings([LEFT, RIGHT], [np.array([[10.0, 0.0], [10.0, 100.0]])], 40.0, 0)
        assert set(readings) == set(FOLLOWER_SENSORS)

    def test_the_decoder_events_are_null_not_zero(self):
        # A drawing has no decode, so it has no strand changes and no priced
        # retrace turns — „none happened" and „nothing counted them" must not
        # look alike (`core.eigenhand.tintentreue.Rohzahlen`).
        readings = messen.drawn_readings([LEFT], [np.array([[10.0, 0.0], [10.0, 100.0]])], 40.0, 0)
        assert readings["jumps"] is None and readings["hairpins"] is None
        assert (readings["runs"], readings["strands"], readings["paper_lifts"]) == (1, 1, 0)
        assert readings["ink_unvisited_share"] == 0.0


class TestTheFollowersInk:
    def test_the_strands_are_the_followers_own_on_the_same_ink(self, monkeypatch):
        # `ink_and_seed` builds the strands through `strands_of` and the
        # sub-pixel rail on the ink-evidence case — the calls `follow_word`
        # makes. The composition is stubbed (a synthetic crop has no plate
        # behind it); the ink is real.
        import tools.pairlab.tintenpfad as follower
        import tools.wordlab.derive as derive
        from core.extract import binarize_adaptive, skeleton_and_width
        from core.word_metric import despeckle
        from tools.pairlab.tintenpfad import TintenpfadWeights

        crop = np.ones((120, 160))
        crop[20:100, 38:42] = 0.1  # two stems, 60 px apart
        crop[20:100, 98:102] = 0.1
        mask = despeckle(binarize_adaptive(crop))
        skel, width_map = skeleton_and_width(mask)
        case = SimpleNamespace(crop=crop, mask=mask, skel=skel, width_map=width_map)
        monkeypatch.setattr(
            derive, "derive_word", lambda _case: SimpleNamespace(report={}, registration={"tx": 0.0}, xh_px=40.0)
        )
        monkeypatch.setattr(follower, "seed_samples", lambda *_a: SimpleNamespace(stroke=np.array([0, 0, 1, 1])))

        strands, seed_lifts, xh = messen.ink_and_seed(case, TintenpfadWeights())
        assert (seed_lifts, xh) == (1, 40.0)
        assert len(strands) == 2
        left_stem = [np.array([[40.0, 20.0], [40.0, 100.0]])]
        readings = messen.drawn_readings(strands, left_stem, xh, seed_lifts)
        assert readings["ink_unvisited_share"] == pytest.approx(0.5, abs=0.05)
        # One run against a seed that lifts once: nothing unsanctioned.
        assert readings["paper_lifts"] == 0

    def test_a_failed_composition_is_no_measurement(self, monkeypatch):
        import tools.wordlab.derive as derive
        from tools.pairlab.tintenpfad import TintenpfadWeights

        monkeypatch.setattr(
            derive, "derive_word", lambda _case: SimpleNamespace(report={"failed": True}, registration={}, xh_px=0.0)
        )
        assert messen.ink_and_seed(SimpleNamespace(), TintenpfadWeights()) is None


def test_the_provenance_names_the_producer_and_the_herkunft():
    block = messen.messung("2026-09-25", {"mask_labels": True})
    assert block["gemessen_von"] == messen.MESS_VERFAHREN == "messen"
    assert block["herkunft"] == "authored"
    assert block["eingabe"] == {"mask_labels": True}
    assert block["besucht"] == {"toleranz_xh": messen.VISIT_TOLERANCE_XH, "anteil": messen.TRAVELLED_SHARE}
