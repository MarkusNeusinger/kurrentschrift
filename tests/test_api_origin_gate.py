"""The shared-secret origin gate (`api/origin_gate.py`).

Both Cloud Run services stand with `ingress=all`, so the raw `*.run.app`
address answers without ever touching Cloudflare — and every edge measure (the
rate-limiting rule, the WAF, the cache) is one URL away from being bypassed. A
Cloudflare Transform Rule stamps `X-Origin-Secret` onto everything it proxies
for `api.kurrentschrift.ink`; this suite pins that the API requires it, that it
is DORMANT until the secret is configured (which is the rollback), and that the
two paths which must never be locked out are not.
"""

from __future__ import annotations

import pytest

from api.origin_gate import ORIGIN_SECRET_HEADER
from core.config import settings
from tests.api_harness import Harness


SECRET = "s3cret-from-the-edge"


@pytest.fixture
def armed(monkeypatch):
    """Turn the gate on for one test, the way Cloud Run's env does."""
    monkeypatch.setattr(settings, "origin_secret", SECRET)


def _edge() -> dict[str, str]:
    return {ORIGIN_SECRET_HEADER: SECRET}


async def test_the_gate_is_off_until_a_secret_is_configured(api: Harness):
    """The default everywhere: local dev, the test suite, and production until
    step (c) of the rollout. Unsetting the variable is the rollback, and it
    must need no deploy — so `origin_secret` is read per request."""
    assert settings.origin_secret is None
    await api.seed_style_and_source()

    assert (await api.client.request("GET", "/styles")).status == 200
    # …even with a wrong header, which is what the window between the Transform
    # Rule going live and the secret being set looks like.
    assert (await api.client.request("GET", "/styles", headers={ORIGIN_SECRET_HEADER: "anything"})).status == 200
    assert (await api.client.request("GET", "/health")).json()["origin_gate"] == "off"
    # …and the unarmed gate still SAYS whether a header arrived. That is what
    # step (b) of the rollout is measured with: the rule goes live first, and
    # every path that must keep working has to answer `off-seen` before the
    # switch is thrown. A bare `off` would have made arming a leap — above all
    # for the admin route, where the apex `/api/*` reaches this service through
    # a Cloudflare Worker whose subrequest may or may not carry the stamp.
    res = await api.client.request("GET", "/health", headers={ORIGIN_SECRET_HEADER: "anything"})
    assert res.json()["origin_gate"] == "off-seen"


async def test_the_right_header_passes_and_a_wrong_one_does_not(api: Harness, armed):
    await api.seed_style_and_source()

    assert (await api.client.request("GET", "/styles", headers=_edge())).status == 200

    for headers in (
        {},
        {ORIGIN_SECRET_HEADER: ""},
        {ORIGIN_SECRET_HEADER: "wrong"},
        {ORIGIN_SECRET_HEADER: SECRET[:-1]},
    ):
        res = await api.client.request("GET", "/styles", headers=headers)
        assert res.status == 403, headers
        assert res.headers["cache-control"] == "private, no-store"
        # The refusal names the front door and nothing else — never the secret,
        # never its length, never whether the caller was close.
        detail = res.json()["detail"]
        assert "api.kurrentschrift.ink" in detail
        assert SECRET not in detail


async def test_the_gate_covers_every_method_and_the_admin_paths(api: Harness, armed):
    """A gate that only saw GET would be one verb away from useless — and the
    reserved dataset's write paths are exactly what a direct caller wants."""
    _, source_id = await api.seed_style_and_source()

    assert (await api.client.request("PUT", f"/sources/{source_id}/bboxes/n", json_body={})).status == 403
    assert (await api.client.request("HEAD", "/styles")).status == 403
    assert (await api.client.request("GET", "/no-such-route")).status == 403
    # With the admin credential too: the gate asks which door you came in at,
    # not who you are, and it answers first.
    assert (await api.client.request("GET", "/hands", headers=api.admin_headers())).status == 403
    # …and with both, the request reaches the gate behind it — break-glass over
    # the direct URL needs BOTH headers now (documented in frontend-stack.md).
    assert (await api.client.request("GET", "/hands", headers=api.admin_headers() | _edge())).status == 200


async def test_health_and_the_prerendered_pages_are_never_gated(api: Harness, armed):
    """`/health` is how the deploy smoke reaches the candidate revision on its
    `run.app` tag URL — which by definition never passes the edge, so gating it
    would make every deploy fail closed. `/seo-proxy` is belt and braces: the
    site's nginx DOES come through the edge, but the cost of being wrong there
    is every crawler seeing a 403."""
    assert (await api.client.request("GET", "/styles")).status == 403

    assert (await api.client.request("GET", "/health")).status == 200
    assert (await api.client.request("GET", "/seo-proxy/schriftkunde")).status in (200, 404)
    assert (await api.client.request("GET", "/seo-proxy/")).status in (200, 404)

    from api.origin_gate import is_exempt

    assert is_exempt("/seo-proxy", "GET")  # the redirect to /seo-proxy/
    assert not is_exempt("/seo-proxy-admin", "GET")
    assert not is_exempt("/healthz", "GET")


async def test_a_preflight_is_never_refused(api: Harness, armed):
    """A browser cannot attach a custom header to a CORS preflight. A gate that
    refused one would break every cross-origin call on the site instead of
    protecting anything — and the 403 itself must stay readable, which is why
    the middleware sits inside CORSMiddleware."""
    from api.origin_gate import is_exempt

    assert is_exempt("/styles", "OPTIONS")

    preflight = await api.client.request(
        "OPTIONS",
        "/styles",
        headers={
            "Origin": "https://kurrentschrift.ink",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-admin-token",
        },
    )
    assert preflight.status == 200
    assert preflight.headers["access-control-allow-origin"] == "https://kurrentschrift.ink"

    # And a refused REAL request still carries the CORS headers, so the browser
    # reports a 403 rather than an opaque network error.
    refused = await api.client.request("GET", "/styles", headers={"Origin": "https://kurrentschrift.ink"})
    assert refused.status == 403
    assert refused.headers["access-control-allow-origin"] == "https://kurrentschrift.ink"


async def test_health_reports_the_verdict_for_the_request_it_was_asked_with(api: Harness, armed):
    """What makes the rollout measurable: every route into the service can be
    asked whether the header arrives, BEFORE the gate is armed."""

    async def verdict(headers: dict[str, str] | None = None) -> str:
        res = await api.client.request("GET", "/health", headers=headers)
        assert res.status == 200
        return res.json()["origin_gate"]

    assert await verdict(_edge()) == "ok"
    assert await verdict() == "missing"
    assert await verdict({ORIGIN_SECRET_HEADER: "wrong"}) == "mismatch"


async def test_a_trailing_newline_in_the_secret_cannot_lock_everyone_out(monkeypatch, api: Harness):
    """The ADMIN_TOKEN incident of 2026-08, one secret later: a value created
    with `echo` carries a newline, Cloud Run injects the bytes verbatim, and an
    HTTP header physically cannot transport one — so every request would 403
    and no value of the header could ever fix it. The setting strips."""
    from core.config import Settings

    monkeypatch.setenv("ORIGIN_SECRET", f"{SECRET}\n")
    assert Settings().origin_secret == SECRET

    monkeypatch.setattr(settings, "origin_secret", Settings(origin_secret=f"  {SECRET}  ").origin_secret)
    await api.seed_style_and_source()
    assert (await api.client.request("GET", "/styles", headers=_edge())).status == 200
