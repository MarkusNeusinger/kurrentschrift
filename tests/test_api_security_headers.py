"""The API host's own two response headers, and the CSP report endpoint.

`api/security_headers.py` is a floor: every response this service produces
carries `nosniff` and a `Referrer-Policy`, including the ones no router ever
sees — the origin gate's 403 and the rate limiter's 429 are JSON bodies handed
to a browser like any other.

`api/routers/csp.py` is the other half of the report-only week: it is the one
POST on this API that anybody may call, so the tests below pin what it accepts,
what it refuses, and that it still answers 204 with no credential at all.
"""

from __future__ import annotations

import logging

import pytest

from api.rate_limit import public_limiter, write_limiter
from api.routers import csp as csp_module
from api.security_headers import SECURITY_HEADERS
from tests.api_harness import Harness


EXPECTED = {name.decode(): value.decode() for name, value in SECURITY_HEADERS}

# One violation in each wire format, same underlying complaint.
REPORT_URI_BODY = {
    "csp-report": {
        "document-uri": "https://kurrentschrift.ink/quiz",
        "violated-directive": "img-src",
        "effective-directive": "img-src",
        "blocked-uri": "https://example.invalid/tracker.gif",
        "disposition": "report",
        "source-file": "https://kurrentschrift.ink/assets/index-abc.js",
        "line-number": 12,
    }
}
REPORT_TO_BODY = [
    {
        "type": "csp-violation",
        "url": "https://kurrentschrift.ink/quiz",
        "body": {
            "documentURL": "https://kurrentschrift.ink/quiz",
            "effectiveDirective": "img-src",
            "blockedURL": "https://example.invalid/tracker.gif",
            "disposition": "report",
            "sourceFile": "https://kurrentschrift.ink/assets/index-abc.js",
            "lineNumber": 12,
        },
    }
]


async def _post_raw(body: bytes, *, content_type: str, path: str = "/csp-report") -> dict:
    """POST arbitrary BYTES to the real app.

    `tests.api_harness.AsgiClient` always JSON-encodes its payload, so a body
    that is not JSON cannot be expressed there — and "what happens to a body
    that is not JSON" is exactly the question on a public POST. This route
    touches no database, so it needs none of the harness's wiring.
    """
    from api.main import app

    messages: list[dict] = []
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"testserver"),
            (b"content-type", content_type.encode()),
            (b"content-length", str(len(body)).encode()),
        ],
        "client": ("testclient", 50000),
        "server": ("testserver", 443),
    }
    sent = {"done": False}

    async def receive():
        if not sent["done"]:
            sent["done"] = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    return {"status": start["status"], "headers": dict(start.get("headers", []))}


@pytest.fixture(autouse=True)
def _fresh_state():
    """Each test starts with an empty violation memo and full token buckets.

    The memo is module state by design (one log line per distinct violation per
    process), so without this a test's reports would be counted as repeats of
    the previous test's.
    """
    csp_module._seen.clear()
    csp_module._overflow = 0
    public_limiter.reset()
    write_limiter.reset()
    yield
    csp_module._seen.clear()
    csp_module._overflow = 0


async def test_a_public_read_carries_both_headers(api: Harness):
    res = await api.client.request("GET", "/health")
    assert res.status == 200
    for name, value in EXPECTED.items():
        assert res.headers.get(name) == value


async def test_a_gated_read_carries_them_too(api: Harness):
    """The 401 is the response an attacker sees most often — it gets the floor."""
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("GET", f"/sources/{source_id}/templates/n/fit")
    assert res.status == 401
    for name, value in EXPECTED.items():
        assert res.headers.get(name) == value


async def test_a_404_carries_them_too(api: Harness):
    res = await api.client.request("GET", "/no-such-route")
    assert res.status == 404
    for name, value in EXPECTED.items():
        assert res.headers.get(name) == value


async def test_a_rate_limit_refusal_carries_them(api: Harness):
    """The limiter answers from OUTSIDE the router, so only middleware order
    puts the headers on its 429 — which is what this pins."""
    original = public_limiter.burst
    # Below one token but above zero: a burst of exactly 0 turns the bucket OFF
    # (`TokenBucketLimiter.enabled`) instead of making it refuse.
    public_limiter.burst = 0.5
    try:
        public_limiter.reset()
        res = await api.client.request("GET", "/styles")
        assert res.status == 429
        for name, value in EXPECTED.items():
            assert res.headers.get(name) == value
    finally:
        public_limiter.burst = original
        public_limiter.reset()


