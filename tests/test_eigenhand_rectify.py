"""Synthetic capture round-trip: render → distort → detect → rectify."""

from __future__ import annotations

import numpy as np
import pytest
from skimage import transform

from tools.eigenhand import ingest
from tools.eigenhand.fiducial import FiducialError, Mark, detect_fiducials, orient_corners
from tools.eigenhand.rasterize import mm_to_px, rasterize_layout


def _layout() -> dict:
    return {
        "format": 1,
        "sheet": "B0001",
        "hand": "test-suetterlin",
        "style": "suetterlin",
        "page_mm": {"width": 210.0, "height": 297.0},
        "fiducials": {
            "size_mm": 8.0,
            "hole_mm": 3.0,
            "donut": "tl",
            "centers_mm": {"tl": [7.0, 7.0], "tr": [203.0, 7.0], "bl": [7.0, 290.0], "br": [203.0, 290.0]},
        },
        "rows": [
            {
                "strip": "S0001",
                "attempt": 1,
                "attempts": 1,
                "band_mm": {"asc_top": 15.0, "waist": 21.0, "baseline": 27.0, "desc_bot": 33.0},
                "marks_mm": {"ok": [196.0, 21.5, 201.0, 26.5], "nein": [202.0, 21.5, 207.0, 26.5]},
                "boxes": [{"word": "lesen", "label": "lesen", "x0_mm": 15.0, "x1_mm": 120.0}],
            },
            {
                "strip": "S0002",
                "attempt": 1,
                "attempts": 1,
                "band_mm": {"asc_top": 42.0, "waist": 48.0, "baseline": 54.0, "desc_bot": 60.0},
                "marks_mm": {"ok": [196.0, 48.5, 201.0, 53.5], "nein": [202.0, 48.5, 207.0, 53.5]},
                "boxes": [{"word": "das", "label": "das", "x0_mm": 15.0, "x1_mm": 100.0}],
            },
        ],
        "provenance": {"date": "2026-08-22", "commit": "", "config_hash": "", "streifen_sha256": ""},
    }


def _distorted_capture(layout: dict, dpi: float = 150.0, rotate: bool = True) -> np.ndarray:
    """Rasterize the sheet, then apply perspective + noise + an optional 180° flip."""
    image = np.asarray(rasterize_layout(layout, dpi=dpi), dtype=np.float64) / 255.0
    height, width = image.shape
    src = np.array([[0, 0], [width, 0], [0, height], [width, height]], dtype=float)
    dst = np.array(
        [
            [width * 0.03, height * 0.02],
            [width * 0.985, height * 0.012],
            [width * 0.012, height * 0.97],
            [width * 0.96, height * 0.99],
        ]
    )
    tform = transform.ProjectiveTransform.from_estimate(dst, src)  # output→input for warp
    warped = transform.warp(image, tform, output_shape=(height, width), cval=1.0)
    if rotate:
        warped = np.rot90(warped, 2)
    rng = np.random.default_rng(7)
    return np.clip(warped + rng.normal(0.0, 0.02, warped.shape), 0.0, 1.0)


class TestRectify:
    def test_guide_lines_recover_within_half_a_millimetre(self):
        layout = _layout()
        capture = _distorted_capture(layout)
        warped, dpi, _marks = ingest.rectify(capture, layout)
        assert 100.0 < dpi < 200.0  # the synthetic capture was rendered at 150

        column_a = ingest._px(40.0)
        column_b = ingest._px(90.0)
        window_mm = 3.0
        for row in layout["rows"]:
            for y_mm in row["band_mm"].values():
                y_expected = ingest._px(y_mm)
                half = ingest._px(window_mm)
                strip = warped[y_expected - half : y_expected + half, column_a:column_b]
                darkest = int(np.argmin(strip.mean(axis=1)))
                deviation_mm = abs(darkest - half) / ingest.PX_PER_MM
                assert deviation_mm <= 0.5, f"line {y_mm} mm off by {deviation_mm:.2f} mm"

    def test_upside_down_capture_lands_upright(self):
        # Rectified without rotation must equal rectified with rotation — the
        # donut anchors orientation either way.
        layout = _layout()
        upright, _, _ = ingest.rectify(_distorted_capture(layout, rotate=False), layout)
        flipped, _, _ = ingest.rectify(_distorted_capture(layout, rotate=True), layout)
        difference = np.abs(upright - flipped).mean()
        assert difference < 0.02

    def test_missing_fiducial_fails_loudly(self):
        layout = _layout()
        capture = _distorted_capture(layout, rotate=False)
        edge = int(mm_to_px(30.0, 150.0))
        capture[:edge, :edge] = 1.0  # paint the top-left mark away
        with pytest.raises(FiducialError):
            ingest.rectify(capture, layout)


