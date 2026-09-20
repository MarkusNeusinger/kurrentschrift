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
import json
from urllib.parse import quote

import numpy as np
import pytest
from PIL import Image
from sqlalchemy import inspect, update

from core.database import EigenhandRepository, EigenhandStrip
from core.eigenhand import bogen
from core.eigenhand.befund import BEFUND_FORMAT, body_runs_expected
from core.eigenhand.flecken import FLECKEN_FORMAT
from core.eigenhand.pfad import PFAD_FORMAT, SUPPORTED_FORMATS, frame_for_box
from core.eigenhand.plan import load_plan
from tests.api_harness import Harness


HAND = "mn-suetterlin"
PX_PER_MM = 300.0 / 25.4
# What `eigenhand_strips.pfade_format` says about a Fassung nobody has followed:
# the column's server default (migration 0032). Deliberately NOT `PFAD_FORMAT` —
# that number moves with every release of the lockstep, and the rows already in
# the database do not move with it. The two were the same until 2026-09-20.
UNFOLLOWED_FORMAT = 1


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
        # Both denominators come from the committed plan — a new wave (append-never)
        # grows them together; pinning a literal here would break on every wave.
        assert data["strips"] == {
            "total": len(plan["strips"]),
            "belegt": 0,
            "unterwegs": 0,
            "geplant": len(plan["strips"]),
        }
        assert data["fassungen"]["angenommen"] == 0
        # Capitals, digits and signs are part of the answer (owner, 2026-08-22).
        for bucket in ("klein", "gross", "ligatur", "ziffer", "zeichen"):
            layer = data["glyphs"][bucket]
            assert layer["possible"] > 0, bucket
            assert layer["covered"] == 0 and layer["belege"] == 0
            assert len(layer["keys"]) == layer["possible"]
        assert data["glyphs"]["ziffer"]["possible"] == 10
        assert data["joins"]["possible"] > 100 and data["joins"]["covered"] == 0
        # No Übergangsraum row pushed yet — no weighted Quoten, and it says so.
        assert data["quoten"] is None


class TestFaellig:
    """The due local steps ride on the Bestand — the Übergabekarten's data.

    A field on the read that is already made for every one of the four
    Unteransichten, rather than a route of its own: the subject is the same and
    a second request would have to be kept in sync with every reload of this
    one. What is pinned here is that the rules fire through HTTP the way
    `tests/test_eigenhand_faellig.py` pins them in the pure layer, and that the
    two extra reads it costs stay cheap.
    """

    @pytest.mark.asyncio
    async def test_an_untouched_hand_is_only_asked_for_the_weight_table(self, api: Harness):
        # Nothing printed, nothing written, no setup row: the one thing the
        # server can see missing is the Übergangsraum.
        due = (await _bestand(api))["faellig"]
        assert [row["id"] for row in due] == ["universe_push"]
        assert due[0]["befehl"] == "uv run python -m tools.eigenhand.universe --push"

    @pytest.mark.asyncio
    async def test_a_printed_bogen_and_a_missing_image_become_cards_and_clear_again(self, api: Harness):
        await _put_universe(api, _universe())
        printed = await _print(api, strips=["S0001", "S0002"], date="2026-09-19")
        sheet = printed["sheets"][0]["sheet"]

        # Printed, nobody judged it: the oldest outstanding Bogen, by name.
        [bogen_card] = (await _bestand(api))["faellig"]
        assert bogen_card["id"] == "bogen_pull"
        assert bogen_card["params"] == {"hand": HAND, "sheet": sheet, "offen": 2, "weitere": 0}
        assert f"--sheet {sheet}" in bogen_card["befehl"]

        # Judged, but the pixels are still in the private archive.
        await _record(api, [_accepted(sid, sheet, index) for index, sid in enumerate(printed["sheets"][0]["strips"])])
        [strip_card] = (await _bestand(api))["faellig"]
        assert strip_card["id"] == "sync_streifen" and strip_card["params"]["ohne_bild"] == 2

    @pytest.mark.asyncio
    async def test_a_stored_image_takes_its_fassung_out_of_the_due_list(self, api: Harness):
        await _put_universe(api, _universe())
        await _store_strip(api)
        # Printed, judged, image up — one strip of a one-strip sheet, so
        # nothing about this hand is waiting at the machine any more.
        assert (await _bestand(api))["faellig"] == []

    @pytest.mark.asyncio
    async def test_a_saved_setup_is_due_until_the_hand_has_written_something(self, api: Harness):
        await _put_universe(api, _universe())
        assert (await _put_setup(api, feder="Brause 361", tinte="Carbon Black")).status == 200
        [card] = (await _bestand(api))["faellig"]
        assert card["id"] == "setup_pull" and card["befehl"].endswith(f"--hand {HAND} --pull")

        await _store_strip(api)
        assert [row["id"] for row in (await _bestand(api))["faellig"]] == []

    @pytest.mark.asyncio
    async def test_the_extra_reads_load_neither_the_pixels_nor_the_paths(self, api: Harness, monkeypatch):
        """The busiest admin read must not start dragging blobs along.

        The due list needs to know WHICH strips are stored, never what is in
        them: `strips_of` defers the PNG and the `pfade` column, and the two
        methods that do load them are made to fail here — if the Bestand read
        ever reaches for one, this test is what says so.
        """
        await _put_universe(api, _universe())
        await _store_strip(api)

        async def refuse(*args, **kwargs):
            raise AssertionError("the Bestand read pulled a strip blob")

        monkeypatch.setattr(EigenhandRepository, "strip", refuse)
        monkeypatch.setattr(EigenhandRepository, "strip_pfade", refuse)
        assert (await _bestand(api))["faellig"] == []

        async with api.session_maker() as session:
            rows = await EigenhandRepository(session).strips_of(HAND)
            assert rows, "the stored strip should be listed"
            for row in rows:
                loaded = inspect(row).dict
                assert "png" not in loaded and "pfade" not in loaded


def _universe(items: dict[str, float] | None = None, **overrides) -> dict:
    """A tiny Soll universe in the shape `tools.eigenhand.universe --push` sends."""
    return {
        "format": 1,
        "en_weight": 0.25,
        "min_count": 100,
        "min_word_len": 2,
        "corpora": {"de_50k.txt": "a" * 64, "en_50k.txt": "b" * 64},
        "words_used": {"de": 3, "en": 2},
        "corpus_items": 2,
        "pool_sha256": "c" * 64,
        "items": items if items is not None else {"e@medial": 100.0, "l>e": 40.0, "Z@initial": 0.0},
    } | overrides


async def _put_universe(api: Harness, body: dict) -> object:
    return await api.client.request("PUT", "/eigenhand/uebergangsraum", json_body=body, headers=api.admin_headers())


