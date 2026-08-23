"""The Eigenhand endpoints: the own-hand Bestand and the Bogen printer.

Same in-memory aiosqlite stack as the other HTTP suites (`tests/api_harness.py`
via the `api` fixture). What matters here beyond the usual roundtrip is that
the SERVER path and the LOCAL path stay one system: the admin view prints the
Bögen the CLI would print, counts what the CLI counts, and stores the layout a
local ingest run has to register against.

Proves: the Bestand's denominators come from the committed plan (so an empty
hand already knows how many glyphs and joins exist); an accepted Fassung moves
exactly its own strip's items; a stack of Bögen never repeats a strip; the PDF
is re-rendered byte-identically from the stored layout; verdicts are idempotent
per printed row and refuse a contradiction; and every route is admin-gated.
"""

from __future__ import annotations

import pytest

from core.eigenhand import bogen
from core.eigenhand.plan import load_plan
from tests.api_harness import Harness


HAND = "mn-suetterlin"


async def _print(api: Harness, **body) -> dict:
    res = await api.client.request(
        "POST", "/eigenhand/sheets", json_body={"hand": HAND, **body}, headers=api.admin_headers()
    )
    assert res.status == 201, res.body
    return res.json()


async def _bestand(api: Harness, hand: str = HAND) -> dict:
    res = await api.client.request("GET", f"/eigenhand/bestand/{hand}", headers=api.admin_headers())
    assert res.status == 200, res.body
    return res.json()


async def _record(api: Harness, fassungen: list[dict]):
    return await api.client.request(
        "POST", "/eigenhand/fassungen", json_body={"hand": HAND, "fassungen": fassungen}, headers=api.admin_headers()
    )


def _accepted(strip: str, sheet: str, row_index: int, fassung: str = "F01") -> dict:
    return {"strip": strip, "fassung": fassung, "sheet": sheet, "row_index": row_index, "status": "angenommen"}


class TestBestand:
    """What a hand holds — measured against the committed plan, not against itself."""

    @pytest.mark.asyncio
    async def test_an_untouched_hand_already_knows_its_denominators(self, api: Harness):
        data = await _bestand(api)
        plan = load_plan()
        assert data["strips"] == {"total": len(plan["strips"]), "belegt": 0, "unterwegs": 0, "geplant": 120}
        assert data["fassungen"]["angenommen"] == 0
        # Capitals, digits and signs are part of the answer (owner, 2026-08-22).
        for bucket in ("klein", "gross", "ligatur", "ziffer", "zeichen"):
            layer = data["glyphs"][bucket]
            assert layer["possible"] > 0, bucket
            assert layer["covered"] == 0 and layer["belege"] == 0
            assert len(layer["keys"]) == layer["possible"]
        assert data["glyphs"]["ziffer"]["possible"] == 10
        assert data["joins"]["possible"] > 100 and data["joins"]["covered"] == 0
        # No Übergangsraum table on the server — no weighted Quoten, and it says so.
        assert data["quoten"] is None

    @pytest.mark.asyncio
    async def test_an_accepted_fassung_moves_exactly_its_own_strips_items(self, api: Harness):
        printed = await _print(api, strips=["S0001"], date="2026-08-23")
        sheet = printed["sheets"][0]["sheet"]
        assert (await _record(api, [_accepted("S0001", sheet, 0)])).status == 200

        data = await _bestand(api)
        assert data["strips"]["belegt"] == 1
        assert data["fassungen"]["angenommen"] == 1
        plan = load_plan()
        expected_keys = set()
        for word in plan["strips"]["S0001"]["words"]:
            from core.eigenhand import coverage
            from core.eigenhand.plan import shaping_form_of

            for item in coverage.word_items(shaping_form_of(plan, word)):
                if coverage.JOIN_SEP not in item:
                    expected_keys.add(item.split(coverage.POSITION_SEP)[0])
        written = {row["key"] for bucket in data["glyphs"].values() for row in bucket["keys"] if row["belege"]}
        assert written == expected_keys

    @pytest.mark.asyncio
    async def test_a_rejected_row_counts_as_a_rejection_and_nothing_else(self, api: Harness):
        printed = await _print(api, strips=["S0001"], date="2026-08-23")
        sheet = printed["sheets"][0]["sheet"]
        await _record(
            api, [{"strip": "S0001", "fassung": "F01", "sheet": sheet, "row_index": 0, "status": "verworfen"}]
        )
        data = await _bestand(api)
        assert data["fassungen"] == {"angenommen": 0, "verworfen": 1, "zurueckgezogen": 0}
        assert data["strips"]["belegt"] == 0
        assert data["joins"]["covered"] == 0

    @pytest.mark.asyncio
    async def test_a_malformed_hand_id_is_refused_before_anything_is_read(self, api: Harness):
        # A misspelled style, a wrong case, a trailing newline: all reach the
        # handler and are refused there. A path-like id never reaches it —
        # the slash makes it a different route, which answers 404.
        for bad in ("mn-suetterln", "MN-Suetterlin", "mn-suetterlin%0A", "plain"):
            res = await api.client.request("GET", f"/eigenhand/bestand/{bad}", headers=api.admin_headers())
            assert res.status == 400, (bad, res.status)
        traversal = await api.client.request("GET", "/eigenhand/bestand/../etc", headers=api.admin_headers())
        assert traversal.status == 404


