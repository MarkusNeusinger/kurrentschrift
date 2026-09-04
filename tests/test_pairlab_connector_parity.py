"""pairlab draws the PRODUCTION Übergang, not a copy of it (audit Befund 18).

Until 2026-09-04 ``tools.pairlab.analyze._generate_connector`` claimed in its
docstring to be "the exact maths of ``core.compose.compose_word``'s join block
(same constants, same guards)". Those lines last moved on 2026-07-11;
``core.compose._connector_centerline`` was rebuilt three times afterwards
(#308, #358, #366) and today carries 18 parameters and branches into garland,
fork and Absatz. The dissection now REPLAYS production's own call
(``tools.pairlab.prodconn``) instead of re-deriving it, and this file is what
keeps that true:

* the recorder must not change what it records — a composition wrapped in
  ``recording()`` is item-for-item the composition without it;
* a replay at zero shift must return production's centerline point for point,
  on every join of every golden word — that is the "identical geometry in,
  identical curve out" parity;
* moving both letters by the same horizontal amount must move the whole join
  by that amount and nothing else, which is the one property the shift
  bookkeeping (``dx`` for B's x, the line itself for B's y) can get wrong;
* and the frozen mirror must stay measurably DIFFERENT, so nobody can quietly
  point the dissection back at it.

Hermetic: everything runs on the committed golden fixture's frozen payloads —
no DB, no gitignored bench root.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pytest

from core.compose import _endpoint_tangent, compose_word
from core.shaping import GlyphSlot
from tools.pairlab.analyze import _generate_connector
from tools.pairlab.prodconn import JoinCall, label_calls, recording, replay


FIXTURE = Path(__file__).parent / "fixtures" / "compose_golden.json.gz"
# Resampling budget for comparing two curves of unequal point count. Only used
# for the mirror-divergence reading; the parity assertions compare verbatim.
SHAPE_SAMPLES = 64
# The word ruler's sensitivity window (audit 2026-09-02, Befund 2): a shape
# difference below the floor is invisible to it, one above the ceiling is
# larger than anything it can resolve.
RULER_WINDOW = (0.05, 0.12)


def _entries() -> list[dict]:
    return json.loads(gzip.decompress(FIXTURE.read_bytes()))["words"]


def _slots(entry: dict) -> list[GlyphSlot]:
    return [GlyphSlot(**s) for s in entry["slots"]]


def _compose_recorded(entry: dict) -> tuple[dict, dict[int, JoinCall]]:
    slots = _slots(entry)
    with recording() as calls:
        composed = compose_word(slots, entry["payloads"], provenance=True)
    return composed, label_calls(composed, calls)


def _body_lines(composed: dict) -> dict[int, list[list]]:
    """slot index -> its non-diacritic centerlines, writing order."""
    lines: dict[int, list[list]] = {}
    for item in composed["items"]:
        if "slot_index" in item and not item.get("diacritic"):
            lines.setdefault(int(item["slot_index"]), []).append(item["centerline"])
    return lines


def _resample(points) -> np.ndarray:
    a = np.asarray(points, dtype=float).reshape(-1, 2)
    arc = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(a, axis=0).T))])
    if arc[-1] <= 1e-12:
        return np.repeat(a[:1], SHAPE_SAMPLES, axis=0)
    t = np.linspace(0.0, arc[-1], SHAPE_SAMPLES)
    return np.column_stack([np.interp(t, arc, a[:, 0]), np.interp(t, arc, a[:, 1])])


def _curve_distance(a, b) -> np.ndarray:
    """Pointwise distance of two arc-length-resampled curves, in x-height units."""
    return np.hypot(*(_resample(a) - _resample(b)).T)


# ------------------------------------------------------- the recorder is inert


@pytest.mark.parametrize("entry", _entries(), ids=lambda e: e["text"])
def test_recording_leaves_the_composition_untouched(entry: dict) -> None:
    plain = compose_word(_slots(entry), entry["payloads"], provenance=True)
    with recording():
        taped = compose_word(_slots(entry), entry["payloads"], provenance=True)
    assert taped == plain


def test_recording_restores_the_production_function_after_a_failure() -> None:
    import core.compose as compose

    before = compose._connector_centerline
    with pytest.raises(RuntimeError):
        with recording():
            assert compose._connector_centerline is not before  # the swap is live inside
            raise RuntimeError("boom")
    assert compose._connector_centerline is before


def test_label_calls_rejects_a_composition_it_did_not_record() -> None:
    entry = next(e for e in _entries() if len(e["slots"]) > 1)
    composed, _ = _compose_recorded(entry)
    with pytest.raises(ValueError, match="disagree"):
        label_calls(composed, [])


# ------------------------------------------------------------------- parity


@pytest.mark.parametrize("entry", _entries(), ids=lambda e: e["text"])
def test_replay_at_zero_shift_is_the_production_curve(entry: dict) -> None:
    """Identical geometry in, identical curve out — verbatim, not approximately."""
    _, joins = _compose_recorded(entry)
    for call in joins.values():
        assert [tuple(p) for p in replay(call)] == list(call.centerline)


@pytest.mark.parametrize("entry", _entries(), ids=lambda e: e["text"])
def test_replay_labels_every_generated_join(entry: dict) -> None:
    composed, joins = _compose_recorded(entry)
    generated = [it for it in composed["items"] if it.get("pair") and it["pair"][1] is not None]
    assert sorted(joins) == sorted(int(it["from_slot"]) for it in generated)
    for slot_a, call in joins.items():
        assert call.from_slot == slot_a < call.to_slot


@pytest.mark.parametrize("entry", _entries(), ids=lambda e: e["text"])
def test_a_shared_horizontal_shift_moves_the_whole_join(entry: dict) -> None:
    """B's x lives on ``dx`` and B's y on the line — the one thing the shift
    bookkeeping can get wrong. Moving BOTH letters right by the same amount
    must translate the join and change nothing else; a vertical shift is
    deliberately NOT asserted, because the grammar's thresholds
    (HIGH_EXIT_Y, DESCENDER_EXIT_Y, the baseline) are absolute heights and a
    y-move may legitimately pick a different branch.
    """
    _, joins = _compose_recorded(entry)
    for call in joins.values():
        moved = np.asarray(replay(call, exit_shift=(0.37, 0.0), entry_shift=(0.37, 0.0)), dtype=float)
        base = np.asarray(call.centerline, dtype=float)
        assert moved.shape == base.shape
        assert np.allclose(moved - base, [0.37, 0.0], atol=1e-9)


# --------------------------------------------- the frozen mirror stays frozen


def _mirror_rows() -> list[dict]:
    """Per golden join: how far the 2026-07-11 mirror sits from production."""
    rows: list[dict] = []
    for entry in _entries():
        composed, joins = _compose_recorded(entry)
        bodies = _body_lines(composed)
        for slot_a, call in joins.items():
            a_line = [tuple(p) for p in bodies[slot_a][-1]]
            b_line = [tuple(p) for p in bodies[call.to_slot][0]]
            taut = _generate_connector(
                a_line[-1], _endpoint_tangent(a_line, at_end=True), b_line[0], _endpoint_tangent(b_line, at_end=False)
            )
            d = _curve_distance(call.centerline, taut)
            rows.append(
                {
                    "word": entry["text"],
                    "pair": f"{call.pair[0]}→{call.pair[1]}",
                    "median": float(np.median(d)),
                    "max": float(d.max()),
                }
            )
    return rows


def test_the_frozen_mirror_is_not_the_production_connector() -> None:
    """Befund 18 as a standing number, so the mirror cannot be re-adopted quietly.

    Measured 2026-09-04 on the golden words: 6 of 44 joins sit at or above the
    ruler window's 0.05 xh floor, two of them above its 0.12 xh ceiling
    (`sitzen` ſ→i 0.177 median / 0.398 max, `lesen` ſ→e 0.173 / 0.397). On the
    frozen Sütterlin bench sets — where pairlab actually runs — 89 of 248 joins
    differ, 23 of them above the ceiling; see `messjournal.md` §14 „Übergänge
    P-Spiegel“.
    """
    rows = _mirror_rows()
    above_floor = [r for r in rows if r["median"] >= RULER_WINDOW[0]]
    assert above_floor, "the mirror reproduces production everywhere — re-read Befund 18 before deleting this test"
    assert max(r["median"] for r in rows) > RULER_WINDOW[1]
