"""Tests for the ink follower (`tools.pairlab.follow`, tintenfolger.md §3).

Everything here runs WITHOUT fixtures, DB or network: the follower is a second
solve over the chain problem, so the synthetic word of `test_pairlab_chain`
(rasterised ink of a known path, hand-built case + composition) exercises the
whole route — the re-linearised rebuild, the proximal term, the retrace guard,
the round loop and the candidate file the trace bench reads.

Three of them are load-bearing:

* the ROUNDS-0 identity, because „the follower changed nothing" has to be a
  testable statement rather than a claim;
* the gradient decomposition on the REBUILT problem, because a wrong gradient
  stalls L-BFGS-B silently and looks exactly like „the follower does not help";
* the `KS_FOLLOW_*` isolation, because a follower sweep that moved a `CHAIN_*`
  would re-tune the measurement path the follower is graded against.
"""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace

import numpy as np
import pytest

from core.fit import DEFAULT_LAMBDA_REG
from core.quality_suetterlin import MIN_RETRACE_PAIRS
from tests.test_pairlab_chain import UNIT_PX, _flat_fields, _synthetic_word
from tools.pairlab.chain import ChainSegmentSpec, build_chain_problem, fit_word_chain, gradient_decomposition
from tools.pairlab.follow import (
    CANDIDATE_FRAME,
    FollowWeights,
    _source_id_of,
    _with,
    apply_retrace_guard,
    build_follow_problem,
    candidate_payload,
    follow_case,
    follow_derived,
    follow_word_chain,
    parse_sweep,
    retrace_anchor_mask,
    retrace_sample_mask,
)
from tools.pairlab.trace import assemble_word_strokes


TWO_LETTER_SHIFTS = [(0.10, 0.0), (-0.08, 0.04)]


@pytest.fixture(scope="module")
def synthetic():
    """One synthetic two-letter word and its chain solve, shared by the module.

    The chain fit is an INPUT to every follower call here, so solving it once is
    not a shortcut: `follow_word_chain` never mutates the problem it restarts
    from (`respec_from_solution` reads, the guard writes to the REBUILT one).
    """
    case, result, windows, _truth = _synthetic_word(TWO_LETTER_SHIFTS)
    fit = fit_word_chain(case, [0, 1], result=result, windows_px=windows, keep_solve=True)
    assert fit is not None and fit.problem is not None
    return case, result, windows, fit


def _chain_strokes(result, fit) -> list[list[list[float]]]:
    """The chain fit's own assembled pen path — the harvest's assembly, verbatim."""
    return assemble_word_strokes(
        fit.stroke_polylines_px,
        traced_slots=set(fit.slots),
        xh=result.xh_px,
        registration={
            "tx": result.registration["tx"],
            "ty": result.registration["ty"],
            "baseline_row": result.baseline_row,
        },
    )


# ------------------------------------------------------------ the identity arm


def test_rounds_zero_returns_the_chain_fit_verbatim(synthetic) -> None:
    """The baseline arm is an IDENTITY, not a re-derivation.

    With no round to run there is nothing to re-linearise, so the follower must
    hand back the chain's own geometry — segments, pen-down polylines and the
    assembled trace — rather than recompute something almost equal to it.
    """
    case, result, windows, fit = synthetic
    followed = follow_word_chain(
        case, [0, 1], result=result, windows_px=windows, fit=fit, weights=FollowWeights(rounds=0)
    )
    assert followed is not None
    assert followed.rounds == []
    assert followed.fit_meta["n_rounds"] == 0
    assert followed.segments is fit.segments
    assert followed.stroke_polylines_px is fit.stroke_polylines_px
    assert followed.slot_shift_units == fit.slot_shift_units
    assert followed.global_shift_units == fit.global_shift_units
    assert followed.converged == fit.converged and followed.converged_local == fit.converged_local
    assert followed.strokes_units == _chain_strokes(result, fit)


def test_a_fit_without_its_solve_is_a_caller_error(synthetic) -> None:
    """A restart needs the problem the optimum came from — never a rebuild of it."""
    case, result, windows, fit = synthetic
    naked = fit_word_chain(case, [0, 1], result=result, windows_px=windows)
    assert naked is not None and naked.problem is None
    with pytest.raises(ValueError, match="keep_solve"):
        follow_word_chain(case, [0, 1], result=result, windows_px=windows, fit=naked)


# ---------------------------------------------------------------- one round