class TestUebergangsraum:
    """The Soll universe in the DB (author's decision 2026-08-25): one row, whole, idempotent."""

    @pytest.mark.asyncio
    async def test_the_table_is_stored_served_back_and_idempotent(self, api: Harness):
        first = await _put_universe(api, _universe())
        assert first.status == 200, first.body
        assert first.json()["stored"] is True and first.json()["replaced"] is False
        again = await _put_universe(api, _universe())
        assert again.json() == {**first.json(), "stored": False}  # same build → no-op, same hash
        res = await api.client.request("GET", "/eigenhand/uebergangsraum", headers=api.admin_headers())
        assert res.status == 200
        data = res.json()
        assert data["items"] == _universe()["items"] and data["item_count"] == 3
        assert data["corpora"]["de_50k.txt"] == "a" * 64 and data["sha256"] == first.json()["sha256"]

    @pytest.mark.asyncio
    async def test_a_different_build_replaces_the_row_whole(self, api: Harness):
        await _put_universe(api, _universe())
        res = await _put_universe(api, _universe({"e@medial": 200.0}, corpus_items=1))
        assert res.json()["stored"] is True and res.json()["replaced"] is True
        data = (await api.client.request("GET", "/eigenhand/uebergangsraum", headers=api.admin_headers())).json()
        # Whole, not merged: the old items are gone, the new provenance stands.
        assert data["items"] == {"e@medial": 200.0} and data["corpus_items"] == 1

    @pytest.mark.asyncio
    async def test_before_the_first_push_the_row_is_a_404_with_the_command(self, api: Harness):
        res = await api.client.request("GET", "/eigenhand/uebergangsraum", headers=api.admin_headers())
        assert res.status == 404 and "universe --push" in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_a_malformed_item_key_or_an_empty_table_is_refused(self, api: Harness):
        bad = await _put_universe(api, _universe({"e medial": 1.0}))
        assert bad.status == 400 and "coverage item key" in bad.json()["detail"]
        empty = await _put_universe(api, _universe({}))
        assert empty.status == 422
        # One universe only: a row under another name would be unreachable.
        other = await _put_universe(api, _universe(name="other"))
        assert other.status == 422

    @pytest.mark.asyncio
    async def test_the_stored_weights_light_up_the_quoten_and_weight_the_queue(self, api: Harness):
        # The same derivation the terminal uses: with the row present, the
        # Bestand carries the Quoten over the stored item set, and the print
        # queue's repetition tier ranks by weighted Soll gain.
        assert (await _bestand(api))["quoten"] is None
        await _put_universe(api, _universe({"e@medial": 100.0, "l>e": 40.0, "Z@initial": 0.0}))
        data = await _bestand(api)
        quoten = data["quoten"]
        assert quoten is not None and quoten["items"] == 3
        assert quoten["erstbeleg"] == 0 and quoten["erstbeleg_weighted"] == 0.0
        assert quoten["soll_belege"] >= 3 * 3  # every item at least the floor target
        printed = await _print(api, sheets=1, date="2026-08-26")
        sheet, rows = printed["sheets"][0]["sheet"], printed["sheets"][0]["strips"]
        await _record(api, [_accepted(sid, sheet, index) for index, sid in enumerate(rows)])
        after = await _bestand(api)
        assert after["quoten"]["erstbeleg"] >= 1, "an accepted row with an e moves e@medial"
        assert 0.0 < after["quoten"]["erstbeleg_weighted"] <= 1.0

    @pytest.mark.asyncio
    async def test_a_befund_from_another_format_is_refused_not_stored(self, api: Harness):
        """The SERVER holds the contract — a tool can always be an old copy.

        The measurement is computed locally and interpreted here, so a Befund
        from a different format would be read under semantics it was never
        measured with. Same refusal as the Lesart fold check, and the row must
        not exist afterwards: a stored measurement carries no second chance.
        """
        printed = await _print(api, strips=["S0001"], date="2026-08-23")
        sheet = printed["sheets"][0]["sheet"]
        stale = {**_accepted("S0001", sheet, 0), "befund": {"format": BEFUND_FORMAT + 1, "woerter": []}}
        assert (await _record(api, [stale])).status == 409
        assert (await _bestand(api))["fassungen"]["angenommen"] == 0

        current = {**_accepted("S0001", sheet, 0), "befund": {"format": BEFUND_FORMAT, "woerter": []}}
        assert (await _record(api, [current])).status == 200
        assert (await _bestand(api))["fassungen"]["angenommen"] == 1

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

        # A Kartei written before the change declares the OLD spelling's hash
        # (insertion order of its layout.json). Accepted too — a rollout must
        # not strand a local Kartei on a 400.
        old_spelling = hashlib.sha256((json.dumps(layout, ensure_ascii=False, indent=1) + "\n").encode()).hexdigest()
        assert old_spelling != body["layout_sha256"]
        older = await api.client.request(
            "PUT",
            f"/eigenhand/sheets/{HAND}/B0001",
            json_body=body | {"layout_sha256": old_spelling},
            headers=api.admin_headers(),
        )
        assert older.status == 201 and older.json()["imported"] is False, older.body

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
        assert first.json() == {"hand": HAND, "recorded": 1, "skipped": 0, "flecken_filled": 0}
        assert second.json() == {"hand": HAND, "recorded": 0, "skipped": 1, "flecken_filled": 0}
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
    async def test_the_listing_states_each_box_with_its_items_and_filters_by_word_and_item(self, api: Harness):
        from core.eigenhand import coverage
        from core.eigenhand.plan import shaping_form_of

        stored = await _store_strip(api)
        plan = load_plan()
        words = plan["strips"]["S0001"]["words"]

        async def listed(**params) -> list[str]:
            res = await api.client.request(
                "GET", f"/eigenhand/strips/{HAND}", params=params, headers=api.admin_headers()
            )
            assert res.status == 200, res.body
            return [row["strip"] for row in res.json()["strips"]]

        listing = await api.client.request("GET", f"/eigenhand/strips/{HAND}", headers=api.admin_headers())
        boxes = listing.json()["strips"][0]["boxes"]
        # Every box: its index (the crop's address), its word, the SAME items
        # the Bestand counts for it, and where it sits in the stored strip.
        assert [{k: v for k, v in box.items() if k != "rect_px"} for box in boxes] == [
            {"index": i, "word": w, "items": coverage.word_items(shaping_form_of(plan, w))} for i, w in enumerate(words)
        ]
        # The rectangles are the word crop's own, in strip pixels: inside the
        # strip, ascending, and each the full height — a word crop keeps the
        # whole band (`core.eigenhand.crop`).
        rects = [box["rect_px"] for box in boxes]
        assert all(r is not None for r in rects)
        assert [r[0] for r in rects] == sorted(r[0] for r in rects)
        assert all(0 <= r[0] < r[2] <= stored["width_px"] and r[1] == 0 and r[3] == stored["height_px"] for r in rects)

        # A word: case-insensitive substring — the search box's contract.
        fragment = words[1][1:3]
        assert await listed(wort=fragment.upper()) == ["S0001"]
        assert await listed(wort="qqqqqq") == []

        # An item: a bare glyph key stands for every position; a positioned
        # key and a join match exactly; a bare key never matches a join.
        items = [item for box in boxes for item in box["items"]]
        positioned = next(item for item in items if "@" in item)
        join = next(item for item in items if ">" in item)
        assert await listed(item=positioned.split("@")[0]) == ["S0001"]
        assert await listed(item=positioned) == ["S0001"]
        assert await listed(item=join) == ["S0001"]
        assert await listed(item=join.split(">")[0].replace("-", "") + "0x0") == []
        assert await listed(item="x0x0@final") == []
        # Both at once narrow, never widen.
        assert await listed(wort=fragment, item=join) == ["S0001"]
        assert await listed(wort="qqqqqq", item=join) == []

        bad = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}", params={"item": "a b"}, headers=api.admin_headers()
        )
        assert bad.status == 400

    @pytest.mark.asyncio
    async def test_a_colour_strip_is_stored_as_it_is_and_served_without_its_rulings_on_request(self, api: Harness):
        # Author's decision 2026-08-27: strips keep their colour; dropping the
        # rulings is a view computed on request, never what gets stored.
        stored = await _store_strip(api, upload=False)
        width, height = stored["width_px"], stored["height_px"]
        pixels = np.full((height, width, 3), 235, dtype=np.uint8)
        ruling_rows = (height // 3, height // 2)
        for row in ruling_rows:
            pixels[row : row + 3, :, :] = (150, 225, 235)  # pale cyan
        pixels[:, 200:206, :] = (30, 30, 30)  # a stroke crossing both rulings
        buffer = io.BytesIO()
        Image.fromarray(pixels, mode="RGB").save(buffer, format="PNG")
        rgb = buffer.getvalue()
        put = await _put_strip(api, rgb, stored)
        assert put.status == 201, put.body

        whole = await api.client.request("GET", f"/eigenhand/strips/{HAND}/S0001/F01", headers=api.admin_headers())
        assert whole.body == rgb  # stored and served as uploaded — colour included

        view = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/S0001/F01", params={"lineatur": "ohne"}, headers=api.admin_headers()
        )
        assert view.status == 200, view.body
        assert view.headers["cache-control"] == "private, no-store"
        with Image.open(io.BytesIO(view.body)) as image:
            assert image.mode == "L" and image.size == (width, height)
            plane = np.asarray(image, dtype=np.int32)
        assert plane[ruling_rows[0] + 1, 20] >= 230  # the ruling is paper now
        assert plane[ruling_rows[0] + 1, 203] <= 40  # the ink crossing it is still ink
        assert plane[5, 20] == 235  # paper untouched

        # The view composes with a word cut, and a malformed value is refused.
        cut = await api.client.request(
            "GET",
            f"/eigenhand/strips/{HAND}/S0001/F01",
            params={"lineatur": "ohne", "box": 1},
            headers=api.admin_headers(),
        )
        with Image.open(io.BytesIO(cut.body)) as image:
            assert image.mode == "L" and image.size[1] == height and image.size[0] < width
        bad = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/S0001/F01", params={"lineatur": "weg"}, headers=api.admin_headers()
        )
        assert bad.status == 400

    @pytest.mark.asyncio
    async def test_a_greyscale_strip_has_no_rulings_to_drop_and_comes_back_as_it_is(self, api: Harness):
        stored = await _store_strip(api)
        view = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/S0001/F01", params={"lineatur": "ohne"}, headers=api.admin_headers()
        )
        assert view.status == 200 and view.body == stored["png"]

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
    async def test_a_strip_over_the_size_limit_is_refused_with_413(self, api: Harness, monkeypatch):
        """The one bound on how much a single request can push into the DB.

        `MAX_STRIP_BYTES` is 8 MiB in production; the limit is lowered here so
        the test can cross it with a real PNG instead of shipping 11 MB of
        base64 through the suite. The refusal must be 413 — a size problem is
        not a malformed request — and must name both numbers, because the tool
        on the other end (`tools.eigenhand.sync --mit-streifen`) prints it.
        """
        import api.routers.eigenhand as eigenhand_router

        stored = await _store_strip(api, record=True, upload=False)
        monkeypatch.setattr(eigenhand_router, "MAX_STRIP_BYTES", len(stored["png"]) - 1)
        res = await _put_strip(api, stored["png"], stored)
        assert res.status == 413
        assert str(len(stored["png"])) in res.json()["detail"]

        # One byte of headroom and the same request goes through — so the 413
        # is the limit talking, not some other refusal upstream of it.
        monkeypatch.setattr(eigenhand_router, "MAX_STRIP_BYTES", len(stored["png"]))
        assert (await _put_strip(api, stored["png"], stored)).status == 201

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


