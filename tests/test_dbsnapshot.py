"""Unit tests for the archive tool's pure parts.

The archiving itself needs a live API and a git remote and is exercised by a
restore drill, not here. What IS unit-testable is every rule that decides
whether a snapshot may be filed at all — and those are the rules whose silent
failure would be indistinguishable from a working backup.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.dbsnapshot.fetch import _git, _restore_inheritance, check_plausible


def test_a_failed_required_git_call_stops_the_run(tmp_path: Path) -> None:
    """A failed add/commit/push must never read as a filed snapshot.

    By the time these run, the snapshot has already been moved into the archive
    working tree. Swallowing the error would leave it there uncommitted while
    the tool reports it archived — the exact false sense of safety this tool
    exists to remove.
    """
    with pytest.raises(SystemExit) as raised:
        _git("add", "--", "nothing", cwd=tmp_path, required=True)
    assert "NOT committed" in str(raised.value)


def test_an_informational_git_call_stays_quiet(tmp_path: Path) -> None:
    """The manifest's commit id and the branch name may legitimately be absent."""
    assert _git("rev-parse", "--short", "HEAD", cwd=tmp_path) == ""


def test_a_resolved_default_is_archived_as_inherit() -> None:
    """`GET /sources` resolves the nullable overrides; the archive must not.

    Storing the resolved value would turn „inherits the style" into „overrides
    it with the default as it stood that day" — invisible in any render
    comparison, and noticed only much later when a style edit stops
    propagating.
    """
    styles = [{"id": "suetterlin", "default_style_ratio": [1.0, 1.0, 1.0], "default_slant_deg": 90.0}]
    sources = [
        {"id": "suetterlin-1922", "style_id": "suetterlin", "style_ratio": [1.0, 1.0, 1.0], "slant_deg": 90.0},
        {"id": "koch-1928", "style_id": "suetterlin", "style_ratio": [2.0, 3.0, 2.0], "slant_deg": 78.0},
    ]
    assert _restore_inheritance(sources, styles) == 2
    assert sources[0]["style_ratio"] is None and sources[0]["slant_deg"] is None
    # A genuine override survives untouched — the point is the null, not tidiness.
    assert sources[1]["style_ratio"] == [2.0, 3.0, 2.0]
    assert sources[1]["slant_deg"] == 78.0


def test_an_unknown_style_leaves_the_source_alone() -> None:
    """Without the style's defaults there is nothing to compare against."""
    sources = [{"id": "x", "style_id": "gone", "style_ratio": [1.0], "slant_deg": 90.0}]
    assert _restore_inheritance(sources, []) == 0
    assert sources[0]["style_ratio"] == [1.0]


def test_an_empty_primary_table_is_refused() -> None:
    """A snapshot without the hand-made tables is not a snapshot."""
    problems = check_plausible({"bboxes": 0, "templates": 5, "templates_with_raw_path": 5}, None)
    assert any("bboxes" in p for p in problems)


def test_templates_without_a_raw_path_look_unauthorised() -> None:
    """The stylus path is the whole point; its absence is the admin gate, not data."""
    problems = check_plausible({"bboxes": 7, "templates": 5, "templates_with_raw_path": 0}, None)
    assert any("raw_path" in p for p in problems)


def test_a_shrinking_snapshot_is_refused() -> None:
    """An archive that quietly shrinks looks exactly like a full one in a listing."""
    previous = {"counts": {"bboxes": 77, "templates": 106, "templates_with_raw_path": 86}}
    counts = {"bboxes": 77, "templates": 90, "templates_with_raw_path": 86}
    problems = check_plausible(counts, previous)
    assert any("shrinking" in p and "templates" in p for p in problems)


def test_a_growing_snapshot_passes() -> None:
    previous = {"counts": {"bboxes": 77, "templates": 106, "templates_with_raw_path": 86}}
    counts = {"bboxes": 78, "templates": 107, "templates_with_raw_path": 87}
    assert check_plausible(counts, previous) == []
