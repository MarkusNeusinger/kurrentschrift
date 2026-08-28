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
- the write path: /write/glyphs batching + `missing` + the `variant` selector
  (chart ductus vs. Laufform row), /write/word happy path from seeded synthetic
  templates, 404/422 error paths.
"""

from __future__ import annotations

import re

import pytest
from fastapi import HTTPException

from core.config import settings
from core.database import LAUFFORM_VARIANT
from core.shaping import glyph_keys_of, shape_text
from tests.api_harness import Harness


# ------------------------------------------------------------------ admin gate

# Every admin-gated endpoint (method, path template, JSON body or None). /fit,
# /quality and /diagnostic are compute-heavy read endpoints gated like the
# writes (each re-runs the image pipeline per request).
WRITE_ENDPOINTS = [
    ("PUT", "/sources/{src}/bboxes/a", {}),
    ("DELETE", "/sources/{src}/bboxes/a", None),
    ("PUT", "/sources/{src}/pairs/n/e", {}),
    ("DELETE", "/sources/{src}/pairs/n/e", None),
    ("POST", "/sources/{src}/templates/a/trace", {}),
    ("POST", "/sources/{src}/templates/a/trace-preview", {}),
    ("POST", "/sources/{src}/templates/a/resample", {}),
    ("DELETE", "/sources/{src}/templates/a", None),
    ("GET", "/sources/{src}/templates/a/fit", None),
    ("GET", "/sources/{src}/templates/a/quality", None),
    ("GET", "/sources/{src}/templates/a/diagnostic", None),
    # The stored-score batch read recomputes nothing, but a quality score is
    # measured over the learned dataset — gated like the rest of the moat.
    ("GET", "/sources/{src}/templates/quality", None),
    # The raw authored template (anchors + stylus path) is the open-core
    # moat — gated like the writes even though it is a read.
    ("GET", "/sources/{src}/templates/a", None),
    # Same moat: the resolved render context carries the pooled nib/pen, i.e.
    # geometry measured over every authored template of the source.
    ("GET", "/sources/{src}/render-context", None),
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


# ------------------------------------------------------------------ config


def test_cors_allow_origin_regex_splits_by_environment(monkeypatch):
    """Production allows only the public site origin; the localhost/LAN
    conveniences exist in development only. An explicit env override wins."""
    monkeypatch.setattr(settings, "cors_origin_regex", None)
    monkeypatch.setattr(settings, "environment", "production")
    prod = settings.cors_allow_origin_regex
    assert re.match(prod, "https://kurrentschrift.ink")
    assert re.match(prod, "https://www.kurrentschrift.ink")
    assert not re.match(prod, "http://kurrentschrift.ink")
    assert not re.match(prod, "http://localhost:3000")
    assert not re.match(prod, "http://192.168.1.20:3000")

    monkeypatch.setattr(settings, "environment", "development")
    dev = settings.cors_allow_origin_regex
    assert re.match(dev, "http://localhost:3000")
    assert re.match(dev, "http://192.168.1.20:3000")

    monkeypatch.setattr(settings, "cors_origin_regex", r"^https://example\.org$")
    assert settings.cors_allow_origin_regex == r"^https://example\.org$"


async def test_require_db_503_detail_distinguishes_init_failure(monkeypatch):
    """`DATABASE_URL is set but the connection failed` must not be answered
    with `Set DATABASE_URL...` — that detail is for the unconfigured case."""
    import api.dependencies as api_dependencies

    monkeypatch.setattr(api_dependencies, "is_db_configured", lambda: False)
    monkeypatch.setattr(api_dependencies, "db_init_failed", lambda: False)
    with pytest.raises(HTTPException) as exc:
        await api_dependencies.require_db(db=None)
    assert exc.value.status_code == 503
    assert "not configured" in exc.value.detail

    monkeypatch.setattr(api_dependencies, "is_db_configured", lambda: True)
    with pytest.raises(HTTPException) as exc:
        await api_dependencies.require_db(db=None)
    assert exc.value.status_code == 503
    assert "initialisation failed" in exc.value.detail


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


async def test_api_robots_txt_opens_the_host_and_reserves_training(api: Harness):
    """The API host's own crawler policy: nothing disallowed (reserved data is
    gated by auth, not by robots rules), retrieval welcome, the /write renders
    kept out of model training."""
    res = await api.client.request("GET", "/robots.txt")
    assert res.status == 200
    assert res.headers["content-type"].startswith("text/plain")
    body = res.body.decode()
    assert "Disallow:" not in body
    assert "Allow: /" in body
    assert "Content-Signal: search=yes,ai-input=yes,ai-train=no" in body
    # The pointer that makes the rest of the surface findable from here: an
    # assistant that lands on this host's robots.txt (the README names it)
    # must be handed the machine guide with the full retrieval URLs.
    assert "https://kurrentschrift.ink/llms.txt" in body


async def test_hands_reads_are_gated_and_never_cacheable(api: Harness):
    """The writer registry indexes the reserved dataset: 401 without the
    token, and the admin's answer must not land in a shared cache."""
    from core.database import Hand

    style_id, _ = await api.seed_style_and_source()
    async with api.session_maker() as session:
        session.add(Hand(id="hand-test", style_id=style_id, label="Testhand", era="1920er", note=None))
        await session.commit()

    assert (await api.client.request("GET", "/hands")).status == 401
    assert (await api.client.request("GET", "/hands/hand-test")).status == 401

    res = await api.client.request("GET", "/hands", headers=api.admin_headers())
    assert res.status == 200
    assert [h["id"] for h in res.json()] == ["hand-test"]
    assert res.headers["cache-control"] == "private, no-store"
    res = await api.client.request("GET", "/hands/hand-test", headers=api.admin_headers())
    assert res.status == 200
    assert res.json()["label"] == "Testhand"
    assert res.headers["cache-control"] == "private, no-store"


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


