"""No NEW reserved-dataset blob may enter the public git history.

Publishing exposes every blob ever committed, not just HEAD, and this
repository has been public since 2026-05-19. The learned dataset — authored
ductus templates, Laufformen, occurrence statistics — is reserved outside the
MIT grant (README "License", `docs/reference/quellen-und-rechte.md` §5), so a
rendered template dump committed anywhere outside the code trees is a leak
that a later `git rm` does not undo.

History already holds such payloads, and they are pinned by content hash in
two maps below. `ACCEPTED_BLOBS` is what the author DECIDED to accept on
2026-09-02 rather than purge — `.design-sync/previews/_writtenGlyphData.ts`,
added 2026-06-20 and untracked again on 2026-07-31. `PENDING_AUTHOR_DECISION`
is what this net surfaced afterwards and nobody has ruled on yet.

Pinning both is what keeps the alarm meaningful rather than muting it: the
recorded blobs stay quiet, they are named in §5 for what they are (settled or
open), and any payload that is not one of them turns this test red the day it
lands. The decision was to accept what is already public, NOT to accept the
class.

Why by blob hash and not by path: a path allowlist would wave through a NEW
dump written to the same path, which is exactly the mistake this guards
against. The hash identifies one immutable object and nothing else.

The scan is deliberately scoped the way the `/audit-licenses` doctrine words
it — a hit under a code tree is source, a test or prose ABOUT the format, and
those trees legitimately carry these identifiers. Only blobs outside them are
candidates, which also keeps the test cheap: it walks the ~80 paths that have
ever lived outside the code trees rather than pickaxing all of history, so its
cost grows with repository breadth, not with the number of commits.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent

# Identifiers that only a rendered template payload carries.
PAYLOAD_KEYS = (b"skeleton_polyline_px", b"pixel_anchors", b"half_widths_px", b"anchors_template", b"outline_paths")

# A key alone is not a leak: CHANGELOG.md, CLAUDE.md and the generator scripts
# all NAME these fields, and prose about the format is explicitly allowed. What
# distinguishes a dump is that the numbers travel with the key — so a blob only
# counts when it also carries a long run of numeric literals. Without this the
# net cries wolf on every release note that mentions a field name, and a net
# that always fires is one nobody reads.
_NUMBER_RUN = re.compile(rb"(?:-?\d+(?:\.\d+)?\s*,\s*){40,}")

# Trees whose contents are source, tests, tooling or documentation about the
# format. `/audit-licenses` states the same rule in prose.
CODE_TREES = (
    "core/",
    "api/",
    "app/",
    "tools/",
    "tests/",
    "docs/",
    "alembic/",
    "data/",
    "scripts/",
    "changelog.d/",
    ".claude/",
    ".github/",
)

# Blob hash → path, for payloads the author has DECIDED to accept rather than
# purge. Adding a line here is a licensing decision, never a way to get a test
# green: it belongs to the author, and the reasoning goes in
# `docs/reference/quellen-und-rechte.md` §5 in the same PR.
ACCEPTED_BLOBS = {"4e02e1a7be720d34c3f161c17afe821a1032df1b": ".design-sync/previews/_writtenGlyphData.ts"}

# Payloads this net found in the existing history that the author has NOT yet
# ruled on. They are pinned, not blessed: recording them is what keeps the
# alarm honest — the accepted blob is quiet, these are documented as an open
# question (`quellen-und-rechte.md` §5), and anything NOT in either map is a
# fresh leak that fails the test the day it lands.
#
# These three glyphs are the pre-DB hand-traced canonicals of the very first
# prototype, deleted from HEAD long before the DB existed. The 2026-09-02 audit
# recorded them as "0,9–1,1 KB hand seeds" and set them aside on that basis;
# measured, each blob is ~39 KB and carries 50 `pixel_anchors` plus
# `half_widths_px` — the same class of authored geometry as the accepted blob,
# not a stub. That correction is why they are listed here instead of dismissed.
PENDING_AUTHOR_DECISION = {
    "0625420282bb2bf4ff6d4b9ce1a7a37e896667e2": "mvp/canonical/e-medial_v0.json",
    "5592aa6840ed79a34804e5c6c910b4a2751bcff1": "mvp/canonical/e-medial_v0.json",
    "c9ffc7a207a1d9ed89712dc0d5fa279964e5d5b3": "mvp/canonical/s-final_v0.json",
    "bfd13c3c568dfdb8a44e04df1e13e43c82a3eaf6": "mvp/canonical/s-medial_v0.json",
}

KNOWN_BLOBS = {**ACCEPTED_BLOBS, **PENDING_AUTHOR_DECISION}


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
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        pytest.skip(f"git history not available here: {exc}")


def test_no_new_reserved_blob_in_history(payload_blobs: dict[str, str]) -> None:
    """Nothing carries a reserved payload except the blobs already on record.

    This is the repeat guard: the decision of 2026-09-02 was to accept what is
    already in the public history, NOT to accept the class. A payload committed
    from now on lands here as a red test on the day it lands, while a `git rm`
    later would not undo it.
    """
    unexpected = {sha: path for sha, path in payload_blobs.items() if sha not in KNOWN_BLOBS}
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
    for sha, path in sorted(KNOWN_BLOBS.items()):
        assert sha in payload_blobs, f"recorded blob {sha[:12]} ({path}) is no longer in history — drop the entry"
        assert payload_blobs[sha] == path, f"recorded blob {sha[:12]} now lives at {payload_blobs[sha]}, not {path}"
