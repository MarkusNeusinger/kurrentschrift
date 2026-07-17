"""Glyph-pair overrides (redesign R3): CRUD endpoints + the composer hook.

The §4 generator remains the default for every join; these tests pin the new
sparse override layer — storage roundtrip, validation, and that /write/word
consumes ONLY approved rows while the no-override path stays byte-identical.
"""

from __future__ import annotations

import pytest

from core.compose import compose_word
from core.shaping import shape_text
from tests.api_harness import Harness


GEOMETRY = {"offset": [0.42, 0.0], "connector": [[0.0, 0.0], [0.2, 0.35], [0.42, 0.55]]}


def _pair_body(**overrides) -> dict:
    body = {"geometry": GEOMETRY, "provenance": "harvested", "specimen_id": "nn", "approved": True}
    body.update(overrides)
    return body


async def test_pair_put_get_list_delete_roundtrip(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/pairs/n/e", json_body=_pair_body(), headers=api.admin_headers()
    )
    assert res.status == 200, res.body
    out = res.json()
    assert (out["left_key"], out["right_key"]) == ("n", "e")
    assert out["approved"] is True
    assert out["geometry"]["connector"] == GEOMETRY["connector"]
    assert out["provenance_source_id"] == source_id

    res = await api.client.request("GET", f"/sources/{source_id}/pairs/n/e")
    assert res.status == 200
    assert res.json() == out

    res = await api.client.request("GET", f"/sources/{source_id}/pairs")
    assert [(r["left_key"], r["right_key"]) for r in res.json()] == [("n", "e")]

    res = await api.client.request("DELETE", f"/sources/{source_id}/pairs/n/e", headers=api.admin_headers())
    assert res.status == 204
    res = await api.client.request("GET", f"/sources/{source_id}/pairs/n/e")
    assert res.status == 404


async def test_pair_put_rejects_unknown_key_and_bad_geometry(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/pairs/zz/e", json_body=_pair_body(), headers=api.admin_headers()
    )
    assert res.status == 422
    # A one-point connector cannot be a join.
    bad = _pair_body(geometry={"offset": [0.4, 0.0], "connector": [[0.0, 0.0]]})
    res = await api.client.request("PUT", f"/sources/{source_id}/pairs/n/e", json_body=bad, headers=api.admin_headers())
    assert res.status == 422
    # Out-of-range coordinates are data breakage, not geometry.
    bad = _pair_body(geometry={"offset": [0.4, 0.0], "connector": [[0.0, 0.0], [999.0, 0.0]]})
    res = await api.client.request("PUT", f"/sources/{source_id}/pairs/n/e", json_body=bad, headers=api.admin_headers())
    assert res.status == 422


async def _composed_nn(api: Harness, source_id: str) -> dict:
    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "nn"})
    assert res.status == 200, res.body
    return res.json()


async def test_write_word_uses_only_approved_overrides(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")

    baseline = await _composed_nn(api, source_id)

    # Unapproved: stored but never rendered — output identical to no override.
    await api.client.request(
        "PUT", f"/sources/{source_id}/pairs/n/n", json_body=_pair_body(approved=False), headers=api.admin_headers()
    )
    assert await _composed_nn(api, source_id) == baseline

    # Approved: the stored connector replaces the generated Übergang verbatim.
    await api.client.request(
        "PUT", f"/sources/{source_id}/pairs/n/n", json_body=_pair_body(approved=True), headers=api.admin_headers()
    )
    overridden = await _composed_nn(api, source_id)
    assert overridden != baseline
    # The connector item is the stored polyline translated to the left exit.
    stroked = [it for it in overridden["items"] if "stroke_width" in it and not it["lift"]]
    connector = stroked[0]
    pts = connector["centerline"]
    assert len(pts) == len(GEOMETRY["connector"])
    ex, ey = pts[0]
    for (px, py), (gx, gy) in zip(pts, GEOMETRY["connector"], strict=True):
        assert px == pytest.approx(ex + gx, abs=1e-9)
        assert py == pytest.approx(ey + gy, abs=1e-9)


def test_compose_word_without_overrides_is_byte_identical():
    """The pair_overrides param must not perturb the default path."""
    slots = shape_text("nn")
    anchors = [[0.0, 0.0], [0.05, 0.45], [0.12, 0.62], [0.25, 0.55], [0.32, 0.25], [0.35, 0.0]]
    payload = {
        "glyph_key": "n",
        "advance": 0.45,
        "entry": {"xy": [0.0, 0.0], "tangent_deg": 60.0, "coupling": "baseline"},
        "exit_pt": {"xy": [0.35, 0.0], "tangent_deg": -60.0, "coupling": "baseline"},
        "anchors_template": anchors,
        "centerlines_template": [anchors],
        "half_widths_template": [0.05] * len(anchors),
        "outline_paths": [],
        "template_guides": {"baseline": 0, "midband": 1, "ascender": 2, "descender": -1},
    }
    payloads = {"n": payload}
    assert compose_word(slots, payloads) == compose_word(slots, payloads, pair_overrides={})
    assert compose_word(slots, payloads) == compose_word(slots, payloads, pair_overrides=None)
