"""Tests for the snake follower (`tools.pairlab.schlange`).

Synthetic curves and fields only — no fixture, no DB, no solve of the chain.
Pinned here, each next to the failure it was added for:

* the banded metric equals its dense oracle (a wrong band is a wrong wave);
* reparametrisation keeps every corner as a node and `s0` monotone — the
  first prototype eroded every cusp and reported ink reversals 0, a false
  pass on the loop's primary sensor;
* the weld rule reproduces the assembler's pen runs;
* the corner offset follows the seam kind — a shared seam keeps the corner
  index, a lifted one shifts it by one; the two branches shipped swapped once
  and put every corner of a mixed run on the node next door;
* cut-back + assemble round-trips an unmoved seed to the same strokes;
* ductus order of the entries — an i-dot emitted before the body run costs
  0.06 xh of dtw on every word (prototype arm a);
* `corner_halo` 0 frees exactly the corner's own bending row;
* a straight stroke converges into a synthetic EDT valley without the cap;
* one bad case is a `skipped`/`failed` ROW, never an exception — an unscorable
  fixture case, a composition missing a glyph, a crash on either side of the
  derive; an exception here escapes `ProcessPoolExecutor.map` and takes the
  whole `--all` sweep down;
* the private helpers this stand-alone module borrows keep their signatures.
"""

from __future__ import annotations

import importlib
import inspect
from collections.abc import Sequence

import numpy as np
import pytest
from scipy.linalg import solve_banded
from scipy.ndimage import distance_transform_edt

from tools.pairlab import schlange
from tools.pairlab.follow import STATUS_FAILED, STATUS_SKIPPED
from tools.pairlab.schlange import (
    SnakeParams,
    bending_apply,
    bending_weights,
    coherence_stats,
    coverage_force,
    cut_back,
    ductus_order,
    evolve_curve,
    metric_banded,
    metric_dense,
    resample_curve,
    seed_curve,
    snake_payload,
    weld_pieces,
)
from tools.pairlab.trace import assemble_word_strokes
from tools.wordlab.cases import WordCase
from tools.wordlab.derive import WordDeriveResult


XH = 40.0
TX, TY, BASELINE_ROW = 30.0, 0.0, 110.0
REGISTRATION = {"tx": TX, "ty": TY, "baseline_row": BASELINE_ROW}


def _piece(
    seg: int,
    stroke: int,
    kind: str,
    pts: Sequence[Sequence[float]] | np.ndarray,
    *,
    corners: Sequence[int] = (),
    w_in: bool = False,
    w_out: bool = False,
    slot: int | None = None,
    key: str | None = None,
) -> dict:
    return {
        "seg": seg,
        "stroke": stroke,
        "kind": kind,
        "slot": slot,
        "key": key,
        "pts": np.asarray(pts, dtype=float),
        "corners": list(corners),
        "w_in": w_in,
        "w_out": w_out,
    }


# ----------------------------------------------------------------- operators


def test_the_banded_metric_equals_its_dense_oracle() -> None:
    rng = np.random.default_rng(3)
    n, beta_s, alpha_s = 23, 7.0**4, 1.5
    rhs = rng.normal(size=(n, 2))
    banded = solve_banded((2, 2), metric_banded(n, beta_s, alpha_s), rhs)
    dense = np.linalg.solve(metric_dense(n, beta_s, alpha_s), rhs)
    assert banded == pytest.approx(dense, abs=1e-9)


def test_bending_apply_is_the_weighted_normal_operator() -> None:
    rng = np.random.default_rng(5)
    n = 17
    x = rng.normal(size=(n, 2))
    w = rng.uniform(0.0, 4.0, size=n - 2)
    d2 = np.zeros((n - 2, n))
    for i in range(n - 2):
        d2[i, i : i + 3] = (1.0, -2.0, 1.0)
    assert bending_apply(x, w) == pytest.approx(d2.T @ (w[:, None] * (d2 @ x)), abs=1e-12)


