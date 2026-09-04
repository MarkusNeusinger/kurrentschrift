"""The two token buckets in front of the API (`api/rate_limit.py`).

A narrow one for the compose path `/write/word*` and a wide one over every
other route, GET and HEAD included. On the `run.app` URL — both Cloud Run
services stand with `ingress=all` — they are the only rate limit at all. What
they must do is behaviour over TIME, so every timing test drives an injected
clock instead of sleeping.
"""

from __future__ import annotations

import pytest

from api.rate_limit import TokenBucketLimiter, public_limiter, write_limiter
from tests.api_harness import Harness


class FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def test_burst_is_spent_then_refills_at_the_configured_rate():
    clock = FakeClock()
    limiter = TokenBucketLimiter(per_minute=60, burst=3, now=clock)

    assert [limiter.check("1.2.3.4") for _ in range(3)] == [None, None, None]
    # Fourth request in the same instant: one full token is 1 s away.
    assert limiter.check("1.2.3.4") == pytest.approx(1.0)

    clock.advance(1.0)
    assert limiter.check("1.2.3.4") is None
    assert limiter.check("1.2.3.4") == pytest.approx(1.0)

    # Idle long enough and the bucket is back to full — but never fuller.
    clock.advance(3600.0)
    assert [limiter.check("1.2.3.4") for _ in range(3)] == [None, None, None]
    assert limiter.check("1.2.3.4") is not None


def test_buckets_are_per_client():
    clock = FakeClock()
    limiter = TokenBucketLimiter(per_minute=60, burst=1, now=clock)

    assert limiter.check("1.2.3.4") is None
    assert limiter.check("1.2.3.4") is not None
    # A second caller is untouched by the first one's spending.
    assert limiter.check("5.6.7.8") is None


def test_retrying_in_a_tight_loop_refills_no_faster_than_waiting():
    """Refilling is a function of elapsed time, not of how often you ask: a
    rejection stores the timestamp it refilled TO, so the same seconds are
    never credited twice."""
    clock = FakeClock()
    limiter = TokenBucketLimiter(per_minute=60, burst=1, now=clock)
    assert limiter.check("1.2.3.4") is None

    waits = []
    for _ in range(15):  # 0.75 s of retries, still short of the 1 s refill
        clock.advance(0.05)
        wait = limiter.check("1.2.3.4")
        assert wait is not None
        waits.append(wait)
    # …and the promised wait shrinks monotonically towards zero meanwhile.
    assert waits == sorted(waits, reverse=True)
    assert waits[-1] == pytest.approx(0.25)

    clock.advance(0.30)  # 1.05 s total since the token was taken
    assert limiter.check("1.2.3.4") is None


def test_zero_rate_disables_the_limiter():
    limiter = TokenBucketLimiter(per_minute=0, burst=20)
    assert limiter.enabled is False
    assert all(limiter.check("1.2.3.4") is None for _ in range(1000))


def test_full_buckets_are_evicted_once_the_table_grows(monkeypatch):
    """A caller rotating source IPs must not grow the table without bound.
    A bucket that has refilled to full decides nothing, so it can be forgotten."""
    import api.rate_limit as rate_limit

    monkeypatch.setattr(rate_limit, "MAX_TRACKED_CLIENTS", 10)
    clock = FakeClock()
    limiter = TokenBucketLimiter(per_minute=60, burst=1, now=clock)

    for i in range(10):
        assert limiter.check(f"10.0.0.{i}") is None
    assert len(limiter._buckets) == 10

    clock.advance(60.0)  # everyone seen so far has refilled to full
    assert limiter.check("10.0.1.1") is None
    assert list(limiter._buckets) == ["10.0.1.1"]


# ---------------------------------------------------------------- over HTTP


# One WHOLE token of the narrow bucket: it meters by characters composed, and
# a full-length text is what one token buys. The tests below that count tokens
# ask for this text, so "one request, one token" still reads literally; the
# metering itself is exercised by the short-text tests further down.
FULL_LEN_TEXT = "n" * 160


async def _seed_word(api: Harness) -> str:
    from core.shaping import glyph_keys_of, shape_text

    style_id, source_id = await api.seed_style_and_source()
    for key in glyph_keys_of(shape_text("nn")):
        await api.seed_template(style_id, source_id, key, "n")
    return source_id


