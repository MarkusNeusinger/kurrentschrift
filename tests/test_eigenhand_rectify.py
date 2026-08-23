"""Synthetic capture round-trip: render → distort → detect → rectify."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image
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
                "mark_mm": [202.0, 21.5, 207.0, 26.5],
                "cut_mm": [12.0, 11.0, 197.0, 40.0],
                "boxes": [{"word": "lesen", "label": "lesen", "x0_mm": 15.0, "x1_mm": 120.0}],
            },
            {
                "strip": "S0002",
                "attempt": 1,
                "attempts": 1,
                "band_mm": {"asc_top": 42.0, "waist": 48.0, "baseline": 54.0, "desc_bot": 60.0},
                "mark_mm": [202.0, 48.5, 207.0, 53.5],
                "cut_mm": [12.0, 38.0, 197.0, 67.0],
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

    def test_every_crop_comes_out_at_the_strip_format(self, tmp_path, monkeypatch):
        # The point of the Schnittband: what the scissors produce and what the
        # importer files are the same rectangle, identical for every row —
        # rows carrying different words must not yield different crops.
        monkeypatch.setenv("EIGENHAND_DATA", str(tmp_path / "own-hand"))
        layout = _layout()
        warped, dpi, _marks = ingest.rectify(_distorted_capture(layout), layout)
        scan = tmp_path / "scan.png"
        Image.fromarray(np.zeros((4, 4), dtype=np.uint8)).save(scan)
        session = {"date": "2026-08-23", "feder": "", "tinte": "", "papier": "", "geraet": "scanner"}
        payload = ingest.build_payload("test-suetterlin", "B0001", layout, warped, scan, session, dpi)

        import_dir = ingest.hand_dir("test-suetterlin") / "blaetter" / "B0001" / "import"
        sizes = {Image.open(import_dir / row["crop"]).size for row in payload["rows"]}
        assert len(sizes) == 1, f"strips differ in size: {sizes}"
        width_px, height_px = sizes.pop()
        cut = layout["rows"][0]["cut_mm"]
        assert abs(width_px / ingest.PX_PER_MM - (cut[2] - cut[0])) < 0.5
        assert abs(height_px / ingest.PX_PER_MM - (cut[3] - cut[1])) < 0.5

    def test_the_printed_strip_id_does_not_fake_ink(self, tmp_path, monkeypatch):
        # The id is printed INSIDE the Schnittband's top pad. QC must still see
        # an unwritten row as `leer` — otherwise every empty row looks written.
        monkeypatch.setenv("EIGENHAND_DATA", str(tmp_path / "own-hand"))
        layout = _layout()
        warped, dpi, _marks = ingest.rectify(_distorted_capture(layout, rotate=False), layout)
        cut, band = layout["rows"][0]["cut_mm"], layout["rows"][0]["band_mm"]
        top, bottom = int(mm_to_px(cut[1] + 0.5, 300.0)), int(mm_to_px(band["asc_top"] - 1.0, 300.0))
        left, right = int(mm_to_px(cut[0] + 1.0, 300.0)), int(mm_to_px(cut[0] + 15.0, 300.0))
        warped[top:bottom, left:right] = 0.05  # a fat stand-in for "S0001"

        scan = tmp_path / "scan.png"
        Image.fromarray(np.zeros((4, 4), dtype=np.uint8)).save(scan)
        session = {"date": "2026-08-23", "feder": "", "tinte": "", "papier": "", "geraet": "scanner"}
        payload = ingest.build_payload("test-suetterlin", "B0001", layout, warped, scan, session, dpi)
        assert "leer" in payload["rows"][0]["qc"]

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


class TestCaptureChannel:
    """Pale cyan rulings drop out of a colour capture's blue channel."""

    @staticmethod
    def _sheet(tmp_path):
        """A 3-band strip: paper, a cyan ruling, black ink."""
        from tools.eigenhand import geometry

        def rgb(hexc):
            return tuple(int(hexc[i : i + 2], 16) for i in (1, 3, 5))

        pixels = np.zeros((3, 4, 3), dtype=np.uint8)
        pixels[0] = (250, 250, 246)  # paper
        pixels[1] = rgb(geometry.CAPTURE_STYLES["baseline"][0])  # printed line
        pixels[2] = (25, 25, 25)  # black ink
        path = tmp_path / "capture.png"
        Image.fromarray(pixels, mode="RGB").save(path)
        return path

    def test_the_blue_channel_keeps_ink_and_loses_the_rulings(self, tmp_path):
        plane, channel = ingest.load_capture(self._sheet(tmp_path))
        assert channel == "blau"
        paper, ruling, ink = plane[0].mean(), plane[1].mean(), plane[2].mean()
        assert ruling > ingest.INK_THRESHOLD, "the ruling would be read as ink"
        assert abs(ruling - paper) < 0.12, "the ruling should sit near paper, not merely above the threshold"
        assert ink < ingest.INK_THRESHOLD, "the ink has to survive the channel pick"

    def test_a_greyscale_capture_still_works_and_says_so(self, tmp_path):
        colour = Image.open(self._sheet(tmp_path)).convert("L")
        path = tmp_path / "grey.png"
        colour.save(path)
        plane, channel = ingest.load_capture(path)
        assert channel == "grau"
        # Even flattened to grey the rulings stay clear of the ink threshold —
        # cyan is the better choice in both capture modes, not a bet on one.
        assert plane[1].mean() > ingest.INK_THRESHOLD
        assert plane[2].mean() < ingest.INK_THRESHOLD

    def test_an_explicit_channel_overrides_the_default(self, tmp_path):
        plane, channel = ingest.load_capture(self._sheet(tmp_path), "rot")
        assert channel == "rot"
        # The red channel is exactly the wrong one for cyan — it is the darkest
        # component there. Pinned so the default can never drift onto it.
        assert plane[1].mean() < ingest.load_capture(self._sheet(tmp_path))[0][1].mean()