def test_a_wave_step_moves_the_neighbours_with_the_node() -> None:
    """One unit force on one node: with ell = 7 the response spans the
    neighbourhood, with ell = 1 (the control) it is nearly a point."""
    n = 61
    f = np.zeros((n, 2))
    f[30, 0] = 1.0
    wide = solve_banded((2, 2), metric_banded(n, 7.0**4), f)[:, 0]
    narrow = solve_banded((2, 2), metric_banded(n, 1.0), f)[:, 0]
    assert wide[33] / wide[30] > 0.8  # three nodes away still moves with the peak
    assert narrow[33] / narrow[30] < 0.2


# ----------------------------------------------------------- reparametrise


def _vee(h: float = 0.8) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = np.linspace(0.0, 10.0, 41)
    left = np.column_stack([a, a])  # up to the apex (10, 10)
    right = np.column_stack([10.0 + a[1:], 10.0 - a[1:]])
    x = np.vstack([left, right])
    d = np.linalg.norm(np.diff(x, axis=0), axis=1)
    s0 = np.concatenate([[0.0], np.cumsum(d)])
    corner_s = np.array([s0[40]])
    return x, s0, corner_s


def test_reparametrisation_keeps_the_corner_as_a_node_and_s0_monotone() -> None:
    x, s0, corner_s = _vee()
    xn, s0n = resample_curve(x, s0, 0.8, corner_s)
    assert np.all(np.diff(s0n) > 0)
    apex = np.linalg.norm(xn - np.array([10.0, 10.0]), axis=1).min()
    assert apex < 1e-9
    spacing = np.linalg.norm(np.diff(xn, axis=0), axis=1)
    assert spacing.min() > 0.5 and spacing.max() < 1.1


def test_repeated_resampling_erodes_a_cusp_only_without_the_breakpoint() -> None:
    """The artefact of the first prototype, pinned: 300 resamplings without the
    corner as a breakpoint round the cusp off (the apex drifts inward); with it
    the apex stays exactly where the ductus put it."""
    x, s0, corner_s = _vee()
    kept, s_kept = x.copy(), s0.copy()
    lost, s_lost = x.copy(), s0.copy()
    # 0.9 px: the apex then never lands on a lattice point of the resampling
    # (at 0.7 it would, 14.14 = 20 × 0.707, and nothing would erode).
    for _ in range(300):
        kept, s_kept = resample_curve(kept, s_kept, 0.9, corner_s)
        lost, s_lost = resample_curve(lost, s_lost, 0.9, None)
    apex = np.array([10.0, 10.0])
    assert np.linalg.norm(kept - apex, axis=1).min() < 1e-9
    assert np.linalg.norm(lost - apex, axis=1).min() > 0.1


def test_corner_halo_zero_frees_exactly_the_corners_own_row() -> None:
    x, s0, corner_s = _vee()
    xn, s0n = resample_curve(x, s0, 0.8, corner_s)
    n = len(xn)
    j = int(np.searchsorted(s0n, corner_s[0]))
    w0 = bending_weights(n, s0n, corner_s, 4.0, 0)
    w1 = bending_weights(n, s0n, corner_s, 4.0, 1)
    assert list(np.flatnonzero(w0 == 0.0)) == [j - 1]
    assert list(np.flatnonzero(w1 == 0.0)) == [j - 2, j - 1, j]
    assert np.all(bending_weights(n, s0n, corner_s, 0.0, 0) == 0.0)


# ------------------------------------------------------------------ welding


def test_the_weld_rule_reproduces_the_assemblers_pen_runs() -> None:
    """[letter with a dot, connector, letter with a lift] → three runs: the dot
    (emitted as soon as it is seen — `ductus_order` sorts later), the body run
    across the seam, the second letter's lifted stroke."""
    pieces = [
        _piece(0, 0, "letter", [(0, 0), (1, 1)], w_out=True, key="i", slot=0),
        _piece(0, 1, "letter", [(0.5, 1.5), (0.5, 1.6)], key="i", slot=0),  # the dot: neither seam
        _piece(1, 0, "connector", [(1, 1), (2, 1)], w_in=True, w_out=True),
        _piece(2, 0, "letter", [(2, 1), (3, 0)], w_in=True, key="n", slot=1),
        _piece(2, 1, "letter", [(3, 0), (3.5, 1)], w_out=True, key="n", slot=1),
    ]
    curves = weld_pieces(pieces)
    shape = [[(p["seg"], p["stroke"]) for p in c] for c in curves]
    assert shape == [[(0, 1)], [(0, 0), (1, 0), (2, 0)], [(2, 1)]]


