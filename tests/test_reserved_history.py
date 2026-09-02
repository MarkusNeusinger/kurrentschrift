"""No NEW reserved-dataset blob may enter the public git history.

Publishing exposes every blob ever committed, not just HEAD, and this
repository has been public since 2026-05-19. The learned dataset — authored
ductus templates, Laufformen, occurrence statistics — is reserved outside the
MIT grant (README "License", `docs/reference/quellen-und-rechte.md` §5), so a
rendered template dump committed anywhere outside the code trees is a leak
that a later `git rm` does not undo.

History already holds five such payloads, pinned by content hash in
`ACCEPTED_BLOBS` below. The author decided to accept rather than purge them:
the design-sync preview dump on 2026-09-02, and the four pre-DB prototype
canonicals this net then surfaced on 2026-09-03, on the same reasoning.

Pinning them is what keeps the alarm meaningful rather than muting it: the
recorded blobs stay quiet, they are named in §5 with their reasoning, and any
payload that is not one of them turns this test red the day it lands. The
decision was to accept what is already public, NOT to accept the class.

Why by blob hash and not by path: a path allowlist would wave through a NEW
dump written to the same path, which is exactly the mistake this guards
against. The hash identifies one immutable object and nothing else.

The scan is scoped the way the `/audit-licenses` doctrine words it — a hit
under a code tree is source, a test or prose ABOUT the format, and those trees
legitimately carry these identifiers. `data/` is NOT such a tree: it holds
data by definition, and is the likeliest home for an authored payload, so it
is scanned.

Cost: every VERSION of every outside-tree path is its own blob, so this reads
a few thousand objects, not eighty — but it does so in two batched `cat-file`
calls and finishes in about three seconds. It is cheaper than pickaxing the
history per payload key (~8 s per pattern) and, unlike that, it inspects
content rather than trusting a path or an extension.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent

# Identifiers that only a reserved payload carries — every wire shape §5
# reserves, not just the canonical templates: templates and their renders
# (`skeleton_polyline_px`, `anchors_template`, `half_widths_template`,
# `centerlines_template`, `outline_paths`), per-occurrence instances
# (`anchors`, `half_widths`, `strokes`) and per-hand aggregates
# (`cluster_center`, `connector_center`). The short forms are deliberate:
# `anchors` subsumes `pixel_anchors` and `anchors_template`, `half_widths`
# subsumes `half_widths_px`. Measured against the whole history, widening the
# list this far adds no false positive — it still flags exactly the five
# recorded blobs.
PAYLOAD_KEYS = (
    b"skeleton_polyline",
    b"anchors",
    b"half_widths",
    b"centerlines",
    b"outline_paths",
    b"strokes",
    b"cluster_center",
    b"connector_center",
)

# A key alone is not a leak: CHANGELOG.md, CLAUDE.md and the generator scripts
# all NAME these fields, and prose about the format is explicitly allowed. What
# distinguishes a dump is that the numbers travel with the key — so a blob only
# counts when it also carries a long run of numeric literals. Without this the
# net cries wolf on every release note that mentions a field name, and a net
# that always fires is one nobody reads.
# The separator has to tolerate brackets, not just commas: dense geometry is
# just as often nested (`anchors_template: [[x, y], …]`, `outline_paths`) as
# flat, and a comma-only run breaks at every `],[` — so a dump made only of
# coordinate PAIRS would have slipped through while looking guarded.
_NUMBER_RUN = re.compile(rb"(?:-?\d+(?:\.\d+)?[\s,\[\]]+){40,}")

# Trees whose contents are source, tests, tooling or documentation about the
# format. `/audit-licenses` states the same rule in prose.
# `data/` is deliberately NOT here: `datenablage.md` defines it as data, not
# code, and it is the most natural place for someone to put an authored
# payload — exempting it would blind the guard exactly where it is needed.
CODE_TREES = (
    "core/",
    "api/",
    "app/",
    "tools/",
    "tests/",
    "docs/",
    "alembic/",
    "scripts/",
    "changelog.d/",
    ".claude/",
    ".github/",
)

# Blob hash → path, for payloads the author has DECIDED to accept rather than
# purge. Adding a line here is a licensing decision, never a way to get a test
# green: it belongs to the author, and the reasoning goes in
# `docs/reference/quellen-und-rechte.md` §5 in the same PR.
ACCEPTED_BLOBS = {
    # Decision of 2026-09-02: the design-sync preview dump.
    "4e02e1a7be720d34c3f161c17afe821a1032df1b": ".design-sync/previews/_writtenGlyphData.ts",
    # Decision of 2026-09-03, same reasoning: the pre-DB hand-traced canonicals
    # of the very first prototype, added 2026-05-20 (4dc98c7) and gone from
    # HEAD since 2026-05-22 (9365b65), when /mvp/ moved to /core/ + Postgres.
    # The 2026-09-02 audit had set them aside as "0,9–1,1 KB hand seeds";
    # measured they are 6.5–53 KB and carry 50 anchors plus half widths each,
    # the same class of authored geometry as the blob above. This net is what
    # corrected that, which is why they are listed rather than dismissed.
    "0625420282bb2bf4ff6d4b9ce1a7a37e896667e2": "mvp/canonical/e-medial_v0.json",
    "5592aa6840ed79a34804e5c6c910b4a2751bcff1": "mvp/canonical/e-medial_v0.json",
    "c9ffc7a207a1d9ed89712dc0d5fa279964e5d5b3": "mvp/canonical/s-final_v0.json",
    "bfd13c3c568dfdb8a44e04df1e13e43c82a3eaf6": "mvp/canonical/s-medial_v0.json",
}


def _git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, check=True).stdout


def _candidate_blobs() -> dict[str, str]:
    """Blob hash → path for every object ever committed outside the code trees."""
    named: dict[str, str] = {}
    for line in _git("rev-list", "--objects", "--all").splitlines():
        sha, _, path = line.decode("utf-8", "surrogateescape").partition(" ")
        path = path.strip()
        if not path or path.startswith(CODE_TREES):
            continue
        named.setdefault(sha, path)
    if not named:
        return {}

    # One batch call resolves the types; trees share the namespace with blobs.
    probe = "\n".join(named).encode() + b"\n"
    checked = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        input=probe,
        capture_output=True,
        check=True,
    ).stdout
    blobs = {}
    for line in checked.split(b"\n"):
        parts = line.split()
        if len(parts) == 2 and parts[1] == b"blob":
            sha = parts[0].decode()
            blobs[sha] = named[sha]
    return blobs


def _blobs_carrying_payload(blobs: dict[str, str]) -> dict[str, str]:
    """Subset whose CONTENT holds a rendered-template identifier."""
    if not blobs:
        return {}
    stream = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "--batch"],
        input="\n".join(blobs).encode() + b"\n",
        capture_output=True,
        check=True,
    ).stdout

    found: dict[str, str] = {}
    pos = 0
    while pos < len(stream):
        header_end = stream.find(b"\n", pos)
        if header_end == -1:
            break
        header = stream[pos:header_end].split()
        if len(header) != 3:  # "<sha> missing" or malformed — nothing to read
            pos = header_end + 1
            continue
        sha, size = header[0].decode(), int(header[2])
        body = stream[header_end + 1 : header_end + 1 + size]
        if any(key in body for key in PAYLOAD_KEYS) and _NUMBER_RUN.search(body):
            found[sha] = blobs[sha]
        pos = header_end + 1 + size + 1  # trailing newline after the body
    return found


@pytest.fixture(scope="module")
def payload_blobs() -> dict[str, str]:
    try:
        # A shallow clone has no history to walk, so the scan would come back
        # empty and BOTH tests below would report something untrue — one a
        # false all-clear, the other a false alarm. Skipping says so out loud
        # instead. CI checks out the backend job with fetch-depth: 0 for
        # exactly this reason.
        # (Asked of git rather than by looking for `.git/shallow`: in a worktree
        # `.git` is a file and the marker lives in the shared git dir.)
        if _git("rev-parse", "--is-shallow-repository").strip() == b"true":
            pytest.skip("shallow clone: no history to scan (CI uses fetch-depth: 0)")
        return _blobs_carrying_payload(_candidate_blobs())
    except FileNotFoundError as exc:
        # No git executable at all — a genuinely unavailable environment, not a
        # verdict about the history. Everything else is deliberately NOT caught:
        # a failing `rev-list` or `cat-file` must turn this red, because a guard
        # that skips on its own errors lets CI stay green without ever looking.
        pytest.skip(f"git executable not available here: {exc}")


@pytest.mark.parametrize(
    ("shape", "body", "expected"),
    [
        # A flat width array — the shape that happened to be present in the
        # blobs already on record.
        ("flat", b'"half_widths_px": [' + b", ".join(b"0.5" for _ in range(50)) + b"]", True),
        # Coordinate PAIRS: `],[` between the numbers. A comma-only separator
        # broke the run here, so this dump would have passed as clean.
        ("nested pairs", b'"anchors_template": [' + b", ".join(b"[1.0, 2.0]" for _ in range(50)) + b"]", True),
        # Prose and code name the fields without carrying the numbers.
        ("prose mention", b"The payload carries `half_widths_px` and `outline_paths` per glyph.", False),
        # Numbers without a payload key are not a template dump.
        ("bare numbers", b"[" + b", ".join(b"3" for _ in range(200)) + b"]", False),
    ],
)
def test_detector_matches_payload_shapes_not_mentions(shape: str, body: bytes, expected: bool) -> None:
    """The detector needs a payload key AND numbers travelling with it."""
    detected = any(key in body for key in PAYLOAD_KEYS) and bool(_NUMBER_RUN.search(body))
    assert detected is expected, f"{shape}: expected detected={expected}"


def test_no_new_reserved_blob_in_history(payload_blobs: dict[str, str]) -> None:
    """Nothing carries a reserved payload except the blobs already on record.

    This is the repeat guard: the decision of 2026-09-02 was to accept what is
    already in the public history, NOT to accept the class. A payload committed
    from now on lands here as a red test on the day it lands, while a `git rm`
    later would not undo it.
    """
    unexpected = {sha: path for sha, path in payload_blobs.items() if sha not in ACCEPTED_BLOBS}
    assert not unexpected, (
        "NEW reserved template payload(s) in the public git history: "
        + ", ".join(f"{path} ({sha[:12]})" for sha, path in sorted(unexpected.items(), key=lambda kv: kv[1]))
        + ". Publishing exposes every blob ever committed and a later `git rm` does not undo it — "
        "do not add it to the allowlist to get green; see docs/reference/quellen-und-rechte.md §5."
    )


def test_recorded_blobs_still_describe_reality(payload_blobs: dict[str, str]) -> None:
    """Both maps describe history, so neither can quietly cover something else.

    If an entry stops matching — history rewritten after all, or a path moved —
    the line must go or be corrected, rather than sit there granting an
    exemption to nothing.
    """
    for sha, path in sorted(ACCEPTED_BLOBS.items()):
        assert sha in payload_blobs, f"recorded blob {sha[:12]} ({path}) is no longer in history — drop the entry"
        assert payload_blobs[sha] == path, f"recorded blob {sha[:12]} now lives at {payload_blobs[sha]}, not {path}"
