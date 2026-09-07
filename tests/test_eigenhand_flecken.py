"""Die Fleckenmaske — what the detector may erase, and what it must never touch.

The printer drops toner specks into the right part of the page; they land
inside a filed strip and inside the writer's verdict box. The mask removes
them as DATA (circles applied on read), so these tests are about the ONE
question that matters for ground truth: does the automatic pass ever propose a
circle over the author's own ink.

The synthetic crops are built against REAL layout geometry (a composed Bogen,
not invented numbers) — the exclusions depend on the ruling, the box edges and
the printed zones, so a made-up rectangle would test something else.

Proves: a lone speck far from the writing is found; an i-dot, a high-set dot,
a comma and a speck fused to a letter are not; printed matter and the label
zone are out of reach; a verdict box with three specks does not read as a
tick while a cross does; the mask paints paper without touching the filed
bytes; and a circle outside its strip is a loud refusal.
"""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from core.eigenhand import bogen, crop, flecken
from core.eigenhand.kartei import empty_kartei
from core.eigenhand.plan import load_plan


PX_PER_MM = 300.0 / 25.4


@pytest.fixture(scope="module")
def row() -> dict:
    """One real layout row — the geometry an ingest run would have cropped."""
    composed = bogen.compose_sheet(
        plan=load_plan(),
        kartei=empty_kartei("mn-suetterlin", "suetterlin"),
        hand="mn-suetterlin",
        style="suetterlin",
        date="2026-09-07",
        rows=1,
        repeat=1,
        strips=["S0001"],
        hints=True,
    )
    return composed["layout"]["rows"][0]


class Crop:
    """A blank strip crop in the row's own geometry, drawn on in millimetres.

    Coordinates are PAGE millimetres, as the layout states them; the class
    converts to the crop's own pixels, which is exactly the shift the detector
    has to get right.
    """

    def __init__(self, row: dict):
        x0, y0, x1, y1 = row["cut_mm"]
        self.origin = (x0, y0)
        self.x0_px, self.y0_px = round(x0 * PX_PER_MM), round(y0 * PX_PER_MM)
        width = round(x1 * PX_PER_MM) - self.x0_px
        height = round(y1 * PX_PER_MM) - self.y0_px
        self.plane = np.ones((height, width), dtype=np.float32)
        self.row = row

    def _px(self, x_mm: float, y_mm: float) -> tuple[float, float]:
        return (x_mm * PX_PER_MM - self.x0_px, y_mm * PX_PER_MM - self.y0_px)

    def bar(self, x_mm: float, y_mm: float, width_mm: float, height_mm: float, level: float = 0.1) -> None:
        cx, cy = self._px(x_mm, y_mm)
        half_w, half_h = width_mm * PX_PER_MM / 2, height_mm * PX_PER_MM / 2
        self.plane[max(0, round(cy - half_h)) : round(cy + half_h), max(0, round(cx - half_w)) : round(cx + half_w)] = (
            level
        )

    def dot(self, x_mm: float, y_mm: float, diameter_mm: float, level: float = 0.1) -> None:
        cx, cy = self._px(x_mm, y_mm)
        radius = diameter_mm * PX_PER_MM / 2
        yy, xx = np.ogrid[: self.plane.shape[0], : self.plane.shape[1]]
        self.plane[(xx - cx) ** 2 + (yy - cy) ** 2 <= radius * radius] = level

    def find(self) -> list[dict]:
        return flecken.find_flecken(
            self.plane,
            px_per_mm=PX_PER_MM,
            detectable=flecken.writing_window(self.plane.shape, self.row, self.x0_px, self.y0_px, PX_PER_MM),
        )


@pytest.fixture
def band(row: dict) -> dict:
    return row["band_mm"]


@pytest.fixture
def letter_x(row: dict) -> float:
    """A millimetre well inside the first word box — where writing belongs."""
    return row["boxes"][0]["x0_mm"] + 4.0


