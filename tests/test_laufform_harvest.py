"""Tests for the Laufform harvest (`tools.laufform.harvest`, issue #278 Stage B).

Everything here runs WITHOUT the frozen fixtures, a DB or the network: a
synthetic `WordCase` whose ink is rasterised from a known path plus a
stand-in `WordDeriveResult` (the pattern of `tests/test_pairlab_chain.py`)
feed the real harvest, and `iter_fixture_word_cases` / `derive_word` are
monkeypatched on the module so the fixture loader is never touched.

Two halves:

* the **pure** pieces of the chain path — the run narrowing, the gate cascade,
  the pen-run assembly across a seam, the wire-cap guard and the px → word-unit
  transform — each on hand-built data, so a gate can be exercised without
  having to talk the optimiser into producing a degenerate connector; and
* the **slot path's byte identity**: `GOLDEN_SLOT_PATH` was captured from the
  harvest BEFORE the Stage-B restructure and is asserted unchanged. The slot
  path is what has produced every stored Laufform row so far — the refactor
  must not have moved a single digit of it.
"""

from __future__ import annotations

import json

import numpy as np
import pytest
from PIL import Image, ImageDraw

from core.compose import _endpoint_tangent
from core.extract import skeleton_and_width
from core.shaping import GlyphSlot
from tools.laufform import harvest as harvest_mod
from tools.laufform.harvest import (
    MAX_ANCHOR_SPIKE_RATIO,
    MAX_STROKE_POINTS,
    MAX_WORD_STROKES,
    CaseHarvest,
    HarvestOptions,
    _chainable_runs,
    _is_diacritic,
    _px_to_word_units,
    anchor_spike_ratio,
    assemble_word_strokes,
    cap_word_strokes,
    harvest_case,
    letter_gate,
)
from tools.pairlab.analyze import _generate_connector
from tools.pairlab.chain import ChainSegment, ChainWordFit
from tools.wordlab.cases import WordCase
from tools.wordlab.derive import WordDeriveResult


XH = 40.0
BASELINE_ROW = 110.0
X_ORIGIN = 30.0
ADVANCE = 1.6
REGISTRATION = {"tx": X_ORIGIN, "ty": 0.0, "baseline_row": BASELINE_ROW}


# ------------------------------------------------------- a synthetic specimen


def _slot(key: str | None = "a", *, space: bool = False, joins: bool = True) -> GlyphSlot:
    return GlyphSlot(key=key, text=key or " ", position="medial", ligature=False, space=space, joins=joins)


def _letter_anchors(k: int = 6) -> np.ndarray:
    """The one template letter: an arc whose first anchor sits at x = 0, so the
    placement offset the harvest recovers is exactly the item's first x."""
    t = np.linspace(0.0, 1.0, k)
    return np.column_stack([0.9 * t, 0.15 + 0.55 * np.sin(np.pi * t)])


def _rasterise(polyline_units: np.ndarray, *, width_px: int = 5):
    px = X_ORIGIN + polyline_units[:, 0] * XH
    py = BASELINE_ROW - polyline_units[:, 1] * XH
    w = int(px.max() + 3 * XH)
    h = int(BASELINE_ROW + 1.5 * XH)
    img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(img).line([(float(a), float(b)) for a, b in zip(px, py, strict=True)], fill=255, width=width_px)
    skel, width_map = skeleton_and_width(np.asarray(img) > 127)
    return skel, width_map, (h, w)


def _synthetic_word(shifts: list[tuple[float, float]], *, k: int = 6, width_px: int = 5):
    """`(case, result)` for a run of `len(shifts)` letters.

    The COMPOSITION places the same template every `ADVANCE`; the INK is that
    composition displaced per slot by `shifts[i]` and joined by the production
    connector — so a fit has something real to find, and the harvest's own
    frame recovery is exercised rather than stubbed.
    """
    anchors = _letter_anchors(k)
    n = len(shifts)
    placed = [anchors + np.array([i * ADVANCE, 0.0]) for i in range(n)]
    truth = [p + np.asarray(shifts[i], dtype=float) for i, p in enumerate(placed)]
    path: list[np.ndarray] = [truth[0]]
    for i in range(n - 1):
        a_line = [tuple(p) for p in truth[i]]
        b_line = [tuple(p) for p in truth[i + 1]]
        conn = np.asarray(
            _generate_connector(
                a_line[-1], _endpoint_tangent(a_line, at_end=True), b_line[0], _endpoint_tangent(b_line, at_end=False)
            ),
            dtype=float,
        ).reshape(-1, 2)
        path.append(conn[1:-1])
        path.append(truth[i + 1])
    skel, width_map, shape = _rasterise(np.vstack(path), width_px=width_px)

    half_w = (0.5 * width_px) / XH
    case = WordCase(
        id="synthetic",
        word="a" * n,
        kind="word",
        slots=[_slot("a") for _ in range(n)],
        templates={
            "a": {
                "glyph": "a",
                "anchors": anchors.tolist(),
                "half_widths": [half_w] * k,
                "trace_meta": {"stroke_starts": [0], "corner_anchors": []},
            }
        },
        style_ratio=[1.0, 1.0, 1.0],
        width_resolver="constant",
        nib_units=half_w,
        rect=[0, 0, shape[1], shape[0]],
        baseline_y=int(BASELINE_ROW),
        midband_y=int(BASELINE_ROW - XH),
        crop=np.zeros(shape),
        skel=skel,
        width_map=width_map,
    )
    result = WordDeriveResult(
        case=case,
        payloads={"a": {"centerlines_template": [anchors.tolist()]}},
        composed={
            "missing": [],
            "items": [{"rings": [], "slot_index": i, "centerline": p.tolist()} for i, p in enumerate(placed)],
        },
        report={"loss": 0.0},
        segments=None,
        xh_px=XH,
        baseline_row=BASELINE_ROW,
        registration={"tx": X_ORIGIN, "ty": 0.0, "xh_px": XH},
    )
    return case, result


