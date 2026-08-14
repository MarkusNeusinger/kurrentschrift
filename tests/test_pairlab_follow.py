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

The arm-⑥ half at the bottom adds a fourth: a synthetic JUNCTION whose true
crossing and whose skeleton branch point are deliberately different points, so
„the extrapolation corrects the junction displacement" is measured against a
known answer rather than asserted.
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
    LANDMARK_TARGET_MODES,
    FollowWeights,
    _intersect_lines,
    _source_id_of,
    _uncertainty_weights,
    _with,
    apply_landmark_targets,
    apply_retrace_guard,
    build_follow_problem,
    calibrate_case,
    calibration_report,
    candidate_payload,
    extrapolated_targets,
    follow_case,
    follow_derived,
    follow_word_chain,
    landmark_calibration,
    landmark_energy,
    landmark_meta,
    landmark_targeting,
    parse_sweep,
    print_calibration,
    raw_landmark_targets,
    retrace_anchor_mask,
    retrace_sample_mask,
)
from tools.pairlab.landmarks import skeleton_branch_points
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
    with pytest.raises(SystemExit, match="not a numeric FollowWeights field"):
        parse_sweep("lambda=1.0")
    # …and the two NON-numeric fields are refused by name: they select a
    # formulation (`landmark_targets`) or switch a guard off (`retrace_guard`),
    # and a "ladder" over them would compare two objectives under one label.
    for field_name in ("landmark_targets", "retrace_guard"):
        with pytest.raises(SystemExit, match="not a numeric FollowWeights field"):
            parse_sweep(f"{field_name}=1.0")
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


# -------------------------------------------- arm ⑥: the extrapolated targets
#
# The premise is a geometric fact, so it is BUILT rather than assumed: a junction
# whose ink is thicker on one side thins to a branch point that is NOT the
# crossing of the two centerlines. Below, the rays define the true crossing and a
# blob offset along one of them displaces the branch point away from it — the
# published junction displacement, in a canvas where the right answer is known.

JUNCTION_ORIGIN_PX = 4.3
JUNCTION_BASELINE_PX = 60.0
JUNCTION_SHAPE = (100, 100)
JUNCTION_ANGLES = (20.0, 200.0, 95.0, 275.0)  # two straight strokes crossing at 75 deg


def _junction_units(x_px: float, y_px: float) -> tuple[float, float]:
    """Crop px → the template units the chain's landmark targets live in."""
    return ((x_px - JUNCTION_ORIGIN_PX) / UNIT_PX, (JUNCTION_BASELINE_PX - y_px) / UNIT_PX)


def _junction_px(u: float, v: float) -> tuple[float, float]:
    return (JUNCTION_ORIGIN_PX + u * UNIT_PX, JUNCTION_BASELINE_PX - v * UNIT_PX)


def _ray(skel: np.ndarray, centre, angle_deg: float, length: float) -> None:
    """One 1-px skeleton ray, stepped along its DOMINANT axis.

    Stepping along the dominant axis is what keeps it a thinned skeleton: a
    finer parameterisation would stamp staircase pixels with three neighbours
    each, and `skeleton_branch_points` would then report a branch point every few
    pixels along a perfectly straight stroke.
    """
    dx, dy = np.cos(np.radians(angle_deg)), np.sin(np.radians(angle_deg))
    lead = max(abs(dx), abs(dy))
    for step in range(int(length * lead) + 1):
        t = step / lead
        skel[int(round(centre[1] + t * dy)), int(round(centre[0] + t * dx))] = True


def _junction_skeleton(centre, angles, *, length: float = 30.0, blob_radius: float = 2.0, blob_offset=(0.0, 0.0)):
    """Rays from `centre` at `angles`, welded by an ink blob that may sit OFF it."""
    skel = np.zeros(JUNCTION_SHAPE, dtype=bool)
    for angle in angles:
        _ray(skel, centre, angle, length)
    yy, xx = np.mgrid[0 : JUNCTION_SHAPE[0], 0 : JUNCTION_SHAPE[1]]
    skel |= np.hypot(xx - (centre[0] + blob_offset[0]), yy - (centre[1] + blob_offset[1])) <= blob_radius
    return skel


