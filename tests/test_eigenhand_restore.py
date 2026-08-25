"""The restore guarantee: repo + private archive rebuild the own-hand tables.

The owner's requirement (2026-08-24) is blunt — if the database is gone, the
public repository plus the private archive have to bring back both the
important table contents AND the strips as images. This test is that promise,
executed: the whole local chain runs (print → rasterise → ingest → Siebung →
apply → archive snapshot), the local data root is then WIPED, and the restore
runs out of the archive alone against a database that has never seen this hand.

The API is the real one — the app, its validation, its refusals — reached
through the in-process ASGI harness instead of the network. `sync` runs in a
worker thread and hands its HTTP calls back to the test's event loop, so what
is exercised is the client an operator would actually run, not a re-write of it.

Proves: every Bogen, verdict and strip comes back; the strips come back
byte-identical (sha256 against the archived files); a word crop can be cut out
of a RESTORED strip, which is the check that the geometry survived too; and the
restore is idempotent — running it a second time changes nothing.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from tests.api_harness import Harness
from tools.eigenhand import apply as apply_mod
from tools.eigenhand import ingest as ingest_mod
from tools.eigenhand import sheet as sheet_mod
from tools.eigenhand import snapshot as snapshot_mod
from tools.eigenhand import sync as sync_mod
from tools.eigenhand.rasterize import mm_to_px, rasterize_layout
from tools.eigenhand.store import hand_dir


HAND = "test-suetterlin"
DATE = "2026-08-24"
SHEET = "B0001"
ROWS = 2


@pytest.fixture
def dataroot(tmp_path, monkeypatch) -> Path:
    monkeypatch.setenv("EIGENHAND_DATA", str(tmp_path / "own-hand"))
    return tmp_path / "own-hand"


def _write_by_hand(layout: dict, dpi: float = 300.0) -> Image.Image:
    """Rasterise the Bogen and put ink in its boxes — a stand-in for writing.

    Straight lines, not letters: what has to survive the round trip is the
    GEOMETRY (which strip, which row, which millimetres), and a scribble that
    lands inside the right box tests that as well as a real word would.
    """
    image = rasterize_layout(layout, dpi=dpi)
    draw = ImageDraw.Draw(image)
    for row in layout["rows"]:
        band = row["band_mm"]
        for box in row["boxes"]:
            draw.line(
                [
                    mm_to_px(box["x0_mm"] + 1.0, dpi),
                    mm_to_px(band["baseline"], dpi),
                    mm_to_px(box["x1_mm"] - 1.0, dpi),
                    mm_to_px(band["waist"], dpi),
                ],
                fill=20,
                width=6,
            )
    return image


def _capture(dataroot: Path) -> dict:
    """Print a Bogen, „write" it, ingest it, accept every row, file the Fassungen."""
    sheet_mod.main(["--hand", HAND, "--date", DATE, "--rows", str(ROWS)])
    sheet_dir = hand_dir(HAND) / "blaetter" / SHEET
    layout = json.loads((sheet_dir / "layout.json").read_text(encoding="utf-8"))

    scan = dataroot / "scan.png"
    _write_by_hand(layout).save(scan)
    ingest_mod.main([str(scan), "--hand", HAND, "--sheet", SHEET])

    payload = json.loads((sheet_dir / "import" / "payload.json").read_text(encoding="utf-8"))
    lines = [f"{row['uid']}:angenommen" for row in payload["rows"]]
    result = dataroot / f"siebung-{SHEET}.txt"
    result.write_text(
        f"SIEBUNG/1 bogen={SHEET} geprueft={len(lines)} von {len(lines)}\n" + "\n".join(lines) + "\n", encoding="utf-8"
    )
    apply_mod.main([str(result), "--hand", HAND, "--sheet", SHEET])
    return layout


def _archive_snapshot(tmp_path: Path) -> Path:
    archive = tmp_path / "archive"
    archive.mkdir(exist_ok=True)
    snapshot_mod.main(["--hand", HAND, "--archive", str(archive), "--stamp", "0001"])
    return archive / "own-hand" / HAND / "0001"