def test_a_round_moves_the_samples_towards_the_ink(synthetic) -> None:
    """A released round descends: total energy and the ink term both fall.

    `e_geo` is the distance-transform half of the objective — the follower's
    whole purpose is to buy some of it back where the chain's form prior held
    the path off the measured ink.
    """
    case, result, windows, fit = synthetic
    followed = follow_word_chain(
        case,
        [0, 1],
        result=result,
        windows_px=windows,
        fit=fit,
        weights=FollowWeights(rounds=1, prox=0.01 * DEFAULT_LAMBDA_REG),
    )
    assert followed is not None
    assert len(followed.rounds) == 1
    record = followed.rounds[0]
    assert record["energy_after"] <= record["energy_before"]
    assert record["e_geo_after"] <= record["e_geo_before"]
    assert record["max_anchor_motion_units"] > 0.0
    assert record["hit_iteration_cap"] is False
    assert followed.strokes_units and all(len(s) >= 2 for s in followed.strokes_units)


def test_the_proximal_term_prices_displacement_from_the_chain_optimum(synthetic) -> None:
    """`e_reg` is zero at the rebuilt problem's start and positive after motion.

    That IS the change of meaning §3 asks for: the term no longer measures the
    distance to the chart form (which is where the chain's `e_reg` was zero),
    but the distance to the geometry solve 1 ended at.
    """
    _case, _result, _windows, fit = synthetic
    problem, _mask = build_follow_problem(fit.problem, fit.params, FollowWeights(rounds=1))
    assert problem.energy_terms(problem.x0)["e_reg"] == 0.0

    moved = problem.x0.copy()
    head = 2 + 2 * problem.n_blocks
    moved[head:] += 0.05  # every free anchor leaves the chain optimum
    assert problem.energy_terms(moved)["e_reg"] > 0.0
    # …and „the chain optimum" is meant literally: the rebuilt problem starts on
    # the very plan anchors solve 1 ended at, seam for seam.
    assert np.allclose(problem.plan_anchors(problem.x0), fit.problem.plan_anchors(fit.params))


def test_the_round_loop_stops_when_nothing_moved(synthetic) -> None:
    """`FOLLOW_ROUND_EPS_UNITS` ends the loop: a round that moved less than the
    ruler can see must not buy another rebuild."""
    case, result, windows, fit = synthetic
    followed = follow_word_chain(
        case, [0, 1], result=result, windows_px=windows, fit=fit, weights=FollowWeights(rounds=3, round_eps_units=10.0)
    )
    assert followed is not None
    assert len(followed.rounds) == 1
    assert followed.fit_meta["stopped_early"] is True
    assert followed.fit_meta["rounds_requested"] == 3


# ------------------------------------------------------------- the retrace guard


def _out_and_back(x0: float = 0.6, k: int = 12) -> np.ndarray:
    """A `t`-like stem written up and back 0.04 xh beside itself, then a tail.

    The stem is a retrace zone by any definition; the tail runs away from it and
    is the control half of the assertion — a guard that cages everything says
    nothing about retraces.
    """
    up = np.column_stack([np.full(k, x0), np.linspace(0.0, 1.2, k)])
    down = np.column_stack([np.full(k, x0 + 0.04), np.linspace(1.2, 0.05, k)])
    tail = np.column_stack([np.linspace(x0 + 0.10, x0 + 1.4, k), np.linspace(0.05, 0.5, k)])
    return np.vstack([up, down, tail])


def _retrace_problem(prox: float) -> tuple:
    anchors = _out_and_back()
    spec = ChainSegmentSpec(
        kind="letter", anchors=anchors, slot_index=0, key="t", half_widths=np.full(len(anchors), 0.07)
    )
    problem = build_chain_problem(
        [spec], unit_px=UNIT_PX, x_origin_px=4.3, baseline_y_px=45.7, lambda_reg=prox, **_flat_fields()
    )
    mask = retrace_anchor_mask(problem, prox_units=0.15)
    return problem, mask


def test_the_retrace_guard_keeps_its_anchors_at_the_full_chain_lambda() -> None:
    """The guard's realisation, asserted directly: per-anchor Tikhonov weights.

    A caged anchor's effective weight is `lambda_reg · reg_w` = the chain's own
    λ; every other letter anchor is released to λ_prox. The scaling lives in
    `reg_w` (not in `lambda_reg`) precisely so λ_prox = 0 — arm ①'s first rung —
    stays expressible with the guard still standing.
    """
    prox = 0.1 * DEFAULT_LAMBDA_REG
    problem, mask = _retrace_problem(prox)
    assert mask.any(), "the out-and-back stem must be detected as a retrace zone"
    assert not mask.all(), "the tail is not a retrace and must stay released"

    apply_retrace_guard(problem, mask, prox_weight=prox)
    assert problem.lambda_reg == pytest.approx(DEFAULT_LAMBDA_REG)
    effective = problem.lambda_reg * problem.reg_w
    assert np.allclose(effective[mask], DEFAULT_LAMBDA_REG)
    assert np.allclose(effective[~mask], prox)


