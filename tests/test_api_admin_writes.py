"""Authorized admin-write flows — the paths behind a CORRECT X-Admin-Token.

`test_api_http.py` proves the gate rejects; this suite proves the gated
handlers actually work: bbox PUT/GET roundtrip incl. the coalesce semantics,
the full /trace pipeline against the on-disk synthetic chart, the glyph_key ↔
glyph identity backstop, the 423 lock, and DELETE semantics.
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
        f"/sources/{source_id}/bboxes/n",
        json_body=_bbox_body(n_anchors=42, locked=True),
        headers=api.admin_headers(),
    )
    assert res.status == 200
    out = res.json()
    assert out["glyph_key"] == "n"
    assert (out["y0"], out["y1"], out["x0"], out["x1"]) == (100, 700, 300, 500)
    assert out["n_anchors"] == 42
    assert out["locked"] is True

    res = await api.client.request("GET", f"/sources/{source_id}/bboxes/n")
    assert res.status == 200
    assert res.json() == out


async def test_put_bbox_omitted_fields_preserve_stored_values(api: Harness):
    """The coalesce contract: a plain bbox re-save without locked/n_anchors
    must not wipe the stored flag or silently rewrite the anchor count."""
    _, source_id = await api.seed_style_and_source()
    await api.client.request(
        "PUT",
        f"/sources/{source_id}/bboxes/n",
        json_body=_bbox_body(n_anchors=42, locked=True),
        headers=api.admin_headers(),
    )
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n", json_body=_bbox_body(), headers=api.admin_headers()
    )
    assert res.status == 200
    out = res.json()
    assert out["n_anchors"] == 42
    assert out["locked"] is True


async def test_put_bbox_rejects_baseline_above_midband(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/bboxes/n",
        json_body=_bbox_body(baseline_y=400, midband_y=500),
        headers=api.admin_headers(),
    )
    assert res.status == 422


async def test_put_bbox_rejects_rectangle_beyond_chart(api: Harness):
    """A bbox reaching past the stored chart dimensions must 422 — it would
    store fine but produce a zero-size crop that 500s the public /crop."""
    _, source_id = await api.seed_style_and_source()  # chart_size 800×800
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n", json_body=_bbox_body(x1=900), headers=api.admin_headers()
    )
    assert res.status == 422
    assert "chart dimensions" in res.json()["detail"]
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n", json_body=_bbox_body(y1=801), headers=api.admin_headers()
    )
    assert res.status == 422


async def test_delete_bbox_removes_row(api: Harness):
    _, source_id = await api.seed_style_and_source()
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n", json_body=_bbox_body(), headers=api.admin_headers()
    )
    res = await api.client.request("DELETE", f"/sources/{source_id}/bboxes/n", headers=api.admin_headers())
    assert res.status == 204
    res = await api.client.request("GET", f"/sources/{source_id}/bboxes/n")
    assert res.status == 404


async def test_delete_bbox_nonexistent_404(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("DELETE", f"/sources/{source_id}/bboxes/n", headers=api.admin_headers())
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
        "PUT", f"/sources/{source_id}/bboxes/n", json_body=_bbox_body(locked=True), headers=api.admin_headers()
    )
    res = await api.client.request("GET", f"/sources/{source_id}/bboxes/status")
    assert res.status == 200
    rows = res.json()
    assert rows == [{"glyph_key": "n", "locked": True, "x0": 300, "x1": 500, "y0": 100, "y1": 700, "baseline_y": 600}]


# ------------------------------------------------------------------ trace


async def test_trace_happy_path_persists_template(api: Harness, synthetic_chart_path: str):
    """The full write pipeline: bbox → trace against the on-disk synthetic
    chart → template readable via GET and listed with has_data."""
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n", json_body=_bbox_body(), headers=api.admin_headers()
    )
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/n/trace",
        json_body={"glyph": "n", "raw_path": _bar_raw_path(), "n_anchors": 24},
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body
    out = res.json()
    assert out["glyph_key"] == "n"
    assert out["glyph"] == "n"
    assert len(out["anchors"]) > 0
    assert len(out["half_widths"]) == len(out["anchors"])
    assert out["advance"] > 0

    res = await api.client.request("GET", f"/sources/{source_id}/templates/n")
    assert res.status == 200
    assert res.json()["glyph_key"] == "n"

    res = await api.client.request("GET", f"/sources/{source_id}/templates")
    assert res.status == 200
    rows = res.json()
    assert [r["glyph_key"] for r in rows] == ["n"]
    assert rows[0]["has_data"] is True

    # _sync_bbox_anchor_count: the bbox mirrors the count the derivation used.
    res = await api.client.request("GET", f"/sources/{source_id}/bboxes/n")
    actual = out["trace_meta"].get("n_anchors") or len(out["anchors"])
    assert res.json()["n_anchors"] == actual


async def test_trace_without_bbox_409(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/n/trace",
        json_body={"glyph": "n", "raw_path": _bar_raw_path()},
        headers=api.admin_headers(),
    )
    assert res.status == 409


async def test_trace_locked_bbox_423_then_force_succeeds(api: Harness, synthetic_chart_path: str):
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n", json_body=_bbox_body(locked=True), headers=api.admin_headers()
    )
    body = {"glyph": "n", "position": "medial", "raw_path": _bar_raw_path()}
    res = await api.client.request(
        "POST", f"/sources/{source_id}/templates/n/trace", json_body=body, headers=api.admin_headers()
    )
    assert res.status == 423
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/n/trace",
        json_body={**body, "force": True},
        headers=api.admin_headers(),
    )
    assert res.status == 200


# ------------------------------------------- glyph_key ↔ glyph backstop


async def _trace_status(api: Harness, source_id: str, glyph_key: str, glyph: str) -> int:
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/{glyph_key}/trace",
        json_body={"glyph": glyph, "raw_path": [{"x": 0.0, "y": 0.0}]},
        headers=api.admin_headers(),
    )
    return res.status


async def test_trace_rejects_key_glyph_mismatch(api: Harness):
    """A URL key that names a different glyph than the payload must 422 —
    the upsert conflicts on (style, glyph, variant), so a mismatch would
    rewrite another row's glyph_key (silent 404s afterwards)."""
    _, source_id = await api.seed_style_and_source()
    assert await _trace_status(api, source_id, "a", "b") == 422
    assert await _trace_status(api, source_id, "b", "a") == 422


