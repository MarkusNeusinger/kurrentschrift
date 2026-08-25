"""The Eigenhand PDF writer: golden bytes + structural honesty checks."""

from __future__ import annotations

import copy
import hashlib
import re

import pytest

from core.eigenhand import geometry, pdfgen
from core.eigenhand.bogen import MARK_CAPTION, ROW_ID_GAP_MM, build_layout, geometry_digest, render_pdf, select_strips
from core.eigenhand.plan import load_plan


def _capture(layout: dict) -> dict[str, list]:
    """Render one layout and return the primitives it drew, in millimetres.

    Checking the composed sheet beats checking the constants: an element is
    only safe if what lands on paper is safe, wherever its coordinates came
    from.
    """
    captured: dict[str, list] = {}
    real = pdfgen.build_pdf

    def spy(rects, lines, texts):
        captured["rects"], captured["lines"], captured["texts"] = rects, lines, texts
        return real(rects, lines, texts)

    pdfgen.build_pdf = spy
    try:
        render_pdf(layout)
    finally:
        pdfgen.build_pdf = real
    return captured


def _fixed_layout() -> dict:
    """A small, fully explicit layout — no clock, no git, no repo state."""
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
            "centers_mm": {"tl": [10.0, 10.0], "tr": [200.0, 10.0], "bl": [10.0, 287.0], "br": [200.0, 287.0]},
        },
        "rows": [
            {
                "strip": "S0001",
                "attempt": 1,
                "attempts": 2,
                "band_mm": {"asc_top": 15.0, "waist": 21.0, "baseline": 27.0, "desc_bot": 33.0},
                "mark_mm": [202.0, 21.5, 207.0, 26.5],
                "cut_mm": [12.0, 11.0, 197.0, 40.0],
                "boxes": [
                    {"word": "lesen", "label": "lesen", "x0_mm": 15.0, "x1_mm": 40.0},
                    {"word": "Haustür", "label": "Haus*|tür", "x0_mm": 43.0, "x1_mm": 80.0},
                ],
            },
            {
                "strip": "S0001",
                "attempt": 2,
                "attempts": 2,
                "band_mm": {"asc_top": 42.0, "waist": 48.0, "baseline": 54.0, "desc_bot": 60.0},
                "mark_mm": [202.0, 48.5, 207.0, 53.5],
                "cut_mm": [12.0, 38.0, 197.0, 67.0],
                "boxes": [{"word": "das", "label": "das", "x0_mm": 15.0, "x1_mm": 38.0}],
            },
        ],
        "provenance": {"date": "2026-08-22", "commit": "abc1234", "config_hash": "0123456789", "streifen_sha256": "x"},
    }


# Pinned bytes of _fixed_layout() — deterministic by construction (no clock,
# no git, no repo state). A change here is a REAL output change: re-pin only
# deliberately, with the diff understood.
#
# Re-baselined 2026-08-25 (printable-area pass): the Passmarken moved from
# 7 mm to 10 mm off each edge so they clear PRINT_SAFE_MM, and header, footer
# and legend moved from the writing margin to META_MARGIN_MM so they keep the
# same 4 mm off the marks they had before. Rows, boxes and rulings are
# untouched.
# Re-baselined again the same day, twice: the legend was reworded so it no
# longer needs the long s it could not print, and then the foot of the sheet
# was rebuilt — the writer's irreversible rules and the ruler check took the
# place the duplicated machine id had held.
# Re-baselined 2026-08-25 (strip self-identification): each row's top pad now
# carries hand, sheet and print date right-aligned beside its strip id, so a
# CUT strip says where it is from without the Kartei.
GOLDEN_SHA256 = "150e14625e61ca2b7e2eb90f2ff777aa9a4857379f7df5388e8e116e7c285f1b"