class TestFleckenmaske:
    """The printer's specks: stored as circles, painted out on read, never baked in."""

    @staticmethod
    async def _patch(api: Harness, circles: list[dict], strip: str = "S0001", fassung: str = "F01"):
        return await api.client.request(
            "PATCH",
            f"/eigenhand/strips/{HAND}/{strip}/{fassung}/flecken",
            json_body={"flecken": circles},
            headers=api.admin_headers(),
        )

    @pytest.mark.asyncio
    async def test_a_mask_is_saved_listed_and_replaced_whole(self, api: Harness):
        await _store_strip(api)
        saved = await self._patch(api, [{"x_mm": 30.0, "y_mm": 8.0, "r_mm": 0.6, "quelle": "hand"}])
        assert saved.status == 200, saved.body
        assert saved.json()["flecken"] == [{"x_mm": 30.0, "y_mm": 8.0, "r_mm": 0.6, "quelle": "hand"}]

        listing = await api.client.request("GET", f"/eigenhand/strips/{HAND}", headers=api.admin_headers())
        assert listing.json()["strips"][0]["flecken"] == saved.json()["flecken"]

        # A full replace, because the brush both adds and removes: an empty
        # list is „nothing to erase", not „leave what is there".
        cleared = await self._patch(api, [])
        assert cleared.status == 200 and cleared.json()["flecken"] == []
        listing = await api.client.request("GET", f"/eigenhand/strips/{HAND}", headers=api.admin_headers())
        assert listing.json()["strips"][0]["flecken"] == []

    @pytest.mark.asyncio
    async def test_a_fassung_nobody_judged_has_no_mask_to_hold(self, api: Harness):
        await _print(api, strips=["S0001"], date="2026-08-23")
        res = await self._patch(api, [{"x_mm": 1.0, "y_mm": 1.0, "r_mm": 0.3}])
        assert res.status == 404

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "circle",
        [
            {"x_mm": 9000.0, "y_mm": 8.0, "r_mm": 0.6},  # off the strip
            {"x_mm": 30.0, "y_mm": 900.0, "r_mm": 0.6},
            {"x_mm": 30.0, "y_mm": 8.0, "r_mm": 50.0},  # far past the brush
        ],
    )
    async def test_a_circle_outside_the_strip_is_refused(self, api: Harness, circle: dict):
        await _store_strip(api)
        res = await self._patch(api, [circle])
        assert res.status == 422, res.body

    @pytest.mark.asyncio
    async def test_the_image_comes_masked_by_default_and_raw_on_request(self, api: Harness):
        """The specks go without the filed bytes moving — `flecken=mit` proves it."""
        stored = await _store_strip(api, upload=False)
        width, height = stored["width_px"], stored["height_px"]
        pixels = np.full((height, width), 235, dtype=np.uint8)
        speck = (height // 2, 900)
        pixels[speck[0] - 3 : speck[0] + 3, speck[1] - 3 : speck[1] + 3] = 10
        buffer = io.BytesIO()
        Image.fromarray(pixels, mode="L").save(buffer, format="PNG")
        raw = buffer.getvalue()
        assert (await _put_strip(api, raw, stored)).status == 201

        # The mask speaks the CROP's millimetres — pixel over scale, with the
        # page origin (`crop_origin_mm`) playing no part at all.
        circle = {"x_mm": speck[1] / PX_PER_MM, "y_mm": speck[0] / PX_PER_MM, "r_mm": 0.6, "quelle": "auto"}
        assert (await self._patch(api, [circle])).status == 200

        masked = await api.client.request("GET", f"/eigenhand/strips/{HAND}/S0001/F01", headers=api.admin_headers())
        assert masked.status == 200
        with Image.open(io.BytesIO(masked.body)) as image:
            plane = np.asarray(image, dtype=np.int32)
        assert plane[speck[0], speck[1]] > 200  # the speck is paper now
        assert plane.shape == (height, width)

        rohe = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/S0001/F01", params={"flecken": "mit"}, headers=api.admin_headers()
        )
        assert rohe.body == raw  # the filed bytes, untouched

        bad = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/S0001/F01", params={"flecken": "weg"}, headers=api.admin_headers()
        )
        assert bad.status == 400

    @staticmethod
    def _pushed(circles: list[dict] | None, **overrides) -> dict:
        """A verdict carrying a mask, with the format marker the sync sends."""
        return {**_accepted("S0001", "B0001", 0), "flecken": circles, "flecken_format": FLECKEN_FORMAT, **overrides}

    @pytest.mark.asyncio
    async def test_a_pushed_mask_fills_a_row_that_has_none_and_never_overwrites_one(self, api: Harness):
        """The sync direction: up to fill, never over. The workbench is the master."""
        await _print(api, strips=["S0001"], date="2026-08-23")
        auto = [{"x_mm": 30.0, "y_mm": 8.0, "r_mm": 0.4, "quelle": "auto"}]
        first = await _record(api, [self._pushed(auto)])
        assert first.json() == {"hand": HAND, "recorded": 1, "skipped": 0, "flecken_filled": 0}
        listing = await api.client.request("GET", f"/eigenhand/archive/{HAND}", headers=api.admin_headers())
        assert listing.json()["fassungen"][0]["flecken"] == auto

        by_hand = [{"x_mm": 44.0, "y_mm": 9.0, "r_mm": 0.5, "quelle": "hand"}]
        assert (await self._patch(api, by_hand)).status == 200
        again = await _record(api, [self._pushed(auto)])
        assert again.json()["flecken_filled"] == 0
        archive = await api.client.request("GET", f"/eigenhand/archive/{HAND}", headers=api.admin_headers())
        assert archive.json()["fassungen"][0]["flecken"] == by_hand

    @pytest.mark.asyncio
    async def test_a_row_recorded_before_the_maske_existed_gains_one(self, api: Harness):
        await _print(api, strips=["S0001"], date="2026-08-23")
        assert (await _record(api, [_accepted("S0001", "B0001", 0)])).status == 200
        auto = [{"x_mm": 30.0, "y_mm": 8.0, "r_mm": 0.4, "quelle": "auto"}]
        again = await _record(api, [self._pushed(auto)])
        assert again.json() == {"hand": HAND, "recorded": 0, "skipped": 1, "flecken_filled": 1}
        archive = await api.client.request("GET", f"/eigenhand/archive/{HAND}", headers=api.admin_headers())
        assert archive.json()["fassungen"][0]["flecken"] == auto

    @pytest.mark.asyncio
    async def test_an_empty_mask_is_a_reading_and_closes_the_row_to_the_auto_list(self, api: Harness):
        """`[]` is „looked, nothing to erase" — a restore of it must stick."""
        await _print(api, strips=["S0001"], date="2026-08-23")
        assert (await _record(api, [self._pushed([])])).json()["recorded"] == 1
        archive = await api.client.request("GET", f"/eigenhand/archive/{HAND}", headers=api.admin_headers())
        assert archive.json()["fassungen"][0]["flecken"] == []
        stale = [{"x_mm": 30.0, "y_mm": 8.0, "r_mm": 0.4, "quelle": "auto"}]
        assert (await _record(api, [self._pushed(stale)])).json()["flecken_filled"] == 0
        archive = await api.client.request("GET", f"/eigenhand/archive/{HAND}", headers=api.admin_headers())
        assert archive.json()["fassungen"][0]["flecken"] == []

    @pytest.mark.asyncio
    async def test_a_pushed_mask_is_bounded_by_the_printed_schnittband(self, api: Harness):
        """The same check on both write paths — the brush's and the sync's."""
        await _print(api, strips=["S0001"], date="2026-08-23")
        far_out = [{"x_mm": 900.0, "y_mm": 8.0, "r_mm": 0.4, "quelle": "auto"}]
        res = await _record(api, [self._pushed(far_out)])
        assert res.status == 422, res.body

    @pytest.mark.asyncio
    async def test_a_mask_from_another_detector_format_is_refused(self, api: Harness):
        await _print(api, strips=["S0001"], date="2026-08-23")
        auto = [{"x_mm": 30.0, "y_mm": 8.0, "r_mm": 0.4, "quelle": "auto"}]
        res = await _record(api, [self._pushed(auto, flecken_format=FLECKEN_FORMAT + 1)])
        assert res.status == 409, res.body

    @pytest.mark.asyncio
    async def test_a_hand_edit_re_measures_the_befund_against_the_new_mask(self, api: Harness):
        """A speck is not the writer's ink — erasing one must not leave a stale reading."""
        stored = await _store_strip(api, upload=False)
        width, height = stored["width_px"], stored["height_px"]
        pixels = np.full((height, width), 235, dtype=np.uint8)
        band = stored["row"]["band_mm"]
        origin = stored["crop_origin_mm"]
        box = stored["row"]["boxes"][0]

        # A stroke in the first word box, and a speck a good way to its right.
        def px(mm: float, axis: int) -> int:
            return int(round((mm - origin[axis]) * PX_PER_MM))

        pixels[
            px(band["waist"], 1) : px(band["baseline"], 1), px(box["x0_mm"] + 3.0, 0) : px(box["x0_mm"] + 3.4, 0)
        ] = 20
        speck_x, speck_y = px(box["x0_mm"] + 20.0, 0), px((band["waist"] + band["baseline"]) / 2, 1)
        pixels[speck_y - 3 : speck_y + 3, speck_x - 3 : speck_x + 3] = 20
        buffer = io.BytesIO()
        Image.fromarray(pixels, mode="L").save(buffer, format="PNG")
        assert (await _put_strip(api, buffer.getvalue(), stored)).status == 201

        async def befund() -> dict:
            res = await api.client.request("GET", f"/eigenhand/archive/{HAND}", headers=api.admin_headers())
            return res.json()["fassungen"][0]["befund"]

        # An empty mask is still a mask: it triggers the same reading, and with
        # the speck standing the box reads as TWO body runs.
        assert (await self._patch(api, [])).status == 200
        with_speck = await befund()
        assert with_speck is not None and with_speck["format"] == BEFUND_FORMAT
        assert with_speck["woerter"][0]["teile"]["koerper"] == 2

        erased = [{"x_mm": speck_x / PX_PER_MM, "y_mm": speck_y / PX_PER_MM, "r_mm": 0.6, "quelle": "hand"}]
        assert (await self._patch(api, erased)).status == 200
        # Erased, the same strip is one stroke again — the reading followed the
        # mask instead of going stale.
        assert (await befund())["woerter"][0]["teile"]["koerper"] == 1


