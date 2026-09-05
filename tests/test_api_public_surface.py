"""The public/reserved split of the read API — the technical half of the
open-core reservation (docs/reference/quellen-und-rechte.md §5).

The site's crawler policy is open (`ai-train=yes` since 2026-08-28), so the
reservation of the learned dataset rests on exactly one mechanism: the reads
that carry it answer 401 without the admin credential. This suite pins that
split in both directions and keeps it complete:

- every GET route of the app must be listed as PUBLIC or RESERVED — a new read
  endpoint in neither set fails here, so the split can never drift silently;
- every PUBLIC read answers without credentials (any status but a gate's);
- every RESERVED read answers 401 without credentials, whatever else the
  request would have hit (a 404 for a missing row comes AFTER the gate);
- every NON-GET operation answers 401 without credentials, against an
  explicitly empty list of public write paths. Everything this API writes is
  authored data, so the list has nothing in it — but a future public write
  path has to be named there rather than simply forgotten.

PUBLIC is what the public pages and their crawlers need: catalogue descriptors
(styles, sources), the quiz bank, the /write renders, the slim bbox status
flags, the PD chart and its crops, and the word specimens whose sidecar lives
in the public repo already. Everything that carries a bbox row, a template
row, an occurrence, a pair override, a hand, an aggregate or the own-hand
Bestand is RESERVED.
"""

from __future__ import annotations

from fastapi.routing import APIRoute

from api.main import app
from tests.api_harness import Harness


# FastAPI's own documentation routes — not part of the split.
_FRAMEWORK = {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}

PUBLIC = {
    "/",
    "/health",
    "/robots.txt",
    "/llms.txt",
    "/seo-proxy/",
    "/seo-proxy/{route:path}",
    "/styles",
    "/styles/{style_id}",
    "/sources",
    "/sources/{source_id}",
    "/sources/{source_id}/chart",
    "/sources/{source_id}/bboxes/status",
    "/sources/{source_id}/bboxes/{glyph_key}/crop",
    "/sources/{source_id}/templates",
    "/sources/{source_id}/word-samples",
    "/sources/{source_id}/word-samples/{sample_id}/crop",
    "/sources/{source_id}/write/glyphs",
    "/sources/{source_id}/write/glyphs/{glyph_key}",
    "/sources/{source_id}/write/glyphs/{glyph_key}.svg",
    "/sources/{source_id}/write/word",
    "/sources/{source_id}/write/word.svg",
    "/quiz-words",
    # The Lesart page's readings: a handful of dictionary words per query,
    # never the vocabulary (its load is the admin POST/DELETE, not a GET).
    "/lesarten",
    "/lesarten/dictionary",
}

RESERVED = {
    "/hands",
    "/hands/{hand_id}",
    "/hands/{hand_id}/aggregates",
    "/hands/{hand_id}/pair-aggregates",
    "/sources/{source_id}/render-context",
    "/sources/{source_id}/bboxes",
    "/sources/{source_id}/bboxes/{glyph_key}",
    "/sources/{source_id}/templates/quality",
    "/sources/{source_id}/templates/{glyph_key}",
    "/sources/{source_id}/templates/{glyph_key}/diagnostic",
    "/sources/{source_id}/templates/{glyph_key}/fit",
    "/sources/{source_id}/templates/{glyph_key}/quality",
    "/sources/{source_id}/pairs",
    "/sources/{source_id}/pairs/{left_key}/{right_key}",
    "/sources/{source_id}/instances",
    "/sources/{source_id}/pair-instances",
    "/sources/{source_id}/word-instances",
    "/sources/{source_id}/word-samples/{sample_id}/score",
    "/sources/{source_id}/work-items",
    "/work-items",
    "/work-items/{item_id}",
    "/eigenhand/hands",
    "/eigenhand/bestand/{hand}",
    "/eigenhand/uebergangsraum",
    "/eigenhand/stacks/{hand}/pdf",
    "/eigenhand/sheets/{hand}/{sheet}/pdf",
    "/eigenhand/sheets/{hand}/{sheet}/layout",
    "/eigenhand/archive/{hand}",
    "/eigenhand/setups",
    "/eigenhand/setups/{hand}",
    "/eigenhand/strips/{hand}",
    "/eigenhand/strips/{hand}/{strip}/{fassung}",
}

# Non-GET operations that are deliberately open to the public. It exists so
# that opening a write path is a visible, named decision rather than a
# forgotten decorator, and it held exactly ONE entry for a long time by being
# empty: everything this API writes is authored data — bboxes, templates,
# Laufform rows, occurrences, pair overrides, work items, the own-hand Bestand
# — i.e. exactly the reserved dataset (quellen-und-rechte.md §5).
#
# `POST /csp-report` is the first exception and does not touch that argument:
# it accepts a browser's account of the SITE's own Content-Security-Policy,
# writes nothing anywhere (api/routers/csp.py logs and counts in process), and
# must answer anonymously or the report channel delivers nothing at all. It
# reads no data and returns none — its 204 carries no body.
PUBLIC_WRITES: set[tuple[str, str]] = {("POST", "/csp-report")}

# Placeholder values for the path parameters; `{source_id}` is filled from the
# seeded source at request time.
_PARAMS = {
    "style_id": "teststyle",
    "glyph_key": "n",
    "sample_id": "wenn",
    "hand_id": "test-hand",
    "item_id": "1",
    "left_key": "n",
    "right_key": "e",
    "hand": "mn-suetterlin",
    "sheet": "B0001",
    "strip": "S0001",
    "fassung": "1",
    # Only write paths reach these (the Lesart vocabulary load) — the gate
    # fires long before the value means anything.
    "gen": "1",
}
# The renders 422 without their query — a 422 is not a gate, but a real
# request is the more honest probe.
_QUERY = {
    "/sources/{source_id}/write/glyphs": {"keys": "n"},
    "/sources/{source_id}/write/word": {"text": "n"},
    "/sources/{source_id}/write/word.svg": {"text": "n"},
}
_GATE_STATUSES = {401, 403}


