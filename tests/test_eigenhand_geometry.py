"""Geometry of the Eigenhand Bogen: preset pins, band math, packing invariants."""

from __future__ import annotations

import pytest

from tools.eigenhand import geometry


class TestPresetPins:
    """Pinned against app/src/lib/lineatur.ts PRESETS — the source of truth.

    A mismatch here means one side changed without the other; fix them
    together (the TS file wins).
    """

    def test_kurrent(self):
        p = geometry.PRESETS["kurrent"]
        assert (p.ratio, p.x_height_mm, p.slant_deg, p.show_slant, p.slant_spacing_mm) == (
            (2, 1, 2),
            2.5,
            65.0,
            True,
            10.0,
        )

    def test_suetterlin(self):
        p = geometry.PRESETS["suetterlin"]
        assert (p.ratio, p.x_height_mm, p.slant_deg, p.show_slant, p.slant_spacing_mm) == (
            (1, 1, 1),
            6.0,
            90.0,
            False,
            10.0,
        )

    def test_offenbacher(self):
        p = geometry.PRESETS["offenbacher"]
        assert (p.ratio, p.x_height_mm, p.slant_deg, p.show_slant, p.slant_spacing_mm) == (
            (2, 3, 2),
            5.0,
            77.0,
            True,
            12.0,
        )

    def test_ruling_styles_pin_the_druck_theme(self):
        # lineatur.ts RULING_THEMES[0] (druck): color + width per role.
        assert geometry.ROLE_STYLES["baseline"][:2] == ("#1A1A17", 0.35)
        assert geometry.ROLE_STYLES["waist"][:2] == ("#6B6A63", 0.25)
        assert geometry.ROLE_STYLES["ascender"] == ("#B8B6AE", 0.18, (1.6, 1.6))
        assert geometry.ROLE_STYLES["slant"] == ("#D6D4CB", 0.15, (1.0, 1.6))


class TestBandMath:
    def test_suetterlin_row_is_18mm(self):
        assert geometry.row_height_mm(geometry.PRESETS["suetterlin"]) == 18.0

    def test_suetterlin_default_rows_breathe(self):
        # 34 mm pitch (owner 2026-08-23: more room between the rows, and the
        # gap has to carry two cut lines), footer zone reserved: 7 rows.
        assert geometry.max_rows(geometry.PRESETS["suetterlin"]) == 7

    def test_a_flat_script_spends_its_surplus_on_padding_not_on_rows(self):
        # Owner, 2026-08-23: "for the other scripts there is maybe room for a
        # bit more air above and below the lineature." Kurrent builds a 12.5 mm
        # row where Sütterlin builds 18 — that difference goes into the strip's
        # padding until CUT_MIN_HEIGHT_MM is reached, not into a taller stack.
        kurrent, suetterlin = geometry.PRESETS["kurrent"], geometry.PRESETS["suetterlin"]
        assert geometry.row_height_mm(kurrent) < geometry.row_height_mm(suetterlin)
        assert geometry.cut_size_mm(kurrent)[1] >= geometry.CUT_MIN_HEIGHT_MM
        assert geometry._cut_surplus_mm(geometry.row_height_mm(kurrent)) > 0
        assert geometry._cut_surplus_mm(geometry.row_height_mm(suetterlin)) == 0

    def test_row_band_ordering(self):
        band = geometry.row_band(geometry.PRESETS["offenbacher"], 20.0)
        assert band.asc_top == 20.0
        assert band.asc_top < band.waist < band.baseline < band.desc_bot
        assert round(band.baseline - band.waist, 6) == 5.0  # x-height


