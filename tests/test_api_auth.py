"""The Cloudflare Access branch of `api.auth.require_admin` — the path that
actually gates prod.

`test_api_http.py` covers the X-Admin-Token fallback (401/503); this suite
covers the JWT side by monkeypatching `_verify_cf_access_jwt` (HTTP level)
and the JWKS/decode plumbing (unit level). DELETE /bboxes/{key} is the probe
endpoint: past auth it returns 404 (no bbox is seeded), so status encodes
only the gate — 401/403 = blocked, 404 = the handler ran.
"""

from __future__ import annotations

import jwt as pyjwt
import pytest

import api.auth as api_auth
from core.config import settings
from tests.api_harness import ADMIN_TOKEN, Harness


ALLOWED = "admin@example.com"


async def _probe(api: Harness, source_id: str, headers: dict[str, str]) -> tuple[int, dict]:
    res = await api.client.request("DELETE", f"/sources/{source_id}/bboxes/a-medial", headers=headers)
    return res.status, (res.json() if res.body else {})


@pytest.fixture
def cf(monkeypatch):
    """Allow-list one email; patch the JWT verifier per test via the returned hook."""
    monkeypatch.setattr(settings, "admin_allowed_emails_raw", ALLOWED)

    def set_verifier(result):
        monkeypatch.setattr(api_auth, "_verify_cf_access_jwt", lambda token: result)

    return set_verifier


async def test_valid_jwt_listed_email_authorizes(api: Harness, cf):
    _, source_id = await api.seed_style_and_source()
    cf(ALLOWED)
    status, _ = await _probe(api, source_id, {"Cf-Access-Jwt-Assertion": "jwt"})
    assert status == 404  # past the gate: the handler ran (no bbox seeded)


async def test_valid_jwt_unlisted_email_403_names_email(api: Harness, cf):
    _, source_id = await api.seed_style_and_source()
    cf("stranger@example.com")
    status, body = await _probe(api, source_id, {"Cf-Access-Jwt-Assertion": "jwt"})
    assert status == 403
    assert "stranger@example.com" in body["detail"]


async def test_unlisted_email_does_not_fall_through_to_token(api: Harness, cf):
    """A REAL identity that isn't allow-listed is a hard 403 — the break-glass
    token fallback exists only for an unverifiable JWT."""
    _, source_id = await api.seed_style_and_source()
    cf("stranger@example.com")
    status, _ = await _probe(api, source_id, {"Cf-Access-Jwt-Assertion": "jwt", "X-Admin-Token": ADMIN_TOKEN})
    assert status == 403


async def test_invalid_jwt_falls_through_to_token_path(api: Harness, cf):
    """A garbage/unverifiable JWT (verifier → None) must not 500 or hard-fail:
    it falls through so the operator keeps break-glass access via the token."""
    _, source_id = await api.seed_style_and_source()
    cf(None)
    status, _ = await _probe(api, source_id, {"Cf-Access-Jwt-Assertion": "garbage", "X-Admin-Token": ADMIN_TOKEN})
    assert status == 404  # past the gate: the handler ran (no bbox seeded)


async def test_invalid_jwt_without_token_401(api: Harness, cf):
    _, source_id = await api.seed_style_and_source()
    cf(None)
    status, _ = await _probe(api, source_id, {"Cf-Access-Jwt-Assertion": "garbage"})
    assert status == 401


# ------------------------------------------------ _verify_cf_access_jwt unit


class _StubSigningKey:
    key = "stub-key"


class _StubJwksClient:
    def __init__(self, error: Exception | None = None):
        self.error = error

    def get_signing_key_from_jwt(self, token):
        if self.error is not None:
            raise self.error
        return _StubSigningKey()


@pytest.fixture
def cf_config(monkeypatch):
    monkeypatch.setattr(settings, "cf_access_team_domain", "team.example.com")
    monkeypatch.setattr(settings, "cf_access_aud", "test-aud")


def test_verify_returns_lowercased_email(monkeypatch, cf_config):
    monkeypatch.setattr(api_auth, "_jwks_client", lambda: _StubJwksClient())
    monkeypatch.setattr(api_auth.pyjwt, "decode", lambda *a, **kw: {"email": "Admin@Example.COM"})
    assert api_auth._verify_cf_access_jwt("token") == "admin@example.com"


def test_verify_returns_none_on_jwt_error(monkeypatch, cf_config):
    monkeypatch.setattr(api_auth, "_jwks_client", lambda: _StubJwksClient(error=pyjwt.PyJWTError("bad")))
    assert api_auth._verify_cf_access_jwt("token") is None


def test_verify_returns_none_without_email_claim(monkeypatch, cf_config):
    monkeypatch.setattr(api_auth, "_jwks_client", lambda: _StubJwksClient())
    monkeypatch.setattr(api_auth.pyjwt, "decode", lambda *a, **kw: {"sub": "no-email"})
    assert api_auth._verify_cf_access_jwt("token") is None


def test_verify_returns_none_when_unconfigured(monkeypatch):
    """No team domain / audience configured → the JWT path is simply off."""
    monkeypatch.setattr(settings, "cf_access_team_domain", None)
    monkeypatch.setattr(settings, "cf_access_aud", None)
    api_auth._jwks_client.cache_clear()
    try:
        assert api_auth._verify_cf_access_jwt("token") is None
    finally:
        api_auth._jwks_client.cache_clear()
