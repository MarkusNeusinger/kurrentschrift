"""The identity of a fixture root, shared by every bench that measures on one.

The frozen roots under ``tools/wordbench/fixtures`` are gitignored, so a
re-export leaves no diff and a quoted headline used to have no way of naming
the base it belonged to — the audit of 2026-09-02 found a pair of numbers
nobody could reconstruct. #478 gave the word bench the sensor; this module is
that sensor lifted out of ``tools/wordbench/run.py`` so the trace tools
(``tools/tracebench``, ``tools/pairlab``) run the SAME code rather than a
second implementation that could drift from it.

Three pieces, in the order a run uses them:

* :func:`root_digest` — the citable fingerprint of one root;
* :func:`add_expect_root_argument` — the ``--expect-root`` flag, worded once;
* :func:`announce_roots` — the two header lines per root, then the abort.

Pure: filesystem reads and prints, no DB, no network, and it never touches a
measured number.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable


MANIFEST_FILE = "manifest.json"

EXPECT_ROOT_HELP = (
    "comma-separated digest prefixes (see root_digest) the selected fixture roots MUST start "
    "with; the run aborts BEFORE measuring on any mismatch, so it can never silently score a "
    "different base than the one a result is quoted against"
)


def root_digest(root: Path) -> str:
    """The identity of a fixture root: SHA-256 over its complete file listing.

    The digest is taken over the SORTED list of ``(relative POSIX path, size in
    bytes, SHA-256 of the bytes)`` of every regular file under ``root``: one
    ``"<relpath>\\0<size>\\0<sha256>\\n"`` record per file, sorted by the
    relative path, concatenated into a single SHA-256. Properties that make it
    usable as a citable base identity:

    * deterministic — the sort is the only ordering, so the filesystem's walk
      order, the machine and the export's own dict order cannot move it;
    * blind to metadata — mtimes, ownership and permissions are not hashed, so
      copying a root between checkouts (which the benches do) keeps it stable;
    * sensitive to one flipped byte anywhere, including a file merely ADDED or
      REMOVED, because the path list itself is hashed.

    Its purpose: a headline is only comparable to another headline measured on
    the same base. The roots are gitignored, so nothing in the repo records a
    re-export — quoting ``exported_at`` plus the first 12 hex of this digest
    next to a number makes an undeclared re-baseline visible at once instead of
    at the next audit.
    """
    outer = hashlib.sha256()
    files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
    for path in files:
        inner = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                inner.update(chunk)
        rel = path.relative_to(root).as_posix()
        outer.update(f"{rel}\0{path.stat().st_size}\0{inner.hexdigest()}\n".encode())
    return outer.hexdigest()


def check_expected_roots(expect: str, digests: dict[str, str]) -> None:
    """Abort unless every selected root — and every stated prefix — is accounted for.

    ``expect`` is a comma-separated list of digest prefixes (a run over two
    sets selects two roots and therefore needs two). BOTH directions are
    required: an unmatched root would let the run measure a base nobody asked
    for, and an unmatched prefix is a stale or mistyped expectation that must
    not pass silently just because the other half happened to match.
    """
    prefixes = [p.strip().lower() for p in expect.split(",") if p.strip()]
    if not prefixes:
        raise SystemExit("--expect-root: no digest prefix given")
    unmatched_roots = [n for n, d in sorted(digests.items()) if not any(d.startswith(p) for p in prefixes)]
    unmatched_prefixes = [p for p in prefixes if not any(d.startswith(p) for d in digests.values())]
    if unmatched_roots or unmatched_prefixes:
        actual = "\n  ".join(f"{n} digest={d}" for n, d in sorted(digests.items()))
        raise SystemExit(
            "--expect-root does not match the fixture roots this run would measure"
            + (f"\n  unmatched roots: {', '.join(unmatched_roots)}" if unmatched_roots else "")
            + (f"\n  unmatched prefixes: {', '.join(unmatched_prefixes)}" if unmatched_prefixes else "")
            + f"\n  {actual}"
        )


def add_expect_root_argument(parser: argparse.ArgumentParser) -> None:
    """Wire ``--expect-root`` onto a bench CLI, worded the same everywhere."""
    parser.add_argument("--expect-root", help=EXPECT_ROOT_HELP)


def _manifest_of(root: Path) -> dict:
    """A root's manifest, or ``{}`` — the sensor must never break a run itself.

    A patched candidate root (a Laufform card, §14 LF3b-W) can be assembled
    without a manifest; its digest is still the thing worth printing, so a
    missing or unreadable file degrades to ``exported_at=unknown`` rather than
    to a traceback.
    """
    try:
        manifest = json.loads((root / MANIFEST_FILE).read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return manifest if isinstance(manifest, dict) else {}


def announce_roots(roots: Iterable[Path], expect: str | None = None) -> list[dict[str, str]]:
    """State WHICH BASE this run measures, then make it a precondition.

    Prints the two header lines per root — ``root: <name> exported_at=…`` and
    ``digest=<12 hex>`` — and only afterwards enforces ``--expect-root``, so a
    mismatch report is preceded by the actual digests a re-run would need.
    Returns the per-root metadata (with the FULL digest) for a ``--json``
    report: a stored report must be enough to re-check its own base.

    Call it before the first measurement, never after — the whole point is that
    a run cannot produce a number against fixtures it was not asked for.
    """
    meta: list[dict[str, str]] = []
    for root in roots:
        manifest = _manifest_of(root)
        entry = {
            "name": root.name,
            "set": str(manifest.get("set", "words")),
            "exported_at": str(manifest.get("exported_at") or "unknown"),
            "digest": root_digest(root),
        }
        meta.append(entry)
        print(f"root: {entry['name']} exported_at={entry['exported_at']}")
        print(f"digest={entry['digest'][:12]}")
    if expect:
        check_expected_roots(expect, {m["name"]: m["digest"] for m in meta})
    return meta