def _to_px(pts_units) -> np.ndarray:
    a = np.asarray(pts_units, dtype=float).reshape(-1, 2)
    return np.column_stack([X_ORIGIN + a[:, 0] * XH, BASELINE_ROW - a[:, 1] * XH])


def _entry(kind: str, segment: int, points_units, *, slot=None, key=None, stroke_index: int = 0) -> dict:
    return {
        "kind": kind,
        "segment_index": segment,
        "slot_index": slot,
        "key": key,
        "stroke_index": stroke_index,
        "points_px": _to_px(points_units),
    }


# ----------------------------------------------------------- the gate cascade


def test_letter_gate_passes_a_clean_letter() -> None:
    assert (
        letter_gate(
            converged_local=True,
            geo_rmse_px=1.0,
            rmse_max=2.2,
            at_bound=False,
            anchors_ok=True,
            connector_reasons=[None, None],
        )
        == "ok"
    )


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"converged_local": False}, "not_converged_local"),
        ({"geo_rmse_px": 9.0}, "geo_rmse"),
        ({"at_bound": True}, "at_bound"),
        ({"anchors_ok": False}, "anchor_count"),
        ({"connector_reasons": [None, "backward_arc"]}, "connector_degenerate"),
    ],
)
def test_letter_gate_names_the_first_failure(kwargs: dict, expected: str) -> None:
    base = {
        "converged_local": True,
        "geo_rmse_px": 1.0,
        "rmse_max": 2.2,
        "at_bound": False,
        "anchors_ok": True,
        "connector_reasons": [None, None],
    }
    assert letter_gate(**{**base, **kwargs}) == expected


def test_letter_gate_order_is_fixed() -> None:
    """A letter failing several gates reports the FIRST one, so the per-reason
    histogram counts it once and the code is stable across runs."""
    assert (
        letter_gate(
            converged_local=False,
            geo_rmse_px=9.0,
            rmse_max=2.2,
            at_bound=True,
            anchors_ok=False,
            connector_reasons=["seam_share"],
        )
        == "not_converged_local"
    )
    # …and the two like-for-like gates are told apart rather than merged
    assert (
        letter_gate(
            converged_local=True, geo_rmse_px=9.0, rmse_max=2.2, at_bound=True, anchors_ok=True, connector_reasons=[]
        )
        == "geo_rmse"
    )


# ------------------------------------------------- „Anker im leeren Papier"


def _even_chain(n: int = 10, step: float = 0.1) -> np.ndarray:
    """A chain whose every step is exactly `step` — spike ratio 1.0."""
    return np.column_stack([np.arange(n, dtype=float) * step, np.zeros(n)])


def test_anchor_spike_ratio_of_an_even_chain_is_one() -> None:
    assert anchor_spike_ratio(_even_chain(), [0]) == pytest.approx(1.0)


def test_anchor_spike_ratio_of_a_real_letter_is_modest() -> None:
    """The template arc steps unevenly (fast at the ends, slow over the
    shoulder) and must stay far below the gate — an honest fit pays nothing."""
    assert 1.0 <= anchor_spike_ratio(_letter_anchors(), [0]) < MAX_ANCHOR_SPIKE_RATIO


def test_anchor_spike_ratio_flags_an_out_and_back_needle() -> None:
    """The measured failure form: ONE anchor leaves the stroke and returns one
    step later, every other anchor sitting cleanly on the line."""
    chain = _even_chain()
    chain[5, 1] += 1.0
    assert anchor_spike_ratio(chain, [0]) > MAX_ANCHOR_SPIKE_RATIO
    # …and the chain it was cut from is untouched
    assert anchor_spike_ratio(_even_chain(), [0]) == pytest.approx(1.0)