def _routes() -> list[tuple[str, str]]:
    """Every (method, path) operation the app serves, included routers flattened.

    Recent FastAPI keeps an included router as a lazy wrapper in `app.routes`
    (`original_router` + `include_context.prefix`) rather than copying its
    routes in; older versions inline them as `APIRoute`s. Both are walked."""
    found: list[tuple[str, str]] = []
    for route in app.routes:
        inner = getattr(route, "original_router", None)
        if inner is None:
            candidates = [(route, "")]
        else:
            prefix = getattr(getattr(route, "include_context", None), "prefix", "") or ""
            candidates = [(r, prefix) for r in inner.routes]
        for r, prefix in candidates:
            if not isinstance(r, APIRoute):
                continue
            path = prefix + r.path
            if path in _FRAMEWORK:
                continue
            found += [(method, path) for method in r.methods if method not in ("HEAD", "OPTIONS")]
    return found


def _get_routes() -> set[str]:
    """Every GET path the app serves."""
    return {path for method, path in _routes() if method == "GET"}


def _write_operations() -> set[tuple[str, str]]:
    """Every non-GET operation the app serves."""
    return {(method, path) for method, path in _routes() if method != "GET"}


def test_every_get_route_is_classified():
    routes = _get_routes()
    unclassified = sorted(routes - PUBLIC - RESERVED)
    stale = sorted((PUBLIC | RESERVED) - routes)
    assert not unclassified, f"GET routes in neither PUBLIC nor RESERVED: {unclassified}"
    assert not stale, f"classified paths that no longer exist: {stale}"
    assert not (PUBLIC & RESERVED)


def _fill(path: str, source_id: str) -> str:
    # `{route:path}` is a Starlette converter, not a format spec.
    return path.replace("{route:path}", "{route}").format(source_id=source_id, route="schriftkunde", **_PARAMS)


async def test_public_reads_answer_without_credentials(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    for path in sorted(PUBLIC):
        res = await api.client.request("GET", _fill(path, source_id), params=_QUERY.get(path))
        assert res.status not in _GATE_STATUSES, f"{path} is gated but listed PUBLIC ({res.status})"


async def test_reserved_reads_are_401_without_credentials(api: Harness):
    _, source_id = await api.seed_style_and_source()
    for path in sorted(RESERVED):
        res = await api.client.request("GET", _fill(path, source_id))
        assert res.status == 401, f"{path} answered {res.status} without the admin credential"


async def test_every_write_operation_is_gated(api: Harness):
    """No credential, no write — for EVERY non-GET operation, not a hand-kept
    sample of them.

    `tests/test_api_http.py::WRITE_ENDPOINTS` covered 11 of the 33 by hand, so
    a new POST/PUT/PATCH/DELETE that forgot `require_admin` fell through no net
    at all. This walks the router table instead, so the pin cannot go stale:
    every operation answers 401 (or 403 on a CF-Access identity outside the
    allow-list) before it ever looks at the body.
    """
    _, source_id = await api.seed_style_and_source()
    operations = _write_operations()
    # Non-vacuity: the app has 30+ write operations; a walk that finds a
    # handful means the router flattening broke, not that the surface shrank.
    assert len(operations) >= 30, f"only {len(operations)} write operations found — the route walk is broken"
    for method, path in sorted(operations):
        if (method, path) in PUBLIC_WRITES:
            continue
        res = await api.client.request(method, _fill(path, source_id), json_body={})
        assert res.status in _GATE_STATUSES, f"{method} {path} answered {res.status} without the admin credential"


async def test_every_public_write_is_named_and_argued(api: Harness):
    """The exception list is a decision, not a drawer.

    Each entry needs a case, and the case is written above the list. Today
    there is exactly one: `POST /csp-report`, which takes a browser's report
    about the SITE's own Content-Security-Policy, writes nothing and returns
    nothing (api/routers/csp.py). It must answer anonymously — a report cannot
    carry a credential — which is why it cannot simply be gated like the rest.

    A second entry is not forbidden; adding one WITHOUT extending this
    docstring is. And the path must really be reachable: the assertion below
    keeps the list from silently naming an operation that answers 401 anyway,
    which would look like an argued exception and be a dead line.
    """
    assert PUBLIC_WRITES == {("POST", "/csp-report")}
    res = await api.client.request("POST", "/csp-report", json_body={})
    assert res.status not in _GATE_STATUSES, "the one public write is gated after all"


async def test_reserved_reads_are_never_cacheable(api: Harness):
    """With the credential, every reserved read that answers with a body must
    say `no-store` — the gate stamps it (api.auth.require_admin), so this pins
    that no route bypasses the gate's response. Placeholder ids make many
    reads 404 here; those carry no rows and are not the concern."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    answered = 0
    for path in sorted(RESERVED):
        res = await api.client.request("GET", _fill(path, source_id), headers=api.admin_headers())
        if res.status >= 300:
            continue
        answered += 1
        assert "no-store" in res.headers.get("cache-control", ""), f"{path} is cacheable: {res.headers}"
    assert answered >= 8, f"only {answered} reserved reads answered 2xx — the probe lost its teeth"
