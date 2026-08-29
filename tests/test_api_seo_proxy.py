"""The crawler pages: `GET /seo-proxy/{route}` serves the prerendered file of a
public route from `settings.prerender_dir`, the prerendered 404 (status 404)
for anything else, and never anything outside that directory.

The files themselves are the app build's output (app/prerender/, pinned by
app/src/lib/seo/prerender.test.ts); here a temp directory stands in for them,
plus one test that the COMMITTED directory has what the image will ship.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from api.routers import seo
from core.config import REPO_ROOT, settings
from tests.api_harness import Harness


@pytest.fixture
def prerender_dir(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / "index.html").write_text("<!-- p -->\n<title>Start</title>", encoding="utf-8")
    (tmp_path / "schriftkunde.html").write_text("<!-- p -->\n<title>Schriftkunde</title>", encoding="utf-8")
    (tmp_path / "schreiben").mkdir()
    (tmp_path / "schreiben" / "uebungsblatt.html").write_text("<!-- p -->\n<title>Blatt</title>", encoding="utf-8")
    (tmp_path / "404.html").write_text(
        '<meta name="robots" content="noindex,follow"><title>404</title>', encoding="utf-8"
    )
    monkeypatch.setattr(settings, "prerender_dir", tmp_path)
    seo._page.cache_clear()
    yield tmp_path
    seo._page.cache_clear()


async def _get(api: Harness, path: str):
    return await api.client.request("GET", path)


async def test_serves_the_page_of_a_route(api: Harness, prerender_dir: Path):
    for path, title in (
        ("/seo-proxy/", "Start"),
        ("/seo-proxy/schriftkunde", "Schriftkunde"),
        ("/seo-proxy/schriftkunde/", "Schriftkunde"),
        ("/seo-proxy/schreiben/uebungsblatt", "Blatt"),
    ):
        res = await _get(api, path)
        assert res.status == 200, path
        assert res.headers["content-type"].startswith("text/html")
        # Never edge-cached: a cached page never reaches the read counter.
        assert res.headers["cache-control"] == "private, no-store"
        assert f"<title>{title}</title>" in res.body.decode()


async def test_head_answers_like_get(api: Harness, prerender_dir: Path):
    """Crawlers and link checkers probe with HEAD first; a 405 would read as a
    dead page (it did, until 2026-08-29). Status and headers are the GET's —
    content-length included, so a checker learns the page's size. The body
    itself is dropped by the server (uvicorn), not by the handler; the
    in-process harness still carries it, so only the headers are compared."""
    for path, status in (("/seo-proxy/schriftkunde", 200), ("/seo-proxy/gibt-es-nicht", 404)):
        get = await _get(api, path)
        head = await api.client.request("HEAD", path)
        assert head.status == get.status == status, path
        for name in ("content-type", "cache-control", "content-length"):
            assert head.headers[name] == get.headers[name], (path, name)


async def test_unknown_route_gets_the_prerendered_404_with_status_404(api: Harness, prerender_dir: Path):
    res = await _get(api, "/seo-proxy/gibt-es-nicht")
    assert res.status == 404
    assert res.headers["cache-control"] == "private, no-store"
    assert "noindex" in res.body.decode()


@pytest.mark.parametrize(
    "route",
    [
        "../secret",
        "schriftkunde.html",  # the file name is not a route — no duplicate URL
        "Schriftkunde",  # routes are lowercase
        "schreiben/../index",
        "%2e%2e/index",
        "index.html",
        # The two file names that are not routes: only the EMPTY route is the
        # home page, and the error page is never a 200 page of its own.
        "index",
        "404",
        "404/",
    ],
)
async def test_nothing_but_a_route_name_reaches_the_disk(api: Harness, prerender_dir: Path, route: str):
    (prerender_dir.parent / "secret.html").write_text("<title>leak</title>", encoding="utf-8")
    res = await _get(api, f"/seo-proxy/{route}")
    assert res.status == 404
    body = res.body.decode()
    assert "leak" not in body
    assert "<title>Start</title>" not in body  # never the home page under another name


async def test_missing_prerender_directory_still_answers_a_noindex_404(api: Harness, tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "prerender_dir", tmp_path / "nowhere")
    seo._page.cache_clear()
    try:
        res = await _get(api, "/seo-proxy/schriftkunde")
        assert res.status == 404
        assert "noindex" in res.body.decode()
    finally:
        seo._page.cache_clear()


def test_the_committed_prerender_directory_has_what_the_image_ships():
    """api/Dockerfile copies app/prerender/ — the pages the app build wrote
    and committed. Without them every crawler would get the 404 page."""
    d = REPO_ROOT / "app" / "prerender"
    for name in ("index.html", "404.html", "schriftkunde.html", "schreiben/uebungsblatt.html"):
        assert (d / name).is_file(), f"app/prerender/{name} missing — run `npm run prerender` in app/ and commit"
    assert (d / "index.html").read_text(encoding="utf-8").startswith("<!-- kurrentschrift.ink prerender -->")