def test_a_pen_lift_is_not_a_discontinuity() -> None:
    """The case that would otherwise reject every multi-stroke glyph (i, u, sz,
    t, ae): the hand lifts and sets down a whole x-height away, which is a jump
    of exactly the needle's magnitude but no discontinuity of the LINE."""
    body = _even_chain(5)
    dot = _even_chain(4) + np.array([0.2, 1.0])
    chain = np.vstack([body, dot])
    assert anchor_spike_ratio(chain, [0, 5]) == pytest.approx(1.0)
    # read as ONE stroke the very same geometry is over the gate — the
    # exclusion is what separates a pen lift from a broken fit
    assert anchor_spike_ratio(chain, [0]) > MAX_ANCHOR_SPIKE_RATIO


def test_anchor_spike_ratio_at_the_threshold_boundary() -> None:
    """Eight steps of 1 and one of 8: median 1, largest 8, ratio exactly 8.0.
    The gate is `> MAX_ANCHOR_SPIKE_RATIO`, so this one is still accepted."""
    chain = np.column_stack([np.array([0.0, 1, 2, 3, 4, 5, 6, 7, 8, 16]), np.zeros(10)])
    assert anchor_spike_ratio(chain, [0]) == pytest.approx(MAX_ANCHOR_SPIKE_RATIO)
    assert not anchor_spike_ratio(chain, [0]) > MAX_ANCHOR_SPIKE_RATIO
    chain[-1, 0] += 0.5  # a hair over
    assert anchor_spike_ratio(chain, [0]) > MAX_ANCHOR_SPIKE_RATIO


