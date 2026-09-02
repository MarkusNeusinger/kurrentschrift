"""The 4-decimal wire contract of the `/write` render payloads.

`docs/reference/write-api.md` states that every number in a render payload is
rounded to four decimals, and `core/pipeline.py` holds that for what it stores.
Composition does not round, so `/write/word` shipped a third of its numbers as
float64 noise (`0.015600000000000001`) — bytes below the contract's own
resolution on the API's most-requested route. `core.rounding` is the walk that
puts the contract back on at serialisation; this suite pins it in three places:
the pure function, the `_geometry_response` boundary that calls it, and the
served responses.
"""

from __future__ import annotations

import re

from core.rounding import WIRE_DECIMALS, round_wire_numbers
from core.shaping import glyph_keys_of, shape_text
from tests.api_harness import Harness


# Every JSON number literal with a fractional part; the group is the fraction.
_FRACTION = re.compile(rb"-?\d+\.(\d+)")


def _over_contract(body: bytes) -> list[bytes]:
    """Number literals in `body` carrying more decimals than the contract."""
    return [m.group(0) for m in _FRACTION.finditer(body) if len(m.group(1)) > WIRE_DECIMALS]


def test_round_wire_numbers_walks_containers_and_spares_non_floats():
    payload = {
        "items": [{"centerline": [[0.015600000000000001, 1.3921424233232222]], "n": 240, "gap": True}],
        "text": "lesen",
        "missing": [],
        "bounds": (0.12345678, -0.98765432),
        "meta": None,
    }
    assert round_wire_numbers(payload) == {
        "items": [{"centerline": [[0.0156, 1.3921]], "n": 240, "gap": True}],
        "text": "lesen",
        "missing": [],
        # A tuple becomes a list, which is what JSON makes of it anyway.
        "bounds": [0.1235, -0.9877],
        "meta": None,
    }


def test_round_wire_numbers_is_idempotent():
    """`/write/glyphs` is already rounded by the pipeline, so a second pass
    must not move a single byte of it."""
    once = round_wire_numbers({"a": [0.1234567, 0.1], "b": {"c": -0.00005}})
    assert round_wire_numbers(once) == once


def test_geometry_response_rounds_before_serialising():
    """The boundary itself — the same place the Cache-Control header sits."""
    from api.routers.write import _geometry_response

    res = _geometry_response({"items": [{"centerline": [[0.015600000000000001, 1.3921424233232222]]}]})
    assert res.body == b'{"items":[{"centerline":[[0.0156,1.3921]]}]}'


async def test_write_word_response_holds_the_four_decimal_contract(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    word = "lesen"
    # Through the real shaper, so the seed always covers whatever `lesen`
    # shapes into (the long-s rule turns its `s` into `longs`).
    for key in glyph_keys_of(shape_text(word)):
        await api.seed_template(style_id, source_id, key, key)

    res = await api.client.request("GET", f"/sources/{source_id}/write/word", params={"text": word})
    assert res.status == 200
    assert res.json()["missing"] == []
    # Non-vacuity: a composed word is thousands of numbers, not a handful.
    assert len(_FRACTION.findall(res.body)) > 500
    assert _over_contract(res.body) == []


async def test_write_glyphs_response_holds_the_four_decimal_contract(api: Harness):
    """The batch read was already inside the contract except for the fluent
    widening's `advance`/`exit_pt`; the walk closes that too, and rounds
    nothing else — its bytes are otherwise unchanged."""
    style_id, source_id = await api.seed_style_and_source(width_resolver="constant")
    await api.seed_template(style_id, source_id, "e", "e")

    res = await api.client.request("GET", f"/sources/{source_id}/write/glyphs", params={"keys": "e"})
    assert res.status == 200
    assert len(_FRACTION.findall(res.body)) > 100
    assert _over_contract(res.body) == []
