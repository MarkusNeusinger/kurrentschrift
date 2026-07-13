"""Shared HTTP constants for the routers."""

# Public, rarely-changing render/word-bank payloads: cache hard at browser + edge.
# Template geometry only changes on an admin re-trace and the quiz bank on a
# reseed, so five minutes of browser staleness is fine while `s-maxage` targets
# the CDN and stale-while-revalidate bridges revalidation without a blocking
# round trip. Used by write.py and quiz_words.py.
CACHE_CONTROL = "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"
