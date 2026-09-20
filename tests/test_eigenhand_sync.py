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

from core.eigenhand.flecken import FLECKEN_FORMAT
from tools.eigenhand import pull as pull_mod
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


class TestFleckenmaskeDirection:
    """The one field whose master is the SERVER — up to fill, down to keep.

    The specks are found locally at import, but the author erases them with the
    brush in the workbench, so the corrected mask only exists up there. `sync`
    may therefore fill a row that has none and never overwrite one; `pull
    --flecken` is what brings the hand-edited list back into the Kartei and the
    Fassungen's meta.json, which is what puts it into the next archive
    snapshot — and from there, through `sync --from`, back into a restored DB.
    """

    @staticmethod
    def _pushed_row(monkeypatch, fake: _FakeApi) -> dict:
        assert _run(monkeypatch, fake) == 0
        body = next(body for method, url, body in fake.calls if url.endswith("/fassungen"))
        return body["fassungen"][0]

    def _with_mask(self, maske) -> None:
        kartei = load_kartei(HAND)
        kartei["strips"]["S0001"]["fassungen"][0]["flecken"] = maske
        save_kartei(HAND, kartei)

    def test_a_local_mask_travels_with_its_fassung(self, dataroot, monkeypatch):
        _build(dataroot)
        maske = [{"x_mm": 30.0, "y_mm": 8.0, "r_mm": 0.4, "quelle": "auto"}]
        self._with_mask(maske)
        row = self._pushed_row(monkeypatch, _FakeApi())
        assert row["flecken"] == maske
        # The detector's format travels with it, so an older API refuses the
        # push instead of storing circles under other semantics.
        assert row["flecken_format"] == FLECKEN_FORMAT

    def test_a_fassung_nobody_has_looked_at_pushes_no_mask_at_all(self, dataroot, monkeypatch):
        """`null` is „nobody has looked" — the state the server may still fill."""
        _build(dataroot)
        row = self._pushed_row(monkeypatch, _FakeApi())
        assert row["flecken"] is None
        assert row["flecken_format"] is None

    def test_an_emptied_mask_travels_as_an_empty_list(self, dataroot, monkeypatch):
        """`[]` is a READING — „looked, nothing to erase".

        `pull --flecken` writes it once the author has removed every circle, and
        `sync --from` is the restore path: collapsing it to `null` would bring
        the cleared master back as „nobody has looked" and leave it open to
        being re-filled with the stale automatic list.
        """
        _build(dataroot)
        self._with_mask([])
        row = self._pushed_row(monkeypatch, _FakeApi())
        assert row["flecken"] == []
        assert row["flecken_format"] == FLECKEN_FORMAT

    def test_pull_brings_the_hand_edited_mask_back_into_kartei_and_meta(self, dataroot, monkeypatch, capsys):
        _build(dataroot)
        by_hand = [{"x_mm": 44.0, "y_mm": 9.0, "r_mm": 0.5, "quelle": "hand"}]

        def fake(method: str, url: str, token: str, body=None, allow_404: bool = False):
            assert (method, url.endswith(f"/eigenhand/archive/{HAND}")) == ("GET", True)
            return {
                "hand": HAND,
                "style": "suetterlin",
                "fassungen": [{"strip": "S0001", "fassung": "F01", "flecken": by_hand}],
            }

        monkeypatch.setattr(pull_mod, "request_json", fake)
        monkeypatch.setenv("ADMIN_TOKEN", "t")
        assert pull_mod.main(["--hand", HAND, "--flecken", "--api", "https://example.test"]) == 0
        assert load_kartei(HAND)["strips"]["S0001"]["fassungen"][0]["flecken"] == by_hand
        meta = json.loads((dataroot / HAND / "fassungen" / "S0001" / "F01" / "meta.json").read_text(encoding="utf-8"))
        assert meta["flecken"] == by_hand
        assert "snapshot" in capsys.readouterr().out

    def test_pull_leaves_a_fassung_the_server_has_no_mask_for_alone(self, dataroot, monkeypatch):
        _build(dataroot)
        kartei = load_kartei(HAND)
        local = [{"x_mm": 1.0, "y_mm": 2.0, "r_mm": 0.3, "quelle": "auto"}]
        kartei["strips"]["S0001"]["fassungen"][0]["flecken"] = local
        save_kartei(HAND, kartei)
        monkeypatch.setattr(
            pull_mod,
            "request_json",
            lambda *a, **k: {"hand": HAND, "style": "suetterlin", "fassungen": [{"strip": "S0001", "fassung": "F01"}]},
        )
        monkeypatch.setenv("ADMIN_TOKEN", "t")
        assert pull_mod.main(["--hand", HAND, "--flecken", "--api", "https://example.test"]) == 0
        assert load_kartei(HAND)["strips"]["S0001"]["fassungen"][0]["flecken"] == local

    def test_pull_wants_either_a_sheet_or_the_masks(self, monkeypatch):
        monkeypatch.setenv("ADMIN_TOKEN", "t")
        with pytest.raises(SystemExit):
            pull_mod.main(["--hand", HAND])


