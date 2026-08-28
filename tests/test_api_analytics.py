"""Server-side bot analytics (api/analytics.py + the middleware in api/main.py).

Adapted from anyplot's suite: the taxonomy, the neutral sender agent, the
visitor-IP rule, the status-as-property rule and the middleware's public-path
mapping are the properties that made anyplot's bot site usable — each one was
found by watching events vanish."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api import main as api_main
from api.analytics import AI_AGENTS, BOT_SENDER_UA, classify_asset, detect_ai_agent, track_asset_fetch, track_bot_fetch
from api.request_context import visitor_ip
from core.config import settings
from tests.api_harness import Harness


@pytest.fixture(autouse=True)
def _analytics_on(monkeypatch):
    # The default is production-only; the suite runs as `development`.
    monkeypatch.setattr(settings, "bot_analytics", True)


def _request(user_agent: str, **headers: str) -> MagicMock:
    request = MagicMock()
    request.headers = {"user-agent": user_agent, **headers}
    request.client.host = "203.0.113.7"
    return request


# ------------------------------------------------------------------ taxonomy


@pytest.mark.parametrize(
    ("user_agent", "expected"),
    [
        ("Mozilla/5.0 (compatible; Claude-User/1.0)", ("claude", "user_directed")),
        ("Mozilla/5.0 (compatible; Claude-SearchBot/1.0)", ("claude", "index")),
        ("Mozilla/5.0 (compatible; ClaudeBot/1.0; +claudebot@anthropic.com)", ("claude", "training")),
        ("Mozilla/5.0 (compatible; ChatGPT-User/1.0; +https://openai.com/bot)", ("chatgpt", "user_directed")),
        ("Mozilla/5.0 (compatible; GPTBot/1.4)", ("chatgpt", "training")),
        ("Mozilla/5.0 (compatible; Google-InspectionTool/1.0)", ("google", "inspection")),
        ("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", ("google", "search")),
        ("MistralAI-User/1.0", ("mistral", "user_directed")),
        ("Mozilla/5.0 (compatible; Applebot-Extended/1.0)", ("apple", "search")),
        # The bare xAI tokens the nginx map serves: plain "Grok" and "xAI-Bot"
        # (no grok substring) were prerendered but not counted until these
        # patterns existed — mirrored from anyplot #10808.
        ("Grok/1.0", ("grok", "user_directed")),
        ("Mozilla/5.0 (compatible; xAI-Bot/1.0)", ("grok", "user_directed")),
    ],
)
def test_detect_ai_agent_classifies_vendor_and_kind(user_agent: str, expected: tuple[str, str]) -> None:
    assert detect_ai_agent(user_agent) == expected


@pytest.mark.parametrize(
    "user_agent",
    [
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Twitterbot/1.0",  # a preview bot, not an assistant — the main site's business
        "",
    ],
)
def test_detect_ai_agent_ignores_humans_and_previews(user_agent: str) -> None:
    assert detect_ai_agent(user_agent) is None


def test_specific_patterns_come_before_their_prefixes() -> None:
    """Substring matching, first match wins — `claude-user` must never be
    shadowed by `claudebot`, `google-inspectiontool` never by `googlebot`."""
    order = [pattern for pattern, _, _ in AI_AGENTS]
    for specific, broad in (
        ("claude-user", "claudebot"),
        ("google-inspectiontool", "googlebot"),
        ("gptbot", "chatgpt-user"),
    ):
        if broad in specific:
            assert order.index(specific) < order.index(broad)


# ------------------------------------------------------------------ track_bot_fetch


async def test_records_against_the_bot_site_with_the_public_url_and_props() -> None:
    with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        track_bot_fetch(_request("MistralAI-User/1.0"), "/schreiben/uebungsblatt", 200)
        await asyncio.sleep(0)  # let the fire-and-forget task run

        payload = mock_client.post.call_args[1]["json"]
        assert payload["domain"] == settings.plausible_bots_domain == "bots.kurrentschrift.ink"
        assert payload["name"] == "bot_fetch"
        assert payload["url"] == "https://kurrentschrift.ink/schreiben/uebungsblatt"
        assert payload["props"] == {
            "assistant": "mistral",
            "kind": "user_directed",
            "path": "/schreiben/uebungsblatt",
            "status": "200",
        }


async def test_events_travel_under_the_neutral_agent() -> None:
    """Plausible drops events whose UA it identifies as a bot — every UA on
    this path. The identity is not lost: it travels in the props."""
    with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        track_bot_fetch(_request("Mozilla/5.0 (compatible; Claude-User/1.0)"), "/schriftkunde", 200)
        await asyncio.sleep(0)

        call = mock_client.post.call_args[1]
        assert call["headers"]["User-Agent"] == BOT_SENDER_UA
        assert call["json"]["props"]["assistant"] == "claude"


async def test_reports_the_visitor_not_our_own_infrastructure() -> None:
    """Plausible uses the FIRST valid forwarded address and drops events that
    carry a CDN/server address — handing it the rightmost entry (ours) loses
    every event silently."""
    request = _request(
        "Mozilla/5.0 (compatible; Claude-User/1.0)", **{"x-forwarded-for": "unknown, 203.0.113.7, 10.0.0.9"}
    )
    request.client.host = "127.0.0.1"
    with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        track_bot_fetch(request, "/", 200)
        await asyncio.sleep(0)

        assert mock_client.post.call_args[1]["headers"]["X-Forwarded-For"] == "203.0.113.7"


async def test_a_miss_is_recorded_with_its_status() -> None:
    with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        track_bot_fetch(_request("Mozilla/5.0 (compatible; Claude-User/1.0)"), "/gibt-es-nicht", 404)
        await asyncio.sleep(0)

        assert mock_client.post.call_args[1]["json"]["props"]["status"] == "404"


async def test_sends_nothing_for_a_human() -> None:
    with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        track_bot_fetch(_request("Mozilla/5.0 (X11; Linux) Chrome/126.0 Safari/537.36"), "/", 200)
        await asyncio.sleep(0)

        mock_client.post.assert_not_called()


async def test_sends_nothing_when_disabled(monkeypatch) -> None:
    """A dev run must never write to the live bot site."""
    monkeypatch.setattr(settings, "bot_analytics", None)
    monkeypatch.setattr(settings, "environment", "development")
    assert settings.bot_analytics_enabled is False
    with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        track_bot_fetch(_request("Mozilla/5.0 (compatible; Claude-User/1.0)"), "/", 200)
        await asyncio.sleep(0)

        mock_client.post.assert_not_called()
    monkeypatch.setattr(settings, "environment", "production")
    assert settings.bot_analytics_enabled is True


def test_a_failed_send_never_raises(caplog) -> None:
    """Analytics must never take a request down — the failure goes to the log."""

    async def run() -> None:
        with patch("api.analytics.httpx.AsyncClient", side_effect=RuntimeError("boom")):
            track_bot_fetch(_request("Mozilla/5.0 (compatible; Claude-User/1.0)"), "/", 200)
            await asyncio.sleep(0)

    asyncio.run(run())
    assert "Plausible tracking failed" in caplog.text


# ------------------------------------------------------------------ visitor_ip


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        # The crawler path: nginx forwards the crawler first, Cloudflare then
        # appends the container's hop and sets cf-connecting-ip to the
        # container's Google egress — the one address Plausible drops.
        ({"cf-connecting-ip": "34.90.1.1", "x-forwarded-for": "203.0.113.7, 172.71.1.1, 34.90.1.1"}, "203.0.113.7"),
        ({"cf-connecting-ip": "198.51.100.4", "x-forwarded-for": "203.0.113.7"}, "203.0.113.7"),
        ({"x-forwarded-for": "203.0.113.7, 10.0.0.9"}, "203.0.113.7"),
        ({"x-forwarded-for": "unknown, 203.0.113.7"}, "203.0.113.7"),
        ({"cf-connecting-ip": "not-an-ip", "x-forwarded-for": "2001:db8::1"}, "2001:db8::1"),
        # No usable forwarded entry: Cloudflare's own header, then the peer.
        ({"cf-connecting-ip": "198.51.100.4", "x-forwarded-for": "unknown"}, "198.51.100.4"),
        ({}, "203.0.113.7"),
    ],
)
def test_visitor_ip_takes_the_first_valid_forwarded_address(headers: dict[str, str], expected: str) -> None:
    assert visitor_ip(_request("x", **headers)) == expected


# ------------------------------------------------------------------ middleware


async def test_middleware_reports_the_public_path_and_the_status(api: Harness, tmp_path, monkeypatch) -> None:
    """The hook fires once per /seo-proxy request with the PUBLIC path (the
    proxy prefix stripped, the root as "/") and the status the handler
    produced — a 404 is reported as 404."""
    monkeypatch.setattr(settings, "prerender_dir", tmp_path)
    (tmp_path / "index.html").write_text("<title>x</title>", encoding="utf-8")
    (tmp_path / "schriftkunde.html").write_text("<title>y</title>", encoding="utf-8")
    (tmp_path / "404.html").write_text("<title>404</title>", encoding="utf-8")
    from api.routers import seo

    seo._page.cache_clear()
    ua = {"User-Agent": "Mozilla/5.0 (compatible; Claude-User/1.0)"}
    with patch.object(api_main, "track_bot_fetch") as track:
        await api.client.request("GET", "/seo-proxy/schriftkunde", headers=ua)
        await api.client.request("GET", "/seo-proxy/", headers=ua)
        await api.client.request("GET", "/seo-proxy/gibt-es-nicht/", headers=ua)
    seo._page.cache_clear()
    calls = [(c.args[1], c.args[2]) for c in track.call_args_list]
    assert calls == [("/schriftkunde", 200), ("/", 200), ("/gibt-es-nicht", 404)]


async def test_middleware_ignores_machine_files_and_api_reads(api: Harness) -> None:
    ua = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)"}
    with patch.object(api_main, "track_bot_fetch") as track, patch.object(api_main, "track_asset_fetch") as assets:
        await api.client.request("GET", "/robots.txt", headers=ua)
        await api.client.request("GET", "/styles", headers=ua)
        await api.client.request("GET", "/health", headers=ua)
    track.assert_not_called()
    assets.assert_not_called()


# ------------------------------------------------------------------ asset fetches


@pytest.mark.parametrize(
    ("path", "text", "expected"),
    [
        ("/sources/suetterlin-1922/write/glyphs/e.svg", None, ("glyph_svg", "suetterlin-1922", "e")),
        ("/sources/suetterlin-1922/write/glyphs/longs", None, ("glyph_json", "suetterlin-1922", "longs")),
        ("/sources/loth-1866/write/word.svg", "  Glück  ", ("word_svg", "loth-1866", "Glück")),
        (
            "/sources/suetterlin-1922/write/word",
            "lesen und schreiben",
            ("word_json", "suetterlin-1922", "lesen und schreiben"),
        ),
        ("/sources/suetterlin-1922/bboxes/e/crop", None, ("crop", "suetterlin-1922", "e")),
        ("/sources/suetterlin-1922/write/glyphs", None, None),  # the batch read
        ("/sources/suetterlin-1922/templates", None, None),  # the inventory
        ("/sources/suetterlin-1922/bboxes/status", None, None),
        ("/seo-proxy/schriftkunde", None, None),
    ],
)
def test_classify_asset(path: str, text: str | None, expected) -> None:
    assert classify_asset(path, text) == expected


def test_classify_asset_caps_the_word_text() -> None:
    _, _, key = classify_asset("/sources/s/write/word.svg", "x" * 200)
    assert key == "x" * 80


def test_classify_asset_normalises_the_word_text_like_the_route() -> None:
    """A decomposed and a composed umlaut are one word to /word (NFC) — and
    one dashboard key. The first literal below carries `u` + U+0308 (combining
    diaeresis), invisibly different from the precomposed `ü` in the second."""
    decomposed = classify_asset("/sources/s/write/word.svg", "Glück")
    composed = classify_asset("/sources/s/write/word.svg", "Glück")
    assert decomposed == composed == ("word_svg", "s", "Glück")
    # The NFC form has five code points; the decomposed input above had six.
    assert len(decomposed[2]) == 5


async def test_asset_fetch_carries_what_who_and_why() -> None:
    request = _request("Mozilla/5.0 (compatible; Claude-User/1.0)")
    request.url.path = "/sources/suetterlin-1922/write/glyphs/e.svg"
    with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        track_asset_fetch(request, asset="glyph_svg", source="suetterlin-1922", key="e", status=200)
        await asyncio.sleep(0)

        call = mock_client.post.call_args[1]
        assert call["headers"]["User-Agent"] == BOT_SENDER_UA
        payload = call["json"]
        assert payload["name"] == "asset_fetch"
        assert payload["domain"] == settings.plausible_bots_domain
        assert payload["url"] == "https://api.kurrentschrift.ink/sources/suetterlin-1922/write/glyphs/e.svg"
        assert payload["props"] == {
            "asset": "glyph_svg",
            "source": "suetterlin-1922",
            "key": "e",
            "assistant": "claude",
            "kind": "user_directed",
            "status": "200",
        }


async def test_asset_fetch_ignores_the_spa_and_curl() -> None:
    with patch("api.analytics.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        for ua in ("Mozilla/5.0 (X11; Linux) Chrome/126.0 Safari/537.36", "curl/8.5.0"):
            track_asset_fetch(_request(ua), asset="crop", source="suetterlin-1922", key="e", status=200)
        await asyncio.sleep(0)
        mock_client.post.assert_not_called()


async def test_middleware_reports_asset_fetches_with_key_and_status(api: Harness) -> None:
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    ua = {"User-Agent": "Mozilla/5.0 (compatible; Claude-User/1.0)"}
    with patch.object(api_main, "track_asset_fetch") as assets:
        await api.client.request("GET", f"/sources/{source_id}/write/glyphs/n.svg", headers=ua)
        await api.client.request("GET", f"/sources/{source_id}/write/word.svg", params={"text": "nn"}, headers=ua)
        await api.client.request("GET", f"/sources/{source_id}/write/glyphs/zz", headers=ua)
        await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": "n"}, headers=ua)
    calls = [(c.kwargs["asset"], c.kwargs["key"], c.kwargs["status"]) for c in assets.call_args_list]
    assert calls == [("glyph_svg", "n", 200), ("word_svg", "nn", 200), ("glyph_json", "zz", 404)]
