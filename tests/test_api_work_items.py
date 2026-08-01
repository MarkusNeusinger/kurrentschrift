"""The work-item endpoints (Werkbank W1 + W4): the Auftragskorb's admin API.

Same in-memory aiosqlite stack as the other HTTP suites (`tests/api_harness.py`
via the `api` fixture). Proves the create/list roundtrip per kind, the status
filter a session queries at round start, the §5 handling protocol the PATCH
enforces (restate before working, diagnose + report before closing), the
source-free queue a session reads without knowing any source id, delete, and
that every route is admin-gated and rejects an unworkable target.
"""

from __future__ import annotations

import pytest

from api.routers.work_items import check_transition
from tests.api_harness import Harness


def _letter_item(**overrides) -> dict:
    item = {"kind": "letter", "glyph_key": "n", "note": "Bogen zu flach"}
    item.update(overrides)
    return item


async def _file(api: Harness, source_id: str, body: dict) -> dict:
    res = await api.client.request(
        "POST", f"/sources/{source_id}/work-items", json_body=body, headers=api.admin_headers()
    )
    assert res.status == 201, res.body
    return res.json()


async def _patch(api: Harness, item_id: int, body: dict, source_id: str | None = None):
    """The protocol PATCH — source-free by default, which is how a working
    session reaches it."""
    path = f"/work-items/{item_id}" if source_id is None else f"/sources/{source_id}/work-items/{item_id}"
    return await api.client.request("PATCH", path, json_body=body, headers=api.admin_headers())


async def _ack(
    api: Harness, item_id: int, understanding: str = "Der n-Bogen ist nur in Wörtern zu flach, solo stimmt er."
):
    res = await _patch(api, item_id, {"status": "ack", "understanding": understanding, "reproduced": "yes"})
    assert res.status == 200, res.body
    return res.json()


async def test_create_and_list_per_kind(api: Harness):
    _, source_id = await api.seed_style_and_source()
    letter = await _file(api, source_id, _letter_item(specimen_kind="word", specimen_id="wenn"))
    assert letter["id"] > 0
    assert letter["status"] == "open"
    assert letter["glyph_key"] == "n" and letter["note"] == "Bogen zu flach"
    assert letter["resolution"] is None
    # Every row names its own source, so the source-free queue is actionable.
    assert letter["source_id"] == source_id
    # A fresh item carries no protocol fields yet.
    assert (letter["understanding"], letter["stage"], letter["acked_at"], letter["closed_at"]) == (None,) * 4

    pair = await _file(
        api, source_id, {"kind": "pair", "left_key": "n", "right_key": "e", "note": "Übergang zu hoch", "word": "wenn"}
    )
    word = await _file(api, source_id, {"kind": "word", "word": "wenn", "specimen_kind": "word", "specimen_id": "wenn"})

    res = await api.client.request("GET", f"/sources/{source_id}/work-items", headers=api.admin_headers())
    assert res.status == 200
    rows = res.json()
    # Oldest first — the order a session works them off.
    assert [r["id"] for r in rows] == [letter["id"], pair["id"], word["id"]]
    assert [r["kind"] for r in rows] == ["letter", "pair", "word"]
    assert rows[1]["left_key"] == "n" and rows[1]["right_key"] == "e"
    assert rows[2]["specimen_id"] == "wenn"

    # Items are per source — another source's basket stays empty.
    _, other_source = await api.seed_style_and_source()
    res = await api.client.request("GET", f"/sources/{other_source}/work-items", headers=api.admin_headers())
    assert res.json() == []


async def test_full_protocol_run_and_status_filter(api: Harness):
    """open → ack → done: the session restates the task, works, then closes it
    with the diagnosed stage and what changed."""
    _, source_id = await api.seed_style_and_source()
    first = await _file(api, source_id, _letter_item())
    second = await _file(api, source_id, _letter_item(glyph_key="e", note="Schleife zu eng"))

    acked = await _ack(api, first["id"])
    assert acked["status"] == "ack"
    assert acked["reproduced"] == "yes"
    assert acked["acked_at"] is not None and acked["closed_at"] is None

    res = await _patch(
        api,
        first["id"],
        {"status": "done", "stage": "laufform", "resolution": "Laufform neu abgeleitet, PR #999, Wörter 0.124→0.121"},
    )
    assert res.status == 200
    out = res.json()
    assert out["status"] == "done" and out["stage"] == "laufform"
    assert out["resolution"].startswith("Laufform neu abgeleitet")
    assert out["closed_at"] is not None
    # The partial update leaves the human's note and the restatement alone.
    assert out["note"] == "Bogen zu flach"
    assert out["understanding"].startswith("Der n-Bogen")

    res = await api.client.request(
        "GET", f"/sources/{source_id}/work-items", params={"status": "open"}, headers=api.admin_headers()
    )
    assert [r["id"] for r in res.json()] == [second["id"]]
    res = await api.client.request(
        "GET", f"/sources/{source_id}/work-items", params={"status": "done"}, headers=api.admin_headers()
    )
    assert [r["id"] for r in res.json()] == [first["id"]]

    # A note-only PATCH needs no protocol fields and leaves the status alone.
    res = await _patch(api, second["id"], {"note": "Schleife zu eng, siehe Abb. 19"}, source_id=source_id)
    assert res.json()["status"] == "open"
    assert res.json()["note"] == "Schleife zu eng, siehe Abb. 19"

    res = await _patch(api, 9999, {"status": "ack", "understanding": "x", "reproduced": "no"})
    assert res.status == 404


