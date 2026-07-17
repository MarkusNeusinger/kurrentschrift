"""HTTP tests for the public word-sample reads (words.json sidecar + crops)."""

from __future__ import annotations

import json
from io import BytesIO

import numpy as np
from PIL import Image

from core.chart import load_word_samples


def _make_plate(path, w=200, h=100):
    """A white plate with a black 10px column at x=[50, 60) spanning full height."""
    arr = np.full((h, w), 255, dtype=np.uint8)
    arr[:, 50:60] = 0
    Image.fromarray(arr, mode="L").save(path)


def _sidecar(tmp_path, words: list[dict]) -> str:
    """Write plate + words.json into tmp_path; return the chart_path to seed."""
    _make_plate(tmp_path / "plate.png")
    (tmp_path / "words.json").write_text(json.dumps({"words": words}), encoding="utf-8")
    # The chart raster itself need not exist — the sidecar sits next to it.
    return str(tmp_path / "chart.png")


WORD = {
    "word": "unter",
    "page": "plate.png",
    "x0": 40,
    "x1": 120,
    "y0": 10,
    "y1": 90,
    "baseline_y": 70,
    "midband_y": 40,
}


async def test_list_word_samples(api, tmp_path):
    chart_path = _sidecar(
        tmp_path,
        [
            WORD,
            {**WORD, "id": "unter-2", "kind": "pair"},
            {**WORD, "id": "abc", "set": "abb22"},
            {**WORD, "id": "emptyset", "set": "  "},
            {"word": "malformed"},  # missing rect/page — skipped, not 500
        ],
    )
    _, source_id = await api.seed_style_and_source(chart_path=chart_path)
    res = await api.client.request("GET", f"/sources/{source_id}/word-samples")
    assert res.status == 200
    assert "max-age" in res.headers.get("cache-control", "")
    rows = res.json()
    assert [r["id"] for r in rows] == ["unter", "unter-2", "abc", "emptyset"]
    first = rows[0]
    assert first["word"] == "unter"
    assert first["kind"] == "word"
    assert first["sample_set"] is None
    assert (first["width"], first["height"]) == (80, 80)
    # Lineature is crop-local: page 70/40 minus y0=10.
    assert (first["baseline_y"], first["midband_y"]) == (60, 30)
    assert rows[1]["kind"] == "pair"
    assert rows[2]["sample_set"] == "abb22"
    # A whitespace-only set tag normalizes to null — it must not classify the
    # row as another hand.
    assert rows[3]["sample_set"] is None


async def test_list_word_samples_empty_without_sidecar(api, tmp_path):
    _, source_id = await api.seed_style_and_source(chart_path=str(tmp_path / "chart.png"))
    res = await api.client.request("GET", f"/sources/{source_id}/word-samples")
    assert res.status == 200
    assert res.json() == []


async def test_list_word_samples_invalid_sidecar_json(api, tmp_path):
    (tmp_path / "words.json").write_text("{not json", encoding="utf-8")
    _, source_id = await api.seed_style_and_source(chart_path=str(tmp_path / "chart.png"))
    res = await api.client.request("GET", f"/sources/{source_id}/word-samples")
    assert res.status == 200
    assert res.json() == []


def test_load_word_samples_hardening(tmp_path):
    """Traversal pages, malformed numbers and degenerate rects are skipped."""
    (tmp_path / "words.json").write_text(
        json.dumps(
            {
                "words": [
                    {**WORD, "id": "ok"},
                    {**WORD, "id": "traversal", "page": "../secret.png"},
                    {**WORD, "id": "abs", "page": "/etc/passwd"},
                    {**WORD, "id": "badnum", "x0": "wide"},
                    {**WORD, "id": "inverted", "x1": WORD["x0"]},
                    {**WORD, "id": "flatband", "midband_y": WORD["baseline_y"]},
                    "not-a-dict",
                ]
            }
        ),
        encoding="utf-8",
    )
    rows = load_word_samples(tmp_path / "chart.png")
    assert [r["id"] for r in rows] == ["ok"]


async def test_word_sample_crop_png_and_excludes(api, tmp_path):
    exclude_word = {**WORD, "id": "ex", "exclude": [[40, 10, 120, 90]]}  # blank the whole crop
    chart_path = _sidecar(tmp_path, [WORD, exclude_word])
    _, source_id = await api.seed_style_and_source(chart_path=chart_path)

    res = await api.client.request("GET", f"/sources/{source_id}/word-samples/unter/crop")
    assert res.status == 200
    assert res.headers["content-type"] == "image/png"
    img = np.array(Image.open(BytesIO(res.body)))
    assert img.shape == (80, 80)
    # The plate's ink column (page x=[50, 60)) lands at crop x=[10, 20).
    assert img[:, 10:20].max() < 30
    assert img[:, 30:].min() > 200

    res = await api.client.request("GET", f"/sources/{source_id}/word-samples/ex/crop")
    blanked = np.array(Image.open(BytesIO(res.body)))
    assert blanked.min() > 200  # exclude painted paper-white over the ink


async def test_word_sample_crop_404(api, tmp_path):
    chart_path = _sidecar(tmp_path, [WORD])
    _, source_id = await api.seed_style_and_source(chart_path=chart_path)
    res = await api.client.request("GET", f"/sources/{source_id}/word-samples/nope/crop")
    assert res.status == 404


async def test_word_sample_crop_failures_are_404_not_500(api, tmp_path):
    """Hand-maintained-data breakage — rect outside the plate, missing plate
    file — answers 404 on the public read instead of 500."""
    outside = {**WORD, "id": "outside", "x0": 500, "x1": 600, "baseline_y": 70, "midband_y": 40}
    lost_plate = {**WORD, "id": "lost", "page": "gone.png"}
    chart_path = _sidecar(tmp_path, [outside, lost_plate])
    _, source_id = await api.seed_style_and_source(chart_path=chart_path)
    for sample_id in ("outside", "lost"):
        res = await api.client.request("GET", f"/sources/{source_id}/word-samples/{sample_id}/crop")
        assert res.status == 404, sample_id


def test_load_word_samples_missing_sidecar(tmp_path):
    assert load_word_samples(tmp_path / "chart.png") == []