def test_the_weld_joins_a_letter_stroke_holding_the_seam_out() -> None:
    pieces = [
        _piece(0, 0, "letter", [(0, 0), (1, 1)], w_out=True, key="a", slot=0),
        _piece(1, 0, "connector", [(1, 1), (2, 1)], w_in=True, w_out=True),
        _piece(2, 0, "letter", [(2, 1), (3, 0)], w_in=True, w_out=True, key="b", slot=1),
        _piece(3, 0, "connector", [(3, 0), (4, 0)], w_in=True, w_out=True),
        _piece(4, 0, "letter", [(4, 0), (5, 1)], w_in=True, key="c", slot=2),
    ]
    assert [len(c) for c in weld_pieces(pieces)] == [5]


# ---------------------------------------------------------------- seed curve


def test_the_corner_offset_follows_each_seam_kind_in_one_welded_run() -> None:
    """`seed_curve` records every ductus corner as a SEED ARC LENGTH, and the
    index it reads that arc length at depends on the seam the piece arrives on:

    * shared seam — the piece's first point IS the tail, so it is dropped and
      the tail takes its place 1:1; `px_eff` keeps the length of `px`, corner
      index `c` still points at `px_eff[c]`, offset 0;
    * lifted seam — the tail is prepended in full, `px_eff` is one LONGER than
      `px`, so every corner index shifts by one.

    The two branches shipped swapped once (`1 if same length else 0`). On a
    welded run that mixes both seam kinds that moved every corner to the node
    next door — and the corner is the breakpoint both the arc-length
    reparametrisation and the free bending row key off. The run below is a
    straight rail on the baseline, so every arc length is a plain x-distance
    in crop px: nodes at 0 · 20 · 40 · 60 · 80 · 85 · 90 · 110.
    """
    pieces = [
        _piece(0, 0, "letter", [(0.0, 0), (0.5, 0), (1.0, 0)], w_out=True, key="a", slot=0),
        # shared seam: this piece starts exactly on the letter's last point
        _piece(1, 0, "connector", [(1.0, 0), (1.5, 0), (2.0, 0), (2.125, 0)], corners=[2], w_in=True, w_out=True),
        # lifted seam: this piece starts 5 px past the connector's last point
        _piece(2, 0, "letter", [(2.25, 0), (2.75, 0)], corners=[0], w_in=True, key="b", slot=1),
    ]
    seed = seed_curve(pieces, XH, TX, TY, BASELINE_ROW)

    # the shared piece's corner at 80.0, the one right behind the lift at 90.0
    assert seed["corner_s"] == pytest.approx([80.0, 90.0], abs=1e-9)
    # each arc length names the corner's OWN pixel, never its neighbour's; with
    # the branches swapped both corners collapse onto the seam node 85.0
    corner_px = [(110.0, 110.0), (120.0, 110.0)]
    for s, pt in zip(seed["corner_s"], corner_px, strict=True):
        assert seed["pts"][int(np.searchsorted(seed["cum"], s))] == pytest.approx(pt, abs=1e-9)


# ---------------------------------------------------------------- cut-back


