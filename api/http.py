"""Shared HTTP constants for the routers, plus the one validation body this API
phrases itself (`no_query_string_body`)."""

import re
from typing import Any


# Public, rarely-changing render/word-bank payloads: cache hard at browser + edge.
# Template geometry only changes on an admin re-trace and the quiz bank on a
# reseed, so five minutes of browser staleness is fine while `s-maxage` targets
# the CDN and stale-while-revalidate bridges revalidation without a blocking
# round trip. Used by write.py, quiz_words.py, styles.py and sources.py.
CACHE_CONTROL = "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"

# Every admin-gated response (quellen-und-rechte.md §5). A `public` directive
# on an authenticated response is how a shared cache ends up serving the
# admin's answer to the next anonymous request for the same URL — so a gated
# read is never cacheable anywhere. Stamped by `api.auth.require_admin` itself,
# so no gated route can forget it; the eigenhand binaries, which return their
# `Response` directly, carry the same value under their own constant.
NO_STORE = "private, no-store"

# Assets that exist for assistants and crawlers — the written letter or word
# as SVG. Cached in the browser only, never at the edge: Cloudflare caches this
# host by rule, and a cached copy never reaches the middleware that counts the
# fetch (api/analytics.py asset_fetch) — verified 2026-08-28, three of four
# assistant fetches were edge HITs and vanished from the count. The SPA never
# requests these, so nothing human-facing loses the edge cache. The JSON and
# crop reads keep CACHE_CONTROL: the Tafel, the hero word and the quiz ride
# on the edge cache, and their assistant counts are understood as cache
# misses (first fetch per asset per edge TTL), not every fetch.
BROWSER_ONLY_CACHE = "private, max-age=300"

# A read whose whole value is being current: the live Lesart vocabulary's
# metadata, which says which fold bucketed it and therefore whether a reload
# has landed. Under CACHE_CONTROL the answer to that question could be a day
# old at the edge and a week old under stale-while-revalidate — an operational
# signal that arrives after the window it describes is no signal. One row, so
# the origin can afford the misses.
STATUS_CACHE = "public, max-age=30"

# The routes that have a PATH form beside their query form, with the hint
# `no_query_string_body` gives for each: what to fetch instead when the query
# string does not survive the way to this API.
_PATH_FORM_HINTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"^/sources/(?P<source_id>[^/]+)/write/word(?:\.svg)?$"),
        "use the path form instead: /sources/{source_id}/write/word/{text} (JSON) "
        "or /sources/{source_id}/write/word/{text}.svg (SVG image)",
    ),
    (
        re.compile(r"^/sources/(?P<source_id>[^/]+)/write/glyphs$"),
        "one glyph at a time has a path form: /sources/{source_id}/write/glyphs/{glyph_key} (JSON) "
        "or /sources/{source_id}/write/glyphs/{glyph_key}.svg (SVG image)",
    ),
)


def no_query_string_body(path: str, errors: list[dict[str, Any]], query: str) -> dict[str, Any] | None:
    """The 422 body for a request whose WHOLE query string went missing — or
    None when the default validation body is the right answer.

    A strict AI fetch client (Claude's web_fetch, 2026-09-18) normalises an
    unseen URL to the closest one it has already seen and drops the query
    string; cache-key normalisation and corporate proxies do the same. FastAPI
    then answers a correct 422 whose `detail` list names the missing `text` —
    but such a client surfaces only the status code, so the failure is silent,
    and even a client that reads the body meets a list that does not say what
    to do. This body does: it names the failure (`error: no_query_string`), the
    parameters that never arrived, and — where the route has one — the path
    form that carries the same request without a query string.

    Only fires when the request reached the server with NO query at all AND
    every reported problem is a missing query parameter: a wrong value, a
    missing one beside others that arrived, or a body problem keeps the
    default `detail` list, which is the right report for those.
    """
    if query or not errors:
        return None
    if not all(e.get("type") == "missing" and tuple(e.get("loc") or ())[:1] == ("query",) for e in errors):
        return None
    missing = [str(e["loc"][1]) for e in errors if len(e.get("loc") or ()) > 1]
    hint = "the request reached the server without a query string — your client dropped it"
    for pattern, path_form in _PATH_FORM_HINTS:
        match = pattern.match(path)
        if match:
            hint = f"{hint}; {path_form.replace('{source_id}', match.group('source_id'))}"
            break
    return {
        "detail": f"missing query parameter{'s' if len(missing) != 1 else ''}: {', '.join(missing) or '?'}",
        "error": "no_query_string",
        "missing": missing,
        "hint": hint,
    }
