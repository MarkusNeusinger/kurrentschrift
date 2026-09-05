"""The delivery-side security policy — `app/security-headers.conf` held against
the files it actually describes.

Four things here can drift silently, and each has cost someone a day
somewhere:

1. **The nonce, which lives in two files at once.** `script-src` names
   `'nonce-$request_id'`; `app/nginx.conf` stamps that same `$request_id` onto
   every `<script` tag with `sub_filter`. Nothing but agreement makes them one
   mechanism. Until 2026-09-04 this was a pair of sha256 hashes, and the whole
   tokenizer that recomputed them from `app/index.html` went with them — a
   hash cannot cover the inline script Cloudflare injects at the edge, whose
   body carries a per-response ray id (the reasoning is in the conf).

2. **nginx's `add_header` inheritance.** A location with any `add_header` of
   its own drops every inherited one. `app/nginx.conf` therefore re-includes
   the snippet in each such location, and forgetting that in a new location is
   invisible in review and invisible in the browser until someone checks that
   one URL.

3. **The report endpoint.** The policy names a URL on the API host; if the
   route moves, reports stop arriving and nothing says so.

4. **The shell's cacheability.** A nonced body that a client may keep and
   replay under a fresh header is the classic way a nonce policy takes a site
   down.

All of it is enforced since 2026-09-05, which is exactly why these have to be
tests: while the policy was Report-Only a broken half was invisible in a
browser, and it is the workbench — the surface no automated pass can open —
that a broken half now takes down.

The nginx parse is deliberately crude — a brace counter over one file we write
ourselves, not a config parser. It only has to be right about this file.
"""

from __future__ import annotations

import re
from pathlib import Path

from api.routers.csp import router as csp_router


ROOT = Path(__file__).resolve().parent.parent
HEADERS_CONF = ROOT / "app" / "security-headers.conf"
NGINX_CONF = ROOT / "app" / "nginx.conf"

INCLUDE_LINE = "include /etc/nginx/security-headers.conf;"


def csp_header_name() -> str:
    """The name the policy is delivered under — enforcing or report-only.

    Read separately from the value, because it is the ONE token that decides
    whether a mistake anywhere else in this file is a log line or an outage.
    """
    conf = HEADERS_CONF.read_text(encoding="utf-8")
    match = re.search(r"^add_header\s+(Content-Security-Policy(?:-Report-Only)?)\s", conf, re.MULTILINE)
    assert match, "no Content-Security-Policy header found in app/security-headers.conf"
    return match.group(1)


def csp_directives() -> dict[str, list[str]]:
    """The Content-Security-Policy(-Report-Only) value, split by directive."""
    conf = HEADERS_CONF.read_text(encoding="utf-8")
    match = re.search(r'add_header\s+Content-Security-Policy(?:-Report-Only)?\s+"([^"]+)"', conf)
    assert match, "no Content-Security-Policy header found in app/security-headers.conf"
    directives = {}
    for part in match.group(1).split(";"):
        tokens = part.split()
        if tokens:
            directives[tokens[0]] = tokens[1:]
    return directives


_ADD_HEADER = re.compile(r"^\s*add_header\b", re.MULTILINE)


