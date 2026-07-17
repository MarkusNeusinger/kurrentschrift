"""Golden regression pin for the composer (shaping + compose on frozen inputs).

Historically the TS→Python parity contract: the fixture was generated from the
SPA's compose.ts on real, frozen glyph payloads right before that file was
retired (the port reproduced it within 1e-6 — PR #143). Since then it pins the
CURRENT composer against accidental change: the frozen payload inputs stay,
the expected slots/outputs are re-baselined DELIBERATELY whenever the
composition rules change on purpose (Phase D transition work):

    REGEN_GOLDEN=1 uv run --extra test pytest tests/test_compose_golden.py

which recomputes `slots` + `composed` from the frozen `payloads` — hermetic,
no DB, no TS. Diff the fixture consciously; a regen is a re-baseline, not a
routine green-up.
"""

from __future__ import annotations

import gzip
import json
import math
import os
from pathlib import Path

import pytest

from core.compose import compose_word
from core.shaping import GlyphSlot, decompose_ligature_slot, glyph_keys_of, shape_text, shape_word, strip_fugen


FIXTURE = Path(__file__).parent / "fixtures" / "compose_golden.json.gz"
ATOL = 1e-6  # golden floats are rounded to 9 decimals; JS↔C libm noise ≪ this

# TS DrawItem/bounds field names → the Python/API snake_case names.
_TS_TO_PY = {
    "strokeWidth": "stroke_width",
    "maskWidth": "mask_width",
    "minX": "min_x",
    "maxX": "max_x",
    "minY": "min_y",
    "maxY": "max_y",
}


def _load() -> dict:
    return json.loads(gzip.decompress(FIXTURE.read_bytes()))


def _snake(value):
    if isinstance(value, dict):
        return {_TS_TO_PY.get(k, k): _snake(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_snake(v) for v in value]
    return value


def _assert_close(a, b, path: str) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        assert set(a) == set(b), f"{path}: keys {sorted(a)} != {sorted(b)}"
        for k in a:
            _assert_close(a[k], b[k], f"{path}.{k}")
        return
    if isinstance(a, list) and isinstance(b, list):
        assert len(a) == len(b), f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            _assert_close(x, y, f"{path}[{i}]")
        return
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        assert math.isclose(a, b, abs_tol=ATOL), f"{path}: {a} != {b}"
        return
    assert a == b, f"{path}: {a!r} != {b!r}"


def _shaped_slots_with_fallback(text: str, payloads: dict) -> list[GlyphSlot]:
    """shape_text + the ligature-decompose fallback, mirroring the word endpoint."""
    slots = shape_text(text)
    if any(s.ligature and s.key and payloads.get(s.key) is None for s in slots):
        expanded: list[GlyphSlot] = []
        for s in slots:
            if s.ligature and s.key and payloads.get(s.key) is None:
                expanded.extend(decompose_ligature_slot(s) or [s])
            else:
                expanded.append(s)
        slots = expanded
    return slots


_PY_TO_TS = {v: k for k, v in _TS_TO_PY.items()}


def _round9(value: object) -> object:
    if isinstance(value, float):
        return round(value, 9)
    if isinstance(value, list):
        return [_round9(v) for v in value]
    if isinstance(value, dict):
        return {k: _round9(v) for k, v in value.items()}
    return value


def _py_shape(value: object) -> object:
    """Python composed dict → the fixture's TS field names (inverse of _snake)."""
    if isinstance(value, dict):
        return {_PY_TO_TS.get(k, k): _py_shape(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_py_shape(v) for v in value]
    return value


def _maybe_regen() -> None:
    if os.environ.get("REGEN_GOLDEN") != "1":
        return
    data = _load()
    for entry in data["words"]:
        slots = _shaped_slots_with_fallback(entry["text"].strip(), entry["payloads"])
        entry["slots"] = [
            {"key": s.key, "text": s.text, "position": s.position, "ligature": s.ligature, "space": s.space}
            for s in slots
        ]
        entry["composed"] = _round9(_py_shape(compose_word(slots, entry["payloads"])))
    FIXTURE.write_bytes(gzip.compress(json.dumps(data, ensure_ascii=False).encode(), 9))


_maybe_regen()


def _words() -> list[dict]:
    return _load()["words"]


@pytest.mark.parametrize("entry", _words(), ids=lambda e: e["text"])
def test_shaping_matches_ts(entry: dict) -> None:
    """Shaped slots (after fallback) are identical to the TS run, field by field."""
    slots = _shaped_slots_with_fallback(entry["text"].strip(), entry["payloads"])
    expected = entry["slots"]
    assert len(slots) == len(expected), f"{entry['text']}: {len(slots)} slots != {len(expected)}"
    for got, want in zip(slots, expected, strict=True):
        assert got.key == want["key"]
        assert got.text == want["text"]
        assert got.position == want["position"]
        assert got.ligature == want["ligature"]
        assert got.space == want["space"]


@pytest.mark.parametrize("entry", _words(), ids=lambda e: e["text"])
def test_compose_matches_ts(entry: dict) -> None:
    """compose_word reproduces composeWord's draw items within tolerance."""
    slots = _shaped_slots_with_fallback(entry["text"].strip(), entry["payloads"])
    composed = compose_word(slots, entry["payloads"])
    expected = _snake(entry["composed"])
    # TS omits `diacritic` unless true and never emits `rings: undefined`; the
    # Python side omits the same keys, so shapes align 1:1.
    _assert_close(composed["items"], expected["items"], f"{entry['text']}.items")
    _assert_close(composed["bounds"], expected["bounds"], f"{entry['text']}.bounds")
    _assert_close(composed["guides"], expected["guides"], f"{entry['text']}.guides")
    assert composed["missing"] == expected["missing"]


def test_glyph_keys_of_dedupes() -> None:
    slots = shape_text("lesen")
    keys = glyph_keys_of(slots)
    assert keys == ["l", "e", "longs", "n"]  # repeated e deduped, order preserved


def test_fuge_forces_round_s_at_morpheme_boundary() -> None:
    """`Haus|tür`: the s before the Fuge is the round Schluss-s, no ſt ligature."""
    slots = shape_word("Haus|tür")
    # The marker carries no glyph — one slot per real letter, in order.
    assert [s.text for s in slots] == ["H", "a", "u", "s", "t", "ü", "r"]
    s_slot = slots[3]
    assert s_slot.key == "s"  # round s despite the medial position
    assert s_slot.position == "medial"
    # No ſt ligature spans the boundary; the t is its own initial-of-part slot.
    assert all(not s.ligature for s in slots)
    assert slots[4].key == "t"


def test_fuge_absent_keeps_long_s() -> None:
    """Without a Fuge the inner s stays long — the unchanged historical default."""
    slots = shape_text("Arbeitsamt")  # naive: inner s is long ſ
    assert [s.key for s in slots] == ["A", "r", "b", "e", "i", "t", "longs", "a", "m", "t"]
    # With the Fuge the boundary s turns round; positions still mark the slot.
    fuge_slots = shape_text("Arbeits|amt")
    assert [s.key for s in fuge_slots][6] == "s"
    assert fuge_slots[6].position == "medial"


def test_strip_fugen_clears_markers() -> None:
    assert strip_fugen("Haus|tür") == "Haustür"
    assert strip_fugen("Donners|tag") == "Donnerstag"
    assert strip_fugen("lesen") == "lesen"
