"""Kartei state machine, apply idempotence, redo/retire, snapshot discipline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from tools.eigenhand import apply as apply_mod
from tools.eigenhand import page as page_mod
from tools.eigenhand import redo, snapshot, store
from tools.eigenhand.kartei import load_kartei, save_kartei, strip_state
from tools.eigenhand.store import hand_dir


HAND = "test-suetterlin"


@pytest.fixture
def dataroot(tmp_path, monkeypatch):
    monkeypatch.setenv("EIGENHAND_DATA", str(tmp_path / "own-hand"))
    return tmp_path / "own-hand"


def _make_sheet(sheet: str = "B0001", rows: list[tuple[str, int, int]] | None = None) -> None:
    """A minimal printed+ingested sheet: layout.json, payload.json, crops."""
    rows = rows or [("S0001", 1, 1), ("S0002", 1, 1)]
    sheet_dir = hand_dir(HAND) / "blaetter" / sheet
    import_dir = sheet_dir / "import"
    import_dir.mkdir(parents=True, exist_ok=True)

    layout_rows = []
    payload_rows = []
    for index, (strip, attempt, attempts) in enumerate(rows):
        band = {
            "asc_top": 15.0 + 27.0 * index,
            "waist": 21.0 + 27.0 * index,
            "baseline": 27.0 + 27.0 * index,
            "desc_bot": 33.0 + 27.0 * index,
        }
        boxes = [{"word": "lesen", "label": "lesen", "x0_mm": 15.0, "x1_mm": 60.0}]
        layout_rows.append({"strip": strip, "attempt": attempt, "attempts": attempts, "band_mm": band, "boxes": boxes})
        crop_name = f"row-{index:02d}.png"
        Image.new("L", (40, 12), 220).save(import_dir / crop_name)
        payload_rows.append(
            {
                "uid": f"{sheet}-r{index:02d}",
                "row_index": index,
                "strip": strip,
                "attempt": attempt,
                "attempts": attempts,
                "words": ["lesen"],
                "qc": [],
                "crop": crop_name,
                "crop_origin_mm": [13.0, band["asc_top"] - 2.0],
            }
        )

    layout = {
        "format": 1,
        "sheet": sheet,
        "hand": HAND,
        "style": "suetterlin",
        "rows": layout_rows,
        "provenance": {"date": "2026-08-22", "commit": "", "config_hash": "", "streifen_sha256": ""},
    }
    (sheet_dir / "layout.json").write_text(json.dumps(layout), encoding="utf-8")
    payload = {
        "format": 1,
        "hand": HAND,
        "sheet": sheet,
        "style": "suetterlin",
        "rows": payload_rows,
        "session": {"date": "2026-08-22", "feder": "Test", "tinte": "", "papier": "", "geraet": "scanner"},
        "scan": {"file": "scan.jpg", "sha256": "0" * 64, "dpi_estimate": 300.0},
        "layout_provenance": layout["provenance"],
    }
    (import_dir / "payload.json").write_text(json.dumps(payload), encoding="utf-8")

    kartei = load_kartei(HAND, "suetterlin")
    kartei["sheets"][sheet] = {
        "printed": "2026-08-22",
        "strips": [r[0] for r in rows],
        "layout_sha256": "",
        "scans": [],
    }
    save_kartei(HAND, kartei)


def _result(sheet: str, lines: list[str]) -> Path:
    path = hand_dir(HAND) / f"siebung-{sheet}.txt"
    path.write_text(
        f"SIEBUNG/1 bogen={sheet} geprueft={len(lines)} von {len(lines)}\n" + "\n".join(lines) + "\n", encoding="utf-8"
    )
    return path


class TestParseResult:
    def test_rejects_wrong_sheet(self):
        with pytest.raises(SystemExit, match="expected B0002"):
            apply_mod.parse_result("SIEBUNG/1 bogen=B0001 geprueft=0 von 9\n", "B0002")

    def test_rejects_garbage_lines(self):
        with pytest.raises(SystemExit, match="unparseable"):
            apply_mod.parse_result("SIEBUNG/1 bogen=B0001 geprueft=1 von 1\nB0001-r00=ok\n", "B0001")

    def test_rejects_duplicate_uids(self):
        text = "SIEBUNG/1 bogen=B0001 geprueft=2 von 2\nB0001-r00:angenommen\nB0001-r00:verworfen#Klecks\n"
        with pytest.raises(SystemExit, match="duplicate uid"):
            apply_mod.parse_result(text, "B0001")

    @pytest.mark.parametrize("verdict", ["angenommen", "spaeter"])
    def test_rejects_a_reason_on_a_non_rejection(self, verdict):
        # The reason chips are the rejection taxonomy; on any other verdict the
        # line was hand-edited, and a silently kept reason nobody can interpret
        # is worse than a refusal.
        text = f"SIEBUNG/1 bogen=B0001 geprueft=1 von 1\nB0001-r00:{verdict}#Klecks\n"
        with pytest.raises(SystemExit, match="belong to verworfen"):
            apply_mod.parse_result(text, "B0001")

    def test_a_note_without_a_reason_is_fine_on_an_accepted_row(self):
        text = 'SIEBUNG/1 bogen=B0001 geprueft=1 von 1\nB0001-r00:angenommen "Feder lief gut"\n'
        assert apply_mod.parse_result(text, "B0001")["B0001-r00"]["note"] == "Feder lief gut"

    def test_parses_reason_and_note(self):
        text = 'SIEBUNG/1 bogen=B0001 geprueft=1 von 1\nB0001-r00:verworfen#verschrieben "zu eng? nein: daneben"\n'
        verdicts = apply_mod.parse_result(text, "B0001")
        assert verdicts["B0001-r00"] == {
            "verdict": "verworfen",
            "reason": "verschrieben",
            "note": "zu eng? nein: daneben",
        }


class TestApply:
    def test_files_fassungen_and_derives_states(self, dataroot):
        _make_sheet()
        assert strip_state(load_kartei(HAND), "S0001") == "unterwegs"
        result = _result("B0001", ["B0001-r00:angenommen", "B0001-r01:verworfen#verschrieben"])
        apply_mod.main([str(result), "--hand", HAND, "--sheet", "B0001"])

        kartei = load_kartei(HAND)
        assert strip_state(kartei, "S0001") == "belegt"
        assert strip_state(kartei, "S0002") == "geplant"  # rejected → back in the queue
        meta = json.loads((hand_dir(HAND) / "fassungen" / "S0001" / "F01" / "meta.json").read_text())
        assert meta["status"] == "angenommen"
        assert meta["words"] == ["lesen"]  # the strip attributes itself, sidecar-free
        assert (hand_dir(HAND) / "fassungen" / "S0001" / "F01" / "streifen.png").exists()
        # Rejected rows are Kartei records only — no files (owner: file just
        # the strips that are relevant).
        assert not (hand_dir(HAND) / "fassungen" / "S0002").exists()
        rejected = kartei["strips"]["S0002"]["fassungen"][0]
        assert (rejected["status"], rejected["reason"], rejected["png_sha256"]) == ("verworfen", "verschrieben", None)

    def test_apply_is_idempotent(self, dataroot):
        _make_sheet()
        result = _result("B0001", ["B0001-r00:angenommen"])
        apply_mod.main([str(result), "--hand", HAND, "--sheet", "B0001"])
        apply_mod.main([str(result), "--hand", HAND, "--sheet", "B0001"])
        assert [f["id"] for f in load_kartei(HAND)["strips"]["S0001"]["fassungen"]] == ["F01"]

    def test_apply_before_ingest_says_so_instead_of_tracing_back(self, dataroot):
        hand_dir(HAND).mkdir(parents=True)  # a hand that has never been ingested
        result = _result("B0001", ["B0001-r00:angenommen"])
        with pytest.raises(SystemExit, match="run ingest"):
            apply_mod.main([str(result), "--hand", HAND, "--sheet", "B0001"])

    def test_a_lost_print_record_is_rebuilt_from_the_layout(self, dataroot):
        # Without this, a Kartei restored from an older snapshot would get an
        # empty sheet stub: no print date, no strips (both drive the derived
        # states) and no layout hash to audit against.
        _make_sheet()
        kartei = load_kartei(HAND)
        del kartei["sheets"]["B0001"]
        save_kartei(HAND, kartei)
        apply_mod.main([str(_result("B0001", ["B0001-r00:angenommen"])), "--hand", HAND, "--sheet", "B0001"])

        record = load_kartei(HAND)["sheets"]["B0001"]
        layout_text = (hand_dir(HAND) / "blaetter" / "B0001" / "layout.json").read_text(encoding="utf-8")
        assert record["printed"] == "2026-08-22"
        assert record["strips"] == ["S0001", "S0002"]
        assert record["layout_sha256"] == hashlib.sha256(layout_text.encode()).hexdigest()
        assert record["scans"] == ["scan.jpg"]

    def test_a_payload_for_another_hand_is_refused(self, dataroot):
        # A stale or copied payload must not file rows into the wrong hand's
        # reserved dataset just because the CLI was pointed at it.
        _make_sheet()
        import_dir = hand_dir(HAND) / "blaetter" / "B0001" / "import"
        payload = json.loads((import_dir / "payload.json").read_text(encoding="utf-8"))
        payload["hand"] = "other-suetterlin"
        (import_dir / "payload.json").write_text(json.dumps(payload), encoding="utf-8")
        result = _result("B0001", ["B0001-r00:angenommen"])
        with pytest.raises(SystemExit, match="wrong hand"):
            apply_mod.main([str(result), "--hand", HAND, "--sheet", "B0001"])
        assert not (hand_dir(HAND) / "fassungen").exists()

    def test_conflicting_reverdict_is_refused(self, dataroot):
        _make_sheet()
        apply_mod.main([str(_result("B0001", ["B0001-r00:angenommen"])), "--hand", HAND, "--sheet", "B0001"])
        with pytest.raises(SystemExit, match="conflicting verdict"):
            apply_mod.main([str(_result("B0001", ["B0001-r00:verworfen#Klecks"])), "--hand", HAND, "--sheet", "B0001"])

    def test_multiple_attempts_become_separate_fassungen(self, dataroot):
        _make_sheet(rows=[("S0001", 1, 3), ("S0001", 2, 3), ("S0001", 3, 3)])
        result = _result("B0001", ["B0001-r00:verworfen#verrutscht", "B0001-r01:angenommen", "B0001-r02:angenommen"])
        apply_mod.main([str(result), "--hand", HAND, "--sheet", "B0001"])
        fassungen = load_kartei(HAND)["strips"]["S0001"]["fassungen"]
        assert [(f["id"], f["attempt"], f["status"]) for f in fassungen] == [
            ("F01", 1, "verworfen"),
            ("F02", 2, "angenommen"),
            ("F03", 3, "angenommen"),
        ]
        strip_dir = hand_dir(HAND) / "fassungen" / "S0001"
        assert sorted(p.name for p in strip_dir.iterdir()) == ["F02", "F03"]  # rejected attempt: no files


class TestRedoRetire:
    def test_the_german_date_spelling_stays_accepted(self, dataroot):
        # --date is the English spelling the language rules ask for; --datum
        # was the original flag and must keep working for anyone's notes.
        _make_sheet()
        apply_mod.main([str(_result("B0001", ["B0001-r00:angenommen"])), "--hand", HAND, "--sheet", "B0001"])
        redo.main(["S0001", "--hand", HAND, "--reason", "unruhig", "--datum", "2026-08-23"])
        assert load_kartei(HAND)["redo"][0]["queued"] == "2026-08-23"

    def test_redo_queues_and_retire_withdraws(self, dataroot):
        _make_sheet()
        apply_mod.main([str(_result("B0001", ["B0001-r00:angenommen"])), "--hand", HAND, "--sheet", "B0001"])
        redo.main(["S0001", "--hand", HAND, "--reason", "nicht optimal", "--retire", "--date", "2026-08-23"])
        kartei = load_kartei(HAND)
        assert kartei["redo"][0]["strip"] == "S0001"
        fassung = kartei["strips"]["S0001"]["fassungen"][0]
        assert fassung["status"] == "zurückgezogen"
        assert fassung["retired"] == "2026-08-23"
        assert strip_state(kartei, "S0001") == "geplant"  # withdrawn no longer counts


class TestSnapshot:
    def _accept_one(self) -> None:
        _make_sheet()
        apply_mod.main([str(_result("B0001", ["B0001-r00:angenommen"])), "--hand", HAND, "--sheet", "B0001"])

    def test_incremental_and_create_only(self, dataroot, tmp_path):
        self._accept_one()
        archive = tmp_path / "archive"
        archive.mkdir()
        snapshot.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])
        assert (archive / "own-hand" / HAND / "0001" / "fassungen" / "S0001" / "F01" / "streifen.png").exists()
        assert not (archive / "own-hand" / HAND / "0001" / "blaetter" / "B0001" / "import").exists()

        snapshot.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0002"])
        second = archive / "own-hand" / HAND / "0002"
        assert (second / "kartei.json").exists()
        assert not (second / "fassungen").exists()  # nothing new → no duplicates

        with pytest.raises(SystemExit, match="create-only"):
            snapshot.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])

    def test_a_later_scan_under_a_known_sheet_still_reaches_the_archive(self, dataroot, tmp_path):
        # The sheet directory grows: `ingest --keep-scan` files another scan
        # every time the Bogen is captured. Skipping the sheet by path alone
        # would lose it silently — and the archive is the only copy.
        self._accept_one()
        archive = tmp_path / "archive"
        archive.mkdir()
        scans = hand_dir(HAND) / "blaetter" / "B0001" / "scans"
        scans.mkdir(parents=True)
        Image.new("L", (8, 8), 200).save(scans / "scan-1.png")
        snapshot.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])
        assert (archive / "own-hand" / HAND / "0001" / "blaetter" / "B0001" / "scans" / "scan-1.png").exists()

        Image.new("L", (8, 8), 180).save(scans / "scan-2.png")
        snapshot.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0002"])
        second = archive / "own-hand" / HAND / "0002" / "blaetter" / "B0001" / "scans"
        assert (second / "scan-2.png").exists()  # the new one is filed
        assert not (second / "scan-1.png").exists()  # the known one is not duplicated

    def test_regenerable_import_crops_stay_out_of_the_archive(self, dataroot, tmp_path):
        self._accept_one()
        archive = tmp_path / "archive"
        archive.mkdir()
        snapshot.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])
        sheet = archive / "own-hand" / HAND / "0001" / "blaetter" / "B0001"
        assert (sheet / "layout.json").exists()
        assert not (sheet / "import").exists()

    def test_shrinking_snapshot_is_refused(self, dataroot, tmp_path, monkeypatch):
        self._accept_one()
        archive = tmp_path / "archive"
        archive.mkdir()
        snapshot.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])
        # A wrong/empty data root must not read as a successful backup.
        fresh = tmp_path / "fresh-root"
        monkeypatch.setenv("EIGENHAND_DATA", str(fresh))
        save_kartei(HAND, load_kartei(HAND, "suetterlin"))
        with pytest.raises(SystemExit, match="shrinking"):
            snapshot.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0002"])


class TestSiebungPage:
    """The page's result file must BE the one-row-per-line format apply reads."""

    def _page(self, dataroot) -> str:
        _make_sheet()
        import_dir = hand_dir(HAND) / "blaetter" / "B0001" / "import"
        Image.new("L", (40, 8), 235).save(import_dir / "header.png")
        payload = json.loads((import_dir / "payload.json").read_text(encoding="utf-8"))
        payload["rows"][0]["pen_mark"] = "angenommen"
        return page_mod.build_page(payload, import_dir)

    def test_notes_are_flattened_before_they_reach_the_result_line(self, dataroot):
        # A pasted line break in a remark would make the whole Siebung
        # unparseable — after the sheet has already been judged.
        assert 's.note.replace(/\\s+/g, " ")' in self._page(dataroot)

    def test_a_flattened_note_round_trips_through_apply(self, dataroot):
        self._page(dataroot)
        text = 'SIEBUNG/1 bogen=B0001 geprueft=1 von 1\nB0001-r00:verworfen#Klecks "zwei Zeilen zu einer"\n'
        assert apply_mod.parse_result(text, "B0001")["B0001-r00"]["note"] == "zwei Zeilen zu einer"

    def test_the_pen_mark_seeds_the_verdict_and_is_named_on_screen(self, dataroot):
        html = self._page(dataroot)
        assert 'data-pen="angenommen"' in html  # seedFromPen() reads this
        assert "Stift auf dem Blatt: Haken" in html