class TestRenderedPdf:
    def test_golden_bytes(self):
        pdf = render_pdf(_fixed_layout())
        assert hashlib.sha256(pdf).hexdigest() == GOLDEN_SHA256

    def test_fiducials_come_from_the_layout_not_the_constants(self):
        """An already-printed Bogen keeps ITS geometry when the constants move.

        This is what makes a printable-area pass safe: the sidecar is the
        contract, so sheets printed before it still re-render — and still
        register — exactly as they were put on paper.
        """
        old = copy.deepcopy(_fixed_layout())
        old["fiducials"]["centers_mm"] = {
            "tl": [7.0, 7.0],
            "tr": [203.0, 7.0],
            "bl": [7.0, 290.0],
            "br": [203.0, 290.0],
        }
        drawn = _capture(old)["rects"]
        half = old["fiducials"]["size_mm"] / 2
        corners = {(round(r.x + half, 3), round(r.y + half, 3)) for r in drawn if r.color == "#000000"}
        assert corners == {(7.0, 7.0), (203.0, 7.0), (7.0, 290.0), (203.0, 290.0)}
        assert render_pdf(old) != render_pdf(_fixed_layout())

    def test_nothing_is_drawn_inside_the_declared_printable_area(self):
        """The sheet must fit the printer it asks for — PRINT_SAFE_MM on every edge.

        Checked on the real composed sheet rather than on the constants: the
        failure this guards against (an HP LaserJet refuses to print within
        4.23 mm and clips a Passmarke, whose centroid then silently biases the
        whole rectification) comes from a DRAWN element, wherever it was
        computed.
        """
        plan = load_plan()
        lo = geometry.PRINT_SAFE_MM
        hi_x, hi_y = geometry.A4_WIDTH_MM - lo, geometry.A4_HEIGHT_MM - lo
        for style in geometry.PRESETS:
            strips = select_strips(plan, {"strips": {}, "redo": [], "sheets": {}}, 7, 1)
            layout = build_layout("B0001", f"t-{style}", style, strips, plan, "2026-08-25", True)
            drawn = _capture(layout)
            for rect in drawn["rects"]:
                assert rect.x >= lo and rect.y >= lo, (style, rect)
                assert rect.x + rect.w <= hi_x and rect.y + rect.h <= hi_y, (style, rect)
            for line in drawn["lines"]:
                pad = line.width_mm / 2
                assert min(line.x1, line.x2) - pad >= lo and max(line.x1, line.x2) + pad <= hi_x, (style, line)
                assert min(line.y1, line.y2) - pad >= lo and max(line.y1, line.y2) + pad <= hi_y, (style, line)
            for item in drawn["texts"]:
                width = pdfgen.helv_width_mm(item.text, item.size_mm)
                assert item.x >= lo and item.x + width <= hi_x, (style, item.text)
                assert item.y - item.size_mm >= lo and item.y <= hi_y, (style, item.text)

    def test_no_text_on_the_sheet_needs_a_glyph_the_font_lacks(self):
        """A "?" on the sheet is a defect that reaches paper without a warning.

        The legend shipped as "rundes s statt langem ſ" and printed "statt
        langem ?" — WinAnsi has no long s, and the note saying so sat four
        lines above the legend in the same file. Checked over the COMPOSED
        page for every script, so it covers the word labels and strip ids from
        the plan as well as the constants.
        """
        plan = load_plan()
        for style in geometry.PRESETS:
            strips = select_strips(plan, {"strips": {}, "redo": [], "sheets": {}}, 7, 1)
            layout = build_layout("B0001", f"t-{style}", style, strips, plan, "2026-08-25", True)
            for item in _capture(layout)["texts"]:
                assert pdfgen.undrawable(item.text) == [], (style, item.text)

    def test_an_undrawable_character_is_refused_not_substituted(self):
        layout = copy.deepcopy(_fixed_layout())
        layout["rows"][0]["boxes"][0]["label"] = "laſſen"
        with pytest.raises(SystemExit, match="WinAnsi"):
            render_pdf(layout)

    def test_the_cfg_stamp_moves_when_the_registration_frame_moves(self):
        """The failure the old stamp had: it hashed a hand-kept constant list.

        PR #412 moved all four Passmarken by 3 mm — the very frame every scan is
        mapped onto — and the printed `cfg` stayed byte-identical, because
        FIDUCIAL_CENTERS was not on the list. Hashing the layout minus its
        provenance cannot forget a millimetre it prints.
        """
        base = _fixed_layout()
        for mutate in (
            lambda lo: lo["fiducials"]["centers_mm"].__setitem__("tl", [7.0, 7.0]),
            lambda lo: lo["rows"][0]["boxes"][0].__setitem__("x1_mm", 99.0),
            lambda lo: lo["rows"][0].__setitem__("mark_mm", [1.0, 2.0, 3.0, 4.0]),
            lambda lo: lo["rows"][0]["band_mm"].__setitem__("baseline", 42.0),
        ):
            moved = copy.deepcopy(base)
            mutate(moved)
            assert geometry_digest(moved) != geometry_digest(base)

    def test_the_cfg_stamp_ignores_its_own_provenance(self):
        # Otherwise it could not live inside the block it is computed for.
        base = _fixed_layout()
        other = copy.deepcopy(base)
        other["provenance"] = {"date": "1999-01-01", "commit": "deadbee", "config_hash": "x", "streifen_sha256": "y"}
        assert geometry_digest(other) == geometry_digest(base)

    def test_the_sheet_prints_the_rules_that_cannot_be_undone(self):
        """Ink, colour scan, scan-before-cut and the verdict box — on the paper.

        They lived only in the operating README, which is not open when the pen
        goes into the ink; and each of them costs a sheet that cannot be
        reprinted (`sheet.py` mints a new id and consumes the queue).
        """
        printed = " ".join(item.text for item in _capture(_fixed_layout())["texts"])
        for fragment in ("nie blau", "in Farbe scannen", "Erst scannen, dann schneiden", "leer = verworfen"):
            assert fragment in printed, fragment

    def test_the_sheet_prints_its_own_ruler_check(self):
        # The only defence against a uniformly scaled print, and it has to be
        # ON the sheet: whoever holds the ruler does not hold the README. The
        # numbers follow the layout's own marks rather than being spelled out,
        # so they cannot drift away from the geometry they check.
        printed = " ".join(item.text for item in _capture(_fixed_layout())["texts"])
        assert "Markenmitten 190,0 × 277,0 mm" in printed
        assert "ohne Skalierung" in printed

    def test_a_cut_strip_says_which_hand_sheet_and_day_it_is_from(self):
        """`S0001` alone does not identify a strip.

        One plan serves all three scripts, so S0001 exists for every hand, and a
        redo prints it again on a later sheet — the attempt suffix only counts
        within one sheet. Without hand, sheet and date on the strip itself, a
        drawer of cut slips is only resolvable through the Kartei and the DB,
        which is exactly what the drawer case has lost.
        """
        layout = _fixed_layout()
        printed = _capture(layout)["texts"]
        for row in layout["rows"]:
            origin = f"{layout['hand']}-{layout['sheet']} · {layout['provenance']['date']}"
            at_row = [
                t for t in printed if t.text == origin and abs(t.y - (row["band_mm"]["asc_top"] - ROW_ID_GAP_MM)) < 1e-6
            ]
            assert at_row, row["strip"]

    def test_both_ends_of_the_strip_line_stay_inside_the_cut_band(self):
        # Outside it the text would be cut away; overlapping each other they
        # would be unreadable. A long hand id is the case that would do it.
        layout = copy.deepcopy(_fixed_layout())
        layout["hand"] = "ein-sehr-langer-schreibername-suetterlin"
        row = layout["rows"][0]
        x0, x1 = row["cut_mm"][0], row["cut_mm"][2]
        runs = sorted(
            (
                (item.x, item.x + pdfgen.helv_width_mm(item.text, item.size_mm))
                for item in _capture(layout)["texts"]
                if abs(item.y - (row["band_mm"]["asc_top"] - ROW_ID_GAP_MM)) < 1e-6
            )
        )
        assert runs[0][0] >= x0 and runs[-1][1] <= x1
        for left, right in zip(runs, runs[1:], strict=False):
            assert left[1] <= right[0], (left, right)

    def test_the_strip_line_stays_in_the_zone_the_qc_masks(self):
        # It is printed matter inside the training image, so it must sit where
        # `ingest._printed_mask` blanks everything: above the ascender line.
        layout = _fixed_layout()
        row = layout["rows"][0]
        for item in _capture(layout)["texts"]:
            if abs(item.y - (row["band_mm"]["asc_top"] - ROW_ID_GAP_MM)) < 1e-6:
                assert item.y <= row["band_mm"]["asc_top"]
                assert item.y - item.size_mm >= row["cut_mm"][1]

    def test_xref_offsets_point_at_their_objects(self):
        text = render_pdf(_fixed_layout()).decode("latin-1")
        xref_offset = int(text.rsplit("startxref\n", 1)[1].split("\n")[0])
        assert text[xref_offset:].startswith("xref")
        entries = re.findall(r"(\d{10}) 00000 n", text[xref_offset:])
        assert len(entries) == 5
        for index, offset in enumerate(entries):
            assert text[int(offset) :].startswith(f"{index + 1} 0 obj")

    def test_stream_length_is_exact(self):
        text = render_pdf(_fixed_layout()).decode("latin-1")
        match = re.search(r"/Length (\d+) >>\nstream\n", text)
        assert match is not None
        assert text[match.end() + int(match.group(1)) :].startswith("\nendstream")

    def test_verdict_boxes_and_caption_are_drawn(self):
        text = render_pdf(_fixed_layout()).decode("latin-1")
        # From the constant, not a literal: the caption gained its question mark
        # in the same pass that put the verdict rule into the footer.
        assert text.count(f"({MARK_CAPTION}) Tj") == 1  # one column caption, above the first row
        assert "(nein) Tj" not in text  # one box only: ticked = ok, empty = not
        assert text.count(" l S") >= 8  # four edges per box, one box per row, two rows

    def test_cut_marks_add_exactly_the_expected_segments(self):
        layout = _fixed_layout()
        marked = render_pdf(layout).decode("latin-1").count(" l S")
        bare = copy.deepcopy(layout)
        for row in bare["rows"]:
            del row["cut_mm"]  # a sheet printed before the Schnittband existed
        cuts = [tuple(row["cut_mm"]) for row in layout["rows"]]
        expected = sum(len(geometry.cut_ticks(cut)) for cut in cuts) + len(geometry.page_cut_ticks(cuts))
        assert marked - render_pdf(bare).decode("latin-1").count(" l S") == expected

    def test_attempt_labels_and_umlauts_survive_winansi(self):
        text = render_pdf(_fixed_layout()).decode("latin-1")
        assert "S0001 \\(1/2\\)" in text  # parens are escaped in PDF literals
        assert "Haus*|tür" in text  # WinAnsi keeps the umlaut, no font embedding