class TestStreifenPfad:
    """The followed pen path of a written word — stored as data beside the image."""

    @staticmethod
    def _path(stored: dict, box_index: int = 0, **overrides) -> dict:
        """A path whose frame really is this strip's, taken off the printed row."""
        frame = frame_for_box(
            stored["row"], stored["crop_origin_mm"], stored["width_px"], stored["height_px"], box_index
        )
        return {
            "box_index": box_index,
            "word": frame["word"],
            "strokes": [[[0.0, 0.0], [0.5, 1.0], [1.0, 0.0]]],
            "registration_px": {"tx": float(frame["rect_px"][0]), "ty": 0.0, "baseline_row": frame["baseline_row"]},
            "xh_px": frame["xh_px"],
            "verfahren": "tintenpfad",
            "erzeugt_am": "2026-09-12",
            "flecken_n": 0,
            **overrides,
        }

    @staticmethod
    async def _put(
        api: Harness,
        pfade: list[dict],
        strip: str = "S0001",
        fassung: str = "F01",
        params: dict | None = None,
        headers: dict[str, str] | None = None,
        blind: bool = False,
        **body,
    ):
        """A push under the format this image writes — `format` is REQUIRED now.

        Spelled here rather than left to a wire default: once the API accepts
        more than one format, a push that names none would claim whichever this
        image happens to write, and the row would be stamped with it. `**body`
        still wins, so a test can declare any format it likes.

        `If-Match` is required too, so the helper READS first and echoes the
        token — which is what the tools do (`tools/eigenhand/apiclient.py`) and
        the only honest way to spell „the list this push was made on". A test
        that wants to exercise the guard itself passes its own header, or
        `blind=True` for the write that does not say which list it was made on.
        """
        url = f"/eigenhand/strips/{HAND}/{strip}/{fassung}/pfade"
        sent = {**api.admin_headers(), **(headers or {})}
        if not blind and "If-Match" not in sent:
            read = await api.client.request("GET", url, headers=api.admin_headers())
            if read.status == 200 and read.headers.get("etag"):
                sent["If-Match"] = read.headers["etag"]
        return await api.client.request(
            "PUT", url, params=params, json_body={"format": PFAD_FORMAT, "pfade": pfade, **body}, headers=sent
        )

    @staticmethod
    async def _get(api: Harness, strip: str = "S0001", fassung: str = "F01"):
        return await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/{strip}/{fassung}/pfade", headers=api.admin_headers()
        )

    @pytest.mark.asyncio
    async def test_a_path_is_stored_read_back_and_replaced_whole(self, api: Harness):
        stored = await _store_strip(api)

        # Before the first follow the answer is NULL — „nobody has looked",
        # which is not the same as „followed, nothing found".
        empty = await self._get(api)
        assert empty.status == 200, empty.body
        assert empty.json()["pfade"] is None
        assert empty.json()["format"] == UNFOLLOWED_FORMAT

        written = await self._put(api, [self._path(stored), self._path(stored, 1)])
        assert written.status == 200, written.body
        assert [p["box_index"] for p in written.json()["pfade"]] == [0, 1]

        read = await self._get(api)
        assert read.json()["pfade"] == written.json()["pfade"]
        assert read.json()["pfade"][0]["verfahren"] == "tintenpfad"
        assert read.json()["pfade"][0]["erzeugt_am"] == "2026-09-12"

        # A full replacement, like the Fleckenmaske: a follower run produces
        # the whole row at once, so an empty push is a reading of its own.
        assert (await self._put(api, [])).status == 200
        assert (await self._get(api)).json()["pfade"] == []

    @pytest.mark.asyncio
    async def test_the_answer_carries_the_word_boxes_with_their_rectangles(self, api: Harness):
        # The stored registration is the STRIP's frame; placing a path over a
        # single word crop needs that crop's rectangle, and it comes along.
        stored = await _store_strip(api)
        boxes = (await self._get(api)).json()["boxes"]
        assert [box["word"] for box in boxes] == load_plan()["strips"]["S0001"]["words"]
        assert boxes[0]["rect_px"][2] <= stored["width_px"]

    @pytest.mark.asyncio
    async def test_the_paths_are_served_uncacheable_and_never_ride_on_the_listing(self, api: Harness):
        stored = await _store_strip(api)
        assert (await self._put(api, [self._path(stored)])).status == 200

        read = await self._get(api)
        assert read.headers.get("cache-control") == "private, no-store"

        # The two stand SIDE BY SIDE, and the pairing is the point: the ETag
        # here is an application lock over the stored cell, not a cache
        # validator, so `no-store` does not make it meaningless and it does not
        # make `no-store` any weaker. Nothing downstream is entitled to keep a
        # copy of these pixels' derivations — the token exists so a per-box
        # write can say which list it was drawn on.
        assert read.headers.get("etag")

        # The listing stays the cheap question („which rows does this hand
        # hold") — the paths are loaded only by the route that is asked for
        # them, which is what the deferred column is for.
        listing = await api.client.request("GET", f"/eigenhand/strips/{HAND}", headers=api.admin_headers())
        assert "pfade" not in listing.json()["strips"][0]

    @pytest.mark.asyncio
    async def test_the_token_follows_the_stored_list_and_not_the_request(self, api: Harness):
        # What makes it usable as a lock: two reads of an unchanged cell give
        # the same token, a write moves it, and the answer to the write already
        # carries the new one — so the editor can save twice in a row without a
        # re-read between the saves.
        stored = await _store_strip(api)
        first = (await self._get(api)).headers["etag"]
        assert (await self._get(api)).headers["etag"] == first

        written = await self._put(api, [self._path(stored)])
        assert written.status == 200, written.body
        after = written.headers["etag"]
        assert after != first
        assert (await self._get(api)).headers["etag"] == after

    @pytest.mark.asyncio
    async def test_the_full_push_demands_the_token_of_the_list_it_replaces(self, api: Harness):
        # The terminal door, and the OLDER of the two windows: `sync --from`
        # reads a Fassung, merges the archived boxes into what is up there and
        # pushes the whole list back — everything that landed in between is
        # inside that gap. A token on the answer alone would protect nothing
        # (V20, §6.4 „Speichern"), so the condition sits on the write.
        stored = await _store_strip(api)
        token = (await self._get(api)).headers["etag"]

        unsaid = await self._put(api, [self._path(stored)], blind=True)
        assert unsaid.status == 428, unsaid.body
        assert (await self._get(api)).json()["pfade"] is None

        stale = await self._put(api, [self._path(stored)], headers={"If-Match": '"not-the-stored-list"'})
        assert stale.status == 412, stale.body
        assert (await self._get(api)).json()["pfade"] is None

        matched = await self._put(api, [self._path(stored)], headers={"If-Match": token})
        assert matched.status == 200, matched.body

        # A weakened validator of the SAME digest is accepted: Cloudflare turns
        # a strong entity tag into a weak one whenever it re-encodes a
        # response, and these answers are gzipped at the origin and leave
        # through that zone. The value is a content digest and this is an
        # application lock, so `W/"…"` says exactly as much — this caller read
        # THIS list. A weak tag of another digest is still a 412.
        after = matched.headers["etag"]
        assert (await self._put(api, [self._path(stored, 1)], headers={"If-Match": f"W/{after}"})).status == 200
        weak_other = await self._put(api, [self._path(stored)], headers={"If-Match": 'W/"not-the-stored-list"'})
        assert weak_other.status == 412, weak_other.body

    @pytest.mark.asyncio
    async def test_a_fassung_whose_pixels_are_not_here_has_no_path_to_hold(self, api: Harness):
        # A path is followed on the ink, so the image has to be up here first.
        stored = await _store_strip(api, upload=False)
        assert (await self._get(api)).status == 404
        assert (await self._put(api, [self._path(stored)])).status == 404

    @pytest.mark.asyncio
    async def test_a_path_from_an_unsupported_format_is_refused_not_stored(self, api: Harness):
        # The 409 fires on a format this image does not KNOW — not on every
        # format it does not write. That difference is the lockstep: the API
        # admits the newer shape one release before a writer produces it.
        stored = await _store_strip(api)
        res = await self._put(api, [self._path(stored)], format=max(SUPPORTED_FORMATS) + 1)
        assert res.status == 409
        assert (await self._get(api)).json()["pfade"] is None
        # Refused means nothing moved — not even the marker of a row that was
        # never followed.
        assert (await self._get(api)).json()["format"] == UNFOLLOWED_FORMAT

    @pytest.mark.asyncio
    async def test_a_push_that_names_no_format_is_not_a_push(self, api: Harness):
        # The field is REQUIRED since the guard admits more than one number: a
        # default bound to the moving constant would let a formatless push claim
        # whatever this image writes, and the row would be stamped with it —
        # the mislabelling the stored marker exists to prevent, moved from the
        # read to the write.
        stored = await _store_strip(api)
        res = await api.client.request(
            "PUT",
            f"/eigenhand/strips/{HAND}/S0001/F01/pfade",
            json_body={"pfade": [self._path(stored)]},
            headers=api.admin_headers(),
        )
        assert res.status == 422, res.body
        assert (await self._get(api)).json()["pfade"] is None

    @pytest.mark.asyncio
    async def test_a_skipped_box_says_why_it_carries_no_path(self, api: Harness):
        # Four situations were one state („no entry") until format 2: the box
        # was not chosen, the Bogen has no geometry, the word needs glyphs the
        # plate has none for, the follower gave up. Only the third is a jump to
        # the plate rather than tracing work, so the Nachfahr-Liste has to be
        # able to tell them apart (author decision C, 2026-09-20).
        stored = await _store_strip(api)
        skip = {
            "box_index": 1,
            "word": self._path(stored, 1)["word"],
            "status": "skipped",
            "grund": "unauthored",
            "detail": "unauthored: y",
            "strokes": [],
            "verfahren": "tintenpfad",
        }
        written = await self._put(api, [self._path(stored), skip], format=2)
        assert written.status == 200, written.body
        answer = (await self._get(api)).json()
        assert answer["format"] == 2
        assert [(p["box_index"], p["status"], p["grund"]) for p in answer["pfade"]] == [
            (0, "ok", None),
            (1, "skipped", "unauthored"),
        ]
        assert answer["pfade"][1]["strokes"] == [] and answer["pfade"][1]["registration_px"] is None

        # …and the same entry under format 1 is refused rather than stored: a
        # row stamped 1 whose cell carries format-2 fields is exactly the
        # mislabelling the stored marker exists to prevent.
        refused = await self._put(api, [skip], format=1)
        assert refused.status == 422, refused.body
        assert (await self._get(api)).json()["format"] == 2

    def test_the_wire_vocabulary_is_the_one_the_core_refuses_by(self):
        # Pydantic can only type a literal, `check_paths` refuses by the tuple
        # in core — two lists that drift would refuse different things at the
        # two layers, and the 422 would name the wrong vocabulary.
        from typing import get_args

        from api.schemas import PfadGrund, PfadSpanHerkunft, PfadStatus
        from core.eigenhand.pfad import SKIP_REASONS, SPAN_HERKUNFT, STATUS_VALUES

        assert get_args(PfadStatus) == STATUS_VALUES
        assert get_args(PfadGrund) == SKIP_REASONS
        assert get_args(PfadSpanHerkunft) == SPAN_HERKUNFT

    @pytest.mark.asyncio
    async def test_a_letter_boundary_that_leaves_its_stroke_is_refused(self, api: Harness):
        # The spans index SAMPLES of a stroke, and nothing held them against it
        # until format 2 — a desynchronised span is well-formed in every number
        # it carries, so only the stroke it names can refuse it.
        stored = await _store_strip(api)
        path = self._path(stored)
        assert len(path["strokes"][0]) == 3
        good = await self._put(
            api,
            [{**path, "letter_spans": [{"stroke": 0, "slot": 0, "first": 0, "last": 2, "herkunft": "auto"}]}],
            format=2,
        )
        assert good.status == 200, good.body
        assert (await self._get(api)).json()["pfade"][0]["letter_spans"][0]["herkunft"] == "auto"

        bad = await self._put(
            api,
            [{**path, "letter_spans": [{"stroke": 0, "slot": 0, "first": 0, "last": 9, "herkunft": "auto"}]}],
            format=2,
        )
        assert bad.status == 422, bad.body
        assert "stroke 0" in bad.json()["detail"] and "3 point(s)" in bad.json()["detail"]

    @pytest.mark.asyncio
    async def test_a_hand_corrected_boundary_survives_a_re_follow_but_is_not_dropped(self, api: Harness):
        # The field rule in both directions: the box may be followed again —
        # its Bahn is a derivation — but the boundaries on it are the author's
        # own and have to come back with the push.
        stored = await _store_strip(api)
        path = self._path(stored)
        span = {"stroke": 0, "slot": 0, "first": 0, "last": 1, "herkunft": "authored"}
        assert (await self._put(api, [{**path, "letter_spans": [span]}], format=2)).status == 200

        dropped = await self._put(api, [{**path, "erzeugt_am": "2026-09-19"}], format=2)
        assert dropped.status == 409, dropped.body
        assert "letter boundaries" in dropped.json()["detail"]
        assert (await self._get(api)).json()["pfade"][0]["erzeugt_am"] == "2026-09-12"

        again = await self._put(api, [{**path, "erzeugt_am": "2026-09-19", "letter_spans": [span]}], format=2)
        assert again.status == 200, again.body
        answer = (await self._get(api)).json()["pfade"][0]
        assert answer["erzeugt_am"] == "2026-09-19"
        assert answer["letter_spans"] == [span]

    @pytest.mark.asyncio
    async def test_a_skip_cannot_quietly_take_the_place_of_a_hand_drawn_bahn(self, api: Harness):
        # The new entry type opened a hole in the very rule this PR rebuilds: a
        # skip claiming `verfahren: authored` passed as „the author correcting
        # his own trace" and replaced the drawing with an empty entry — no 409,
        # and so none of the archive guards that hang off `--replace-authored`
        # (review, PR #639). A skip says there is no path here; that is never
        # an answer BY HAND.
        stored = await _store_strip(api)
        drawing = {**self._path(stored), "verfahren": "authored"}
        assert (await self._put(api, [drawing], format=2)).status == 200

        skip = {
            "box_index": 0,
            "word": drawing["word"],
            "status": "skipped",
            "grund": "gave_up",
            "strokes": [],
            "verfahren": "authored",
        }
        refused = await self._put(api, [skip], format=2)
        assert refused.status == 409, refused.body
        assert "hand-drawn Bahn" in refused.json()["detail"]
        assert (await self._get(api)).json()["pfade"][0]["strokes"] == drawing["strokes"]

        # And the door the terminal opens does not let it through either: past
        # the displacement guard the CONTENT rule refuses the claim itself, so
        # an authored skip cannot be stored even where nothing is displaced —
        # on an empty row, for instance (review, PR #639).
        overridden = await self._put(api, [skip], format=2, params={"replace_authored": "true"})
        assert overridden.status == 422, overridden.body
        assert "cannot claim" in overridden.json()["detail"]

        # …while giving the drawing up for a FOLLOWED skip still works, which
        # is the one way a box that was drawn goes back to having no path.
        given_up = await self._put(
            api, [{**skip, "verfahren": "tintenpfad"}], format=2, params={"replace_authored": "true"}
        )
        assert given_up.status == 200, given_up.body
        assert (await self._get(api)).json()["pfade"][0]["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_the_answer_carries_the_rows_own_format_not_this_images_constant(self, api: Harness):
        """A stored path keeps the format it was written under.

        The read used to stamp its answer with `PFAD_FORMAT`, so the day the
        constant moves every older row would claim the newer semantics — and an
        Ampel would colour sensors nothing ever computed on it. Here the row is
        put on a format this image does not write; the answer has to follow the
        ROW. This is the whole point of the column, and the only assertion that
        would fail again if the constant crept back into the answer.
        """
        stored = await _store_strip(api)
        # A Fassung nobody has followed already carries the marker — the column
        # is NOT NULL, so there is no „unknown format" state to handle. And it
        # carries the MIGRATION's number, not the running image's: the two came
        # apart the day the second release moved `PFAD_FORMAT`.
        assert (await self._get(api)).json()["format"] == UNFOLLOWED_FORMAT
        assert (await self._put(api, [self._path(stored)])).status == 200
        assert (await self._get(api)).json()["format"] == PFAD_FORMAT

        async with api.session_maker() as session:
            await session.execute(
                update(EigenhandStrip)
                .where(EigenhandStrip.hand == HAND, EigenhandStrip.strip == "S0001", EigenhandStrip.fassung == "F01")
                .values(pfade_format=PFAD_FORMAT + 1)
            )
            await session.commit()

        answer = (await self._get(api)).json()
        assert answer["format"] == PFAD_FORMAT + 1
        assert [entry["box_index"] for entry in answer["pfade"]] == [0]

        # The other half of the contract: a write re-stamps the row with what
        # it actually stored. Without the marker coming back DOWN here, a row
        # could keep claiming a format its content no longer has — and every
        # assertion above would still pass with the write-side stamp deleted.
        assert (await self._put(api, [self._path(stored)])).status == 200
        assert (await self._get(api)).json()["format"] == PFAD_FORMAT

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "broken",
        [
            {"box_index": 99},
            {"word": "irgendwas"},
            {"registration_px": {"tx": 9_000_000.0, "ty": 0.0, "baseline_row": 10.0}},
            {"strokes": [[[0.0, 0.0], [500.0, 1.0]]]},
        ],
    )
    async def test_a_path_that_does_not_belong_to_this_strip_is_refused(self, api: Harness, broken: dict):
        stored = await _store_strip(api)
        res = await self._put(api, [{**self._path(stored), **broken}])
        assert res.status == 422, res.body
        assert (await self._get(api)).json()["pfade"] is None

    @pytest.mark.asyncio
    async def test_a_hand_drawn_path_is_never_replaced_by_a_followed_one(self, api: Harness):
        # The write is a FULL replacement, so a follower run can take a path
        # the author drew himself away in two ways — by overwriting the box and
        # by simply leaving it out. Both are refused WHOLE, before anything is
        # committed: this answer has no per-box `skipped` channel, so a silent
        # skip would leave the operator believing the run was stored.
        stored = await _store_strip(api)
        drawn = await self._put(api, [self._path(stored, verfahren="authored")])
        assert drawn.status == 200, drawn.body

        overwritten = await self._put(api, [self._path(stored)])
        assert overwritten.status == 409, overwritten.body
        assert (await self._get(api)).json()["pfade"][0]["verfahren"] == "authored"

        omitted = await self._put(api, [self._path(stored, 1)])
        assert omitted.status == 409, omitted.body
        read = (await self._get(api)).json()["pfade"]
        assert [(p["box_index"], p["verfahren"]) for p in read] == [(0, "authored")]

    @pytest.mark.asyncio
    async def test_the_query_flag_is_the_one_way_past_a_hand_drawn_path(self, api: Harness):
        # An explicit act at the keyboard (`tools.eigenhand.pfad
        # --replace-authored`), deliberately not a fourth `force` button in the
        # workbench: no browser code sends this parameter.
        stored = await _store_strip(api)
        assert (await self._put(api, [self._path(stored, verfahren="authored")])).status == 200

        given_up = await self._put(api, [self._path(stored)], params={"replace_authored": "true"})
        assert given_up.status == 200, given_up.body
        assert (await self._get(api)).json()["pfade"][0]["verfahren"] == "tintenpfad"

    @pytest.mark.asyncio
    async def test_the_author_may_correct_his_own_hand_drawn_path(self, api: Harness):
        # What keeps a hand-drawing surface possible: the rule guards against a
        # DERIVATION replacing ground truth, not against the author himself.
        stored = await _store_strip(api)
        assert (await self._put(api, [self._path(stored, verfahren="authored")])).status == 200

        again = await self._put(api, [self._path(stored, verfahren="authored", erzeugt_am="2026-09-18")])
        assert again.status == 200, again.body
        assert (await self._get(api)).json()["pfade"][0]["erzeugt_am"] == "2026-09-18"