def _cross_anchors(centre, angles=(30.0, 105.0), *, half_units: float = 1.2, k: int = 6):
    """A ductus polyline crossing ITSELF over `centre`: one pen stroke per limb.

    Deliberately at other angles than the ink: the correspondence is what ties
    the two together, and a polyline that reproduced the ink exactly would let a
    broken extrapolation pass by coincidence.
    """
    strokes = [
        np.asarray(
            [
                _junction_units(
                    centre[0] + t * np.cos(np.radians(a)) * UNIT_PX, centre[1] + t * np.sin(np.radians(a)) * UNIT_PX
                )
                for t in np.linspace(-half_units, half_units, k)
            ]
        )
        for a in angles
    ]
    return np.vstack(strokes), [k * i for i in range(len(strokes))]


def _junction_problem(skel: np.ndarray, anchors: np.ndarray, starts, *, width_raw=1.5, n_samples: int = 64):
    fields = _flat_fields(JUNCTION_SHAPE)
    fields["skel"] = skel
    fields["width_raw"] = (
        np.full(JUNCTION_SHAPE, float(width_raw)) if np.isscalar(width_raw) else np.asarray(width_raw, dtype=float)
    )
    spec = ChainSegmentSpec(
        kind="letter",
        anchors=anchors,
        slot_index=0,
        key="x",
        half_widths=np.full(len(anchors), 0.07),
        stroke_starts=list(starts),
    )
    return build_chain_problem(
        [spec],
        unit_px=UNIT_PX,
        x_origin_px=JUNCTION_ORIGIN_PX,
        baseline_y_px=JUNCTION_BASELINE_PX,
        n_samples=n_samples,
        **fields,
    )


def _one_junction(*, angles=JUNCTION_ANGLES, blob_offset=(0.0, 0.0), width_raw=1.5, length=30.0, blob_radius=2.0):
    """`(centre_px, problem)` for a one-letter chain over one synthetic junction."""
    centre = (45.0, 45.0)
    skel = _junction_skeleton(centre, angles, length=length, blob_radius=blob_radius, blob_offset=blob_offset)
    anchors, starts = _cross_anchors(centre)
    problem = _junction_problem(skel, anchors, starts, width_raw=width_raw)
    assert problem.landmark_op.shape[0] == 1, "the scaffolding must produce exactly one correspondence"
    return centre, problem


def _target_px(problem, targeting, row: int = 0):
    return np.asarray(_junction_px(*targeting.targets[row]))


def test_the_extrapolation_recovers_the_crossing_the_branch_point_hides() -> None:
    """The whole of arm ⑥ in one measurement, against a KNOWN answer.

    The ink's two centerlines cross at `centre`; the ink blob sits 3 px along one
    of them, so the thinned skeleton's branch point — what the chain's landmark
    term aims at today — is displaced from the crossing by more than a pixel.
    Extrapolating the incident branches across the junction has to put the target
    back on the crossing.
    """
    centre, problem = _one_junction(blob_offset=(3.0, 0.0))
    branch_points = skeleton_branch_points(problem.skel)
    assert len(branch_points) == 1
    displacement = float(np.hypot(*(branch_points[0] - np.asarray(centre))))
    assert displacement > 1.0, "the premise: the branch point is NOT the crossing"

    raw = raw_landmark_targets(problem)
    assert _target_px(problem, raw) == pytest.approx(branch_points[0], abs=1e-9)

    refined = extrapolated_targets(problem)
    assert refined.reasons == ["ok"]
    assert float(np.hypot(*(_target_px(problem, refined) - np.asarray(centre)))) < 0.5
    # …and the move is reported in the units the arm's cost column is read in
    assert refined.shifts_units[0] == pytest.approx(displacement / UNIT_PX, rel=0.25)
    assert refined.entries[0]["n_branches"] == 4
    assert refined.entries[0]["cross_angle_deg"] == pytest.approx(75.0, abs=5.0)


