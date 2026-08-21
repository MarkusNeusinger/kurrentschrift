"""Tests for the shared ductus target (`tools.tracebench.soll`).

The real computation runs over the frozen fixture cases and the compose stack,
so what a unit test can pin is the contract around it: a root without
composition data degrades to a warning instead of a failure, the flat report
fields are exactly the Soll pair, and the shared strokes builder (K0-S, §14
`aug21`) reproduces the historical lift-split/dedupe rules and cuts a run
restriction exactly along the item span — the guard's soll and the metric's
read the SAME strokes or nothing.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tools.tracebench.soll import SollRow, composition_strokes, ductus_soll, soll_row_fields


def test_a_root_without_cases_degrades_to_a_warning(tmp_path: Path) -> None:
    out, warnings = ductus_soll(["die"], which="words", style="suetterlin", fixtures_root=tmp_path)
    assert out == {}
    assert len(warnings) == 1
    assert "Duktus-Soll" in warnings[0]


def _item(points, *, slot=None, lift=False):
    return {"centerline": points, "slot_index": slot, "lift": lift}


def test_the_builder_lift_splits_and_dedupes_like_the_historical_loop() -> None:
    items = [
        _item([[0.0, 0.0], [1.0, 0.0]], slot=0),
        _item([[1.0, 0.0], [2.0, 0.5]]),  # connector continues; duplicate seam point dropped
        _item([[3.0, 1.5], [3.2, 1.6]], slot=1, lift=True),  # a lift starts a new stroke
    ]
    strokes = composition_strokes(items)
    assert [len(s) for s in strokes] == [3, 2]
    assert np.allclose(strokes[0], [[0.0, 0.0], [1.0, 0.0], [2.0, 0.5]])


def test_the_run_restriction_keeps_the_span_and_the_deferred_mark() -> None:
    items = [
        _item([[0.0, 0.0], [1.0, 0.0]], slot=0),
        _item([[1.0, 0.0], [2.0, 0.0]]),  # connector 0->1, inside the span
        _item([[2.0, 0.0], [3.0, 0.0]], slot=1),
        _item([[3.0, 0.0], [4.0, 0.0]]),  # connector 1->2
        _item([[4.0, 0.0], [5.0, 0.0]], slot=2),
        _item([[0.4, 1.3], [0.6, 1.3]], slot=0, lift=True),  # slot 0's deferred mark
    ]
    run01 = composition_strokes(items, slots={0, 1})
    # letters 0+1 and their connector weld into one stroke; the skipped slot-2
    # block closes it, the deferred mark comes back as its own stroke
    assert [len(s) for s in run01] == [4, 2]
    assert np.allclose(run01[0][-1], [3.0, 0.0])
    assert np.allclose(run01[1], [[0.4, 1.3], [0.6, 1.3]])
    run2 = composition_strokes(items, slots={2})
    assert [len(s) for s in run2] == [2]
    assert np.allclose(run2[0], [[4.0, 0.0], [5.0, 0.0]])


def test_the_full_word_needs_no_slots_and_a_gapless_restriction_matches_it() -> None:
    items = [
        _item([[0.0, 0.0], [1.0, 0.0]], slot=0),
        _item([[1.0, 0.0], [2.0, 0.0]]),
        _item([[2.0, 0.0], [3.0, 0.0]], slot=1),
    ]
    full = composition_strokes(items)
    restricted = composition_strokes(items, slots={0, 1})
    assert len(full) == len(restricted) == 1
    assert np.array_equal(full[0], restricted[0])


def test_the_follow_knob_defaults_to_the_init_source() -> None:
    from tools.pairlab.follow import FollowWeights  # noqa: PLC0415

    assert FollowWeights().soll_source == "init"


def test_soll_row_fields_keep_letters_and_composition_apart() -> None:
    letters = SollRow(label="Σ", strokes=None, crossings=3, zones=1, touches=2, overlaps=0)
    comp = SollRow(label="Komp", strokes=2, crossings=4, zones=2, touches=1, overlaps=1)
    assert soll_row_fields((letters, comp)) == {
        "soll_cross_letters": 3,
        "soll_zones_letters": 1,
        "soll_cross": 4,
        "soll_zones": 2,
        "soll_touch": 1,
        "soll_overlap": 1,
    }