class TestTheDetector:
    def test_a_lone_speck_far_from_the_writing_is_found(self, row: dict, band: dict, letter_x: float):
        sheet = Crop(row)
        sheet.bar(letter_x, (band["waist"] + band["baseline"]) / 2, 0.4, band["baseline"] - band["waist"])
        speck_x = letter_x + 20.0
        speck_y = (band["waist"] + band["baseline"]) / 2
        sheet.dot(speck_x, speck_y, 0.4)
        found = sheet.find()
        assert len(found) == 1, found
        assert found[0]["quelle"] == "auto"
        # Stated in the CROP's millimetres, not the page's.
        assert found[0]["x_mm"] == pytest.approx(speck_x - sheet.origin[0], abs=0.2)
        assert found[0]["y_mm"] == pytest.approx(speck_y - sheet.origin[1], abs=0.2)
        assert found[0]["r_mm"] < flecken.FLECK_MAX_R_MM

    def test_an_i_dot_over_its_stem_is_never_masked(self, row: dict, band: dict, letter_x: float):
        sheet = Crop(row)
        sheet.bar(letter_x, (band["waist"] + band["baseline"]) / 2, 0.4, band["baseline"] - band["waist"])
        sheet.dot(letter_x, band["waist"] - 1.5, 0.35)
        assert sheet.find() == []

    def test_a_dot_set_high_above_its_letter_survives_on_its_position(self, row: dict, band: dict, letter_x: float):
        """Past the clearance, so only the „stands over a letter" rule can save it."""
        sheet = Crop(row)
        sheet.bar(letter_x, (band["waist"] + band["baseline"]) / 2, 0.4, band["baseline"] - band["waist"])
        rise = flecken.SPECK_CLEARANCE_MM + 1.0
        sheet.dot(letter_x, band["waist"] - rise, 0.35)
        assert sheet.find() == []

    def test_a_comma_beside_a_word_is_never_masked(self, row: dict, band: dict, letter_x: float):
        sheet = Crop(row)
        sheet.bar(letter_x, (band["waist"] + band["baseline"]) / 2, 0.4, band["baseline"] - band["waist"])
        sheet.bar(letter_x + 0.9, band["baseline"] + 0.2, 0.25, 0.5)
        assert sheet.find() == []

    def test_a_speck_fused_to_a_letter_is_one_component_with_it(self, row: dict, band: dict, letter_x: float):
        sheet = Crop(row)
        sheet.bar(letter_x, (band["waist"] + band["baseline"]) / 2, 0.4, band["baseline"] - band["waist"])
        sheet.dot(letter_x + 0.2, band["baseline"] - 1.0, 0.4)
        assert sheet.find() == []

    def test_the_printed_zones_are_out_of_reach(self, row: dict, band: dict, letter_x: float):
        """A speck in the strip id's pad or in the clear-text label is left alone.

        Neither zone is the writer's ink, and painting paper over printed
        matter would be a lie about the paper the strip was cut from.
        """
        sheet = Crop(row)
        sheet.dot(letter_x, row["cut_mm"][1] + 2.0, 0.4)
        sheet.dot(letter_x, band["desc_bot"] + 3.0, 0.4)
        assert sheet.find() == []

    def test_a_blot_the_size_of_a_letter_is_not_a_speck(self, row: dict, band: dict, letter_x: float):
        """The author's own ink blot stays: it is evidence of the hand, not of the printer."""
        sheet = Crop(row)
        sheet.dot(letter_x + 20.0, (band["waist"] + band["baseline"]) / 2, 1.5)
        assert sheet.find() == []

    def test_a_blank_crop_yields_nothing(self, row: dict):
        assert Crop(row).find() == []


class TestTheVerdictBox:
    """A tick is a stroke, a speck is a dot — three specks must not file a row."""

    @staticmethod
    def _box(size_mm: float = 3.2) -> np.ndarray:
        side = round(size_mm * PX_PER_MM)
        return np.ones((side, side), dtype=np.float32)

    def test_three_specks_do_not_read_as_a_tick(self):
        patch = self._box()
        radius = round(0.25 * PX_PER_MM / 2)
        for cx, cy in ((8, 9), (20, 24), (30, 12)):
            patch[cy - radius : cy + radius, cx - radius : cx + radius] = 0.1
        reading = flecken.read_mark(patch, PX_PER_MM)
        assert reading.specks == 3
        assert reading.tick is False
        assert reading.fraction == 0.0

    def test_a_cross_reads_as_a_tick(self):
        patch = self._box()
        side = patch.shape[0]
        for step in range(side):
            patch[step, step] = 0.1
            patch[step, side - 1 - step] = 0.1
        # A one-pixel diagonal is thinner than a pen; widen it the way a nib does.
        patch = np.minimum(patch, np.roll(patch, 3, axis=1))
        reading = flecken.read_mark(patch, PX_PER_MM)
        assert reading.tick is True
        assert reading.stroke_mm > flecken.MARK_MIN_STROKE_MM

    def test_an_empty_box_says_nothing(self):
        reading = flecken.read_mark(self._box(), PX_PER_MM)
        assert (reading.tick, reading.specks, reading.stroke_mm) == (False, 0, 0.0)

    def test_a_box_with_no_pixels_at_all_is_not_a_crash(self):
        assert flecken.read_mark(np.zeros((0, 0), dtype=np.float32), PX_PER_MM).tick is False