def test_a_crossing_thinning_split_into_two_y_junctions_still_refines() -> None:
    """The mechanism that kept arm ⑥ inert on every real word, in one canvas.

    Thinning does not turn a shallow crossing into one branch point. It turns it
    into TWO Y-junctions bridged by a short segment — here two straight passes at
    ±10° whose skeleton is a bridge with two limbs at each end. A core that stops
    before the bridge walks that as a T: three limbs (two real, one the bridge)
    and the crossing's fourth limb behind the partner Y, which no tolerance can
    repair because three limbs cannot yield two disjoint pairs at all.

    Measured on the dev words, that partner sits 9.4–13.2 px away where the ink
    is 6.4–8.4 px wide; `FOLLOW_LANDMARK_CLUSTER_WIDTHS` absorbs it, and the four
    limbs the crossing really has come back. The right answer is known: the two
    passes cross at the bridge's midpoint, 6 px from the branch point the
    correspondence was assigned.
    """
    skel = np.zeros(JUNCTION_SHAPE, dtype=bool)
    left, right = (42.0, 45.0), (50.0, 45.0)
    crossing = np.array([46.0, 45.0])
    _ray(skel, left, 0.0, 8.0)  # the bridge: where the two passes' ink has merged
    for angle in (190.0, 170.0):
        _ray(skel, left, angle, 40.0)
    for angle in (10.0, -10.0):
        _ray(skel, right, angle, 40.0)
    anchors, starts = _cross_anchors(left)
    problem = _junction_problem(skel, anchors, starts, width_raw=4.0)

    branch_points = skeleton_branch_points(problem.skel)
    assert len(branch_points) == 2, "the premise: thinning reports the crossing TWICE"
    assert min(float(np.hypot(*(b - crossing))) for b in branch_points) > 4.0

    refined = extrapolated_targets(problem)
    assert refined.reasons == ["ok"]
    assert refined.entries[0]["n_branches"] == 4
    assert float(np.hypot(*(_target_px(problem, refined) - crossing))) < 1.0


def test_two_limbs_that_meet_again_stay_two_limbs() -> None:
    """A weld inside the walk radius must not fuse two limbs into one branch.

    The Euclidean annulus the first version labelled components in has no way to
    tell „one branch" from „two branches that touch": on the real skeletons its
    components reached 19–49 px where a 1-px arc across the annulus is 13 px at
    most, so limbs were being welded — by a tight loop, by the next junction, or
    (as here) by ink that simply crosses the annulus. The geodesic walk carries
    each limb's identity from the core boundary outward and BLOCKS the pixel two
    limbs both reach, so the weld costs the confluence and nothing else.
    """
    centre = (45.0, 45.0)
    skel = _junction_skeleton(centre, JUNCTION_ANGLES, length=30.0, blob_radius=2.0)
    a, b = (
        (centre[0] + 9 * np.cos(np.radians(angle)), centre[1] + 9 * np.sin(np.radians(angle))) for angle in (20.0, 95.0)
    )
    _ray(skel, a, float(np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0]))), float(np.hypot(*(np.subtract(b, a)))))
    anchors, starts = _cross_anchors(centre)
    problem = _junction_problem(skel, anchors, starts, width_raw=1.5)

    refined = extrapolated_targets(problem)
    assert refined.reasons == ["ok"]
    assert refined.entries[0]["n_branches"] == 4, "the welded limbs kept their identities"
    assert refined.entries[0]["cross_angle_deg"] == pytest.approx(75.0, abs=5.0)
    assert float(np.hypot(*(_target_px(problem, refined) - np.asarray(centre)))) < 1.0


