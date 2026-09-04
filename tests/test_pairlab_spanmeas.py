"""``dspan``, the extension-normalized shape distance (rescue path of #488).

The four synthetic controls this sensor was pre-registered on
(`docs/reference/messjournal.md` §14 „Übergänge S1 — Vorregistrierung“) live
here, because they are the sensor's construction and must hold on every commit,
not only on a measurement day:

* **P1 — blind to the extension.** A connector that only grew a head draws the
  same shape over the shared stretch: ``dspan`` = 0, while ``dconn`` rises with
  the added arc. That rise is the artifact §14 „Übergänge J4“ had to clean by
  hand before its number could be read.
* **P2 — sensitive to the shape.** Deform the shared stretch and ``dspan``
  reports the deformation.
* **N1 — identity reads zero.** The measured curve fed in as the composed one
  must produce no signal; a sensor that fires on identity is measuring its own
  plumbing.
* **N2 — placement is not shape.** A pure translation must not move it —
  ``doff`` owns placement, this column owns shape.

The end-to-end run over a fixture root is fixture-gated like the other bench
tests: the roots are DB-derived and gitignored.
"""

from __future__ import annotations

import numpy as np
import pytest

from tools.pairlab.spanmeas import arc_length, clip_tail, common_span, compare_joins, dconn, dspan, summarise
from tools.wordlab.cases import DEFAULT_FIXTURES_DIR


def _line(n: int = 25) -> np.ndarray:
    """A straight unit-length polyline, the neutral carrier for the controls."""
    return np.column_stack([np.linspace(0.0, 1.0, n), np.zeros(n)])


def _with_head(points: np.ndarray, extra: float) -> np.ndarray:
    """The same curve, extended backwards along its first segment by ``extra``.

    This is what the J4 exit trim does to a connector: the letter stops writing
    its stub, so the join draws that piece — more arc at the head, the shared
    stretch untouched.
    """
    d = points[0] - points[1]
    d = d / np.hypot(*d)
    return np.vstack([points[0] + d * extra, points])


# ------------------------------------------------------------------- clipping


def test_clip_tail_keeps_exactly_the_requested_arc() -> None:
    clipped = clip_tail(_line(), 0.4)
    assert arc_length(clipped) == pytest.approx(0.4, abs=1e-12)
    assert clipped[-1] == pytest.approx(_line()[-1])


def test_clip_tail_cut_is_independent_of_the_sampling() -> None:
    """The cut is interpolated, so a coarse curve is cut at the same point."""
    coarse = clip_tail(_line(3), 0.37)
    fine = clip_tail(_line(201), 0.37)
    assert coarse[0] == pytest.approx(fine[0], abs=1e-12)


def test_clip_tail_passes_through_when_nothing_to_cut() -> None:
    line = _line()
    assert np.array_equal(clip_tail(line, 5.0), line)
    assert np.array_equal(clip_tail(line, 0.0), line)


def test_common_span_reduces_both_to_the_shorter_extension() -> None:
    short, long_ = _line(), _with_head(_line(), 0.5)
    a, b = common_span(long_, short)
    assert arc_length(a) == pytest.approx(arc_length(b), abs=1e-12)
    assert arc_length(a) == pytest.approx(1.0, abs=1e-12)


# ------------------------------------------------------- pre-registered gates


@pytest.mark.parametrize("extra", [0.05, 0.2, 0.5])
def test_p1_dspan_is_blind_to_a_pure_head_extension(extra: float) -> None:
    measured = _line()
    composed = _with_head(measured, extra)
    assert dspan(composed, measured) == pytest.approx(0.0, abs=1e-12)


def test_p1_dconn_is_the_one_that_moves() -> None:
    """The artifact the sensor exists to remove, shown on the same two curves."""
    measured = _line()
    grew = [dconn(_with_head(measured, extra), measured) for extra in (0.0, 0.05, 0.2, 0.5)]
    assert grew[0] == pytest.approx(0.0, abs=1e-12)
    assert grew == sorted(grew)
    assert grew[-1] > 0.1  # half an x-height of head reads as a shape change


def test_p2_dspan_reports_a_deformation_of_the_shared_stretch() -> None:
    """A ramp of height δ over the span reads as ≈ δ/2 — the mean of the ramp."""
    measured = _line()
    delta = 0.1
    composed = np.column_stack([measured[:, 0], measured[:, 0] * delta])
    assert dspan(composed, measured) == pytest.approx(delta / 2, abs=0.005)


