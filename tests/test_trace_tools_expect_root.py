"""Every trace tool states its fixture root, and `--expect-root` really aborts.

#478 gave the WORD bench the base sensor (`root: … exported_at=…` /
`digest=…`, plus `--expect-root`); the trace tools kept measuring silently
against whatever root sat on disk — and they are the ones a §14 entry quotes,
so a number from `tracebench`, `k0eval` or `pairlab.follow` could name no base
at all. This module pins the sensor on each entry point that reads a fixture
root, in the one way that matters: the check happens BEFORE the first
measurement, and a mismatch exits non-zero naming both digests.

The pattern per tool: a temporary root with two files, the root resolver
patched to return it, and the first measuring call patched to raise
``_Measured``. A matching prefix therefore surfaces as ``_Measured`` (the run
went on), a mismatched one as ``SystemExit`` with ``_Measured`` never raised
(the run died at the gate).

Pure: temporary directories, no fixtures, no DB, no network, no solve.
"""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from tools.wordbench.roots import root_digest


class _Measured(Exception):
    """Raised by the patched measuring call — 'the run got past the gate'."""


@dataclass(frozen=True)
class ToolCase:
    """One CLI: where it resolves its root, and what it does first afterwards."""

    module: str
    root_resolver: str  # the attribute that returns the fixture root
    first_measurement: str  # the attribute called right AFTER the announcement
    argv: tuple[str, ...]  # arguments the parser requires, expect-root aside


# Every entry point of tools/tracebench and tools/pairlab that reads a fixture
# root. `tools.wordbench.run` has its own suite (tests/test_wordbench_roots.py).
TOOLS = (
    ToolCase("tools.tracebench.run", "find_fixture_root", "load_reference", ()),
    ToolCase("tools.tracebench.k0eval", "find_fixture_root", "load_reference", ("base-cand.json",)),
    ToolCase("tools.tracebench.view", "find_fixture_root", "load_reference", ()),
    ToolCase("tools.tracebench.excursions", "find_fixture_root", "load_reference", ("cand.json",)),
    ToolCase("tools.pairlab.follow", "_root_for", "_load_cases", ("--all",)),
    ToolCase("tools.pairlab.spanmeas", "_root_for", "run_set", ()),
    ToolCase("tools.pairlab.chainbench", "_root_for", "plan_occurrences", ()),
    ToolCase("tools.pairlab.__main__", "_root_for", "find_occurrences", ("re",)),
)

FILES = {
    "manifest.json": b'{"set": "words", "exported_at": "2026-09-04T12:22:29+00:00"}',
    "templates.json": b'{"a": 1}',
}


@pytest.fixture
def root(tmp_path: Path) -> Path:
    root = tmp_path / "suetterlin-1922"
    for name, data in FILES.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(data)
    return root


def _prepared(case: ToolCase, root: Path, monkeypatch: pytest.MonkeyPatch, expect: str | None):
    """Import the tool, point it at `root`, and arm the measurement tripwire."""
    module = importlib.import_module(case.module)

    def _root(*_args, **_kwargs) -> Path:
        return root

    def _measure(*_args, **_kwargs):
        raise _Measured(case.module)

    monkeypatch.setattr(module, case.root_resolver, _root)
    monkeypatch.setattr(module, case.first_measurement, _measure)
    expect_argv = ["--expect-root", expect] if expect else []
    monkeypatch.setattr(sys, "argv", [case.module, *case.argv, *expect_argv])
    return module


@pytest.mark.parametrize("case", TOOLS, ids=lambda c: c.module)
def test_a_matching_digest_lets_the_run_proceed(case: ToolCase, root: Path, monkeypatch, capsys):
    module = _prepared(case, root, monkeypatch, root_digest(root)[:12])

    with pytest.raises(_Measured):
        module.main()

    out = capsys.readouterr().out
    assert "root: suetterlin-1922 exported_at=2026-09-04T12:22:29+00:00" in out
    assert f"digest={root_digest(root)[:12]}" in out


@pytest.mark.parametrize("case", TOOLS, ids=lambda c: c.module)
def test_a_mismatched_digest_aborts_before_the_first_measurement(case: ToolCase, root: Path, monkeypatch, capsys):
    module = _prepared(case, root, monkeypatch, "cafe00")

    # Not _Measured: the run must die at the gate, not after it.
    with pytest.raises(SystemExit) as excinfo:
        module.main()

    message = str(excinfo.value)
    assert "unmatched prefixes: cafe00" in message
    # Both digests — the expected one from the message, the actual one so the
    # fix (re-export, or quote the other base) is a copy-paste away.
    assert root_digest(root) in message
    assert f"digest={root_digest(root)[:12]}" in capsys.readouterr().out


@pytest.mark.parametrize("case", TOOLS, ids=lambda c: c.module)
def test_without_the_flag_the_run_only_states_its_base(case: ToolCase, root: Path, monkeypatch, capsys):
    module = _prepared(case, root, monkeypatch, None)

    with pytest.raises(_Measured):
        module.main()

    assert f"digest={root_digest(root)[:12]}" in capsys.readouterr().out