def _without_comments(text: str) -> str:
    """nginx comment lines dropped — a `#` line that MENTIONS `add_header` is
    prose, and prose must not count as a directive (it did, on the first run)."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def _all_location_blocks() -> list[str]:
    """Every `location …{ … }` block of app/nginx.conf, as raw text."""
    conf = NGINX_CONF.read_text(encoding="utf-8")
    blocks = []
    for match in re.finditer(r"^\s*location\s[^{]*\{", conf, re.MULTILINE):
        depth = 0
        start = match.start()
        for i in range(match.end() - 1, len(conf)):
            if conf[i] == "{":
                depth += 1
            elif conf[i] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(conf[start : i + 1])
                    break
    return blocks


def locations_with_add_header() -> list[str]:
    """Every location block that sets a header itself, and so drops the rest."""
    return [b for b in _all_location_blocks() if _ADD_HEADER.search(_without_comments(b))]


# The nonce as the stamp spells it. Its counterpart in the header is read out
# of the PARSED directive, never out of the raw file: security-headers.conf
# explains itself at length and quotes `'nonce-…'` in its own prose, so a regex
# over the whole file would happily report a nonce the policy no longer carries.
_STAMP = re.compile(r"""sub_filter\s+'<script'\s+'<script nonce="(\$[A-Za-z_][A-Za-z0-9_]*)"'\s*;""")
_HEADER_NONCE = re.compile(r"^'nonce-(\$[A-Za-z_][A-Za-z0-9_]*)'$")


def header_nonce_variable() -> str | None:
    """The nginx variable `script-src` reads its nonce from, if any."""
    for token in csp_directives().get("script-src", []):
        match = _HEADER_NONCE.match(token)
        if match:
            return match.group(1)
    return None


def test_the_policy_is_delivered_enforcing():
    """The header name, which is the whole difference between a log and an outage.

    Report-Only from 2026-09-02, enforcing since 2026-09-05 by the author's
    decision: that time — 40 hours of it on the nonce path — produced no report
    from the site's own code, only the deliberate probe and once two reports
    from a single client whose injected Cloudflare script had not been stamped
    (see the conf for the evidence and the rollback).

    This test is the record of that state, not a ban on ever going back. A
    deliberate return to Report-Only — a source turns up that nothing found —
    changes the header and this line together, and that is the point: the
    repository should never disagree with what the edge is serving.
    """
    assert csp_header_name() == "Content-Security-Policy", (
        f"the policy is delivered as {csp_header_name()!r}. Enforcing is the state of "
        "2026-09-05; a deliberate rollback to Report-Only updates this test with the header."
    )


def test_script_src_takes_its_nonce_from_a_per_request_variable():
    """A nonce is only a nonce if it is fresh per response.

    A literal would be a constant baked into an image and reused for the life
    of a revision, which is `'unsafe-inline'` with extra syllables.
    `$request_id` is nginx's own 16 random bytes as 32 hex digits: hex is
    inside the base64-value charset the CSP nonce grammar accepts, and 16 bytes
    is the 128 bits of entropy CSP recommends.
    """
    script_src = csp_directives()["script-src"]
    nonces = [t for t in script_src if t.startswith("'nonce-")]
    assert nonces == ["'nonce-$request_id'"], (
        f"script-src carries {nonces or 'no nonce'}; expected exactly one, 'nonce-$request_id'."
    )


def test_the_header_and_the_stamp_name_the_same_variable():
    """The failure with no symptom until every inline script is dead.

    The policy promises a nonce; `sub_filter` writes one onto the tags. Nothing
    connects the two files but this equality. While the policy was Report-Only a
    mismatch was invisible — the page still worked and the reports looked like
    noise — and since it went enforcing the same mismatch takes the workbench
    down, which is the surface no automated pass can open.
    """
    stamps = _STAMP.findall(NGINX_CONF.read_text(encoding="utf-8"))
    assert stamps, (
        "app/nginx.conf stamps no CSP nonce onto <script> tags. Report-Only used to "
        "hide that; the enforcing policy does not."
    )
    assert set(stamps) == {header_nonce_variable()}, (
        f"the stamp writes {sorted(set(stamps))} but script-src reads "
        f"{header_nonce_variable()!r} — the tags would carry a nonce the policy does not allow."
    )


def test_script_src_asks_for_a_sample():
    """Without `'report-sample'` a report cannot name the script it is about.

    A nonce policy collapses every inline violation onto one
    directive/blocked/document tuple, so the sample is the only field that says
    WHICH inline script was reported — which is how the report-only hours could
    tell Cloudflare's injected script apart from one of ours, and how an
    enforced block will be read the same way. Measured on the live site before
    this change: the report arrived with an EMPTY sample, because the directive
    did not ask for one.
    """
    assert "'report-sample'" in csp_directives()["script-src"], (
        "script-src does not ask for a sample, so every inline violation reports as an "
        "anonymous 'inline' and the report week cannot name the script it is about."
    )


def test_the_stamp_sits_at_server_level():
    """Both routes to the shell, not one of them.

    `location = /index.html` answers a direct request and `location /`'s
    `try_files … /index.html` fallback reaches it by internal redirect, so a
    stamp placed inside either location is a stamp missing from some path the
    site actually serves. Searching the whole file would be satisfied by a
    stamp buried in one location, which is exactly the regression this refuses,
    so the locations are cut out first.
    """
    conf = NGINX_CONF.read_text(encoding="utf-8")
    outside = conf
    for block in _all_location_blocks():
        outside = outside.replace(block, "")
    outside = _without_comments(outside)
    assert _STAMP.search(outside), (
        "the CSP nonce stamp is not at server level — a location that serves the shell "
        "without it hands out tags the policy will refuse."
    )
    assert "sub_filter_once off;" in outside, (
        "sub_filter replaces only the FIRST match without `sub_filter_once off`; "
        "index.html has more than one <script> tag."
    )


def test_script_src_never_falls_back_to_unsafe_inline():
    """'unsafe-inline' would make the nonce decoration.

    It is also silently ignored by browsers as soon as a nonce or hash is
    present, so a well-meant "safety margin" here would be a no-op in Chromium
    and a hole in whatever reads the policy leniently.
    """
    assert "'unsafe-inline'" not in csp_directives()["script-src"], (
        "script-src allows 'unsafe-inline' beside a nonce. Browsers ignore it, so this "
        "only tells the next reader there is a fallback where there is none."
    )


def test_style_src_keeps_unsafe_inline_and_says_so():
    """The one place it IS allowed — Emotion has no other path (see the conf)."""
    assert "'unsafe-inline'" in csp_directives()["style-src"]
    assert "Emotion" in HEADERS_CONF.read_text(encoding="utf-8")


def test_policy_reports_to_a_route_this_api_serves():
    """And it keeps reporting under enforcement — `report-uri` survived the
    switch on purpose, because a source that is actually being BLOCKED is worth
    hearing about more, not less."""
    directives = csp_directives()
    reported_to = directives["report-uri"][0]
    assert reported_to.endswith("/csp-report")
    served = {route.path for route in csp_router.routes}
    assert "/csp-report" in served, f"the policy reports to {reported_to}, which this API does not serve"


def test_every_nginx_location_with_its_own_header_reincludes_the_snippet():
    """nginx's add_header does not merge across levels — the trap this pins."""
    offenders = [b.splitlines()[0].strip() for b in locations_with_add_header() if INCLUDE_LINE not in b]
    assert not offenders, (
        "these locations set a header of their own and therefore DROP every "
        f"inherited security header: {offenders}. Add `{INCLUDE_LINE}` to each."
    )


