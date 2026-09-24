"""The own-hand follower's three input stages — the pure arithmetic, on synthetic ink.

Four things are pinned here. Where the printed labels sit on a written strip,
read off the same page primitives the PDF is drawn from, and that clearing them
after binarisation removes every label pixel while leaving the handwriting bit
for bit (stage 1, `TestLabelZones`). That the plate-scale resampling is a no-op
inside the plate's range and that a Bahn followed on a resampled crop maps back
onto the strip exactly (stage 2, `TestPlateScale`). That the anisotropic seed
registration reads the baseline and the waist a hand actually wrote on, keeps
x and y apart, and falls back to the identity instead of guessing
(`TestSeedRegistration`). And that the composed seed is stretched in x only,
without touching a bench case (`TestComposedScale`).

No fixture root, no network, no follower: everything runs on arrays built here.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from core.eigenhand import bogen
from core.eigenhand.follower_input import (
    PLATE_MODE_CALIBRATION,
    PLATE_XH_PX,
    SEED_SCALE_BOUNDS,
    CropToStrip,
    ModeCalibration,
    ink_of,
    label_zones_px,
    mode_calibration,
    plate_factor,
    register_seed,
    register_seed_width,
    resample_to_plate,
    scale_composed_x,
    scale_index,
    scale_zones,
    skeleton_modes,
    zones_in_crop,
)
from core.eigenhand.kartei import empty_kartei
from core.eigenhand.pfad import XH_NOMINAL_TOLERANCE
from core.eigenhand.plan import load_plan


PX_PER_MM = 10.0


@pytest.fixture(scope="module")
def sheet() -> dict:
    """One real composed Bogen (layout + its first row) — the geometry a written strip was cut from."""
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
    layout = composed["layout"]
    row = layout["rows"][0]
    x0, y0, x1, y1 = row["cut_mm"]
    return {
        "layout": layout,
        "row": row,
        "origin": [x0, y0],
        "width_px": int(round((x1 - x0) * PX_PER_MM)),
        "height_px": int(round((y1 - y0) * PX_PER_MM)),
    }


def _row_px(sheet: dict, mm: float) -> int:
    return int(round((mm - sheet["origin"][1]) * PX_PER_MM))


def _inside(shape: tuple[int, int], zones: list) -> np.ndarray:
    out = np.zeros(shape, dtype=bool)
    for x0, y0, x1, y1 in zones:
        out[max(0, y0) : max(0, y1), max(0, x0) : max(0, x1)] = True
    return out


def _paint(plane: np.ndarray, y0: int, y1: int, x0: int, x1: int, grey: float = 0.1) -> None:
    plane[y0:y1, x0:x1] = grey


def _handwriting(sheet: dict) -> np.ndarray:
    """A paper plane with one written word: a garland between waist and baseline, 3 px thick."""
    plane = np.ones((sheet["height_px"], sheet["width_px"]))
    band = sheet["row"]["band_mm"]
    waist, baseline = _row_px(sheet, band["waist"]), _row_px(sheet, band["baseline"])
    left = int(round((sheet["row"]["boxes"][0]["x0_mm"] - sheet["origin"][0]) * PX_PER_MM)) + 40
    for k in range(8):
        x = left + 40 * k
        _paint(plane, waist, baseline, x, x + 3)  # a downstroke
        _paint(plane, baseline - 3, baseline, x, x + 43)  # the garland's foot to the next one
    return plane


def _with_labels(sheet: dict, zones: list, plane: np.ndarray) -> np.ndarray:
    """The same plane with printed text inside every zone — grey glyph-like bars, as the printer leaves them."""
    out = plane.copy()
    for x0, y0, x1, y1 in zones:
        for x in range(x0 + 6, x1 - 6, 9):
            _paint(out, y0 + 7, y1 - 7, x, x + 3, grey=0.35)
        _paint(out, (y0 + y1) // 2, (y0 + y1) // 2 + 2, x0 + 6, x1 - 6, grey=0.35)
    return out


class TestLabelZones:
    """Stage 1 — the printed labels, cleared after binarisation and nowhere else."""

    def test_every_printed_text_of_the_strip_is_found_and_nothing_else(self, sheet: dict):
        zones = label_zones_px(sheet["layout"], sheet["row"], sheet["origin"], sheet["width_px"], sheet["height_px"])
        # The strip id, the provenance line beside it, one label per box — and
        # not the page header or the „ok?" caption, which lie outside the cut.
        assert len(zones) == 2 + len(sheet["row"]["boxes"])
        band = sheet["row"]["band_mm"]
        top, bottom = _row_px(sheet, band["asc_top"]), _row_px(sheet, band["desc_bot"])
        for x0, y0, x1, y1 in zones:
            assert 0 <= x0 < x1 <= sheet["width_px"] and 0 <= y0 < y1 <= sheet["height_px"]
            # None of them reaches into the ruled band the hand writes in.
            assert y1 <= top or y0 >= bottom

    def test_a_row_without_a_schnittband_has_no_zones_rather_than_a_refusal(self, sheet: dict):
        row = {**sheet["row"], "cut_mm": []}
        assert label_zones_px(sheet["layout"], row, sheet["origin"], sheet["width_px"], sheet["height_px"]) == []

    def test_clearing_the_labels_removes_every_label_pixel_and_keeps_the_hand_bit_for_bit(self, sheet: dict):
        zones = label_zones_px(sheet["layout"], sheet["row"], sheet["origin"], sheet["width_px"], sheet["height_px"])
        hand = _handwriting(sheet)
        printed = _with_labels(sheet, zones, hand)
        inside = _inside(printed.shape, zones)

        standard, _skel, _width = ink_of(printed)
        cleared, skel, _width = ink_of(printed, zones)
        hand_only, hand_skel, _width = ink_of(hand)

        # The bug this stage fixes: the standard mask reads the labels as ink.
        assert (standard & inside).sum() > 500
        assert not (cleared & inside).any() and not (skel & inside).any()
        # And the handwriting is exactly what it is without any print beside it.
        assert np.array_equal(cleared, hand_only)
        assert np.array_equal(skel, hand_skel)

    def test_no_zones_is_the_standard_mask_bit_for_bit(self, sheet: dict):
        from core.extract import binarize_adaptive, skeleton_and_width
        from core.word_metric import despeckle

        plane = _with_labels(sheet, [(100, 10, 200, 40)], _handwriting(sheet))
        mask, skel, width = ink_of(plane)
        standard = despeckle(binarize_adaptive(np.ascontiguousarray(plane, dtype=np.float64)))
        standard_skel, standard_width = skeleton_and_width(standard)
        assert np.array_equal(mask, standard) and np.array_equal(skel, standard_skel)
        assert np.array_equal(width, standard_width) and width.dtype == standard_width.dtype

    def test_a_label_stroke_poking_out_of_its_zone_goes_whole(self):
        # A descender of the printed text crossing the zone's edge: more than
        # half of it inside, so the part outside must not survive as a stub
        # the skeleton would keep.
        plane = np.ones((120, 200))
        _paint(plane, 30, 90, 50, 54, grey=0.3)  # 60 px tall, zone covers rows 20..70 → 40 of 60 inside
        mask, _skel, _width = ink_of(plane, [(40, 20, 80, 70)])
        assert not mask.any()

    def test_zones_move_into_a_crop_by_its_own_origin(self):
        assert zones_in_crop([(110, 5, 150, 40)], [100, 0, 400, 300]) == [(10, 5, 50, 40)]


class TestPlateScale:
    """Stage 2 — the plate's px per x-height, and the exact way back to the strip."""

    @pytest.mark.parametrize("xh", [28.0, PLATE_XH_PX, 33.0])
    def test_inside_the_plates_range_nothing_is_resampled(self, xh: float):
        assert plate_factor(xh) is None
        assert resample_to_plate(np.ones((40, 60)), xh) is None

    def test_outside_it_the_crop_comes_to_the_plates_scale(self):
        assert plate_factor(70.86) == pytest.approx(PLATE_XH_PX / 70.86)
        assert plate_factor(20.0) == pytest.approx(PLATE_XH_PX / 20.0)
        with pytest.raises(ValueError):
            plate_factor(0.0)

    def test_the_resampled_crop_carries_its_own_exact_factors(self):
        crop = np.ones((342, 557))
        crop[194:198, 50:500] = 0.1  # a baseline stroke at rows 194..197
        small, fx, fy = resample_to_plate(crop, 70.86)
        factor = PLATE_XH_PX / 70.86
        assert small.shape == (round(342 * factor), round(557 * factor))
        assert (fx, fy) == (small.shape[1] / 557, small.shape[0] / 342)
        assert 0.0 <= small.min() and small.max() <= 1.0
        # The stroke lands where the pixel-centre convention puts it.
        dark_rows = np.nonzero(small[:, 100] < 0.5)[0]
        assert abs(dark_rows.mean() - scale_index(195.5, fy)) < 1.0

    def test_zones_scale_as_edges_rounded_outward(self):
        assert scale_zones([(10, 11, 21, 21)], 0.5, 0.5) == [(5, 5, 11, 11)]

    def test_the_mapping_to_the_strip_and_back_is_the_identity(self):
        mapping = CropToStrip(1026, 3, 0.4371633752244165, 0.43859649122807015)
        points = np.array([[0.0, 0.0], [12.25, 80.5], [243.0, 149.0], [-3.0, 151.75]])
        assert np.allclose(mapping.to_crop(mapping.to_strip(points)), points, atol=1e-12)
        strip = np.array([[1026.0, 0.0], [1400.5, 194.0], [1582.0, 341.0]])
        assert np.allclose(mapping.to_strip(mapping.to_crop(strip)), strip, atol=1e-12)

    def test_without_resampling_the_mapping_is_the_plain_offset(self):
        mapping = CropToStrip(1026, 0)
        assert not mapping.resampled
        points = np.array([[0.1, 0.2], [3.7, 190.0]])
        assert np.array_equal(mapping.to_strip(points), points + np.array([1026.0, 0.0]))

    def test_the_stored_frame_puts_the_bahn_on_exactly_the_strip_pixels_it_was_followed_at(self):
        # The stored contract is ONE x-height for both axes; the two resampling
        # factors differ in the fourth digit. Mapped back through the stored
        # row, the Bahn has to land where the crop's own mapping puts it.
        mapping = CropToStrip(1026, 0, 0.4371633752244165, 0.43859649122807015)
        strokes = [[[0.0, 0.0], [0.5, 1.0], [1.25, 0.4]], [[2.0, -0.6], [2.1, 1.9]]]
        registration = {"tx": -4.0, "ty": -1.5, "baseline_row": 85}
        xh = 31.0

        def crop_px(points, reg, xh_px):
            pts = np.asarray(points, dtype=float)
            return np.column_stack([pts[:, 0] * xh_px + reg["tx"], reg["baseline_row"] + reg["ty"] - pts[:, 1] * xh_px])

        stored, frame, xh_stored = mapping.stored_frame(strokes, registration, xh)
        assert xh_stored == pytest.approx(xh / mapping.fy)
        for mine, theirs in zip(stored, strokes, strict=True):
            expected = mapping.to_strip(crop_px(theirs, registration, xh))
            assert np.allclose(crop_px(mine, frame, xh_stored), expected, atol=1e-9)

    def test_an_unresampled_stored_frame_is_the_offset_and_the_same_strokes(self):
        strokes = [[[0.0, 0.0], [1.0, 1.0]]]
        stored, frame, xh = CropToStrip(40, 7).stored_frame(strokes, {"tx": 3.0, "ty": -1.0, "baseline_row": 240}, 118)
        assert stored is strokes
        assert frame == {"tx": 43.0, "ty": -1.0, "baseline_row": 247.0}
        assert xh == 118.0