def _bahn(box: int = 0, word: str = "lesen", **overrides) -> dict:
    """One hand-drawn Bahn as the API answers with it."""
    return {
        "box_index": box,
        "word": word,
        "strokes": [[[0.0, 0.0], [1.0, 1.0]]],
        "registration_px": {"tx": 40.0, "ty": 0.0, "baseline_row": 240.0},
        "xh_px": 120.0,
        "verfahren": "authored",
        "konfiguration": {},
        "meta": {},
        "erzeugt_am": "2026-09-20",
        "flecken_n": None,
        **overrides,
    }


def _as_stored(entry: dict, pfad_format: int) -> dict:
    """What the real API answers a push with — NORMALISED, like `check_paths`.

    A format-1 entry accepted under format 2 comes back carrying the four keys
    of that format, filled in. The fake echoed the request verbatim instead, so
    the restore's „did the Bahn come back" check compared against something the
    real server never sends and the miscount it caused was invisible here
    (found in review, PR #639).
    """
    if pfad_format < 2:
        return entry
    return {"status": "ok", "grund": None, "detail": None, "letter_spans": None, **entry}


class _FakePfadApi:
    """The two reads the Bahn chain makes, and every write it attempts.

    Answers `GET /eigenhand/strips/{hand}` with the stored Fassungen and
    `GET|PUT …/{strip}/{fassung}/pfade` with what it holds for that box — a
    Fassung it does not hold is a 404, which is what an unrestored strip
    image looks like from the client's side.
    """

    def __init__(
        self, pfade: dict[tuple[str, str], list[dict]], *, declared: int | None = 1, rows=None, swallow: bool = False
    ):
        self.pfade = dict(pfade)
        self.declared = declared
        self.rows = list(rows) if rows is not None else sorted(pfade)
        # A server that answers a PUT with less than it was handed — the one
        # shape a restore counted off the REQUEST would have called a success.
        self.swallow = swallow
        self.calls: list[tuple[str, str, dict | None]] = []

    def __call__(self, method: str, url: str, token: str, body: dict | None = None, allow_404: bool = False):
        self.calls.append((method, url, body))
        plain = url.split("?")[0]
        if plain.endswith("/pfade"):
            strip, fassung = plain.split("/")[-3:-1]
            if method == "PUT":
                echo = [] if self.swallow else [_as_stored(entry, body["format"]) for entry in body["pfade"]]
                self.pfade[(strip, fassung)] = echo
                return {"format": body["format"], "pfade": echo}
            if (strip, fassung) not in self.pfade:
                if allow_404:
                    return None
                raise SystemExit(f"GET {url} → 404")
            answer: dict = {"pfade": self.pfade[(strip, fassung)]}
            if self.declared is not None:
                answer["format"] = self.declared
            return answer
        if method == "GET" and "/strips/" in url:
            # `sha256: ""` — no bytes are stored up here, so `_push_strips`
            # uploads rather than skipping, which is what a restore does.
            return {"hand": HAND, "strips": [{"strip": s, "fassung": f, "sha256": ""} for s, f in self.rows]}
        if method == "PUT" and "/sheets/" in url:
            return {"sheet": url.rsplit("/", 1)[-1], "imported": True}
        if method == "POST" and url.endswith("/fassungen"):
            return {"hand": HAND, "recorded": len(body["fassungen"]), "skipped": 0}
        return {}

    def pushed(self) -> list[dict]:
        return [body for method, url, body in self.calls if method == "PUT" and url.split("?")[0].endswith("/pfade")]


def _pull_pfade(monkeypatch, fake: _FakePfadApi) -> int:
    monkeypatch.setattr(pull_mod, "request_json", fake)
    monkeypatch.setenv("ADMIN_TOKEN", "t")
    return pull_mod.main(["--hand", HAND, "--pfade", "--api", "https://example.test"])


