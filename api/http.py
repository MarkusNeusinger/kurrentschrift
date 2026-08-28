"""Shared HTTP constants for the routers."""

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
