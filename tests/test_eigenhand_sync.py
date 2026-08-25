"""Pushing the local chain up: the bookkeeping, the strips, the restore path.

`sync` is the only way local work becomes visible in the admin view, and — read
with `--from` — the only way a lost DB gets its own-hand tables back out of the
private archive. Both directions run through the same code here on purpose: a
restore path that is a second implementation is a restore path nobody finds out
is broken until the day it is needed.

The API itself is faked; what these tests pin is the CLIENT's contract. Every
HTTP call the real tool would make is recorded and asserted on.

Proves: a Fassung carries the effective nib/ink/paper of its own row; strips go
up only when asked for and only once; a filed strip that no longer matches its
Kartei hash is refused BEFORE it is sent; a snapshot directory is read exactly
like the working data root; and the standing setup merges rather than blanking
the fields a run does not name.
"""

from __future__ import annotations

import hashlib
import io
import json

import pytest
from PIL import Image

from tools.eigenhand import setup as setup_mod
from tools.eigenhand import snapshot as snapshot_mod
from tools.eigenhand import sync as sync_mod
from tools.eigenhand.kartei import load_kartei, save_kartei


HAND = "test-suetterlin"
SESSION = {
    "date": "2026-08-24",
    "feder": "Brause 361",
    "tinte": "Carbon Black",
    "papier": "Clairalfa",
    "geraet": "scanner",
}


@pytest.fixture
def dataroot(tmp_path, monkeypatch):
    monkeypatch.setenv("EIGENHAND_DATA", str(tmp_path / "own-hand"))
    return tmp_path / "own-hand"


def _png(shade: int = 220) -> bytes:
    buffer = io.BytesIO()
    Image.new("L", (2185, 343), shade).save(buffer, format="PNG")
    return buffer.getvalue()


def _build(root, sheet: str = "B0001", strip: str = "S0001", fassung: str = "F01", shade: int = 220) -> bytes:
    """A hand with one printed Bogen and one accepted, filed Fassung."""
    sheet_dir = root / HAND / "blaetter" / sheet
    sheet_dir.mkdir(parents=True, exist_ok=True)
    layout = {
        "format": 1,
        "sheet": sheet,
        "hand": HAND,
        "style": "suetterlin",
        "rows": [{"strip": strip, "attempt": 1, "attempts": 1, "cut_mm": [12.0, 13.0, 197.0, 42.0], "boxes": []}],
        "provenance": {"date": "2026-08-24", "commit": "", "config_hash": "", "streifen_sha256": ""},
    }
    (sheet_dir / "layout.json").write_text(json.dumps(layout), encoding="utf-8")

    png = _png(shade)
    fassung_dir = root / HAND / "fassungen" / strip / fassung
    fassung_dir.mkdir(parents=True, exist_ok=True)
    (fassung_dir / "streifen.png").write_bytes(png)
    (fassung_dir / "meta.json").write_text(
        json.dumps({"crop_origin_mm": [12.0, 13.0], "scan": {"dpi_estimate": 300.0}, "session": SESSION}),
        encoding="utf-8",
    )

    kartei = load_kartei(HAND, "suetterlin")
    kartei["sheets"][sheet] = {"printed": "2026-08-24", "strips": [strip], "layout_sha256": "a" * 64, "scans": []}
    kartei["strips"][strip] = {
        "fassungen": [
            {
                "id": fassung,
                "sheet": sheet,
                "row_index": 0,
                "attempt": 1,
                "attempts": 1,
                "status": "angenommen",
                "reason": None,
                "note": None,
                "png_sha256": hashlib.sha256(png).hexdigest(),
                "filed": "2026-08-24",
                "session": SESSION,
            }
        ]
    }
    save_kartei(HAND, kartei)
    return png


class _FakeApi:
    """Records every call and answers the GETs the sync makes."""

    def __init__(self, stored: dict | None = None, setup: dict | None = None):
        self.calls: list[tuple[str, str, dict | None]] = []
        self.stored = stored or {}
        self.setup = setup

    def __call__(self, method: str, url: str, token: str, body: dict | None = None, allow_404: bool = False):
        self.calls.append((method, url, body))
        if method == "GET" and "/setups/" in url:
            return self.setup
        if method == "GET" and "/strips/" in url:
            return {
                "hand": HAND,
                "strips": [{"strip": s, "fassung": f, "sha256": d} for (s, f), d in self.stored.items()],
            }
        if method == "PUT" and "/sheets/" in url:
            return {"sheet": url.rsplit("/", 1)[-1], "imported": True}
        if method == "POST" and url.endswith("/fassungen"):
            return {"hand": HAND, "recorded": len(body["fassungen"]), "skipped": 0}
        return {"stored": True}

    def puts(self, kind: str) -> list[dict]:
        return [body for method, url, body in self.calls if method == "PUT" and f"/{kind}/" in url]


