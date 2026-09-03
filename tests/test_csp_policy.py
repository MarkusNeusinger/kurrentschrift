"""The delivery-side security policy — `app/security-headers.conf` held against
the files it actually describes.

Three things here can drift silently, and each has cost someone a day
somewhere:

1. **The inline-script hashes.** The policy allows `app/index.html`'s two
   inline scripts by sha256 instead of `'unsafe-inline'`, which is the whole
   point of having a `script-src` at all. A hash is computed over the exact
   bytes between `<script>` and `</script>`, so a single re-indent of that
   block silently stops the Plausible stub and the hero preload from running.
   The report-only week would catch it — once. This catches it before merge.

2. **nginx's `add_header` inheritance.** A location with any `add_header` of
   its own drops every inherited one. `app/nginx.conf` therefore re-includes
   the snippet in each such location, and forgetting that in a new location is
   invisible in review and invisible in the browser until someone checks that
   one URL.

3. **The report endpoint.** The policy names a URL on the API host; if the
   route moves, reports stop arriving and nothing says so.

The nginx parse is deliberately crude — a brace counter over one file we write
ourselves, not a config parser. It only has to be right about this file.
"""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

from api.routers.csp import router as csp_router


ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "app" / "index.html"
HEADERS_CONF = ROOT / "app" / "security-headers.conf"
NGINX_CONF = ROOT / "app" / "nginx.conf"

INCLUDE_LINE = "include /etc/nginx/security-headers.conf;"

# `</script\s*>`, not `</script>`: HTML lets whitespace stand before the closing
# angle bracket, so a browser ends the element at `</script >` while a literal
# pattern reads on to the NEXT closing tag — and then hashes two scripts as one
# (CodeQL's `py/bad-tag-filter`). The same class of mismatch is why the comment
# strip below exists.
_SCRIPT = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>", re.DOTALL | re.IGNORECASE)
_TYPE = re.compile(r"""type\s*=\s*["']?([^"'\s>]+)""", re.IGNORECASE)
# `src=` as a substring matched `data-src=` too, and missed `SRC = "…"` — an
# EXTERNAL script read as inline gets a hash for its (empty) body, and an
# INLINE one read as external loses the hash it needs. The boundary is a space
# or a closing quote rather than `\b`, because `\b` sits inside `data-src` as
# well (the hyphen is a non-word character).
_SRC_ATTR = re.compile(r"""(?:^|[\s"'])src\s*=""", re.IGNORECASE)
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
# A <script> whose type is none of these is a DATA BLOCK (the JSON-LD in
# index.html): the browser never executes it, and CSP never asks for a hash.
_EXECUTABLE_TYPES = {"", "module", "text/javascript", "application/javascript"}


def inline_script_hashes(html: str) -> list[str]:
    """`sha256-…` for every executable inline script, in document order.

    Commented-out markup is removed first: a `<script>` inside `<!-- -->` never
    runs, so hashing it would put a permanent phantom into the policy — and the
    day someone deletes the comment, the hash would still be there, allowing a
    script nobody can see any more (this is what bit anyplot's index.html).
    """
    out = []
    for match in _SCRIPT.finditer(_COMMENT.sub("", html)):
        attrs = match.group("attrs")
        if _SRC_ATTR.search(attrs):
            continue
        declared = _TYPE.search(attrs)
        if (declared.group(1).lower() if declared else "") not in _EXECUTABLE_TYPES:
            continue
        digest = hashlib.sha256(match.group("body").encode("utf-8")).digest()
        out.append(f"sha256-{base64.b64encode(digest).decode('ascii')}")
    return out


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


def locations_with_add_header() -> list[str]:
    """Every `location …{ … }` block of app/nginx.conf that sets a header itself.

    Returned as the raw block text, so the caller can check what is inside it.
    """
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
    return [b for b in blocks if _ADD_HEADER.search(_without_comments(b))]


def test_script_src_allows_exactly_the_inline_scripts_of_index_html():
    """Every inline script is hashed, and no hash outlives the script it was for."""
    expected = inline_script_hashes(INDEX_HTML.read_text(encoding="utf-8"))
    assert expected, "app/index.html has no inline scripts — did the extraction break?"
    allowed = [t.strip("'") for t in csp_directives()["script-src"] if t.startswith("'sha256-")]
    assert sorted(allowed) == sorted(expected), (
        "script-src hashes and app/index.html's inline scripts disagree.\n"
        f"  in the policy: {sorted(allowed)}\n"
        f"  in index.html: {sorted(expected)}\n"
        "Recompute after ANY edit to an inline <script> — even whitespace."
    )


def test_the_script_scanner_reads_html_the_way_a_browser_does():
    """The extractor decides which hashes the policy must carry, so its blind
    spots become policy holes. Three of them, each with its own way of lying:

    * `</script >` — legal HTML. A literal `</script>` pattern reads past it to
      the next closing tag and hashes TWO scripts as one, so the real first
      script gets no hash and stops running (CodeQL `py/bad-tag-filter`).
    * `SRC = "…"` / `data-src=` — an external script read as inline earns a
      hash for its empty body; an inline one read as external loses its hash.
    * a commented-out `<script>` — never runs, so its hash is a standing
      permission for code that is not in the page.
    """
    only = inline_script_hashes("<script>x()</script >\n<script>y()</script>")
    assert len(only) == 2, "a space before the closing bracket swallowed the next script"

    assert inline_script_hashes('<script SRC = "/a.js"></script>') == []
    assert inline_script_hashes('<script data-src="x">z()</script>') == inline_script_hashes("<script>z()</script>")

    assert inline_script_hashes("<!-- <script>ghost()</script> -->") == []
    # …and the comment must not eat what follows it either.
    assert inline_script_hashes("<!-- note --><script>real()</script>") == inline_script_hashes(
        "<script>real()</script>"
    )


def test_script_src_never_falls_back_to_unsafe_inline():
    """'unsafe-inline' would make the hashes decoration.

    It is also silently ignored by browsers as soon as a hash is present, so a
    well-meant "safety margin" here would be a no-op in Chromium and a hole in
    whatever reads the policy leniently.
    """
    assert "'unsafe-inline'" not in csp_directives()["script-src"]


def test_style_src_keeps_unsafe_inline_and_says_so():
    """The one place it IS allowed — Emotion has no other path (see the conf)."""
    assert "'unsafe-inline'" in csp_directives()["style-src"]
    assert "Emotion" in HEADERS_CONF.read_text(encoding="utf-8")


def test_policy_reports_to_a_route_this_api_serves():
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


def test_the_spa_shell_is_never_cached_by_its_age():
    """`location = /index.html` with `no-cache` — the white-page fix.

    Without a Cache-Control the shell carried only Last-Modified, so browsers
    cached it heuristically and, after a deploy, asked for asset hashes that
    `try_files … =404` no longer knows.
    """
    conf = NGINX_CONF.read_text(encoding="utf-8")
    block = re.search(r"location\s*=\s*/index\.html\s*\{(.*?)\}", conf, re.DOTALL)
    assert block, "no `location = /index.html` block in app/nginx.conf"
    assert re.search(r'add_header\s+Cache-Control\s+"no-cache"', block.group(1))


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