class TestStreifenPfadKasten:
    """The per-box write — the first door a Bahn can come through from a browser.

    Everything the earlier rounds built stands behind it: the archive chain so
    a drawing can be filed before anything may overwrite it, the stored format
    marker so an entry is read under the semantics it was written in, the
    field-level authored rule so a re-follow cannot take the author's letter
    boundaries away. What this route adds is the token that keeps a one-box
    write from landing on a list somebody else has meanwhile replaced.
    """

    @staticmethod
    async def _patch(
        api: Harness,
        pfad: dict,
        token: str | None,
        box: int | None = None,
        strip: str = "S0001",
        fassung: str = "F01",
        **body,
    ):
        index = pfad["box_index"] if box is None else box
        return await api.client.request(
            "PATCH",
            f"/eigenhand/strips/{HAND}/{strip}/{fassung}/pfade/{index}",
            json_body={"format": PFAD_FORMAT, "pfad": pfad, **body},
            headers={**api.admin_headers(), **({} if token is None else {"If-Match": token})},
        )

    @staticmethod
    async def _read(api: Harness, strip: str = "S0001", fassung: str = "F01"):
        res = await api.client.request(
            "GET", f"/eigenhand/strips/{HAND}/{strip}/{fassung}/pfade", headers=api.admin_headers()
        )
        assert res.status == 200, res.body
        return res

    @staticmethod
    def _drawn(stored: dict, box_index: int = 0, **overrides) -> dict:
        """A box as the editor hands it over — `verfahren` is the route's job."""
        return TestStreifenPfad._path(stored, box_index, verfahren="authored", **overrides)

    @pytest.mark.asyncio
    async def test_a_box_drawn_by_hand_is_stored_and_the_row_keeps_its_neighbours(self, api: Harness):
        # The whole reason this is a PATCH: the editor knows ONE box. A full
        # push would have to restate the rest of the row from a list the
        # browser read minutes ago, and any follower run that landed in between
        # would go with it.
        stored = await _store_strip(api)
        followed = TestStreifenPfad._path(stored, 1)
        assert (await TestStreifenPfad._put(api, [followed])).status == 200

        read = await self._read(api)
        written = await self._patch(api, self._drawn(stored, 0, erzeugt_am="2026-09-20"), read.headers["etag"])
        assert written.status == 200, written.body
        assert written.headers.get("cache-control") == "private, no-store"

        answer = written.json()["pfade"]
        assert [(entry["box_index"], entry["verfahren"]) for entry in answer] == [(0, "authored"), (1, "tintenpfad")]
        assert answer[1] == (await self._read(api)).json()["pfade"][1]
        assert (await self._read(api)).json()["pfade"] == answer

    @pytest.mark.asyncio
    async def test_the_same_box_drawn_again_replaces_its_own_entry(self, api: Harness):
        # „Speichern" twice on the same box is the normal case, and the second
        # save is the author correcting his own trace — the one thing the
        # authored rule has always let through.
        stored = await _store_strip(api)
        first = await self._patch(api, self._drawn(stored), (await self._read(api)).headers["etag"])
        assert first.status == 200, first.body

        second = await self._patch(api, self._drawn(stored, 0, erzeugt_am="2026-09-21"), first.headers["etag"])
        assert second.status == 200, second.body
        answer = (await self._read(api)).json()["pfade"]
        assert len(answer) == 1
        assert answer[0]["erzeugt_am"] == "2026-09-21"

    @pytest.mark.asyncio
    async def test_the_letter_boundaries_belong_to_the_bahn_they_were_drawn_on(self, api: Harness):
        # A loss, and an intended one. The save replaces the box's entry whole,
        # so a body without `letter_spans` gives up the ones the author
        # corrected there — the same rule the full push applies to an answer by
        # hand, and right for the same reason: a corrected boundary describes
        # THESE strokes. `displaced_authored` does not stand in the way of it
        # either (`by_hand` short-circuits both fields), so nothing refuses
        # this and nothing should. The duty it puts on the editor: resend the
        # stored spans whenever the strokes are unchanged.
        stored = await _store_strip(api)
        corrected = [{"stroke": 0, "slot": 0, "first": 0, "last": 2, "herkunft": "authored"}]
        first = await self._patch(
            api, self._drawn(stored, letter_spans=corrected), (await self._read(api)).headers["etag"], format=2
        )
        assert first.status == 200, first.body
        assert (await self._read(api)).json()["pfade"][0]["letter_spans"] == corrected

        again = await self._patch(api, self._drawn(stored), first.headers["etag"], format=2)
        assert again.status == 200, again.body
        assert (await self._read(api)).json()["pfade"][0]["letter_spans"] is None

    @pytest.mark.asyncio
    async def test_a_write_that_does_not_say_which_list_it_was_drawn_on_is_refused(self, api: Harness):
        # 428 rather than a write that looks safe: without the token this route
        # is a lost update by construction, and a client that may leave the
        # header out has no guard at all.
        stored = await _store_strip(api)
        res = await self._patch(api, self._drawn(stored), None)
        assert res.status == 428, res.body
        assert (await self._read(api)).json()["pfade"] is None

        # …and the refusal does not hand the token over. It would be the
        # obvious courtesy and it would give the guard away: write blind,
        # collect the token from the 428, resend — and the unseen overwrite is
        # back. The token is earned by reading the list.
        assert (await self._read(api)).headers["etag"] not in res.json()["detail"]

    @pytest.mark.asyncio
    async def test_a_write_onto_a_list_that_has_moved_on_is_refused(self, api: Harness):
        # The window this closes: the editor reads the Fassung, a follower run
        # replaces the row, and the editor writes its box back onto the list it
        # read — taking the run with it. With the token the second write is a
        # 412 and the author redraws on what is actually there.
        stored = await _store_strip(api)
        token = (await self._read(api)).headers["etag"]
        assert (await TestStreifenPfad._put(api, [TestStreifenPfad._path(stored, 1)])).status == 200

        res = await self._patch(api, self._drawn(stored), token)
        assert res.status == 412, res.body
        assert [entry["box_index"] for entry in (await self._read(api)).json()["pfade"]] == [1]
        # Same rule as the 428: the refusal names what the client sent, never
        # what is stored — otherwise a stale save just retries with the token
        # the refusal handed it, on a list nobody looked at.
        assert (await self._read(api)).headers["etag"] not in res.json()["detail"]

        # …and the read that follows the refusal hands out the token that works.
        again = await self._patch(api, self._drawn(stored), (await self._read(api)).headers["etag"])
        assert again.status == 200, again.body

    @pytest.mark.asyncio
    async def test_a_write_that_claims_any_stored_list_is_refused(self, api: Harness):
        # `If-Match: *` is HTTP for „whatever is there", which is exactly the
        # „I did not look" this guard exists to catch.
        stored = await _store_strip(api)
        res = await self._patch(api, self._drawn(stored), "*")
        assert res.status == 412, res.body
        assert (await self._read(api)).json()["pfade"] is None

    @pytest.mark.asyncio
    async def test_a_token_an_intermediary_weakened_still_names_the_same_list(self, api: Harness):
        # The save the author actually makes goes through Cloudflare, which
        # turns a strong entity tag into a weak one whenever it re-encodes a
        # response — and these answers are gzipped at the origin. A browser
        # echoes what it was handed, so a strict-strong comparison would 412
        # every save on the one deployment path the workbench has, for a reason
        # invisible from here.
        stored = await _store_strip(api)
        res = await self._patch(api, self._drawn(stored), f"W/{(await self._read(api)).headers['etag']}")
        assert res.status == 200, res.body
        assert (await self._read(api)).json()["pfade"][0]["verfahren"] == "authored"

    @pytest.mark.asyncio
    async def test_the_address_and_the_body_have_to_name_the_same_box(self, api: Harness):
        stored = await _store_strip(api)
        res = await self._patch(api, self._drawn(stored, 1), (await self._read(api)).headers["etag"], box=0)
        assert res.status == 422, res.body
        assert "box 1" in res.json()["detail"] and "box 0" in res.json()["detail"]
        assert (await self._read(api)).json()["pfade"] is None

    @pytest.mark.asyncio
    async def test_nothing_derived_comes_through_this_door(self, api: Harness):
        # The route stamps `authored`, and a body claiming another provenance
        # is refused rather than re-labelled: a followed path stored as the
        # author's own hand would be ground truth nothing could ever tell apart
        # from a drawing — the one mistake the whole authored rule exists to
        # prevent, and the reason the full push is a separate door.
        stored = await _store_strip(api)
        res = await self._patch(api, TestStreifenPfad._path(stored), (await self._read(api)).headers["etag"])
        assert res.status == 422, res.body
        assert "tintenpfad" in res.json()["detail"]
        assert (await self._read(api)).json()["pfade"] is None

    @pytest.mark.asyncio
    async def test_a_hand_drawn_box_cannot_be_a_skip(self, api: Harness):
        # `check_paths` refuses an authored skip outright, and that refusal is
        # what stands in for the displacement guard here: an empty entry cannot
        # take a drawing's place through this door.
        stored = await _store_strip(api)
        drawn = self._drawn(stored)
        assert (await self._patch(api, drawn, (await self._read(api)).headers["etag"])).status == 200

        skip = {
            "box_index": 0,
            "word": drawn["word"],
            "status": "skipped",
            "grund": "gave_up",
            "strokes": [],
            "verfahren": "authored",
        }
        res = await self._patch(api, skip, (await self._read(api)).headers["etag"])
        assert res.status == 422, res.body
        assert "cannot claim" in res.json()["detail"]
        assert (await self._read(api)).json()["pfade"][0]["strokes"] == drawn["strokes"]

    @pytest.mark.asyncio
    async def test_a_box_that_does_not_belong_to_this_strip_is_refused_by_the_same_rules(self, api: Harness):
        # 422 over `check_paths` on the one-element list, so the box rules live
        # in one place and this route cannot refuse by a second, drifting copy.
        stored = await _store_strip(api)
        token = (await self._read(api)).headers["etag"]
        broken = self._drawn(stored, 0, registration_px={"tx": 9_000_000.0, "ty": 0.0, "baseline_row": 10.0})
        res = await self._patch(api, broken, token)
        assert res.status == 422, res.body
        assert (await self._read(api)).json()["pfade"] is None

    @pytest.mark.asyncio
    async def test_one_box_may_not_relabel_the_ones_beside_it(self, api: Harness):
        # The stamp is a statement about every entry in the cell, so a per-box
        # write declaring another format would re-label its neighbours — the
        # mislabelling the stored marker exists to prevent, one layer down.
        stored = await _store_strip(api)
        assert (await TestStreifenPfad._put(api, [TestStreifenPfad._path(stored, 1)], format=1)).status == 200
        token = (await self._read(api)).headers["etag"]

        res = await self._patch(api, self._drawn(stored), token, format=2)
        assert res.status == 409, res.body
        assert "format 1" in res.json()["detail"]
        assert (await self._read(api)).json()["format"] == 1

        # Under the row's own format the same box goes in.
        assert (await self._patch(api, self._drawn(stored), token, format=1)).status == 200

    @pytest.mark.asyncio
    async def test_the_first_box_of_an_unfollowed_row_sets_its_format(self, api: Harness):
        # A row nobody has followed carries the migration's number and no
        # entries, so there is nothing to re-label: the first entry decides
        # what the list is.
        stored = await _store_strip(api)
        assert (await self._read(api)).json()["format"] == UNFOLLOWED_FORMAT
        written = await self._patch(api, self._drawn(stored), (await self._read(api)).headers["etag"], format=2)
        assert written.status == 200, written.body
        assert (await self._read(api)).json()["format"] == 2

    @pytest.mark.asyncio
    async def test_a_format_this_image_cannot_read_is_refused_here_too(self, api: Harness):
        stored = await _store_strip(api)
        res = await self._patch(
            api, self._drawn(stored), (await self._read(api)).headers["etag"], format=max(SUPPORTED_FORMATS) + 1
        )
        assert res.status == 409, res.body
        assert (await self._read(api)).json()["pfade"] is None