def _run(monkeypatch, fake: _FakeApi, *argv: str) -> int:
    monkeypatch.setattr(sync_mod, "request_json", fake)
    monkeypatch.setenv("ADMIN_TOKEN", "t")
    return sync_mod.main(["--hand", HAND, "--api", "https://example.test", *argv])


class TestBookkeeping:
    def test_a_fassung_carries_the_effective_setup_of_its_own_row(self, dataroot, monkeypatch):
        _build(dataroot)
        fake = _FakeApi()
        assert _run(monkeypatch, fake) == 0
        pushed = [body for method, url, body in fake.calls if method == "POST"][0]["fassungen"]
        assert len(pushed) == 1
        # Denormalised on purpose: a Fassung says out of itself what it was
        # written with, without a join and without "NULL means like the hand".
        assert {key: pushed[0][key] for key in ("feder", "tinte", "papier", "geraet")} == {
            "feder": "Brause 361",
            "tinte": "Carbon Black",
            "papier": "Clairalfa",
            "geraet": "scanner",
        }

    def test_without_the_flag_no_pixels_leave_the_machine(self, dataroot, monkeypatch):
        _build(dataroot)
        fake = _FakeApi()
        _run(monkeypatch, fake)
        assert fake.puts("strips") == []
        assert not any("/strips/" in url for _method, url, _body in fake.calls)

    def test_a_bogen_without_a_layout_holds_its_verdicts_back(self, dataroot, monkeypatch, capsys):
        _build(dataroot)
        (dataroot / HAND / "blaetter" / "B0001" / "layout.json").unlink()
        fake = _FakeApi()
        _run(monkeypatch, fake)
        assert [body for method, url, body in fake.calls if method == "POST"][0]["fassungen"] == []
        assert "held back" in capsys.readouterr().out


class TestStripUpload:
    def test_the_strip_goes_up_once_and_is_skipped_when_the_hash_is_known(self, dataroot, monkeypatch):
        png = _build(dataroot)
        digest = hashlib.sha256(png).hexdigest()

        fake = _FakeApi()
        _run(monkeypatch, fake, "--mit-streifen")
        uploaded = fake.puts("strips")
        assert len(uploaded) == 1
        assert uploaded[0]["sha256"] == digest
        assert (uploaded[0]["width_px"], uploaded[0]["height_px"]) == (2185, 343)
        assert uploaded[0]["crop_origin_mm"] == [12.0, 13.0]
        assert uploaded[0]["dpi"] == 300.0

        # Second run: the server already holds these bytes.
        again = _FakeApi(stored={("S0001", "F01"): digest})
        _run(monkeypatch, again, "--mit-streifen")
        assert again.puts("strips") == []

    def test_a_filed_strip_that_no_longer_matches_its_record_is_never_sent(self, dataroot, monkeypatch):
        _build(dataroot)
        # Something rewrote the file after it was filed — a local corruption,
        # and the server is not the place to discover it.
        (dataroot / HAND / "fassungen" / "S0001" / "F01" / "streifen.png").write_bytes(_png(shade=100))
        fake = _FakeApi()
        with pytest.raises(SystemExit, match="no longer matches its record"):
            _run(monkeypatch, fake, "--mit-streifen")
        assert fake.puts("strips") == []

    def test_a_rejected_fassung_keeps_its_pixels_local(self, dataroot, monkeypatch):
        _build(dataroot)
        kartei = load_kartei(HAND)
        kartei["strips"]["S0001"]["fassungen"][0]["status"] = "verworfen"
        save_kartei(HAND, kartei)
        fake = _FakeApi()
        _run(monkeypatch, fake, "--mit-streifen")
        assert fake.puts("strips") == []

    def test_an_accepted_fassung_without_its_file_fails_the_run(self, dataroot, monkeypatch):
        # A silent skip here is the dangerous case: on the restore path it would
        # report success while leaving strips out of the DB. `apply.py` files a
        # PNG for every accepted row, so a missing one is a damaged source.
        _build(dataroot)
        (dataroot / HAND / "fassungen" / "S0001" / "F01" / "streifen.png").unlink()
        with pytest.raises(SystemExit, match="have no filed strip"):
            _run(monkeypatch, _FakeApi(), "--mit-streifen")

    def test_what_is_there_still_goes_up_before_the_run_fails(self, dataroot, monkeypatch):
        # One gap must not hide the rest — the strips that exist are pushed,
        # and only then does the run report itself incomplete.
        _build(dataroot)
        _build(dataroot, strip="S0002", shade=180)
        (dataroot / HAND / "fassungen" / "S0002" / "F01" / "meta.json").unlink()
        fake = _FakeApi()
        with pytest.raises(SystemExit, match="S0002/F01"):
            _run(monkeypatch, fake, "--mit-streifen")
        assert [body["sha256"] for body in fake.puts("strips")] == [
            hashlib.sha256(_png()).hexdigest()  # S0001's, the one that was complete
        ]