class TestPacking:
    def test_rows_respect_usable_width(self):
        preset = geometry.PRESETS["suetterlin"]
        words = ["Galoppieren", "das", "unter", "Schwindsucht", "zu", "regieren", "im", "haben"] * 3
        rows = geometry.pack_words_into_rows(list(words), preset)
        usable = geometry.usable_row_width_mm()
        for row in rows:
            width = sum(geometry.estimate_word_width_mm(w, preset.x_height_mm) for w in row)
            width += geometry.BOX_GAP_MM * (len(row) - 1)
            assert width <= usable + 1e-9

    def test_packing_keeps_the_reserve_free(self):
        # The first plan packed rows to 180.0 of 180 mm. The width model is an
        # estimate until real ink calibrates it, so the packing now stops
        # PACK_SLACK_MM short (owner, 2026-08-23: "there has to be buffer").
        preset = geometry.PRESETS["suetterlin"]
        words = ["Galoppieren", "das", "unter", "Schwindsucht", "zu", "regieren", "im", "haben"] * 3
        budget = geometry.usable_row_width_mm() - geometry.PACK_SLACK_MM
        for row in geometry.pack_words_into_rows(list(words), preset):
            width = sum(geometry.estimate_word_width_mm(w, preset.x_height_mm) for w in row)
            width += geometry.BOX_GAP_MM * (len(row) - 1)
            assert width <= budget + 1e-9 or len(row) == 1  # a lone over-wide word gets its own row

    def test_every_box_is_wider_than_its_estimate(self):
        # The reserve is handed back to the BOXES, not left at the line end:
        # a word must not be ruined because the room ran out mid-word.
        preset = geometry.PRESETS["suetterlin"]
        # A row as the packing hands it over — one that fits with the reserve.
        words = geometry.pack_words_into_rows(["Galoppieren", "das", "Schwindsucht"], preset)[0]
        boxes = geometry.boxes_for_row(words, preset)
        for word, (x0, x1) in zip(words, boxes, strict=True):
            assert x1 - x0 > geometry.estimate_word_width_mm(word, preset.x_height_mm)
        assert boxes[-1][1] - boxes[0][0] == pytest.approx(geometry.usable_row_width_mm())

    def test_packing_preserves_multiset(self):
        words = ["lesen", "das", "denen", "lesen"]
        rows = geometry.pack_words_into_rows(list(words), geometry.PRESETS["suetterlin"])
        assert sorted(w for row in rows for w in row) == sorted(words)

    def test_boxes_do_not_overlap_and_stay_in_margins(self):
        preset = geometry.PRESETS["suetterlin"]
        boxes = geometry.boxes_for_row(["lesen", "das", "dann"], preset)
        previous_end = 15.0 - 1e-9
        for x0, x1 in boxes:
            assert x0 >= previous_end
            assert x1 > x0
            assert x1 <= geometry.A4_WIDTH_MM - 15.0 + 1e-9
            previous_end = x1


class TestClip:
    def test_inside_segment_unchanged(self):
        assert geometry.clip_to_rect(1, 1, 2, 2, 0, 0, 3, 3) == (1, 1, 2, 2)

    def test_outside_segment_is_none(self):
        assert geometry.clip_to_rect(-2, -2, -1, -1, 0, 0, 3, 3) is None

    def test_crossing_segment_is_clipped_to_the_rect(self):
        clipped = geometry.clip_to_rect(-1, 1, 4, 1, 0, 0, 3, 3)
        assert clipped == (0, 1, 3, 1)