def test_p2_dspan_grows_with_the_deformation() -> None:
    measured = _line()
    values = [dspan(np.column_stack([measured[:, 0], measured[:, 0] * d]), measured) for d in (0.02, 0.05, 0.1, 0.2)]
    assert values == sorted(values)


def test_n1_identity_reads_zero() -> None:
    measured = _line()
    assert dspan(measured, measured) == pytest.approx(0.0, abs=1e-12)
    assert dspan(measured.copy(), measured) == pytest.approx(0.0, abs=1e-12)


def test_n1_identity_reads_zero_on_a_curved_join() -> None:
    t = np.linspace(0.0, 1.0, 31)
    curve = np.column_stack([t, 0.3 * np.sin(np.pi * t)])
    assert dspan(curve, curve) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("shift", [(0.4, 0.0), (0.0, -0.7), (1.3, 2.1)])
def test_n2_a_pure_translation_does_not_move_it(shift: tuple[float, float]) -> None:
    t = np.linspace(0.0, 1.0, 31)
    measured = np.column_stack([t, 0.3 * np.sin(np.pi * t)])
    composed = np.column_stack([t, 0.2 * np.sin(np.pi * t)])
    before = dspan(composed, measured)
    after = dspan(composed + np.asarray(shift), measured)
    assert after == pytest.approx(before, abs=1e-12)


def test_a_degenerate_curve_yields_nan_not_a_crash() -> None:
    assert np.isnan(dspan(np.zeros((1, 2)), _line()))


# ----------------------------------------------------------------- row layer


def _composed(centerline: list[list[float]]) -> dict:
    return {
        "items": [
            {"slot_index": 0, "centerline": [[0.0, 0.0], [0.3, 0.0]]},
            {"pair": ["n", "e"], "from_slot": 0, "to_slot": 1, "centerline": centerline},
            {"slot_index": 1, "centerline": [[0.6, 0.0], [0.9, 0.0]]},
        ]
    }


class _Slot:
    def __init__(self, key: str) -> None:
        self.key = key
        self.position = None


def _measured_row(connector: list[list[float]], *, fit_ok: bool = True) -> dict:
    return {
        "slot": 0,
        "left_key": "n",
        "right_key": "e",
        "geometry": {"offset": [0.3, 0.0], "connector": connector},
        "measurements": {"fit_ok": fit_ok},
    }


def test_compare_joins_reports_both_columns_and_the_clip() -> None:
    measured = [[0.0, 0.0], [0.5, 0.0], [1.0, 0.0]]
    composed = _composed([[-0.4, 0.0], [0.0, 0.0], [0.5, 0.0], [1.0, 0.0]])
    rows = compare_joins(composed, [_Slot("n"), _Slot("e")], [_measured_row(measured)])
    assert len(rows) == 1
    assert rows[0]["dspan"] == 0.0  # the head is all that differs
    assert rows[0]["dconn"] > 0.0
    assert rows[0]["clipped"] == pytest.approx(0.4, abs=1e-9)


def test_compare_joins_drops_a_distrusted_dissection() -> None:
    measured = [[0.0, 0.0], [1.0, 0.0]]
    composed = _composed([[0.0, 0.0], [1.0, 0.0]])
    assert compare_joins(composed, [_Slot("n"), _Slot("e")], [_measured_row(measured, fit_ok=False)]) == []


def test_summarise_of_nothing_is_empty_not_zero() -> None:
    """A run with no comparable join must not report a median of 0.0."""
    assert summarise([]) == {"n": 0, "dspan_median": None, "dconn_median": None, "clipped_median": None, "n_clipped": 0}


# ------------------------------------------------------------ end to end (local)

fixtures_present = any(DEFAULT_FIXTURES_DIR.rglob("pair_instances.json"))


@pytest.mark.skipif(not fixtures_present, reason="word-bench fixtures are local-only (gitignored)")
def test_run_set_produces_rows_on_the_frozen_words() -> None:
    from tools.pairlab.spanmeas import run_set

    rows = run_set("words")
    assert rows
    assert all(0.0 <= r["dspan"] < 5.0 for r in rows)
    assert summarise(rows)["n"] == len(rows)
