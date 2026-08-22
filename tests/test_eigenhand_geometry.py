"""Geometry of the Eigenhand Bogen: preset pins, band math, packing invariants."""

from __future__ import annotations

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
        # 27 mm pitch, footer zone reserved: 9 rows, not the 10 that would cram.
        assert geometry.max_rows(geometry.PRESETS["suetterlin"]) == 9

    def test_kurrent_fits_more_rows(self):
        assert geometry.max_rows(geometry.PRESETS["kurrent"]) > 9

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