class TestRestoreFromArchive:
    def test_a_snapshot_directory_is_read_exactly_like_the_working_root(self, dataroot, tmp_path, monkeypatch):
        png = _build(dataroot)
        # An archive snapshot has the same shape one level down: kartei.json
        # plus fassungen/ and blaetter/ (tools/eigenhand/snapshot.py).
        snapshot = tmp_path / "archive" / "own-hand" / HAND / "2026-08-24-1830"
        snapshot.mkdir(parents=True)
        (snapshot / "kartei.json").write_text(
            (dataroot / HAND / "kartei.json").read_text(encoding="utf-8"), encoding="utf-8"
        )
        for sub in ("blaetter", "fassungen"):
            _copy_tree(dataroot / HAND / sub, snapshot / sub)

        # The working root is emptied — the archive alone has to carry it.
        _wipe(dataroot / HAND / "fassungen")
        fake = _FakeApi()
        assert _run(monkeypatch, fake, "--mit-streifen", "--from", str(snapshot)) == 0
        assert len(fake.puts("sheets")) == 1
        assert fake.puts("strips")[0]["sha256"] == hashlib.sha256(png).hexdigest()

    def test_a_later_snapshot_still_restores_the_whole_hand(self, dataroot, tmp_path, monkeypatch):
        """The archive is layered, and only the FIRST snapshot is self-contained.

        `snapshot.py` skips any unit already present in an earlier snapshot, so
        snapshot 2 holds a complete Kartei beside just its increment. Reading
        one directory would push snapshot 2's single strip and report success —
        the exact silent-partial-restore the guarantee exists to rule out
        (found in review, PR #410).
        """
        archive = tmp_path / "archive"
        archive.mkdir()

        _build(dataroot)  # session 1: S0001 on B0001
        snapshot_mod.main(["--hand", HAND, "--archive", str(archive), "--stamp", "2026-08-24-1830"])
        _build(dataroot, sheet="B0002", strip="S0002", shade=180)  # session 2
        snapshot_mod.main(["--hand", HAND, "--archive", str(archive), "--stamp", "2026-08-25-1900"])

        hand_archive = archive / "own-hand" / HAND
        second = hand_archive / "2026-08-25-1900"
        # Precondition of the whole test: the later snapshot really is partial.
        assert not (second / "fassungen" / "S0001").exists()
        assert not (second / "blaetter" / "B0001").exists()

        # The working copy is gone; the operator points at the LATEST snapshot,
        # which is the natural thing to do.
        _wipe(dataroot / HAND)
        fake = _FakeApi()
        assert _run(monkeypatch, fake, "--mit-streifen", "--from", str(second)) == 0

        registered = sorted(url.rsplit("/", 1)[-1] for m, url, _b in fake.calls if m == "PUT" and "/sheets/" in url)
        assert registered == ["B0001", "B0002"], "both Bögen must be registered, not just the later one"
        pushed = {
            (url.split("/")[-2], url.split("/")[-1]) for m, url, _b in fake.calls if m == "PUT" and "/strips/" in url
        }
        assert pushed == {("S0001", "F01"), ("S0002", "F01")}

    def test_the_standing_setup_comes_back_when_the_server_has_none(self, dataroot, tmp_path, monkeypatch):
        # eigenhand_hands is the fourth own-hand table and §8.1 promises all
        # four; nothing carried it before (found in review, PR #410).
        from tools.eigenhand.store import save_setup

        _build(dataroot)
        save_setup(HAND, {"hand": HAND, "style": "suetterlin", "feder": "Brause 361", "tinte": "Carbon Black"})
        archive = tmp_path / "archive"
        archive.mkdir()
        snapshot_mod.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])
        snapshot = archive / "own-hand" / HAND / "0001"
        assert (snapshot / "setup.json").exists(), "the snapshot must carry the setup at all"

        _wipe(dataroot / HAND)
        fake = _FakeApi()
        _run(monkeypatch, fake, "--from", str(snapshot))
        setups = [body for m, url, body in fake.calls if m == "PUT" and "/setups/" in url]
        assert len(setups) == 1
        assert setups[0]["feder"] == "Brause 361" and setups[0]["tinte"] == "Carbon Black"

    def test_a_setup_already_on_the_server_is_never_overwritten(self, dataroot, tmp_path, monkeypatch):
        # This is a restore, not a sync of the setup: a cached copy on an old
        # machine must not silently replace a nib the author changed elsewhere.
        from tools.eigenhand.store import save_setup

        _build(dataroot)
        save_setup(HAND, {"hand": HAND, "style": "suetterlin", "feder": "alt"})
        archive = tmp_path / "archive"
        archive.mkdir()
        snapshot_mod.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])

        fake = _FakeApi(setup={"hand": HAND, "style": "suetterlin", "feder": "neu"})
        _run(monkeypatch, fake, "--from", str(archive / "own-hand" / HAND / "0001"))
        assert [body for m, url, body in fake.calls if m == "PUT" and "/setups/" in url] == []

    def test_a_snapshot_of_another_hand_is_refused(self, dataroot, tmp_path, monkeypatch):
        _build(dataroot)
        snapshot = tmp_path / "foreign"
        snapshot.mkdir()
        (snapshot / "kartei.json").write_text(
            json.dumps({"hand": "other-kurrent", "style": "kurrent", "sheets": {}, "strips": {}, "redo": []}),
            encoding="utf-8",
        )
        with pytest.raises(SystemExit, match="refusing to push it as"):
            _run(monkeypatch, _FakeApi(), "--from", str(snapshot))

    def test_a_directory_without_a_kartei_says_what_to_point_at(self, dataroot, tmp_path, monkeypatch):
        _build(dataroot)
        with pytest.raises(SystemExit, match="point --from at a snapshot directory"):
            _run(monkeypatch, _FakeApi(), "--from", str(tmp_path / "nowhere"))


