"""No NEW reserved-dataset blob may enter the public git history.

Publishing exposes every blob ever committed, not just HEAD, and this
repository has been public since 2026-05-19. The learned dataset — authored
ductus templates, Laufformen, occurrence statistics — is reserved outside the
MIT grant (README "License", `docs/reference/quellen-und-rechte.md` §5), so a
rendered template dump committed anywhere outside the code trees is a leak
that a later `git rm` does not undo.

History already holds 13 such blobs, pinned by content hash in
`ACCEPTED_BLOBS` below. The author decided to accept rather than purge them:
the design-sync preview dump on 2026-09-02, and every revision of the three
pre-DB prototype canonicals this net then surfaced, on 2026-09-03, on the
same reasoning.

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

# Reserved identifier → the fewest numbers that key can legitimately carry.
#
# The list was walked against `api/schemas.py` field by field so that every
# reserved wire shape is represented, not just the ones a review happened to
# name:
#
#   templates + renders  `skeleton_polyline`, `anchors`, `half_widths`,
#                        `centerlines`, `outline_paths`, `outline_polygon`,
#                        `silhouette_px`, `fitted_outline_px`
#   glyph occurrences    `anchors`, `half_widths`      (InstanceItem/Out)
#   word occurrences     `strokes`                     (WordInstanceItem/Out)
#   pair overrides       `connector`                   (PairGeometry, and via
#                        it PairInstanceItem.geometry)
#   aggregates           `cluster_center`, `laufform_anchors` (AggregateOut),
#                        `connector`/`offset_center`   (PairAggregateOut)
#   bbox authoring       `points` (MaskStroke), `slant_xs` (GuideConfig)
#
# Short forms are deliberate and do the subsuming: `anchors` covers
# `pixel_anchors`, `anchors_template` and `laufform_anchors`; `half_widths`
# covers `half_widths_px`/`_template`; `outline_polygon` covers
# `outline_polygons`; `connector` covers `connector_center`.
#
# The floor is PER KEY because the schemas differ: `InstanceItem.anchors` has
# min_length 4, i.e. eight coordinates, while `PairGeometry.connector` is
# schema-valid as a two-point join and `WordInstanceItem.strokes` as a single
# two-point stroke — four numbers each. One global floor would either miss the
# small shapes or invite false positives on the large ones. Measured over the
# whole history these floors produce no false positive: they flag exactly the
# recorded blobs and nothing else.
PAYLOAD_KEYS: dict[bytes, int] = {
    b"skeleton_polyline": 8,
    b"anchors": 8,
    b"half_widths": 6,
    b"centerlines": 8,
    b"outline_paths": 8,
    b"outline_polygon": 8,
    b"silhouette_px": 8,
    b"fitted_outline_px": 8,
    b"strokes": 4,
    b"connector": 4,
    b"offset_center": 4,
    b"cluster_center": 4,
    b"points": 6,
    b"slant_xs": 4,
}


# A key alone is not a leak: CHANGELOG.md, CLAUDE.md and the generator scripts
# all NAME these fields, and prose about the format is explicitly allowed. What
# distinguishes a dump is that the numbers travel WITH the key — so the run is
# looked for right after each key, not anywhere in the blob.
#
# Key-local and short rather than global and long: between two items sit JSON
# keys that break any longer run, so a global 40-number floor passed small
# occurrence dumps while claiming to cover them. The separator tolerates
# brackets because dense geometry is as often nested (`[[x, y], …]`) as flat,
# and a comma-only run breaks at `],[`.
def _run_of(count: int) -> re.Pattern[bytes]:
    return re.compile(rb"(?:-?\d+(?:\.\d+)?[\s,\[\]]+){%d,}" % count)


_RUNS = {key: _run_of(count) for key, count in PAYLOAD_KEYS.items()}
_KEY_WINDOW = 300

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
    # measured they run to tens of KB and carry 50 anchors plus half widths,
    # the same class of authored geometry as the blob above. This net is what
    # corrected that, which is why they are listed rather than dismissed.
    # Four revisions of each of the three files: the decision names the files,
    # and every version of them is the same authored geometry. The key-local
    # detector below sees revisions the earlier coarse one missed.
    "0625420282bb2bf4ff6d4b9ce1a7a37e896667e2": "mvp/canonical/e-medial_v0.json",
    "32577587ee768f37588e264848299238358b8829": "mvp/canonical/e-medial_v0.json",
    "5592aa6840ed79a34804e5c6c910b4a2751bcff1": "mvp/canonical/e-medial_v0.json",
    "8f027feb34d73976243e8594b264b2ffa2141cc4": "mvp/canonical/e-medial_v0.json",
    "2064f13f3c508ee129e1387a5ad113a328a7fb8c": "mvp/canonical/s-final_v0.json",
    "56e9069a92b764407eafb951597c6d2051c3efc6": "mvp/canonical/s-final_v0.json",
    "c9ffc7a207a1d9ed89712dc0d5fa279964e5d5b3": "mvp/canonical/s-final_v0.json",
    "e63a328c738f61b9ad250529cbf93b3ff2fe81e3": "mvp/canonical/s-final_v0.json",
    "43ca615760b026555fb4e7f2d9a85e8c453263c7": "mvp/canonical/s-medial_v0.json",
    "700eab8caeffd0c6214f28b05cf1e6329c3c35f1": "mvp/canonical/s-medial_v0.json",
    "bfd13c3c568dfdb8a44e04df1e13e43c82a3eaf6": "mvp/canonical/s-medial_v0.json",
    "c1db86ec15a47922710179d6c0746d12bda1a873": "mvp/canonical/s-medial_v0.json",
}


def carries_payload(body: bytes) -> bool:
    """True when a reserved key is followed by coordinates rather than prose."""
    for key, run in _RUNS.items():
        start = 0
        while (found_at := body.find(key, start)) != -1:
            if run.search(body[found_at : found_at + _KEY_WINDOW]):
                return True
            start = found_at + 1
    return False


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
        if carries_payload(body):
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
        # The SMALLEST reserved occurrence: `InstanceItem.anchors` allows four
        # points, so eight coordinates, and the next item's JSON keys break the
        # run. A global 40-number floor let this through while claiming to
        # cover occurrences; key-local detection catches it.
        ("minimal occurrence", b'{"anchors": [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]], "glyph": "e"}', True),
        # The SMALLEST schema-valid word occurrence: WordInstanceItem.strokes
        # allows a single two-point stroke, so four numbers. An eight-number
        # floor would have let this through.
        ("minimal strokes", b'{"strokes": [[[1.0, 2.0], [3.0, 4.0]]], "word": "das"}', True),
        # Render geometry from the fit path, which the key list missed at first.
        ("fitted outline", b'"fitted_outline_px": [' + b", ".join(b"[1.0, 2.0]" for _ in range(6)) + b"]", True),
        # The SMALLEST reserved pair override: PairGeometry needs only an
        # offset and a two-point connector — four numbers in the connector.
        ("minimal pair override", b'{"offset": [0.5, 0.0], "connector": [[0.0, 0.0], [0.4, 0.1]]}', True),
        # Numbers far from the key are not the key's payload.
        ("key far from numbers", b'"half_widths" is a field.' + b"x" * 400 + b"1, 2, 3, 4, 5, 6, 7, 8, 9,", False),
    ],
)
def test_detector_matches_payload_shapes_not_mentions(shape: str, body: bytes, expected: bool) -> None:
    """The detector needs a payload key AND numbers travelling with it."""
    assert carries_payload(body) is expected, f"{shape}: expected detected={expected}"


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