def _garland(height: int = 160, width: int = 240, baseline: int = 96, waist: int = 70) -> np.ndarray:
    """A 1-px skeleton of a garland hand: flat feet on `baseline`, flat tops on `waist`, verticals between."""
    skel = np.zeros((height, width), dtype=bool)
    for x in range(20, 220, 20):
        skel[waist : baseline + 1, x] = True
        skel[baseline, x : x + 10] = True
        skel[waist, x + 10 : x + 20] = True
        skel[waist : baseline + 1, x + 10] = True
    return skel


# The identity calibration: the estimator taken at its word, so a test can
# name the rows it must come out on without the plate's bias in between.
UNBIASED = ModeCalibration(ratio=1.0, offset_xh=0.0)


class TestSeedRegistration:
    """Stage 3 — the hand's own lineature and width, and the refusals to guess."""

    def test_the_modes_read_the_rows_the_hand_wrote_on(self):
        # Printed ruling: baseline 100, x-height 40. The hand wrote smaller
        # and higher — feet on 96, tops on 70.
        assert skeleton_modes(_garland(), 40.0, 100.0) == (96.0, 70.0)

    def test_the_registration_moves_the_lineature_and_keeps_x_apart(self):
        seed = register_seed(_garland(), 100, 60, 0, composed_width_units=10.0, calibration=UNBIASED)
        assert seed.applied and seed.reason is None
        assert (seed.baseline_y, seed.midband_y) == (96, 70)
        assert seed.readings["sy"] == pytest.approx(26 / 40)
        # sx is its own number: the ink's width over the composed width at the
        # REGISTERED x-height, not the vertical factor reused.
        cols = np.nonzero(_garland().any(axis=0))[0]
        assert seed.x_scale == pytest.approx((cols.max() - cols.min()) / (10.0 * 26))
        assert seed.x_scale != pytest.approx(seed.readings["sy"])

    def test_the_plate_calibration_undoes_the_estimators_bias(self):
        seed = register_seed(_garland(), 100, 60, 0, composed_width_units=5.0)
        assert seed.applied
        xh_hand = 26 / PLATE_MODE_CALIBRATION.ratio
        baseline = 96 - PLATE_MODE_CALIBRATION.offset_xh * xh_hand
        assert (seed.baseline_y, seed.midband_y) == (int(round(baseline)), int(round(baseline - xh_hand)))

    def test_rows_in_another_frame_come_back_in_that_frame(self):
        # A plate crop's rows are page rows; the skeleton's row 0 sits at the
        # crop's top. The registration is the same, shifted by that offset.
        seed = register_seed(_garland(), 600, 560, 500, composed_width_units=10.0, calibration=UNBIASED)
        assert (seed.baseline_y, seed.midband_y) == (596, 570)

    def test_unreadable_modes_leave_the_seed_where_it_was(self):
        skel = np.zeros((160, 240), dtype=bool)
        skel[5, 20:200] = True  # ink nowhere near the printed band
        seed = register_seed(skel, 100, 60, 0, composed_width_units=10.0)
        assert not seed.applied and "unreadable" in seed.reason
        assert (seed.baseline_y, seed.midband_y, seed.x_scale) == (100, 60, 1.0)

    def test_no_ink_leaves_the_seed_where_it_was(self):
        seed = register_seed(np.zeros((160, 240), dtype=bool), 100, 60, 0, composed_width_units=10.0)
        assert not seed.applied and (seed.baseline_y, seed.midband_y, seed.x_scale) == (100, 60, 1.0)

    def test_a_waist_on_the_baseline_is_no_x_height(self):
        skel = np.zeros((160, 240), dtype=bool)
        skel[84, 20:200] = True  # both windows meet at B − 0.4 xh = 84
        seed = register_seed(skel, 100, 60, 0, composed_width_units=10.0)
        assert not seed.applied and "waist" in seed.reason

    def test_a_reading_past_the_bounds_falls_back_rather_than_being_clamped(self):
        # A composed word a tenth as wide as the ink would need k ≈ 7.7 — no
        # hand the Bogen was written in, and a stored x-height the API refuses.
        wild = register_seed(_garland(), 100, 60, 0, composed_width_units=1.0, calibration=UNBIASED)
        assert not wild.applied and "outside" in wild.reason
        assert (wild.baseline_y, wild.midband_y, wild.x_scale) == (100, 60, 1.0)
        assert wild.readings["k"] > SEED_SCALE_BOUNDS[1]
        # Without bounds the reading is applied as measured.
        free = register_seed(_garland(), 100, 60, 0, composed_width_units=1.0, calibration=UNBIASED, bounds=None)
        assert free.applied and free.x_scale == pytest.approx(wild.readings["k"])

    def test_the_x_scale_alone_reads_k_against_the_rows_it_was_handed(self):
        # R-split (`sep24b`): the same ink width as the full registration, but
        # measured against the case's own x-height, and the rows untouched.
        cols = np.nonzero(_garland().any(axis=0))[0]
        seed = register_seed_width(_garland(), 100, 60, composed_width_units=5.0)
        assert seed.applied and seed.reason is None
        assert (seed.baseline_y, seed.midband_y) == (100, 60)
        assert seed.x_scale == pytest.approx((cols.max() - cols.min()) / (5.0 * 40))
        assert "sy" not in seed.readings and seed.readings["xh_case"] == 40.0
        # The full registration's k is the same width over a different x-height.
        full = register_seed(_garland(), 100, 60, 0, composed_width_units=5.0, calibration=UNBIASED)
        assert full.x_scale * full.readings["xh_registered"] == pytest.approx(seed.x_scale * 40.0)

    def test_the_x_scale_alone_falls_back_rather_than_being_clamped(self):
        wild = register_seed_width(_garland(), 100, 60, composed_width_units=0.5)
        assert not wild.applied and "outside" in wild.reason
        assert (wild.baseline_y, wild.midband_y, wild.x_scale) == (100, 60, 1.0)
        free = register_seed_width(_garland(), 100, 60, composed_width_units=0.5, bounds=None)
        assert free.applied and free.x_scale == pytest.approx(wild.readings["k"])
        empty = register_seed_width(np.zeros((160, 240), dtype=bool), 100, 60, composed_width_units=5.0)
        assert not empty.applied and empty.x_scale == 1.0
        flat = register_seed_width(_garland(), 100, 60, composed_width_units=0.0)
        assert not flat.applied and "width" in flat.reason

    def test_the_bounds_are_the_apis_own_x_height_tolerance(self):
        assert SEED_SCALE_BOUNDS == (1 / XH_NOMINAL_TOLERANCE, XH_NOMINAL_TOLERANCE)

    def test_the_calibration_is_the_estimators_reading_on_a_known_lineature(self):
        # Three „plate words" whose true lineature is baseline 100, x-height 40:
        # the estimator reads 26/40 of it and the baseline 4 px high.
        cal, n, unreadable = mode_calibration([(_garland(), 40.0, 100.0)] * 3)
        assert (n, unreadable) == (3, 0)
        assert cal.ratio == pytest.approx(26 / 40)
        assert cal.offset_xh == pytest.approx(-4 / 40)


