"""The one way the local chain talks to the admin API.

Three tools reach up to the server — `pull` (fetch a Bogen printed in the
admin view), `sync` (push the bookkeeping, and optionally the strips) and
`setup` (the standing nib/ink/paper). They had a private `urllib` helper each,
which is one copy too many the moment a timeout, a header or an error format
has to change.

Deliberately `urllib` rather than a client library: the tool family has no HTTP
dependency, and these are a handful of admin calls, not a transport layer.

The direction of travel is fixed and stays fixed: tools never write to the DB
themselves (`docs/reference/werkzeuge.md` — measurement layer, no DB writes).
Every write goes through the admin-gated API, which is what validates it.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


DEFAULT_API = "https://api.kurrentschrift.ink"

# Strip uploads carry ~350 KB base64 over a home uplink; the bookkeeping calls
# are small. One generous timeout beats two constants nobody tunes.
TIMEOUT_S = 120


def api_base(value: str | None = None) -> str:
    """The API base URL: the flag, else $EIGENHAND_API, else production."""
    return (value or os.environ.get("EIGENHAND_API") or DEFAULT_API).rstrip("/")


def admin_token(value: str | None = None) -> str:
    """The admin token, or a refusal that names both ways to supply it."""
    token = value or os.environ.get("ADMIN_TOKEN")
    if not token:
        raise SystemExit("no admin token — set ADMIN_TOKEN or pass --token")
    return token


def request_bytes(method: str, url: str, token: str, body: dict | None = None, allow_404: bool = False) -> bytes | None:
    """One admin call. Raises SystemExit with the server's own words on 4xx/5xx.

    `allow_404` turns „not there" into ``None`` for the callers where absence
    is an answer rather than a failure — a hand that has no standing setup yet
    is the normal state before the first one is typed.
    """
    data = json.dumps(body).encode() if body is not None else None
    headers = {"X-Admin-Token": token}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)  # noqa: S310 — https URL from argv
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as res:  # noqa: S310
            return res.read()
    except urllib.error.HTTPError as exc:
        if allow_404 and exc.code == 404:
            return None
        # The API's `detail` is written for exactly this reader — it says what
        # to fix and in which order. Truncated, never swallowed.
        raise SystemExit(f"{method} {url} → {exc.code}: {exc.read().decode()[:400]}") from exc


def request_json(method: str, url: str, token: str, body: dict | None = None, allow_404: bool = False) -> dict | None:
    raw = request_bytes(method, url, token, body, allow_404)
    return None if raw is None else json.loads(raw.decode() or "{}")
