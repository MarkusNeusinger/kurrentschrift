"""`POST /csp-report` — where the site's Content-Security-Policy reports land.

The site ships its policy as `Content-Security-Policy-Report-Only` for one week
before it is switched to enforcing (`app/security-headers.conf`). A report-only
policy blocks nothing, so the week is worth exactly as much as the reports it
produces — hence this endpoint. It **counts and logs; it writes nothing**. No
table, no row, no reserved data: a violation report is a browser's account of
the SITE's own configuration, and the only thing anyone will ever do with it is
read a log line and add a source to the policy.

**Why it lives on the API host.** A report endpoint has to answer anonymously,
and the apex `/api/*` is gated by Cloudflare Access — an anonymous POST there
gets a 302 to a login. `api.kurrentschrift.ink` is the open host, and it passes
the Cloudflare edge exactly like every other browser request, so the origin
gate's header is stamped on the way in (`api/origin_gate.py`).

**Two body shapes, one endpoint.** There are two wire formats:

* `report-uri` POSTs a single object `{"csp-report": {...}}` as
  `application/csp-report`. Every current browser sends it, and it is the only
  channel the policy declares today;
* `report-to` (the Reporting API) POSTs an ARRAY of envelopes
  `[{"type": "csp-violation", "body": {...}}]` as `application/reports+json`,
  with camelCase field names where the old ones are hyphenated.

Only the first is in use — a browser walk on 2026-09-02 measured that
declaring `report-to` makes Chromium ignore `report-uri` and then deliver
nothing at all, so it was taken back out (`app/security-headers.conf` carries
the measurement). The second shape is parsed anyway: it costs one branch, and
it means the day `report-to` is proven to deliver, only the header changes.

**Every logged value is sanitised, and no reported URL is logged whole.** The
fields of a report are attacker-controlled — this is an anonymous POST — so a
value carrying a newline would forge further log entries. `_field` renders
control characters and caps the length of everything it returns, and it is the
one door all seven values pass through.

The public pages additionally put what the VISITOR TYPED into the URL —
`/federprobe?text=…` and `/lesen/vergleichen?text=…` are shareable by design —
and a report carries `document-uri` verbatim. Query and fragment are cut off
before anything is logged or memoised (`_path_only`), so a security measure
never turns into a transcript of what strangers wrote.

**Deliberately NOT exempt from the rate limiter.** This is the one POST on this
API that anyone may call, so the wide bucket (600/min per client) is precisely
the net it needs; a browser emits a handful of reports per document, orders of
magnitude below that. The one thing a limiter cannot bound is a single huge
body, so the read is capped here instead.

**Deliberately NOT exempt from the origin gate** either — reports come through
the edge like everything else. If the week produces no reports at all, that is
the first thing to check, with the probe in
`docs/reference/frontend-stack.md` §6.
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Any

from fastapi import APIRouter, Request, Response

from api.http import NO_STORE


logger = logging.getLogger(__name__)

router = APIRouter(tags=["security"])

# A CSP report is a few hundred bytes; 64 KB is room for a pathological
# `script-sample` and nothing more. Anything larger is not a browser.
MAX_BODY_BYTES = 64 * 1024

# One log line per distinct violation, and then one per hundredth repeat. A
# single missing source produces one report per page view, and a log that
# repeats it ten thousand times is a log nobody reads — but a violation that
# fires ten thousand times is also not the same finding as one that fires
# twice, and the every-hundredth line is where that difference shows.
# The dict is per process and lost on restart, which is correct: the point is
# to name the distinct violations of the report-only week, not to be a meter.
_REPEAT_INTERVAL = 100
# Above this many distinct violations the counter stops growing. A policy with
# 200 distinct violations does not need the 201st to be understood, and an
# unbounded dict is a memory leak with a public POST in front of it.
_MAX_TRACKED = 200

_lock = threading.Lock()
_seen: dict[tuple[str, str, str], int] = {}
# How many reports arrived after the memo filled up. Counted, not logged: a
# violation past the cap has no count of its own, so "first time seen" would be
# true forever and every single report would produce a line — the flood the
# memo exists to prevent, arriving through the door left open for it.
_overflow = 0


# Control characters, rendered rather than emitted. THE reason this exists: a
# report is an anonymous POST whose fields are interpolated into a log line, so
# a value carrying `\n` would forge further Cloud Logging entries, and other
# control characters can hide what the real entry says (Copilot review, PR #497).
_CONTROL = {c: f"\\x{c:02x}" for c in [*range(0x20), 0x7F]}
# Long enough for any real URL that matters, short enough that a padded field
# cannot push the interesting part of the line out of view.
MAX_FIELD_CHARS = 300


def _field(report: dict[str, Any], *names: str) -> str:
    """First non-empty value among `names`, as a SAFE string.

    The two wire formats spell the same field differently (`violated-directive`
    vs `effectiveDirective`), so every read names both.

    Every value the endpoint logs passes through here, which is what makes the
    sanitising trustworthy: there is one door, not seven.
    """
    for name in names:
        value = report.get(name)
        if value:
            return str(value).translate(_CONTROL)[:MAX_FIELD_CHARS]
    return "?"


def _path_only(url: str) -> str:
    """A reported URL with its query and fragment removed.

    **This is a privacy measure, not tidiness.** The public pages put what the
    VISITOR TYPED into the URL — `/federprobe?text=…` and
    `/lesen/vergleichen?text=…` are shareable by design — and a violation report
    carries `document-uri` verbatim. Logging it whole would copy a stranger's
    text into Cloud Logging as a side effect of a security measure. The path is
    what a policy finding is about; the query never is.

    Applied to `blocked-uri` for the same reason: a blocked request to this
    site's own API carries the rendered text in its query string.
    """
    for cut in ("#", "?"):
        url = url.split(cut, 1)[0]
    return url


def _reports(payload: Any) -> list[dict[str, Any]]:
    """Every violation object in a body of either shape."""
    if isinstance(payload, dict):
        inner = payload.get("csp-report")
        return [inner] if isinstance(inner, dict) else []
    if isinstance(payload, list):
        found = []
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            # `type` is absent on some implementations; a body that looks like a
            # CSP report is treated as one.
            body = entry.get("body")
            if isinstance(body, dict) and entry.get("type", "csp-violation") == "csp-violation":
                found.append(body)
        return found
    return []


def _record(report: dict[str, Any]) -> None:
    """Log a violation the first time it is seen, then every hundredth time."""
    global _overflow
    directive = _field(report, "effective-directive", "effectiveDirective", "violated-directive", "violatedDirective")
    blocked = _path_only(_field(report, "blocked-uri", "blockedURL", "blockedURI"))
    document = _path_only(_field(report, "document-uri", "documentURL", "documentURI"))
    key = (directive, blocked, document)
    with _lock:
        if key in _seen:
            count = _seen[key] + 1
            _seen[key] = count
        elif len(_seen) < _MAX_TRACKED:
            count = 1
            _seen[key] = count
        else:
            _overflow += 1
            count = None
            announce_overflow = _overflow == 1
    if count is None:
        if announce_overflow:
            logger.warning(
                "CSP reports: more than %d distinct violations seen — further NEW ones are counted, not logged",
                _MAX_TRACKED,
            )
        return
    if count == 1 or count % _REPEAT_INTERVAL == 0:
        logger.warning(
            "CSP report (#%d): %s blocked %s on %s — disposition=%s, source=%s:%s",
            count,
            directive,
            blocked,
            document,
            _field(report, "disposition"),
            _path_only(_field(report, "source-file", "sourceFile")),
            _field(report, "line-number", "lineNumber"),
        )


async def _read_capped(request: Request, limit: int) -> bytes | None:
    """The request body, or `None` once it exceeds `limit`.

    Read from the stream rather than `await request.body()` so an oversized
    body is refused while it arrives instead of after it is all in memory.
    """
    size = 0
    chunks: list[bytes] = []
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/csp-report", status_code=204, include_in_schema=False)
async def csp_report(request: Request) -> Response:
    """Take a browser's CSP violation report, log it, answer 204.

    `include_in_schema=False`: this is a browser-to-server channel described by
    the policy header, not part of the documented read API, and listing it in
    openapi.json would only invite it to be called by hand.

    The status codes are for humans holding a `curl`, not for browsers — a
    browser discards the response to a report unread, so nothing here can
    influence a page. `no-store` for the same reason a 429 carries it: the
    answer is about this one caller and must never be served to another.
    """
    raw = await _read_capped(request, MAX_BODY_BYTES)
    if raw is None:
        return Response(status_code=413, headers={"Cache-Control": NO_STORE})
    try:
        payload = json.loads(raw) if raw else None
    except (ValueError, UnicodeDecodeError):
        return Response(status_code=400, headers={"Cache-Control": NO_STORE})
    for report in _reports(payload):
        _record(report)
    return Response(status_code=204, headers={"Cache-Control": NO_STORE})
