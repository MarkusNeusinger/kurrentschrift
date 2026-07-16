"""Authorized admin compute endpoints + the untested public reads.

`test_api_admin_writes.py` covers the bbox/trace/delete write flows; this
suite closes the remaining router gaps found by the audit: the admin compute
endpoints (/trace-preview, /resample incl. its 404/409/423 ladder,
/diagnostic, /fit, /quality), the two chart image endpoints, the single-glyph
write read, the /write/word input bounds + ligature-decompose fallback over
HTTP, and the get-by-id 404s. Same in-memory aiosqlite stack
(`tests/api_harness.py` via the `api` fixture).
"""

from __future__ import annotations

from tests.api_harness import Harness


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _bbox_body(**overrides) -> dict:
    body = {"y0": 100, "y1": 700, "x0": 300, "x1": 500, "baseline_y": 600, "midband_y": 500}
    body.update(overrides)
    return body


def _bar_raw_path() -> list[dict]:
    return [{"x": 400.0, "y": float(y)} for y in range(210, 591, 10)]


async def _seed_traced_glyph(api: Harness, chart_path: str, width_resolver: str = "pressure") -> str:
    """Style + source + bbox + a real /trace against the synthetic chart."""
    _, source_id = await api.seed_style_and_source(width_resolver=width_resolver, chart_path=chart_path)
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
    return source_id


# ------------------------------------------------------------- trace-preview


async def test_trace_preview_returns_raw_and_refined_without_writing(api: Harness, synthetic_chart_path: str):
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(), headers=api.admin_headers()
    )
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/n-medial/trace-preview",
        json_body={"glyph": "n", "position": "medial", "raw_path": _bar_raw_path(), "n_anchors": 24},
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body
    out = res.json()
    assert set(out) == {"raw", "refined"}
    # Dry run: nothing persisted.
    res = await api.client.request("GET", f"/sources/{source_id}/templates/n-medial")
    assert res.status == 404


async def test_trace_preview_constant_style_computes_once(api: Harness, synthetic_chart_path: str):
    """Gleichzug has no edge-refine stage — raw and refined are the same preview."""
    _, source_id = await api.seed_style_and_source(width_resolver="constant", chart_path=synthetic_chart_path)
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(), headers=api.admin_headers()
    )
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/n-medial/trace-preview",
        json_body={"glyph": "n", "position": "medial", "raw_path": _bar_raw_path(), "n_anchors": 24},
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body
    out = res.json()
    assert out["raw"] == out["refined"]


async def test_trace_preview_without_bbox_409(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/n-medial/trace-preview",
        json_body={"glyph": "n", "position": "medial", "raw_path": _bar_raw_path()},
        headers=api.admin_headers(),
    )
    assert res.status == 409


# ------------------------------------------------------------------ resample


async def test_resample_ladder_and_happy_path(api: Harness, synthetic_chart_path: str):
    """The full 409/404/409/423 ladder, then a successful re-derivation."""
    # No bbox at all → 409.
    _, bare_source = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    res = await api.client.request(
        "POST", f"/sources/{bare_source}/templates/n-medial/resample", json_body={}, headers=api.admin_headers()
    )
    assert res.status == 409

    # Bbox but no canonical → 404.
    await api.client.request(
        "PUT", f"/sources/{bare_source}/bboxes/n-medial", json_body=_bbox_body(), headers=api.admin_headers()
    )
    res = await api.client.request(
        "POST", f"/sources/{bare_source}/templates/n-medial/resample", json_body={}, headers=api.admin_headers()
    )
    assert res.status == 404

    # Canonical without raw_path (imported/legacy row) → 409 with the re-trace hint.
    style_id = (await api.client.request("GET", f"/sources/{bare_source}")).json()["style_id"]
    await api.seed_template(style_id, bare_source, "n-medial", "n", "medial")
    res = await api.client.request(
        "POST", f"/sources/{bare_source}/templates/n-medial/resample", json_body={}, headers=api.admin_headers()
    )
    assert res.status == 409
    assert "re-trace" in res.json()["detail"]

    # Fully traced glyph: locked → 423, force → 200 and the template survives.
    source_id = await _seed_traced_glyph(api, synthetic_chart_path)
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(locked=True), headers=api.admin_headers()
    )
    res = await api.client.request(
        "POST", f"/sources/{source_id}/templates/n-medial/resample", json_body={}, headers=api.admin_headers()
    )
    assert res.status == 423
    res = await api.client.request(
        "POST",
        f"/sources/{source_id}/templates/n-medial/resample",
        json_body={"force": True},
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body
    out = res.json()
    assert out["glyph_key"] == "n-medial"
    assert len(out["anchors"]) > 0


# ------------------------------------------------------- diagnostic / quality


async def test_diagnostic_404s_and_happy_path(api: Harness, synthetic_chart_path: str):
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    res = await api.client.request(
        "GET", f"/sources/{source_id}/templates/n-medial/diagnostic", headers=api.admin_headers()
    )
    assert res.status == 404  # no bbox

    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(), headers=api.admin_headers()
    )
    res = await api.client.request(
        "GET", f"/sources/{source_id}/templates/n-medial/diagnostic", headers=api.admin_headers()
    )
    assert res.status == 404  # bbox but no canonical

    traced_source = await _seed_traced_glyph(api, synthetic_chart_path)
    res = await api.client.request(
        "GET", f"/sources/{traced_source}/templates/n-medial/diagnostic", headers=api.admin_headers()
    )
    assert res.status == 200, res.body
    out = res.json()
    # The 3-column payload: crop metadata + skeleton overlay + width profile.
    for key in ("crop_size", "skeleton_polyline_px", "half_widths_px"):
        assert key in out