def test_a_t_junction_keeps_the_raw_branch_point() -> None:
    """Three branches make ONE continuation pair — and one line cannot intersect.

    The refusal is the point: a T is a real junction with no crossing to
    extrapolate, so the honest target is the branch point plus the reason. That
    reason is its OWN name rather than `no_continuation_pair`, because three
    limbs can never yield two disjoint pairs however the pairing is scored — a
    property of the ink, not a refusal the tolerance could ever lift. On the dev
    words this class is 7 of 21 targets, and reading it as a failed pairing would
    have sent the work at a threshold that has nothing to say about it.
    """
    centre, problem = _one_junction(angles=(0.0, 180.0, 90.0))
    refined = extrapolated_targets(problem)
    assert refined.reasons == ["t_junction"]
    assert refined.entries[0]["n_branches"] == 3
    assert np.allclose(refined.targets, refined.raw_targets)
    assert _target_px(problem, refined) == pytest.approx(np.asarray(centre), abs=1e-9)


def test_a_near_parallel_junction_is_refused_as_ill_conditioned() -> None:
    """Two strokes meeting at 12°: the intersection slides along their direction.

    Same threshold and same reason the frozen detector applies to a polyline's
    own crossing (`landmarks.LANDMARK_MIN_ANGLE_DEG`) — an ill-conditioned point
    is not a target, however precisely the arithmetic reports it.
    """
    _centre, problem = _one_junction(angles=(0.0, 12.0, 180.0, 192.0), width_raw=5.5, length=26.0)
    refined = extrapolated_targets(problem)
    assert refined.reasons == ["ill_conditioned"]
    assert refined.entries[0]["n_branches"] == 4
    assert refined.entries[0]["cross_angle_deg"] < 15.0
    assert np.allclose(refined.targets, refined.raw_targets)


def test_two_branches_are_a_passing_stroke_not_a_crossing() -> None:
    """Two incident branches are a stroke passing through — its own named class.

    `touch_point`, not `few_branches`: nothing about the ink here can be walked
    into a crossing, so it is a property of the material rather than a refusal
    worth chasing. On the dev words it is 5 of 21 targets — every one of them a
    retrace or a corner the frozen detector matched a ductus crossing to.
    """
    _centre, problem = _one_junction(angles=(0.0, 180.0), length=40.0)
    refined = extrapolated_targets(problem)
    assert refined.reasons == ["touch_point"]
    assert refined.entries[0]["n_branches"] == 2
    assert np.allclose(refined.targets, refined.raw_targets)


def test_without_an_ink_side_nothing_is_refined_and_the_reason_says_so() -> None:
    """„No junction here" is a different statement from „too few branches".

    A correspondence can only exist where a skeleton did, but the walk must still
    answer honestly when the ink it is handed is empty — the same discipline
    `chain._landmark_correspondence` follows when no skeleton is supplied at all.
    """
    _centre, problem = _one_junction(blob_offset=(3.0, 0.0))
    problem.skel = None
    refined = extrapolated_targets(problem)
    assert refined.reasons == ["no_junction"]
    assert refined.entries[0]["n_branches"] == 0
    assert np.allclose(refined.targets, refined.raw_targets)


def test_an_extrapolation_beyond_the_displacement_bound_is_refused() -> None:
    """The published bound is the local stroke width — further is another junction.

    Driven through the threshold rather than through a contrived skeleton: the
    same junction that refines cleanly above is refused once the bound is put
    below the correction it wants to make.
    """
    _centre, problem = _one_junction(blob_offset=(3.0, 0.0))
    refined = extrapolated_targets(problem, max_shift_widths=0.01)
    assert refined.reasons == ["far_from_branch"]
    assert np.allclose(refined.targets, refined.raw_targets)