class TestPfadBoxes:
    """The meta-only read: which word boxes of a hand are in which state.

    The question „welche Kästen tragen welchen Zustand" costs one request per
    (strip, Fassung) through the path read and drags a few thousand points per
    word along for numbers nobody asked for. Here it is one answer, and what
    makes it worth having is what is NOT in it.
    """

    # A follower's full diagnosis block, all four graded sensors inside their
    # green bound. `paper_lifts: 0` is one run, which is what the script writes
    # both plan words of S0001 in (`body_runs_expected`).
    GREEN = {
        "ink_unvisited_share": 0.0,
        "paper_lifts": 0,
        "paper_excursion_xh": 0.1,
        "aiou": 0.9,
        "jumps": 1,
        "hairpins": 0,
    }

    @staticmethod
    async def _stand(api: Harness, hand: str = HAND, params: dict | None = None):
        return await api.client.request("GET", f"/eigenhand/pfade/{hand}", params=params, headers=api.admin_headers())

    @pytest.mark.asyncio
    async def test_every_box_of_the_hand_is_stated_and_not_one_point_travels(self, api: Harness):
        stored = await _store_strip(api)
        assert (await TestStreifenPfad._put(api, [TestStreifenPfad._path(stored)])).status == 200

        answer = await self._stand(api)
        assert answer.status == 200, answer.body
        # A projection of the reserved own-hand pixels — same gate, same header
        # as the pixels themselves (`private, no-store`).
        assert answer.headers.get("cache-control") == "private, no-store"
        body = answer.json()
        assert body["hand"] == HAND
        assert len(body["fassungen"]) == 1
        fassung = body["fassungen"][0]
        assert (fassung["strip"], fassung["fassung"], fassung["sheet"], fassung["row_index"]) == (
            "S0001",
            "F01",
            "B0001",
            0,
        )
        assert fassung["format"] == PFAD_FORMAT and fassung["gefolgt"] is True

        # Both boxes of the frozen plan appear, the one with an entry and the
        # one without: a box with no path is the state this list exists to show.
        assert [box["word"] for box in fassung["kaesten"]] == load_plan()["strips"]["S0001"]["words"]
        followed, empty = fassung["kaesten"]
        assert (followed["box_index"], followed["verfahren"], followed["erzeugt_am"]) == (0, "tintenpfad", "2026-09-12")
        assert followed["absetzer_soll"] == body_runs_expected(followed["word"])
        assert (empty["verfahren"], empty["erzeugt_am"], empty["flecken_n"]) == (None, None, None)
        assert empty["tintentreue"]["grund"] == "kein Eintrag"

        # The whole point: the Bahn stays behind the per-Fassung read.
        assert "strokes" not in json.dumps(body)

    @pytest.mark.asyncio
    async def test_a_measured_box_carries_its_light_and_the_fassung_its_counter(self, api: Harness):
        # Author decision E of 2026-09-20: a Fassung gets a COUNTER („3 von 4
        # Kästen folgen"), never a colour — a second verdict beside the
        # Streifen-Befund with its own vocabulary is exactly what was refused.
        stored = await _store_strip(api)
        followed = TestStreifenPfad._path(stored, meta={"tintenpfad": self.GREEN})
        skip = {
            "box_index": 1,
            "word": TestStreifenPfad._path(stored, 1)["word"],
            "status": "skipped",
            "grund": "unauthored",
            "detail": "unauthored: y",
            "strokes": [],
            "verfahren": "tintenpfad",
        }
        assert (await TestStreifenPfad._put(api, [followed, skip], format=2)).status == 200

        fassung = (await self._stand(api)).json()["fassungen"][0]
        assert fassung["format"] == 2
        light = fassung["kaesten"][0]["tintentreue"]
        assert (light["stufe"], light["gemessen"], light["sensor"]) == ("folgt", True, None)
        assert light["format"] == 2 and light["vorlaeufig"] is True
        # The raw readings ride along — a step and the sensor that names it,
        # never a scalar.
        assert {sensor["name"] for sensor in light["sensoren"]} == {
            "Absetzer (Bahn)",
            "Tinte ohne Bahn",
            "Papier-Exkursion",
            "AIoU",
            "Sprünge und Haken",
        }
        assert fassung["kaesten"][0]["offen"] is False

        # The Skip-Eintrag keeps its reason, which is what tells „unauthored,
        # go to the plate" from „the follower gave up, trace it" — and the
        # light says the same thing rather than talking about a measurement
        # that was never owed on a box with no path.
        skipped = fassung["kaesten"][1]
        assert (skipped["status"], skipped["grund"], skipped["detail"]) == ("skipped", "unauthored", "unauthored: y")
        assert skipped["tintentreue"]["grund"] == "übersprungen: unautoriert"
        assert skipped["tintentreue"]["stufe"] == "nicht beurteilt"
        assert skipped["offen"] is True
        assert fassung["zaehler"] == {"kaesten": 2, "gemessen": 1, "folgt": 1, "von_hand": 0}

    @pytest.mark.asyncio
    async def test_a_skip_is_never_graded_however_much_meta_it_carries(self, api: Harness):
        # `meta` is a free blob and a skip carries it through untouched, so a
        # follower that one day records WHY it gave up would hand this read a
        # full diagnosis block on a box with no Bahn at all. Grading it would
        # make that box green, take it off the work list and count it in
        # „3 von 4 folgen" — a path that does not exist, reported as the best
        # kind there is.
        stored = await _store_strip(api)
        skip = {
            "box_index": 0,
            "word": TestStreifenPfad._path(stored)["word"],
            "status": "skipped",
            "grund": "gave_up",
            "strokes": [],
            "verfahren": "tintenpfad",
            "meta": {"tintenpfad": self.GREEN},
        }
        assert (await TestStreifenPfad._put(api, [skip], format=2)).status == 200

        fassung = (await self._stand(api)).json()["fassungen"][0]
        box = fassung["kaesten"][0]
        assert box["tintentreue"]["grund"] == "übersprungen: aufgegeben"
        assert box["tintentreue"]["gemessen"] is False and box["offen"] is True
        assert fassung["zaehler"] == {"kaesten": 2, "gemessen": 0, "folgt": 0, "von_hand": 0}

    @pytest.mark.asyncio
    async def test_an_unmeasured_hand_drawn_box_is_counted_and_is_not_open_work(self, api: Harness):
        # „von Hand gezeichnet" is ground truth: grey because nothing has
        # MEASURED it, not because it is a defect — and therefore done, not
        # open (V21's „j von Hand (ungemessen)" counter).
        stored = await _store_strip(api)
        assert (await TestStreifenPfad._put(api, [TestStreifenPfad._path(stored, verfahren="authored")])).status == 200

        fassung = (await self._stand(api)).json()["fassungen"][0]
        drawn = fassung["kaesten"][0]
        assert drawn["tintentreue"]["grund"] == "von Hand gezeichnet" and drawn["offen"] is False
        assert fassung["zaehler"] == {"kaesten": 2, "gemessen": 0, "folgt": 0, "von_hand": 1}

    @pytest.mark.asyncio
    async def test_the_filter_keeps_the_open_boxes_and_leaves_the_counter_alone(self, api: Harness):
        stored = await _store_strip(api)
        followed = TestStreifenPfad._path(stored, meta={"tintenpfad": self.GREEN})
        assert (await TestStreifenPfad._put(api, [followed], format=2)).status == 200

        narrowed = (await self._stand(api, params={"nur": "offen"})).json()["fassungen"][0]
        # Box 0 follows, box 1 has no entry at all — only the second is work.
        assert [box["box_index"] for box in narrowed["kaesten"]] == [1]
        # …and the counter still answers the FASSUNG, not the query: a number
        # that moved with the filter would mean something else on every click.
        assert narrowed["zaehler"] == {"kaesten": 2, "gemessen": 1, "folgt": 1, "von_hand": 0}

    @pytest.mark.asyncio
    async def test_a_fassung_with_nothing_open_drops_out_of_the_filtered_answer(self, api: Harness):
        stored = await _store_strip(api)
        both = [TestStreifenPfad._path(stored, index, meta={"tintenpfad": self.GREEN}) for index in (0, 1)]
        assert (await TestStreifenPfad._put(api, both, format=2)).status == 200

        assert len((await self._stand(api)).json()["fassungen"]) == 1
        # Nothing left to work on, so the row is not a line in the list at all
        # — an empty Fassung would be a row that says „look here" about nothing.
        assert (await self._stand(api, params={"nur": "offen"})).json()["fassungen"] == []

    @pytest.mark.asyncio
    async def test_a_mask_edited_after_the_follow_says_so_beside_the_light(self, api: Harness):
        # The state the SPA computes today as a free-standing warning chip
        # (`PfadCaption`): the entry was followed under a mask of a different
        # size, so its numbers describe other ink than the picture now shows.
        stored = await _store_strip(api)
        followed = TestStreifenPfad._path(stored, meta={"tintenpfad": self.GREEN})
        assert (await TestStreifenPfad._put(api, [followed], format=2)).status == 200
        assert (await TestFleckenmaske._patch(api, [{"x_mm": 30.0, "y_mm": 8.0, "r_mm": 0.6, "quelle": "hand"}])).status

        box = (await self._stand(api)).json()["fassungen"][0]["kaesten"][0]
        assert box["stale"] is True and box["flecken_n"] == 0
        assert box["tintentreue"]["grund"] == "Maske geändert"
        assert box["offen"] is True

    def test_the_step_vocabulary_is_the_one_core_derives(self):
        # Pydantic can only type a literal; the steps are decided in core. Two
        # lists that drifted would let a surface branch on a step this API
        # never sends — the same trap the path vocabularies are pinned against.
        from typing import get_args

        from api.schemas import TintentreueStufe
        from core.eigenhand.tintentreue import STUFE_UNGEMESSEN, STUFEN

        assert get_args(TintentreueStufe) == (*STUFEN, STUFE_UNGEMESSEN)

    def test_the_one_grey_reason_the_spa_compares_is_the_one_core_writes(self):
        # `grund` is a free `str` on the wire, so the ONE place the SPA compares
        # it needs a pin of its own: the Nachfahr-Zeile suppresses its „Maske
        # geändert" chip where the verdict already carries that sentence, and a
        # rename in core would silently print it twice. The severity ladder
        # deliberately reads typed fields instead and is not affected.
        from pathlib import Path

        from core.eigenhand.tintentreue import GRUND_MASKE

        src = (Path(__file__).resolve().parents[1] / "app/src/sections/admin/eigenhand/stripBoxRows.ts").read_text(
            encoding="utf-8"
        )
        assert f"maske: '{GRUND_MASKE}'" in src

    @pytest.mark.asyncio
    async def test_a_hand_with_nothing_written_answers_a_list_and_a_bad_filter_is_refused(self, api: Harness):
        empty = await self._stand(api)
        assert empty.status == 200 and empty.json() == {"hand": HAND, "fassungen": []}

        assert (await self._stand(api, hand="nicht-eine-hand")).status == 400
        assert (await self._stand(api, params={"nur": "irgendwas"})).status == 422


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
            ("PATCH", f"/eigenhand/strips/{HAND}/S0001/F01/flecken"),
            ("GET", f"/eigenhand/strips/{HAND}/S0001/F01/pfade"),
            ("PUT", f"/eigenhand/strips/{HAND}/S0001/F01/pfade"),
            ("PATCH", f"/eigenhand/strips/{HAND}/S0001/F01/pfade/0"),
            ("GET", f"/eigenhand/pfade/{HAND}"),
            ("GET", "/eigenhand/uebergangsraum"),
            ("PUT", "/eigenhand/uebergangsraum"),
        ],
    )
    async def test_every_route_needs_the_admin_header(self, api: Harness, method: str, path: str):
        res = await api.client.request(method, path, json_body={} if method in ("POST", "PUT", "PATCH") else None)
        assert res.status == 401, (path, res.status)

    @pytest.mark.asyncio
    async def test_a_hand_appears_in_the_list_once_it_has_a_bogen(self, api: Harness):
        empty = await api.client.request("GET", "/eigenhand/hands", headers=api.admin_headers())
        assert empty.json() == {"hands": [], "styles": ["kurrent", "suetterlin", "offenbacher"]}
        await _print(api, strips=["S0001"], date="2026-08-23")
        listed = await api.client.request("GET", "/eigenhand/hands", headers=api.admin_headers())
        assert listed.json()["hands"] == [HAND]
