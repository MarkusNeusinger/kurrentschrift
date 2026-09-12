"""The Streifen-Pfad's pure half: where a word box sits, and what a path may be.

Two things are tested here because both are arithmetic the server and the local
follower must agree on to the pixel: the frame a word box spans inside a stored
strip (`frame_for_box`), and the refusals that keep a pushed path from being
stored against the wrong ink (`check_paths`).
"""

from __future__ import annotations

import pytest

from core.eigenhand.pfad import MAX_UNIT, check_paths, frame_for_box, frames_of_row


# 10 px per mm, a strip 190 mm wide cut at x 10..200 and y 20..60.
SCALE = 10.0
WIDTH_PX = 1900
HEIGHT_PX = 400
ORIGIN_MM = [10.0, 20.0]

ROW = {
    "strip": "S0001",
    "cut_mm": [10.0, 20.0, 200.0, 60.0],
    "band_mm": {"asc_top": 24.0, "waist": 32.0, "baseline": 44.0, "desc_bot": 56.0},
    "boxes": [{"word": "lesen", "x0_mm": 15.0, "x1_mm": 45.0}, {"word": "das", "x0_mm": 55.0, "x1_mm": 75.0}],
}


def _frame(index: int = 0, **overrides):
    row = {**ROW, **overrides}
    return frame_for_box(row, ORIGIN_MM, WIDTH_PX, HEIGHT_PX, index)


def _path(**overrides) -> dict:
    return {
        "box_index": 0,
        "word": "lesen",
        "strokes": [[[0.0, 0.0], [0.5, 1.0], [1.0, 0.0]]],
        "registration_px": {"tx": 40.0, "ty": 0.0, "baseline_row": 240.0},
        "xh_px": 120.0,
        "verfahren": "tintenpfad",
        **overrides,
    }


class TestFrameForBox:
    """The nominal frame — printed ruling, strip pixels, never the word crop's."""

    def test_the_lineature_comes_out_in_strip_pixels_off_the_printed_band(self):
        frame = _frame()
        # baseline 44 mm, waist 32 mm, crop starting at 20 mm, 10 px/mm.
        assert frame["baseline_row"] == pytest.approx(240.0)
        assert frame["waist_row"] == pytest.approx(120.0)
        assert frame["xh_px"] == pytest.approx(120.0)
        assert frame["px_per_mm"] == pytest.approx(SCALE)

    def test_the_rectangle_is_the_word_crops_own_padded_and_full_height(self):
        # The same arithmetic the word-crop route cuts with: 1 mm of padding on
        # both sides, the full strip height, clamped to the strip.
        assert _frame(0)["rect_px"] == [40, 0, 360, HEIGHT_PX]
        assert _frame(1)["rect_px"] == [440, 0, 660, HEIGHT_PX]
        assert _frame(1)["word"] == "das"

    def test_a_box_the_row_does_not_have_is_refused(self):
        with pytest.raises(ValueError, match="there is no box 2"):
            _frame(2)

    def test_a_bogen_without_ruling_or_cut_geometry_is_refused_not_guessed(self):
        with pytest.raises(ValueError, match="band_mm"):
            _frame(0, band_mm={"asc_top": 24.0})
        with pytest.raises(ValueError, match="Schnittband"):
            _frame(0, cut_mm=[])

    def test_a_row_whose_geometry_is_missing_yields_no_frames_rather_than_failing(self):
        # The listing must not break over an old Bogen: a strip without
        # rectangles simply has none to offer.
        assert frames_of_row({**ROW, "cut_mm": []}, ORIGIN_MM, WIDTH_PX, HEIGHT_PX) is None
        assert len(frames_of_row(ROW, ORIGIN_MM, WIDTH_PX, HEIGHT_PX)) == 2


