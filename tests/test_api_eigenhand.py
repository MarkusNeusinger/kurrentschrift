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

import base64
import hashlib
import io
from urllib.parse import quote

import pytest
from PIL import Image
from sqlalchemy import inspect

from core.database import EigenhandRepository
from core.eigenhand import bogen
from core.eigenhand.plan import load_plan
from tests.api_harness import Harness


HAND = "mn-suetterlin"
PX_PER_MM = 300.0 / 25.4


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


async def _put_setup(api: Harness, **fields) -> object:
    return await api.client.request("PUT", f"/eigenhand/setups/{HAND}", json_body=fields, headers=api.admin_headers())


def _png(width_px: int, height_px: int, shade: int = 235) -> bytes:
    """A stand-in for a scanned strip — grayscale, the mode ingest files."""
    buffer = io.BytesIO()
    Image.new("L", (width_px, height_px), color=shade).save(buffer, format="PNG")
    return buffer.getvalue()


async def _put_strip(api: Harness, png: bytes, stored: dict, **overrides) -> object:
    strip = stored.get("strip", "S0001")
    body = {
        "sheet": "B0001",
        "row_index": 0,
        "png_base64": base64.b64encode(png).decode(),
        "width_px": stored["width_px"],
        "height_px": stored["height_px"],
        "dpi": 300.0,
        "crop_origin_mm": stored["crop_origin_mm"],
        "sha256": hashlib.sha256(png).hexdigest(),
    } | overrides
    return await api.client.request(
        "PUT", f"/eigenhand/strips/{HAND}/{strip}/F01", json_body=body, headers=api.admin_headers()
    )


