"""Settings hygiene for the Secret-Manager-backed values.

Regression guard for a real prod outage: the `ADMIN_TOKEN` secret version was
created with a trailing newline, Cloud Run injected the raw bytes, and because
an HTTP header cannot carry a newline the X-Admin-Token break-glass path
answered 401 for every possible token value.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException, Response

from api.auth import require_admin
from core.config import Settings, settings


SECRET_FIELDS = ("database_url", "cf_access_team_domain", "cf_access_aud", "admin_token")


@pytest.mark.parametrize("field", SECRET_FIELDS)
@pytest.mark.parametrize("raw", ["value\n", "value\r\n", "  value  ", "value\t"])
def test_trailing_whitespace_is_stripped(field: str, raw: str) -> None:
    assert getattr(Settings(**{field: raw}), field) == "value"


@pytest.mark.parametrize("field", SECRET_FIELDS)
@pytest.mark.parametrize("blank", ["", "   ", "\n"])
def test_blank_becomes_none(field: str, blank: str) -> None:
    """A whitespace-only secret must not read as a configured value — the admin
    gate has to fail closed (503) rather than compare against an empty string."""
    assert getattr(Settings(**{field: blank}), field) is None


@pytest.mark.parametrize("field", SECRET_FIELDS)
def test_clean_value_survives_untouched(field: str) -> None:
    assert getattr(Settings(**{field: "abc123"}), field) == "abc123"


def test_admin_gate_accepts_header_when_secret_had_a_newline(monkeypatch) -> None:
    """The outage itself: secret stored as "tok\\n", header can only send "tok"."""
    monkeypatch.setattr(settings, "admin_token", Settings(admin_token="tok\n").admin_token)

    response = Response()
    require_admin(response, x_admin_token="tok", cf_access_jwt=None)  # must not raise
    # The gate stamps the no-store header on the response it lets through.
    assert response.headers["cache-control"] == "private, no-store"

    with pytest.raises(HTTPException) as excinfo:
        require_admin(Response(), x_admin_token="wrong", cf_access_jwt=None)
    assert excinfo.value.status_code == 401
