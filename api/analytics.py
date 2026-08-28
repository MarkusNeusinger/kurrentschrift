"""Server-side Plausible events for the crawler path — which assistant read
which page, on whose behalf.

Crawlers execute no JavaScript, so the Plausible script never sees them; the
only place their page reads are visible is the API's `/seo-proxy` handler
(api/routers/seo.py), which the site's nginx sends every mapped crawler UA to.
The middleware in api/main.py reports each of those reads here.

Adapted from `api/analytics.py` in the sister project anyplot — the taxonomy
`AI_AGENTS` is kept identical on purpose (one vocabulary for both sites'
dashboards); the og:image half of anyplot's module has no counterpart here.
Doctrine: docs/reference/crawler-richtlinie.md §3.
"""

from __future__ import annotations

import asyncio
import logging

import httpx
from fastapi import Request

from api.request_context import visitor_ip
from core.config import settings


logger = logging.getLogger(__name__)

PLAUSIBLE_ENDPOINT = "https://plausible.io/api/event"
SITE_ORIGIN = "https://kurrentschrift.ink"

# Plausible discards events whose User-Agent it recognises as a bot, and it
# recognises all of them — anyplot verified this against the live API: the
# same event sent as `Claude-User` never appears, sent as a browser UA it
# does. Forwarding the real crawler UA therefore guarantees the bot site
# records nothing at all. So the events travel under a neutral agent; nothing
# is lost, because the UA only feeds Plausible's browser/OS/device detection
# (meaningless for a crawler) while the identity that matters travels in the
# `assistant` and `kind` properties.
BOT_SENDER_UA = "kurrentschrift-server/1.0"

# Which assistant, and on whose behalf. The distinction is the point: a
# user-directed fetch means a person asked their assistant to open this page,
# which is a reader; an index crawler is building a corpus with no one waiting.
# Ordered most-specific first — matching is substring-based, and e.g.
# "claude-user" must never be shadowed by a broader "claude" pattern.
# Vendor taxonomy per each vendor's own crawler documentation. IDENTICAL to
# anyplot's table by decision — change both in the same breath.
AI_AGENTS: tuple[tuple[str, str, str], ...] = (
    # (user-agent substring, assistant, kind)
    ("claude-user", "claude", "user_directed"),
    ("claude-searchbot", "claude", "index"),
    ("claudebot", "claude", "training"),
    ("chatgpt-user", "chatgpt", "user_directed"),
    ("oai-searchbot", "chatgpt", "index"),
    ("gptbot", "chatgpt", "training"),
    ("perplexity-user", "perplexity", "user_directed"),
    ("perplexitybot", "perplexity", "index"),
    ("gemini-deep-research", "gemini", "user_directed"),
    ("gemininotebook", "gemini", "user_directed"),
    ("notebooklm", "gemini", "user_directed"),
    ("google-agent", "gemini", "user_directed"),
    ("googleagent", "gemini", "user_directed"),
    ("mistralai-user", "mistral", "user_directed"),
    ("mistralai-index", "mistral", "index"),
    ("meta-externalfetcher", "meta", "user_directed"),
    ("meta-webindexer", "meta", "index"),
    ("duckassistbot", "duckduckgo", "user_directed"),
    ("amzn-user", "amazon", "user_directed"),
    ("amzn-searchbot", "amazon", "index"),
    ("grok-deepsearch", "grok", "user_directed"),
    ("grokbot", "grok", "user_directed"),
    ("xai-grok", "grok", "user_directed"),
    ("youbot", "you", "index"),
    ("cohere-ai", "cohere", "user_directed"),
    # Classic search crawlers. Worth recording for the same reason the AI ones
    # are: crawl frequency per engine is otherwise only visible by sampling
    # Search Console's URL inspection one URL at a time.
    ("google-inspectiontool", "google", "inspection"),
    ("googleother", "google", "search"),
    ("googlebot", "google", "search"),
    ("bingbot", "bing", "search"),
    ("duckduckbot", "duckduckgo", "search"),
    ("yandexbot", "yandex", "search"),
    ("baiduspider", "baidu", "search"),
    # Last among the Apple patterns: "applebot" is a substring of
    # "applebot-extended", which is a robots.txt token rather than a real UA —
    # but ordering it here keeps the match correct if that ever changes.
    ("applebot", "apple", "search"),
)


def detect_ai_agent(user_agent: str) -> tuple[str, str] | None:
    """Return (assistant, kind) for a known AI or search agent, else None.

    Matching is substring-based on the lowercased UA, first match wins, so
    AI_AGENTS is ordered most-specific first.
    """
    ua = user_agent.lower()
    for pattern, assistant, kind in AI_AGENTS:
        if pattern in ua:
            return assistant, kind
    return None


# Hold strong references to in-flight fire-and-forget tasks: asyncio only
# weak-references tasks, so without this set the GC can collect them
# mid-flight and silently drop events.
_BACKGROUND_TASKS: set[asyncio.Task] = set()


async def _send_plausible_event(client_ip: str, name: str, url: str, props: dict[str, str], domain: str) -> None:
    """Send one event to Plausible (runs as a background task)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                PLAUSIBLE_ENDPOINT,
                headers={"User-Agent": BOT_SENDER_UA, "X-Forwarded-For": client_ip, "Content-Type": "application/json"},
                json={"name": name, "url": url, "domain": domain, "props": props},
            )
    except Exception as e:  # noqa: BLE001 — analytics must never take a request down
        # warning (not debug) so a broken pipeline is visible in prod logs.
        logger.warning("Plausible tracking failed (non-critical): %s", e)


def _handle_task_exception(task: asyncio.Task) -> None:
    """Surface exceptions from fire-and-forget tasks instead of losing them."""
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as e:  # noqa: BLE001
        logger.warning("Background analytics task failed: %s", e)


def track_bot_fetch(request: Request, path: str, status: int) -> None:
    """Record an AI or search agent requesting a page (fire-and-forget).

    Recorded against the BOT site (`settings.plausible_bots_domain`), never
    the main one: every Plausible event creates a visitor, and mixing crawler
    reads into the human numbers is what made anyplot's trend lines unusable
    (its audit of 2026-07-08: visitors ~40 % too high).

    Non-agent traffic is ignored, so humans and unclassified bots cost nothing
    beyond a substring scan. The `kind` prop is the one that answers the
    question worth asking — `user_directed` means a person asked their
    assistant to open this page, which is a reader; `search`, `index` and
    `training` are machines building a corpus with nobody waiting.

    Args:
        request: FastAPI request, for the UA and forwarded IP
        path: Public path being requested, e.g. "/schriftkunde"
        status: Response status. Recorded rather than filtered on: an
            assistant asking for a URL that does not exist is a signal worth
            having, and counting it as a successful read would be a lie.
            Filter on it in the dashboard.
    """
    if not settings.bot_analytics_enabled:
        return
    detected = detect_ai_agent(request.headers.get("user-agent", ""))
    if detected is None:
        return
    assistant, kind = detected

    props = {"assistant": assistant, "kind": kind, "path": path, "status": str(status)}
    url = f"{SITE_ORIGIN}{path}"
    task = asyncio.create_task(
        _send_plausible_event(visitor_ip(request), "bot_fetch", url, props, settings.plausible_bots_domain)
    )
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)
    task.add_done_callback(_handle_task_exception)
