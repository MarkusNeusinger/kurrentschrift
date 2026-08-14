"""Tests for the harness itself (`tools.tracebench.run`).

The CLI carries three rules §14 pre-registered, and a rule a client is merely
asked to follow is not a rule — so each of them is tested here: the startup
assertion that the ruler still has all ten development words, the refusal of a
confirmation run below five words, and the identity gate whose failure has to
end the process rather than print a warning above a table of numbers.

The whole tree is built in `tmp_path` — ten tiny words with a two-stroke trace
each — so this runs in CI where the real fixture roots are gitignored.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tests.test_tracebench_reference import row, write_entry
from tools.tracebench.reference import load_reference
from tools.tracebench.run import (
    MIN_CONFIRM_WORDS,
    assert_dev_set_intact,
    find_fixture_root,
    main,
    score_all,
    select_split,
    write_csv,
)
from tools.tracebench.sets import TRACEBENCH_DEV_IDS


DEV = sorted(TRACEBENCH_DEV_IDS)
EXTRA = ["Dorf", "Hand", "Nacht", "Sonne", "Wald", "regieren"]  # the held-out reserve


def build_tree(tmp_path: Path, rows: list[dict], *, style: str = "suetterlin", which: str = "words") -> Path:
    """`<fixtures>/<style>/<source>/` with a manifest, entries and the artifact."""
    fixtures = tmp_path / "fixtures"
    root = fixtures / style / "suetterlin-1922"
    root.mkdir(parents=True, exist_ok=True)
    ids = [r["specimen_id"] for r in rows]
    for entry_id in ids:
        write_entry(root, entry_id, slots=["d", "i", "e"])
    (root / "manifest.json").write_text(
        json.dumps({"set": which, "source_id": "suetterlin-1922", "words": [{"id": i, "word": i} for i in ids]})
    )
    (root / "word_instances.json").write_text(json.dumps({"hand_id": "a-hand", "rows": rows}))
    return fixtures


def full_tree(tmp_path: Path, **kwargs) -> Path:
    return build_tree(tmp_path, [row(i) for i in DEV + EXTRA], **kwargs)


# ------------------------------------------------------------- the fixture root


def test_the_root_is_found_by_its_manifest_set_not_its_name(tmp_path: Path) -> None:
    fixtures = full_tree(tmp_path)
    assert find_fixture_root(fixtures, "suetterlin", "words").name == "suetterlin-1922"
    with pytest.raises(SystemExit, match="no 'pairs' fixtures"):
        find_fixture_root(fixtures, "suetterlin", "pairs")


# --------------------------------------------------------- the startup assertion


def test_a_complete_development_set_passes_the_startup_assertion(tmp_path: Path) -> None:
    assert_dev_set_intact(load_reference(find_fixture_root(full_tree(tmp_path), "suetterlin", "words")))


def test_a_missing_development_word_is_a_hard_error_that_names_it(tmp_path: Path) -> None:
    """§14: „das Lineal hat ein Wort verloren".

    Losing a word does not make the bench smaller, it silently changes which
    population the headline describes — so the run dies instead of reporting.
    """
    rows = [row(i) for i in DEV if i != "muß"]
    reference = load_reference(find_fixture_root(build_tree(tmp_path, rows), "suetterlin", "words"))
    with pytest.raises(SystemExit, match="muß"):
        assert_dev_set_intact(reference)


def test_a_frame_stale_development_word_says_so(tmp_path: Path) -> None:
    rows = [row(i) if i != "zwei" else row(i, frame_stale="xh_px 29 vs expected 30±0.51") for i in DEV]
    reference = load_reference(find_fixture_root(build_tree(tmp_path, rows), "suetterlin", "words"))
    with pytest.raises(SystemExit, match="zwei .frame_stale."):
        assert_dev_set_intact(reference)


def test_a_traced_development_word_does_not_count_as_a_reference(tmp_path: Path) -> None:
    """The reference is the HUMAN trace; a harvest row in its place would make
    the bench grade the candidate against a sibling of itself."""
    rows = [row(i) if i != "die" else row(i, "traced") for i in DEV]
    reference = load_reference(find_fixture_root(build_tree(tmp_path, rows), "suetterlin", "words"))
    with pytest.raises(SystemExit, match="die"):
        assert_dev_set_intact(reference)


# ------------------------------------------------------------------ the splits


def test_the_dev_split_is_exactly_the_frozen_ids(tmp_path: Path) -> None:
    reference = load_reference(find_fixture_root(full_tree(tmp_path), "suetterlin", "words"))
    ids, warnings = select_split(reference, "dev", None)
    assert set(ids) == set(DEV) and not warnings


def test_the_confirm_split_is_everything_else(tmp_path: Path) -> None:
    reference = load_reference(find_fixture_root(full_tree(tmp_path), "suetterlin", "words"))
    ids, warnings = select_split(reference, "confirm", None)
    assert set(ids) == set(EXTRA) and not set(ids) & TRACEBENCH_DEV_IDS
    assert not warnings


def test_a_confirmation_below_five_words_is_refused(tmp_path: Path) -> None:
    """„Eine Bestätigung auf N Wörtern ist Theater" — the API of the bench
    enforces it rather than trusting the operator to notice."""
    rows = [row(i) for i in DEV] + [row(i) for i in EXTRA[: MIN_CONFIRM_WORDS - 1]]
    reference = load_reference(find_fixture_root(build_tree(tmp_path, rows), "suetterlin", "words"))
    with pytest.raises(SystemExit, match="theatre"):
        select_split(reference, "confirm", None)


def test_the_all_split_warns_that_it_is_not_held_out(tmp_path: Path) -> None:
    reference = load_reference(find_fixture_root(full_tree(tmp_path), "suetterlin", "words"))
    ids, warnings = select_split(reference, "all", None)
    assert set(ids) == set(DEV) | set(EXTRA)
    assert any("held-out" in w for w in warnings)


def test_a_hand_picked_word_filter_says_it_is_not_pre_registered(tmp_path: Path) -> None:
    reference = load_reference(find_fixture_root(full_tree(tmp_path), "suetterlin", "words"))
    ids, warnings = select_split(reference, "dev", "die,mit")
    assert ids == ["die", "mit"] or set(ids) == {"die", "mit"}
    assert any("pre-registered" in w for w in warnings)


# ------------------------------------------------------------------ the scoring


def test_rows_come_back_in_the_requested_order(tmp_path: Path) -> None:
    from tools.tracebench.candidates import authored_provider  # noqa: PLC0415

    reference = load_reference(find_fixture_root(full_tree(tmp_path), "suetterlin", "words"))
    ids = ["mit", "die", "und"]
    rows = score_all(
        reference, authored_provider(reference, ids), ids, label="authored", split="dev", resample_step=0.05
    )
    assert [r["id"] for r in rows] == ids


def test_parallel_scoring_does_not_reorder_the_report(tmp_path: Path) -> None:
    """`--jobs` may change the runtime and nothing else — a bench whose row order
    depended on scheduling could not be diffed against yesterday's report."""
    from tools.tracebench.candidates import authored_provider  # noqa: PLC0415

    reference = load_reference(find_fixture_root(full_tree(tmp_path), "suetterlin", "words"))
    ids = ["und", "die", "mit", "will"]
    candidates = authored_provider(reference, ids)
    serial = score_all(reference, candidates, ids, label="a", split="dev", resample_step=0.05)
    parallel = score_all(reference, candidates, ids, label="a", split="dev", resample_step=0.05, jobs=2)
    assert [r["id"] for r in parallel] == ids
    assert [r["dtw_xh"] for r in parallel] == [r["dtw_xh"] for r in serial]