async def test_quality_409_without_pixel_meta_then_scores_after_trace(api: Harness, synthetic_chart_path: str):
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(), headers=api.admin_headers()
    )
    # A legacy template without pixel-space trace meta → clear 409, not a 500.
    style_id = (await api.client.request("GET", f"/sources/{source_id}")).json()["style_id"]
    await api.seed_template(style_id, source_id, "n-medial", "n", "medial")
    res = await api.client.request(
        "GET", f"/sources/{source_id}/templates/n-medial/quality", headers=api.admin_headers()
    )
    assert res.status == 409

    traced_source = await _seed_traced_glyph(api, synthetic_chart_path)
    res = await api.client.request(
        "GET", f"/sources/{traced_source}/templates/n-medial/quality", headers=api.admin_headers()
    )
    assert res.status == 200, res.body
    out = res.json()
    assert set(out) == {"stored", "candidate", "candidate_refine"}
    assert out["stored"] is not None
    assert out["candidate"] is not None  # raw_path present → dry-run re-derivation ran


async def test_fit_404_without_canonical(api: Harness, synthetic_chart_path: str):
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(), headers=api.admin_headers()
    )
    res = await api.client.request("GET", f"/sources/{source_id}/templates/n-medial/fit", headers=api.admin_headers())
    assert res.status == 404


# ------------------------------------------------------------ chart endpoints


async def test_get_chart_streams_the_source_image(api: Harness, synthetic_chart_path: str):
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    res = await api.client.request("GET", f"/sources/{source_id}/chart")
    assert res.status == 200
    assert res.headers["content-type"] == "image/png"
    assert res.headers["cache-control"] == "public, max-age=86400"
    assert res.body.startswith(PNG_MAGIC)


async def test_get_chart_404_when_file_missing(api: Harness):
    _, source_id = await api.seed_style_and_source()  # deliberately nonexistent chart_path
    res = await api.client.request("GET", f"/sources/{source_id}/chart")
    assert res.status == 404


async def test_get_crop_raw_and_mask_render_png(api: Harness, synthetic_chart_path: str):
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    res = await api.client.request("GET", f"/sources/{source_id}/bboxes/n-medial/crop")
    assert res.status == 404  # no bbox yet

    await api.client.request(
        "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=_bbox_body(), headers=api.admin_headers()
    )
    for view in ("raw", "mask"):
        res = await api.client.request("GET", f"/sources/{source_id}/bboxes/n-medial/crop", params={"view": view})
        assert res.status == 200, (view, res.body[:120])
        assert res.headers["content-type"] == "image/png"
        assert "max-age" in res.headers.get("cache-control", "")
        assert res.body.startswith(PNG_MAGIC)


# ------------------------------------------------------------- write endpoints


async def test_write_single_glyph_payload_and_404(api: Harness, synthetic_chart_path: str):
    source_id = await _seed_traced_glyph(api, synthetic_chart_path)
    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs/n-medial")
    assert res.status == 200, res.body
    out = res.json()
    assert out["glyph_key"] == "n-medial"
    assert "max-age" in res.headers.get("cache-control", "")

    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs/x-medial")
    assert res.status == 404


async def test_write_word_bounds_422(api: Harness, synthetic_chart_path: str):
    _, source_id = await api.seed_style_and_source(chart_path=synthetic_chart_path)
    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "   "})
    assert res.status == 422
    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "x" * 161})
    assert res.status == 422


async def test_write_word_decomposes_missing_ligature_over_http(api: Harness):
    """ "Buch" with no ch-final canonical: the ligature decomposes server-side
    into c+h (second get_many query), so the word still writes with generated
    Übergänge instead of a connector-severing hole."""
    style_id, source_id = await api.seed_style_and_source()
    for key, glyph, position in (
        ("B-initial", "B", "initial"),
        ("u-medial", "u", "medial"),
        ("c-medial", "c", "medial"),
        ("h-final", "h", "final"),
    ):
        await api.seed_template(style_id, source_id, key, glyph, position)
    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "Buch"})
    assert res.status == 200, res.body
    out = res.json()
    assert out["missing"] == []
    # Four letters' silhouettes made it into the draw items (connectors extra).
    assert len([it for it in out["items"] if it.get("rings")]) == 4


# ------------------------------------------------------- bbox geometry sanity


async def test_put_bbox_rejects_degenerate_geometry(api: Harness):
    """Inverted/degenerate rectangles must 422 at write time — stored, they
    would 500 the public crop/derivation reads later."""
    _, source_id = await api.seed_style_and_source()
    for bad in (
        _bbox_body(x0=500, x1=300),  # inverted x
        _bbox_body(y0=700, y1=100, baseline_y=600, midband_y=500),  # inverted y
        _bbox_body(x0=300, x1=300),  # zero width
        _bbox_body(x0=-10),  # negative coordinate
    ):
        res = await api.client.request(
            "PUT", f"/sources/{source_id}/bboxes/n-medial", json_body=bad, headers=api.admin_headers()
        )
        assert res.status == 422, bad


# ----------------------------------------------------------- get-by-id 404s


async def test_get_by_id_404s(api: Harness):
    for path in ("/styles/does-not-exist", "/sources/does-not-exist", "/hands/999999"):
        res = await api.client.request("GET", path)
        assert res.status == 404, path