async def test_trace_allograph_keys_validate_against_registry(api: Harness):
    """The s-allographs are separate glyphs: `longs` belongs to long-s (ſ),
    `s` to the round Schluss-s. 409 (= past validation, bbox missing) vs 422."""
    _, source_id = await api.seed_style_and_source()
    assert await _trace_status(api, source_id, "longs", "ſ") == 409
    assert await _trace_status(api, source_id, "longs", "s") == 422
    assert await _trace_status(api, source_id, "s", "s") == 409
    assert await _trace_status(api, source_id, "s", "ſ") == 422


async def test_trace_unknown_glyph_keeps_custom_key(api: Harness):
    """Glyphs outside the registry subset keep their client-chosen key —
    validation proceeds to the bbox check (409, bbox missing)."""
    _, source_id = await api.seed_style_and_source()
    assert await _trace_status(api, source_id, "clover", "☘") == 409


async def test_trace_unknown_glyph_cannot_claim_registry_key(api: Harness):
    """An out-of-registry glyph posting to a registry-owned key must 422 —
    the upsert would stamp `n` onto the ☘ row and duplicate the key against
    the real n row."""
    _, source_id = await api.seed_style_and_source()
    assert await _trace_status(api, source_id, "n", "☘") == 422
    assert await _trace_status(api, source_id, "longs", "☘") == 422


async def test_trace_stored_row_identity_mismatch_409(api: Harness):
    """Stored-row backstop for keys outside the registry: a key that already
    names one custom glyph refuses a trace re-keying it to another. (Asserted
    on the detail text — a missing bbox also answers 409.)"""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "clover", "☘")
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/clover/trace",
        json_body={"glyph": "♣", "raw_path": [{"x": 0.0, "y": 0.0}]},
        headers=api.admin_headers(),
    )
    assert res.status == 409
    assert "already names" in res.json()["detail"]
    res = await api.client.request("GET", f"/sources/{source_id}/templates/clover")
    assert res.json()["glyph"] == "☘"


# ------------------------------------------------------------------ delete


async def test_delete_template_removes_row(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    res = await api.client.request("DELETE", f"/sources/{source_id}/templates/n", headers=api.admin_headers())
    assert res.status == 204
    res = await api.client.request("GET", f"/sources/{source_id}/templates/n")
    assert res.status == 404


async def test_delete_template_nonexistent_404(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("DELETE", f"/sources/{source_id}/templates/n", headers=api.admin_headers())
    assert res.status == 404


async def test_fit_rejects_out_of_bounds_tuning_params(api: Harness):
    """The /fit tuning knobs feed a scipy optimisation — reject absurd values
    at the boundary instead of burning CPU on them."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    for params in ({"lambda_reg": -1}, {"lambda_reg": 101}, {"width_weight": -0.1}, {"width_weight": 11}):
        res = await api.client.request(
            "GET", f"/sources/{source_id}/templates/n/fit", params=params, headers=api.admin_headers()
        )
        assert res.status == 422, f"{params}: expected 422, got {res.status}"