async def _store_strip(api: Harness, record: bool = True, upload: bool = True, strip: str = "S0001") -> dict:
    """Print a Bogen, judge its row, and push the strip image — the whole chain.

    The strip's geometry is derived from the STORED layout at 300 DPI, exactly
    the way `tools/eigenhand/ingest.py` cuts it, so the crop arithmetic in the
    endpoint is tested against the same numbers the paper carries.

    `strip` picks which row of the frozen plan to use — the ones carrying a
    non-Latin-1 word or a repeated word are real cases the endpoint has to
    handle, and they only exist in specific strips.
    """
    await _print(api, strips=[strip], date="2026-08-23")
    layout = (
        await api.client.request("GET", f"/eigenhand/sheets/{HAND}/B0001/layout", headers=api.admin_headers())
    ).json()
    row = layout["rows"][0]
    x0, y0, x1, y1 = row["cut_mm"]
    stored = {
        "strip": strip,
        "row": row,
        "crop_origin_mm": [round(x0, 3), round(y0, 3)],
        "width_px": int(round(x1 * PX_PER_MM)) - int(round(x0 * PX_PER_MM)),
        "height_px": int(round(y1 * PX_PER_MM)) - int(round(y0 * PX_PER_MM)),
    }
    if record:
        assert (await _record(api, [_accepted(strip, "B0001", 0)])).status == 200
    stored["png"] = _png(stored["width_px"], stored["height_px"])
    if upload:
        stored["put"] = await _put_strip(api, stored["png"], stored)
    return stored


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
    async def test_a_new_job_starts_at_the_front_again(self, api: Harness):
        # Printed, never written: the next job prints the same strips on new
        # Bögen — "sheets in circulation" is not a queue criterion (owner,
        # 2026-08-26). Only what is belegt drops out.
        first = await _print(api, sheets=2, date="2026-08-26")
        again = await _print(api, sheets=2, date="2026-08-26")
        assert [s["strips"] for s in again["sheets"]] == [s["strips"] for s in first["sheets"]]
        assert [s["sheet"] for s in again["sheets"]] == ["B0003", "B0004"]
        rows = first["sheets"][0]["strips"]
        await _record(api, [_accepted(rows[0], "B0001", 0)])
        third = await _print(api, sheets=1, date="2026-08-26")
        assert third["sheets"][0]["strips"][0] == rows[1], "the belegt strip dropped out, nothing else did"

    @pytest.mark.asyncio
    async def test_a_stack_is_served_as_one_pdf(self, api: Harness):
        printed = await _print(api, sheets=3, date="2026-08-26")
        ids = [s["sheet"] for s in printed["sheets"]]
        res = await api.client.request(
            "GET", f"/eigenhand/stacks/{HAND}/pdf", params={"sheets": ",".join(ids)}, headers=api.admin_headers()
        )
        assert res.status == 200, res.body
        assert res.body.startswith(b"%PDF-1.4") and b"/Count 3 >>" in res.body
        assert res.headers.get("cache-control") == "no-store"
        assert f"{HAND}-{ids[0]}-{ids[-1]}.pdf" in res.headers.get("content-disposition", "")
        layouts = [
            (
                await api.client.request("GET", f"/eigenhand/sheets/{HAND}/{sheet}/layout", headers=api.admin_headers())
            ).json()
            for sheet in ids
        ]
        assert bogen.render_stack_pdf(layouts) == res.body
        missing = await api.client.request(
            "GET", f"/eigenhand/stacks/{HAND}/pdf", params={"sheets": f"{ids[0]},B0099"}, headers=api.admin_headers()
        )
        assert missing.status == 404
        empty = await api.client.request(
            "GET", f"/eigenhand/stacks/{HAND}/pdf", params={"sheets": ""}, headers=api.admin_headers()
        )
        assert empty.status == 400

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
    def _body(strips: list[str], sheet: str = "B0001", hand: str = HAND, date: str = "2026-08-23") -> dict:
        """A real local print: composed exactly the way `tools.eigenhand.sheet` would."""
        composed = bogen.compose_sheet(
            plan=load_plan(),
            kartei={"format": 1, "hand": hand, "style": "suetterlin", "sheets": {}, "strips": {}, "redo": []},
            hand=hand,
            style="suetterlin",
            date=date,
            strips=strips,
        )
        assert composed["sheet"] == sheet  # the empty Kartei mints B0001
        return {
            "style": "suetterlin",
            "printed_on": date,
            "strips": composed["strips"],
            "layout": composed["layout"],
            "layout_sha256": composed["layout_sha256"],
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
        # Same id, genuinely different Bogen (other rows → other layout).
        clash = await api.client.request(
            "PUT", f"/eigenhand/sheets/{HAND}/B0001", json_body=self._body(["S0002"]), headers=api.admin_headers()
        )
        assert clash.status == 409

    @pytest.mark.asyncio
    async def test_a_server_printed_bogen_pulled_and_pushed_back_is_the_same_bogen(self, api: Harness):
        # The documented loop: Admin-Druck → `pull` → `ingest` → `sync`. What
        # `pull` gets back is the stored layout re-serialised by JSONB with its
        # keys REORDERED; `sync` hashes THAT and pushes it back. Same geometry,
        # same Bogen — the first real photo of 2026-08-26 died on a 409 here.
        await _print(api, strips=["S0001"], date="2026-08-26")
        served = (
            await api.client.request("GET", f"/eigenhand/sheets/{HAND}/B0001/layout", headers=api.admin_headers())
        ).json()

        def reordered(value):
            if isinstance(value, dict):
                return {k: reordered(value[k]) for k in reversed(list(value))}
            if isinstance(value, list):
                return [reordered(v) for v in value]
            return value

        layout = reordered(served)
        body = {
            "style": "suetterlin",
            "printed_on": "2026-08-26",
            "strips": ["S0001"],
            "layout": layout,
            "layout_sha256": bogen.layout_digest(layout),
        }
        back = await api.client.request(
            "PUT", f"/eigenhand/sheets/{HAND}/B0001", json_body=body, headers=api.admin_headers()
        )
        assert back.status == 201 and back.json()["imported"] is False, back.body

        # A row written before the digest was order-independent carries the
        # old spelling's hash in its column; the compare must not read it.
        async with api.session_maker() as session:
            row = await EigenhandRepository(session).sheet(HAND, "B0001")
            row.layout_sha256 = "0" * 64
            await session.commit()
        legacy = await api.client.request(
            "PUT", f"/eigenhand/sheets/{HAND}/B0001", json_body=body, headers=api.admin_headers()
        )
        assert legacy.status == 201 and legacy.json()["imported"] is False, legacy.body

    @pytest.mark.asyncio
    async def test_a_layout_naming_another_bogen_is_refused(self, api: Harness):
        # The layout BECOMES the record: the PDF is re-rendered from it and a
        # scan is registered against it, so it has to be this Bogen's.
        body = self._body(["S0001"])
        wrong_sheet = await api.client.request(
            "PUT", f"/eigenhand/sheets/{HAND}/B0002", json_body=body, headers=api.admin_headers()
        )
        assert wrong_sheet.status == 400
        body["layout"] = {**body["layout"], "hand": "xx-kurrent"}
        wrong_hand = await api.client.request(
            "PUT", f"/eigenhand/sheets/{HAND}/B0001", json_body=body, headers=api.admin_headers()
        )
        assert wrong_hand.status == 400
        assert (await _bestand(api))["sheets"]["printed"] == 0

    @pytest.mark.asyncio
    async def test_a_declared_hash_that_does_not_match_the_layout_is_refused(self, api: Harness):
        # The hash decides idempotency vs. conflict, so it is derived here,
        # never taken on the client's word.
        body = self._body(["S0001"]) | {"layout_sha256": "b" * 64}
        res = await api.client.request(
            "PUT", f"/eigenhand/sheets/{HAND}/B0001", json_body=body, headers=api.admin_headers()
        )
        assert res.status == 400

    @pytest.mark.asyncio
    async def test_strips_must_match_the_layouts_rows(self, api: Harness):
        body = self._body(["S0001"]) | {"strips": ["S0002"]}
        res = await api.client.request(
            "PUT", f"/eigenhand/sheets/{HAND}/B0001", json_body=body, headers=api.admin_headers()
        )
        assert res.status == 400


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

    @pytest.mark.asyncio
    async def test_a_verdict_for_a_bogen_nobody_printed_is_refused(self, api: Harness):
        # A Fassung IS a Beleg: it marks a Streifen `belegt` and moves the
        # coverage. A ghost row would conjure training data out of nothing.
        res = await _record(api, [_accepted("S0001", "B0042", 0)])
        assert res.status == 404
        data = await _bestand(api)
        assert data["fassungen"]["angenommen"] == 0 and data["strips"]["belegt"] == 0

    @pytest.mark.asyncio
    async def test_a_verdict_must_name_the_strip_that_row_carried(self, api: Harness):
        await _print(api, strips=["S0001", "S0002"], date="2026-08-23")
        wrong_strip = await _record(api, [_accepted("S0002", "B0001", 0)])
        assert wrong_strip.status == 400
        beyond = await _record(api, [_accepted("S0001", "B0001", 7)])
        assert beyond.status == 400
        assert (await _bestand(api))["fassungen"]["angenommen"] == 0


class TestSetup:
    """The standing nib/ink/paper — typed once, read back by every import."""

    @pytest.mark.asyncio
    async def test_a_setup_is_written_read_back_and_updated_in_place(self, api: Harness):
        written = await _put_setup(api, feder="Brause 361 Steno", tinte="Platinum Carbon Black", papier="Clairalfa 90")
        assert written.status == 200, written.body
        assert written.json()["style"] == "suetterlin"
        assert written.json()["tinte"] == "Platinum Carbon Black"

        read = await api.client.request("GET", f"/eigenhand/setups/{HAND}", headers=api.admin_headers())
        assert read.json()["feder"] == "Brause 361 Steno"

        # An update overwrites: the standing setup answers „what do I reach for
        # now"; the historical truth lives per Fassung.
        await _put_setup(api, feder="Brause Rose", tinte="Platinum Carbon Black")
        again = await api.client.request("GET", f"/eigenhand/setups/{HAND}", headers=api.admin_headers())
        assert again.json()["feder"] == "Brause Rose" and again.json()["papier"] is None
        listed = await api.client.request("GET", "/eigenhand/setups", headers=api.admin_headers())
        assert [row["hand"] for row in listed.json()["setups"]] == [HAND]

    @pytest.mark.asyncio
    async def test_an_unset_hand_says_so_rather_than_inventing_a_setup(self, api: Harness):
        res = await api.client.request("GET", f"/eigenhand/setups/{HAND}", headers=api.admin_headers())
        assert res.status == 404

    @pytest.mark.asyncio
    async def test_a_malformed_hand_id_is_refused(self, api: Harness):
        res = await api.client.request("GET", "/eigenhand/setups/mn-fraktur", headers=api.admin_headers())
        assert res.status == 400


class TestStrips:
    """The written strip in the DB — and any word cut out of it on demand."""

    @pytest.mark.asyncio
    async def test_a_strip_is_stored_listed_and_served_back_byte_identically(self, api: Harness):
        stored = await _store_strip(api)
        assert stored["put"].status == 201, stored["put"].body
        assert stored["put"].json() == {"strip": "S0001", "fassung": "F01", "stored": True}

        listing = await api.client.request("GET", f"/eigenhand/strips/{HAND}", headers=api.admin_headers())
        row = listing.json()["strips"][0]
        assert (row["strip"], row["fassung"], row["sheet"], row["row_index"]) == ("S0001", "F01", "B0001", 0)
        assert row["sha256"] == hashlib.sha256(stored["png"]).hexdigest()
        # The words come from the committed plan — a listing costs no pixels.
        assert row["words"] == load_plan()["strips"]["S0001"]["words"]

        served = await api.client.request("GET", f"/eigenhand/strips/{HAND}/S0001/F01", headers=api.admin_headers())
        assert served.status == 200
        assert served.body == stored["png"]
        assert served.headers["content-type"] == "image/png"
        # Reserved dataset: never in a shared cache, never on the viewer's disk.
        assert served.headers["cache-control"] == "private, no-store"

    @pytest.mark.asyncio
    async def test_a_word_crop_is_cut_from_the_layout_without_extra_storage(self, api: Harness):
        stored = await _store_strip(api)
        word = stored["row"]["boxes"][1]["word"]
        cut = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/S0001/F01", params={"wort": word}, headers=api.admin_headers()
        )
        assert cut.status == 200, cut.body
        with Image.open(io.BytesIO(cut.body)) as image:
            width, height = image.size
        assert height == stored["height_px"]  # full strip height, on purpose
        assert 0 < width < stored["width_px"]
        by_index = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/S0001/F01", params={"box": 1}, headers=api.admin_headers()
        )
        assert by_index.body == cut.body

    @pytest.mark.asyncio
    async def test_a_word_outside_latin_1_is_served_not_crashed(self, api: Harness):
        """Header values are Latin-1, and the frozen plan is not.

        `„wohl“` and `don’t` are in the committed strip plan, so this is the
        normal path for four of its strips, not an edge case — and it used to
        raise UnicodeEncodeError inside the response, i.e. a 500 (review, #410).
        """
        stored = await _store_strip(api, strip="S0020")
        word = next(box["word"] for box in stored["row"]["boxes"] if any(ord(c) > 255 for c in box["word"]))
        res = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/S0020/F01", params={"wort": word}, headers=api.admin_headers()
        )
        assert res.status == 200, res.body
        disposition = res.headers["content-disposition"]
        # The plain filename is ASCII so the header encodes at all; the real
        # name rides along RFC 5987, which is what browsers actually use.
        disposition.encode("latin-1")
        assert "filename*=UTF-8''" in disposition
        assert quote(word, safe="") in disposition

    @pytest.mark.asyncio
    async def test_a_word_that_appears_twice_is_reachable_by_index(self, api: Harness):
        # `find_box` resolves a repeated word to its FIRST box by design — the
        # index is the disambiguator, and eight strips of the plan need it.
        stored = await _store_strip(api, strip="S0101")
        words = [box["word"] for box in stored["row"]["boxes"]]
        assert words[0] == words[1], "S0101 is expected to carry its first word twice"

        async def cut(**params):
            res = await api.client.request(
                "GET", f"/eigenhand/strips/{HAND}/S0101/F01", params=params, headers=api.admin_headers()
            )
            assert res.status == 200, res.body
            return res.body

        first, second, by_word = await cut(box=0), await cut(box=1), await cut(wort=words[1])
        assert first != second, "the two occurrences must be different rectangles"
        assert by_word == first, "by text the API answers with the first box — that is the documented behaviour"

    @pytest.mark.asyncio
    async def test_a_word_the_row_does_not_carry_is_refused(self, api: Harness):
        await _store_strip(api)
        res = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/S0001/F01", params={"wort": "nichtdrin"}, headers=api.admin_headers()
        )
        assert res.status == 400

    @pytest.mark.asyncio
    async def test_the_same_bytes_again_are_a_no_op_and_different_bytes_a_conflict(self, api: Harness):
        stored = await _store_strip(api)
        again = await _put_strip(api, stored["png"], stored)
        assert again.status == 201 and again.json()["stored"] is False

        other = _png(stored["width_px"], stored["height_px"], shade=120)
        clash = await _put_strip(api, other, stored)
        assert clash.status == 409
        served = await api.client.request("GET", f"/eigenhand/strips/{HAND}/S0001/F01", headers=api.admin_headers())
        assert served.body == stored["png"]

    @pytest.mark.asyncio
    async def test_the_no_op_check_never_reads_the_stored_bytes(self, api: Harness):
        """A re-run of a sync must not pull every stored PNG back out of the DB.

        The check compares hashes, so it has no use for the pixels — and a hand
        with a few waves behind it would otherwise move tens of megabytes for
        nothing on every repeat push (Copilot review, PR #410).
        """
        stored = await _store_strip(api)
        async with api.session_maker() as session:
            row = await EigenhandRepository(session).strip_meta(HAND, "S0001", "F01")
            assert row is not None and row.sha256 == hashlib.sha256(stored["png"]).hexdigest()
            # The blob is deferred: it is not in the loaded state, and touching
            # it in this async session would have to lazy-load (which raises).
            assert "png" not in inspect(row).dict

        again = await _put_strip(api, stored["png"], stored)
        assert again.status == 201 and again.json()["stored"] is False

    @pytest.mark.asyncio
    async def test_pixels_without_a_recorded_fassung_are_refused(self, api: Harness):
        # Same „no ghost rows" rule as the verdicts, one step further: an image
        # nothing in the Bestand accounts for would be evidence out of nowhere.
        stored = await _store_strip(api, record=False)
        assert stored["put"].status == 404
        listing = await api.client.request("GET", f"/eigenhand/strips/{HAND}", headers=api.admin_headers())
        assert listing.json()["strips"] == []

    @pytest.mark.asyncio
    async def test_a_declared_hash_that_does_not_match_the_bytes_is_refused(self, api: Harness):
        # sha256 is the archive's identity for this file — a wrong one would
        # break the restore check silently.
        stored = await _store_strip(api, record=True, upload=False)
        res = await _put_strip(api, stored["png"], stored, sha256="c" * 64)
        assert res.status == 400

    @pytest.mark.asyncio
    async def test_a_hash_that_contradicts_the_recorded_fassung_is_refused(self, api: Harness):
        await _print(api, strips=["S0001"], date="2026-08-23")
        verdict = _accepted("S0001", "B0001", 0) | {"png_sha256": "d" * 64}
        assert (await _record(api, [verdict])).status == 200
        stored = await _store_strip(api, record=False, upload=False)
        res = await _put_strip(api, stored["png"], stored)
        assert res.status == 409

    @pytest.mark.asyncio
    async def test_bytes_that_are_not_a_png_are_refused(self, api: Harness):
        stored = await _store_strip(api, record=True, upload=False)
        res = await _put_strip(api, b"this is not a PNG", stored)
        assert res.status == 400

    @pytest.mark.asyncio
    async def test_declared_dimensions_must_match_the_image(self, api: Harness):
        # The stored size IS the crop's scale — a listing that disagrees with
        # the pixels would cut every word crop in the wrong place, silently.
        stored = await _store_strip(api, record=True, upload=False)
        res = await _put_strip(api, stored["png"], {**stored, "width_px": stored["width_px"] + 17})
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
            ("GET", "/eigenhand/setups"),
            ("GET", f"/eigenhand/setups/{HAND}"),
            ("PUT", f"/eigenhand/setups/{HAND}"),
            ("GET", f"/eigenhand/strips/{HAND}"),
            ("GET", f"/eigenhand/strips/{HAND}/S0001/F01"),
            ("PUT", f"/eigenhand/strips/{HAND}/S0001/F01"),
        ],
    )
    async def test_every_route_needs_the_admin_header(self, api: Harness, method: str, path: str):
        res = await api.client.request(method, path, json_body={} if method in ("POST", "PUT") else None)
        assert res.status == 401, (path, res.status)

    @pytest.mark.asyncio
    async def test_a_hand_appears_in_the_list_once_it_has_a_bogen(self, api: Harness):
        empty = await api.client.request("GET", "/eigenhand/hands", headers=api.admin_headers())
        assert empty.json() == {"hands": [], "styles": ["kurrent", "suetterlin", "offenbacher"]}
        await _print(api, strips=["S0001"], date="2026-08-23")
        listed = await api.client.request("GET", "/eigenhand/hands", headers=api.admin_headers())
        assert listed.json()["hands"] == [HAND]