def test_the_guard_survives_a_zero_proximal_weight() -> None:
    """At λ_prox = 0 the released anchors carry no term at all and the caged ones
    keep the full chain λ — the combination a `lambda_reg = 0` formulation could
    not express."""
    problem, mask = _retrace_problem(0.0)
    apply_retrace_guard(problem, mask, prox_weight=0.0)
    effective = problem.lambda_reg * problem.reg_w
    assert np.allclose(effective[mask], DEFAULT_LAMBDA_REG)
    assert np.allclose(effective[~mask], 0.0)


def test_the_guard_is_off_when_the_caller_switches_it_off(synthetic) -> None:
    _case, _result, _windows, fit = synthetic
    _problem, mask = build_follow_problem(
        fit.problem, fit.params, FollowWeights(rounds=1, prox=0.1, retrace_guard=False)
    )
    assert not mask.any()


def test_a_graze_thinner_than_the_minimum_is_not_a_retrace() -> None:
    """The bench's own pass rule: fewer than `MIN_RETRACE_PAIRS` contiguous
    flagged samples is a coincidental touch, not doubly-written ink."""
    # 13 px up and 13 px back down, 2 px beside itself — a stem, in crop pixels.
    px = np.concatenate([np.zeros(13), np.full(13, 2.0)])
    py = np.concatenate([np.arange(13.0), np.arange(12.0, -1.0, -1.0)])
    assert retrace_sample_mask(px, py, [0], prox_px=3.0, min_pairs=MIN_RETRACE_PAIRS).any()
    assert not retrace_sample_mask(px, py, [0], prox_px=3.0, min_pairs=99).any()
    # …and a straight line has no anti-parallel partner to begin with
    assert not retrace_sample_mask(np.linspace(0.0, 40.0, 40), np.zeros(40), [0], prox_px=3.0).any()


# ------------------------------------------------------- the discipline check


def test_the_gradient_decomposition_reproduces_the_rebuilt_gradient(synthetic) -> None:
    """§11's build rule on the FOLLOWER's problem, at both ends of a round.

    `gradient_decomposition` raises unless the seven weighted forces re-add to
    the gradient L-BFGS-B actually followed — including the guard's per-anchor
    reg weights, which is the one thing this module changes about the objective.
    """
    case, result, windows, fit = synthetic
    weights = FollowWeights(rounds=1, prox=0.1 * DEFAULT_LAMBDA_REG)
    problem, mask = build_follow_problem(fit.problem, fit.params, weights)
    at_start = gradient_decomposition(problem, problem.x0)
    assert at_start["residual_rel"] < 1e-9

    followed = follow_word_chain(
        case, [0, 1], result=result, windows_px=windows, fit=fit, weights=weights, keep_solve=True
    )
    assert followed is not None and followed.params is not None
    at_optimum = gradient_decomposition(followed.problem, followed.params)
    assert at_optimum["residual_rel"] < 1e-9
    assert mask.shape == (len(problem.anchors_free),)


def test_two_identical_runs_produce_identical_strokes(synthetic) -> None:
    """No RNG, no wall clock in the geometry: byte-identical traces or the
    follower cannot be compared against itself across arms."""
    case, result, windows, fit = synthetic
    weights = FollowWeights(rounds=1, prox=0.1 * DEFAULT_LAMBDA_REG)
    first = follow_word_chain(case, [0, 1], result=result, windows_px=windows, fit=fit, weights=weights)
    second = follow_word_chain(case, [0, 1], result=result, windows_px=windows, fit=fit, weights=weights)
    assert first is not None and second is not None
    assert json.dumps(first.strokes_units) == json.dumps(second.strokes_units)
    assert first.rounds[0]["max_anchor_motion_units"] == second.rounds[0]["max_anchor_motion_units"]


# ------------------------------------------------------------ the whole word


def test_follow_derived_produces_a_storable_row(synthetic) -> None:
    """The word pipeline: grid windows → runs → follower → welded pen path →
    the harvest's own record shape (rounded registration, integer baseline row)."""
    case, result, _windows, _fit = synthetic
    info = follow_derived(case, result, weights=FollowWeights(rounds=1))
    assert info["status"] == "ok"
    assert info["specimen_id"] == case.id and info["word"] == case.word
    assert info["strokes"] and all(len(s) >= 2 for s in info["strokes"])
    assert set(info["registration_px"]) == {"tx", "ty", "baseline_row"}
    assert isinstance(info["registration_px"]["baseline_row"], int)
    assert info["xh_px"] == pytest.approx(round(float(result.xh_px), 2))
    assert info["meta"]["fit_path"] == "follow"
    assert info["meta"]["provisional"] is True
    assert info["meta"]["run_slots"] == [[0, 1]]


