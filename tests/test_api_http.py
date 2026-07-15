"""HTTP-level API tests — FastAPI app over an in-memory SQLite (aiosqlite) DB.

The suite exercises the real routing/auth/serialization stack without any
Postgres or network; the shared stack (ASGI client + Harness) lives in
`tests/api_harness.py`, the `api` fixture in `tests/conftest.py`. The
authorized admin-write paths are covered by `tests/test_api_admin_writes.py`,
the Cloudflare Access branch by `tests/test_api_auth.py`.

Covered:
- admin gate: 401 for every write endpoint on a missing/wrong X-Admin-Token
  (incl. the compute-heavy GET /fit + /quality), fail-closed 503 when no
  ADMIN_TOKEN is configured;
- public reads: /health, /styles + /sources (empty DB → empty list, with
  Cache-Control), /quiz-words;
- the write path: /write/glyphs batching + `missing`, /write/word happy path
  from seeded synthetic templates, 404/422 error paths.
"""

from __future__ import annotations

import pytest

from core.config import settings
from core.shaping import glyph_keys_of, shape_text
from tests.api_harness import Harness


# ------------------------------------------------------------------ admin gate

# Every admin-gated endpoint (method, path template, JSON body or None). /fit
# and /quality are compute-heavy read endpoints gated like the writes.
WRITE_ENDPOINTS = [
    ("PUT", "/sources/{src}/bboxes/a-medial", {}),
    ("DELETE", "/sources/{src}/bboxes/a-medial", None),
    ("POST", "/sources/{src}/templates/a-medial/trace", {}),
    ("POST", "/sources/{src}/templates/a-medial/trace-preview", {}),
    ("POST", "/sources/{src}/templates/a-medial/resample", {}),
    ("DELETE", "/sources/{src}/templates/a-medial", None),
    ("GET", "/sources/{src}/templates/a-medial/fit", None),
    ("GET", "/sources/{src}/templates/a-medial/quality", None),
]


@pytest.mark.parametrize(("method", "path", "body"), WRITE_ENDPOINTS)
async def test_write_endpoints_reject_missing_token(api: Harness, method: str, path: str, body):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(method, path.format(src=source_id), json_body=body)
    assert res.status == 401, f"{method} {path}: expected 401 without token, got {res.status}"


@pytest.mark.parametrize(("method", "path", "body"), WRITE_ENDPOINTS)
async def test_write_endpoints_reject_wrong_token(api: Harness, method: str, path: str, body):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(
        method, path.format(src=source_id), json_body=body, headers={"X-Admin-Token": "wrong-token"}
    )
    assert res.status == 401, f"{method} {path}: expected 401 on wrong token, got {res.status}"


@pytest.mark.parametrize(("method", "path", "body"), WRITE_ENDPOINTS)
async def test_write_endpoints_fail_closed_without_configured_token(api: Harness, monkeypatch, method, path, body):
    """No ADMIN_TOKEN configured (and no Cloudflare Access) → 503, never open."""
    monkeypatch.setattr(settings, "admin_token", None)
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request(method, path.format(src=source_id), json_body=body)
    assert res.status == 503, f"{method} {path}: expected fail-closed 503, got {res.status}"


# ------------------------------------------------------------------ public reads


async def test_health_ok(api: Harness):
    res = await api.client.request("GET", "/health")
    assert res.status == 200
    assert res.json()["status"] == "healthy"


async def test_styles_empty_db_returns_empty_list_with_cache_control(api: Harness):
    res = await api.client.request("GET", "/styles")
    assert res.status == 200
    assert res.json() == []
    assert "cache-control" in res.headers, "GET /styles must set Cache-Control"


async def test_sources_empty_db_returns_empty_list_with_cache_control(api: Harness):
    res = await api.client.request("GET", "/sources")
    assert res.status == 200
    assert res.json() == []
    assert "cache-control" in res.headers, "GET /sources must set Cache-Control"


async def test_quiz_words_empty_db_returns_empty_list_with_cache_control(api: Harness):
    res = await api.client.request("GET", "/quiz-words")
    assert res.status == 200
    assert res.json() == []
    assert "cache-control" in res.headers


async def test_styles_lists_seeded_style(api: Harness):
    style_id, _ = await api.seed_style_and_source()
    res = await api.client.request("GET", "/styles")
    assert res.status == 200
    rows = res.json()
    assert [r["id"] for r in rows] == [style_id]
    # The chart bytes don't exist on disk, so the style is not authorable.
    assert rows[0]["authorable"] is False


# ------------------------------------------------------------------ write payloads


async def test_write_word_unknown_source_404(api: Harness):
    res = await api.client.request("GET", "/sources/no-such-source/write/word", params={"text": "nn"})
    assert res.status == 404


async def test_write_word_blank_text_422(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "   "})
    assert res.status == 422


async def test_write_glyphs_empty_keys_422(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": " , "})
    assert res.status == 422


async def test_write_glyphs_batch_and_missing(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n-initial", "n", "initial")
    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": "n-initial,zz-medial"})
    assert res.status == 200
    data = res.json()
    assert [g["glyph_key"] for g in data["glyphs"]] == ["n-initial"]
    assert data["missing"] == ["zz-medial"]
    assert "cache-control" in res.headers
    payload = data["glyphs"][0]
    for field in ("outline_paths", "centerlines_template", "entry", "exit_pt", "advance", "template_guides"):
        assert field in payload


async def test_write_word_happy_path_with_seeded_templates(api: Harness):
    """Compose a whole word from synthetic canonicals seeded via the session.

    The glyph keys are derived through the real shaper so the seed always
    matches whatever `core.shaping` emits for the word.
    """
    style_id, source_id = await api.seed_style_and_source()
    word = "nn"
    slots = shape_text(word)
    for slot in slots:
        assert slot.key is not None
        await api.seed_template(style_id, source_id, slot.key, slot.text, slot.position)

    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": word})
    assert res.status == 200
    data = res.json()
    assert data["text"] == word
    assert data["missing"] == []
    # At least one draw item per glyph; connectors/Endstrich may add more.
    assert len(data["items"]) >= len(slots)
    assert "bounds" in data and "guides" in data
    assert "cache-control" in res.headers


async def test_write_word_without_templates_reports_missing(api: Harness):
    """Documented behavior for un-authored glyphs: 200, keys in `missing`,
    the word composes as gaps instead of failing."""
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "nn"})
    assert res.status == 200
    data = res.json()
    assert sorted(data["missing"]) == sorted(glyph_keys_of(shape_text("nn")))
    assert data["items"] == []