def test_the_intersection_refuses_a_near_parallel_pair() -> None:
    """The conditioning guard itself, on two lines and nothing else."""
    p1, u1 = np.array([0.0, 0.0]), np.array([1.0, 0.0])
    p2, u2 = np.array([0.0, 4.0]), np.array([np.cos(np.radians(60.0)), -np.sin(np.radians(60.0))])
    crossing = _intersect_lines(p1, u1, p2, u2, min_angle_deg=15.0)
    assert crossing is not None
    assert crossing[1] == pytest.approx(0.0, abs=1e-9)
    assert crossing[0] == pytest.approx(4.0 / np.tan(np.radians(60.0)), rel=1e-9)
    shallow = np.array([np.cos(np.radians(5.0)), -np.sin(np.radians(5.0))])
    assert _intersect_lines(p1, u1, p2, shallow, min_angle_deg=15.0) is None


# ------------------------------------------------------------ the uncertainty


def test_uncertainty_weights_are_relative_and_average_to_one() -> None:
    """`1/sigma^2`, normalised so the term keeps the scale it is calibrated at.

    Mean 1 is not cosmetic: `e_landmark` is a MEAN of squared residuals, and a
    weighting that changed its scale would make a calibrated weight mean
    something different on every word.
    """
    weights = _uncertainty_weights(np.array([0.05, 0.10, 0.20]))
    assert float(np.mean(weights)) == pytest.approx(1.0)
    assert weights[0] > weights[1] > weights[2]  # thinner ink, more certain target
    assert weights[0] / weights[1] == pytest.approx(4.0)  # …quadratically so
    assert np.allclose(_uncertainty_weights(np.full(4, 0.13)), 1.0)
    assert _uncertainty_weights(np.zeros(0)).shape == (0,)


def test_thicker_ink_buys_a_larger_sigma_and_a_smaller_weight() -> None:
    """The chain from the ink to the weight, end to end on two real junctions.

    One thin junction on the left, one thick on the right, in ONE problem — the
    weights are relative, so a comparison across two problems could not see them.
    """
    centres = [(30.0, 45.0), (70.0, 45.0)]
    skel = np.zeros(JUNCTION_SHAPE, dtype=bool)
    anchors, starts, offset = [], [], 0
    for centre in centres:
        skel |= _junction_skeleton(centre, JUNCTION_ANGLES, length=16.0, blob_radius=1.5)
        block, block_starts = _cross_anchors(centre, half_units=0.5)
        anchors.append(block)
        starts.extend(offset + s for s in block_starts)
        offset += len(block)
    columns = np.arange(JUNCTION_SHAPE[1])[None, :] * np.ones((JUNCTION_SHAPE[0], 1))
    problem = _junction_problem(
        skel, np.vstack(anchors), starts, width_raw=np.where(columns < 50, 1.5, 4.0), n_samples=96
    )
    assert problem.landmark_op.shape[0] == 2

    refined = extrapolated_targets(problem)
    assert refined.reasons == ["ok", "ok"]
    assert refined.entries[0]["half_width_px"] < refined.entries[1]["half_width_px"]
    assert refined.sigmas[0] < refined.sigmas[1]
    assert refined.weights[0] > 1.0 > refined.weights[1]
    assert float(np.mean(refined.weights)) == pytest.approx(1.0)
    # …and the uniform arm of the ladder keeps the same targets at weight 1
    uniform = landmark_targeting(problem, "extrapolated_uniform")
    assert np.allclose(uniform.targets, refined.targets)
    assert np.allclose(uniform.weights, 1.0)


