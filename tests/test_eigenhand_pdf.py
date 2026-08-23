"""The Eigenhand PDF writer: golden bytes + structural honesty checks."""

from __future__ import annotations

import hashlib
import re

import pytest

from tools.eigenhand import pdfgen
from tools.eigenhand.sheet import render_pdf


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
            "centers_mm": {"tl": [7.0, 7.0], "tr": [203.0, 7.0], "bl": [7.0, 290.0], "br": [203.0, 290.0]},
        },
        "rows": [
            {
                "strip": "S0001",
                "attempt": 1,
                "attempts": 2,
                "band_mm": {"asc_top": 15.0, "waist": 21.0, "baseline": 27.0, "desc_bot": 33.0},
                "mark_mm": [199.0, 21.5, 204.0, 26.5],
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
                "mark_mm": [199.0, 48.5, 204.0, 53.5],
                "boxes": [{"word": "das", "label": "das", "x0_mm": 15.0, "x1_mm": 38.0}],
            },
        ],
        "provenance": {"date": "2026-08-22", "commit": "abc1234", "config_hash": "0123456789", "streifen_sha256": "x"},
    }


# Pinned bytes of _fixed_layout() — deterministic by construction (no clock,
# no git, no repo state). A change here is a REAL output change: re-pin only
# deliberately, with the diff understood.
GOLDEN_SHA256 = "1c5deb4c30a54b806e69cf291cdc8822a946be6f0956ccf586cb978af6601764"


class TestRenderedPdf:
    def test_golden_bytes(self):
        pdf = render_pdf(_fixed_layout())
        assert hashlib.sha256(pdf).hexdigest() == GOLDEN_SHA256

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
        assert text.count("(ok) Tj") == 1  # one column caption, above the first row
        assert "(nein) Tj" not in text  # one box only: ticked = ok, empty = not
        assert text.count(" l S") >= 8  # four edges per box, one box per row, two rows

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

    def test_a_non_ascii_digit_is_measured_as_the_char_that_gets_emitted(self):
        # _escape() writes "?" for anything outside WinAnsi, so the metric must
        # measure "?" — not the digit advance the character never gets.
        assert pdfgen.helv_width_mm("١", 10.0) == pdfgen.helv_width_mm("?", 10.0)
