"""Shared HTTP cache policy for the public read endpoints."""

from fastapi import Response


# Template geometry only changes on an admin re-trace and the quiz bank only on a
# reseed, so the public read endpoints (write/*, quiz-words) cache hard: browsers
# hold 5 min, the CDN a day (`s-maxage`, once a cache rule allows JSON there), and
# both serve stale up to a week while revalidating without a blocking round trip.
PUBLIC_CACHE_CONTROL = "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"


def set_public_cache(response: Response) -> None:
    """Stamp the shared public-read cache policy onto a response."""
    response.headers["Cache-Control"] = PUBLIC_CACHE_CONTROL
