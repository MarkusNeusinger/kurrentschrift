"""The chronik: one create-only directory per optimisation round, kept forever.

A duel page (`tools/tracebench/view.py`) is worth an afternoon while it is on
screen and worth nothing a week later, because the next round overwrites
`temp/duell.html`. What the owner asked for on 2026-08-14 is the opposite: the
comparisons of every round PERSIST, so progress stays visible — and so the good
ones can later seed a public method explainer instead of being reconstructed
from memory.

So this is an archive, not a cache, and it borrows the whole discipline of
`tools/dbsnapshot` rather than inventing a second one:

* **Create-only.** Every round is a new timestamped directory. An existing one
  is never opened for writing, never overwritten, never renamed, never removed.
  There is no delete path — not as a flag, not as a cleanup step.
* **Nothing empty gets filed.** Every named artifact must exist and carry bytes
  BEFORE the directory is created; a silent empty snapshot is worse than none,
  because in a listing it looks exactly like a full one.
* **Outside the working tree.** The pages carry traced geometry — learned
  dataset, reserved outside the MIT grant (`quellen-und-rechte.md` §5) — and
  `git clean -xfd` deletes gitignored files, so an archive under `temp/` is not
  an archive. The repository carries the TOOL; its output lives elsewhere.

Root resolution mirrors `tools.dbsnapshot.fetch`, which takes its archive from
`--archive` / `KURRENTSCHRIFT_ARCHIVE` and has no built-in path: here it is
`--root` / `KS_CHRONIK_ROOT`, and when only the db archive is configured, the
chronik sits BESIDE that clone as `tracebench-chronik`. With neither, the run
refuses and says so — it does not quietly pick a directory the next `git clean`
would take away.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]

# `--root`'s environment twin, and the db archive whose sibling the chronik is
# when only that one is configured (`tools.dbsnapshot.fetch`'s convention).
ENV_ROOT = "KS_CHRONIK_ROOT"
ENV_DB_ARCHIVE = "KURRENTSCHRIFT_ARCHIVE"
CHRONIK_DIRNAME = "tracebench-chronik"

INDEX_FILE = "INDEX.md"
INDEX_HEADER = (
    "# tracebench-Chronik\n\n"
    "Eine Zeile je Runde: Zeitstempel · Label · abgelegte Dateien · Notiz.\n"
    "Anlegen frei, löschen nie (`tools/tracebench/chronik.py`).\n\n"
)

# The stamp format of `tools.dbsnapshot.fetch` — sortable, path-safe, UTC.
STAMP_FORMAT = "%Y-%m-%dT%H-%M-%SZ"
# A label becomes a directory name, so it is reduced to characters that mean the
# same thing on every filesystem. Replaced, never dropped silently.
LABEL_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def utc_stamp() -> str:
    """The snapshot stamp — the only clock reading in this package."""
    return datetime.now(UTC).strftime(STAMP_FORMAT)


def slug(label: str) -> str:
    """A directory-safe label. Raises `SystemExit` when nothing usable is left."""
    cleaned = LABEL_SAFE.sub("-", (label or "").strip()).strip("-")
    if not cleaned:
        raise SystemExit(f"--label {label!r} has no usable characters — name the round (e.g. arm1-prox01)")
    return cleaned


def resolve_root(explicit: str | None) -> Path:
    """Where the chronik lives — see the module docstring for the order."""
    if explicit:
        root = Path(explicit)
    elif os.environ.get(ENV_ROOT):
        root = Path(os.environ[ENV_ROOT])
    elif os.environ.get(ENV_DB_ARCHIVE):
        # Beside the database archive clone, not inside it: the chronik is a
        # different kind of thing (rendered comparisons, not table rows) and
        # must not ride along in that repository's commits.
        root = Path(os.environ[ENV_DB_ARCHIVE]).expanduser().resolve().parent / CHRONIK_DIRNAME
    else:
        raise SystemExit(
            f"no chronik root — pass --root, or set {ENV_ROOT} (or {ENV_DB_ARCHIVE}, whose parent then holds "
            f"a {CHRONIK_DIRNAME}/ sibling). It must lie OUTSIDE the working tree: `git clean -xfd` removes "
            "everything gitignored, so a round archived under temp/ is not archived."
        )
    root = root.expanduser().resolve()
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise SystemExit(
            f"{root} is inside the working tree {REPO_ROOT} — the chronik holds traced geometry (open-core "
            "reservation) and must survive `git clean -xfd`; choose a directory outside the repository"
        )
    if root.exists() and not root.is_dir():
        raise SystemExit(f"{root} exists and is not a directory — the chronik root must be a directory")
    return root


def check_sources(files: Sequence[str | Path]) -> list[Path]:
    """The artifacts to file, verified BEFORE anything is created.

    Everything that can make a snapshot worthless is checked here: an empty
    list, a path that does not exist, a directory, a file with no bytes, and two
    sources that would land on the same name inside the round's directory.
    """
    if not files:
        raise SystemExit("--files is empty — a round with no artifact is not a round")
    resolved: list[Path] = []
    names: dict[str, Path] = {}
    for raw in files:
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"{path} does not exist — nothing filed")
        if not path.is_file():
            raise SystemExit(f"{path} is not a file — the chronik files artifacts, not directories")
        if path.stat().st_size == 0:
            raise SystemExit(f"{path} is empty — an empty artifact looks like safety and is not, nothing filed")
        if path.name in names and names[path.name] != path:
            raise SystemExit(f"two sources are both called {path.name!r} ({names[path.name]} and {path})")
        names[path.name] = path
        resolved.append(path)
    return resolved


def index_line(stamp: str, label: str, names: Sequence[str], note: str | None) -> str:
    """The one INDEX line a round contributes."""
    line = f"- `{stamp}-{label}` · {', '.join(names)}"
    if note:
        note_text = " ".join(note.split())
        line += f" · {note_text}"
    return line + "\n"


def append_index(root: Path, line: str) -> Path:
    """Append one line to the chronik index, creating it with its header once."""
    path = root / INDEX_FILE
    if not path.exists():
        path.write_text(INDEX_HEADER + line, encoding="utf-8")
    else:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
    return path


def snapshot(
    root: Path, label: str, files: Sequence[str | Path], *, note: str | None = None, stamp: str | None = None
) -> Path:
    """File one round. Returns the created directory; never touches an existing one."""
    name = slug(label)
    sources = check_sources(files)
    taken_at = stamp or utc_stamp()
    target = root / f"{taken_at}-{name}"
    if target.exists():
        raise SystemExit(f"{target} already exists — the chronik is create-only, a round is never rewritten")
    target.mkdir(parents=True)
    for source in sources:
        shutil.copy2(source, target / source.name)
    append_index(root, index_line(taken_at, name, [s.name for s in sources], note))
    return target


def read_index(root: Path) -> str:
    """The index as text, or an empty string when this chronik holds no round yet."""
    path = root / INDEX_FILE
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.tracebench.chronik", description=__doc__.splitlines()[0])
    parser.add_argument("--root", help=f"chronik root (default: ${ENV_ROOT}, else the {CHRONIK_DIRNAME}/ sibling)")
    sub = parser.add_subparsers(dest="command", required=True)

    take = sub.add_parser("snapshot", help="file one round's artifacts (create-only)")
    take.add_argument("--label", required=True, help="the round's name, e.g. arm1-prox01")
    take.add_argument("--files", nargs="+", required=True, help="the artifacts to file")
    take.add_argument("--note", help="one line for the index")

    sub.add_parser("list", help="print the chronik index")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = resolve_root(args.root)
    if args.command == "list":
        text = read_index(root)
        print(text.rstrip("\n") if text else f"no rounds filed in {root} yet")
        return 0
    target = snapshot(root, args.label, args.files, note=args.note)
    print(f"filed {len(args.files)} artifact(s) in {target}")
    print(f"index  {root / INDEX_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
