"""HTTP-level API tests — FastAPI app over an in-memory SQLite (aiosqlite) DB.

The suite exercises the real routing/auth/serialization stack without any
Postgres or network: `get_db` is dependency-overridden with an aiosqlite
in-memory AsyncSession (`Base.metadata.create_all` — the models use a portable
JSON type that maps to JSONB on Postgres only), and the app is driven through a
minimal in-process ASGI client, so the lifespan (which would initialise the
real engine) never runs and no extra HTTP client dependency is needed.

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

import itertools
import json
from urllib.parse import urlencode

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import api.dependencies as api_dependencies
from api.main import app
from core.config import settings
from core.database import Base, Source, Style, Template, get_db
from core.shaping import glyph_keys_of, shape_text


ADMIN_TOKEN = "test-admin-token"

# Unique style/source ids per test: api.rendering memoises the pooled pen per
# (style, source) with a 10-minute TTL, so reusing ids across tests would leak
# a pen calibrated from another test's templates.
_ids = itertools.count()


# ------------------------------------------------------------------ ASGI client


class _Response:
    def __init__(self, status: int, headers: dict[str, str], body: bytes):
        self.status = status
        self.headers = headers
        self.body = body

    def json(self):
        return json.loads(self.body)


class AsgiClient:
    """Minimal in-process ASGI 3 client (GET/PUT/POST/DELETE, JSON bodies).

    Deliberately does NOT run the lifespan protocol — `api.main`'s lifespan
    would initialise the real DB engine, which these tests replace wholesale.
    No accept-encoding is sent, so GZipMiddleware passes bodies through.
    """

    def __init__(self, asgi_app):
        self.app = asgi_app

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
        json_body: dict | list | None = None,
    ) -> _Response:
        body = json.dumps(json_body).encode() if json_body is not None else b""
        raw_headers = [(b"host", b"testserver")]
        if json_body is not None:
            raw_headers.append((b"content-type", b"application/json"))
        raw_headers.append((b"content-length", str(len(body)).encode()))
        for k, v in (headers or {}).items():
            raw_headers.append((k.lower().encode(), v.encode()))
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": urlencode(params or {}).encode(),
            "root_path": "",
            "headers": raw_headers,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
        received = {"sent": False}
        messages: list[dict] = []

        async def receive():
            if not received["sent"]:
                received["sent"] = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        async def send(message):
            messages.append(message)

        await self.app(scope, receive, send)
        start = next(m for m in messages if m["type"] == "http.response.start")
        out_headers = {k.decode().lower(): v.decode() for k, v in start.get("headers", [])}
        payload = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
        return _Response(start["status"], out_headers, payload)


# ------------------------------------------------------------------ harness


class Harness:
    def __init__(self, client: AsgiClient, session_maker: async_sessionmaker):
        self.client = client
        self.session_maker = session_maker

    async def seed_style_and_source(self, width_resolver: str = "pressure") -> tuple[str, str]:
        """Insert one style + one chart source; returns (style_id, source_id)."""
        n = next(_ids)
        style_id, source_id = f"teststyle{n}", f"test-source-{n}"
        async with self.session_maker() as session:
            session.add(
                Style(
                    id=style_id,
                    name="Test style",
                    width_resolver=width_resolver,
                    default_slant_deg=65.0,
                    default_style_ratio=[2, 1, 2],
                )
            )
            session.add(
                Source(
                    id=source_id,
                    style_id=style_id,
                    kind="chart",
                    title="Synthetic test chart",
                    license="CC0",
                    chart_path="data/does-not-exist/chart.png",
                    chart_size={"w": 100, "h": 100},
                )
            )
            await session.commit()
        return style_id, source_id

    async def seed_template(self, style_id: str, source_id: str, glyph_key: str, glyph: str, position: str) -> None:
        """A minimal but render-valid canonical: an n-like arch in template coords
        (baseline = 0, midband = 1) with a constant hairline width profile."""
        anchors = [[0.0, 0.0], [0.05, 0.45], [0.12, 0.62], [0.25, 0.55], [0.32, 0.25], [0.35, 0.0]]
        async with self.session_maker() as session:
            session.add(
                Template(
                    style_id=style_id,
                    provenance_source_id=source_id,
                    glyph_key=glyph_key,
                    glyph=glyph,
                    position=position,
                    variant=0,
                    advance=0.45,
                    entry={"xy": [0.0, 0.0], "tangent_deg": 60.0, "coupling": "baseline"},
                    exit_pt={"xy": [0.35, 0.0], "tangent_deg": -60.0, "coupling": "baseline"},
                    anchors=anchors,
                    half_widths=[0.05] * len(anchors),
                    raw_path=[],
                    trace_meta={},
                    measurements={},
                )
            )
            await session.commit()


@pytest.fixture
async def api(monkeypatch):
    """The FastAPI app wired to a fresh in-memory aiosqlite DB.

    - `get_db` is dependency-overridden with sessions off a StaticPool engine
      (one shared connection, so seeded rows are visible to request sessions);
    - `api.dependencies.is_db_configured` is forced True so `require_db` passes
      regardless of the host's real DATABASE_URL / .env;
    - a known ADMIN_TOKEN is configured (individual tests may unset it).
    """
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(api_dependencies, "is_db_configured", lambda: True)
    monkeypatch.setattr(settings, "admin_token", ADMIN_TOKEN)

    try:
        yield Harness(AsgiClient(app), session_maker)
    finally:
        app.dependency_overrides.pop(get_db, None)
        await engine.dispose()


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