def test_a_word_without_a_candidate_is_a_skipped_row(tmp_path: Path) -> None:
    reference = load_reference(find_fixture_root(full_tree(tmp_path), "suetterlin", "words"))
    rows = score_all(reference, {}, ["die"], label="x", split="dev", resample_step=0.05)
    assert rows[0]["status"] == "skipped" and rows[0]["dtw_xh"] is None


def test_the_csv_carries_every_column_any_row_had(tmp_path: Path) -> None:
    path = tmp_path / "out" / "rows.csv"
    write_csv([{"id": "a", "dtw_xh": 0.5}, {"id": "b", "dtw_xh": None, "extra": 1}], path)
    lines = path.read_text().splitlines()
    assert lines[0] == "id,dtw_xh,extra"
    assert lines[1].startswith("a,0.5")


# ---------------------------------------------------------------- end to end


def _run(monkeypatch: pytest.MonkeyPatch, fixtures: Path, *args: str) -> None:
    monkeypatch.setattr(sys, "argv", ["tracebench", "--fixtures", str(fixtures), *args])
    main()


def test_the_identity_run_passes_its_own_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    fixtures = full_tree(tmp_path)
    _run(monkeypatch, fixtures, "--candidate", "authored", "--split", "dev", "--json", str(tmp_path / "r.json"))
    printed = capsys.readouterr().out
    assert "identity gate:   PASS" in printed
    report = json.loads((tmp_path / "r.json").read_text())
    assert report["summary"]["scored"] == len(DEV)
    assert report["summary"]["dtw_xh_median"] == 0.0
    assert report["candidate"] == "authored" and report["split"] == "dev"


def test_a_second_run_can_be_paired_against_the_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """`--compare` reads a previous `--json` report and prints the paired block."""
    fixtures = full_tree(tmp_path)
    baseline = tmp_path / "baseline.json"
    _run(monkeypatch, fixtures, "--candidate", "authored", "--words", "die,mit", "--json", str(baseline))
    capsys.readouterr()
    _run(
        monkeypatch,
        fixtures,
        "--candidate",
        "authored",
        "--words",
        "die,mit",
        "--compare",
        str(baseline),
        "--csv",
        str(tmp_path / "rows.csv"),
    )
    printed = capsys.readouterr().out
    assert "compare vs" in printed and "sign_test:" in printed
    assert "dtw_delta_median: 0.000000" in printed
    assert (tmp_path / "rows.csv").read_text().splitlines()[0].startswith("id,word,kind")


def test_a_broken_ruler_ends_the_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """§14's kill criterion: with the identity broken, no candidate number is read."""
    from tools.tracebench import run as run_mod  # noqa: PLC0415

    real = run_mod.score_word

    def drifting(entry, candidate, **kwargs):
        scored = real(entry, candidate, **kwargs)
        scored["dtw_xh"] = 0.004  # a frame that no longer maps a row onto itself
        return scored

    monkeypatch.setattr(run_mod, "score_word", drifting)
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, full_tree(tmp_path), "--candidate", "authored")
    assert exc.value.code != 0
    assert "identity gate:   FAIL" in capsys.readouterr().out


def test_the_development_split_is_refused_on_another_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The ten frozen ids are Abb.-19 words: on the pair plates the split is
    undefined, not empty."""
    fixtures = build_tree(tmp_path, [row(i) for i in EXTRA], which="pairs")
    with pytest.raises(SystemExit, match="defined on the 'words' set"):
        _run(monkeypatch, fixtures, "--set", "pairs", "--split", "dev")


def test_a_root_without_the_artifact_stops_with_a_named_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixtures = full_tree(tmp_path)
    (fixtures / "suetterlin" / "suetterlin-1922" / "word_instances.json").unlink()
    with pytest.raises(SystemExit, match="word_instances"):
        _run(monkeypatch, fixtures, "--candidate", "authored")
