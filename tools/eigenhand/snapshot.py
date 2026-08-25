"""Incremental, create-only copy of one hand's data into the private archive.

dbsnapshot discipline (tools/dbsnapshot/fetch.py is the pattern): the
archive is the private clone OUTSIDE the working tree that already holds the
DB snapshots — own-hand scans and the database's authored word traces end up
in the SAME reserved place. Safety properties, in the order they matter:

* **Create-only.** Every run writes a new timestamped directory under
  ``<archive>/own-hand/<hand>/``. Existing directories are never opened for
  writing, never overwritten, never removed — no delete path exists.
* **Incremental without duplicates — and without gaps.** A Fassung directory
  already present in ANY earlier snapshot is skipped (matched by its relative
  path, and verified against the Kartei's SHA256): a filed Fassung never
  changes. Bogen contents are compared FILE by file instead, because a sheet
  directory does grow — a second capture files another scan under ``scans/``.
  ``kartei.json``, the strip-plan copy and the standing setup ride along in
  full each time — they are small and make every snapshot self-describing.
  Note what this means for a READER: only the FIRST snapshot holds the whole
  hand; every later one holds its increment beside a complete Kartei. Anything
  restoring from the archive has to read the snapshots as one layered tree —
  ``tools/eigenhand/sync.py --from`` does.
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


def _units(root: Path) -> list[tuple[str, Path, bool]]:
    """The copy units under one tree: Fassung dirs, Bogen FILES. (rel, path, is_dir)

    A Fassung is immutable once filed — apply.py refuses to overwrite one — so
    the whole directory is a single unit, matched by relative path. A Bogen
    directory is NOT immutable: ``ingest --keep-scan`` files another scan under
    ``scans/`` every time the sheet is captured again. Skipping such a sheet by
    path alone would leave the later scan out of the archive while the run
    still printed success, so its files are units of their own.
    """
    units: list[tuple[str, Path, bool]] = []
    fassungen = root / "fassungen"
    if fassungen.is_dir():
        for strip in sorted(fassungen.iterdir()):
            for fassung in sorted(strip.iterdir()) if strip.is_dir() else ():
                # Only directories are copy units: a stray file (.DS_Store,
                # a scratch note) would break shutil.copytree at the worst
                # possible moment — mid-archive.
                if fassung.is_dir():
                    units.append((f"fassungen/{strip.name}/{fassung.name}", fassung, True))
    blaetter = root / "blaetter"
    if blaetter.is_dir():
        for sheet in sorted(blaetter.iterdir()):
            if not sheet.is_dir():
                continue
            for path in sorted(sheet.rglob("*")):
                relative = path.relative_to(sheet)
                # Crops and payload under import/ are regenerable from the scan
                # plus layout.json — the archive keeps what cannot be recomputed.
                if not path.is_file() or "import" in relative.parts:
                    continue
                units.append((f"blaetter/{sheet.name}/{relative.as_posix()}", path, False))
    return units


def _known_relpaths(hand_archive: Path) -> set[str]:
    """Copy units present in ANY earlier snapshot (relative paths)."""
    known: set[str] = set()
    if not hand_archive.is_dir():
        return known
    for snapshot in hand_archive.iterdir():
        if snapshot.is_dir():
            known.update(rel for rel, _path, _is_dir in _units(snapshot))
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

    kartei_file = hand_dir(args.hand) / "kartei.json"
    if not kartei_file.exists():
        # load_kartei would hand back an empty in-memory default — a snapshot
        # of nothing must not look like a backup (Copilot finding, PR #406).
        raise SystemExit(f"{kartei_file} missing — nothing recorded for this hand yet (run sheet/ingest/apply first)")
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
    shutil.copy2(kartei_file, target / "kartei.json")
    shutil.copy2(STREIFEN_JSON, target / "streifenplan.json")
    # The standing setup rides along in full like the Kartei: it is the fourth
    # own-hand table (`eigenhand_hands`), it is two lines of JSON, and without
    # it the restore recipe brings back sheets, verdicts and strips but not the
    # nib/ink/paper the whole campaign is calibrated on (found in review, PR
    # #410). `sync --from` pushes it when the server has none.
    setup_file = source / "setup.json"
    if setup_file.exists():
        shutil.copy2(setup_file, target / "setup.json")

    copied_fassungen = copied_files = 0
    for rel, path, is_dir in _units(source):
        if rel in known:
            continue
        if is_dir:
            shutil.copytree(path, target / rel)
            copied_fassungen += 1
        else:
            (target / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target / rel)
            copied_files += 1

    print(
        f"filed snapshot {target.relative_to(archive)}: {copied_fassungen} new Fassungen, "
        f"{copied_files} new Bogen files, {total_fassungen} Fassungen total"
    )
    if args.push:
        _git(archive, "add", "-A", str(target.relative_to(archive)))
        _git(archive, "commit", "-m", f"own-hand snapshot {args.hand} {stamp}")
        _git(archive, "push")
        print("archive committed and pushed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