class TestPngSize:
    def test_the_size_comes_out_of_the_ihdr(self):
        assert sync_mod._png_size(_png()) == (2185, 343)

    def test_anything_that_is_not_a_png_is_refused(self):
        with pytest.raises(SystemExit, match="not a PNG"):
            sync_mod._png_size(b"not an image at all, really not")


class TestStandingSetup:
    def test_naming_one_field_keeps_the_others(self, dataroot, monkeypatch):
        seen: list[dict] = []

        def fake(method, url, token, body=None, allow_404=False):
            if method == "GET":
                return {"hand": HAND, "style": "suetterlin", "feder": "alt", "tinte": "Carbon Black", "papier": "90 g"}
            seen.append(body)
            return {"hand": HAND, "style": "suetterlin", **body}

        monkeypatch.setattr(setup_mod, "request_json", fake)
        monkeypatch.setenv("ADMIN_TOKEN", "t")
        assert setup_mod.main(["--hand", HAND, "--api", "https://example.test", "--feder", "neu"]) == 0
        assert seen[0]["feder"] == "neu"
        # Correcting one typo must not blank the rest of the campaign's setup.
        assert seen[0]["tinte"] == "Carbon Black" and seen[0]["papier"] == "90 g"

    def test_show_reads_the_local_cache_without_a_token(self, dataroot, monkeypatch, capsys):
        from tools.eigenhand.store import save_setup

        monkeypatch.delenv("ADMIN_TOKEN", raising=False)
        save_setup(HAND, {"hand": HAND, "style": "suetterlin", "feder": "Brause 361"})
        assert setup_mod.main(["--hand", HAND, "--show"]) == 0
        assert "Brause 361" in capsys.readouterr().out


def _copy_tree(src, dst) -> None:
    import shutil

    shutil.copytree(src, dst)


def _wipe(path) -> None:
    import shutil

    shutil.rmtree(path)