def test_the_word_pipeline_mirrors_the_harvest_at_rounds_zero(synthetic) -> None:
    """The plumbing claim, tested rather than asserted in prose.

    At rounds 0 the follower replaces the fit with the fit, so its whole word
    trace must be the harvest's own `chain_word_strokes` output byte for byte —
    which is only true if the grid windows, the run cutting, the restart-capital
    rule, the welding and the wire caps really are the harvest's and not a
    second implementation of them.
    """
    from tools.laufform.harvest import HarvestOptions, chain_word_strokes

    case, result, _windows, _fit = synthetic
    harvest_strokes, _meta = chain_word_strokes(case, result, HarvestOptions(path="chain"))
    info = follow_derived(case, result, weights=FollowWeights(rounds=0))
    assert info["status"] == "ok"
    assert info["strokes"] == harvest_strokes


def test_an_unscorable_case_is_a_row_not_an_exception() -> None:
    """One word must never take a sweep down (the harvest's and the bench's rule)."""
    case, _result, _windows, _truth = _synthetic_word([(0.0, 0.0)])
    case.scorable = False
    info = follow_case(case)
    assert info["status"] == "skipped"
    assert "unauthored" in info["detail"]
    assert info["strokes"] == []


# --------------------------------------------------------- the candidate file


def test_the_candidate_frame_literal_matches_the_bench() -> None:
    """Re-declared, never imported — so the equality is pinned here instead."""
    from tools.tracebench.candidates import CANDIDATE_FRAME as BENCH_FRAME

    assert CANDIDATE_FRAME == BENCH_FRAME


def test_the_candidate_file_round_trips_through_the_bench_provider(synthetic, tmp_path) -> None:
    """The emitted JSON is read by `tools.tracebench.candidates.file_provider`
    with no failed row — the contract that makes a follower run scoreable at
    all."""
    from tools.tracebench.candidates import file_provider

    case, result, _windows, _fit = synthetic
    info = follow_derived(case, result, weights=FollowWeights(rounds=1))
    payload = candidate_payload(
        [info], style="suetterlin", source_id="suetterlin-1922", which="words", weights=FollowWeights()
    )
    assert payload["frame"] == CANDIDATE_FRAME
    assert payload["tool"] == "pairlab.follow"
    assert payload["provisional"] is True
    assert payload["excluded"] == []
    path = tmp_path / "follow.json"
    path.write_text(json.dumps(payload))

    reference = SimpleNamespace(entries={case.id: object()})
    candidates = file_provider(path)(reference, [case.id])
    candidate = candidates[case.id]
    assert candidate.status == "ok", candidate.detail
    assert candidate.strokes == info["strokes"]
    assert candidate.xh_px == pytest.approx(info["xh_px"])
    assert candidate.meta["label"] == "follow"


def test_a_row_without_a_pen_path_is_excluded_and_counted() -> None:
    """A failed word is never written as an empty candidate (which would score
    as a catastrophic trace); it is counted by reason instead."""
    payload = candidate_payload(
        [{"specimen_id": "muss", "status": "failed", "detail": "no pen path", "strokes": []}],
        style="suetterlin",
        source_id="suetterlin-1922",
        which="words",
    )
    assert payload["rows"] == []
    assert payload["excluded"] == [{"specimen_id": "muss", "status": "failed", "detail": "no pen path"}]


# ------------------------------------------------------------------ the knobs


def test_the_source_id_comes_from_the_frozen_manifest(tmp_path) -> None:
    """Never guessed from a directory name: a word set freezes into
    `<source_id>` and its pairs into `<source_id>-pairs`, so the manifest's own
    `set` field is the discriminator (the wordbench's rule)."""
    root = tmp_path / "suetterlin"
    (root / "src-1922").mkdir(parents=True)
    (root / "src-1922-pairs").mkdir(parents=True)
    (root / "src-1922" / "manifest.json").write_text(json.dumps({"set": "words", "source_id": "src-1922"}))
    (root / "src-1922-pairs" / "manifest.json").write_text(json.dumps({"set": "pairs", "source_id": "src-1922"}))
    assert _source_id_of(tmp_path, "suetterlin", "words") == "src-1922"
    assert _source_id_of(tmp_path, "suetterlin", "pairs") == "src-1922"
    assert _source_id_of(tmp_path, "kurrent", "words") == ""