class TestOrientation:
    @staticmethod
    def _quadrants(donut: str) -> dict[str, Mark]:
        return {
            q: Mark(
                center={"tl": (10.0, 10.0), "tr": (90.0, 10.0), "bl": (10.0, 90.0), "br": (90.0, 90.0)}[q],
                area=100.0,
                has_hole=(q == donut),
            )
            for q in ("tl", "tr", "bl", "br")
        }

    def test_identity_when_donut_is_top_left(self):
        oriented = orient_corners(self._quadrants("tl"))
        assert oriented["tl"].has_hole

    def test_all_rotations_put_the_donut_top_left(self):
        for donut in ("tr", "br", "bl"):
            oriented = orient_corners(self._quadrants(donut))
            assert oriented["tl"].has_hole
            assert len({m.center for m in oriented.values()}) == 4

    def test_two_holes_are_ambiguous(self):
        marks = self._quadrants("tl")
        marks["br"] = Mark(marks["br"].center, marks["br"].area, True)
        with pytest.raises(FiducialError, match="ambiguous"):
            orient_corners(marks)


class TestDetection:
    def test_finds_four_marks_on_a_clean_render(self):
        image = np.asarray(rasterize_layout(_layout(), dpi=150.0), dtype=np.float64) / 255.0
        marks = detect_fiducials(image)
        assert set(marks) == {"tl", "tr", "bl", "br"}
        assert marks["tl"].has_hole and not marks["br"].has_hole


class TestPenMark:
    """The writer's ok/nein tick, read off the rectified page."""

    @staticmethod
    def _page_with_ticks(ticks: dict[int, str]) -> tuple[np.ndarray, dict]:
        """Rasterize the layout, ink the named box of the named rows, rectify."""
        layout = _layout()
        image = np.asarray(rasterize_layout(layout, dpi=300.0), dtype=np.float64) / 255.0
        for row_index, key in ticks.items():
            x0, y0, x1, y1 = layout["rows"][row_index]["marks_mm"][key]
            top, bottom = int(mm_to_px(y0 + 1.2, 300.0)), int(mm_to_px(y1 - 1.2, 300.0))
            left, right = int(mm_to_px(x0 + 1.2, 300.0)), int(mm_to_px(x1 - 1.2, 300.0))
            image[top:bottom, left:right] = 0.05
        return image.astype(np.float32), layout

    def test_ok_tick_reads_as_accepted(self):
        page, layout = self._page_with_ticks({0: "ok"})
        verdict, flags = ingest.read_pen_mark(page, layout["rows"][0])
        assert (verdict, flags) == ("angenommen", [])

    def test_nein_tick_reads_as_rejected(self):
        page, layout = self._page_with_ticks({0: "nein"})
        assert ingest.read_pen_mark(page, layout["rows"][0])[0] == "verworfen"

    def test_unmarked_row_stays_undecided(self):
        page, layout = self._page_with_ticks({})
        assert ingest.read_pen_mark(page, layout["rows"][0]) == (None, [])

    def test_both_boxes_ticked_is_ambiguous_and_says_so(self):
        page, layout = self._page_with_ticks({0: "ok"})
        x0, y0, x1, y1 = layout["rows"][0]["marks_mm"]["nein"]
        page[
            int(mm_to_px(y0 + 1.2, 300.0)) : int(mm_to_px(y1 - 1.2, 300.0)),
            int(mm_to_px(x0 + 1.2, 300.0)) : int(mm_to_px(x1 - 1.2, 300.0)),
        ] = 0.05
        verdict, flags = ingest.read_pen_mark(page, layout["rows"][0])
        assert verdict is None
        assert "marke-mehrdeutig" in flags

    def test_layout_without_marks_is_tolerated(self):
        page, layout = self._page_with_ticks({})
        row = dict(layout["rows"][0])
        del row["marks_mm"]
        assert ingest.read_pen_mark(page, row) == (None, [])
