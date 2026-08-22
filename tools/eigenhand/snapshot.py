"""Incremental, create-only copy of one hand's data into the private archive.

dbsnapshot discipline (tools/dbsnapshot/fetch.py is the pattern): the
archive is the private clone OUTSIDE the working tree that already holds the
DB snapshots — own-hand scans and the database's authored word traces end up
in the SAME reserved place. Safety properties, in the order they matter:

* **Create-only.** Every run writes a new timestamped directory under
  ``<archive>/own-hand/<hand>/``. Existing directories are never opened for
  writing, never overwritten, never removed — no delete path exists.
* **Incremental without duplicates.** A Fassung or Bogen directory already
  present in ANY earlier snapshot is skipped (matched by its relative path;
  Fassungen additionally verified by the Kartei's SHA256). ``kartei.json``
  and the strip-plan copy ride along in full each time — they are small and
  make every snapshot self-describing.
* **A shrinking snapshot is an error.** If the Kartei holds fewer Fassungen
  than the archive already knows, the run fails — a wrong ``EIGENHAND_DATA``
  or a half-restored working copy must not look like a successful backup.
* **Contents never reach stdout.** Counts and paths only.

    uv run python -m tools.eigenhand.snapshot --hand mn-suetterlin [--push]
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

from tools.eigenhand.kartei import load_kartei
from tools.eigenhand.store import STREIFEN_JSON, hand_dir


ARCHIVE_SUBDIR = "own-hand"


def _archive_root(cli_value: str | None) -> Path:
    value = cli_value or os.environ.get("KURRENTSCHRIFT_ARCHIVE")
    if not value:
        raise SystemExit("no archive: pass --archive or set KURRENTSCHRIFT_ARCHIVE (the private archive clone)")
    root = Path(value).expanduser()
    if not root.is_dir():
        raise SystemExit(f"archive root {root} is not a directory")
    return root


def _units(root: Path) -> list[tuple[str, Path]]:
    """The copy units under one tree: Fassung dirs (two levels) + Bogen dirs (one)."""
    units: list[tuple[str, Path]] = []
    fassungen = root / "fassungen"
    if fassungen.is_dir():
        for strip in sorted(fassungen.iterdir()):
            for fassung in sorted(strip.iterdir()) if strip.is_dir() else ():
                units.append((f"fassungen/{strip.name}/{fassung.name}", fassung))
    blaetter = root / "blaetter"
    if blaetter.is_dir():
        for sheet in sorted(blaetter.iterdir()):
            if sheet.is_dir():
                units.append((f"blaetter/{sheet.name}", sheet))
    return units


def _known_relpaths(hand_archive: Path) -> set[str]:
    """Copy units present in ANY earlier snapshot (relative paths)."""
    known: set[str] = set()
    if not hand_archive.is_dir():
        return known
    for snapshot in hand_archive.iterdir():
        if snapshot.is_dir():
            known.update(rel for rel, _ in _units(snapshot))
    return known


def _verify_checksums(hand: str, kartei: dict) -> int:
    count = 0
    for strip, record in kartei["strips"].items():
        for fassung in record.get("fassungen", []):
            if fassung.get("png_sha256") is None:
                continue  # rejected rows are Kartei records only — no files
            png = hand_dir(hand) / "fassungen" / strip / fassung["id"] / "streifen.png"
            if not png.exists():
                raise SystemExit(f"{png} missing — Kartei and files disagree; not snapshotting")
            digest = hashlib.sha256(png.read_bytes()).hexdigest()
            if digest != fassung["png_sha256"]:
                raise SystemExit(f"{png}: checksum mismatch against the Kartei — not snapshotting")
            count += 1
    return count


def _git(archive: Path, *args: str) -> None:
    done = subprocess.run(  # noqa: S603 — fixed argv, no shell
        ["git", *args], cwd=archive, capture_output=True, text=True, timeout=300, check=False
    )
    if done.returncode != 0:
        detail = (done.stderr or done.stdout).strip().splitlines()
        raise SystemExit(
            f"git {' '.join(args)} failed in {archive}: {detail[-1] if detail else 'no output'}\n"
            "The snapshot is filed in the archive working tree but NOT committed/pushed."
        )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    ap.add_argument("--hand", required=True)
    ap.add_argument("--archive", default=None, help="archive clone root (default: $KURRENTSCHRIFT_ARCHIVE)")
    ap.add_argument("--push", action="store_true", help="git add/commit/push the archive after filing")
    ap.add_argument("--stamp", default=None, help="snapshot directory name (default: UTC now; explicit for tests)")
    args = ap.parse_args(argv)

    kartei = load_kartei(args.hand)
    total_fassungen = _verify_checksums(args.hand, kartei)

    archive = _archive_root(args.archive)
    hand_archive = archive / ARCHIVE_SUBDIR / args.hand
    known = _known_relpaths(hand_archive)
    known_fassungen = sum(1 for rel in known if rel.startswith("fassungen/"))
    if total_fassungen < known_fassungen:
        raise SystemExit(
            f"shrinking snapshot: Kartei holds {total_fassungen} Fassungen, archive already knows "
            f"{known_fassungen} — wrong data root? Refusing."
        )

    stamp = args.stamp or datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d-%H%M")
    target = hand_archive / stamp
    if target.exists():
        raise SystemExit(f"{target} already exists — create-only, pick a new --stamp")
    target.mkdir(parents=True)

    source = hand_dir(args.hand)
    shutil.copy2(source / "kartei.json", target / "kartei.json")
    shutil.copy2(STREIFEN_JSON, target / "streifenplan.json")

    copied = 0
    for rel, path in _units(source):
        if rel in known:
            continue
        # Bogen import/ crops are regenerable from scan + layout — skip them.
        shutil.copytree(path, target / rel, ignore=shutil.ignore_patterns("import"))
        copied += 1

    noun = "directory" if copied == 1 else "directories"
    print(f"filed snapshot {target.relative_to(archive)}: {copied} new {noun}, {total_fassungen} Fassungen total")
    if args.push:
        _git(archive, "add", "-A", str(target.relative_to(archive)))
        _git(archive, "commit", "-m", f"own-hand snapshot {args.hand} {stamp}")
        _git(archive, "push")
        print("archive committed and pushed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