def test_a_swept_arm_keeps_an_integer_knob_an_integer() -> None:
    """`--sweep rounds=1,2` must reach the loop as counts, not as floats."""
    base = FollowWeights()
    assert _with(base, "rounds", 3.0).rounds == 3
    assert isinstance(_with(base, "rounds", 3.0).rounds, int)
    assert _with(base, "prox", 0.25).prox == 0.25
    # …and one arm moves exactly one thing
    swept = _with(base, "prox", 0.25)
    assert (swept.rounds, swept.coverage, swept.max_delta) == (base.rounds, base.coverage, base.max_delta)


def test_parse_sweep_validates_against_the_weight_fields() -> None:
    assert parse_sweep("prox=1.0,0.1,0") == ("prox", [1.0, 0.1, 0.0])
    with pytest.raises(SystemExit, match="not a FollowWeights field"):
        parse_sweep("lambda=1.0")
    with pytest.raises(SystemExit, match="no values"):
        parse_sweep("prox=")
    with pytest.raises(SystemExit, match="must be numbers"):
        parse_sweep("prox=loose")


def test_ks_follow_env_overrides_never_touch_the_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    """`KS_FOLLOW_*` moves the follower and NOTHING else.

    The chain is the path the follower is graded against and the one the stored
    occurrences came from; a follower sweep that re-tuned it would compare two
    moving things (§3's guard rail, and `chain.py`'s own budget test one level
    down).
    """
    import tools.pairlab.chain as chain_mod
    import tools.pairlab.follow as follow_mod

    for env in ("KS_FOLLOW_PROX_WEIGHT", "KS_FOLLOW_ROUNDS", "KS_FOLLOW_MAX_ITER"):
        monkeypatch.delenv(env, raising=False)
    follow_mod = importlib.reload(follow_mod)
    assert follow_mod.FOLLOW_PROX_WEIGHT == DEFAULT_LAMBDA_REG
    chain_before = (chain_mod.CHAIN_MAX_ITER, chain_mod.CHAIN_OVERLAP_WEIGHT, chain_mod.CHAIN_LANDMARK_WEIGHT)

    monkeypatch.setenv("KS_FOLLOW_PROX_WEIGHT", "0.25")
    monkeypatch.setenv("KS_FOLLOW_ROUNDS", "5")
    monkeypatch.setenv("KS_FOLLOW_MAX_ITER", "77")
    reloaded = importlib.reload(follow_mod)
    try:
        assert reloaded.FOLLOW_PROX_WEIGHT == 0.25
        assert reloaded.FOLLOW_ROUNDS == 5
        assert reloaded.FOLLOW_MAX_ITER == 77
        # the defaults ride into the configuration object, not just the module
        assert reloaded.FollowWeights().prox == 0.25
        assert reloaded.FollowWeights().rounds == 5
        # …and the chain is untouched, constants and freshly reloaded module alike
        assert (chain_mod.CHAIN_MAX_ITER, chain_mod.CHAIN_OVERLAP_WEIGHT, chain_mod.CHAIN_LANDMARK_WEIGHT) == (
            chain_before
        )
        assert importlib.reload(chain_mod).CHAIN_MAX_ITER == chain_before[0]
        assert DEFAULT_LAMBDA_REG == 1.0
    finally:
        for env in ("KS_FOLLOW_PROX_WEIGHT", "KS_FOLLOW_ROUNDS", "KS_FOLLOW_MAX_ITER"):
            monkeypatch.delenv(env, raising=False)
        importlib.reload(follow_mod)
        importlib.reload(chain_mod)


def test_a_zone_never_straddles_a_pen_lift() -> None:
    # Review finding: index-adjacent flagged samples across a stroke boundary
    # are TWO zones — a merged one would cage anchors the pen never retraced.
    from tools.pairlab.follow import _zone_runs

    where = np.asarray([10, 11, 12, 13, 14, 15])
    same_stroke = np.asarray([0, 0, 0, 0, 0, 0])
    assert [z.tolist() for z in _zone_runs(where, same_stroke)] == [[10, 11, 12, 13, 14, 15]]
    across_lift = np.asarray([0, 0, 0, 1, 1, 1])  # lift between samples 12 and 13
    assert [z.tolist() for z in _zone_runs(where, across_lift)] == [[10, 11, 12], [13, 14, 15]]
    assert _zone_runs(np.asarray([], dtype=int), np.asarray([], dtype=int)) == []