def test_cut_back_and_assemble_round_trip_an_unmoved_seed() -> None:
    pieces = [
        _piece(0, 0, "letter", [(0.2, 0.2), (0.6, 0.5), (1.0, 0.3)], w_out=True, key="a", slot=0),
        _piece(1, 0, "connector", [(1.0, 0.3), (1.3, 0.35), (1.6, 0.3)], w_in=True, w_out=True),
        _piece(2, 0, "letter", [(1.6, 0.3), (2.0, 0.6), (2.4, 0.4)], w_in=True, key="b", slot=1),
    ]
    seed = seed_curve(pieces, XH, TX, TY, BASELINE_ROW)
    assert len(seed["pts"]) == 7  # the two shared seam anchors written once
    entries = ductus_order(cut_back(seed["pts"], seed["cum"], seed))
    direct = [
        {
            "kind": p["kind"],
            "segment_index": p["seg"],
            "slot_index": p["slot"],
            "key": p["key"],
            "stroke_index": p["stroke"],
            "points_px": schlange._to_px(p["pts"], XH, TX, TY, BASELINE_ROW),
        }
        for p in pieces
    ]
    for e, d in zip(entries, direct, strict=True):
        assert e["points_px"] == pytest.approx(d["points_px"], abs=1e-9)
    kw = {"traced_slots": {0, 1}, "xh": XH, "registration": REGISTRATION}
    round_trip, straight = assemble_word_strokes(entries, **kw), assemble_word_strokes(direct, **kw)
    assert len(round_trip) == len(straight) == 1
    assert np.asarray(round_trip[0]) == pytest.approx(np.asarray(straight[0]), abs=1e-9)


def test_ductus_order_puts_the_body_before_the_dot_it_was_emitted_after() -> None:
    dot = {"segment_index": 0, "stroke_index": 1, "kind": "letter"}
    body = {"segment_index": 0, "stroke_index": 0, "kind": "letter"}
    conn = {"segment_index": 1, "stroke_index": 0, "kind": "connector"}
    assert ductus_order([dot, conn, body]) == [body, dot, conn]


# -------------------------------------------------------------------- forces


def test_soft_ownership_with_one_neighbour_is_hard_ownership() -> None:
    rng = np.random.default_rng(11)
    x = np.column_stack([np.linspace(0, 40, 51), np.zeros(51)])
    cov = rng.uniform([0, -3], [40, 3], size=(200, 2))
    hard = coverage_force(x, cov, SnakeParams(cov_soft_k=0))
    soft = coverage_force(x, cov, SnakeParams(cov_soft_k=1))
    assert soft == pytest.approx(hard, abs=1e-12)
    assert np.linalg.norm(hard, axis=1).max() <= 1.0 + 1e-12


def test_coherence_is_zero_for_a_rigid_shift_and_reports_the_corners() -> None:
    x, s0, corner_s = _vee()
    seed = {"pts": x, "cum": s0, "corner_s": corner_s}
    stats = coherence_stats(x + np.array([2.0, -1.0]), s0, seed, XH)
    assert stats["ratio"] == pytest.approx(0.0, abs=1e-9)
    assert stats["ratio_corners"] == pytest.approx(0.0, abs=1e-9)
    assert stats["neighbour_angle_max_deg"] == pytest.approx(0.0, abs=1e-6)


# ----------------------------------------------------------------- evolve


def _line_field(row: int, shape: tuple[int, int] = (60, 140)) -> dict:
    skel = np.zeros(shape, dtype=bool)
    skel[row, 20:120] = True
    dist_raw = distance_transform_edt(~skel)
    ys, xs = np.nonzero(skel)
    return {"dist_raw": dist_raw, "cov_pts": np.column_stack([xs, ys]).astype(float)}


def test_a_straight_stroke_settles_into_the_valley_without_the_cap() -> None:
    fields = _line_field(30)
    pts = np.column_stack([np.linspace(24.0, 116.0, 116), np.full(116, 34.0)])
    d = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    seed = {
        "pts": pts,
        "cum": np.concatenate([[0.0], np.cumsum(d)]),
        "corner_s": np.zeros(0),
        "connector_spans": [],
        "pieces": [],
    }
    prm = SnakeParams(gamma=0.0, max_iter=4000)
    ev = evolve_curve(seed, fields, prm, xh=32.0)
    assert not any(s["hit_cap"] for s in ev["stages"])
    assert ev["stages"][-1]["stop"] in ("tol", "plateau")
    interior = ev["x"][5:-5]
    assert np.abs(interior[:, 1] - 30.0).max() < 0.15
    assert ev["stages"][-1]["residual_max_px"] is not None
    assert ev["wobble"]["curve_ripple_px"] < 0.05