def _record(strip: str = "S0001", fassung: str = "F01") -> dict | None:
    from tools.eigenhand.kartei import fassung_record

    return fassung_record(load_kartei(HAND), strip, fassung)


class TestHandDrawnBahnChain:
    """`pull --pfade → snapshot → sync --from` — the one datum that runs upward.

    Scan, verdict and Fleckenmaske are made at this desk and pushed, so an
    archive run simply picks up the working copy. A Bahn the author traces in
    the workbench is the opposite: it is born in the shared database, nothing
    can follow it again, and neither the own-hand archive nor the DB snapshot
    carried it. These tests pin the chain that closes that gap — and, above
    all, that it closes LOUDLY when it does not.
    """

    def test_the_drawing_lands_in_the_kartei_with_both_its_formats(self, dataroot, monkeypatch, capsys):
        from tools.eigenhand.kartei import PFAD_ARCHIVE_FORMAT

        _build(dataroot)
        assert _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): [_bahn()]})) == 0
        stored = _record()["pfade"]
        assert stored["entries"] == [_bahn()]
        # Two versions, on purpose: the envelope says how to READ this file,
        # `pfad_format` says what the entries inside it mean — and a restore
        # has to declare the second one back to the API.
        assert stored["format"] == PFAD_ARCHIVE_FORMAT
        assert stored["pfad_format"] == 1
        assert "snapshot" in capsys.readouterr().out

    def test_a_followed_path_is_a_derivation_and_is_left_up_there(self, dataroot, monkeypatch):
        # Strip, layout and follower are all in the archive, so a followed path
        # is re-made rather than restored; filing it would put a second truth
        # beside the one that regenerates it.
        _build(dataroot)
        _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): [_bahn(verfahren="tintenpfad")]}))
        assert "pfade" not in _record()

    def test_a_followed_path_whose_boundaries_were_corrected_by_hand_comes_down(self, dataroot, monkeypatch):
        # The second piece of hand work a box can hold, and the one this
        # format adds: a corrected letter boundary cannot be followed again
        # either, the server protects it as its own field, and the only
        # Ziehweg filtered on the BAHN's `verfahren` alone — so it would have
        # had no way into the archive at all (review, PR #639).
        _build(dataroot)
        corrected = _bahn(
            verfahren="tintenpfad",
            letter_spans=[{"stroke": 0, "slot": 0, "first": 0, "last": 2, "herkunft": "authored"}],
        )
        _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): [corrected]}, declared=2))
        assert _record()["pfade"]["entries"] == [corrected]
        assert _record()["pfade"]["pfad_format"] == 2

    def test_a_boundary_the_follower_assigned_is_still_a_derivation(self, dataroot, monkeypatch):
        # `auto` is the run's own work, like the Bahn under it. Pulling those
        # too would file every followed path in the Kartei.
        _build(dataroot)
        auto = _bahn(
            verfahren="tintenpfad", letter_spans=[{"stroke": 0, "slot": 0, "first": 0, "last": 2, "herkunft": "auto"}]
        )
        _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): [auto]}, declared=2))
        assert "pfade" not in _record()

    def test_a_fassung_the_server_holds_no_drawing_for_keeps_its_copy(self, dataroot, monkeypatch, capsys):
        # Never deletes: after `--replace-authored` the local copy IS the only
        # remaining one, and that is precisely the copy this chain exists for.
        _build(dataroot)
        _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): [_bahn()]}))
        capsys.readouterr()
        _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): []}))
        assert _record()["pfade"]["entries"] == [_bahn()]
        # And it is named here too, not only when SOME box is still answered.
        assert "S0001/F01 box 0" in capsys.readouterr().out

    def test_one_given_up_box_does_not_take_its_neighbour_with_it(self, dataroot, monkeypatch, capsys):
        """„Never deletes" has to hold per BOX, not per Fassung.

        The author hands box 0 to a follower and keeps drawing box 1, so the
        server answers with box 1 alone. Writing that answer as the record
        would drop the only remaining copy of box 0 (Copilot review, PR #635).
        """
        _build(dataroot)
        both = [_bahn(box=0), _bahn(box=1, word="das")]
        _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): both}))
        capsys.readouterr()
        _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): [_bahn(box=1, word="das")]}))
        assert _record()["pfade"]["entries"] == both
        # And the operator is told, because the Kartei is now the last copy.
        assert "S0001/F01 box 0" in capsys.readouterr().out

    def test_a_retained_box_under_an_older_wire_format_stops_rather_than_mislabels(self, dataroot, monkeypatch):
        # One record declares ONE format. Carrying an entry written under the
        # old one under a new declaration would mislabel it, and dropping it
        # would lose it — so the Fassung is left alone and named.
        _build(dataroot)
        _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): [_bahn(box=0), _bahn(box=1, word="das")]}))
        newer = _FakePfadApi({("S0001", "F01"): [_bahn(box=1, word="das")]}, declared=2)
        with pytest.raises(SystemExit, match="under an OLDER"):
            _pull_pfade(monkeypatch, newer)
        assert _record()["pfade"]["pfad_format"] == 1  # untouched, nothing lost

    def test_a_drawing_whose_fassung_this_machine_does_not_know_ends_the_run_loudly(self, dataroot, monkeypatch):
        _build(dataroot)
        fake = _FakePfadApi({("S0001", "F01"): [_bahn()], ("S0002", "F01"): [_bahn(word="das")]})
        with pytest.raises(SystemExit, match="S0002/F01"):
            _pull_pfade(monkeypatch, fake)
        # Everything that COULD be filed was filed before the run failed.
        assert _record()["pfade"]["entries"] == [_bahn()]

    def test_an_answer_that_declares_no_format_is_refused(self, dataroot, monkeypatch):
        _build(dataroot)
        with pytest.raises(SystemExit, match="declared no Streifen-Pfad format"):
            _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): [_bahn()]}, declared=None))

    def test_the_drawing_rides_in_the_next_snapshot_of_an_ALREADY_archived_fassung(
        self, dataroot, tmp_path, monkeypatch
    ):
        """Why the Kartei is the landing place (author decision A, 2026-09-20).

        `snapshot.py` treats a filed Fassung directory as one immutable copy
        unit and skips it by relative path, so a file written into an
        already-archived Fassung would never reach the archive while the run
        still reported success. The Kartei escapes that because it is copied in
        FULL every time — this test is the proof, not the assumption.
        """
        archive = tmp_path / "archive"
        archive.mkdir()
        _build(dataroot)
        snapshot_mod.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])

        _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): [_bahn()]}))
        snapshot_mod.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0002"])

        second = archive / "own-hand" / HAND / "0002"
        # The Fassung directory really was skipped as an immutable unit …
        assert not (second / "fassungen" / "S0001").exists()
        # … and the drawing still made it into the archive, through the Kartei.
        kartei = json.loads((second / "kartei.json").read_text(encoding="utf-8"))
        assert kartei["strips"]["S0001"]["fassungen"][0]["pfade"]["entries"] == [_bahn()]

    def _archived(self, dataroot, tmp_path, monkeypatch, bahnen: list[dict] | None = None):
        """A hand with one filed Fassung whose drawing has been pulled and archived."""
        archive = tmp_path / "archive"
        archive.mkdir()
        _build(dataroot)
        if bahnen is not None:
            _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): bahnen}))
        snapshot_mod.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])
        return archive / "own-hand" / HAND / "0001"

    def test_an_ordinary_sync_pushes_no_drawing(self, dataroot, tmp_path, monkeypatch):
        # A Bahn is not bookkeeping this machine owns. Pushing the pulled copy
        # on every sync would quietly resurrect a drawing the author gave up on
        # purpose with `--replace-authored`.
        self._archived(dataroot, tmp_path, monkeypatch, [_bahn()])
        fake = _FakePfadApi({("S0001", "F01"): []})
        assert _run(monkeypatch, fake) == 0
        assert fake.pushed() == []

    def test_the_restore_puts_the_drawing_back_under_its_own_format(self, dataroot, tmp_path, monkeypatch, capsys):
        snapshot = self._archived(dataroot, tmp_path, monkeypatch, [_bahn()])
        _wipe(dataroot / HAND / "fassungen")
        fake = _FakePfadApi({("S0001", "F01"): []})
        assert _run(monkeypatch, fake, "--mit-streifen", "--from", str(snapshot)) == 0
        assert fake.pushed() == [{"format": 1, "pfade": [_bahn()]}]
        assert "1 restored, 0 already there, 0 NOT restored" in capsys.readouterr().out

    def test_the_restore_keeps_the_boxes_the_server_already_holds(self, dataroot, tmp_path, monkeypatch):
        # The write is a FULL replacement per Fassung, so the archived box goes
        # up BESIDE whatever else is stored — otherwise restoring one drawing
        # would delete the followed paths of the rest of the row.
        snapshot = self._archived(dataroot, tmp_path, monkeypatch, [_bahn()])
        followed = _bahn(box=1, word="das", verfahren="tintenpfad")
        fake = _FakePfadApi({("S0001", "F01"): [followed]})
        assert _run(monkeypatch, fake, "--mit-streifen", "--from", str(snapshot)) == 0
        assert [entry["box_index"] for entry in fake.pushed()[0]["pfade"]] == [0, 1]

    def test_a_live_box_written_under_a_newer_format_rides_up_declared_as_such(self, dataroot, tmp_path, monkeypatch):
        # Because the body is a MERGE, a box the archive knows nothing about
        # travels up with it — and declaring the ARCHIVE's older number over a
        # format-2 entry is a 422 that kills the restore on a box it was not
        # even asked to change (review, PR #639). The declaration follows the
        # content, and only ever upward: a format-1 entry is a valid format-2
        # one, while the reverse is the mislabelling the marker exists to stop.
        snapshot = self._archived(dataroot, tmp_path, monkeypatch, [_bahn()])
        skipped = {
            "box_index": 1,
            "word": "das",
            "status": "skipped",
            "grund": "gave_up",
            "strokes": [],
            "verfahren": "tintenpfad",
        }
        fake = _FakePfadApi({("S0001", "F01"): [skipped]}, declared=2)
        assert _run(monkeypatch, fake, "--mit-streifen", "--from", str(snapshot)) == 0
        pushed = fake.pushed()[0]
        assert pushed["format"] == 2
        assert [entry["box_index"] for entry in pushed["pfade"]] == [0, 1]

    def test_a_normalised_answer_still_counts_as_restored(self, dataroot, tmp_path, monkeypatch, capsys):
        # The server fills in the format-2 keys on a format-1 entry it accepts,
        # which is the format doing its job. Exact dict equality read that as
        # „stored changed, or not at all" and ended an otherwise perfect
        # restore with a loud failure (review, PR #639).
        snapshot = self._archived(dataroot, tmp_path, monkeypatch, [_bahn()])
        skipped = {
            "box_index": 1,
            "word": "das",
            "status": "skipped",
            "grund": "gave_up",
            "strokes": [],
            "verfahren": "tintenpfad",
        }
        fake = _FakePfadApi({("S0001", "F01"): [skipped]}, declared=2)
        assert _run(monkeypatch, fake, "--mit-streifen", "--from", str(snapshot)) == 0
        assert "1 restored, 0 already there, 0 NOT restored" in capsys.readouterr().out
        # …and a Bahn the server really did change is still caught.
        changed = _FakePfadApi({("S0001", "F01"): []}, declared=1, swallow=True)
        with pytest.raises(SystemExit, match="NOT restored"):
            _run(monkeypatch, changed, "--mit-streifen", "--from", str(snapshot))

    def test_a_drawing_whose_strip_is_not_up_there_ends_the_restore_loudly(self, dataroot, tmp_path, monkeypatch):
        # THE failure this PR exists to prevent: a restore that reports success
        # while a drawing nothing can follow again stays missing.
        snapshot = self._archived(dataroot, tmp_path, monkeypatch, [_bahn()])
        fake = _FakePfadApi({}, rows=[])
        with pytest.raises(SystemExit, match="1 hand-drawn Bahn\\(en\\) are NOT restored"):
            _run(monkeypatch, fake, "--from", str(snapshot))

    def test_a_second_restore_recognises_the_drawing_it_already_put_back(self, dataroot, tmp_path, monkeypatch, capsys):
        snapshot = self._archived(dataroot, tmp_path, monkeypatch, [_bahn()])
        fake = _FakePfadApi({("S0001", "F01"): []})
        _run(monkeypatch, fake, "--mit-streifen", "--from", str(snapshot))
        capsys.readouterr()
        assert _run(monkeypatch, fake, "--mit-streifen", "--from", str(snapshot)) == 0
        assert "0 restored, 1 already there, 0 NOT restored" in capsys.readouterr().out
        assert len(fake.pushed()) == 1

    def test_an_archive_without_a_drawing_says_so_rather_than_nothing(self, dataroot, tmp_path, monkeypatch, capsys):
        # „The archive carries none" and „this hand never had one" look
        # identical from here, and only one of them is fine.
        snapshot = self._archived(dataroot, tmp_path, monkeypatch)
        fake = _FakePfadApi({("S0001", "F01"): []})
        assert _run(monkeypatch, fake, "--mit-streifen", "--from", str(snapshot)) == 0
        assert "none in this archive" in capsys.readouterr().out

    def test_an_older_stamp_still_restores_the_drawing_pulled_into_a_newer_one(
        self, dataroot, tmp_path, monkeypatch, capsys
    ):
        """The Kartei comes from the NEWEST snapshot, whichever one is named.

        Every snapshot carries a complete Kartei, so an older one is a complete
        record of an EARLIER state. Reading the named directory would restore
        that earlier state — and since a Bahn now rides in the Kartei and
        nowhere else, a `--from` pointed one stamp too far back would report a
        clean run with the drawing still missing (found in review, PR #634).
        """
        archive = tmp_path / "archive"
        archive.mkdir()
        _build(dataroot)
        snapshot_mod.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])
        _pull_pfade(monkeypatch, _FakePfadApi({("S0001", "F01"): [_bahn()]}))
        snapshot_mod.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0002"])
        capsys.readouterr()

        older = archive / "own-hand" / HAND / "0001"
        fake = _FakePfadApi({("S0001", "F01"): []})
        assert _run(monkeypatch, fake, "--mit-streifen", "--from", str(older)) == 0
        assert fake.pushed() == [{"format": 1, "pfade": [_bahn()]}]
        out = capsys.readouterr().out
        assert "1 restored, 0 already there, 0 NOT restored" in out
        assert "Kartei read from 0002" in out  # and it says which one it read

    def test_a_box_the_server_answers_differently_is_left_alone(self, dataroot, tmp_path, monkeypatch, capsys):
        """A given-up box is not resurrected by the next restore.

        `--replace-authored` is how the author hands a drawing over to a
        follower, deliberately. The Kartei keeps the last copy (it never
        deletes), so without this rule every later `sync --from` would push the
        drawing back over the followed path and revert that decision silently —
        and re-arm the 409 on a box that now carries a follow (review, PR #634).
        The same rule protects a drawing he CORRECTED in the workbench after the
        last pull.
        """
        snapshot = self._archived(dataroot, tmp_path, monkeypatch, [_bahn()])
        given_up = _bahn(verfahren="tintenpfad")
        fake = _FakePfadApi({("S0001", "F01"): [given_up]})
        assert _run(monkeypatch, fake, "--mit-streifen", "--from", str(snapshot)) == 0
        assert fake.pushed() == []
        out = capsys.readouterr().out
        assert "0 restored, 0 already there, 1 left as the server has them, 0 NOT restored" in out
        assert "S0001/F01 box 0" in out

    def test_a_restore_the_server_answers_short_of_counts_as_not_restored(
        self, dataroot, tmp_path, monkeypatch
    ) -> None:
        # The closing line is the one number this chain is judged by, so it is
        # read off the ANSWER rather than off the request (review, PR #634).
        snapshot = self._archived(dataroot, tmp_path, monkeypatch, [_bahn()])
        fake = _FakePfadApi({("S0001", "F01"): []}, swallow=True)
        with pytest.raises(SystemExit, match="1 hand-drawn Bahn\\(en\\) are NOT restored"):
            _run(monkeypatch, fake, "--mit-streifen", "--from", str(snapshot))

    def test_a_kartei_from_an_older_shape_stays_readable(self, monkeypatch):
        """An archived Kartei is never rewritten, so old shapes stay readable.

        `snapshot.py` is create-only and „never destroy" is an author
        directive, so there is no place a shape-1 record inside a filed
        snapshot could be migrated. Refusing it on the first bump of
        `PFAD_ARCHIVE_FORMAT` would orphan every snapshot taken before that
        bump (review, PR #634); only a NEWER shape is refused.
        """
        from tools.eigenhand import kartei as kartei_mod

        old = {"id": "F01", "pfade": kartei_mod.pfad_record([_bahn()], 1, "2026-09-20")}
        monkeypatch.setattr(kartei_mod, "PFAD_ARCHIVE_FORMAT", 2)
        assert kartei_mod.pfade_of(old) == [_bahn()]

        newer = {"id": "F01", "pfade": {**old["pfade"], "format": 3}}
        with pytest.raises(SystemExit, match="written by a NEWER tool"):
            kartei_mod.pfade_of(newer)


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
