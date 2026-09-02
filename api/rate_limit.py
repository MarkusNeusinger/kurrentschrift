"""In-process token bucket for the compose path (`/write/word*`).

Keyed per client by `api.request_context.rate_limit_key`, which joins the
unforgeable last hop with `cf-connecting-ip` — see there for why neither header
alone is safe on both of this service's reachable paths.

Why this route and no other: `/write/word` shapes, composes and serialises a
whole line server-side. A unique text is a guaranteed edge-cache MISS, and the
audit of 2026-09-01 measured 0.80 s TTFB and 1,653,798 bytes for one unique
155-character request. With `--concurrency=15 --max-instances=3` a scripted
caller with random texts saturates an instance, scales the service and pays out
~1.6 MB of egress per request. The batch read `/write/glyphs` and the single
glyph reads are bounded by the authored inventory (~30 rows, all warm in the
payload memo) and stay exempt.

This is a NET UNDER the net, and on the `run.app` URL it is the only net: both
Cloud Run services stand with `ingress=all`, so every Cloudflare measure is one
URL away from being bypassed while this one is not. It is per PROCESS, so with
`--max-instances=3` the effective ceiling is up to three times the configured
rate — the point is to bound what one caller can extract from one container,
not to meter exactly.

Defaults live in `core/config.py` (`WRITE_RATE_LIMIT_PER_MIN`,
`WRITE_RATE_LIMIT_BURST`); setting the rate to 0 turns the limiter off, which
is what the test suite's own composition tests rely on being able to do.
"""

from __future__ import annotations

import math
import threading
import time
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from api.http import NO_STORE
from api.request_context import rate_limit_key
from core.config import settings


# Above this many tracked buckets a request first evicts everything that has
# refilled to full (i.e. every caller idle for at least burst/rate seconds).
# A caller rotating source IPs would otherwise grow the dict without bound;
# 20k float pairs is a couple of MB against the 512Mi instance.
MAX_TRACKED_CLIENTS = 20_000


class TokenBucketLimiter:
    """Per-key token bucket: `burst` tokens, refilled at `per_minute`/60 per second.

    `now` is injectable so the tests can drive a fake clock instead of sleeping
    — the whole point of a rate limiter is behaviour over time, and a suite
    that sleeps for it is a suite nobody runs.
    """

    def __init__(self, per_minute: float, burst: float, *, now: Callable[[], float] = time.monotonic) -> None:
        self.per_minute = float(per_minute)
        self.burst = float(burst)
        self._now = now
        self._lock = threading.Lock()
        # key -> (tokens left, timestamp those tokens were counted at)
        self._buckets: dict[str, tuple[float, float]] = {}

    @property
    def rate_per_second(self) -> float:
        return self.per_minute / 60.0

    @property
    def enabled(self) -> bool:
        return self.per_minute > 0 and self.burst > 0

    def check(self, key: str) -> float | None:
        """Take one token for `key`. `None` when allowed, else the seconds to wait.

        The returned wait is what `Retry-After` promises: how long until the
        bucket holds one token again, never a rounded-down zero.
        """
        if not self.enabled:
            return None
        now = self._now()
        with self._lock:
            tokens, seen = self._buckets.get(key, (self.burst, now))
            # Refill first, and store the timestamp the refill was counted TO —
            # keeping the old `seen` beside the new token count would credit the
            # same elapsed seconds again on the next call, and a caller
            # retrying in a tight loop would refill faster than one waiting.
            tokens = min(self.burst, tokens + (now - seen) * self.rate_per_second)
            if tokens < 1.0:
                self._buckets[key] = (tokens, now)
                return (1.0 - tokens) / self.rate_per_second
            self._buckets[key] = (tokens - 1.0, now)
            if len(self._buckets) > MAX_TRACKED_CLIENTS:
                self._evict_full(now)
            return None

    def _evict_full(self, now: float) -> None:
        """Drop every bucket that has refilled to capacity — caller holds the lock.

        A full bucket is indistinguishable from a caller that was never seen,
        so forgetting it changes no decision.
        """
        idle_for = self.burst / self.rate_per_second
        self._buckets = {k: v for k, v in self._buckets.items() if now - v[1] < idle_for}

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


write_limiter = TokenBucketLimiter(settings.write_rate_limit_per_min, settings.write_rate_limit_burst)


async def limit_word_composition(request: Request) -> None:
    """FastAPI dependency for `/write/word` and `/write/word.svg`.

    A 429 carries `Retry-After` (the honest wait, rounded up to whole seconds
    as the header requires) and `no-store`: a rejection is about the caller,
    never about the URL, and must not be cached for the next visitor.
    """
    wait = write_limiter.check(rate_limit_key(request))
    if wait is None:
        return
    raise HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        detail=(
            f"too many word compositions — the limit is {int(write_limiter.per_minute)} per minute "
            f"per client (burst {int(write_limiter.burst)})"
        ),
        headers={"Retry-After": str(max(1, math.ceil(wait))), "Cache-Control": NO_STORE},
    )