def test_the_plateau_switch_off_leaves_only_tol_and_cap() -> None:
    fields = _line_field(30)
    pts = np.column_stack([np.linspace(24.0, 116.0, 116), np.full(116, 31.0)])
    d = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    seed = {
        "pts": pts,
        "cum": np.concatenate([[0.0], np.cumsum(d)]),
        "corner_s": np.zeros(0),
        "connector_spans": [],
        "pieces": [],
    }
    ev = evolve_curve(seed, fields, SnakeParams(gamma=0.0, max_iter=50, plateau_drop=0.0, sigmas_px=(1.0,)), xh=32.0)
    assert ev["stages"][0]["stop"] in ("tol", "cap")


# ---------------------------------------------------------------- payload


def test_the_payload_stamps_the_snakes_own_fields_and_excludes_failures() -> None:
    prm = SnakeParams(gamma=0.01)
    rows = [
        {
            "kind": "word",
            "specimen_id": "han",
            "word": "han",
            "registration_px": {},
            "xh_px": 32.0,
            "strokes": [[[0, 0], [1, 1]]],
            "status": "ok",
            "meta": {},
        },
        {
            "kind": "word",
            "specimen_id": "das",
            "word": "das",
            "registration_px": {},
            "xh_px": None,
            "strokes": [],
            "status": "failed",
            "detail": "no pen path",
        },
    ]
    payload = snake_payload(rows, style="suetterlin", source_id="suetterlin-1922", which="words", label="t", prm=prm)
    assert payload["tool"] == schlange.SCHLANGE_TOOL_NAME
    assert payload["frame"] == "word_registration"
    assert payload["weights"]["gamma"] == 0.01 and payload["weights"]["corner_halo"] == 0
    assert payload["provisional"] is True
    assert [r["specimen_id"] for r in payload["rows"]] == ["han"]
    assert payload["excluded"] == [{"specimen_id": "das", "status": "failed", "detail": "no pen path"}]


def test_every_param_is_a_cli_flag_and_round_trips() -> None:
    parser = schlange.build_parser()
    args = parser.parse_args(
        ["--gamma", "0.01", "--corner-halo", "1", "--sigmas", "2,1.5", "--no-bar-bridge", "--cov-soft-k", "4", "han"]
    )
    prm = schlange.params_from_args(args)
    assert (prm.gamma, prm.corner_halo, prm.sigmas_px, prm.bar_bridge, prm.cov_soft_k) == (
        0.01,
        1,
        (2.0, 1.5),
        False,
        4,
    )
    assert schlange.params_from_args(parser.parse_args(["han"])) == SnakeParams()


# ------------------------------------------------------------ case isolation


def _bare_case(case_id: str = "toy", *, scorable: bool = True) -> WordCase:
    return WordCase(
        id=case_id,
        word="i",
        kind="word",
        slots=[],
        templates={},
        style_ratio=[1, 1, 1],
        width_resolver="constant",
        nib_units=0.07,
        scorable=scorable,
    )


_DERIVED_KW = {
    "case": _bare_case(),
    "payloads": {},
    "composed": {"items": [], "missing": []},
    "report": None,
    "segments": None,
    "xh_px": XH,
    "baseline_row": BASELINE_ROW,
    "registration": {"tx": TX, "ty": TY, "xh_px": XH},
}
_DERIVED = WordDeriveResult(**_DERIVED_KW)


