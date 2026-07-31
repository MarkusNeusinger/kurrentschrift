"""The work-item endpoints (Werkbank W1): the Auftragskorb's admin API.

Same in-memory aiosqlite stack as the other HTTP suites (`tests/api_harness.py`
via the `api` fixture). Proves the create/list roundtrip per kind, the status
filter a session queries at round start, the partial PATCH that closes an item,
delete, and that every route is admin-gated and rejects an unworkable target.
"""

from __future__ import annotations

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


async def test_create_and_list_per_kind(api: Harness):
    _, source_id = await api.seed_style_and_source()
    letter = await _file(api, source_id, _letter_item(specimen_kind="word", specimen_id="wenn"))
    assert letter["id"] > 0
    assert letter["status"] == "open"
    assert letter["glyph_key"] == "n" and letter["note"] == "Bogen zu flach"
    assert letter["resolution"] is None

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


async def test_patch_closes_item_and_status_filter(api: Harness):
    _, source_id = await api.seed_style_and_source()
    first = await _file(api, source_id, _letter_item())
    second = await _file(api, source_id, _letter_item(glyph_key="e", note="Schleife zu eng"))

    # The session marks one done with its resolution note; the untouched note
    # survives the partial update.
    res = await api.client.request(
        "PATCH",
        f"/sources/{source_id}/work-items/{first['id']}",
        json_body={"status": "done", "resolution": "Ductus nachgezogen, PR #999"},
        headers=api.admin_headers(),
    )
    assert res.status == 200
    out = res.json()
    assert out["status"] == "done"
    assert out["resolution"] == "Ductus nachgezogen, PR #999"
    assert out["note"] == "Bogen zu flach"

    res = await api.client.request(
        "GET", f"/sources/{source_id}/work-items", params={"status": "open"}, headers=api.admin_headers()
    )
    assert [r["id"] for r in res.json()] == [second["id"]]
    res = await api.client.request(
        "GET", f"/sources/{source_id}/work-items", params={"status": "done"}, headers=api.admin_headers()
    )
    assert [r["id"] for r in res.json()] == [first["id"]]

    # A note-only PATCH leaves the status alone.
    res = await api.client.request(
        "PATCH",
        f"/sources/{source_id}/work-items/{second['id']}",
        json_body={"note": "Schleife zu eng, siehe Abb. 19"},
        headers=api.admin_headers(),
    )
    assert res.json()["status"] == "open"
    assert res.json()["note"] == "Schleife zu eng, siehe Abb. 19"

    res = await api.client.request(
        "PATCH", f"/sources/{source_id}/work-items/9999", json_body={"status": "done"}, headers=api.admin_headers()
    )
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
    needs the admin header."""
    _, source_id = await api.seed_style_and_source()
    item = await _file(api, source_id, _letter_item())
    for method, path, body in (
        ("GET", f"/sources/{source_id}/work-items", None),
        ("POST", f"/sources/{source_id}/work-items", _letter_item()),
        ("PATCH", f"/sources/{source_id}/work-items/{item['id']}", {"status": "done"}),
        ("DELETE", f"/sources/{source_id}/work-items/{item['id']}", None),
    ):
        res = await api.client.request(method, path, json_body=body)
        assert res.status == 401, f"{method} {path} is not gated"


async def test_rejects_unworkable_targets_and_unknown_keys(api: Harness):
    _, source_id = await api.seed_style_and_source()
    for body in (
        {"kind": "letter", "note": "welcher Buchstabe?"},  # letter without glyph_key
        {"kind": "pair", "left_key": "n"},  # pair missing the right side
        {"kind": "word", "note": "welches Wort?"},  # word without word or specimen
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
