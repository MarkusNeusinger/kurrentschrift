"""Shared HTTP test harness — FastAPI app over an in-memory SQLite (aiosqlite) DB.

Extracted from `test_api_http.py` so the admin-write and auth suites reuse the
same stack: `get_db` is dependency-overridden with an aiosqlite in-memory
AsyncSession (`Base.metadata.create_all` — the models use a portable JSON type
that maps to JSONB on Postgres only), and the app is driven through a minimal
in-process ASGI client, so the lifespan (which would initialise the real
engine) never runs and no extra HTTP client dependency is needed.

The `api` fixture wiring lives in `tests/conftest.py`.
"""

from __future__ import annotations

import itertools
import json
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import async_sessionmaker

from core.database import Source, Style, Template


ADMIN_TOKEN = "test-admin-token"

# Unique style/source ids per test: api.rendering memoises the pooled pen per
# (style, source) with a 10-minute TTL, so reusing ids across tests would leak
# a pen calibrated from another test's templates.
_ids = itertools.count()


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


class Harness:
    def __init__(self, client: AsgiClient, session_maker: async_sessionmaker):
        self.client = client
        self.session_maker = session_maker

    async def seed_style_and_source(
        self,
        width_resolver: str = "pressure",
        chart_path: str = "data/does-not-exist/chart.png",
        chart_size: dict | None = None,
    ) -> tuple[str, str]:
        """Insert one style + one chart source; returns (style_id, source_id).

        `chart_path` defaults to a nonexistent file (most tests never touch the
        chart bytes); the trace tests pass the on-disk synthetic chart. When a
        real chart is passed, its actual pixel size is read from disk so the
        stored `chart_size` metadata stays truthful.
        """
        n = next(_ids)
        style_id, source_id = f"teststyle{n}", f"test-source-{n}"
        if chart_size is None:
            chart_size = {"w": 100, "h": 100}
            try:
                from PIL import Image

                with Image.open(chart_path) as img:
                    chart_size = {"w": img.width, "h": img.height}
            except OSError:
                pass  # default placeholder for the deliberately-nonexistent chart
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
                    chart_path=chart_path,
                    chart_size=chart_size,
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

    def admin_headers(self) -> dict[str, str]:
        return {"X-Admin-Token": ADMIN_TOKEN}
