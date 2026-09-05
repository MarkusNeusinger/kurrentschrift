"""The nib-coupled ink clearance: off by default, floored, and inert today.

`nib_clearance` reads the placement's ink clearances in nib radii instead of
x-heights (core.compose CLEARANCE_REF_HALF). It was pre-registered, measured
and NOT adopted — messjournal.md §14 „Ink-Clearance an die Feder `sep05`" — so
what needs pinning is not that it improves anything but that it cannot leak:
below the calibration pen the switch is arithmetically a no-op, which is what
keeps the golden fixture and both bench headlines byte-identical while the arm
stays in the tree.

No DB: two synthetic glyphs plus the frozen payloads of the golden fixture.
"""

from __future__ import annotations

import gzip
import json
import math
from pathlib import Path

import pytest

from core.compose import CLEARANCE_REF_HALF, WORD_INK_GAP, _clearance_scale, compose_word
from core.shaping import GlyphSlot


GOLDEN = Path(__file__).parent / "fixtures" / "compose_golden.json.gz"

# A body stroke that ends the first word, and one whose ink reaches far LEFT of
# its own entry — the capital-bow case in which WORD_INK_GAP, and only it,
# decides the distance. A scalar clearance is the cleanest place to read the
# scale off the composed geometry.
_WORD_A = [(0.0, 0.0), (0.3, 0.25), (0.6, 0.5)]
_WORD_B = [(-0.8, 0.4), (0.0, 0.0), (0.35, 0.3), (0.7, 0.55)]


def _payload(centerline: list[tuple[float, float]], half: float) -> dict:
    return {
        "centerlines_template": [[list(p) for p in centerline]],
        "half_widths_template": [half] * len(centerline),
        "entry": {"xy": list(centerline[1])},
        "outline_paths": [],
        "template_guides": {"midband": 1.0},
    }


def _slots(*keys: str | None) -> list[GlyphSlot]:
    return [
        GlyphSlot(
            key=k,
            text=" " if k is None else k,
            position=None if k is None else "isolated",
            ligature=False,
            space=k is None,
        )
        for k in keys
    ]


def _word_gap(half: float, *, nib_clearance: bool) -> float:
    """Realised ink gap between the two words of "a b" at pen radius ``half``."""
    composed = compose_word(
        _slots("a", None, "b"),
        {"a": _payload(_WORD_A, half), "b": _payload(_WORD_B, half)},
        provenance=True,
        nib_clearance=nib_clearance,
    )
    items = composed["items"]
    cut = next(i for i, it in enumerate(items) if it.get("slot_index") == 2)
    xs_a = [x for it in items[:cut] for x, _ in it["centerline"]]
    xs_b = [x for it in items[cut:] for x, _ in it["centerline"]]
    return min(xs_b) - max(xs_a)


@pytest.mark.parametrize("half", [0.02, 0.05, CLEARANCE_REF_HALF])
def test_scale_is_one_at_and_below_the_calibration_pen(half: float) -> None:
    # Floored on purpose: nothing has ever measured what a LIGHTER pen should
    # do to this hand's spacing, so the switch may not invent a tightening.
    assert _clearance_scale(half, True) == 1.0
    assert _clearance_scale(half, False) == 1.0


def test_scale_follows_the_pen_above_the_calibration() -> None:
    assert math.isclose(_clearance_scale(0.097, True), 0.097 / CLEARANCE_REF_HALF)
    # …and stays inert while the switch is off, whatever the pen.
    assert _clearance_scale(0.097, False) == 1.0


def test_switch_is_a_no_op_at_todays_pen() -> None:
    # The bench root's pooled Gleichzug nib IS the calibration pen, so every
    # number this repo quotes has to survive flipping the switch.
    off = _word_gap(CLEARANCE_REF_HALF, nib_clearance=False)
    on = _word_gap(CLEARANCE_REF_HALF, nib_clearance=True)
    assert math.isclose(off, on, abs_tol=1e-12)
    assert math.isclose(off, WORD_INK_GAP, abs_tol=1e-9)


def test_switch_widens_exactly_by_the_nib_ratio_above_it() -> None:
    plate = 0.097  # the half-width measured on the 1922 word plates
    assert math.isclose(_word_gap(plate, nib_clearance=False), WORD_INK_GAP, abs_tol=1e-9)
    assert math.isclose(_word_gap(plate, nib_clearance=True), WORD_INK_GAP * plate / CLEARANCE_REF_HALF, abs_tol=1e-9)


def test_golden_payloads_are_untouched_by_the_switch() -> None:
    # The frozen payloads carry half 0.071 — below the calibration pen, so the
    # golden fixture is inside the floor and the arm cannot move it. This is
    # the property that lets a measured, unadopted arm live in the tree.
    for entry in json.loads(gzip.decompress(GOLDEN.read_bytes()))["words"]:
        slots = [GlyphSlot(**s) for s in entry["slots"]]
        base = compose_word(slots, entry["payloads"])
        armed = compose_word(slots, entry["payloads"], nib_clearance=True)
        assert armed == base, entry["text"]
