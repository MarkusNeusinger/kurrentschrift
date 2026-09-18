"""`GET /sources/{id}/write/glyphs/{glyph_key}.svg` — one written glyph as an
SVG image (api/glyph_svg.py), the picture next to the JSON number list."""

from __future__ import annotations

from api.glyph_svg import glyph_svg, polyline_to_path_d, rings_to_path_d, word_svg
from tests.api_harness import Harness


# ------------------------------------------------------------------ word.svg


async def test_word_svg_draws_glyphs_and_connectors(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    res = await api.client.request("GET", f"/sources/{source_id}/write/word.svg", params={"text": " nn "})
    assert res.status == 200, res.body
    assert res.headers["content-type"].startswith("image/svg+xml")
    # Browser cache only — an edge HIT would never reach the fetch counter.
    assert res.headers["cache-control"] == "private, max-age=300"
    body = res.body.decode()
    assert body.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="')
    assert body.count('fill-rule="evenodd"') == 2  # two letters, filled
    assert 'fill="none" stroke="#2b2419"' in body and 'stroke-linecap="round"' in body  # the generated join
    assert "<title>nn — Synthetic test chart</title>" in body
    assert body.count("<line ") == 4


async def test_word_svg_404_when_nothing_can_be_written(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("GET", f"/sources/{source_id}/write/word.svg", params={"text": "zz"})
    assert res.status == 404
    assert "no canonical for z" in res.json()["detail"]


async def test_word_svg_shares_the_word_input_contract(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("GET", f"/sources/{source_id}/write/word.svg", params={"text": "   "})
    assert res.status == 422
    res = await api.client.request("GET", f"/sources/{source_id}/write/word.svg", params={"text": "x" * 161})
    assert res.status == 422


async def test_word_path_form_answers_like_the_query_form(api: Harness):
    """`/write/word/{text}` and `/write/word/{text}.svg` — the text as a path
    segment, for clients that drop query strings — return exactly what the
    query form returns for the same text, and route the `.svg` suffix to the
    picture rather than composing it as letters."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")

    by_query = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "nn"})
    by_path = await api.client.request("GET", f"/sources/{source_id}/write/word/nn")
    assert by_path.status == 200, by_path.body
    assert by_path.headers["content-type"].startswith("application/json")
    assert by_path.headers["cache-control"] == by_query.headers["cache-control"]
    assert by_path.json() == by_query.json()
    assert by_path.json()["text"] == "nn"

    svg_by_query = await api.client.request("GET", f"/sources/{source_id}/write/word.svg", params={"text": "nn"})
    svg_by_path = await api.client.request("GET", f"/sources/{source_id}/write/word/nn.svg")
    assert svg_by_path.status == 200, svg_by_path.body
    assert svg_by_path.headers["content-type"].startswith("image/svg+xml")
    assert svg_by_path.headers["cache-control"] == "private, max-age=300"
    assert svg_by_path.body == svg_by_query.body
    assert "<title>nn — Synthetic test chart</title>" in svg_by_path.body.decode()


async def test_word_path_form_shares_the_input_contract_and_the_404(api: Harness):
    _, source_id = await api.seed_style_and_source()
    # The harness hands the path percent-DECODED, as an ASGI server would.
    res = await api.client.request("GET", f"/sources/{source_id}/write/word/  ")
    assert res.status == 422
    assert res.json()["detail"] == "text must contain at least one non-space character"
    res = await api.client.request("GET", f"/sources/{source_id}/write/word/{'x' * 161}")
    assert res.status == 422
    res = await api.client.request("GET", f"/sources/{source_id}/write/word/zz.svg")
    assert res.status == 404
    assert "no canonical for z" in res.json()["detail"]


async def test_word_path_form_reads_a_trailing_svg_as_the_picture(api: Harness):
    """The documented ambiguity of the path form: `.svg` is the shape, never
    part of the text — `/word/n.svg` is the picture of "n", and the text
    "n.svg" itself is only reachable through the query form."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    res = await api.client.request("GET", f"/sources/{source_id}/write/word/n.svg")
    assert res.status == 200
    assert res.headers["content-type"].startswith("image/svg+xml")
    assert "<title>n — Synthetic test chart</title>" in res.body.decode()
    by_query = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": "n.svg"})
    assert by_query.status == 200
    assert by_query.json()["text"] == "n.svg"


def test_word_svg_renders_items_on_the_ruling():
    composed = {
        "items": [
            {"glyph_key": "n", "rings": [[[0, 0], [0.4, 0], [0.4, 1], [0, 1]]], "centerline": [[0, 0], [0.4, 1]]},
            {"centerline": [[0.4, 0.5], [0.8, 0.2]], "stroke_width": 0.05, "lift": False},
        ],
        "bounds": {"min_x": 0.0, "max_x": 0.8, "min_y": 0.0, "max_y": 1.0},
        "guides": {"baseline": 0.0, "midband": 1.0, "ascender": 2.0, "descender": -1.0},
    }
    svg = word_svg(composed, name="nn", height_px=100)
    assert 'viewBox="-0.15 -2.15 1.1 3.3"' in svg
    assert '<path d="M0,0 L0.4,0 L0.4,-1 L0,-1 Z" fill="#2b2419" fill-rule="evenodd"' in svg
    assert '<path d="M0.4,-0.5 L0.8,-0.2" fill="none" stroke="#2b2419" stroke-width="0.05"' in svg
    assert polyline_to_path_d([[1, 2], [3, 4]]) == "M1,-2 L3,-4"


# ------------------------------------------------------------------ glyph.svg


async def test_svg_of_a_traced_glyph(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs/n.svg")
    assert res.status == 200
    assert res.headers["content-type"].startswith("image/svg+xml")
    # Browser cache only — an edge HIT would never reach the fetch counter.
    assert res.headers["cache-control"] == "private, max-age=300"
    body = res.body.decode()
    assert body.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="')
    assert 'fill-rule="evenodd"' in body and '<path d="M' in body
    # The ruling: baseline solid, midband dashed — four guide lines.
    assert body.count("<line ") == 4
    assert "<title>n — Synthetic test chart</title>" in body


async def test_svg_route_does_not_shadow_the_json_read(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs/n")
    assert res.status == 200
    assert res.headers["content-type"].startswith("application/json")
    assert res.json()["glyph_key"] == "n"


async def test_svg_404_without_a_canonical(api: Harness):
    _, source_id = await api.seed_style_and_source()
    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs/zz.svg")
    assert res.status == 404


def test_rings_flip_y_and_close_each_subpath():
    d = rings_to_path_d([[[0, 0], [1, 0], [1, 1]], [[0, 0], [1, 1]]])  # the 2-point ring is dropped
    assert d == "M0,0 L1,0 L1,-1 Z"


def test_glyph_svg_spans_the_ruling_and_labels_the_glyph():
    payload = {
        "outline_paths": [[[[0.1, 0.0], [0.4, 0.0], [0.4, 0.9], [0.1, 0.9]]]],
        "template_guides": {"baseline": 0.0, "midband": 1.0, "ascender": 3.0, "descender": -2.0},
    }
    svg = glyph_svg(payload, name='e <"Test">', height_px=100)
    # view box: x from 0.1-0.15 to 0.4+0.15, y from -(3+0.15) spanning 5.3
    assert 'viewBox="-0.05 -3.15 0.6 5.3"' in svg
    assert 'height="100"' in svg and 'width="11"' in svg
    assert "<title>e &lt;&quot;Test&quot;&gt;</title>" in svg
    assert 'y1="0" y2="0"' in svg  # the baseline sits at y = 0