class TestComposedScale:
    """Stage 3's sx on the composition — x only, and never on a bench case."""

    COMPOSED = {
        "items": [
            {"centerline": [[0.0, 0.0], [1.0, 1.0]], "rings": [[[0.0, 0.1], [2.0, 0.3]]], "slot_index": 0},
            {"centerline": [[1.5, 0.2], [3.0, 0.8]], "lift": True},
            {"kind": "guide"},
        ],
        "bounds": {"min_x": -0.5, "max_x": 3.0, "min_y": -1.0, "max_y": 2.0},
        "missing": [],
    }

    def test_every_drawn_x_and_the_horizontal_bounds_scale_and_nothing_else(self):
        out = scale_composed_x(self.COMPOSED, 0.5)
        assert out["items"][0]["centerline"] == [[0.0, 0.0], [0.5, 1.0]]
        assert out["items"][0]["rings"] == [[[0.0, 0.1], [1.0, 0.3]]]
        assert out["items"][1]["centerline"] == [[0.75, 0.2], [1.5, 0.8]]
        assert out["items"][1]["lift"] is True and out["items"][0]["slot_index"] == 0
        assert out["items"][2] == {"kind": "guide"}
        assert out["bounds"] == {"min_x": -0.25, "max_x": 1.5, "min_y": -1.0, "max_y": 2.0}
        assert out["missing"] == []
        # The composer's own payload is left as it was.
        assert self.COMPOSED["items"][0]["centerline"] == [[0.0, 0.0], [1.0, 1.0]]

    def test_derive_word_stretches_only_a_case_that_carries_a_scale(self, monkeypatch):
        import tools.wordlab.derive as derive
        from tools.wordlab.cases import WordCase

        composed = dict(self.COMPOSED)
        monkeypatch.setattr(derive, "compose_word", lambda *_a, **_k: composed)
        case = WordCase(
            id="x",
            word="x",
            kind="word",
            slots=[],
            templates={},
            style_ratio=[1, 1, 1],
            width_resolver="constant",
            nib_units=None,
        )
        # A bench case: the composer's payload, the very object.
        assert derive.derive_word(case).composed is composed
        stretched = derive.derive_word(dataclasses.replace(case, seed_x_scale=2.0)).composed
        assert stretched["items"][1]["centerline"] == [[3.0, 0.2], [6.0, 0.8]]
