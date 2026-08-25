"""Cutting one word out of a stored strip — the arithmetic, without a server.

A word crop is derived, never stored: the strip row remembers where its crop
started in millimetres, the sheet's layout says where each word box sits, and
the pixel width supplies the scale. These tests pin that chain against REAL
layout geometry (a composed Bogen, not invented numbers), because the whole
point of the derivation is that it agrees with the paper.

Proves: the scale comes out of the Schnittband; a word box lands where the
layout put it; the padding is clamped to the strip instead of running off it;
the crop keeps the full strip height; a word that is not in the row is a loud
refusal rather than a silently wrong rectangle.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image

from core.eigenhand import bogen, crop
from core.eigenhand.kartei import empty_kartei
from core.eigenhand.plan import load_plan


DPI = 300.0
PX_PER_MM = DPI / 25.4


@pytest.fixture(scope="module")
def row() -> dict:
    """One real layout row — the geometry an ingest run would have cropped."""
    composed = bogen.compose_sheet(
        plan=load_plan(),
        kartei=empty_kartei("mn-suetterlin", "suetterlin"),
        hand="mn-suetterlin",
        style="suetterlin",
        date="2026-08-24",
        rows=1,
        repeat=1,
        strips=["S0001"],
        hints=True,
    )
    return composed["layout"]["rows"][0]


@pytest.fixture(scope="module")
def stored(row: dict) -> dict:
    """What the strip row stores: origin in mm, size in px, at 300 DPI."""
    x0, y0, x1, y1 = row["cut_mm"]
    return {
        "crop_origin_mm": [round(x0, 3), round(y0, 3)],
        "width_px": int(round(x1 * PX_PER_MM)) - int(round(x0 * PX_PER_MM)),
        "height_px": int(round(y1 * PX_PER_MM)) - int(round(y0 * PX_PER_MM)),
        "cut_mm": row["cut_mm"],
    }


class TestScale:
    def test_the_scale_is_the_strips_own_width_over_the_schnittband(self, stored: dict):
        scale = crop.px_per_mm(stored["width_px"], stored["cut_mm"])
        assert scale == pytest.approx(PX_PER_MM, rel=1e-3)

    @pytest.mark.parametrize(
        ("width_px", "cut_mm"),
        [(0, [10.0, 0.0, 200.0, 20.0]), (2000, [200.0, 0.0, 10.0, 20.0]), (2000, [10.0, 0.0, 10.0, 20.0])],
    )
    def test_a_strip_without_a_usable_width_refuses(self, width_px: int, cut_mm: list[float]):
        with pytest.raises(SystemExit):
            crop.px_per_mm(width_px, cut_mm)


class TestWordBox:
    def test_a_word_lands_where_the_layout_put_it(self, row: dict, stored: dict):
        box = row["boxes"][1]
        left, top, right, bottom = crop.word_box_px(box, **stored, pad_mm=0.0)
        assert left == pytest.approx((box["x0_mm"] - stored["crop_origin_mm"][0]) * PX_PER_MM, abs=1.0)
        assert right == pytest.approx((box["x1_mm"] - stored["crop_origin_mm"][0]) * PX_PER_MM, abs=1.0)
        # Vertically the whole strip: an ascender or a descender is exactly
        # what one opens a word crop to look at.
        assert (top, bottom) == (0, stored["height_px"])

    def test_the_padding_widens_the_cut_on_both_sides(self, row: dict, stored: dict):
        box = row["boxes"][1]
        tight = crop.word_box_px(box, **stored, pad_mm=0.0)
        padded = crop.word_box_px(box, **stored, pad_mm=2.0)
        assert padded[0] < tight[0] and padded[2] > tight[2]
        assert (tight[0] - padded[0]) == pytest.approx(2.0 * PX_PER_MM, abs=1.5)

    def test_the_first_word_keeps_its_padding_inside_the_strip(self, row: dict, stored: dict):
        left, _, right, _ = crop.word_box_px(row["boxes"][0], **stored, pad_mm=50.0)
        assert left == 0 and right <= stored["width_px"]
        assert right > left

    def test_a_box_beyond_the_strip_still_yields_a_usable_rectangle(self, stored: dict):
        far = {"word": "x", "x0_mm": 900.0, "x1_mm": 950.0}
        left, _, right, _ = crop.word_box_px(far, **stored)
        assert 0 <= left < right <= stored["width_px"]


class TestFindBox:
    def test_a_word_resolves_to_its_box(self, row: dict):
        word = row["boxes"][1]["word"]
        assert crop.find_box(row, word, None) == row["boxes"][1]

    def test_an_index_resolves_positionally(self, row: dict):
        assert crop.find_box(row, None, 0) == row["boxes"][0]

    def test_a_word_the_row_does_not_carry_is_a_loud_refusal(self, row: dict):
        with pytest.raises(SystemExit, match="is not in this row"):
            crop.find_box(row, "nichtdrin", None)

    def test_an_index_past_the_row_is_a_loud_refusal(self, row: dict):
        with pytest.raises(SystemExit, match="there is no box"):
            crop.find_box(row, None, 99)

    def test_naming_neither_is_a_loud_refusal(self, row: dict):
        with pytest.raises(SystemExit, match="name a word"):
            crop.find_box(row, None, None)


class TestCutPng:
    def test_the_cut_has_the_requested_size_and_keeps_the_grayscale(self):
        source = Image.new("L", (400, 60), color=200)
        buffer = io.BytesIO()
        source.save(buffer, format="PNG")

        cut = crop.cut_png(buffer.getvalue(), (100, 0, 220, 60))
        with Image.open(io.BytesIO(cut)) as image:
            assert image.size == (120, 60)
            # Not binarised, not re-coloured — the two-channel doctrine says the
            # stored grayscale IS the darkness channel.
            assert image.mode == "L"
            assert image.getpixel((0, 0)) == 200
