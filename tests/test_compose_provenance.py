"""Provenance tagging on compose_word (diagnostics only, default off).

Runs on the committed golden fixture's frozen payloads — hermetic, no DB.
The contract: ``provenance=False`` emits no extra keys (the exact shape is
pinned separately by test_compose_golden), ``provenance=True`` tags every
glyph stroke with its slot and every connector with its pair WITHOUT touching
the geometry.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from core.compose import compose_word
from core.shaping import GlyphSlot


FIXTURE = Path(__file__).parent / "fixtures" / "compose_golden.json.gz"

PROVENANCE_KEYS = {"slot_index", "glyph_key", "pair", "from_slot", "to_slot"}


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
            if t["to_slot"] is None:  # the word-final Endstrich leaves its last glyph
                assert t["pair"] == [slots[t["from_slot"]].key, None]
            else:
                assert t["pair"] == [slots[t["from_slot"]].key, slots[t["to_slot"]].key]
                assert t["from_slot"] < t["to_slot"]
            assert "slot_index" not in t
        else:  # a glyph stroke (body or deferred diacritic)
            assert t["glyph_key"] == slots[t["slot_index"]].key
            assert "pair" not in t