async def test_closing_needs_the_protocol_fields(api: Harness):
    """The §5 doctrine as a 422: an item cannot be closed by a session that
    never said what it understood, never diagnosed a stage or reports nothing."""
    _, source_id = await api.seed_style_and_source()
    item = await _file(api, source_id, _letter_item())

    # Closing straight out of 'open' — no restatement on file.
    res = await _patch(api, item["id"], {"status": "done", "stage": "laufform", "resolution": "irgendwas"})
    assert res.status == 422
    assert "understanding" in res.json()["detail"]

    # Acking without saying anything.
    for body in (
        {"status": "ack"},
        {"status": "ack", "understanding": "   ", "reproduced": "yes"},
        {"status": "ack", "understanding": "verstanden"},  # no `reproduced`
    ):
        res = await _patch(api, item["id"], body)
        assert res.status == 422, body

    await _ack(api, item["id"])

    # Acked, but closing without the stage or without an outcome.
    for body in (
        {"status": "done", "resolution": "gefixt"},
        {"status": "done", "stage": "join_rule"},
        {"status": "done", "stage": "join_rule", "resolution": "  "},
        {"status": "returned", "stage": "chart_ductus"},
    ):
        res = await _patch(api, item["id"], body)
        assert res.status == 422, body

    # A stage outside the §3 vocabulary is a typo, not a new stage.
    res = await _patch(api, item["id"], {"status": "done", "stage": "sonstiges", "resolution": "x"})
    assert res.status == 422

    # And an unknown status likewise.
    res = await _patch(api, item["id"], {"status": "erledigt"})
    assert res.status == 422


async def test_returned_item_goes_back_to_the_author(api: Harness):
    """§5.6: when the missing piece is the author's ground truth the session
    hands the row back instead of closing it — a state of its own, not a
    'done' with a prefixed note."""
    _, source_id = await api.seed_style_and_source()
    item = await _file(api, source_id, _letter_item())
    await _ack(api, item["id"], "Das n ist auch solo falsch — Tafel-Duktus, nicht Laufform.")

    res = await _patch(
        api,
        item["id"],
        {
            "status": "returned",
            "stage": "chart_ductus",
            "resolution": "Rückgabe an Autor: n im Wizard neu nachfahren (zweiter Abstrich setzt zu früh an).",
        },
    )
    assert res.status == 200
    assert res.json()["status"] == "returned"

    res = await api.client.request("GET", "/work-items", params={"status": "returned"}, headers=api.admin_headers())
    assert [r["id"] for r in res.json()] == [item["id"]]


async def test_rejecting_a_restatement_reopens_the_item(api: Harness):
    """The admin's veto on a misunderstanding: back to 'open', but the rejected
    restatement stays on the record."""
    _, source_id = await api.seed_style_and_source()
    item = await _file(api, source_id, _letter_item())
    await _ack(api, item["id"], "Das e daneben ist zu eng.")

    res = await _patch(
        api,
        item["id"],
        {"status": "open", "note": "Bogen zu flach\n\nKorrektur: es geht um das n, nicht um das e."},
        source_id=source_id,
    )
    assert res.status == 200
    out = res.json()
    assert out["status"] == "open"
    assert out["closed_at"] is None
    assert out["understanding"] == "Das e daneben ist zu eng."
    assert out["acked_at"] is not None
    assert "Korrektur:" in out["note"]


async def test_source_free_queue_across_sources(api: Harness):
    """The round-start read a session can make without knowing any source id —
    the failure mode that sent an earlier session grepping the router source."""
    _, first_source = await api.seed_style_and_source()
    _, second_source = await api.seed_style_and_source()
    one = await _file(api, first_source, _letter_item())
    two = await _file(api, second_source, _letter_item(glyph_key="e"))

    res = await api.client.request("GET", "/work-items", params={"status": "open"}, headers=api.admin_headers())
    assert res.status == 200
    rows = res.json()
    assert [r["id"] for r in rows] == [one["id"], two["id"]]
    assert [r["source_id"] for r in rows] == [first_source, second_source]

    res = await api.client.request(
        "GET", "/work-items", params={"source_id": second_source}, headers=api.admin_headers()
    )
    assert [r["id"] for r in res.json()] == [two["id"]]

    # A typo'd source is a 404, not a quietly empty basket.
    res = await api.client.request("GET", "/work-items", params={"source_id": "nope"}, headers=api.admin_headers())
    assert res.status == 404

    res = await api.client.request("GET", f"/work-items/{two['id']}", headers=api.admin_headers())
    assert res.json()["source_id"] == second_source
    res = await api.client.request("GET", "/work-items/9999", headers=api.admin_headers())
    assert res.status == 404