class TestPrinting:
    """The Bogen printer — the same composition the CLI runs, persisted differently."""

    @pytest.mark.asyncio
    async def test_a_stack_never_puts_one_strip_on_two_sheets(self, api: Harness):
        printed = await _print(api, sheets=5, date="2026-08-23")
        assert [s["sheet"] for s in printed["sheets"]] == ["B0001", "B0002", "B0003", "B0004", "B0005"]
        all_strips = [sid for sheet in printed["sheets"] for sid in sheet["strips"]]
        assert len(all_strips) == len(set(all_strips)), "a strip was printed twice in one stack"
        assert (await _bestand(api))["strips"]["unterwegs"] == len(all_strips)

    @pytest.mark.asyncio
    async def test_the_queue_leads_with_what_was_rejected(self, api: Harness):
        first = await _print(api, sheets=1, date="2026-08-23")
        sheet = first["sheets"][0]["sheet"]
        rows = first["sheets"][0]["strips"]
        await _record(
            api,
            [
                _accepted(sid, sheet, index)
                if index != 1
                else {
                    "strip": sid,
                    "fassung": "F01",
                    "sheet": sheet,
                    "row_index": index,
                    "status": "verworfen",
                    "reason": "verschrieben",
                }
                for index, sid in enumerate(rows)
            ],
        )
        # The rejected strip is still `geplant`, so it leads the next Bogen.
        assert (await _bestand(api))["queue"][0] == rows[1]

    @pytest.mark.asyncio
    async def test_the_pdf_is_re_rendered_from_the_stored_layout(self, api: Harness):
        await _print(api, strips=["S0001", "S0002"], date="2026-08-23")
        res = await api.client.request("GET", f"/eigenhand/sheets/{HAND}/B0001/pdf", headers=api.admin_headers())
        assert res.status == 200
        assert res.body.startswith(b"%PDF-1.4")
        assert res.headers.get("cache-control") == "no-store"

        layout_res = await api.client.request(
            "GET", f"/eigenhand/sheets/{HAND}/B0001/layout", headers=api.admin_headers()
        )
        assert layout_res.status == 200
        layout = layout_res.json()
        assert [row["strip"] for row in layout["rows"]] == ["S0001", "S0002"]
        # Byte-identical: the layout IS the contract, the PDF only follows it.
        assert bogen.render_pdf(layout) == res.body

    @pytest.mark.asyncio
    async def test_an_unknown_bogen_is_a_404_and_a_malformed_one_a_400(self, api: Harness):
        missing = await api.client.request("GET", f"/eigenhand/sheets/{HAND}/B0009/pdf", headers=api.admin_headers())
        assert missing.status == 404
        bad = await api.client.request("GET", f"/eigenhand/sheets/{HAND}/Bogen1/pdf", headers=api.admin_headers())
        assert bad.status == 400

    @pytest.mark.asyncio
    async def test_explicit_strips_and_a_stack_are_mutually_exclusive(self, api: Harness):
        res = await api.client.request(
            "POST",
            "/eigenhand/sheets",
            json_body={"hand": HAND, "sheets": 3, "strips": ["S0001"]},
            headers=api.admin_headers(),
        )
        assert res.status == 400

    @pytest.mark.asyncio
    async def test_an_unknown_strip_is_refused_without_printing(self, api: Harness):
        res = await api.client.request(
            "POST", "/eigenhand/sheets", json_body={"hand": HAND, "strips": ["S9999"]}, headers=api.admin_headers()
        )
        assert res.status == 400
        assert (await _bestand(api))["sheets"]["printed"] == 0