def test_the_whitening_prices_exactly_the_weighted_residual() -> None:
    """`e_landmark` after `apply_landmark_targets` IS `mean(w·|P − T|²)`.

    Computed here from the UNWHITENED operator and the plain targets, so the
    assertion tests the whitening identity rather than restating it.
    """
    _centre, problem = _one_junction(blob_offset=(3.0, 0.0), width_raw=2.0)
    targeting = extrapolated_targets(problem)
    expected = landmark_energy(problem, problem.x0, targeting)
    predicted = float(
        np.sum(
            targeting.weights[:, None]
            * ((problem.landmark_op @ problem.plan_anchors(problem.x0)) - targeting.targets) ** 2
        )
        / problem.landmark_op.shape[0]
    )
    assert expected == pytest.approx(predicted, rel=1e-12)

    apply_landmark_targets(problem, targeting)
    assert problem.energy_terms(problem.x0)["e_landmark"] == pytest.approx(expected, rel=1e-12)
    # …and the raw arm is what the term prices without any of this
    _c2, control = _one_junction(blob_offset=(3.0, 0.0), width_raw=2.0)
    assert control.energy_terms(control.x0)["e_landmark"] != pytest.approx(expected, rel=1e-6)
    # the refinement's provenance rides in the report the arm reads its costs off
    entry = next(e for e in problem.landmark_report if e["reason"] == "ok")
    assert entry["target_mode"] == "extrapolated"
    assert entry["refine_reason"] == "ok"
    assert entry["sigma_units"] > 0.0
    meta = landmark_meta(problem, mode="extrapolated")
    assert meta == {
        "mode": "extrapolated",
        "applied": True,
        "n_detected": 1,
        "n_targets": 1,
        "drops": {},
        "refined": {"ok": 1},
        "shift_units_median": entry["refine_shift_units"],
        "sigma_units_median": entry["sigma_units"],
    }


# ----------------------------------------------------------------- inertness


def test_refined_targets_at_weight_zero_are_byte_identical() -> None:
    """The term's own inertness rule, extended to its targets.

    At weight 0 the landmark energy enters `f` as `+ 0.0` and contributes no
    gradient at all, so re-aiming it CANNOT move an anchor — and the equality
    below is bit equality, not `approx`: an arm at `landmark = 0` is an identity,
    which is what makes the paired comparison against the frozen chain baseline
    legitimate.
    """
    _centre, aimed = _one_junction(blob_offset=(3.0, 0.0))
    _centre2, untouched = _one_junction(blob_offset=(3.0, 0.0))
    apply_landmark_targets(aimed, extrapolated_targets(aimed))
    assert aimed.landmark_weight == 0.0
    rng = np.random.default_rng(66)
    params = rng.uniform(-0.05, 0.05, size=len(aimed.x0))
    for p in (aimed.x0, params):
        f_a, g_a = aimed.objective(p)
        f_b, g_b = untouched.objective(p)
        assert f_a == f_b
        assert np.array_equal(g_a, g_b)
    # …and NOT vacuous: at a positive weight the two aim at different points
    _c3, armed = _one_junction(blob_offset=(3.0, 0.0))
    armed.landmark_weight = 1.0
    before = armed.objective(params)[0]
    apply_landmark_targets(armed, extrapolated_targets(armed))
    assert armed.objective(params)[0] != before


def test_the_target_mode_changes_nothing_at_landmark_weight_zero(synthetic) -> None:
    """The follower level of the same claim: identical traces across all modes."""
    case, result, windows, fit = synthetic
    traces = {}
    for mode in LANDMARK_TARGET_MODES:
        followed = follow_word_chain(
            case,
            [0, 1],
            result=result,
            windows_px=windows,
            fit=fit,
            weights=FollowWeights(rounds=1, landmark=0.0, landmark_targets=mode),
        )
        assert followed is not None
        assert followed.fit_meta["landmark"]["mode"] == mode
        assert followed.fit_meta["landmark"]["applied"] is False
        traces[mode] = json.dumps(followed.strokes_units)
    assert len(set(traces.values())) == 1


def test_an_unknown_target_mode_is_a_caller_error(synthetic) -> None:
    _case, _result, _windows, fit = synthetic
    with pytest.raises(ValueError, match="unknown landmark target mode"):
        build_follow_problem(fit.problem, fit.params, FollowWeights(rounds=1, landmark_targets="nearest"))
    with pytest.raises(ValueError, match="unknown landmark target mode"):
        landmark_targeting(fit.problem, "nearest")


# --------------------------------------------------------- the calibration hook