class TestPenMark:
    """The writer's tick in the one verdict box, read off the rectified page."""

    @staticmethod
    def _page_with_ticks(ticked_rows: set[int]) -> tuple[np.ndarray, dict]:
        """Rasterize the layout, ink the verdict box of the named rows, rectify."""
        layout = _layout()
        image = np.asarray(rasterize_layout(layout, dpi=300.0), dtype=np.float64) / 255.0
        for row_index in ticked_rows:
            x0, y0, x1, y1 = layout["rows"][row_index]["mark_mm"]
            top, bottom = int(mm_to_px(y0 + 1.2, 300.0)), int(mm_to_px(y1 - 1.2, 300.0))
            left, right = int(mm_to_px(x0 + 1.2, 300.0)), int(mm_to_px(x1 - 1.2, 300.0))
            image[top:bottom, left:right] = 0.05
        return image.astype(np.float32), layout

    def test_a_tick_reads_as_accepted(self):
        page, layout = self._page_with_ticks({0})
        assert ingest.read_pen_mark(page, layout["rows"][0]) == "angenommen"

    def test_an_empty_box_reads_as_rejected(self):
        # Owner rule 2026-08-23: a cross or check in the box means ok, and
        # nothing in it means not ok. An unticked row is not accepted, and the
        # strip simply returns to the print queue.
        page, layout = self._page_with_ticks(set())
        assert ingest.read_pen_mark(page, layout["rows"][0]) == "verworfen"

    def test_rows_are_read_independently(self):
        page, layout = self._page_with_ticks({1})
        assert ingest.read_pen_mark(page, layout["rows"][0]) == "verworfen"
        assert ingest.read_pen_mark(page, layout["rows"][1]) == "angenommen"

    def test_a_stray_speck_is_not_a_tick(self):
        # The printed outline is excluded by the inset; a single dot inside
        # stays below MARK_MIN_FRACTION and must not read as a decision.
        page, layout = self._page_with_ticks(set())
        x0, y0, _x1, _y1 = layout["rows"][0]["mark_mm"]
        top, left = int(mm_to_px(y0 + 2.4, 300.0)), int(mm_to_px(x0 + 2.4, 300.0))
        page[top : top + 2, left : left + 2] = 0.05
        assert ingest.read_pen_mark(page, layout["rows"][0]) == "verworfen"

    def test_layout_without_a_mark_box_is_tolerated(self):
        page, layout = self._page_with_ticks(set())
        row = dict(layout["rows"][0])
        del row["mark_mm"]
        assert ingest.read_pen_mark(page, row) is None
