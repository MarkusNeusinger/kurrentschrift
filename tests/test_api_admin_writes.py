"""Authorized admin-write flows — the paths behind a CORRECT X-Admin-Token.

`test_api_http.py` proves the gate rejects; this suite proves the gated
handlers actually work: bbox PUT/GET roundtrip incl. the coalesce semantics,
the full /trace pipeline against the on-disk synthetic chart, the glyph_key ↔
(glyph, position) identity backstop, the 423 lock, and DELETE semantics.
Same in-memory aiosqlite stack (`tests/api_harness.py` via the `api` fixture).
"""

from __future__ import annotations

from tests.api_harness import Harness


def _bbox_body(**overrides) -> dict:
    """The synthetic-chart bbox as a PUT body (see conftest.synthetic_bbox)."""
    body = {"y0": 100, "y1": 700, "x0": 300, "x1": 500, "baseline_y": 600, "midband_y": 500}
    body.update(overrides)
    return body


def _bar_raw_path() -> list[dict]:
    """A dense stylus path down the synthetic chart's vertical bar
    (chart-global pixel coords, matching conftest.synthetic_chart)."""
    return [{"x": 400.0, "y": float(y)} for y in range(210, 591, 10)]


# ------------------------------------------------------------------ bbox writes


async def test_put_bbox_roundtrips_via_get(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/bboxes/n-medial",
        json_body=_bbox_body(n_anchors=42, locked=True),
        headers=api.admin_headers(),
    )
    assert res.status == 200
    out = res.json()
    assert out["glyph_key"] == "n-medial"
    assert (out["y0"], out["y1"], out["x0"], out["x1"]) == (100, 700, 300, 500)
    assert out["n_anchors"] == 42
    assert out["locked"] is True

    res = await api.client.request("GET", f"/sources/{source_id}/bboxes/n-medial")
    assert res.status == 200
    assert res.json() == out


async def test_put_bbox_omitted_fields_preserve_stored_values(api: Harness):
    """The coalesce contract: a plain bbox re-save without locked/n_anchors
    must not wipe the stored flag or silently rewrite the anchor count."""
    _, source_id = await api.seed_style_and_source()
    await api.client.request(
        "PUT",
        f"/sources/{source_id}/bboxes/n-medial",
        json_body=_bbox_body(n_anchors=42, locked=True),
        headers=api.admin_headers(),
    )
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(), headers=api.admin_headers()
    )
    assert res.status == 200
    out = res.json()
    assert out["n_anchors"] == 42
    assert out["locked"] is True


async def test_put_bbox_rejects_baseline_above_midband(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/bboxes/n-medial",
        json_body=_bbox_body(baseline_y=400, midband_y=500),
        headers=api.admin_headers(),
    )
    assert res.status == 422


async def test_delete_bbox_removes_row(api: Harness):
    _, source_id = await api.seed_style_and_source()
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(), headers=api.admin_headers()
    )
    res = await api.client.request("DELETE", f"/sources/{source_id}/bboxes/n-medial", headers=api.admin_headers())
    assert res.status == 204
    res = await api.client.request("GET", f"/sources/{source_id}/bboxes/n-medial")
    assert res.status == 404


async def test_bbox_status_lists_flags_and_layout_scalars(api: Harness):
    """The slim public read: availability flags + the Tafel's layout scalars
    per glyph_key, none of the heavy mask/ink/patch fields. The literal
    /status path must win over /{glyph_key}."""
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("GET", f"/sources/{source_id}/bboxes/status")
    assert res.status == 200
    assert res.json() == []

    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(locked=True), headers=api.admin_headers()
    )
    res = await api.client.request("GET", f"/sources/{source_id}/bboxes/status")
    assert res.status == 200
    rows = res.json()
    assert rows == [
        {
            "glyph_key": "n-medial",
            "locked": True,
            "split": False,
            "x0": 300,
            "x1": 500,
            "y0": 100,
            "y1": 700,
            "baseline_y": 600,
        }
    ]


# ------------------------------------------------------------------ trace


async def test_trace_happy_path_persists_template(api: Harness, synthetic_chart_path: str):
    """The full write pipeline: bbox → trace against the on-disk synthetic
    chart → template readable via GET and listed with has_data."""
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(), headers=api.admin_headers()
    )
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/n-medial/trace",
        json_body={"glyph": "n", "position": "medial", "raw_path": _bar_raw_path(), "n_anchors": 24},
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body
    out = res.json()
    assert out["glyph_key"] == "n-medial"
    assert out["glyph"] == "n"
    assert out["position"] == "medial"
    assert len(out["anchors"]) > 0
    assert len(out["half_widths"]) == len(out["anchors"])
    assert out["advance"] > 0

    res = await api.client.request("GET", f"/sources/{source_id}/templates/n-medial")
    assert res.status == 200
    assert res.json()["glyph_key"] == "n-medial"

    res = await api.client.request("GET", f"/sources/{source_id}/templates")
    assert res.status == 200
    rows = res.json()
    assert [r["glyph_key"] for r in rows] == ["n-medial"]
    assert rows[0]["has_data"] is True

    # _sync_bbox_anchor_count: the bbox mirrors the count the derivation used.
    res = await api.client.request("GET", f"/sources/{source_id}/bboxes/n-medial")
    actual = out["trace_meta"].get("n_anchors") or len(out["anchors"])
    assert res.json()["n_anchors"] == actual