def test_server_block_includes_the_snippet_too():
    """The locations without an add_header of their own inherit from here."""
    conf = NGINX_CONF.read_text(encoding="utf-8")
    # Outside every `location` block, i.e. at server level.
    outside = conf
    for block in locations_with_add_header():
        outside = outside.replace(block, "")
    assert INCLUDE_LINE in outside


def test_the_spa_shell_is_never_stored():
    """`location = /index.html` with `no-store` — two fixes in one header.

    The original one: without a Cache-Control the shell carried only
    Last-Modified, so browsers cached it heuristically and, after a deploy,
    asked for asset hashes that `try_files … =404` no longer knows.

    The second, since the nonce: a stored shell pairs yesterday's `nonce="…"`
    in the body with today's header, and a 304 is worse still, because HTTP
    says the 304's headers REPLACE the stored ones. `no-cache` used to buy a
    zero-byte 304 here and no longer can — `sub_filter` clears `Last-Modified`
    and `ETag` on any response it rewrites, measured against this config as a
    200 with the full body for a conditional request. Same bytes as `no-store`,
    without the guarantee; the conf carries the numbers.
    """
    conf = NGINX_CONF.read_text(encoding="utf-8")
    block = re.search(r"location\s*=\s*/index\.html\s*\{(.*?)\}", conf, re.DOTALL)
    assert block, "no `location = /index.html` block in app/nginx.conf"
    assert re.search(r'add_header\s+Cache-Control\s+"no-store"', block.group(1)), (
        "the shell carries a per-request CSP nonce and must not be storable"
    )


def test_report_to_stays_out_until_it_is_seen_delivering():
    """Measured on 2026-09-02: with `report-to` in the policy, Chromium ignores
    `report-uri` — as specified — and delivered NOTHING; without it, the same
    violation arrived in under a second. A channel that silences the working
    one without replacing it is worse than no channel.

    This is not a ban forever. It comes back the day a report is seen arriving
    through it over HTTPS — and then this test is the place to record that.
    """
    directives = csp_directives()
    assert "report-uri" in directives
    assert "report-to" not in directives
    conf = HEADERS_CONF.read_text(encoding="utf-8")
    assert not re.search(r"^add_header\s+Reporting-Endpoints\b", conf, re.MULTILINE), (
        "Reporting-Endpoints without a `report-to` in the policy announces an endpoint nothing uses"
    )


def test_the_transport_and_frame_headers_are_all_present():
    conf = HEADERS_CONF.read_text(encoding="utf-8")
    for header in (
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Strict-Transport-Security",
    ):
        assert re.search(rf"^add_header\s+{header}\b", conf, re.MULTILINE), f"{header} missing"
    # 180 days, and the author's decision of 2026-09-02 was explicitly WITHOUT
    # includeSubDomains and WITHOUT preload — both are hard to walk back.
    hsts = re.search(r'add_header\s+Strict-Transport-Security\s+"([^"]+)"', conf).group(1)
    assert hsts == "max-age=15552000", hsts


def test_every_header_is_marked_always():
    """Without `always`, nginx drops the header on error responses — a 404 and a
    500 are exactly the pages where a missing frame or sniff guard matters."""
    for line in HEADERS_CONF.read_text(encoding="utf-8").splitlines():
        if line.startswith("add_header"):
            assert line.rstrip().endswith("always;"), line