async def test_write_glyphs_variant_selects_the_laufform_row(api: Harness):
    """`variant` picks WHICH stored form is rendered — the admin letter view
    shows the chart ductus (0) and the derived Laufform (100) side by side.
    A key without a row for the asked variant behaves like an unknown key."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await api.seed_template(style_id, source_id, "n", "n", variant=LAUFFORM_VARIANT)
    await api.seed_template(style_id, source_id, "e", "e")

    res = await api.client.request(
        "GET", f"/sources/{source_id}/write/glyphs", params={"keys": "n,e", "variant": str(LAUFFORM_VARIANT)}
    )
    assert res.status == 200
    data = res.json()
    # Only `n` has a Laufform row; `e` is reported missing rather than falling
    # back to its chart form, which would silently claim a measurement.
    assert [g["glyph_key"] for g in data["glyphs"]] == ["n"]
    assert data["missing"] == ["e"]


async def test_write_glyphs_variant_out_of_range_422(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": "n", "variant": "-1"})
    assert res.status == 422


async def test_write_glyphs_batch_and_missing(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": "n,zz"})
    assert res.status == 200
    data = res.json()
    assert [g["glyph_key"] for g in data["glyphs"]] == ["n"]
    assert data["missing"] == ["zz"]
    assert "cache-control" in res.headers
    payload = data["glyphs"][0]
    for field in ("outline_paths", "centerlines_template", "entry", "exit_pt", "advance", "template_guides"):
        assert field in payload


async def test_write_glyphs_widen_round_bodies_on_the_gleichzug_path(api: Harness):
    """Issue #289 regression: the write path's row builder must pass `glyph`
    through, or `core.pipeline._fluent_widen` (FLUENT_BODY_PITCH) silently dies
    on `/write` while the wordbench fixtures keep measuring with it.

    A pinched `e` body (verticals 0.30 apart, target 0.40) on a Gleichzug
    (`constant`) style must come back widened: the growth of 0.10 shifts the
    exit and the advance right by exactly that much.
    """
    style_id, source_id = await api.seed_style_and_source(width_resolver="constant")
    x2 = 0.8  # second body vertical: 0.5 + the pinched 0.30 pitch
    anchors = [
        [0.0, 0.55],
        [0.25, 0.75],
        [0.5, 1.0],
        [0.5, 0.5],
        [0.5, 0.0],
        [x2 - 0.1, 0.9],
        [x2, 1.0],
        [x2, 0.5],
        [x2, 0.0],
        [x2 + 0.2, 0.25],
        [x2 + 0.45, 0.5],
    ]
    await api.seed_template(
        style_id,
        source_id,
        "e",
        "e",
        anchors=anchors,
        advance=x2 + 0.45,
        entry={"xy": [0.0, 0.55], "tangent_deg": 40.0, "coupling": "midband"},
        exit_pt={"xy": [x2 + 0.45, 0.5], "tangent_deg": 40.0, "coupling": "midband"},
        trace_meta={"stroke_starts": [0]},
    )
    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": "e"})
    assert res.status == 200
    payload = res.json()["glyphs"][0]
    grow = (0.40 / 0.30 - 1.0) * 0.30  # FLUENT_BODY_PITCH["e"] over the seeded pitch
    assert payload["advance"] == pytest.approx(x2 + 0.45 + grow, abs=1e-6)
    assert payload["exit_pt"]["xy"][0] == pytest.approx(x2 + 0.45 + grow, abs=1e-6)
    assert payload["entry"]["xy"] == [0.0, 0.55]  # left of the body — stays put
    assert payload["exit_pt"]["tangent_deg"] == 40.0  # direction rides along untouched


async def test_write_word_happy_path_with_seeded_templates(api: Harness):
    """Compose a whole word from synthetic canonicals seeded via the session.

    The glyph keys are derived through the real shaper so the seed always
    matches whatever `core.shaping` emits for the word.
    """
    style_id, source_id = await api.seed_style_and_source()
    word = "nn"
    slots = shape_text(word)
    assert all(slot.key is not None for slot in slots)
    for key in glyph_keys_of(slots):  # deduped — both n slots share ONE row now
        await api.seed_template(style_id, source_id, key, "n")

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


# ------------------------------------------------------------- render context


async def test_render_context_serves_the_pooled_nib_unrounded(api: Harness):
    """The reason this endpoint exists: the pooled Gleichzug nib at FULL
    precision, where the render payload only carries it rounded to 4 decimals.

    Three templates with 0.061 / 0.073 / 0.089 pool to 0.0743…, whose 4-decimal
    readback is off by ~3e-5 xh — enough to flip a knife-edge ink-clearance
    decision when an offline renderer reproduces a served composition.
    """
    style_id, source_id = await api.seed_style_and_source(width_resolver="constant")
    for key, half_width in (("n", 0.061), ("e", 0.073), ("a", 0.089)):
        await api.seed_template(style_id, source_id, key, key, half_width=half_width)

    res = await api.client.request("GET", f"/sources/{source_id}/render-context", headers=api.admin_headers())
    assert res.status == 200
    ctx = res.json()
    expected = (0.061 + 0.073 + 0.089) / 3
    assert ctx["constant_nib_units"] == pytest.approx(expected, abs=1e-15)
    # Not merely "close": the value must carry the decimals the payload drops.
    assert ctx["constant_nib_units"] != round(ctx["constant_nib_units"], 4)
    assert ctx["width_resolver"] == "constant"
    assert ctx["style_id"] == style_id
    assert ctx["style_ratio"] == [2, 1, 2]
    assert ctx["pen"] is None  # a constant style writes with the nib, not a pen

    # …and it is the SAME nib the public render payload draws with, rounded.
    written = await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": "n"})
    half_widths = written.json()["glyphs"][0]["half_widths_template"]
    assert half_widths[0] == pytest.approx(round(expected, 4))


async def test_render_context_reports_the_pooled_pen_of_a_pressure_style(api: Harness):
    style_id, source_id = await api.seed_style_and_source(width_resolver="pressure")
    await api.seed_template(style_id, source_id, "n", "n", half_width=0.062)

    res = await api.client.request("GET", f"/sources/{source_id}/render-context", headers=api.admin_headers())
    assert res.status == 200
    ctx = res.json()
    # A pressure source has no pooled Gleichzug nib — that scalar is the
    # constant-width path's, and claiming one here would mis-render.
    assert ctx["constant_nib_units"] is None
    assert ctx["pen"]["kind"] == "pressure"
    assert ctx["pen"]["hairline_half"] == pytest.approx(0.062)
    assert ctx["pen"]["nib_width_units"] is None


async def test_render_context_unknown_source_404(api: Harness):
    res = await api.client.request("GET", "/sources/no-such-source/render-context", headers=api.admin_headers())
    assert res.status == 404
