"""The `/write/word*` token bucket (`api/rate_limit.py`).

The bucket is the only rate limit in front of the compose path, and on the
`run.app` URL — both Cloud Run services stand with `ingress=all` — it is the
only one at all. What it must do is behaviour over TIME, so every timing test
drives an injected clock instead of sleeping.
"""

from __future__ import annotations

import pytest

from api.rate_limit import TokenBucketLimiter, write_limiter
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


async def _seed_word(api: Harness) -> str:
    from core.shaping import glyph_keys_of, shape_text

    style_id, source_id = await api.seed_style_and_source()
    for key in glyph_keys_of(shape_text("nn")):
        await api.seed_template(style_id, source_id, key, "n")
    return source_id


async def test_write_word_answers_429_with_retry_after(api: Harness, monkeypatch):
    source_id = await _seed_word(api)
    clock = FakeClock()
    monkeypatch.setattr(write_limiter, "_now", clock)
    monkeypatch.setattr(write_limiter, "burst", 2.0)
    write_limiter.reset()

    for _ in range(2):
        assert (
            await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "nn"})
        ).status == 200

    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "nn"})
    assert res.status == 429
    assert res.headers["retry-after"] == "1"
    # A rejection is about the caller, never the URL — it must not be cached
    # for the next visitor.
    assert res.headers["cache-control"] == "private, no-store"
    assert "per minute" in res.json()["detail"]

    # The SVG twin shares the bucket: same composition, same cost.
    res = await api.client.request("GET", f"/sources/{source_id}/write/word.svg", params={"text": "nn"})
    assert res.status == 429

    clock.advance(60.0)
    assert (await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "nn"})).status == 200


async def test_glyph_reads_are_exempt_from_the_word_limit(api: Harness, monkeypatch):
    """The inventory-bounded reads must keep answering while the compose path
    is throttled — the Tafel and the quiz ride on `/write/glyphs`."""
    source_id = await _seed_word(api)
    # A bucket that never holds a whole token: every word request is over.
    monkeypatch.setattr(write_limiter, "burst", 0.5)
    write_limiter.reset()

    assert (await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "nn"})).status == 429
    assert (await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": "n"})).status == 200
    assert (await api.client.request("GET", f"/sources/{source_id}/write/glyphs/n")).status == 200
    assert (await api.client.request("GET", f"/sources/{source_id}/write/glyphs/n.svg")).status == 200


async def test_the_bucket_keys_on_the_rightmost_forwarded_entry(api: Harness, monkeypatch):
    """The leftmost `x-forwarded-for` entry is client-controlled: trusting it
    would let a caller both evade its own limit and lock someone else out."""
    source_id = await _seed_word(api)
    monkeypatch.setattr(write_limiter, "burst", 1.0)
    write_limiter.reset()

    spend = {"x-forwarded-for": "9.9.9.9, 203.0.113.7"}
    assert (
        await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "nn"}, headers=spend)
    ).status == 200
    # Same trusted hop, a different forged leftmost entry: still the same bucket.
    forged = {"x-forwarded-for": "1.1.1.1, 203.0.113.7"}
    assert (
        await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "nn"}, headers=forged)
    ).status == 429
    # A genuinely different last hop is a different bucket.
    other = {"x-forwarded-for": "9.9.9.9, 198.51.100.4"}
    assert (
        await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "nn"}, headers=other)
    ).status == 200