class TestCheckPaths:
    """What a pushed path has to be before it is stored against a strip."""

    @staticmethod
    def _check(paths, **kwargs):
        return check_paths(paths, ROW, WIDTH_PX, HEIGHT_PX, **kwargs)

    def test_a_well_formed_path_survives_and_carries_its_provenance(self):
        stored = self._check([_path(erzeugt_am="2026-09-12", flecken_n=3, konfiguration={"rail": "tentfit"})])
        assert len(stored) == 1
        assert stored[0]["verfahren"] == "tintenpfad"
        assert stored[0]["erzeugt_am"] == "2026-09-12"
        assert stored[0]["flecken_n"] == 3
        assert stored[0]["konfiguration"] == {"rail": "tentfit"}
        assert stored[0]["registration_px"] == {"tx": 40.0, "ty": 0.0, "baseline_row": 240.0}

    def test_the_stored_list_comes_back_in_box_order(self):
        second = _path(box_index=1, word="das", registration_px={"tx": 440.0, "ty": 0.0, "baseline_row": 240.0})
        assert [p["box_index"] for p in self._check([second, _path()])] == [0, 1]

    def test_a_box_that_is_not_on_this_row_is_refused(self):
        with pytest.raises(ValueError, match="not a box of this row"):
            self._check([_path(box_index=7)])

    def test_two_paths_for_one_box_are_refused(self):
        with pytest.raises(ValueError, match="two paths"):
            self._check([_path(), _path()])

    def test_a_word_that_contradicts_the_printed_box_is_refused(self):
        with pytest.raises(ValueError, match="the printed box carries"):
            self._check([_path(word="Galopp")])

    def test_a_word_that_contradicts_the_frozen_plan_is_refused(self):
        # The plan is the strip's identity: a layout that somehow disagreed
        # with it must not put a path under a word the strip never held.
        with pytest.raises(ValueError, match="the frozen plan says"):
            self._check([_path()], words=["Galopp", "das"])
        assert self._check([_path()], words=["lesen", "das"])

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"strokes": []}, "non-empty"),
            ({"strokes": [[[0.0, 0.0]]]}, "2..4096 points"),
            ({"strokes": [[[0.0, 0.0, 1.0], [1.0, 1.0, 1.0]]]}, r"\[x, y\] pairs"),
            ({"strokes": [[[0.0, 0.0], [MAX_UNIT + 1, 1.0]]]}, "out of range"),
            ({"verfahren": ""}, "verfahren"),
            ({"erzeugt_am": "gestern"}, "ISO date"),
            ({"xh_px": 0.0}, "not a scale"),
            ({"flecken_n": -1}, "flecken_n"),
        ],
    )
    def test_a_malformed_entry_is_refused_rather_than_repaired(self, overrides: dict, message: str):
        with pytest.raises(ValueError, match=message):
            self._check([_path(**overrides)])

    @pytest.mark.parametrize(
        "registration",
        [
            {"tx": 99_000.0, "ty": 0.0, "baseline_row": 240.0},
            {"tx": 40.0, "ty": 0.0, "baseline_row": 99_000.0},
            {"tx": 40.0, "ty": 0.0},
        ],
    )
    def test_a_registration_that_does_not_lie_on_this_strip_is_refused(self, registration: dict):
        # The one error that would otherwise draw a perfectly well-formed path
        # over the wrong ink — silently, and forever.
        with pytest.raises(ValueError):
            self._check([_path(registration_px=registration)])

    def test_a_word_that_starts_a_little_left_of_the_strip_is_still_accepted(self):
        # A word's own origin may sit left of the ink (the composition starts
        # at the Anstrich), so the bound is slack, not zero.
        assert self._check([_path(registration_px={"tx": -20.0, "ty": 0.0, "baseline_row": 240.0})])

    def test_an_empty_push_is_a_reading_and_not_a_refusal(self):
        # „followed, nothing found" — the same distinction the Fleckenmaske
        # draws between an empty list and NULL.
        assert check_paths([], ROW, WIDTH_PX, HEIGHT_PX) == []


class TestFollowerHandover:
    """The seam between the local follower and what the API stores."""

    def test_the_crop_frame_is_translated_into_the_strips_own_frame(self):
        # The follower registers against the CROP it was handed; the stored
        # frame is the STRIP's. Getting this wrong would draw every path of
        # every word on top of the first one.
        from tools.eigenhand.pfad import _entry

        frame = _frame(1)
        info = {
            "strokes": [[[0.0, 0.0], [1.0, 1.0]]],
            "registration_px": {"tx": 3.0, "ty": -1.0, "baseline_row": 240.0},
            "xh_px": 118.0,
            "meta": {"letter_spans": [], "tintenpfad": {"runs": 2}},
        }
        entry = _entry(info, frame, flecken_n=2, today="2026-09-12")
        assert entry["box_index"] == 1
        assert entry["word"] == "das"
        assert entry["registration_px"] == {"tx": 3.0 + frame["rect_px"][0], "ty": -1.0, "baseline_row": 240.0}
        assert entry["flecken_n"] == 2
        assert entry["erzeugt_am"] == "2026-09-12"
        # And what comes out of the follower has to pass the API's own gate.
        assert check_paths([entry], ROW, WIDTH_PX, HEIGHT_PX, ["lesen", "das"])

    def test_the_declared_configuration_is_one_the_follower_accepts(self):
        # The arms are named in the tool and stored with every path; a renamed
        # weight would otherwise only surface on a real run against real ink.
        from tools.eigenhand.pfad import KONFIGURATION
        from tools.pairlab.tintenpfad import TintenpfadWeights

        weights = TintenpfadWeights(**KONFIGURATION)
        assert (weights.rail, weights.edt_upsample, weights.ink_bridge_xh) == ("tentfit", 4, 1.0)
        assert all(
            getattr(weights, arm) for arm in ("tip_read", "hairpin_tip", "ride_back", "tip_grey_stop", "self_jump")
        )