def _freeze(monkeypatch, *limiters_and_bursts: tuple[TokenBucketLimiter, float]) -> FakeClock:
    """Give the process-wide limiters a small burst AND a stopped clock.

    Shrinking the burst alone is not enough: the wide bucket refills at 10
    tokens per second (the narrow one at 1), so on a loaded runner enough real
    time can pass between two awaited requests to hand one back and the
    assertion flips (Copilot review, PR #490). With the clock frozen nothing
    refills unless a test advances it on purpose.
    """
    clock = FakeClock()
    for limiter, burst in limiters_and_bursts:
        monkeypatch.setattr(limiter, "_now", clock)
        monkeypatch.setattr(limiter, "burst", burst)
        limiter.reset()
    return clock


async def test_write_word_answers_429_with_retry_after(api: Harness, monkeypatch):
    source_id = await _seed_word(api)
    clock = FakeClock()
    monkeypatch.setattr(write_limiter, "_now", clock)
    monkeypatch.setattr(write_limiter, "burst", 2.0)
    write_limiter.reset()

    for _ in range(2):
        assert (
            await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": FULL_LEN_TEXT})
        ).status == 200

    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": FULL_LEN_TEXT})
    assert res.status == 429
    assert res.headers["retry-after"] == "1"
    # A rejection is about the caller, never the URL — it must not be cached
    # for the next visitor.
    assert res.headers["cache-control"] == "private, no-store"
    assert "per minute" in res.json()["detail"]

    # The SVG twin shares the bucket: same composition, same cost.
    res = await api.client.request("GET", f"/sources/{source_id}/write/word.svg", params={"text": FULL_LEN_TEXT})
    assert res.status == 429

    clock.advance(60.0)
    assert (
        await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": FULL_LEN_TEXT})
    ).status == 200


