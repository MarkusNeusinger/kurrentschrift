"""The print queue and the Stapel: one selection per job, one PDF per stack.

Owner decision 2026-08-26: a print job starts at the FRONT of the plan minus
the strips that are already belegt — a Bogen that was printed but never
written holds nothing back (the new print is asked for because the old sheet
is gone), and "sheets in circulation" is not a quantity the queue counts. The
pages of one job continue the queue among themselves, and the job comes out
as ONE PDF with one page per Bogen.

Pure-core checks against the committed strip plan; no data root, no DB.
"""

from __future__ import annotations

import re

import pytest

from core.eigenhand import pdfgen
from core.eigenhand.bogen import compose_sheet, compose_stack, render_pdf, render_stack_pdf, select_strips
from core.eigenhand.kartei import empty_kartei, next_sheet_id
from core.eigenhand.plan import load_plan, ordered_strips


HAND = "test-suetterlin"
STYLE = "suetterlin"
DATE = "2026-08-26"


def _kartei(printed: dict[str, list[str]] | None = None, accepted: list[str] = (), rejected: list[str] = ()) -> dict:
    kartei = empty_kartei(HAND, STYLE)
    for sheet, strips in (printed or {}).items():
        kartei["sheets"][sheet] = {"printed": DATE, "strips": strips, "layout_sha256": "x", "scans": []}
    for status, strips in (("angenommen", accepted), ("verworfen", rejected)):
        for strip in strips:
            kartei["strips"].setdefault(strip, {"fassungen": []})["fassungen"].append(
                {"id": "F01", "status": status, "sheet": "B0001", "row_index": 0}
            )
    return kartei


class TestQueue:
    def test_a_printed_but_unwritten_strip_is_printed_again(self):
        plan = load_plan()
        first = ordered_strips(plan)[:5]
        kartei = _kartei(printed={"B0001": first})  # printed, never judged → "unterwegs"
        assert select_strips(plan, kartei, 5, 1) == first

    def test_belegt_strips_are_skipped_and_rejected_ones_come_back(self):
        plan = load_plan()
        first = ordered_strips(plan)[:5]
        kartei = _kartei(printed={"B0001": first}, accepted=first[:2], rejected=[first[2]])
        assert select_strips(plan, kartei, 3, 1) == first[2:5]

    def test_the_redo_list_still_leads(self):
        plan = load_plan()
        ordered = ordered_strips(plan)
        kartei = _kartei(accepted=ordered[:3])
        kartei["redo"] = [{"strip": ordered[1]}]
        assert select_strips(plan, kartei, 2, 1) == [ordered[1], ordered[3]]


class TestStack:
    def test_pages_continue_the_queue_and_ids_are_consecutive(self):
        plan = load_plan()
        stack = compose_stack(
            plan=plan, kartei=_kartei(printed={"B0001": []}), hand=HAND, style=STYLE, date=DATE, sheets=3
        )
        sheets = stack["sheets"]
        assert [s["sheet"] for s in sheets] == ["B0002", "B0003", "B0004"]
        flat = [sid for s in sheets for sid in s["strips"]]
        assert flat == ordered_strips(plan)[: len(flat)], "the pages walk the plan in order"
        assert len(flat) == len(set(flat)), "a strip landed on two pages of one stack"

    def test_a_second_job_starts_at_the_front_again(self):
        plan = load_plan()
        first = compose_stack(plan=plan, kartei=_kartei(), hand=HAND, style=STYLE, date=DATE, sheets=2)["sheets"]
        recorded = _kartei(printed={s["sheet"]: s["strips"] for s in first})
        second = compose_stack(plan=plan, kartei=recorded, hand=HAND, style=STYLE, date=DATE, sheets=2)["sheets"]
        assert [s["strips"] for s in second] == [s["strips"] for s in first]
        assert [s["sheet"] for s in second] == ["B0003", "B0004"]

    def test_attempt_groups_stay_on_one_page(self):
        plan = load_plan()
        stack = compose_stack(
            plan=plan, kartei=_kartei(), hand=HAND, style=STYLE, date=DATE, sheets=2, rows=5, repeat=2
        )
        for sheet in stack["sheets"]:
            assert len(sheet["strips"]) == 4  # 5 rows, pairs only: the odd row stays empty
            assert sheet["strips"][0::2] == sheet["strips"][1::2]
            assert all(row["attempts"] == 2 for row in sheet["layout"]["rows"])
        assert stack["sheets"][0]["strips"][-1] != stack["sheets"][1]["strips"][0]

    def test_a_stack_of_one_is_the_single_sheet(self):
        plan = load_plan()
        single = compose_sheet(plan=plan, kartei=_kartei(), hand=HAND, style=STYLE, date=DATE, rows=4)
        stack = compose_stack(plan=plan, kartei=_kartei(), hand=HAND, style=STYLE, date=DATE, rows=4)
        assert single["strips"] == stack["sheets"][0]["strips"]
        assert single["pdf"] == stack["pdf"] == stack["sheets"][0]["pdf"]

    def test_explicit_strips_refuse_a_stack(self):
        plan = load_plan()
        with pytest.raises(SystemExit, match="ONE Bogen"):
            compose_stack(plan=plan, kartei=_kartei(), hand=HAND, style=STYLE, date=DATE, sheets=2, strips=["S0001"])

    def test_the_ids_never_collide_with_recorded_ones(self):
        plan = load_plan()
        kartei = _kartei(printed={"B0001": [], "B0007": []})
        stack = compose_stack(plan=plan, kartei=kartei, hand=HAND, style=STYLE, date=DATE, sheets=2, rows=3)
        assert [s["sheet"] for s in stack["sheets"]] == ["B0008", "B0009"]
        assert next_sheet_id(kartei) == "B0008", "composing must not mutate the caller's Kartei"


class TestStackPdf:
    def _layouts(self, n: int) -> list[dict]:
        plan = load_plan()
        stack = compose_stack(plan=plan, kartei=_kartei(), hand=HAND, style=STYLE, date=DATE, sheets=n, rows=3)
        return [s["layout"] for s in stack["sheets"]]

    def test_one_page_is_byte_identical_to_the_single_writer(self):
        layout = self._layouts(1)[0]
        assert render_stack_pdf([layout]) == render_pdf(layout)

    def test_three_pages_are_one_document(self):
        text = render_stack_pdf(self._layouts(3)).decode("latin-1")
        assert text.startswith("%PDF-1.4")
        assert "/Count 3 >>" in text
        assert text.count("/Type /Page ") == 3
        assert text.count("/Type /Font") == 1, "one shared font object"
        # Every page's content stream is exact and every xref entry points at its object.
        for match in re.finditer(r"/Length (\d+) >>\nstream\n", text):
            assert text[match.end() + int(match.group(1)) :].startswith("\nendstream")
        xref_offset = int(text.rsplit("startxref\n", 1)[1].split("\n")[0])
        entries = re.findall(r"(\d{10}) 00000 n", text[xref_offset:])
        assert len(entries) == 5 + 2 * 2  # catalog, pages, page 1, content 1, font + (page, content) × 2
        for index, offset in enumerate(entries):
            assert text[int(offset) :].startswith(f"{index + 1} 0 obj")

    def test_the_pages_carry_their_own_sheet_ids(self):
        layouts = self._layouts(2)
        text = render_stack_pdf(layouts).decode("latin-1")
        assert text.index(layouts[0]["sheet"]) < text.index(layouts[1]["sheet"])

    def test_an_empty_stack_is_refused(self):
        with pytest.raises(ValueError):
            pdfgen.build_pdf_pages([])
