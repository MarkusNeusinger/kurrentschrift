"""The occurrence batch endpoints (handmodell H1/H2): /instances + /pair-instances.

Same in-memory aiosqlite stack as the other HTTP suites (`tests/api_harness.py`
via the `api` fixture). Proves the admin gate, the hand get-or-create, the
upsert-vs-replace semantics on the occurrence identity, the registry-key
validation, and that reads are public.
"""

from __future__ import annotations

from sqlalchemy import select

from core.database import Instance
from tests.api_harness import Harness


def _instance_item(**overrides) -> dict:
    item = {
        "glyph_key": "n",
        "glyph": "n",
        "position": "medial",
        "y0": 10,
        "y1": 40,
        "x0": 100,
        "x1": 130,
        "anchors": [[0.0, 0.0], [0.1, 0.5], [0.2, 0.6], [0.3, 0.0]],
        "measurements": {"specimen_id": "wenn", "slot": 1, "geo_rmse_px": 1.2},
    }
    item.update(overrides)
    return item


def _pair_item(**overrides) -> dict:
    item = {
        "left_key": "n",
        "right_key": "e",
        "kind": "word",
        "specimen_id": "wenn",
        "slot": 2,
        "geometry": {"offset": [0.4, 0.0], "connector": [[0.0, 0.0], [0.2, 0.3], [0.4, 0.0]]},
        "measurements": {"fit_ok": True, "gen_chamfer": 0.21},
    }
    item.update(overrides)
    return item


def _batch(items: list[dict], **overrides) -> dict:
    body = {"hand": {"id": "test-hand", "label": "Test norm hand", "era": "1922"}, "items": items}
    body.update(overrides)
    return body


# ------------------------------------------------------------------- instances


async def test_put_instances_stores_rows_creates_hand_and_links_template(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/instances",
        json_body=_batch([_instance_item(), _instance_item(position="final", x0=200, x1=230)]),
        headers=api.admin_headers(),
    )
    assert res.status == 200
    out = res.json()
    assert out == {"hand_id": "test-hand", "stored": 2, "deleted": 0, "skipped": 0}

    # Public read, fresh rows, measurements intact.
    res = await api.client.request("GET", f"/sources/{source_id}/instances", params={"glyph_key": "n"})
    assert res.status == 200
    rows = res.json()
    assert len(rows) == 2
    assert {r["position"] for r in rows} == {"medial", "final"}
    assert all(r["hand_id"] == "test-hand" for r in rows)
    assert rows[0]["measurements"]["specimen_id"] == "wenn"

    # The hand row was get-or-created under the source's style, and the
    # occurrence links its canonical (base-variant) template.
    res = await api.client.request("GET", "/hands")
    assert any(h["id"] == "test-hand" for h in res.json())
    async with api.session_maker() as session:
        stored = (await session.execute(select(Instance))).scalars().all()
        assert all(i.template_id is not None for i in stored)


async def test_put_instances_upserts_on_identity_and_replace_wipes(api: Harness):
    _, source_id = await api.seed_style_and_source()
    body = _batch([_instance_item(), _instance_item(x0=200)])
    await api.client.request("PUT", f"/sources/{source_id}/instances", json_body=body, headers=api.admin_headers())
    # Same identities again → refreshed in place, not duplicated.
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/instances", json_body=body, headers=api.admin_headers()
    )
    assert res.status == 200 and res.json()["stored"] == 2
    res = await api.client.request("GET", f"/sources/{source_id}/instances")
    assert len(res.json()) == 2

    # replace=true is a full re-harvest: old rows go, the batch remains.
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/instances",
        json_body=_batch([_instance_item(x0=300)], replace=True),
        headers=api.admin_headers(),
    )
    assert res.json() == {"hand_id": "test-hand", "stored": 1, "deleted": 2, "skipped": 0}
    res = await api.client.request("GET", f"/sources/{source_id}/instances")
    assert [r["x0"] for r in res.json()] == [300]


async def test_put_instances_gate_and_validation(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("PUT", f"/sources/{source_id}/instances", json_body=_batch([_instance_item()]))
    assert res.status == 401
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/instances",
        json_body=_batch([_instance_item(glyph_key="zz9")]),
        headers=api.admin_headers(),
    )
    assert res.status == 422
    res = await api.client.request("DELETE", f"/sources/{source_id}/instances", headers=api.admin_headers())
    assert res.status == 200 and res.json() == {"deleted": 0}


async def test_hand_id_reuse_across_styles_conflicts(api: Harness):
    """A hand belongs to ONE style — writing the same hand id under a source
    of another style must 409 instead of silently reassigning the hand."""
    _, source_a = await api.seed_style_and_source()
    _, source_b = await api.seed_style_and_source()  # fresh style + source
    res = await api.client.request(
        "PUT", f"/sources/{source_a}/instances", json_body=_batch([_instance_item()]), headers=api.admin_headers()
    )
    assert res.status == 200
    res = await api.client.request(
        "PUT", f"/sources/{source_b}/instances", json_body=_batch([_instance_item()]), headers=api.admin_headers()
    )
    assert res.status == 409
    assert "belongs to style" in res.json()["detail"]


# -------------------------------------------------------------- pair instances


