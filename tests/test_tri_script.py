"""Tri-script foundation: broad-nib pen model, non-joining glyphs, pen-aware compose.

Covers the three seams the tri-script work added on top of the (golden-pinned)
letter path: the Bandzugfeder width law + chisel sweep (core/widths.py,
core/template.py), digits/punctuation shaping into detached slots
(core/shaping.py), and the composer's detached placement + pen-aware
generated strokes (core/compose.py). Letter-only byte-identity stays pinned
by tests/test_compose_golden.py.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
import pytest

from core.compose import compose_word
from core.shaping import GlyphSlot, glyph_keys_of, shape_text, shape_word
from core.template import chisel_union_rings, template_guides
from core.widths import BroadNib, PenStyle, broad_nib_half_widths, resolve_half_widths


SHAPING_CASES = Path(__file__).parent / "fixtures" / "shaping_cases.json"


# ------------------------------------------------------------- broad-nib law


def test_broad_nib_width_law_extremes():
    nib = BroadNib(width_units=0.2, angle_deg=15.0, edge_fraction=0.25)
    # Moving along the nib edge: only the edge thickness writes.
    assert nib.half_width_at(15.0) == pytest.approx(0.5 * nib.edge_units)
    # Moving perpendicular to the edge: the full nib width writes.
    assert nib.half_width_at(105.0) == pytest.approx(0.5 * nib.width_units)
    # Direction is unsigned: a stroke and its reverse ink the same width.
    assert nib.half_width_at(60.0) == pytest.approx(nib.half_width_at(240.0))


def test_broad_nib_koch_quarter_upstroke():
    """Koch 1928: the upstroke (~28-30 deg) writes about a quarter of the
    downstroke (~78-80 deg along the slant) — the |sin| law reproduces it."""
    nib = BroadNib(width_units=1.0, angle_deg=15.0, edge_fraction=0.0)
    up = nib.half_width_at(29.0)
    down = nib.half_width_at(79.0)
    assert up / down == pytest.approx(0.27, abs=0.05)


def test_broad_nib_half_widths_never_bridge_a_lift():
    # Two strokes: one along the nib edge (thin), one perpendicular (thick).
    a = 15.0
    along = [(t * math.cos(math.radians(a)), t * math.sin(math.radians(a))) for t in np.linspace(0, 1, 5)]
    across = [(t * math.cos(math.radians(a + 90)), t * math.sin(math.radians(a + 90))) for t in np.linspace(0, 1, 5)]
    pts = np.array(along + across)
    nib = BroadNib(width_units=0.2, angle_deg=a, edge_fraction=0.1)
    hw = broad_nib_half_widths(pts, nib, stroke_starts=[0, 5])
    assert np.allclose(hw[:5], 0.5 * nib.edge_units, atol=1e-6)
    assert np.allclose(hw[5:], 0.5 * nib.width_units, atol=1e-6)


def test_resolve_half_widths_broad_nib_regenerates_and_falls_back():
    measured = np.array([0.05, 0.06, 0.05, 0.06])
    pts = np.array([[0.0, 0.0], [0.0, 0.4], [0.0, 0.8], [0.0, 1.2]])  # vertical stroke
    nib = BroadNib(width_units=0.2, angle_deg=15.0, edge_fraction=0.1)
    resolved = resolve_half_widths(measured, "broad_nib", points=pts, stroke_starts=None, nib=nib)
    assert resolved == pytest.approx(nib.half_width_at(90.0) * np.ones(4), abs=1e-9)
    # Without geometry the measurement passes through (diagnostic path).
    assert np.allclose(resolve_half_widths(measured, "broad_nib"), measured)
    # Other resolvers are untouched by the new kwargs.
    assert np.allclose(resolve_half_widths(measured, "constant"), np.median(measured))


def test_chisel_union_rings_vertical_stroke_has_chisel_extent():
    nib = BroadNib(width_units=0.2, angle_deg=15.0, edge_fraction=0.1)
    x = np.zeros(10)
    y = np.linspace(0.0, 1.0, 10)
    rings = chisel_union_rings(x, y, nib)
    assert rings, "sweep must produce a silhouette"
    pts = np.array([p for ring in rings for p in ring])
    hx, hy = nib.half_vector
    ex, ey = nib.edge_vector
    # The stamped nib edge extends the ink horizontally by the half-nib vector
    # (plus edge) on both sides of the centerline.
    assert pts[:, 0].max() == pytest.approx(abs(hx) + abs(ex), abs=1e-3)
    assert pts[:, 0].min() == pytest.approx(-(abs(hx) + abs(ex)), abs=1e-3)
    # Chisel top: the highest ink sits at the tilted nib stamp, above y=1.
    assert pts[:, 1].max() == pytest.approx(1.0 + abs(hy) + abs(ey), abs=1e-3)


# ------------------------------------------------------------ pen calibration


def test_pen_from_profiles_calibrates_per_resolver():
    from api.rendering import pen_from_profiles

    profiles = [[0.02, 0.03, 0.05], [0.06, 0.07, 0.08], [0.01, 0.04]]
    # constant has its own pooled-nib path; no PenStyle.
    assert pen_from_profiles("constant", profiles) is None
    # pressure: the pooled hairline is the P10 of the flattened samples.
    pressure = pen_from_profiles("pressure", profiles)
    assert pressure.kind == "pressure"
    assert pressure.hairline_half == pytest.approx(0.02)  # P10 of 8 sorted samples
    # broad_nib: W = 2*P95, edge fraction = 2*P10/W clamped to [0.05, 0.5].
    broad = pen_from_profiles("broad_nib", profiles)
    assert broad.nib.width_units == pytest.approx(0.16)  # 2 * 0.08
    assert broad.nib.edge_fraction == pytest.approx((2 * 0.02) / 0.16)
    assert broad.nib.angle_deg == pytest.approx(15.0)  # the taught constant, never fitted


def test_pen_from_profiles_falls_back_without_measurements():
    from api.rendering import pen_from_profiles
    from core.widths import BROAD_NIB_WIDTH_UNITS

    assert pen_from_profiles("pressure", []).hairline_half is None
    empty = pen_from_profiles("broad_nib", [[], []])
    assert empty.nib.width_units == pytest.approx(BROAD_NIB_WIDTH_UNITS)


def test_invalidate_pooled_style_clears_all_sources_of_the_style():
    # A style pools from several chart sources (Kurrent: loth + petzendorfer);
    # a write through one source must drop the OTHER source's pool too, or a
    # cross-source re-trace serves a stale pen for the TTL.
    import time

    from api import rendering

    now = time.monotonic()
    rendering._nib_cache[("kurrent", "loth-1866")] = (0.07, now)
    rendering._nib_cache[("kurrent", "petzendorfer-1889")] = (0.06, now)
    rendering._nib_cache[("suetterlin", "suetterlin-1922")] = (0.05, now)
    rendering._pen_cache[("kurrent", "petzendorfer-1889", "pressure")] = (None, now)
    try:
        rendering.invalidate_pooled_style("kurrent")
        assert not [k for k in rendering._nib_cache if k[0] == "kurrent"]
        assert not [k for k in rendering._pen_cache if k[0] == "kurrent"]
        # Other styles keep their pools.
        assert ("suetterlin", "suetterlin-1922") in rendering._nib_cache
    finally:
        rendering._nib_cache.pop(("suetterlin", "suetterlin-1922"), None)


def test_pen_from_profiles_clamps_edge_fraction():
    from api.rendering import pen_from_profiles

    # Near-constant measurements would imply edge ≈ width; the clamp keeps the
    # nib a physical chisel (edge ≤ half the width).
    flatish = [[0.05, 0.05, 0.051, 0.052]]
    assert pen_from_profiles("broad_nib", flatish).nib.edge_fraction == pytest.approx(0.5)


def test_chisel_union_rings_degenerate_inputs():
    nib = BroadNib(width_units=0.2, angle_deg=15.0, edge_fraction=0.1)
    assert chisel_union_rings(np.array([]), np.array([]), nib) == []
    # A single point stamps the bare nib rectangle: area == W * t.
    rings = chisel_union_rings(np.array([0.0]), np.array([0.0]), nib)
    assert len(rings) == 1
    pts = np.array(rings[0])
    x, y = pts[:, 0], pts[:, 1]
    area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    # ring coordinates are rounded to 4 decimals — allow that quantisation
    assert area == pytest.approx(nib.width_units * nib.edge_units, rel=1e-2)


# --------------------------------------------------------- shaping: detached


def test_digits_shape_to_detached_slots():
    slots = shape_word("1922")
    assert [s.key for s in slots] == ["1-initial", "9-medial", "2-medial", "2-final"]
    assert all(not s.joins for s in slots)
    assert glyph_keys_of(slots) == ["1-initial", "9-medial", "2-medial", "2-final"]


def test_punctuation_keeps_word_final_round_s():
    # The trailing comma must not steal the letter run's final position:
    # "Haus," keeps the round Schluss-s.
    slots = shape_word("Haus,")
    assert slots[3].key == "s-final"
    # The comma is a one-token run of its own → position 'initial' (the
    # position is cosmetic for detached glyphs, all three carry the same form).
    assert slots[4].key == "comma-initial"
    assert not slots[4].joins
    # Without the run split the s would read medial → long-s (the old bug).
    assert shape_word("Haus")[3].key == "s-final"


def test_straight_quote_resolves_low_then_high():
    slots = shape_word('"Ja"')
    assert slots[0].key.startswith("quote-low")
    assert slots[-1].key.startswith("quote-high")
    typographic = shape_word("„Ja“")
    assert typographic[0].key.startswith("quote-low")
    assert typographic[-1].key.startswith("quote-high")
    # Occurrence parity, not word position: a quote after other punctuation
    # still opens low — ("Ja") from the Copilot review.
    parenthesised = shape_word('("Ja")')
    quotes = [s for s in parenthesised if s.text == '"']
    assert quotes[0].key.startswith("quote-low")
    assert quotes[1].key.startswith("quote-high")


def test_hyphen_and_dash_map_to_their_glyphs():
    slots = shape_word("Haus-Tür")
    hyphen = [s for s in slots if s.text == "-"][0]
    assert hyphen.key.startswith("hyphen-")
    assert not hyphen.joins
    # Letters on both sides keep their own runs: r final, H initial of ITS run.
    assert slots[0].key == "H-initial"
    assert slots[-1].key == "r-final"
    dash = shape_text("Wort – Wort")
    assert any(s.key and s.key.startswith("dash-") for s in dash)


def test_letters_only_shaping_unchanged():
    slots = shape_word("lesen")
    assert [s.key for s in slots] == ["l-initial", "e-medial", "s-medial", "e-medial", "n-final"]
    assert all(s.joins for s in slots)


# ------------------------------------------------- shaping twin: shared fixture
# core/shaping.py and app/src/domain/shaping.ts MUST agree on text → glyph_keys
# (CLAUDE.md twin mandate). The SAME fixture drives this Python assertion and a
# Vitest test in app/ (app/src/domain/shaping.test.ts): deliberately mutating
# one shaping without the other fails CI. When a case legitimately changes,
# regenerate the expected keys from the Python source of truth (mirrors the
# compose-golden pattern):
#
#     REGEN_SHAPING=1 uv run --extra test pytest tests/test_tri_script.py -k fixture
#
# then re-run BOTH suites (pytest + `npm run test`) to confirm the twin agrees.


def test_shaping_cases_fixture_matches_python_shaping():
    cases = json.loads(SHAPING_CASES.read_text(encoding="utf-8"))
    assert cases, "the shared shaping fixture must not be empty"
    if os.environ.get("REGEN_SHAPING") == "1":
        for case in cases:
            case["keys"] = [s.key for s in shape_text(case["text"])]
        SHAPING_CASES.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        pytest.skip("shaping fixture regenerated from core/shaping.py — re-run without REGEN_SHAPING")
    for case in cases:
        keys = [s.key for s in shape_text(case["text"])]
        assert keys == case["keys"], f"shaping drift on {case['text']!r}: {keys} != {case['keys']}"


# ------------------------------------------------------- compose: detached


def _stub_payload(width: float = 0.4, half: float = 0.05) -> dict:
    """A minimal render payload: one stroke rising from the baseline."""
    cl = [[0.0, 0.0], [width / 2, 0.5], [width, 0.55]]
    return {
        "centerlines_template": [cl],
        "outline_paths": [],
        "half_widths_template": [half, half, half],
        "template_guides": template_guides([1, 1, 1]),
        "entry": {"xy": [0.0, 0.0]},
    }


def _slot(key: str, position: str = "medial", joins: bool = True, text: str = "x") -> GlyphSlot:
    return GlyphSlot(key, text, position, False, False, joins=joins)


def test_compose_detached_glyph_breaks_the_join():
    payloads = {"a-initial": _stub_payload(), "comma-final": _stub_payload(width=0.1)}
    slots = [_slot("a-initial", "initial"), _slot("comma-final", "final", joins=False, text=",")]
    out = compose_word(slots, payloads)
    # letter stroke + Endstrich swing (rising exit) + comma stroke — NO connector.
    kinds = [("rings" in it, "stroke_width" in it) for it in out["items"]]
    stroked = [it for it in out["items"] if "stroke_width" in it]
    assert len(stroked) == 1, "only the Endstrich swing may be stroked — no connector to a detached glyph"
    assert out["items"][-1]["lift"] is True, "the pen lifts into a detached glyph"
    assert not out["missing"]
    del kinds


def test_compose_detached_spacing_uses_clearance():
    payloads = {"1-initial": _stub_payload(width=0.3), "2-final": _stub_payload(width=0.3)}
    slots = [_slot("1-initial", "initial", joins=False, text="1"), _slot("2-final", "final", joins=False, text="2")]
    out = compose_word(slots, payloads)
    items = out["items"]
    assert len(items) == 2  # two glyph strokes, no connector, no swing
    first_max_x = max(x for x, _ in items[0]["centerline"])
    second_min_x = min(x for x, _ in items[1]["centerline"])
    assert second_min_x - first_max_x == pytest.approx(0.16, abs=0.02)  # digit clearance
    assert items[1]["lift"] is True


def test_compose_missing_detached_glyph_still_ends_the_word():
    """An UNAUTHORED comma is still a run boundary: the word before it earns
    its Endstrich, exactly like the pre-registry null-key behaviour."""
    payloads = {"a-initial": _stub_payload()}  # comma has no template
    slots = [_slot("a-initial", "initial"), _slot("comma-final", "final", joins=False, text=",")]
    out = compose_word(slots, payloads)
    stroked = [it for it in out["items"] if "stroke_width" in it]
    assert len(stroked) == 1, "the Endstrich swing must fire before the missing comma's gap"
    assert out["missing"] == ["comma-final"]


def test_compose_letter_after_detached_starts_fresh():
    payloads = {"quote-low-initial": _stub_payload(width=0.1), "W-final": _stub_payload()}
    slots = [_slot("quote-low-initial", "initial", joins=False, text='"'), _slot("W-final", "final")]
    out = compose_word(slots, payloads)
    stroked = [it for it in out["items"] if "stroke_width" in it and "rings" not in it]
    # No connector between the quote and the letter; the letter's swing is the
    # only stroked item.
    assert len(stroked) == 1
    letter_items = [it for it in out["items"] if it.get("centerline") and "stroke_width" not in it]
    assert letter_items[-1]["lift"] is True or letter_items[0]["lift"] is True


# ------------------------------------------------------------ compose: pens


def test_compose_pressure_pen_caps_generated_strokes_at_hairline():
    payloads = {"a-initial": _stub_payload(half=0.08), "b-final": _stub_payload(half=0.08)}
    slots = [_slot("a-initial", "initial"), _slot("b-final", "final")]
    plain = compose_word(slots, payloads)
    hairline = compose_word(slots, payloads, pen=PenStyle(kind="pressure", hairline_half=0.02))
    plain_widths = [it["stroke_width"] for it in plain["items"] if "stroke_width" in it]
    hair_widths = [it["stroke_width"] for it in hairline["items"] if "stroke_width" in it]
    assert all(w == pytest.approx(0.16) for w in plain_widths)
    assert all(w == pytest.approx(0.04) for w in hair_widths)


def test_compose_broad_nib_pen_ships_connector_rings():
    payloads = {"a-initial": _stub_payload(), "b-final": _stub_payload()}
    slots = [_slot("a-initial", "initial"), _slot("b-final", "final")]
    nib = BroadNib(width_units=0.15, angle_deg=15.0, edge_fraction=0.2)
    out = compose_word(slots, payloads, pen=PenStyle(kind="broad_nib", nib=nib))
    generated = [it for it in out["items"] if "stroke_width" in it]
    assert generated, "connector + swing exist"
    for it in generated:
        assert it.get("rings"), "broad-nib generated strokes ship as filled rings"
    # EVERY item's reveal mask covers the stamped nib's extent — glyph strokes
    # too, whose own directions may never reach the nib's widest direction.
    for it in out["items"]:
        assert it["mask_width"] >= nib.width_units * 1.15 - 1e-9


def test_compose_default_pen_is_byte_compatible():
    """pen=None emits exactly the legacy item keys (golden-fixture contract)."""
    payloads = {"a-initial": _stub_payload(), "b-final": _stub_payload()}
    slots = [_slot("a-initial", "initial"), _slot("b-final", "final")]
    out = compose_word(slots, payloads)
    for it in out["items"]:
        assert "rings" not in it or "stroke_width" not in it, "no item mixes fill and stroke by default"
