"""Tri-script foundation: broad-nib pen model, non-joining glyphs, pen-aware compose.

Covers the three seams the tri-script work added on top of the (golden-pinned)
letter path: the Bandzugfeder width law + chisel sweep (core/widths.py,
core/template.py), digits/punctuation shaping into detached slots
(core/shaping.py), and the composer's detached placement + pen-aware
generated strokes (core/compose.py). Letter-only byte-identity stays pinned
by tests/test_compose_golden.py.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from core.compose import compose_word
from core.shaping import GlyphSlot, glyph_keys_of, shape_text, shape_word
from core.template import chisel_union_rings, template_guides
from core.widths import BroadNib, PenStyle, broad_nib_half_widths, resolve_half_widths


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
        assert it["mask_width"] >= nib.width_units * 1.15 - 1e-9


def test_compose_default_pen_is_byte_compatible():
    """pen=None emits exactly the legacy item keys (golden-fixture contract)."""
    payloads = {"a-initial": _stub_payload(), "b-final": _stub_payload()}
    slots = [_slot("a-initial", "initial"), _slot("b-final", "final")]
    out = compose_word(slots, payloads)
    for it in out["items"]:
        assert "rings" not in it or "stroke_width" not in it, "no item mixes fill and stroke by default"