class TestCropName:
    """The crop name from payload.json becomes a path in page.py AND apply.py."""

    @pytest.mark.parametrize(
        "bad",
        [
            "../../etc/passwd.png",  # traversal
            "sub/row-00.png",
            "/abs/row-00.png",
            "..",  # Path("..").name hands it back unchanged — a name test alone misses it
            "page.png",  # the sheet's own preview and header: never dataset files
            "header.png",
            "row-01.png",  # another row's crop
            "row-0.png",  # not the spelling ingest writes
            "",
        ],
    )
    def test_anything_but_this_rows_own_crop_is_refused(self, bad):
        with pytest.raises(SystemExit, match="refusing"):
            store.check_crop_name(bad, 0)

    def test_the_name_ingest_writes_passes(self):
        assert store.check_crop_name(store.crop_name(0), 0) == "row-00.png"
        assert store.check_crop_name(store.crop_name(12), 12) == "row-12.png"

    def test_apply_refuses_before_it_creates_anything(self, dataroot):
        _make_sheet()
        import_dir = hand_dir(HAND) / "blaetter" / "B0001" / "import"
        payload = json.loads((import_dir / "payload.json").read_text(encoding="utf-8"))
        # page.png exists in every import directory — a tampered payload must
        # not be able to file the whole-sheet preview as a strip recording.
        Image.new("L", (20, 30), 210).save(import_dir / "page.png")
        payload["rows"][0]["crop"] = "page.png"
        (import_dir / "payload.json").write_text(json.dumps(payload), encoding="utf-8")
        result = _result("B0001", ["B0001-r00:angenommen"])
        with pytest.raises(SystemExit, match="refusing"):
            apply_mod.main([str(result), "--hand", HAND, "--sheet", "B0001"])
        assert not (hand_dir(HAND) / "fassungen").exists()  # no half-filed Fassung


class TestHandId:
    """A hand id addresses the whole reserved tree — it must stay a plain name."""

    @pytest.mark.parametrize("bad", ["../escape", "mn/suetterlin", "/abs-suetterlin", "MN-Suetterlin", "plain"])
    def test_path_like_or_malformed_ids_are_refused(self, bad):
        with pytest.raises(SystemExit, match="plain"):
            store.check_hand_id(bad)

    def test_a_plain_id_passes_and_stays_under_the_data_root(self, dataroot):
        assert store.check_hand_id("mn-suetterlin") == "mn-suetterlin"
        assert store.hand_dir("mn-suetterlin").parent == store.data_root()