class TestCutBand:
    """Every strip is cut to the same rectangle — that is the whole point."""

    @staticmethod
    def _sheet_cuts(style: str = "suetterlin") -> list[tuple[float, float, float, float]]:
        preset = geometry.PRESETS[style]
        pitch = geometry.row_pitch_mm(preset)
        rows = geometry.max_rows(preset)
        return [
            geometry.cut_box(geometry.row_band(preset, geometry.TOP_MARGIN_MM + index * pitch)) for index in range(rows)
        ]

    @pytest.mark.parametrize("style", ["kurrent", "suetterlin", "offenbacher"])
    def test_every_strip_of_a_sheet_has_the_same_size(self, style):
        sizes = {(round(c[2] - c[0], 6), round(c[3] - c[1], 6)) for c in self._sheet_cuts(style)}
        assert len(sizes) == 1
        assert sizes.pop() == tuple(round(v, 6) for v in geometry.cut_size_mm(geometry.PRESETS[style]))

    def test_the_writing_area_and_the_labels_are_inside_the_cut(self):
        preset = geometry.PRESETS["suetterlin"]
        band = geometry.row_band(preset, 15.0)
        x0, y0, x1, y1 = geometry.cut_box(band)
        boxes = geometry.boxes_for_row(["Handschrift", "lesen"], preset, 15.0)
        assert x0 < min(b[0] for b in boxes) and max(b[1] for b in boxes) < x1
        assert y0 < band.asc_top and band.desc_bot + geometry.LABEL_ZONE_MM <= y1

    def test_both_captions_sit_inside_the_strip_with_room_to_spare(self):
        # Owner, 2026-08-23: push the id and the word away from the lineature
        # "a bit, but without making the strips taller". The pads were shifted
        # against each other, so this checks BOTH: the captions clear the
        # writing band, and they still fit between the cut lines.
        from tools.eigenhand import sheet

        for style in ("kurrent", "suetterlin", "offenbacher"):
            band = geometry.row_band(geometry.PRESETS[style], geometry.TOP_MARGIN_MM)
            _x0, cut_top, _x1, cut_bottom = geometry.cut_box(band)
            id_top = band.asc_top - sheet.ROW_ID_GAP_MM - sheet.ROW_ID_SIZE_MM
            label_bottom = band.desc_bot + sheet.LABEL_GAP_MM + 0.25 * sheet.LABEL_SIZE_MM
            assert cut_top < id_top < band.asc_top, f"{style}: the strip id leaves the Schnittband"
            assert band.desc_bot < label_bottom < cut_bottom, f"{style}: the word label leaves the Schnittband"

    def test_the_verdict_box_stays_off_the_strip(self):
        # The pen tick is bookkeeping, not training data.
        band = geometry.row_band(geometry.PRESETS["suetterlin"], 15.0)
        assert geometry.mark_box(band)[0] > geometry.cut_box(band)[2]

    def test_the_page_is_marked_the_same_at_both_ends(self):
        # Owner, 2026-08-23: below the last strip a vertical tick follows the
        # horizontal one — above the first strip it has to read the same.
        cuts = self._sheet_cuts()
        ticks = geometry.page_cut_ticks(cuts)
        above = [t for t in ticks if t[3] < cuts[0][1]]
        below = [t for t in ticks if t[1] > cuts[-1][3]]
        assert len(above) == 2 and len(below) == 2  # one per vertical cut line
        assert {round(t[0], 3) for t in above} == {geometry.CUT_X0_MM, geometry.CUT_X1_MM}

    def test_strips_never_touch_and_leave_room_for_the_blade(self):
        cuts = self._sheet_cuts()
        gaps = {round(lower[1] - upper[3], 6) for upper, lower in zip(cuts, cuts[1:], strict=False)}
        assert gaps and min(gaps) >= 4.0

    def test_marks_sit_in_the_margins_never_on_a_strip(self):
        cuts = self._sheet_cuts()
        ticks = [t for cut in cuts for t in geometry.cut_ticks(cut)] + geometry.page_cut_ticks(cuts)
        for tx0, ty0, tx1, ty1 in ticks:
            for cx0, cy0, cx1, cy1 in cuts:
                inside_x = cx0 < tx0 < cx1 or cx0 < tx1 < cx1
                inside_y = cy0 < ty0 < cy1 or cy0 < ty1 < cy1
                assert not (inside_x and inside_y), "a cut mark would print on the strip"

    @pytest.mark.parametrize("style", ["kurrent", "suetterlin", "offenbacher"])
    def test_no_cut_mark_comes_near_a_fiducial(self, style):
        # A hairline blurring into a Passmarke would drag its centroid — and
        # with it every millimetre the importer computes.
        cuts = self._sheet_cuts(style)
        ticks = [t for cut in cuts for t in geometry.cut_ticks(cut)] + geometry.page_cut_ticks(cuts)
        keep_out = geometry.FIDUCIAL_SIZE_MM / 2 + 2.0
        for tx0, ty0, tx1, ty1 in ticks:
            for cx, cy in geometry.FIDUCIAL_CENTERS.values():
                clear_x = max(tx0, tx1) < cx - keep_out or min(tx0, tx1) > cx + keep_out
                clear_y = max(ty0, ty1) < cy - keep_out or min(ty0, ty1) > cy + keep_out
                assert clear_x or clear_y, f"cut mark {tx0, ty0, tx1, ty1} crowds the fiducial at {cx, cy}"


class TestMarkBox:
    """The per-row verdict box lives in the right margin, clear of everything."""

    def test_right_of_the_writing_area_and_on_the_page(self):
        band = geometry.row_band(geometry.PRESETS["suetterlin"], 15.0)
        x0, _y0, x1, _y1 = geometry.mark_box(band)
        writing_right = 15.0 + geometry.usable_row_width_mm()
        assert x0 >= writing_right  # never steals writing width
        assert x1 <= geometry.A4_WIDTH_MM - 3.0  # stays printable

    def test_box_is_square_and_sized_as_declared(self):
        band = geometry.row_band(geometry.PRESETS["suetterlin"], 15.0)
        x0, y0, x1, y1 = geometry.mark_box(band)
        assert x1 - x0 == pytest.approx(geometry.MARK_BOX_MM)
        assert y1 - y0 == pytest.approx(geometry.MARK_BOX_MM)

    def test_box_stays_inside_the_row_block_for_every_preset(self):
        for preset in geometry.PRESETS.values():
            band = geometry.row_band(preset, 15.0)
            _x0, y0, _x1, y1 = geometry.mark_box(band)
            assert y0 >= band.asc_top - 1e-9
            assert y1 <= band.desc_bot + 1e-9

    def test_column_clears_the_corner_fiducials_horizontally_only(self):
        # The fiducials sit at the page corners; the mark column shares their
        # x band on purpose (printable there) but never their y band.
        band = geometry.row_band(geometry.PRESETS["suetterlin"], 15.0)
        top_fiducial_bottom = geometry.FIDUCIAL_CENTERS["tr"][1] + geometry.FIDUCIAL_SIZE_MM / 2
        assert geometry.mark_box(band)[1] > top_fiducial_bottom
