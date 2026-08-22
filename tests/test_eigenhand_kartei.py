"""Kartei state machine, apply idempotence, redo/retire, snapshot discipline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from tools.eigenhand import apply as apply_mod
from tools.eigenhand import redo, snapshot
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
        # Rejected rows are Kartei records only — no files ("abgelegt werden
        # nur die relevanten Streifen").
        assert not (hand_dir(HAND) / "fassungen" / "S0002").exists()
        rejected = kartei["strips"]["S0002"]["fassungen"][0]
        assert (rejected["status"], rejected["reason"], rejected["png_sha256"]) == ("verworfen", "verschrieben", None)

    def test_apply_is_idempotent(self, dataroot):
        _make_sheet()
        result = _result("B0001", ["B0001-r00:angenommen"])
        apply_mod.main([str(result), "--hand", HAND, "--sheet", "B0001"])
        apply_mod.main([str(result), "--hand", HAND, "--sheet", "B0001"])
        assert [f["id"] for f in load_kartei(HAND)["strips"]["S0001"]["fassungen"]] == ["F01"]

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
    def test_redo_queues_and_retire_withdraws(self, dataroot):
        _make_sheet()
        apply_mod.main([str(_result("B0001", ["B0001-r00:angenommen"])), "--hand", HAND, "--sheet", "B0001"])
        redo.main(["S0001", "--hand", HAND, "--reason", "nicht optimal", "--retire", "--datum", "2026-08-23"])
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