class TestLocalPrints:
    """A Bogen printed in the terminal, pushed up by `tools.eigenhand.sync`."""

    @staticmethod
    def _body(strips: list[str], sha: str = "a" * 64) -> dict:
        return {
            "style": "suetterlin",
            "printed_on": "2026-08-23",
            "strips": strips,
            "layout": {"format": 1, "sheet": "B0001", "hand": HAND, "style": "suetterlin", "rows": []},
            "layout_sha256": sha,
        }

    @pytest.mark.asyncio
    async def test_an_imported_bogen_takes_its_id_out_of_circulation(self, api: Harness):
        res = await api.client.request(
            "PUT", f"/eigenhand/sheets/{HAND}/B0001", json_body=self._body(["S0001"]), headers=api.admin_headers()
        )
        assert res.status == 201 and res.json()["imported"] is True
        # The server must not mint B0001 again — the paper on the desk has it.
        printed = await _print(api, strips=["S0002"], date="2026-08-23")
        assert printed["sheets"][0]["sheet"] == "B0002"

    @pytest.mark.asyncio
    async def test_the_same_bogen_again_is_a_no_op_and_a_different_layout_a_conflict(self, api: Harness):
        await api.client.request(
            "PUT", f"/eigenhand/sheets/{HAND}/B0001", json_body=self._body(["S0001"]), headers=api.admin_headers()
        )
        again = await api.client.request(
            "PUT", f"/eigenhand/sheets/{HAND}/B0001", json_body=self._body(["S0001"]), headers=api.admin_headers()
        )
        assert again.status == 201 and again.json()["imported"] is False
        clash = await api.client.request(
            "PUT",
            f"/eigenhand/sheets/{HAND}/B0001",
            json_body=self._body(["S0001"], sha="b" * 64),
            headers=api.admin_headers(),
        )
        assert clash.status == 409


class TestVerdicts:
    """Recording the Siebung: idempotent per row, loud on a contradiction."""

    @pytest.mark.asyncio
    async def test_the_same_verdict_twice_is_skipped_not_duplicated(self, api: Harness):
        await _print(api, strips=["S0001"], date="2026-08-23")
        first = await _record(api, [_accepted("S0001", "B0001", 0)])
        second = await _record(api, [_accepted("S0001", "B0001", 0)])
        assert first.json() == {"hand": HAND, "recorded": 1, "skipped": 0}
        assert second.json() == {"hand": HAND, "recorded": 0, "skipped": 1}
        assert (await _bestand(api))["fassungen"]["angenommen"] == 1

    @pytest.mark.asyncio
    async def test_a_conflicting_verdict_for_one_row_is_refused(self, api: Harness):
        await _print(api, strips=["S0001"], date="2026-08-23")
        await _record(api, [_accepted("S0001", "B0001", 0)])
        clash = await _record(
            api, [{"strip": "S0001", "fassung": "F02", "sheet": "B0001", "row_index": 0, "status": "verworfen"}]
        )
        assert clash.status == 409

    @pytest.mark.asyncio
    async def test_a_malformed_id_is_refused(self, api: Harness):
        res = await _record(api, [_accepted("strip-1", "B0001", 0)])
        assert res.status == 400


class TestAdminGate:
    """The Bestand is the reserved dataset's inventory — reads are gated too."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("GET", "/eigenhand/hands"),
            ("GET", f"/eigenhand/bestand/{HAND}"),
            ("POST", "/eigenhand/sheets"),
            ("GET", f"/eigenhand/sheets/{HAND}/B0001/pdf"),
            ("GET", f"/eigenhand/sheets/{HAND}/B0001/layout"),
            ("POST", "/eigenhand/fassungen"),
        ],
    )
    async def test_every_route_needs_the_admin_header(self, api: Harness, method: str, path: str):
        res = await api.client.request(method, path, json_body={} if method == "POST" else None)
        assert res.status == 401, (path, res.status)

    @pytest.mark.asyncio
    async def test_a_hand_appears_in_the_list_once_it_has_a_bogen(self, api: Harness):
        empty = await api.client.request("GET", "/eigenhand/hands", headers=api.admin_headers())
        assert empty.json() == {"hands": [], "styles": ["kurrent", "suetterlin", "offenbacher"]}
        await _print(api, strips=["S0001"], date="2026-08-23")
        listed = await api.client.request("GET", "/eigenhand/hands", headers=api.admin_headers())
        assert listed.json()["hands"] == [HAND]
