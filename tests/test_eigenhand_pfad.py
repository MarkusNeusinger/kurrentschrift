"""The Streifen-Pfad's pure half: where a word box sits, and what a path may be.

Two things are tested here because both are arithmetic the server and the local
follower must agree on to the pixel: the frame a word box spans inside a stored
strip (`frame_for_box`), and the refusals that keep a pushed path from being
stored against the wrong ink (`check_paths`).
"""

from __future__ import annotations

import pytest

from core.eigenhand.pfad import MAX_UNIT, check_paths, frame_for_box, frames_of_row, nominal_xh_px


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
            # A length check let this one through and the workbench printed it
            # as provenance (Copilot review, PR #598).
            ({"erzeugt_am": "2026-99-99"}, "ISO date"),
            ({"xh_px": 0.0}, "not a scale"),
            ({"flecken_n": -1}, "flecken_n"),
        ],
    )
    def test_a_malformed_entry_is_refused_rather_than_repaired(self, overrides: dict, message: str):
        with pytest.raises(ValueError, match=message):
            self._check([_path(**overrides)])

    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"strokes": [[[0.0, 0.0], [float("nan"), 1.0]]]}, "finite"),
            ({"strokes": [[[0.0, 0.0], [float("inf"), 1.0]]]}, "finite"),
            ({"xh_px": float("nan")}, "not a scale"),
            ({"registration_px": {"tx": float("nan"), "ty": 0.0, "baseline_row": 240.0}}, "finite"),
        ],
    )
    def test_a_non_finite_number_is_refused_before_any_range_check(self, overrides: dict, message: str):
        # Every comparison against NaN is False, so a range check alone lets it
        # through — and it reaches the overlay as a NaN SVG coordinate, which
        # draws nothing and explains nothing (Copilot review, PR #598).
        with pytest.raises(ValueError, match=message):
            self._check([_path(**overrides)])

    @pytest.mark.parametrize(
        "registration",
        [
            {"tx": 99_000.0, "ty": 0.0, "baseline_row": 240.0},
            {"tx": 40.0, "ty": 0.0, "baseline_row": 99_000.0},
            {"tx": 40.0, "ty": 0.0},
            # Well inside a "fraction of the image" bound and still off the
            # strip: the allowance is x-heights, not image widths (Copilot
            # review, PR #598). xh here is 120 px, so the bound is ±240.
            {"tx": WIDTH_PX + 600.0, "ty": 0.0, "baseline_row": 240.0},
            {"tx": 40.0, "ty": 0.0, "baseline_row": HEIGHT_PX + 300.0},
        ],
    )
    def test_a_registration_that_does_not_lie_on_this_strip_is_refused(self, registration: dict):
        # The one error that would otherwise draw a perfectly well-formed path
        # over the wrong ink — silently, and forever.
        with pytest.raises(ValueError):
            self._check([_path(registration_px=registration)])

    def test_a_word_that_starts_a_little_left_of_the_strip_is_still_accepted(self):
        # A word's own origin may sit left of the ink (the composition starts
        # at the Anstrich) and a descender reaches past the cut, so the bound is
        # two x-heights of slack rather than zero.
        assert self._check([_path(registration_px={"tx": -20.0, "ty": 0.0, "baseline_row": 240.0})])
        assert self._check([_path(registration_px={"tx": float(WIDTH_PX) + 100.0, "ty": 0.0, "baseline_row": 240.0})])

    @pytest.mark.parametrize("xh", [1300.0, 240.1, 59.9, 0.5])
    def test_an_x_height_the_printed_ruling_could_not_have_is_refused(self, xh: float):
        # The row's printed band is 12 mm at 10 px/mm, so 120 px is the nominal
        # x-height and half to double it is every hand this Bogen could hold.
        with pytest.raises(ValueError, match="not a scale"):
            self._check([_path(xh_px=xh)])
        assert self._check([_path(xh_px=60.0)]) and self._check([_path(xh_px=240.0)])

    def test_an_inflated_x_height_cannot_buy_slack_for_an_off_strip_frame(self):
        # The registration slack is measured in the path's OWN x-height, so an
        # unbounded `xh_px` disabled the very check it is measured with: at a
        # declared 1300 px, `tx = 2500` on this strip passed (review of PR
        # #598). Now the x-height is refused before it can widen anything.
        off_strip = {"tx": WIDTH_PX + 600.0, "ty": 0.0, "baseline_row": 240.0}
        with pytest.raises(ValueError, match="not a scale"):
            self._check([_path(xh_px=1300.0, registration_px=off_strip)])
        # …and the honest x-height still refuses the same frame, as before.
        with pytest.raises(ValueError, match="outside the strip"):
            self._check([_path(registration_px=off_strip)])

    def test_without_a_printed_ruling_the_strip_itself_bounds_the_x_height(self):
        # An old Bogen has no band to compare against; the strip's own height
        # is then the only witness left, and it is still a bound.
        row = {**ROW, "band_mm": {}}
        assert nominal_xh_px(row, WIDTH_PX) is None
        assert nominal_xh_px(ROW, WIDTH_PX) == pytest.approx(120.0)
        assert check_paths([_path(xh_px=120.0)], row, WIDTH_PX, HEIGHT_PX)
        with pytest.raises(ValueError, match="not a scale"):
            check_paths([_path(xh_px=HEIGHT_PX * 3.0)], row, WIDTH_PX, HEIGHT_PX)

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

    def test_a_box_the_row_does_not_have_stops_the_run_before_it_can_erase(self):
        # `--box` narrows the follow, and the write is a FULL replacement — so
        # a typo would follow nothing, push an empty list and wipe the
        # Fassung's stored paths while reporting success (Copilot review,
        # PR #598). Refused where the row's real boxes are known.
        from tools.eigenhand.pfad import follow_row

        row = {"strip": "S0001", "fassung": "F01", "boxes": [{"index": 0, "word": "lesen"}]}
        with pytest.raises(SystemExit, match="no box 7"):
            follow_row("https://example.invalid", "token", "mn-suetterlin", row, {}, [7])

    def test_a_narrowed_run_keeps_the_paths_of_the_boxes_it_did_not_follow(self):
        # The other half of the same finding: re-following ONE word must not
        # drop the rest of the row.
        from tools.eigenhand import pfad as tool

        stored = [{"box_index": 0, "word": "lesen"}, {"box_index": 1, "word": "das"}]
        fresh = [{"box_index": 1, "word": "das", "verfahren": "tintenpfad"}]
        merged = tool._merged("https://example.invalid", "token", "u", fresh, _get=lambda *_: {"pfade": stored})
        assert [entry["box_index"] for entry in merged] == [0, 1]
        assert merged[1] is fresh[0]  # the followed box is the NEW one, not the stored copy

    def test_the_dry_run_files_the_body_the_apply_path_would_send(self, tmp_path, monkeypatch):
        # The dry run is the review surface `--apply` is decided on, so it has
        # to file the MERGED list — filing only the followed boxes made a
        # narrowed run look like a whole-row replacement (review of PR #598).
        import json

        from tools.eigenhand import pfad as tool

        stored = [{"box_index": 0, "word": "lesen"}, {"box_index": 1, "word": "das"}]
        fresh = [{"box_index": 1, "word": "das", "verfahren": "tintenpfad"}]
        merged = tool._merged
        monkeypatch.setattr(tool, "api_base", lambda _api: "https://example.invalid")
        monkeypatch.setattr(tool, "admin_token", lambda _token: "token")
        monkeypatch.setattr(tool, "style_of_hand", lambda _hand: "suetterlin")
        monkeypatch.setattr(tool, "_fixture_prior", lambda _style: {})
        monkeypatch.setattr(
            tool, "_strip_rows", lambda *_a: [{"strip": "S0001", "fassung": "F01", "sheet": "B0001", "row_index": 0}]
        )
        monkeypatch.setattr(tool, "follow_row", lambda *_a: fresh)
        monkeypatch.setattr(tool, "_merged", lambda *args: merged(*args, _get=lambda *_a: {"pfade": stored}))
        monkeypatch.setattr(tool, "request_json", lambda *_a, **_k: pytest.fail("a dry run must not write"))

        out = tmp_path / "pfade.json"
        assert tool.main(["--hand", "mn-suetterlin", "--strip", "S0001", "--box", "1", "--out", str(out)]) == 0
        body = json.loads(out.read_text())
        assert [entry["box_index"] for entry in body["pfade"]] == [0, 1]

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
