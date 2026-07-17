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


# ------------------------------------------------------------ specimen scores


async def test_word_sample_score_requires_admin(api, tmp_path):
    chart_path = _sidecar(tmp_path, [WORD])
    _, source_id = await api.seed_style_and_source(chart_path=chart_path)
    res = await api.client.request("GET", f"/sources/{source_id}/word-samples/unter/score")
    assert res.status == 401


async def test_word_sample_score_404_unknown_sample(api, tmp_path):
    chart_path = _sidecar(tmp_path, [WORD])
    _, source_id = await api.seed_style_and_source(chart_path=chart_path)
    res = await api.client.request("GET", f"/sources/{source_id}/word-samples/nope/score", headers=api.admin_headers())
    assert res.status == 404


async def test_word_sample_score_missing_template_fails_not_500(api, tmp_path):
    """A specimen whose word has no authored template scores 1.0/failed —
    a hole is a failure, not an error (mirrors the bench crash rule)."""
    chart_path = _sidecar(tmp_path, [{**WORD, "id": "nn", "word": "nn"}])
    _, source_id = await api.seed_style_and_source(chart_path=chart_path)
    res = await api.client.request("GET", f"/sources/{source_id}/word-samples/nn/score", headers=api.admin_headers())
    assert res.status == 200
    body = res.json()
    assert body["failed"] is True
    assert body["loss"] == 1.0
    assert body["missing"] == ["n"]
    assert body["segments"] == []


async def test_word_sample_score_success_with_segments(api, tmp_path):
    """Structural contract of a scored specimen: bounded loss + components,
    registration, and provenance-labelled per-segment attribution rows."""
    chart_path = _sidecar(tmp_path, [{**WORD, "id": "nn", "word": "nn"}])
    style_id, source_id = await api.seed_style_and_source(chart_path=chart_path)
    await api.seed_template(style_id, source_id, "n", "n")

    res = await api.client.request("GET", f"/sources/{source_id}/word-samples/nn/score", headers=api.admin_headers())
    assert res.status == 200
    body = res.json()
    assert body["id"] == "nn"
    assert body["word"] == "nn"
    assert body["failed"] is False
    assert 0.0 <= body["loss"] <= 1.0
    for comp in ("transition", "coverage", "width"):
        assert 0.0 <= body[comp] <= 1.0
    assert body["registration"]["xh_px"] == 30.0
    # Scores must not be cached — they move with every template/pair write.
    assert "cache-control" not in res.headers

    segments = body["segments"]
    kinds = [s["kind"] for s in segments]
    # nn = glyph + generated connector + glyph, labelled via compose provenance.
    assert kinds == ["glyph", "connector", "glyph"]
    assert [s.get("glyph_key") for s in segments if s["kind"] == "glyph"] == ["n", "n"]
    connector = segments[kinds.index("connector")]
    assert connector["pair"] == ["n", "n"]
    for s in segments:
        assert 0.0 <= s["penalty"] <= 1.0


async def test_word_sample_score_lost_plate_is_404_not_500(api, tmp_path):
    chart_path = _sidecar(tmp_path, [{**WORD, "id": "lost", "page": "gone.png"}])
    style_id, source_id = await api.seed_style_and_source(chart_path=chart_path)
    await api.seed_template(style_id, source_id, "u", "u")
    res = await api.client.request("GET", f"/sources/{source_id}/word-samples/lost/score", headers=api.admin_headers())
    assert res.status == 404