async def test_delete_item(api: Harness):
    _, source_id = await api.seed_style_and_source()
    item = await _file(api, source_id, _letter_item())
    res = await api.client.request(
        "DELETE", f"/sources/{source_id}/work-items/{item['id']}", headers=api.admin_headers()
    )
    assert res.status == 204
    res = await api.client.request("GET", f"/sources/{source_id}/work-items", headers=api.admin_headers())
    assert res.json() == []
    res = await api.client.request(
        "DELETE", f"/sources/{source_id}/work-items/{item['id']}", headers=api.admin_headers()
    )
    assert res.status == 404


async def test_every_route_is_admin_gated(api: Harness):
    """Work items are internal notes — unlike the occurrence reads, even GET
    needs the admin header. The source-free session routes included."""
    _, source_id = await api.seed_style_and_source()
    item = await _file(api, source_id, _letter_item())
    for method, path, body in (
        ("GET", f"/sources/{source_id}/work-items", None),
        ("POST", f"/sources/{source_id}/work-items", _letter_item()),
        ("PATCH", f"/sources/{source_id}/work-items/{item['id']}", {"note": "x"}),
        ("DELETE", f"/sources/{source_id}/work-items/{item['id']}", None),
        ("GET", "/work-items", None),
        ("GET", f"/work-items/{item['id']}", None),
        ("PATCH", f"/work-items/{item['id']}", {"note": "x"}),
    ):
        res = await api.client.request(method, path, json_body=body)
        assert res.status == 401, f"{method} {path} is not gated"


async def test_rejects_unworkable_targets_and_unknown_keys(api: Harness):
    _, source_id = await api.seed_style_and_source()
    for body in (
        {"kind": "letter", "note": "welcher Buchstabe?"},  # letter without glyph_key
        {"kind": "pair", "left_key": "n"},  # pair missing the right side
        {"kind": "word", "note": "welches Wort?"},  # word without word or specimen
        {"kind": "word", "word": "wenn", "specimen_id": "wenn"},  # specimen id without its namespace
        {"kind": "letter", "glyph_key": "n", "specimen_kind": "word"},  # namespace without id
        {"kind": "ligature", "glyph_key": "ch"},  # not a marked level
        _letter_item(glyph_key="zz9"),  # not a registry glyph
        {"kind": "pair", "left_key": "n", "right_key": "zz9"},
    ):
        res = await api.client.request(
            "POST", f"/sources/{source_id}/work-items", json_body=body, headers=api.admin_headers()
        )
        assert res.status == 422, body

    # An unknown status filter is a typo, not an empty result.
    res = await api.client.request(
        "GET", f"/sources/{source_id}/work-items", params={"status": "offen"}, headers=api.admin_headers()
    )
    assert res.status == 422


# ------------------------------------------------- The protocol rule in isolation


@pytest.mark.parametrize(
    ("stored", "changes", "expected_ok"),
    [
        # No status move: a note edit never needs protocol fields.
        ({}, {"note": "nachgetragen"}, True),
        # Rejecting must never be harder than filing.
        ({"understanding": "…"}, {"status": "open"}, True),
        # 'ack' needs both halves of the restatement.
        ({}, {"status": "ack", "understanding": "verstanden", "reproduced": "no"}, True),
        ({}, {"status": "ack", "understanding": "verstanden"}, False),
        ({}, {"status": "ack", "reproduced": "yes"}, False),
        ({}, {"status": "ack", "understanding": "\n ", "reproduced": "yes"}, False),
        # Closing: the stored understanding counts, so an acked row needs only
        # stage + resolution…
        ({"understanding": "verstanden"}, {"status": "done", "stage": "laufform", "resolution": "gefixt"}, True),
        ({"understanding": "verstanden"}, {"status": "done", "stage": "laufform"}, False),
        ({"understanding": "verstanden"}, {"status": "done", "resolution": "gefixt"}, False),
        # …and a row that never acked cannot close, whatever it reports.
        ({}, {"status": "done", "stage": "laufform", "resolution": "gefixt"}, False),
        # Same gate for the hand-back.
        ({"understanding": "verstanden"}, {"status": "returned", "stage": "chart_ductus", "resolution": "…"}, True),
        ({}, {"status": "returned", "stage": "chart_ductus", "resolution": "…"}, False),
        # A single PATCH may ack and close at once as long as it carries it all.
        ({}, {"status": "done", "understanding": "u", "stage": "join_rule", "resolution": "r"}, True),
    ],
)
def test_check_transition_rules(stored: dict, changes: dict, expected_ok: bool):
    problem = check_transition(stored, changes)
    assert (problem is None) is expected_ok, problem


def test_check_transition_names_the_missing_fields():
    problem = check_transition({}, {"status": "done", "stage": "laufform"})
    assert problem is not None
    assert "understanding" in problem and "resolution" in problem
    assert "stage" not in problem.split("missing:")[1].split(".")[0]
    # The message points at the doctrine, so a session can fix itself.
    assert "optimierungs-werkbank.md" in problem
