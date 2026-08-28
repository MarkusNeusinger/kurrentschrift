"""Shared HTTP constants for the routers."""

# Public, rarely-changing render/word-bank payloads: cache hard at browser + edge.
# Template geometry only changes on an admin re-trace and the quiz bank on a
# reseed, so five minutes of browser staleness is fine while `s-maxage` targets
# the CDN and stale-while-revalidate bridges revalidation without a blocking
# round trip. Used by write.py, quiz_words.py, styles.py and sources.py.
CACHE_CONTROL = "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"

# Admin-gated reads of the reserved dataset (quellen-und-rechte.md §5). A
# `public` directive on an authenticated response is how a shared cache ends
# up serving the admin's answer to the next anonymous request for the same URL
# — so a gated read is never cacheable anywhere. Used by hands.py; the
# eigenhand strips carry the same value under their own constant.
NO_STORE = "private, no-store"