def test_the_calibration_reads_the_scale_and_scales_with_the_multiplier() -> None:
    """§11c's discipline as arithmetic: rungs are fractions of a MEASURED parity.

    The parity weight is `e_geo / e_landmark` at the optimum, so a rung's
    would-be energy is that fraction of `e_geo` — which is what makes „1 % of the
    geometry term" a statement about this objective rather than about another
    path's constant.
    """
    _centre, problem = _one_junction(blob_offset=(3.0, 0.0))
    targeting = extrapolated_targets(problem)
    report = landmark_calibration(problem, problem.x0, targeting, multipliers=(0.01, 0.1, 1.0))
    assert report["mode"] == "extrapolated"
    assert report["n_landmarks"] == problem.landmark_op.shape[0] == 1
    assert report["n_detected"] == len(problem.landmark_report)
    assert report["e_landmark"] == pytest.approx(landmark_energy(problem, problem.x0, targeting))
    assert report["parity_weight"] == pytest.approx(report["e_geo"] / report["e_landmark"])
    energies = [c["would_be_energy"] for c in report["candidates"]]
    assert energies[1] == pytest.approx(10.0 * energies[0])
    assert energies[2] == pytest.approx(100.0 * energies[0])
    for candidate in report["candidates"]:
        assert candidate["share_of_e_geo"] == pytest.approx(candidate["multiplier"])
        assert candidate["weight"] == pytest.approx(candidate["multiplier"] * report["parity_weight"])
    assert report["reasons"] == {"ok": 1}

    # the raw arm is calibrated the same way, against its own (different) energy
    raw = landmark_calibration(problem, problem.x0, raw_landmark_targets(problem), multipliers=(0.1,))
    assert raw["mode"] == "raw"
    assert raw["e_geo"] == pytest.approx(report["e_geo"])
    assert raw["e_landmark"] != pytest.approx(report["e_landmark"], rel=1e-6)


def test_a_solve_without_a_correspondence_calibrates_to_nothing(synthetic) -> None:
    """No landmark, no scale — and no invented number in its place."""
    _case, _result, _windows, fit = synthetic
    problem, params = fit.problem, fit.params
    assert problem.landmark_op.shape[0] == 0
    report = landmark_calibration(problem, params, raw_landmark_targets(problem))
    assert report["n_landmarks"] == 0
    assert report["e_landmark"] == 0.0
    assert report["parity_weight"] is None
    assert all(c["weight"] is None and c["would_be_energy"] is None for c in report["candidates"])


def test_the_calibration_run_solves_once_with_the_term_forced_inert(synthetic, capsys) -> None:
    """The CLI path end to end: one follower solve per run, then BOTH modes read.

    The weight is forced to 0 rather than trusted from the caller, because a
    scale read off a solve the term already moved would report the size of its
    own effect.
    """
    case, _result, _windows, _fit = synthetic
    row = calibrate_case(case, weights=FollowWeights(rounds=1, landmark=5.0))
    assert row["status"] == "ok"
    assert row["specimen_id"] == case.id
    assert [r["slots"] for r in row["runs"]] == [[0, 1]]
    assert set(row["runs"][0]["modes"]) == {"raw", "extrapolated"}
    assert all(m["n_landmarks"] == 0 for m in row["runs"][0]["modes"].values())

    report = calibration_report([row], multipliers=(0.01, 0.1, 1.0))
    assert report["multipliers"] == [0.01, 0.1, 1.0]
    assert report["modes"]["extrapolated"]["n_solves"] == 1
    assert report["modes"]["extrapolated"]["n_solves_with_landmark"] == 0
    assert report["modes"]["extrapolated"]["parity_weight_median"] is None
    assert [r["weight"] for r in report["modes"]["raw"]["rungs"]] == [None, None, None]
    print_calibration(report)
    assert "LANDMARK CALIBRATION" in capsys.readouterr().out


def test_a_calibration_of_an_unscorable_case_is_a_row_not_an_exception() -> None:
    case, _result, _windows, _truth = _synthetic_word([(0.0, 0.0)])
    case.scorable = False
    row = calibrate_case(case)
    assert row["status"] == "skipped" and row["runs"] == []


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