async def test_glyph_reads_are_exempt_from_the_word_limit(api: Harness, monkeypatch):
    """The inventory-bounded reads must keep answering while the compose path
    is throttled — the Tafel and the quiz ride on `/write/glyphs`."""
    source_id = await _seed_word(api)
    # A bucket that never holds a whole token: every word request is over.
    _freeze(monkeypatch, (write_limiter, 0.5))

    assert (
        await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": FULL_LEN_TEXT})
    ).status == 429
    assert (await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": "n"})).status == 200
    assert (await api.client.request("GET", f"/sources/{source_id}/write/glyphs/n")).status == 200
    assert (await api.client.request("GET", f"/sources/{source_id}/write/glyphs/n.svg")).status == 200


# ------------------------------------------------- the wide bucket, all routes


async def test_the_wide_bucket_covers_plain_reads(api: Harness, monkeypatch):
    """The author's decision of 2026-09-02: extreme use must be blocked everywhere, not
    only on the compose path. Before this, nothing stopped a script from
    walking the catalogue and the batch reads in a loop."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    _freeze(monkeypatch, (public_limiter, 2.0))

    assert (await api.client.request("GET", "/styles")).status == 200
    assert (await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": "n"})).status == 200

    res = await api.client.request("GET", "/quiz-words")
    assert res.status == 429
    assert res.headers["retry-after"] == "1"
    assert res.headers["cache-control"] == "private, no-store"
    assert "too many requests" in res.json()["detail"]

    # …and a write, and an unknown path: the limiter sits before routing, so a
    # flood of 404s costs nothing to produce either.
    assert (await api.client.request("PUT", f"/sources/{source_id}/bboxes/n", json_body={})).status == 429
    assert (await api.client.request("GET", "/no-such-route")).status == 429


async def test_head_spends_a_token_like_the_get_it_stands_for(api: Harness, monkeypatch):
    """`HeadAsGetMiddleware` answers HEAD from the GET route, so an unlimited
    HEAD would be a limit one header away from being evaded."""
    await api.seed_style_and_source()
    _freeze(monkeypatch, (public_limiter, 2.0))

    assert (await api.client.request("HEAD", "/styles")).status == 200
    assert (await api.client.request("HEAD", "/styles")).status == 200
    assert (await api.client.request("HEAD", "/styles")).status == 429
    assert (await api.client.request("GET", "/styles")).status == 429


async def test_health_and_the_prerendered_pages_stay_exempt(api: Harness, monkeypatch):
    """`/health` carries the deploy smoke and any uptime probe — throttling it
    to punish a busy client would turn a rate limit into an outage. The
    `/seo-proxy` pages all arrive through the site's nginx and therefore share
    ONE key, so a bucket would throttle the whole crawler funnel at once."""
    _freeze(monkeypatch, (public_limiter, 0.5))  # never holds a whole token

    assert (await api.client.request("GET", "/styles")).status == 429
    for _ in range(3):
        assert (await api.client.request("GET", "/health")).status == 200
        assert (await api.client.request("GET", "/seo-proxy/schriftkunde")).status in (200, 404)
    # The root and the machine files are NOT exempt — they are not the funnel.
    assert (await api.client.request("GET", "/robots.txt")).status == 429
    # …and the exemption is the prefix WITH its slash, so a neighbouring path
    # cannot slip through on a shared stem.
    from api.rate_limit import limiters_for

    assert limiters_for("/seo-proxy/schriftkunde") == ()
    assert limiters_for("/seo-proxy") == ()  # the redirect to /seo-proxy/
    assert limiters_for("/seo-proxy-admin") != ()


async def test_the_narrow_bucket_answers_before_the_wide_one(api: Harness, monkeypatch):
    """Two-stage, narrow first: a caller hammering `/write/word` is told about
    the limit it actually broke, and the refused request does not also spend a
    token of the wide budget."""
    source_id = await _seed_word(api)
    _freeze(monkeypatch, (write_limiter, 1.0), (public_limiter, 10.0))

    assert (
        await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": FULL_LEN_TEXT})
    ).status == 200
    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": FULL_LEN_TEXT})
    assert res.status == 429
    # The NARROW bucket's wording, not the wide one's.
    assert "word compositions" in res.json()["detail"]
    assert str(int(write_limiter.per_minute)) in res.json()["detail"]

    # Nine tokens of the wide budget are left — one spent by the allowed word
    # request, none by the refused one — so the rest of the site keeps working
    # while the compose path is throttled.
    for _ in range(9):
        assert (await api.client.request("GET", "/styles")).status == 200
    assert (await api.client.request("GET", "/styles")).status == 429


async def test_a_wrapped_text_costs_what_it_composes_not_what_it_requests(api: Harness, monkeypatch):
    """The narrow bucket meters CHARACTERS, so splitting one composition into
    several costs the same as sending it whole. The Federprobe's postcard
    depends on it: a 480-character text is written as up to ~57 lines, each its
    own compose request, and per-request metering spent more than the whole
    burst on ONE page view.

    The lines here are 40 characters — a quarter of a full-length request and
    well clear of the eighth-token floor, so what this measures is the
    PROPORTIONALITY and not the floor (which the next test covers)."""
    source_id = await _seed_word(api)
    quarter = "n" * (len(FULL_LEN_TEXT) // 4)

    async def word(text: str) -> int:
        res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": text})
        return res.status

    # One token buys 160 characters, whether they arrive in one request…
    _freeze(monkeypatch, (write_limiter, 1.0))
    assert await word(FULL_LEN_TEXT) == 200
    assert await word(FULL_LEN_TEXT) == 429

    # …or in four of forty. The fourth quarter still fits, the fifth is over:
    # the same 160 characters, the same one token, four times the requests.
    _freeze(monkeypatch, (write_limiter, 1.0))
    for _ in range(4):
        assert await word(quarter) == 200
    assert await word(quarter) == 429


async def test_a_short_text_is_never_cheaper_than_an_eighth_of_a_token(api: Harness, monkeypatch):
    """The floor under `composition_cost`: metering by length must not turn
    one-character requests into a free lane through the narrow bucket."""
    source_id = await _seed_word(api)
    _freeze(monkeypatch, (write_limiter, 1.0))

    for _ in range(8):
        assert (await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "n"})).status == 200
    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "n"})
    assert res.status == 429
    # And the 429 says what a unit is, so a caller of short texts can read it.
    assert "up to 160 characters" in res.json()["detail"]


def test_the_cost_unit_is_the_routes_own_text_limit():
    """`WRITE_COST_UNIT_CHARS` is `MAX_TEXT_LEN` written out — the middleware
    runs before routing and must not import the router, so the two numbers are
    held equal here instead (same reason `WORD_PATHS` is pinned above)."""
    from api.rate_limit import WRITE_COST_UNIT_CHARS
    from api.routers.write import MAX_TEXT_LEN

    assert WRITE_COST_UNIT_CHARS == MAX_TEXT_LEN


def test_a_bucket_without_a_cost_function_charges_one_token():
    """The wide bucket counts REQUESTS: that is its unit, and metering it by
    text length would leave every route without a `text` param uncounted."""
    from starlette.requests import Request

    request = Request({"type": "http", "method": "GET", "path": "/styles", "query_string": b"", "headers": []})
    assert public_limiter.cost_of(request) == 1.0
    assert write_limiter.cost_of(request) == pytest.approx(0.125)


async def test_the_word_path_pattern_matches_the_real_routes():
    """The middleware runs BEFORE routing, so it matches the compose paths by
    pattern. Held against the router table here so the narrow bucket cannot
    silently stop applying if a route is renamed."""
    from fastapi.routing import APIRoute

    from api.main import app
    from api.rate_limit import WORD_PATHS, limiters_for

    word_routes = set()
    for route in app.routes:
        inner = getattr(route, "original_router", None)
        candidates = (
            [(route, "")]
            if inner is None
            else [(r, getattr(getattr(route, "include_context", None), "prefix", "") or "") for r in inner.routes]
        )
        for r, prefix in candidates:
            if isinstance(r, APIRoute) and (prefix + r.path).endswith(("/write/word", "/write/word.svg")):
                word_routes.add(prefix + r.path)

    assert word_routes == {"/sources/{source_id}/write/word", "/sources/{source_id}/write/word.svg"}
    for path in word_routes:
        filled = path.format(source_id="suetterlin-1922")
        assert WORD_PATHS.match(filled), filled
        assert limiters_for(filled) == (write_limiter, public_limiter)

    # …and nothing else is caught by it.
    for other in ("/sources/x/write/glyphs", "/sources/x/write/glyphs/n", "/sources/x/write/word/extra", "/styles"):
        assert not WORD_PATHS.match(other), other
        assert limiters_for(other) == (public_limiter,)


async def test_a_200_is_not_touched_by_the_limiter(api: Harness):
    """The edge keeps caching the public reads exactly as before: the limiter
    counts at the origin and adds nothing to a response it lets through."""
    await api.seed_style_and_source()
    res = await api.client.request("GET", "/styles")
    assert res.status == 200
    assert res.headers["cache-control"] == "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"
    assert "retry-after" not in res.headers


async def test_the_bucket_keys_on_the_rightmost_forwarded_entry(api: Harness, monkeypatch):
    """The leftmost `x-forwarded-for` entry is client-controlled: trusting it
    would let a caller both evade its own limit and lock someone else out."""
    source_id = await _seed_word(api)
    _freeze(monkeypatch, (write_limiter, 1.0))

    async def word(headers: dict[str, str]) -> int:
        res = await api.client.request(
            "GET", f"/sources/{source_id}/write/word", params={"text": FULL_LEN_TEXT}, headers=headers
        )
        return res.status

    assert await word({"x-forwarded-for": "9.9.9.9, 203.0.113.7"}) == 200
    # Same trusted hop, a different forged leftmost entry: still the same bucket.
    assert await word({"x-forwarded-for": "1.1.1.1, 203.0.113.7"}) == 429
    # A genuinely different last hop is a different bucket.
    assert await word({"x-forwarded-for": "9.9.9.9, 198.51.100.4"}) == 200
    # Garbage a proxy inserted is skipped rather than becoming a shared bucket
    # everyone lands in — `203.0.113.7` is still the last REAL address.
    assert await word({"x-forwarded-for": "9.9.9.9, 203.0.113.7, unknown"}) == 429


async def test_a_forged_cf_connecting_ip_cannot_reach_a_victims_bucket(api: Harness, monkeypatch):
    """Both Cloud Run services stand with `ingress=all`, so a caller on the
    `run.app` URL writes `cf-connecting-ip` itself. Keying on it alone would
    let that caller burn a victim's bucket; joined with the unforgeable last
    hop it can only scatter its own requests (Copilot review, PR #481)."""
    source_id = await _seed_word(api)
    _freeze(monkeypatch, (write_limiter, 1.0))

    async def word(headers: dict[str, str]) -> int:
        res = await api.client.request(
            "GET", f"/sources/{source_id}/write/word", params={"text": FULL_LEN_TEXT}, headers=headers
        )
        return res.status

    # The attacker reaches the origin directly and claims the victim's address.
    attacker = {"x-forwarded-for": "198.51.100.66", "cf-connecting-ip": "203.0.113.9"}
    assert await word(attacker) == 200
    assert await word(attacker) == 429  # its own bucket is spent

    # The victim arrives through Cloudflare — different last hop, so a bucket
    # of its own, untouched.
    victim = {"x-forwarded-for": "203.0.113.9, 172.71.0.1", "cf-connecting-ip": "203.0.113.9"}
    assert await word(victim) == 200

    # …and behind one Cloudflare edge two visitors still get one bucket each,
    # which is what `cf-connecting-ip` is in the key for.
    neighbour = {"x-forwarded-for": "203.0.113.10, 172.71.0.1", "cf-connecting-ip": "203.0.113.10"}
    assert await word(neighbour) == 200
    assert await word(victim) == 429