class TestHelvWidth:
    def test_known_advances(self):
        assert pdfgen.helv_width_mm("i", 10.0) == 2.22
        assert pdfgen.helv_width_mm("W", 10.0) == 9.44

    def test_digits_use_the_uniform_advance(self):
        assert pdfgen.helv_width_mm("1", 10.0) == pdfgen.helv_width_mm("9", 10.0) == pytest.approx(5.56)

    def test_a_non_ascii_digit_is_measured_as_the_char_that_gets_drawn(self):
        # Anything outside cp1252 is drawn as "?", so the metric must measure
        # "?" — not the digit advance the character never gets.
        assert pdfgen.winansi("١") == "?"
        assert pdfgen.helv_width_mm("١", 10.0) == pdfgen.helv_width_mm("?", 10.0)

    def test_escaping_never_inflates_the_measured_width(self):
        # The literal escape puts a backslash before "(" and ")" that the
        # reader does not draw. Measuring the ESCAPED string would widen every
        # row id ("S0001 (1/3)") and push it off centre — so the metric runs
        # over the WinAnsi mapping, which keeps the parens single.
        assert pdfgen.winansi("(1/2)") == "(1/2)"
        parts = sum(pdfgen.helv_width_mm(ch, 10.0) for ch in "(1/2)")
        assert pdfgen.helv_width_mm("(1/2)", 10.0) == pytest.approx(parts)

    def test_cp1252_punctuation_carries_its_real_helvetica_width(self):
        # The German quotes and dashes DO have WinAnsi bytes — and real widths.
        # Words like „wohl“ and don’t are in the committed strip plan, so a
        # 556 fallback here would push their printed labels off centre.
        for char, units in (("„", 333), ("“", 333), ("’", 222), ("–", 556), ("—", 1000), ("…", 1000)):
            assert pdfgen.winansi(char) != "?"
            assert pdfgen.helv_width_mm(char, 1000.0) == pytest.approx(units)

    def test_a_quoted_word_is_narrower_than_the_flat_fallback(self):
        quoted = pdfgen.helv_width_mm("„wohl“", 3.0)
        assert quoted < pdfgen.helv_width_mm("Xwohl X", 3.0)  # 556-per-quote fallback
