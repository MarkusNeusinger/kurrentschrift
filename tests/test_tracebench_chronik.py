"""Tests for the create-only round history (`tools.tracebench.chronik`).

An archive is judged by what it REFUSES: writing into a round that already
exists, filing a file that is not there, filing a file with no bytes, filing
nothing at all, and picking a directory the next `git clean -xfd` would take
away. Each of those has a test, because each of them fails silently in the
direction that looks like success.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.tracebench import chronik


STAMP = "2026-08-14T09-30-00Z"


def _artifact(tmp_path: Path, name: str, text: str = "x") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_snapshot_copies_the_files_and_appends_one_index_line(tmp_path: Path) -> None:
    root = tmp_path / "chronik"
    page = _artifact(tmp_path, "duell.html", "<!doctype html>")
    report = _artifact(tmp_path, "chain.json", "{}")

    target = chronik.snapshot(root, "arm1-prox01", [page, report], note="erste Runde", stamp=STAMP)

    assert target == root / f"{STAMP}-arm1-prox01"
    assert (target / "duell.html").read_text() == "<!doctype html>"
    assert (target / "chain.json").read_text() == "{}"
    index = chronik.read_index(root)
    assert index.startswith("# tracebench-Chronik")
    assert f"- `{STAMP}-arm1-prox01` · duell.html, chain.json · erste Runde\n" in index

    second = chronik.snapshot(root, "arm2 prox/02", [page], stamp="2026-08-15T09-30-00Z")
    assert second.name == "2026-08-15T09-30-00Z-arm2-prox-02"  # label slugged, never dropped
    assert len([line for line in chronik.read_index(root).splitlines() if line.startswith("- ")]) == 2
    # The first round is untouched by the second — create-only, never rewritten.
    assert (target / "duell.html").exists()


def test_an_existing_round_is_never_written_into(tmp_path: Path) -> None:
    root = tmp_path / "chronik"
    page = _artifact(tmp_path, "duell.html")
    chronik.snapshot(root, "runde", [page], stamp=STAMP)

    with pytest.raises(SystemExit, match="create-only"):
        chronik.snapshot(root, "runde", [page], stamp=STAMP)


@pytest.mark.parametrize(
    ("files", "message"), [([], "no artifact"), (["missing.html"], "does not exist"), (["empty.html"], "empty")]
)
def test_nothing_is_created_when_a_source_is_unusable(tmp_path: Path, files: list[str], message: str) -> None:
    root = tmp_path / "chronik"
    (tmp_path / "empty.html").write_text("")
    paths = [str(tmp_path / name) for name in files]

    with pytest.raises(SystemExit, match=message):
        chronik.snapshot(root, "runde", paths, stamp=STAMP)

    # The directory must not exist even as an empty shell: a silent empty
    # snapshot looks exactly like a full one in a listing.
    assert not (root / f"{STAMP}-runde").exists()


def test_a_directory_and_a_name_collision_are_refused(tmp_path: Path) -> None:
    root = tmp_path / "chronik"
    folder = tmp_path / "folder"
    folder.mkdir()
    with pytest.raises(SystemExit, match="not a file"):
        chronik.snapshot(root, "runde", [folder], stamp=STAMP)

    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first = _artifact(tmp_path / "a", "duell.html")
    second = _artifact(tmp_path / "b", "duell.html")
    with pytest.raises(SystemExit, match="both called"):
        chronik.snapshot(root, "runde", [first, second], stamp=STAMP)


def test_an_empty_label_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="name the round"):
        chronik.snapshot(tmp_path / "chronik", "///", [_artifact(tmp_path, "duell.html")], stamp=STAMP)


def test_root_resolution_mirrors_the_db_archive_convention(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(chronik.ENV_ROOT, raising=False)
    monkeypatch.delenv(chronik.ENV_DB_ARCHIVE, raising=False)
    with pytest.raises(SystemExit, match="no chronik root"):
        chronik.resolve_root(None)

    # Only the db archive configured: the chronik is its SIBLING, not inside it.
    archive = tmp_path / "kurrentschrift-archiv"
    archive.mkdir()
    monkeypatch.setenv(chronik.ENV_DB_ARCHIVE, str(archive))
    assert chronik.resolve_root(None) == tmp_path / chronik.CHRONIK_DIRNAME

    monkeypatch.setenv(chronik.ENV_ROOT, str(tmp_path / "own"))
    assert chronik.resolve_root(None) == tmp_path / "own"
    assert chronik.resolve_root(str(tmp_path / "explicit")) == tmp_path / "explicit"


def test_a_root_inside_the_working_tree_is_refused() -> None:
    with pytest.raises(SystemExit, match="inside the working tree"):
        chronik.resolve_root(str(chronik.REPO_ROOT / "temp" / "chronik"))


def test_cli_list_prints_the_index(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "chronik"
    assert chronik.main(["--root", str(root), "list"]) == 0
    assert "no rounds filed" in capsys.readouterr().out

    page = _artifact(tmp_path, "duell.html")
    assert chronik.main(["--root", str(root), "snapshot", "--label", "runde", "--files", str(page)]) == 0
    assert chronik.main(["--root", str(root), "list"]) == 0
    out = capsys.readouterr().out
    assert "duell.html" in out
    assert "tracebench-Chronik" in out


def test_the_stamp_is_utc_and_sortable() -> None:
    stamp = chronik.utc_stamp()
    assert stamp.endswith("Z")
    assert len(stamp) == len("2026-08-14T09-30-00Z")
    assert "/" not in stamp and ":" not in stamp
