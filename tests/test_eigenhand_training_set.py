"""The training export of the hand-drawn Bahnen: the draw, the filter, the separation.

Four things are pinned here. The one this module exists for is the SEPARATION
from the bench (`TestBenchSeparation`): the export tree must not be a fixture
root, must not sit inside one, and must not be loadable as one — a strip has no
reference trace (`core/eigenhand/pfad.py`, „NOT `word_instances`";
`docs/proposals/eigenhand-erfassung.md` §12, Prüfstein 2), so a number measured
against a drawn Bahn is not a bench number. It is modelled on
`tests/test_lab_fixture_wiring.py`, which pins the wiring this tree must never
be mistaken for.

The other three are the draw (`TestZiehung`), the record read off the Kartei
(`TestRueckhaltRecord`) and the export itself against a fake API
(`TestExport`). The real export cannot run here at all: it pulls reserved
own-hand pixels out of the shared database, and there is not one hand-drawn
Bahn in existence yet.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from core.config import REPO_ROOT
from tools.eigenhand import training_set as tool
from tools.eigenhand.training_set import (
    HOLDOUT_FORMAT,
    HOLDOUT_SETS,
    MANIFEST_NAME,
    SET_HOLDOUT_FOLLOWER,
    SET_HOLDOUT_RELEASE,
    SET_PRACTICE,
    SETS,
    case_id,
    draw,
    export_root,
    extend,
    holdout_of,
    set_for_strip,
)


HAND = "mn-suetterlin"
SHARES = {SET_HOLDOUT_FOLLOWER: 0.2, SET_HOLDOUT_RELEASE: 0.2}
TODAY = "2026-09-20"

# A tiny stand-in for the committed strip plan: the draw walks its strips, and
# 188 real ones would make every case below slower without testing anything the
# ids do not already say.
SMALL_PLAN = {"strips": {f"S{n:04d}": {"words": ["lesen"]} for n in range(1, 41)}}

# 10 px per mm, a strip 190 mm wide cut at x 10..200 and y 20..60 — the same
# synthetic geometry `tests/test_eigenhand_pfad.py` measures the frame with.
LAYOUT_ROW = {
    "strip": "S0001",
    "cut_mm": [10.0, 20.0, 200.0, 60.0],
    "band_mm": {"asc_top": 24.0, "waist": 32.0, "baseline": 44.0, "desc_bot": 56.0},
    "boxes": [{"word": "lesen", "x0_mm": 15.0, "x1_mm": 45.0}],
}
STRIP_ROW = {
    "strip": "S0001",
    "fassung": "F01",
    "sheet": "B0001",
    "row_index": 0,
    "width_px": 1900,
    "height_px": 400,
    "crop_origin_mm": [10.0, 20.0],
}


@pytest.fixture(autouse=True)
def _no_real_archive(monkeypatch):
    """No test here may fall through to the operator's private archive.

    `archived_holdout` reads `$KURRENTSCHRIFT_ARCHIVE` when no path is
    passed, and on the author's machine that variable points at the real
    clone — which would make these results depend on whose machine runs them.
    The two tests that need an archive build one under `tmp_path`.
    """
    monkeypatch.delenv("KURRENTSCHRIFT_ARCHIVE", raising=False)


def _kartei(tmp_path: Path, monkeypatch) -> dict:
    """An empty Kartei under a throwaway data root."""
    monkeypatch.setenv("EIGENHAND_DATA", str(tmp_path / "own-hand"))
    from tools.eigenhand.kartei import load_kartei

    return load_kartei(HAND)


def _drawn(tmp_path: Path, monkeypatch) -> dict:
    monkeypatch.setattr(tool, "load_plan", lambda *_a: SMALL_PLAN)
    kartei = _kartei(tmp_path, monkeypatch)
    draw(HAND, kartei, "key-a", SHARES, TODAY)
    return kartei


# ------------------------------------------------------------------- separation


class TestBenchSeparation:
    """The export tree is not a bench root, and cannot be mistaken for one."""

    @pytest.fixture(autouse=True)
    def _default_root(self, monkeypatch):
        # These pin the SHIPPED default, not whatever an operator happens to
        # have exported in their shell.
        monkeypatch.delenv("EIGENHAND_TRAINING_SET", raising=False)

    def test_the_export_root_is_outside_every_bench_fixture_root(self):
        from tools.glyphbench.export_fixtures import DEFAULT_OUT_DIR as GLYPH_EXPORT_DIR
        from tools.glyphlab.cases import DEFAULT_FIXTURES_DIR as GLYPHLAB_DIR
        from tools.tracebench.reference import DEFAULT_FIXTURES_DIR as TRACEBENCH_DIR
        from tools.wordbench.export_fixtures import DEFAULT_OUT_DIR as WORD_EXPORT_DIR
        from tools.wordlab.cases import DEFAULT_FIXTURES_DIR as WORDLAB_DIR

        ours = export_root().resolve()
        for bench in (GLYPH_EXPORT_DIR, GLYPHLAB_DIR, TRACEBENCH_DIR, WORD_EXPORT_DIR, WORDLAB_DIR):
            root = bench.resolve()
            assert ours != root
            assert not ours.is_relative_to(root)
            assert not root.is_relative_to(ours)

    def test_the_export_root_is_not_named_like_a_fixture_tree(self):
        # The benches all live under `tools/<bench>/fixtures`; a third tree of
        # that name is what invites `--fixtures` to be pointed at it.
        assert "fixtures" not in export_root().resolve().parts

    def test_the_manifest_is_not_the_name_the_lab_loaders_glob_for(self):
        # `tools.wordlab.cases` / `tools.glyphlab.cases` find a fixture root by
        # globbing `<root>/*/manifest.json` — which is exactly the depth this
        # export writes its own manifest at. A different name means a bench
        # pointed here finds nothing instead of loading reserved material as a
        # frozen reference.
        import inspect

        from tools.wordlab import cases as wordlab_cases

        assert MANIFEST_NAME != "manifest.json"
        assert "manifest.json" in inspect.getsource(wordlab_cases)

    def test_a_lab_loader_pointed_at_this_tree_finds_nothing(self, tmp_path):
        # The behaviour, not the proxy: the test above pins two NAMES, and a
        # discovery change on the loaders' side would leave it green while this
        # tree quietly became loadable. Here the loaders actually run.
        from tools.glyphlab.cases import iter_fixture_cases
        from tools.wordlab.cases import fixture_root_for

        root = tmp_path / "training-sets"
        case = root / HAND / SET_PRACTICE / case_id("S0001", "F01", 0)
        case.mkdir(parents=True)
        (case / "path.json").write_text("{}", encoding="utf-8")
        (root / HAND / MANIFEST_NAME).write_text("{}", encoding="utf-8")

        assert iter_fixture_cases(fixtures_root=root) == []
        with pytest.raises(KeyError):
            fixture_root_for(fixtures_root=root, style="suetterlin")

    def test_the_default_root_is_gitignored(self):
        # „No byte of it enters the repo" is a licensing promise
        # (quellen-und-rechte.md §5), and the tree sits under `tools/`, which is
        # otherwise committed code — so the rule has to be there by name.
        rule = "/" + export_root().resolve().relative_to(REPO_ROOT).as_posix() + "/"
        assert rule in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    def test_a_target_inside_the_repo_but_outside_that_rule_is_refused(self, tmp_path):
        # The rule above is the whole licensing guarantee, and until this guard
        # `--out .` wrote reserved own-hand crops into the checkout as
        # untracked, unignored files.
        assert tool.checked_out(tmp_path / "anywhere") == tmp_path / "anywhere"
        assert tool.checked_out(tool.DEFAULT_EXPORT_ROOT / HAND)
        for inside in (REPO_ROOT, REPO_ROOT / "tools" / "eigenhand", REPO_ROOT / "data" / "samples"):
            with pytest.raises(SystemExit) as exc:
                tool.checked_out(inside)
            assert "quellen-und-rechte" in str(exc.value)


# ------------------------------------------------------------------------ draw


class TestZiehung:
    def test_the_draw_covers_every_plan_strip_and_the_sets_are_disjoint(self, tmp_path, monkeypatch):
        record = _drawn(tmp_path, monkeypatch)["holdout"]
        assert set(record["strips"]) == set(SMALL_PLAN["strips"])
        members = {set_name: {s for s, row in record["strips"].items() if row["set"] == set_name} for set_name in SETS}
        assert members[SET_HOLDOUT_FOLLOWER] & members[SET_HOLDOUT_RELEASE] == set()
        assert members[SET_PRACTICE] & members[SET_HOLDOUT_FOLLOWER] == set()
        assert members[SET_PRACTICE] & members[SET_HOLDOUT_RELEASE] == set()
        assert sum(len(m) for m in members.values()) == len(SMALL_PLAN["strips"])

    def test_membership_is_a_pure_function_of_key_hand_and_strip(self):
        first = [set_for_strip("key-a", HAND, f"S{n:04d}", SHARES) for n in range(1, 60)]
        again = [set_for_strip("key-a", HAND, f"S{n:04d}", SHARES) for n in range(1, 60)]
        assert first == again
        # Another key, and another hand under the same key, hold back other
        # strips — otherwise two hands would share one hold-out set by accident.
        assert first != [set_for_strip("key-b", HAND, f"S{n:04d}", SHARES) for n in range(1, 60)]
        assert first != [set_for_strip("key-a", "xy-kurrent", f"S{n:04d}", SHARES) for n in range(1, 60)]

    def test_the_shares_land_roughly_where_they_were_asked_to(self):
        drawn = [set_for_strip("key-a", HAND, f"S{n:04d}", SHARES) for n in range(1, 1001)]
        for set_name in HOLDOUT_SETS:
            assert 0.15 < drawn.count(set_name) / len(drawn) < 0.25

    def test_the_order_of_the_two_holdout_sets_is_part_of_the_draw(self):
        # Swapping the tuple would re-assign every strip in the band between the
        # two shares, silently and for material already trained on.
        assert HOLDOUT_SETS == (SET_HOLDOUT_FOLLOWER, SET_HOLDOUT_RELEASE)
        lopsided = {SET_HOLDOUT_FOLLOWER: 0.9 - 0.5, SET_HOLDOUT_RELEASE: 0.1}
        swapped = {SET_HOLDOUT_RELEASE: 0.4, SET_HOLDOUT_FOLLOWER: 0.1}
        assert [set_for_strip("k", HAND, f"S{n:04d}", lopsided) for n in range(1, 50)] != [
            set_for_strip("k", HAND, f"S{n:04d}", swapped) for n in range(1, 50)
        ]

    def test_a_second_draw_is_refused_and_names_the_first(self, tmp_path, monkeypatch):
        kartei = _drawn(tmp_path, monkeypatch)
        with pytest.raises(SystemExit) as exc:
            draw(HAND, kartei, "key-b", SHARES, "2026-10-01")
        assert "key-a" in str(exc.value) and TODAY in str(exc.value)

    def test_shares_that_leave_nothing_to_train_on_are_refused(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tool, "load_plan", lambda *_a: SMALL_PLAN)
        kartei = _kartei(tmp_path, monkeypatch)
        with pytest.raises(SystemExit):
            draw(HAND, kartei, "k", {SET_HOLDOUT_FOLLOWER: 0.6, SET_HOLDOUT_RELEASE: 0.5}, TODAY)
        for bad in ({SET_HOLDOUT_FOLLOWER: 0.0, SET_HOLDOUT_RELEASE: 0.2}, {SET_HOLDOUT_FOLLOWER: 0.2}):
            with pytest.raises(SystemExit):
                draw(HAND, kartei, "k", bad, TODAY)

    def test_a_draw_without_a_key_is_refused(self, tmp_path, monkeypatch):
        monkeypatch.setattr(tool, "load_plan", lambda *_a: SMALL_PLAN)
        kartei = _kartei(tmp_path, monkeypatch)
        with pytest.raises(SystemExit):
            draw(HAND, kartei, "   ", SHARES, TODAY)

    def test_the_real_plan_can_be_drawn_over_before_a_single_bahn_exists(self, tmp_path, monkeypatch):
        # The point of the whole shape: the split is decided over the committed
        # plan, so it can be — and should be — fixed while the material is still
        # unwritten. No network, no Bahn, no Fassung.
        kartei = _kartei(tmp_path, monkeypatch)
        record = draw(HAND, kartei, "real", SHARES, TODAY)
        assert len(record["strips"]) > 100


class TestRueckhaltRecord:
    def test_no_record_reads_as_no_draw(self):
        assert holdout_of({}) is None

    def test_a_newer_record_is_refused_rather_than_read_as_empty(self):
        with pytest.raises(SystemExit) as exc:
            holdout_of({"holdout": {"format": HOLDOUT_FORMAT + 1, "strips": {}}})
        assert "NEWER" in str(exc.value)

    def test_a_record_naming_an_unknown_set_is_refused(self):
        record = {"format": HOLDOUT_FORMAT, "strips": {"S0001": {"set": "irgendwas"}}}
        with pytest.raises(SystemExit):
            holdout_of({"holdout": record})

    def test_a_strip_appended_to_the_plan_later_joins_under_the_recorded_key(self, tmp_path, monkeypatch):
        kartei = _drawn(tmp_path, monkeypatch)
        record = kartei["holdout"]
        grown = {"strips": {**SMALL_PLAN["strips"], "S0199": {"words": ["neu"]}}}
        monkeypatch.setattr(tool, "load_plan", lambda *_a: grown)
        added = extend(HAND, record, "2026-11-02")
        assert added == [("S0199", set_for_strip("key-a", HAND, "S0199", SHARES))]
        assert record["strips"]["S0199"]["since"] == "2026-11-02"
        # And the strips that were already there keep both their side and the
        # date they joined on — a later run never re-dates a membership.
        assert record["strips"]["S0001"]["since"] == TODAY
        assert extend(HAND, record, "2026-11-03") == []

    def test_a_draw_filed_in_the_archive_blocks_a_second_one_after_a_lost_data_root(self, tmp_path, monkeypatch):
        # `sync --from` pushes an archived Kartei UP to the API and never
        # writes the local one, so a lost data root would otherwise let
        # `--draw` draw a second time over a hand the archive already knows.
        from tools.eigenhand.snapshot import ARCHIVE_SUBDIR

        drawn = _drawn(tmp_path, monkeypatch)
        archive = tmp_path / "archive"
        filed = archive / ARCHIVE_SUBDIR / HAND / "2026-09-20-1200"
        filed.mkdir(parents=True)
        (filed / "kartei.json").write_text(json.dumps(drawn, ensure_ascii=False), encoding="utf-8")

        found = tool.archived_holdout(HAND, str(archive))
        assert found is not None and found[0]["key"] == "key-a" and found[1] == filed
        # A hand the archive does not know reads as „no draw filed", not as an error.
        assert tool.archived_holdout("xy-kurrent", str(archive)) is None
        assert tool.archived_holdout(HAND, None) is None

        with pytest.raises(SystemExit) as exc:
            tool._refuse_if_archived(HAND, str(archive))
        assert "key-a" in str(exc.value) and "sync --from" in str(exc.value)
        # The newest stamp wins, the same rule `sync._source` follows.
        newer = archive / ARCHIVE_SUBDIR / HAND / "2026-11-02-0900"
        newer.mkdir(parents=True)
        (newer / "kartei.json").write_text(json.dumps(drawn, ensure_ascii=False), encoding="utf-8")
        assert tool.archived_holdout(HAND, str(archive))[1] == newer

    def test_an_export_without_a_local_draw_names_the_archived_one_instead_of_ziehen(self, tmp_path, monkeypatch):
        from tools.eigenhand.snapshot import ARCHIVE_SUBDIR

        drawn = _drawn(tmp_path, monkeypatch)
        archive = tmp_path / "archive"
        filed = archive / ARCHIVE_SUBDIR / HAND / "2026-09-20-1200"
        filed.mkdir(parents=True)
        (filed / "kartei.json").write_text(json.dumps(drawn, ensure_ascii=False), encoding="utf-8")
        # The local Kartei is gone — a fresh data root, as after a machine loss.
        monkeypatch.setenv("EIGENHAND_DATA", str(tmp_path / "lost"))

        with pytest.raises(SystemExit) as exc:
            tool.export(HAND, "https://example.invalid", "token", tmp_path / "out", TODAY, archive=str(archive))
        assert "--draw" not in str(exc.value)
        assert "ARCHIVE does" in str(exc.value)

    def test_a_recorded_membership_the_rule_no_longer_reproduces_stops_the_run(self, tmp_path, monkeypatch):
        kartei = _drawn(tmp_path, monkeypatch)
        record = kartei["holdout"]
        moved = next(s for s, row in record["strips"].items() if row["set"] == SET_PRACTICE)
        record["strips"][moved]["set"] = SET_HOLDOUT_RELEASE
        with pytest.raises(SystemExit) as exc:
            extend(HAND, record, TODAY)
        assert moved in str(exc.value) and "authority" in str(exc.value)


class TestStatusFilter:
    def test_only_accepted_fassungen_are_training_data(self):
        archive = {
            "fassungen": [
                {"strip": "S0001", "fassung": "F01", "status": "angenommen"},
                {"strip": "S0001", "fassung": "F02", "status": "zurueckgezogen"},
                {"strip": "S0002", "fassung": "F01", "status": "verworfen"},
            ]
        }
        assert tool._accepted(archive) == {("S0001", "F01")}

    def test_hand_work_is_a_drawn_bahn_or_corrected_boundaries_but_never_a_skip(self):
        drawn = {"box_index": 0, "verfahren": "authored", "strokes": [[[0.0, 0.0], [1.0, 1.0]]]}
        corrected = {
            "box_index": 1,
            "verfahren": "tintenpfad",
            "strokes": [[[0.0, 0.0], [1.0, 1.0]]],
            "letter_spans": [{"stroke": 0, "slot": 0, "first": 0, "last": 1, "herkunft": "authored"}],
        }
        followed = {"box_index": 2, "verfahren": "tintenpfad", "strokes": [[[0.0, 0.0], [1.0, 1.0]]]}
        # A Skip-Eintrag may claim any `verfahren`; it carries no path, so there
        # is nothing to learn from and nothing to archive.
        skipped = {"box_index": 3, "verfahren": "authored", "status": "skipped", "grund": "gave_up", "strokes": []}
        kept = tool._hand_work([drawn, corrected, followed, skipped])
        assert [entry["box_index"] for entry in kept] == [0, 1]


# ---------------------------------------------------------------------- export


def _plane() -> np.ndarray:
    """A synthetic strip: paper, with one thick dark bar inside word box 0."""
    plane = np.ones((400, 1900), dtype=np.float64)
    plane[150:260, 90:320] = 0.05
    return plane


def _entry(box_index: int = 0) -> dict:
    return {
        "box_index": box_index,
        "word": "lesen",
        "verfahren": "authored",
        "erzeugt_am": "2026-09-21",
        "flecken_n": 2,
        "xh_px": 120.0,
        "registration_px": {"tx": 100.0, "ty": 0.0, "baseline_row": 240.0},
        "strokes": [[[0.0, 0.0], [1.0, 0.5]]],
        "letter_spans": [{"stroke": 0, "slot": 0, "first": 0, "last": 1, "herkunft": "authored"}],
        "konfiguration": {},
        "meta": {},
    }


def _stub_api(monkeypatch, *, fassungen: list[dict], pfade: list[dict]) -> None:
    """Everything the export reads over HTTP, answered from memory."""

    def answer(_method, url, _token, *_a, **_kw):
        if "/archive/" in url:
            return {"hand": HAND, "style": "suetterlin", "fassungen": fassungen}
        if url.endswith("/layout"):
            return {"rows": [LAYOUT_ROW]}
        if url.endswith("/pfade"):
            return {"format": 2, "pfade": pfade}
        return {"hand": HAND, "strips": [STRIP_ROW]}

    monkeypatch.setattr(tool, "request_json", answer)
    monkeypatch.setattr(tool, "_strip_plane", lambda *_a: _plane())
    monkeypatch.setattr(tool, "_style_constants", lambda _style: {"manifest": {}, "source_id": "suetterlin-1922"})
    # No chart row for anything: every word then reads as unauthored, which is
    # the state the interesting cases are in anyway — the author drew them
    # BECAUSE the follower could not.
    monkeypatch.setattr(tool, "LiveDuctus", lambda *_a: SimpleNamespace(have=set(), rows_for=lambda _keys: ({}, {})))


class TestExport:
    def test_an_export_without_a_draw_is_refused_and_names_the_command(self, tmp_path, monkeypatch):
        _kartei(tmp_path, monkeypatch)
        with pytest.raises(SystemExit) as exc:
            tool.export(HAND, "https://example.invalid", "token", tmp_path / "out", TODAY)
        assert "--draw" in str(exc.value)

    def test_a_drawn_box_lands_in_its_set_with_its_two_planes(self, tmp_path, monkeypatch):
        from tools.eigenhand.kartei import save_kartei

        kartei = _drawn(tmp_path, monkeypatch)
        save_kartei(HAND, kartei)
        set_name = kartei["holdout"]["strips"]["S0001"]["set"]
        _stub_api(
            monkeypatch, fassungen=[{"strip": "S0001", "fassung": "F01", "status": "angenommen"}], pfade=[_entry()]
        )
        out = tmp_path / "out"
        assert tool.export(HAND, "https://example.invalid", "token", out, TODAY) == 1

        case = out / set_name / case_id("S0001", "F01", 0)
        payload = json.loads((case / "path.json").read_text(encoding="utf-8"))
        assert payload["set"] == set_name
        assert payload["drawn"] is True
        assert payload["authored_boundaries"] == 1
        assert payload["strokes"] == _entry()["strokes"]
        # The ROW's own Streifen-Pfad format travels beside this file's
        # envelope version: without it „no corrected boundaries" and „written
        # before `letter_spans` existed" are the same picture.
        assert payload["pfad_format"] == 2
        assert payload["format"] == tool.TRAINING_SET_FORMAT
        # The shaped slots travel because `letter_spans[].slot` counts into
        # them; without the slot list a corrected boundary is an index into
        # nothing.
        assert [slot["text"] for slot in payload["slots"]] == list("lesen")
        assert payload["unauthored_glyphs"]
        assert (case / "crop.png").exists() and (case / "ink.png").exists()

        manifest = json.loads((out / MANIFEST_NAME).read_text(encoding="utf-8"))
        assert manifest["sets"][set_name]["cases"] == 1
        assert manifest["holdout"]["key"] == "key-a"
        assert "Prüfstein 2" in manifest["note"]
        # The guard of the separation test, checked on the real tree this time.
        assert not list(out.rglob("manifest.json"))

    def test_a_withdrawn_fassung_leaves_the_export_on_the_next_run(self, tmp_path, monkeypatch):
        from tools.eigenhand.kartei import save_kartei

        kartei = _drawn(tmp_path, monkeypatch)
        save_kartei(HAND, kartei)
        set_name = kartei["holdout"]["strips"]["S0001"]["set"]
        out = tmp_path / "out"
        _stub_api(
            monkeypatch, fassungen=[{"strip": "S0001", "fassung": "F01", "status": "angenommen"}], pfade=[_entry()]
        )
        tool.export(HAND, "https://example.invalid", "token", out, TODAY)
        assert (out / set_name / case_id("S0001", "F01", 0)).is_dir()

        # `redo --retire` withdrew it: the status comes from the archive read,
        # and a first run that filed it must not keep it filed forever.
        _stub_api(
            monkeypatch, fassungen=[{"strip": "S0001", "fassung": "F01", "status": "zurueckgezogen"}], pfade=[_entry()]
        )
        assert tool.export(HAND, "https://example.invalid", "token", out, "2026-09-22") == 0
        assert not (out / set_name / case_id("S0001", "F01", 0)).exists()
        manifest = json.loads((out / MANIFEST_NAME).read_text(encoding="utf-8"))
        assert manifest["skipped"]["not_accepted"] == 1

    def test_pruning_refuses_to_touch_a_tree_this_tool_did_not_write(self, tmp_path):
        # The one delete path in the family, and the guard that keeps a mistyped
        # `--out` from finding anything to destroy.
        foreign = tmp_path / "somebody-elses"
        (foreign / SET_PRACTICE / "keep-me").mkdir(parents=True)
        assert tool._prune(foreign, set(), HAND) == []
        assert (foreign / SET_PRACTICE / "keep-me").is_dir()

    def test_a_second_hand_into_one_out_is_refused_before_anything_is_cut(self, tmp_path, monkeypatch):
        # A case id names no hand, so two hands in one directory interleave in
        # the same `<set_name>/` folders and each run prunes the other's cases away.
        from tools.eigenhand.kartei import save_kartei

        kartei = _drawn(tmp_path, monkeypatch)
        save_kartei(HAND, kartei)
        set_name = kartei["holdout"]["strips"]["S0001"]["set"]
        out = tmp_path / "shared"
        _stub_api(
            monkeypatch, fassungen=[{"strip": "S0001", "fassung": "F01", "status": "angenommen"}], pfade=[_entry()]
        )
        tool.export(HAND, "https://example.invalid", "token", out, TODAY)
        mine = out / set_name / case_id("S0001", "F01", 0)
        assert mine.is_dir()

        with pytest.raises(SystemExit) as exc:
            tool.export("xy-kurrent", "https://example.invalid", "token", out, TODAY)
        assert HAND in str(exc.value)
        assert mine.is_dir()
        # And the delete path alone would have refused too, had it got that far.
        assert tool._prune(out, set(), "xy-kurrent") == []
        assert mine.is_dir()