async def test_put_pair_instances_stores_occurrences_per_identity(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/pair-instances",
        json_body=_batch(
            [
                _pair_item(),
                _pair_item(slot=0, left_key="e", right_key="n"),
                # Same (kind, specimen, slot) twice in one batch — last wins,
                # the ON CONFLICT executemany must never see it twice.
                _pair_item(measurements={"fit_ok": False}),
            ]
        ),
        headers=api.admin_headers(),
    )
    assert res.status == 200
    assert res.json() == {"hand_id": "test-hand", "stored": 2, "deleted": 0, "skipped": 0}

    res = await api.client.request("GET", f"/sources/{source_id}/pair-instances", params={"left_key": "n"})
    rows = res.json()
    assert len(rows) == 1
    assert rows[0]["kind"] == "word" and rows[0]["slot"] == 2
    assert rows[0]["measurements"]["fit_ok"] is False  # the batch's last write
    assert rows[0]["geometry"]["offset"] == [0.4, 0.0]

    # The pair drill namespace is separate: same specimen id + slot, kind=pair.
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/pair-instances",
        json_body=_batch([_pair_item(kind="pair")]),
        headers=api.admin_headers(),
    )
    assert res.json()["stored"] == 1
    res = await api.client.request("GET", f"/sources/{source_id}/pair-instances")
    assert len(res.json()) == 3


async def test_put_pair_instances_gate_and_validation(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("PUT", f"/sources/{source_id}/pair-instances", json_body=_batch([_pair_item()]))
    assert res.status == 401
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/pair-instances",
        json_body=_batch([_pair_item(right_key="zz9")]),
        headers=api.admin_headers(),
    )
    assert res.status == 422


# -------------------------------------------------------------- word instances


def _word_item(**overrides) -> dict:
    item = {
        "kind": "word",
        "specimen_id": "wenn",
        "word": "wenn",
        "slots": ["w", "e", "n", "n"],
        "strokes": [[[0.0, 0.0], [0.4, 0.9], [0.8, 0.0]], [[1.0, 0.0], [1.3, 0.6], [1.6, 0.0]]],
        "provenance": "traced",
        "measurements": {"xh_px": 31.0, "fitted_slots": [0, 1]},
    }
    item.update(overrides)
    return item


async def test_put_word_instances_roundtrip_and_authored_protection(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/word-instances", json_body=_batch([_word_item()]), headers=api.admin_headers()
    )
    assert res.status == 200
    assert res.json() == {"hand_id": "test-hand", "stored": 1, "deleted": 0, "skipped": 0}

    # The admin traces the word manually — authored replaces traced.
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/word-instances",
        json_body=_batch([_word_item(provenance="authored", strokes=[[[0.0, 0.0], [2.0, 1.0]]])]),
        headers=api.admin_headers(),
    )
    assert res.json()["stored"] == 1

    # Within ONE batch an authored item also beats a later traced one for the
    # same identity — the contract holds regardless of item order.
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/word-instances",
        json_body=_batch([_word_item(provenance="authored", strokes=[[[0.0, 0.0], [2.0, 1.0]]]), _word_item()]),
        headers=api.admin_headers(),
    )
    assert res.json() == {"hand_id": "test-hand", "stored": 1, "deleted": 0, "skipped": 1}

    # A re-harvest (traced, replace=true) must NOT touch the authored row:
    # replace spares it and the traced item for its identity is skipped.
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/word-instances",
        json_body=_batch([_word_item(), _word_item(specimen_id="zu", word="zu", slots=["z", "u"])], replace=True),
        headers=api.admin_headers(),
    )
    assert res.json() == {"hand_id": "test-hand", "stored": 1, "deleted": 0, "skipped": 1}

    res = await api.client.request("GET", f"/sources/{source_id}/word-instances", params={"specimen_id": "wenn"})
    rows = res.json()
    assert len(rows) == 1
    assert rows[0]["provenance"] == "authored"
    assert rows[0]["strokes"] == [[[0.0, 0.0], [2.0, 1.0]]]

    # ?word= lists every occurrence of one word TEXT (repeated words carry
    # distinct specimen ids but share `word`).
    await api.client.request(
        "PUT",
        f"/sources/{source_id}/word-instances",
        json_body=_batch([_word_item(specimen_id="wenn-2")]),
        headers=api.admin_headers(),
    )
    res = await api.client.request("GET", f"/sources/{source_id}/word-instances", params={"word": "wenn"})
    assert {r["specimen_id"] for r in res.json()} == {"wenn", "wenn-2"}

    # DELETE protects authored work unless explicitly included.
    res = await api.client.request("DELETE", f"/sources/{source_id}/word-instances", headers=api.admin_headers())
    assert res.json() == {"deleted": 2}  # only the traced rows ("zu", "wenn-2")
    res = await api.client.request(
        "DELETE",
        f"/sources/{source_id}/word-instances",
        params={"include_authored": "true"},
        headers=api.admin_headers(),
    )
    assert res.json() == {"deleted": 1}


async def test_put_word_instances_gate_and_validation(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("PUT", f"/sources/{source_id}/word-instances", json_body=_batch([_word_item()]))
    assert res.status == 401
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/word-instances",
        json_body=_batch([_word_item(slots=["w", "zz9"])]),
        headers=api.admin_headers(),
    )
    assert res.status == 422
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/word-instances",
        json_body=_batch([_word_item(strokes=[[[0.0]]])]),
        headers=api.admin_headers(),
    )
    assert res.status == 422