class TestPaintingItOut:
    def test_the_circle_takes_the_local_paper_level_and_the_rest_stands(self):
        plane = np.full((60, 60), 0.82, dtype=np.float32)
        plane[28:32, 28:32] = 0.05
        plane[0:4, 0:4] = 0.05  # untouched ink elsewhere
        painted = flecken.paint_out(plane, [{"x_mm": 30 / PX_PER_MM, "y_mm": 30 / PX_PER_MM, "r_mm": 0.6}], PX_PER_MM)
        assert painted[28:32, 28:32].min() > 0.7
        assert painted[0:4, 0:4].max() < 0.1

    def test_the_input_plane_is_never_written_to(self):
        plane = np.full((40, 40), 0.9, dtype=np.float32)
        plane[18:22, 18:22] = 0.05
        before = plane.copy()
        flecken.paint_out(plane, [{"x_mm": 20 / PX_PER_MM, "y_mm": 20 / PX_PER_MM, "r_mm": 0.5}], PX_PER_MM)
        assert np.array_equal(plane, before)

    def test_a_colour_strip_stays_colour_and_a_grey_one_grey(self):
        for mode, size in (("L", (120, 40)), ("RGB", (120, 40))):
            image = Image.new(mode, size, color=210 if mode == "L" else (210, 205, 195))
            pixels = image.load()
            for x in range(58, 63):
                for y in range(18, 23):
                    pixels[x, y] = 0 if mode == "L" else (0, 0, 0)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            raw = buffer.getvalue()
            circles = [{"x_mm": 60 / PX_PER_MM, "y_mm": 20 / PX_PER_MM, "r_mm": 0.6}]
            cleaned = crop.without_flecken(raw, circles, PX_PER_MM)
            with Image.open(io.BytesIO(cleaned)) as out:
                assert out.mode == mode
                assert np.asarray(out.convert("L"))[18:23, 58:63].min() > 150
            # The filed bytes are untouched — the view is computed on request.
            with Image.open(io.BytesIO(raw)) as original:
                assert np.asarray(original.convert("L"))[20, 60] == 0

    def test_an_empty_mask_returns_the_bytes_unchanged(self):
        image = Image.new("L", (20, 20), color=200)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        raw = buffer.getvalue()
        assert crop.without_flecken(raw, [], PX_PER_MM) is raw


class TestCheckingAMask:
    def test_a_circle_inside_the_strip_is_accepted_and_rounded(self):
        checked = flecken.check_circles(
            [{"x_mm": 12.3456, "y_mm": 4.0, "r_mm": 0.6, "quelle": "hand"}], width_mm=185.0, height_mm=30.0
        )
        assert checked == [{"x_mm": 12.346, "y_mm": 4.0, "r_mm": 0.6, "quelle": "hand"}]

    @pytest.mark.parametrize(
        "circle",
        [
            {"x_mm": -1.0, "y_mm": 4.0, "r_mm": 0.6},
            {"x_mm": 200.0, "y_mm": 4.0, "r_mm": 0.6},
            {"x_mm": 10.0, "y_mm": 40.0, "r_mm": 0.6},
            {"x_mm": 10.0, "y_mm": 4.0, "r_mm": flecken.FLECK_MAX_R_MM + 1},
            {"x_mm": 10.0, "y_mm": 4.0, "r_mm": 0.6, "quelle": "erfunden"},
            {"x_mm": 10.0, "y_mm": 4.0},
        ],
    )
    def test_anything_outside_the_strip_or_the_brush_is_refused(self, circle: dict):
        with pytest.raises(ValueError):
            flecken.check_circles([circle], width_mm=185.0, height_mm=30.0)

    def test_a_mask_beyond_the_cap_is_refused(self):
        many = [{"x_mm": 1.0, "y_mm": 1.0, "r_mm": 0.3}] * (flecken.FLECKEN_MAX + 1)
        with pytest.raises(ValueError):
            flecken.check_circles(many, width_mm=185.0, height_mm=30.0)


class TestTheKarteiIndex:
    def test_only_fassungen_with_a_mask_appear(self):
        kartei = {
            "strips": {
                "S0001": {
                    "fassungen": [
                        {"id": "F01", "flecken": [{"x_mm": 1.0, "y_mm": 2.0, "r_mm": 0.3, "quelle": "auto"}]},
                        {"id": "F02", "flecken": None},
                        {"id": "F03"},
                    ]
                }
            }
        }
        index = flecken.flecken_index(kartei)
        assert list(index["S0001"]) == ["F01"]