def test_anchor_spike_ratio_of_a_chain_with_nothing_to_judge() -> None:
    assert anchor_spike_ratio(np.zeros((0, 2)), [0]) == 0.0
    assert anchor_spike_ratio(np.array([[0.0, 0.0]]), [0]) == 0.0
    # every anchor its own stroke: no step lies WITHIN one
    assert anchor_spike_ratio(_even_chain(3), [0, 1, 2]) == 0.0
    # a chain that stands still and then jumps is the failure itself
    standstill = np.array([[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [1.0, 0.0]])
    assert anchor_spike_ratio(standstill, [0]) == float("inf")
    assert anchor_spike_ratio(np.zeros((4, 2)), [0]) == 0.0


def test_the_slot_path_rejects_an_anchor_in_blank_paper(monkeypatch: pytest.MonkeyPatch) -> None:
    """End to end: a fit that passes convergence and `--rmse-max` but carries a
    needle is no measurement of the hand — it becomes neither an occurrence nor
    a median, and the diag row says by how much it was over."""
    case, result = _synthetic_word([(0.06, 0.0), (-0.04, 0.03)])
    monkeypatch.setattr(harvest_mod, "derive_word", lambda c: result)
    real_fit = harvest_mod.fit_template_to_instance

    def with_a_needle(*args, **kwargs):
        fr = real_fit(*args, **kwargs)
        fr.anchors = fr.anchors.copy()
        fr.anchors[2, 1] += 6.0  # six x-heights off the stroke and back
        return fr

    monkeypatch.setattr(harvest_mod, "fit_template_to_instance", with_a_needle)
    out = harvest_case(case, HarvestOptions(path="slot", rmse_max=3.0))

    assert [r["gate"] for r in out.diag_rows] == ["anchor_spike", "anchor_spike"]
    assert all(r["accepted"] is False for r in out.diag_rows)
    assert all(r["anchor_spike_ratio"] > MAX_ANCHOR_SPIKE_RATIO for r in out.diag_rows)
    assert out.occurrences == []
    assert out.fits_by_key == {}
    assert out.word_record is None


def test_a_clean_slot_fit_reports_its_spike_ratio(monkeypatch: pytest.MonkeyPatch) -> None:
    """The same case without the needle passes and still carries the number, so
    a run can read how much air the ACCEPTED fits had, not only the rejected."""
    case, result = _synthetic_word([(0.06, 0.0), (-0.04, 0.03)])
    monkeypatch.setattr(harvest_mod, "derive_word", lambda c: result)
    out = harvest_case(case, HarvestOptions(path="slot", rmse_max=3.0))

    assert [r["gate"] for r in out.diag_rows] == ["ok", "ok"]
    assert all(1.0 <= r["anchor_spike_ratio"] <= MAX_ANCHOR_SPIKE_RATIO for r in out.diag_rows)
    assert len(out.occurrences) == 2


# --------------------------------------------------------------- run cutting


def test_chainable_runs_cuts_at_a_slot_without_a_window() -> None:
    """An unauthored letter cannot be a chain segment — and `fit_word_chain`
    would refuse the whole run over it, so the run is cut there instead."""
    case, _ = _synthetic_word([(0.0, 0.0)] * 4)
    assert _chainable_runs(case, {0: {}, 1: {}, 2: {}, 3: {}}) == [[0, 1, 2, 3]]
    assert _chainable_runs(case, {0: {}, 1: {}, 3: {}}) == [[0, 1], [3]]
    assert _chainable_runs(case, {}) == []


def test_chainable_runs_respects_the_word_runs() -> None:
    """A space still breaks the run — `_chainable_runs` only narrows."""
    case, _ = _synthetic_word([(0.0, 0.0)] * 3)
    case.slots.insert(1, _slot(None, space=True))
    grids = {0: {}, 2: {}, 3: {}}
    assert _chainable_runs(case, grids) == [[0], [2, 3]]


# ------------------------------------------------------------ pen assembly


def test_assemble_welds_the_seam_and_keeps_the_diacritic_apart() -> None:
    """`last body stroke → connector → first body stroke` is ONE pen run with
    the shared seam sample dropped; a dot and an interior pen lift are not."""
    body_a = [(0.2, 0.2), (0.6, 0.7), (1.0, 0.3)]
    dot = [(0.5, 1.4), (0.6, 1.45)]
    conn = [(1.0, 0.3), (1.3, 0.35), (1.6, 0.3)]
    body_b0 = [(1.6, 0.3), (2.0, 0.7)]
    body_b1 = [(2.1, 0.9), (2.4, 0.4)]
    entries = [
        _entry("letter", 0, body_a, slot=0, key="i", stroke_index=0),
        _entry("letter", 0, dot, slot=0, key="i", stroke_index=1),
        _entry("connector", 1, conn),
        _entry("letter", 2, body_b0, slot=1, key="n", stroke_index=0),
        _entry("letter", 2, body_b1, slot=1, key="n", stroke_index=1),
    ]
    strokes = assemble_word_strokes(entries, traced_slots={0, 1}, xh=XH, registration=REGISTRATION)

    assert len(strokes) == 3
    spine, dot_out, lift = strokes
    # 3 + (3 - 1) + (2 - 1): both seam samples deduplicated
    assert len(spine) == 3 + 2 + 1
    assert spine[0] == pytest.approx([0.2, 0.2], abs=1e-3)
    assert spine[-1] == pytest.approx([2.0, 0.7], abs=1e-3)
    # no repeated sample anywhere along the welded run
    assert not any(np.allclose(a, b) for a, b in zip(spine[:-1], spine[1:], strict=True))
    assert len(dot_out) == 2 and dot_out[0] == pytest.approx([0.5, 1.4], abs=1e-3)
    assert len(lift) == 2 and lift[0] == pytest.approx([2.1, 0.9], abs=1e-3)


def test_assemble_drops_an_unfitted_letter_and_its_connectors() -> None:
    """A letter the chain never fitted has no geometry to show, and the
    connectors on either side go with it — they would dangle into a letter that
    is not there. That (and only that) is an honest fragment."""
    entries = [
        _entry("letter", 0, [(0.2, 0.2), (1.0, 0.3)], slot=0, key="a", stroke_index=0),
        _entry("connector", 1, [(1.0, 0.3), (1.6, 0.3)]),
        _entry("letter", 2, [(1.6, 0.3), (2.4, 0.4)], slot=1, key="b", stroke_index=0),
        _entry("connector", 3, [(2.4, 0.4), (3.0, 0.4)]),
        _entry("letter", 4, [(3.0, 0.4), (3.8, 0.5)], slot=2, key="c", stroke_index=0),
    ]
    strokes = assemble_word_strokes(entries, traced_slots={0, 2}, xh=XH, registration=REGISTRATION)
    assert len(strokes) == 2
    assert [len(s) for s in strokes] == [2, 2]
    assert strokes[0][0] == pytest.approx([0.2, 0.2], abs=1e-3)
    assert strokes[1][0] == pytest.approx([3.0, 0.4], abs=1e-3)


def test_assemble_lifts_after_a_restart_capital() -> None:
    """Korb #5 (Säbel S→ä): after a restart-class capital the writer sets the
    pen down fresh near the baseline (Grundlinie). The run must end at the capital's body
    and the connector's retrace prefix (its descent to the lowest point) never
    enters the trace — only the fresh set-down (Ansatz) rising into the next letter."""
    body_s = [(0.2, 0.2), (0.8, 1.6), (1.4, 1.8)]
    conn = [(1.4, 1.8), (1.45, 1.0), (1.5, 0.05), (1.7, 0.25), (1.9, 0.5)]
    body_a = [(1.9, 0.5), (2.4, 0.6)]
    entries = [
        _entry("letter", 0, body_s, slot=0, key="S", stroke_index=0),
        _entry("connector", 1, conn),
        _entry("letter", 2, body_a, slot=1, key="ae", stroke_index=0),
    ]
    strokes = assemble_word_strokes(entries, traced_slots={0, 1}, xh=XH, registration=REGISTRATION, restart_slots={0})
    assert len(strokes) == 2
    cap, ansatz = strokes
    assert cap[-1] == pytest.approx([1.4, 1.8], abs=1e-3)  # ends at the capital's ductus end
    assert ansatz[0] == pytest.approx([1.5, 0.05], abs=1e-3)  # the fresh set-down at the baseline turn
    assert ansatz[-1] == pytest.approx([2.4, 0.6], abs=1e-3)  # welded into the next letter

    # Without the restart classification the same geometry stays one pen run.
    welded = assemble_word_strokes(entries, traced_slots={0, 1}, xh=XH, registration=REGISTRATION)
    assert len(welded) == 1


def test_is_diacritic_mirrors_the_chain_rule() -> None:
    """First stroke never, a later stroke floating entirely above the midband
    always (`chain._letter_cut_anchors`' rule on a polyline)."""
    high = _entry("letter", 0, [(0.5, 1.4), (0.6, 1.5)], slot=0, key="i", stroke_index=1)
    assert _is_diacritic(high, XH, REGISTRATION)
    assert not _is_diacritic({**high, "stroke_index": 0}, XH, REGISTRATION)
    touching = _entry("letter", 0, [(0.5, 1.4), (0.6, 0.9)], slot=0, key="i", stroke_index=1)
    assert not _is_diacritic(touching, XH, REGISTRATION)
    assert not _is_diacritic(_entry("connector", 1, [(0.5, 1.4), (0.6, 1.5)]), XH, REGISTRATION)


# ------------------------------------------------------------ frame + caps


def test_px_to_word_units_round_trips() -> None:
    units = np.array([[0.0, 0.0], [1.5, 1.0], [3.25, -0.4]])
    px = _to_px(units)
    back = _px_to_word_units(px[:, 0], px[:, 1], XH, REGISTRATION)
    assert back == pytest.approx(units, abs=1e-4)
    # the baseline maps to y = 0 and the midband to y = 1 by construction
    assert _px_to_word_units(np.array([X_ORIGIN]), np.array([BASELINE_ROW]), XH, REGISTRATION)[0] == pytest.approx(
        [0.0, 0.0]
    )
    assert _px_to_word_units(np.array([X_ORIGIN]), np.array([BASELINE_ROW - XH]), XH, REGISTRATION)[0] == pytest.approx(
        [0.0, 1.0]
    )


def test_cap_word_strokes_downsamples_a_long_run(capsys: pytest.CaptureFixture) -> None:
    long_run = [[float(i) * 1e-3, 0.0] for i in range(MAX_STROKE_POINTS + 500)]
    out = cap_word_strokes([long_run], label="x")
    assert len(out) == 1
    assert len(out[0]) == MAX_STROKE_POINTS
    assert out[0][0] == long_run[0] and out[0][-1] == long_run[-1]  # endpoints kept
    assert "downsampled" in capsys.readouterr().out


def test_cap_word_strokes_keeps_the_longest_runs(capsys: pytest.CaptureFixture) -> None:
    strokes = [[[0.0, 0.0]] * (2 + i) for i in range(MAX_WORD_STROKES + 5)]
    out = cap_word_strokes(strokes, label="x")
    assert len(out) == MAX_WORD_STROKES
    assert [len(s) for s in out] == sorted(len(s) for s in out)  # writing order preserved
    assert min(len(s) for s in out) > 2  # the shortest ones went
    assert "keeping" in capsys.readouterr().out


def test_cap_word_strokes_is_a_no_op_below_the_caps(capsys: pytest.CaptureFixture) -> None:
    strokes = [[[0.0, 0.0], [1.0, 1.0]], [[2.0, 0.0], [3.0, 1.0]]]
    assert cap_word_strokes(strokes) == strokes
    assert capsys.readouterr().out == ""


# ------------------------------------------------- the chain path end to end


def _segment(kind: str, *, slot=None, key=None, converged_local=True, geo_rmse_px=0.5, anchors=None, points=None):
    return ChainSegment(
        kind=kind,
        slot_index=slot,
        key=key,
        anchor_slice=(0, 0),
        sample_slice=(0, 0),
        fitted_anchors=anchors,
        polyline_px=_to_px(points if points is not None else [(0.0, 0.0), (1.0, 0.5)]),
        geo_rmse_px=geo_rmse_px,
        cov_rmse_px=0.6,
        n_cov=20,
        cov_rmse_local_px=0.6,
        n_cov_local=20,
        converged=True,
        converged_local=converged_local,
        max_anchor_delta=0.1,
    )


def _fake_chain_fit(
    case, *, bad_connector: bool = False, bad_letter: int | None = None, needle_letter: int | None = None
) -> ChainWordFit:
    """A three-letter chain with hand-built geometry — the only way to put a
    KNOWN degenerate connector in front of the gate cascade."""
    anchors = np.asarray(case.templates["a"]["anchors"], dtype=float)
    bodies = [[(0.2 + i * ADVANCE, 0.3), (0.6 + i * ADVANCE, 0.7), (1.0 + i * ADVANCE, 0.3)] for i in range(3)]
    healthy = [[(1.0 + i * ADVANCE, 0.3), (1.4 + i * ADVANCE, 0.25), (1.8 + i * ADVANCE, 0.3)] for i in range(2)]
    # A long straight diagonal running BACKWARDS through the left letter — the
    # §5c failure verbatim, which `connector_qc` calls `backward_arc`.
    connectors = [list(healthy[0]), list(healthy[1])]
    if bad_connector:
        connectors[0] = [(1.0, 0.3), (0.6, 0.0), (0.2, -0.3)]

    segments: list[ChainSegment] = []
    entries: list[dict] = []
    for i in range(3):
        fitted = anchors + np.array([0.01, 0.0])
        if needle_letter == i:
            # „Anker im leeren Papier": one anchor out of the stroke and back.
            fitted = fitted.copy()
            fitted[2] = fitted[2] + np.array([0.0, 6.0])
        segments.append(
            _segment("letter", slot=i, key="a", anchors=fitted, points=bodies[i], converged_local=bad_letter != i)
        )
        entries.append(_entry("letter", 2 * i, bodies[i], slot=i, key="a"))
        if i < 2:
            # writing order: L C L C L — letters at the even positions
            segments.append(_segment("connector", points=connectors[i]))
            entries.append(_entry("connector", 2 * i + 1, connectors[i]))
    assert [s.kind for s in segments] == ["letter", "connector", "letter", "connector", "letter"]
    return ChainWordFit(
        case=case,
        slots=[0, 1, 2],
        segments=segments,
        slot_shift_units={0: (0.0, 0.0), 1: (0.0, 0.0), 2: (0.0, 0.0)},
        slot_at_bound={0: False, 1: False, 2: False},
        global_shift_units=(0.0, 0.0),
        cut_indices=[(5, 0), (5, 0)],
        connector_units=[np.asarray(c, dtype=float) for c in connectors],
        stroke_polylines_px=entries,
        converged=True,
        converged_local=bad_letter is None,
        fit_meta={"n_params": 100, "seconds": 0.5},
    )


def _run_chain(monkeypatch: pytest.MonkeyPatch, **fit_kwargs) -> CaseHarvest:
    case, result = _synthetic_word([(0.0, 0.0)] * 3)
    monkeypatch.setattr(harvest_mod, "derive_word", lambda c: result)
    monkeypatch.setattr(harvest_mod, "fit_word_chain", lambda c, run, **kw: _fake_chain_fit(case, **fit_kwargs))
    return harvest_case(case, HarvestOptions(path="chain", rmse_max=2.2))


def test_chain_path_accepts_every_clean_letter(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _run_chain(monkeypatch)
    assert [r["gate"] for r in out.diag_rows] == ["ok", "ok", "ok"]
    assert len(out.occurrences) == 3
    assert len(out.fits_by_key["a"]) == 3
    assert out.word_record is not None
    assert out.word_record["measurements"]["fit_path"] == "chain"
    assert out.word_record["measurements"]["run_slots"] == [[0, 1, 2]]
    # the whole run is ONE pen path: three letters and the two joins between them
    assert len(out.word_record["strokes"]) == 1
    assert out.word_record["measurements"]["traced_slots"] == [0, 1, 2]
    assert out.word_record["measurements"]["fitted_slots"] == [0, 1, 2]
    assert all(o["measurements"]["fit_path"] == "chain" for o in out.occurrences)


def test_the_chain_path_rejects_an_anchor_in_blank_paper(monkeypatch: pytest.MonkeyPatch) -> None:
    """The gate has to sit on the path that actually produced the data.

    Every stored occurrence of the Sütterlin harvest carries
    `fit_path == "chain"` (245 of 245) — the slot path wrote none of them. A
    spike check that lives only in `_harvest_case_slots` therefore rejects
    nothing in production, however well calibrated it is, which is exactly how
    the capital S in „Sprünge" reached the Laufform with an anchor twelve
    pixels from the nearest ink.
    """
    out = _run_chain(monkeypatch, needle_letter=1)
    assert [r["gate"] for r in out.diag_rows] == ["ok", "anchor_spike", "ok"]
    # It reaches neither the occurrence layer nor the Laufform medians.
    assert len(out.occurrences) == 2
    assert len(out.fits_by_key["a"]) == 2
    assert out.word_record["measurements"]["fitted_slots"] == [0, 2]
    # …but it stays in the INSPECTION layer: the chain path separates what was
    # solved from what was accepted precisely so a gated letter remains visible
    # to the admin instead of silently vanishing from the trace.
    assert out.word_record["measurements"]["traced_slots"] == [0, 1, 2]
    # The run says how far over it was, on every fitted row.
    ratios = [r["anchor_spike_ratio"] for r in out.diag_rows]
    assert ratios[1] > harvest_mod.MAX_ANCHOR_SPIKE_RATIO
    assert all(r <= harvest_mod.MAX_ANCHOR_SPIKE_RATIO for r in (ratios[0], ratios[2]))


def test_a_degenerate_connector_rejects_both_adjacent_letters(monkeypatch: pytest.MonkeyPatch) -> None:
    """The seam is a shared parameter — a runaway connector has already been
    paid for out of the two letters' own tails, so they go with it."""
    out = _run_chain(monkeypatch, bad_connector=True)
    gates = [r["gate"] for r in out.diag_rows]
    assert gates == ["connector_degenerate", "connector_degenerate", "ok"]
    assert [r["conn_reason"] for r in out.diag_rows][:1] == ["backward_arc"]
    assert [o["measurements"]["slot"] for o in out.occurrences] == [2]
    assert len(out.fits_by_key["a"]) == 1
    # …but the TRACE still shows what the chain solved, all three letters of it
    record = out.word_record
    assert record["measurements"]["fitted_slots"] == [2]
    assert record["measurements"]["traced_slots"] == [0, 1, 2]
    assert len(record["strokes"]) == 1


def test_one_failing_letter_leaves_the_rest_of_the_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """The chain is one solve, but the gate is per letter: a capital that did
    not converge must not cost the letters after it."""
    out = _run_chain(monkeypatch, bad_letter=0)
    assert [r["gate"] for r in out.diag_rows] == ["not_converged_local", "ok", "ok"]
    assert [o["measurements"]["slot"] for o in out.occurrences] == [1, 2]
    record = out.word_record
    assert record["measurements"]["gates"] == {"0": "not_converged_local", "1": "ok", "2": "ok"}
    assert record["measurements"]["unfitted_slots"] == [0]
    assert record["measurements"]["traced_slots"] == [0, 1, 2]
    # the run is one continuous pen path — the rejected letter is FLAGGED, not
    # cut out (3 body samples each, 3 per connector, both seams deduplicated)
    assert len(record["strokes"]) == 1
    assert len(record["strokes"][0]) == 3 + (3 - 1) + (3 - 1) + (3 - 1) + (3 - 1)


def test_a_failing_middle_letter_keeps_the_pen_path_whole(monkeypatch: pytest.MonkeyPatch) -> None:
    """The regression this file exists for: a letter whose gate bites in the
    MIDDLE of a run used to take its two connectors with it and leave three
    fragments where the hand drew one line. The gate decides what becomes a
    measurement, not what the trace shows."""
    out = _run_chain(monkeypatch, bad_letter=1)
    assert [r["gate"] for r in out.diag_rows] == ["ok", "not_converged_local", "ok"]

    # the occurrence layer is untouched: the wobbly letter is still no statistic
    assert [o["measurements"]["slot"] for o in out.occurrences] == [0, 2]
    assert len(out.fits_by_key["a"]) == 2

    record = out.word_record
    assert record["measurements"]["fitted_slots"] == [0, 2]
    assert record["measurements"]["unfitted_slots"] == [1]
    assert record["measurements"]["traced_slots"] == [0, 1, 2]
    assert record["measurements"]["gates"] == {"0": "ok", "1": "not_converged_local", "2": "ok"}
    assert record["measurements"]["converged_local"] == {"0": True, "1": False, "2": True}

    # ONE body stroke, not three, and the seams are still deduplicated ACROSS
    # the formerly dropped letter
    assert len(record["strokes"]) == 1
    spine = record["strokes"][0]
    assert len(spine) == 3 + (3 - 1) + (3 - 1) + (3 - 1) + (3 - 1)
    assert not any(np.allclose(a, b) for a, b in zip(spine[:-1], spine[1:], strict=True))
    assert spine[0] == pytest.approx([0.2, 0.3], abs=1e-3)
    assert spine[-1] == pytest.approx([0.2 + 2 * ADVANCE + 0.8, 0.3], abs=1e-3)


def test_chain_path_on_real_ink(monkeypatch: pytest.MonkeyPatch) -> None:
    """The unstubbed wiring: grid windows → `fit_word_chain` → gates →
    occurrences + a welded word record, on rasterised ink of a known shape."""
    case, result = _synthetic_word([(0.06, 0.0), (-0.04, 0.03)])
    monkeypatch.setattr(harvest_mod, "derive_word", lambda c: result)
    out = harvest_case(case, HarvestOptions(path="chain", rmse_max=2.5))

    assert [r["gate"] for r in out.diag_rows] == ["ok", "ok"]
    assert len(out.occurrences) == 2
    assert len(out.word_record["strokes"]) == 1  # letter → connector → letter
    anchors = np.asarray(case.templates["a"]["anchors"], dtype=float)
    for occ in out.occurrences:
        fitted = np.asarray(occ["anchors"], dtype=float)
        assert fitted.shape == anchors.shape
        # centered: the median offset against the chart row is gone
        assert np.max(np.abs(np.median(fitted - anchors, axis=0))) < 1e-3
    meta = out.word_record["measurements"]
    assert meta["cut_indices"] == [[[5, 0]]]
    assert meta["converged_local"] == {"0": True, "1": True}
    assert meta["n_params"] > 0


def test_an_unscorable_case_yields_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    case, result = _synthetic_word([(0.0, 0.0), (0.0, 0.0)])
    case.scorable = False
    monkeypatch.setattr(harvest_mod, "derive_word", lambda c: result)
    for path in ("slot", "chain"):
        out = harvest_case(case, HarvestOptions(path=path))
        assert out == CaseHarvest({}, [], None, [])


def test_a_failed_composition_yields_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    case, result = _synthetic_word([(0.0, 0.0), (0.0, 0.0)])
    result.report = {"failed": True}
    monkeypatch.setattr(harvest_mod, "derive_word", lambda c: result)
    assert harvest_case(case, HarvestOptions(path="chain")).occurrences == []
    result.report = {"loss": 0.0}
    result.composed["missing"] = ["a"]
    assert harvest_case(case, HarvestOptions(path="slot")).occurrences == []


# ------------------------------------------------ the slot path, byte for byte

# Captured from `harvest("suetterlin", 1, 3.0)` on the two-letter synthetic case
# below, BEFORE the Stage-B restructure split the per-word loop into
# `harvest_case`. Every stored Laufform row and every stored occurrence came out
# of this path; the restructure is allowed to add a path, never to move it.
GOLDEN_SLOT_PATH = json.loads("""
{"drafts": {"a": {"anchors": [[-0.0076, 0.1467], [0.1741, 0.4759], [0.3637, 0.6722], [0.5368, 0.672],
 [0.7241, 0.4748], [0.9092, 0.1481]], "n_occurrences": 2}},
 "occurrences": [
  {"glyph_key": "a", "glyph": "a", "position": "medial", "variant": 0, "y0": 83, "y1": 104, "x0": 32, "x1": 68,
   "anchors": [[-0.0018, 0.1546], [0.1715, 0.4783], [0.3641, 0.6736], [0.5375, 0.6712], [0.7218, 0.4728],
    [0.9126, 0.1404]], "half_widths": [],
   "measurements": {"specimen_id": "synthetic", "slot": 0, "prev_key": null, "next_key": "a",
    "shift_xh": [-0.0009, 0.0003], "registration_px": [2.0, 0.0], "geo_rmse_px": 0.48, "xh_px": 40.0}},
  {"glyph_key": "a", "glyph": "a", "position": "medial", "variant": 0, "y0": 81, "y1": 102, "x0": 92, "x1": 128,
   "anchors": [[-0.0134, 0.1388], [0.1767, 0.4736], [0.3633, 0.6708], [0.5362, 0.6728], [0.7264, 0.4768],
    [0.9058, 0.1557]], "half_widths": [],
   "measurements": {"specimen_id": "synthetic", "slot": 1, "prev_key": "a", "next_key": null,
    "shift_xh": [0.0008, 0.0008], "registration_px": [-2.0, -2.0], "geo_rmse_px": 0.45, "xh_px": 40.0}}],
 "word_records": [
  {"kind": "word", "specimen_id": "synthetic", "word": "aa", "slots": ["a", "a"],
   "strokes": [[[0.0473, 0.1549], [0.2205, 0.4786], [0.4131, 0.6739], [0.5865, 0.6715], [0.7708, 0.4731],
     [0.9617, 0.1407]],
    [[1.5374, 0.1896], [1.7276, 0.5243], [1.9141, 0.7216], [2.087, 0.7236], [2.2773, 0.5275], [2.4567, 0.2065]]],
   "provenance": "traced",
   "measurements": {"registration_px": {"tx": 30.0, "ty": 0.0, "baseline_row": 110}, "xh_px": 40.0,
    "fitted_slots": [0, 1], "unfitted_slots": [], "geo_rmse_px_by_slot": {"0": 0.48, "1": 0.45}}}]}
""")


def test_slot_path_is_byte_identical_to_the_pre_stage_b_harvest(monkeypatch: pytest.MonkeyPatch) -> None:
    case, result = _synthetic_word([(0.06, 0.0), (-0.04, 0.03)])
    monkeypatch.setattr(harvest_mod, "iter_fixture_word_cases", lambda **kw: iter([case]))
    monkeypatch.setattr(harvest_mod, "derive_word", lambda c: result)

    drafts, occurrences, word_records, diag_rows = harvest_mod.harvest("suetterlin", 1, 3.0)
    assert {"drafts": drafts, "occurrences": occurrences, "word_records": word_records} == GOLDEN_SLOT_PATH
    # the diagnostics are new, and additive: they say nothing the old path did not do
    assert [(r["slot"], r["gate"], r["accepted"]) for r in diag_rows] == [(0, "ok", True), (1, "ok", True)]


def test_harvest_pools_over_cases_in_input_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """The medians must not depend on `--jobs`: `pool.map` yields in input
    order, and the accumulation is the same loop either way."""
    case_a, result_a = _synthetic_word([(0.06, 0.0), (-0.04, 0.03)])
    case_b, result_b = _synthetic_word([(0.02, -0.02)])
    case_b.id = "synthetic-b"
    results = {"synthetic": result_a, "synthetic-b": result_b}
    monkeypatch.setattr(harvest_mod, "iter_fixture_word_cases", lambda **kw: iter([case_a, case_b]))
    monkeypatch.setattr(harvest_mod, "derive_word", lambda c: results[c.id])

    drafts, occurrences, word_records, _ = harvest_mod.harvest("suetterlin", 1, 3.0)
    assert drafts["a"]["n_occurrences"] == 3
    assert [o["measurements"]["specimen_id"] for o in occurrences] == ["synthetic", "synthetic", "synthetic-b"]
    assert [w["specimen_id"] for w in word_records] == ["synthetic", "synthetic-b"]
