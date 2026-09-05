"""Unit tests for the shared fixture-root identity (tools/wordbench/roots.py).

The fixture roots are gitignored, so nothing in the repo records that one was
re-exported — the audit of 2026-09-02 found a headline pair (0.106400 /
0.146580) whose base nobody could reconstruct. ``root_digest`` makes the base
a citable number, ``--expect-root`` makes the expected base a precondition,
and the manifest's ``page_sha256`` finally gets re-checked by the MEASURING
run instead of only by the rebuild.

``page_hash_problems`` is tested here too although it still lives in
``tools/wordbench/run.py``: it is the other half of the same "which base did
this run measure" sensor, and only the word bench has the specimen pages to
re-check.

Pure: temporary directories, no fixtures, no DB, no network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pytest

from tools.wordbench.roots import add_expect_root_argument, announce_roots, check_expected_roots, root_digest
from tools.wordbench.run import build_parser, page_hash_problems


def _write(root: Path, files: dict[str, bytes]) -> Path:
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


FILES = {
    "manifest.json": b'{"set": "words"}',
    "templates.json": b'{"a": 1}',
    "unter/word.json": b'{"rect": [1, 2, 3, 4]}',
    "unter/crop.png": b"\x89PNG not really",
}


def test_the_digest_is_independent_of_creation_and_walk_order(tmp_path: Path):
    a = _write(tmp_path / "a", FILES)
    b = _write(tmp_path / "b", dict(reversed(list(FILES.items()))))

    assert root_digest(a) == root_digest(b)
    # …and stable across repeated calls (no time, no mtime, no randomness).
    assert root_digest(a) == root_digest(a)


def test_one_flipped_byte_changes_the_digest(tmp_path: Path):
    root = _write(tmp_path / "r", FILES)
    before = root_digest(root)

    (root / "unter" / "word.json").write_bytes(b'{"rect": [1, 2, 3, 5]}')

    assert root_digest(root) != before


def test_a_renamed_or_added_file_changes_the_digest(tmp_path: Path):
    root = _write(tmp_path / "r", FILES)
    before = root_digest(root)

    # Same bytes, different path — the path list is hashed too.
    (root / "unter" / "word.json").rename(root / "unter" / "word2.json")
    renamed = root_digest(root)
    assert renamed != before

    (root / "unter" / "word.json").write_bytes(FILES["unter/word.json"])
    assert root_digest(root) not in (before, renamed)


def test_touching_a_file_without_changing_its_bytes_keeps_the_digest(tmp_path: Path):
    # Metadata is deliberately not hashed: copying a root between checkouts
    # (which every bench session does) must not move its identity.
    root = _write(tmp_path / "r", FILES)
    before = root_digest(root)

    (root / "templates.json").touch()
    (root / "templates.json").chmod(0o600)

    assert root_digest(root) == before


def test_the_digest_is_a_full_sha256_hex_string(tmp_path: Path):
    digest = root_digest(_write(tmp_path / "r", FILES))

    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")


def test_a_matching_prefix_passes_and_a_mismatch_aborts_the_run():
    digests = {"words": "abc123" + "0" * 58, "pairs": "def456" + "0" * 58}

    check_expected_roots("abc123,def456", digests)  # exact prefixes
    check_expected_roots("abc,def", digests)  # shorter prefixes are fine
    check_expected_roots("ABC,DEF", digests)  # case-insensitive

    with pytest.raises(SystemExit) as excinfo:
        check_expected_roots("abc123", digests)
    # The message must name what went wrong AND the actual digests, so the
    # fix (re-export, or cite the other base) is one copy-paste away.
    assert "unmatched roots: pairs" in str(excinfo.value)
    assert "def456" in str(excinfo.value)


def test_a_prefix_that_matches_no_root_aborts_too():
    # A stale or mistyped expectation must not slip through just because the
    # other half of the list happened to match.
    with pytest.raises(SystemExit) as excinfo:
        check_expected_roots("abc,cafe", {"words": "abc123" + "0" * 58})

    assert "unmatched prefixes: cafe" in str(excinfo.value)


def test_an_empty_expectation_aborts():
    with pytest.raises(SystemExit):
        check_expected_roots(" , ", {"words": "abc" + "0" * 61})


def test_the_flag_is_wired_and_off_by_default():
    assert build_parser().parse_args([]).expect_root is None
    assert build_parser().parse_args(["--expect-root", "219182"]).expect_root == "219182"


def test_the_flag_helper_produces_the_same_dest_on_any_parser():
    parser = argparse.ArgumentParser()
    add_expect_root_argument(parser)

    assert parser.parse_args([]).expect_root is None
    assert parser.parse_args(["--expect-root", "abc,def"]).expect_root == "abc,def"


def test_announce_prints_the_two_header_lines_and_returns_the_full_digest(tmp_path, capsys):
    root = _write(tmp_path / "suetterlin-1922", FILES)
    (root / "manifest.json").write_bytes(b'{"set": "words", "exported_at": "2026-09-02T08:00:29+00:00"}')

    meta = announce_roots([root])

    out = capsys.readouterr().out.splitlines()
    assert out == ["root: suetterlin-1922 exported_at=2026-09-02T08:00:29+00:00", f"digest={meta[0]['digest'][:12]}"]
    assert meta == [
        {
            "name": "suetterlin-1922",
            "set": "words",
            "exported_at": "2026-09-02T08:00:29+00:00",
            "digest": root_digest(root),
        }
    ]


def test_announce_degrades_to_unknown_rather_than_dying_on_a_patched_root(tmp_path, capsys):
    # A Laufform candidate card (§14 LF3b-W) can be assembled without a
    # manifest; its digest is still the thing worth printing.
    root = _write(tmp_path / "card", {"templates.json": b"{}"})

    meta = announce_roots([root])

    assert meta[0]["exported_at"] == "unknown"
    assert "root: card exported_at=unknown" in capsys.readouterr().out


def test_announce_states_the_base_before_it_aborts_on_a_mismatch(tmp_path, capsys):
    root = _write(tmp_path / "suetterlin-1922", FILES)

    with pytest.raises(SystemExit) as excinfo:
        announce_roots([root], "cafe00")

    # The header comes first: the digest a re-run needs is on screen even
    # though the run died.
    assert f"digest={root_digest(root)[:12]}" in capsys.readouterr().out
    assert "unmatched prefixes: cafe00" in str(excinfo.value)
    assert root_digest(root) in str(excinfo.value)


def _manifest_with_page(tmp_path: Path, data: bytes, recorded: bytes | None = None) -> tuple[dict, Path]:
    page = tmp_path / "data" / "sources" / "suetterlin-1922" / "words-abb19.png"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_bytes(data)
    manifest = {
        "source_id": "suetterlin-1922",
        "page_sha256": {"words-abb19.png": hashlib.sha256(recorded if recorded is not None else data).hexdigest()},
    }
    return manifest, tmp_path


def test_matching_specimen_pages_report_no_problem(tmp_path: Path):
    manifest, repo_root = _manifest_with_page(tmp_path, b"plate bytes")

    assert page_hash_problems(manifest, repo_root) == []


def test_a_changed_specimen_page_is_reported(tmp_path: Path):
    manifest, repo_root = _manifest_with_page(tmp_path, b"plate bytes", recorded=b"the plate it was frozen from")

    problems = page_hash_problems(manifest, repo_root)

    assert len(problems) == 1
    assert problems[0].startswith("words-abb19.png: manifest ")


def test_a_missing_specimen_page_is_reported(tmp_path: Path):
    manifest, repo_root = _manifest_with_page(tmp_path, b"plate bytes")
    (repo_root / "data" / "sources" / "suetterlin-1922" / "words-abb19.png").unlink()

    assert "missing at" in page_hash_problems(manifest, repo_root)[0]


def test_an_older_manifest_without_page_hashes_keeps_running(tmp_path: Path):
    assert page_hash_problems({"source_id": "suetterlin-1922"}, tmp_path) == []
    assert page_hash_problems(json.loads('{"source_id": "x", "page_sha256": {}}'), tmp_path) == []
