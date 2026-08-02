"""Provenance tagging on compose_word (diagnostics only, default off).

Runs on the committed golden fixture's frozen payloads — hermetic, no DB.
The contract: ``provenance=False`` emits no extra keys (the exact shape is
pinned separately by test_compose_golden), ``provenance=True`` tags every
glyph stroke with its slot and every connector with its pair (plus the
coupling endpoints ``exit``/``entry``) WITHOUT touching the geometry.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from core.compose import compose_word
from core.shaping import GlyphSlot, shape_text


FIXTURE = Path(__file__).parent / "fixtures" / "compose_golden.json.gz"

PROVENANCE_KEYS = {"slot_index", "glyph_key", "pair", "from_slot", "to_slot", "exit", "entry"}


def _entries() -> list[dict]:
    return json.loads(gzip.decompress(FIXTURE.read_bytes()))["words"]


def _slots(entry: dict) -> list[GlyphSlot]:
    return [GlyphSlot(**s) for s in entry["slots"]]


@pytest.mark.parametrize("entry", _entries(), ids=lambda e: e["text"])
def test_default_emits_no_provenance_keys(entry: dict) -> None:
    composed = compose_word(_slots(entry), entry["payloads"])
    for it in composed["items"]:
        assert not (PROVENANCE_KEYS & it.keys())


@pytest.mark.parametrize("entry", _entries(), ids=lambda e: e["text"])
def test_provenance_tags_without_touching_geometry(entry: dict) -> None:
    slots = _slots(entry)
    plain = compose_word(slots, entry["payloads"])
    tagged = compose_word(slots, entry["payloads"], provenance=True)
    assert len(tagged["items"]) == len(plain["items"])
    assert tagged["bounds"] == plain["bounds"]
    assert tagged["missing"] == plain["missing"]
    for p, t in zip(plain["items"], tagged["items"], strict=True):
        assert t["centerline"] == p["centerline"]  # geometry identical
        if "stroke_width" in t:  # a generated connector or boundary stroke
            # The coupling endpoints ride along on every join item; they are
            # NOT readable off the centerline (the overlap extension moves its
            # first sample), which is why compose states them.
            assert len(t["exit"]) == 2
            if t["to_slot"] is None:  # the word-final Endstrich leaves its last glyph
                assert t["pair"] == [slots[t["from_slot"]].key, None]
                assert "entry" not in t  # no right glyph to enter
            else:
                assert t["pair"] == [slots[t["from_slot"]].key, slots[t["to_slot"]].key]
                assert t["from_slot"] < t["to_slot"]
                # No sign assertion on the offset: a nested placement (a tucked
                # round body) legitimately puts the entry LEFT of the exit.
                assert len(t["entry"]) == 2
            assert "slot_index" not in t
        else:  # a glyph stroke (body or deferred diacritic)
            assert t["glyph_key"] == slots[t["slot_index"]].key
            assert "pair" not in t
            assert not ({"exit", "entry"} & t.keys())


def _n_payload() -> dict:
    anchors = [[0.0, 0.0], [0.05, 0.45], [0.12, 0.62], [0.25, 0.55], [0.32, 0.25], [0.35, 0.0]]
    return {
        "glyph_key": "n",
        "advance": 0.45,
        "entry": {"xy": [0.0, 0.0], "tangent_deg": 60.0, "coupling": "baseline"},
        "exit_pt": {"xy": [0.35, 0.0], "tangent_deg": -60.0, "coupling": "baseline"},
        "anchors_template": anchors,
        "centerlines_template": [anchors],
        "half_widths_template": [0.05] * len(anchors),
        "outline_paths": [],
        "template_guides": {"baseline": 0, "midband": 1, "ascender": 2, "descender": -1},
    }


def test_override_connector_carries_the_coupling_endpoints() -> None:
    """An override join states the same endpoints as a generated one — the
    stored offset is exactly ``entry - exit`` in x (both baseline-locked)."""
    slots = shape_text("nn")
    payloads = {"n": _n_payload()}
    offset = [0.9, 0.0]
    overrides = {("n", "n"): {"offset": offset, "connector": [[0.0, 0.0], [0.45, 0.1], [0.9, 0.0]]}}
    composed = compose_word(slots, payloads, provenance=True, pair_overrides=overrides)
    joins = [it for it in composed["items"] if it.get("pair") and it["pair"][1] is not None]
    assert joins, "the nn pair must compose one join"
    join = joins[0]
    assert join["override"] is True
    assert join["entry"][0] - join["exit"][0] == pytest.approx(offset[0], abs=1e-9)


def test_override_without_provenance_states_no_endpoints() -> None:
    slots = shape_text("nn")
    payloads = {"n": _n_payload()}
    overrides = {("n", "n"): {"offset": [0.9, 0.0], "connector": [[0.0, 0.0], [0.45, 0.1], [0.9, 0.0]]}}
    composed = compose_word(slots, payloads, pair_overrides=overrides)
    for it in composed["items"]:
        assert not (PROVENANCE_KEYS & it.keys())