async def test_trace_without_bbox_409(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/n-medial/trace",
        json_body={"glyph": "n", "position": "medial", "raw_path": _bar_raw_path()},
        headers=api.admin_headers(),
    )
    assert res.status == 409


async def test_trace_locked_bbox_423_then_force_succeeds(api: Harness, synthetic_chart_path: str):
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(locked=True), headers=api.admin_headers()
    )
    body = {"glyph": "n", "position": "medial", "raw_path": _bar_raw_path()}
    res = await api.client.request(
        "POST", f"/sources/{source_id}/templates/n-medial/trace", json_body=body, headers=api.admin_headers()
    )
    assert res.status == 423
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/n-medial/trace",
        json_body={**body, "force": True},
        headers=api.admin_headers(),
    )
    assert res.status == 200


# ------------------------------------ glyph_key ↔ (glyph, position) backstop


async def _trace_status(api: Harness, source_id: str, glyph_key: str, glyph: str, position: str) -> int:
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/{glyph_key}/trace",
        json_body={"glyph": glyph, "position": position, "raw_path": [{"x": 0.0, "y": 0.0}]},
        headers=api.admin_headers(),
    )
    return res.status


async def test_trace_rejects_key_glyph_mismatch(api: Harness):
    """A URL key that names a different glyph than the payload must 422 —
    the upsert conflicts on (style, glyph, position, variant), so a mismatch
    would rewrite another row's glyph_key (silent 404s afterwards)."""
    _, source_id = await api.seed_style_and_source()
    assert await _trace_status(api, source_id, "a-medial", "b", "medial") == 422
    assert await _trace_status(api, source_id, "a-medial", "a", "final") == 422


async def test_trace_allograph_keys_validate_against_registry(api: Harness):
    """The historical s-keys: `s-medial` belongs to long-s (ſ); round s medial
    is `s-round-medial`. 409 (= past validation, bbox missing) vs 422."""
    _, source_id = await api.seed_style_and_source()
    assert await _trace_status(api, source_id, "s-medial", "ſ", "medial") == 409
    assert await _trace_status(api, source_id, "s-medial", "s", "medial") == 422
    assert await _trace_status(api, source_id, "s-round-medial", "s", "medial") == 409
    assert await _trace_status(api, source_id, "s-final", "s", "final") == 409


async def test_trace_unknown_glyph_falls_back_to_position_suffix(api: Harness):
    """Glyphs outside the registry subset validate by the `{base}-{position}`
    convention only: matching suffix proceeds (409, bbox missing), a foreign
    position suffix is still rejected."""
    _, source_id = await api.seed_style_and_source()
    assert await _trace_status(api, source_id, "clover-medial", "☘", "medial") == 409
    assert await _trace_status(api, source_id, "clover-final", "☘", "medial") == 422


async def test_trace_unknown_glyph_cannot_claim_registry_key(api: Harness):
    """An out-of-registry glyph posting to a registry-owned key (suffix would
    match!) must 422 — the upsert would stamp `n-medial` onto the ☘ row and
    duplicate the key against the real n row."""
    _, source_id = await api.seed_style_and_source()
    assert await _trace_status(api, source_id, "n-medial", "☘", "medial") == 422
    assert await _trace_status(api, source_id, "s-medial", "☘", "medial") == 422


async def test_trace_stored_row_identity_mismatch_409(api: Harness):
    """Stored-row backstop for keys outside the registry: a key that already
    names one custom glyph refuses a trace re-keying it to another. (Asserted
    on the detail text — a missing bbox also answers 409.)"""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "clover-medial", "☘", "medial")
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/clover-medial/trace",
        json_body={"glyph": "♣", "position": "medial", "raw_path": [{"x": 0.0, "y": 0.0}]},
        headers=api.admin_headers(),
    )
    assert res.status == 409
    assert "already names" in res.json()["detail"]
    res = await api.client.request("GET", f"/sources/{source_id}/templates/clover-medial")
    assert res.json()["glyph"] == "☘"


# ------------------------------------------------------------------ delete


async def test_delete_template_removes_row(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n-medial", "n", "medial")
    res = await api.client.request("DELETE", f"/sources/{source_id}/templates/n-medial", headers=api.admin_headers())
    assert res.status == 204
    res = await api.client.request("GET", f"/sources/{source_id}/templates/n-medial")
    assert res.status == 404