async def test_csp_report_is_accepted_without_any_credential(api: Harness, caplog):
    with caplog.at_level(logging.WARNING, logger="api.routers.csp"):
        res = await api.client.request("POST", "/csp-report", json_body=REPORT_URI_BODY)
    assert res.status == 204
    assert res.body == b""
    assert res.headers.get("cache-control") == "private, no-store"
    assert "img-src" in caplog.text
    assert "https://example.invalid/tracker.gif" in caplog.text


async def test_the_reporting_api_body_shape_is_understood_too(api: Harness, caplog):
    """Chromium posts an ARRAY of envelopes with camelCase fields."""
    with caplog.at_level(logging.WARNING, logger="api.routers.csp"):
        res = await api.client.request("POST", "/csp-report", json_body=REPORT_TO_BODY)
    assert res.status == 204
    assert "img-src" in caplog.text
    assert "https://example.invalid/tracker.gif" in caplog.text


async def test_a_repeated_violation_is_counted_but_not_logged_again(api: Harness, caplog):
    with caplog.at_level(logging.WARNING, logger="api.routers.csp"):
        for _ in range(5):
            await api.client.request("POST", "/csp-report", json_body=REPORT_URI_BODY)
    assert caplog.text.count("CSP report") == 1
    assert list(csp_module._seen.values()) == [5]


async def test_a_body_that_is_not_a_report_changes_nothing(api: Harness):
    """A bare object, an empty array, a string — accepted and ignored.

    Anything else would turn a stray POST into a 500 on a public path.
    """
    for body in ({"something": "else"}, [], [{"type": "deprecation", "body": {}}]):
        res = await api.client.request("POST", "/csp-report", json_body=body)
        assert res.status == 204
    assert csp_module._seen == {}


async def test_an_empty_body_is_accepted_and_records_nothing(api: Harness):
    res = await api.client.request("POST", "/csp-report", headers={"content-type": "application/csp-report"})
    assert res.status == 204
    assert csp_module._seen == {}


async def test_a_body_that_is_not_json_is_a_400(api: Harness):
    """Not reachable through the JSON harness — posted as raw bytes."""
    res = await _post_raw(b"<not json at all>", content_type="application/csp-report")
    assert res["status"] == 400
    assert csp_module._seen == {}


async def test_an_oversized_body_is_refused_before_it_is_parsed(api: Harness):
    """A public POST with no size ceiling is a memory tap."""
    huge = {"csp-report": {"script-sample": "x" * (csp_module.MAX_BODY_BYTES + 1)}}
    res = await api.client.request("POST", "/csp-report", json_body=huge)
    assert res.status == 413
    assert csp_module._seen == {}


async def test_the_violation_memo_cannot_grow_without_bound(api: Harness, caplog):
    """A policy with one wrong directive per page would otherwise grow a dict
    behind a public POST, one entry per distinct blocked URL.

    And past the cap the LOG must not become the new leak: a violation with no
    counter of its own would look "seen for the first time" on every single
    report. The overflow is counted and announced once.
    """
    original = public_limiter.per_minute
    # The bucket is not the subject here, and 210 requests in a millisecond is
    # not what it exists to allow.
    public_limiter.per_minute = 0
    overflow = 10
    try:
        with caplog.at_level(logging.WARNING, logger="api.routers.csp"):
            for i in range(csp_module._MAX_TRACKED + overflow):
                body = {"csp-report": {"effective-directive": "img-src", "blocked-uri": f"https://example.invalid/{i}"}}
                res = await api.client.request("POST", "/csp-report", json_body=body)
                assert res.status == 204
    finally:
        public_limiter.per_minute = original
        public_limiter.reset()
    assert len(csp_module._seen) == csp_module._MAX_TRACKED
    assert csp_module._overflow == overflow
    # One line per tracked violation, plus exactly one about the overflow.
    # `"CSP report ("` and not `"CSP report"` — the overflow line says
    # "CSP reports:" and would otherwise be counted as a violation of its own.
    assert caplog.text.count("CSP report (") == csp_module._MAX_TRACKED
    assert caplog.text.count("CSP reports: more than") == 1
