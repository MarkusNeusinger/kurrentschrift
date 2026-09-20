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

Two properties are borrowed verbatim from the archive client
(`tools/wordbench/fetch_fixtures.py`), because the admin token travels as a
HEADER and both of them exist to keep it where it was sent:

* **Redirects are refused, never followed.** urllib forwards custom headers to
  the redirect target, so a 3xx would resend `X-Admin-Token` to another host —
  and the apex `kurrentschrift.ink` really does 302 at the Cloudflare Access
  edge, which makes this a plausible typo, not a theoretical one (found in
  review, PR #410).
* **The scheme must be https**, except against loopback, where the request
  never leaves the machine — that is the local dev server and the restore
  drills.
* **Every request names itself** in a `User-Agent`. urllib's default is
  `Python-urllib/3.x`, and Cloudflare answers that in front of the API with a
  403 (error 1010) before FastAPI ever sees the call — so `setup`, `sync` and
  `pull` could not reach production at all (found 2026-08-25, on the way to the
  first real Bogen). The archive client has carried a name since it was
  written; this one had not.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import NamedTuple
from urllib.parse import urlsplit


DEFAULT_API = "https://api.kurrentschrift.ink"

# Sent on every call. An anonymous urllib request is refused by the edge, not
# by the API — see the module docstring.
USER_AGENT = "kurrentschrift-eigenhand/1.0"

# Strip uploads carry ~350 KB base64 over a home uplink; the bookkeeping calls
# are small. One generous timeout beats two constants nobody tunes.
TIMEOUT_S = 120

_LOOPBACK = ("localhost", "127.0.0.1", "::1")


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Turn every 3xx into an HTTPError instead of following it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ANN201
        return None


_OPENER = urllib.request.build_opener(_NoRedirectHandler())


def api_base(value: str | None = None) -> str:
    """The API base URL: the flag, else $EIGENHAND_API, else production.

    Refuses a plaintext scheme unless the host is loopback: the admin token
    rides in a header, and `http://` to anywhere else would put it on the wire
    in the clear.
    """
    base = (value or os.environ.get("EIGENHAND_API") or DEFAULT_API).rstrip("/")
    parts = urlsplit(base)
    if parts.scheme != "https" and (parts.hostname or "") not in _LOOPBACK:
        raise SystemExit(
            f"API base must be https:// (or loopback for local dev), got {base!r} — "
            "the admin token travels as a header and must not go out in the clear"
        )
    return base


def admin_token(value: str | None = None) -> str:
    """The admin token, or a refusal that names both ways to supply it."""
    token = value or os.environ.get("ADMIN_TOKEN")
    if not token:
        raise SystemExit("no admin token — set ADMIN_TOKEN or pass --token")
    return token


class Answer(NamedTuple):
    """One admin answer: the bytes, and the entity tag they came with.

    The tag exists because a guarded write has to say which stored state it was
    made on: the Streifen-Pfad routes answer a read with an `ETag` and refuse a
    write that does not echo it in `If-Match` (412/428). Carried beside the
    body rather than parsed out of it — it is a property of the ANSWER, and a
    token reassembled from the payload would be this machine's opinion of what
    is stored rather than the server's.
    """

    body: bytes
    etag: str | None


def request_answer(
    method: str, url: str, token: str, body: dict | None = None, allow_404: bool = False, *, if_match: str | None = None
) -> Answer | None:
    """One admin call. Raises SystemExit with the server's own words on 4xx/5xx.

    `allow_404` turns „not there" into ``None`` for the callers where absence
    is an answer rather than a failure — a hand that has no standing setup yet
    is the normal state before the first one is typed.

    `if_match` is passed through verbatim, quotes and all: it is an opaque
    token the server handed out, and a client that reformats one is a client
    that can no longer say which list it read.
    """
    data = json.dumps(body).encode() if body is not None else None
    headers = {"X-Admin-Token": token, "User-Agent": USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if if_match is not None:
        headers["If-Match"] = if_match
    req = urllib.request.Request(url, data=data, method=method, headers=headers)  # noqa: S310 — scheme checked above
    try:
        # `_OPENER` refuses redirects, so the admin header can never be resent
        # to a host other than the one it was addressed to.
        with _OPENER.open(req, timeout=TIMEOUT_S) as res:
            return Answer(res.read(), res.headers.get("ETag"))
    except urllib.error.HTTPError as exc:
        if allow_404 and exc.code == 404:
            return None
        # The API's `detail` is written for exactly this reader — it says what
        # to fix and in which order. Truncated, never swallowed.
        raise SystemExit(f"{method} {url} → {exc.code}: {exc.read().decode()[:400]}") from exc


def request_bytes(
    method: str, url: str, token: str, body: dict | None = None, allow_404: bool = False, *, if_match: str | None = None
) -> bytes | None:
    answer = request_answer(method, url, token, body, allow_404, if_match=if_match)
    return None if answer is None else answer.body


def request_json(
    method: str, url: str, token: str, body: dict | None = None, allow_404: bool = False, *, if_match: str | None = None
) -> dict | None:
    raw = request_bytes(method, url, token, body, allow_404, if_match=if_match)
    return None if raw is None else json.loads(raw.decode() or "{}")


def request_json_with_etag(
    method: str, url: str, token: str, body: dict | None = None, allow_404: bool = False, *, if_match: str | None = None
) -> tuple[dict | None, str | None]:
    """The parsed answer and its entity tag — the read before a guarded write.

    Two returns rather than one, because the caller needs both and neither is
    derivable from the other: the payload is what it merges into, the tag is
    what it has to echo to be allowed to write the merge back. A `None` tag
    means the answer carried none — the write will then be refused by the
    server, which is the loud failure and the right one.
    """
    answer = request_answer(method, url, token, body, allow_404, if_match=if_match)
    if answer is None:
        return None, None
    return json.loads(answer.body.decode() or "{}"), answer.etag