def test_an_unscorable_case_is_a_skipped_row_and_never_derived(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fixture sets deliberately carry `scorable=False` cases (unauthored
    templates). They must come back as a row, and the deriver must not even be
    asked — `tools.pairlab.follow.follow_case`'s rule."""
    monkeypatch.setattr(schlange, "derive_word", lambda case: pytest.fail("an unscorable case must not be derived"))
    row = schlange.follow_case(_bare_case(scorable=False))
    assert (row["status"], row["strokes"], row["xh_px"]) == (STATUS_SKIPPED, [], None)
    assert "unscorable" in row["detail"]


def test_a_crashing_case_is_a_failed_row_and_does_not_take_the_sweep_down(monkeypatch: pytest.MonkeyPatch) -> None:
    """An exception escaping `follow_case` would escape `ProcessPoolExecutor.map`
    and abort the whole `--all` run, so it is caught into one word's row — on
    both sides of the derive: the deriver itself and the snake behind it."""

    def _boom(case: WordCase) -> WordDeriveResult:
        raise RuntimeError("no ink")

    monkeypatch.setattr(schlange, "derive_word", _boom)
    rows = schlange.run_cases([_bare_case("a"), _bare_case("b")], SnakeParams())
    assert [r["specimen_id"] for r in rows] == ["a", "b"]
    assert {r["status"] for r in rows} == {STATUS_FAILED}
    assert rows[0]["detail"] == "RuntimeError: no ink"

    # the second guard: the derive succeeds, the snake behind it raises
    monkeypatch.setattr(schlange, "derive_word", lambda case: _DERIVED)
    monkeypatch.setattr(schlange, "_follow_derived", lambda case, result, prm, started: 1 / 0)
    row = schlange.follow_case(_bare_case())
    assert row["status"] == STATUS_FAILED and row["detail"].startswith("ZeroDivisionError")


def test_a_composition_missing_a_glyph_is_a_skipped_row(monkeypatch: pytest.MonkeyPatch) -> None:
    missing = WordDeriveResult(**{**_DERIVED_KW, "composed": {"missing": ["longs"]}})
    monkeypatch.setattr(schlange, "derive_word", lambda case: missing)
    monkeypatch.setattr(schlange, "_follow_derived", lambda case, result, prm, started: pytest.fail("must not run"))
    row = schlange.follow_case(_bare_case())
    assert row["status"] == STATUS_SKIPPED and "longs" in row["detail"]


# --------------------------------------------------------- borrowed helpers

BORROWED = {
    ("tools.laufform.harvest", "_chainable_runs"): ["case", "grids"],
    ("tools.laufform.harvest", "_grid_fits"): ["case", "result"],
    ("tools.laufform.harvest", "_word_record"): ["case", "strokes", "registration", "xh", "measurements"],
    ("tools.pairlab.analyze", "_to_px"): ["pts", "xh", "tx", "ty", "baseline_row"],
    ("tools.pairlab.chain", "_connector_spec"): ["result", "slot_a", "join_call"],
    ("tools.pairlab.chain", "_letter_spec"): [
        "case",
        "result",
        "slot_index",
        "bar_bridge",
        "x_scale",
        "seed_form",
        "affine",
    ],
    ("tools.pairlab.chain", "_prepare_fields"): ["case", "x_lo", "x_hi", "mark_strokes_px", "unit_px"],
    ("tools.pairlab.follow", "_registration_of"): ["result"],
    ("tools.pairlab.follow", "_restart_slots"): ["case"],
    ("tools.pairlab.follow", "_source_id_of"): ["fixtures_root", "style", "which"],
    ("tools.wordlab.cases", "_root_for"): ["fixtures_root", "style", "which"],
}


@pytest.mark.parametrize(("module", "name"), sorted(BORROWED))
def test_the_borrowed_private_helpers_keep_their_signatures(module: str, name: str) -> None:
    """A stand-alone module that silently breaks on a chain refactor is not
    stand-alone: whoever moves or reshapes one of these promotes it here too.

    ``schlange`` binds each helper once, at its own import time (``from
    tools.pairlab.chain import _connector_spec``), so a sibling test that
    reloads ``chain``/``follow`` in-process (``test_pairlab_chain.py``,
    ``test_pairlab_follow.py``) leaves ``schlange``'s copy stale relative to
    the freshly reloaded module — a full-suite-only flake unrelated to this
    module's own correctness. Reloading ``schlange`` here re-runs its
    ``from ... import`` lines against whatever is CURRENTLY in
    ``sys.modules``, so the identity check compares two fresh reads instead
    of one fresh and one collection-time read."""
    fn = getattr(__import__(module, fromlist=[name]), name)
    assert list(inspect.signature(fn).parameters) == BORROWED[(module, name)]
    assert getattr(importlib.reload(schlange), name) is fn
