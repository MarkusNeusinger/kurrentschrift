"""Two token buckets in front of the API — a narrow one and a wide one.

Both are keyed per client by `api.request_context.rate_limit_key`, which joins
the unforgeable last hop with `cf-connecting-ip` — see there for why neither
header alone is safe on both of this service's reachable paths. Both are
checked by ONE middleware (`RateLimitMiddleware`), narrow first, so a request
that the narrow bucket refuses never spends a wide token.

**Narrow — `/write/word` and `/write/word.svg`** (60/min, burst 20). This is
the one public read whose cost the CALLER sets: it shapes, composes and
serialises a whole line server-side, a unique text is a guaranteed edge-cache
MISS, and the audit of 2026-09-01 measured 0.80 s TTFB and 1,653,798 bytes for
one unique 155-character request. With `--concurrency=15 --max-instances=3` a
scripted caller with random texts saturates an instance, scales the service and
pays out ~1.6 MB of egress per request.

**Wide — every other route, GET and HEAD included** (600/min, burst 120,
owner decision 2026-09-02: "soll nur extreme Nutzung blocken, damit mir keine
riesigen Kosten entstehen können oder jemand alles lahmlegen kann"). The narrow
bucket left the rest of the surface open: `/write/glyphs` batches up to 80
keys, `/diagnostic`-shaped reads and every catalogue read hit the DB, and
nothing stopped a script from walking the whole API in a loop. The wide budget
sits an order of magnitude above what a person browsing the site produces — a
Tafel page load is a handful of batched requests, a quiz round one — and well
under what a harvest needs.

Deliberately NOT metering exactly:

* It counts at the ORIGIN, so cached responses never reach it. Cloudflare keeps
  serving the public reads from the edge exactly as before, and only cache
  MISSES spend a token. Nothing about a 200 changes — no header, no `Vary`, no
  cache class.
* It is per PROCESS. With `--max-instances=3` the effective ceiling is up to
  three times the configured rate. The point is to bound what one caller can
  extract from one container, not to be a meter.
* On the `run.app` URL it is the only net at all: both Cloud Run services stand
  with `ingress=all`, so every Cloudflare measure is one URL away from being
  bypassed while this one is not.

Exempt from both buckets, by path:

* `/health` — the deploy smoke and any uptime probe. Throttling the health
  check to punish a busy client would turn a rate limit into an outage.
* `/seo-proxy/…` — the prerendered crawler pages. Every one of them arrives
  through the site's nginx (Cloud Run app → Cloudflare → this API), so they ALL
  share one key, and a bucket would throttle the entire crawler funnel plus the
  daily bot-serving guard as if it were a single abusive client. They are also
  the cheapest route there is: one committed 8 KB file read, no DB.

Defaults live in `core/config.py` (`WRITE_RATE_LIMIT_PER_MIN`/`_BURST`,
`PUBLIC_RATE_LIMIT_PER_MIN`/`_BURST`); setting either rate to 0 turns that
bucket off.
"""

from __future__ import annotations

import math
import re
import threading
import time
from collections.abc import Callable

from fastapi import Request
from fastapi.responses import JSONResponse

from api.http import NO_STORE
from api.request_context import rate_limit_key
from core.config import settings


# Above this many tracked buckets a request first evicts everything that has
# refilled to full (i.e. every caller idle for at least burst/rate seconds).
# A caller rotating source IPs would otherwise grow the dict without bound;
# 20k float pairs is a couple of MB against the 512Mi instance.
MAX_TRACKED_CLIENTS = 20_000

# The two compose routes of `api/routers/write.py`. Matched on the raw path
# because the middleware runs BEFORE routing — `tests/test_api_rate_limit.py`
# holds this pattern against the real route table so it cannot drift away from
# the router silently.
WORD_PATHS = re.compile(r"^/sources/[^/]+/write/word(\.svg)?$")

# Neither bucket applies here — see the module docstring for why each is out.
# The bare `/seo-proxy` is listed beside the prefix because it is the
# redirect to `/seo-proxy/`; the prefix keeps its trailing slash so it cannot
# also swallow some future `/seo-proxy-admin`.
EXEMPT_PATHS = frozenset({"/health", "/seo-proxy"})
EXEMPT_PREFIXES = ("/seo-proxy/",)


class TokenBucketLimiter:
    """Per-key token bucket: `burst` tokens, refilled at `per_minute`/60 per second.

    `now` is injectable so the tests can drive a fake clock instead of sleeping
    — the whole point of a rate limiter is behaviour over time, and a suite
    that sleeps for it is a suite nobody runs.
    """

    def __init__(
        self, per_minute: float, burst: float, *, name: str = "requests", now: Callable[[], float] = time.monotonic
    ) -> None:
        self.per_minute = float(per_minute)
        self.burst = float(burst)
        # What the 429 calls the thing being counted ("word compositions",
        # "requests") — the tool on the other end prints the detail.
        self.name = name
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

    def too_many(self, wait: float) -> JSONResponse:
        """The 429 this bucket answers with.

        `Retry-After` is the honest wait rounded UP to whole seconds, as the
        header requires — never a rounded-down zero that invites an instant
        retry. `no-store` because a rejection is about the caller, never about
        the URL, and must not be served to the next visitor from any cache.
        """
        detail = (
            f"too many {self.name} — the limit is {int(self.per_minute)} per minute "
            f"per client (burst {int(self.burst)})"
        )
        return JSONResponse(
            {"detail": detail},
            status_code=429,
            headers={"Retry-After": str(max(1, math.ceil(wait))), "Cache-Control": NO_STORE},
        )


write_limiter = TokenBucketLimiter(
    settings.write_rate_limit_per_min, settings.write_rate_limit_burst, name="word compositions"
)
public_limiter = TokenBucketLimiter(
    settings.public_rate_limit_per_min, settings.public_rate_limit_burst, name="requests"
)


def limiters_for(path: str) -> tuple[TokenBucketLimiter, ...]:
    """The buckets a path has to pass, NARROW FIRST.

    Narrow before wide so a caller hammering `/write/word` is told about the
    limit it actually broke, and so a request the narrow bucket refuses does
    not also spend a token of the wide one.
    """
    if path in EXEMPT_PATHS or path.startswith(EXEMPT_PREFIXES):
        return ()
    if WORD_PATHS.match(path):
        return (write_limiter, public_limiter)
    return (public_limiter,)


class RateLimitMiddleware:
    """Apply the buckets to every request, whatever its method.

    An ASGI middleware rather than a route dependency, for three reasons: a
    dependency reaches only the routes it is written on (the point here is that
    ALL of them are covered), it runs after routing so a flood of 404s would
    cost nothing to produce, and it cannot see HEAD — which must spend a token
    exactly like the GET it stands for, or the limit is one header away from
    being evaded.

    Placement (`api/main.py`): inside CORS, so a 429 still carries the CORS
    headers a browser needs in order to READ it as a 429 rather than as an
    opaque network error; outside `HeadAsGetMiddleware`, so HEAD is still
    visible as HEAD here and is counted before it is rewritten.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        buckets = limiters_for(scope["path"])
        if buckets:
            key = rate_limit_key(Request(scope))
            for bucket in buckets:
                wait = bucket.check(key)
                if wait is not None:
                    await bucket.too_many(wait)(scope, receive, send)
                    return
        await self.app(scope, receive, send)