def _bridge(api: Harness, loop: asyncio.AbstractEventLoop):
    """Route the sync client's calls into the in-process app from a worker thread."""
    base = "http://testserver"

    def request_json(method: str, url: str, token: str, body: dict | None = None, allow_404: bool = False):
        path = url[len(base) :] if url.startswith(base) else url
        future = asyncio.run_coroutine_threadsafe(
            api.client.request(method, path, json_body=body, headers=api.admin_headers()), loop
        )
        res = future.result(timeout=60)
        if res.status == 404 and allow_404:
            return None
        if res.status >= 400:
            raise SystemExit(f"{method} {path} → {res.status}: {res.body[:400]!r}")
        return res.json()

    return request_json


async def _restore(api: Harness, snapshot: Path, monkeypatch) -> None:
    monkeypatch.setattr(sync_mod, "request_json", _bridge(api, asyncio.get_running_loop()))
    monkeypatch.setenv("ADMIN_TOKEN", "irrelevant — the bridge carries the harness header")
    await asyncio.to_thread(
        sync_mod.main, ["--hand", HAND, "--api", "http://testserver", "--from", str(snapshot), "--mit-streifen"]
    )


async def _restored(api: Harness) -> dict:
    res = await api.client.request("GET", f"/eigenhand/archive/{HAND}", headers=api.admin_headers())
    assert res.status == 200, res.body
    return res.json()


class TestRestoreFromArchive:
    @pytest.mark.asyncio
    async def test_the_archive_alone_rebuilds_the_tables_and_the_images(
        self, api: Harness, dataroot: Path, tmp_path: Path, monkeypatch
    ):
        layout = _capture(dataroot)
        snapshot = _archive_snapshot(tmp_path)
        archived = {
            f"{path.parent.parent.name}/{path.parent.name}": hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((snapshot / "fassungen").glob("*/*/streifen.png"))
        }
        assert len(archived) == ROWS

        # The machine that held the data is gone. Only repo + archive remain.
        shutil.rmtree(dataroot)
        await _restore(api, snapshot, monkeypatch)

        data = await _restored(api)
        assert [row["sheet"] for row in data["sheets"]] == [SHEET]
        assert data["sheets"][0]["layout_sha256"]
        assert data["sheets"][0]["strips"] == [row["strip"] for row in layout["rows"]]
        assert len(data["fassungen"]) == ROWS
        assert {row["status"] for row in data["fassungen"]} == {"angenommen"}
        # Byte-identical, checked the way the manifest asks for it.
        assert {f"{row['strip']}/{row['fassung']}": row["sha256"] for row in data["strips"]} == archived
        # And the layout came back with them, or no crop could ever be cut again.
        assert data["sheets"][0]["layout"]["rows"][0]["boxes"] == layout["rows"][0]["boxes"]

    @pytest.mark.asyncio
    async def test_a_word_crop_can_be_cut_out_of_a_restored_strip(
        self, api: Harness, dataroot: Path, tmp_path: Path, monkeypatch
    ):
        layout = _capture(dataroot)
        snapshot = _archive_snapshot(tmp_path)
        shutil.rmtree(dataroot)
        await _restore(api, snapshot, monkeypatch)

        data = await _restored(api)
        strip = data["strips"][0]
        word = layout["rows"][strip["row_index"]]["boxes"][0]["word"]
        cut = await api.client.request(
            "GET",
            f"/eigenhand/strips/{HAND}/{strip['strip']}/{strip['fassung']}",
            params={"wort": word},
            headers=api.admin_headers(),
        )
        assert cut.status == 200, cut.body
        with Image.open(io.BytesIO(cut.body)) as image:
            width, height = image.size
            darkest = image.getextrema()[0]
        # Narrower than the strip, full height, and it carries ink — the crop
        # landed on the writing, not next to it.
        assert 0 < width < strip["width_px"]
        assert height == strip["height_px"]
        assert darkest < 128, "the word crop is blank — the mm→px arithmetic missed the box"

    @pytest.mark.asyncio
    async def test_restoring_twice_changes_nothing(self, api: Harness, dataroot: Path, tmp_path: Path, monkeypatch):
        _capture(dataroot)
        snapshot = _archive_snapshot(tmp_path)
        shutil.rmtree(dataroot)
        await _restore(api, snapshot, monkeypatch)
        first = await _restored(api)
        await _restore(api, snapshot, monkeypatch)
        assert await _restored(api) == first
