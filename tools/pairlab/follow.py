"""The ink follower: a re-linearising restart that pulls the chain onto the ink.

Route A of `docs/proposals/tintenfolger.md` §3, and nothing else. The chain fit
(`tools.pairlab.chain`) is a MEASUREMENT fit: its Tikhonov term deliberately
pulls the path towards the chart form so a hand statistic stays robust. As an
ink FOLLOWER it was never meant to be. This module runs a second solve on top of
it that keeps the chain's ORDER (stroke sequence, crossing resolution, seams —
all of it ductus prior) and releases its FORM prior:

    solve 1 = `fit_word_chain` (or a `keep_solve=True` fit handed in)
    round r = 1..rounds:
        specs_r  = respec_from_solution(problem_(r-1), params_(r-1))
        problem_r = build_chain_problem(specs_r, …, FOLLOWER weights)
        params_r  = L-BFGS-B(problem_r, x0 = 0)
    stop early when a round moves no anchor by `FOLLOW_ROUND_EPS_UNITS`.

**It is a re-linearising restart, not a snake.** Three things the chain freezes
at its INITIAL anchors — the chord parameterisation of the spline, the landmark
correspondence, the overlap seam exemptions — are exactly what goes stale after
displacements up to `core.fit.MAX_ANCHOR_DELTA`, i.e. precisely where the fit
worked hardest. Rebuilding the problem at the found optimum re-freezes all three
there, and the gradient stays exactly analytic (which is what a dense snake
would buy nothing for: at ~1.5 px anchor spacing on a ~4 px stroke there is no
resolution to gain, and it would lose the width term and the landmark operator —
the two crossing resolvers).

**What the Tikhonov term means here.** In the rebuilt problem the initial
anchors ARE the chain optimum, so `e_reg` no longer prices distance to the chart
form: it prices **displacement from the chain optimum** — a proximal /
trust-region term rather than a form prior. That change of MEANING is the whole
of v1 (§3: „v1 ändert genau EINE Sache: reg→prox"); the change of VALUE is arm ①
of the pre-registered §14 ladder. λ_prox stays > 0 by default because the EDT
term has zero gradient along the ridge — λ = 0 is the documented zig-zag
degeneration, kept reachable as a characterisation run, never shipped.

**The retrace guard.** Retrace is the blind spot of BOTH data terms: reverse
coverage is satisfied by ONE pass over doubly-written ink, and the ridge pull
rewards collapsing the two passes onto each other. Only the form prior tells
them apart — so anchors whose samples sit in a retrace zone of the init path
keep the FULL chain λ while everything else is released to λ_prox
(`retrace_anchor_mask`, the same `core.geometry.detect_retrace_pairs` rule at
0.15 xh the trace bench counts with).

**Guard rails** (§3, binding): strictly additive and opt-in; `KS_FOLLOW_*` never
moves a `CHAIN_*`; no chain solve changes; the harvest gets no follower path
here; nothing writes to the DB, the API, `core/` or any rendering path. Every
shipping weight below is PROVISIONAL — stamped as such into every artefact — and
acceptance is decided by `tools/tracebench`, never by the distance-transform
residual this solve minimises itself.

    uv run python -m tools.pairlab.follow die laden --rounds 2
    uv run python -m tools.pairlab.follow --all --set words --candidate-out temp/follow.json
    uv run python -m tools.pairlab.follow die --sweep prox=1.0,0.1,0.0
"""

from __future__ import annotations

import argparse
import json
import os
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import minimize

from core.compose import CAP_RESTART_BASES, _key_base
from core.fit import (
    DEFAULT_COVERAGE_WEIGHT,
    DEFAULT_LAMBDA_REG,
    DEFAULT_N_SAMPLES,
    DEFAULT_WIDTH_WEIGHT,
    MAX_ANCHOR_DELTA,
)
from core.geometry import detect_retrace_pairs
from core.quality_suetterlin import MIN_RETRACE_PAIRS

# The word-level run plumbing — the per-slot grid windows, the runs they narrow
# to and the stored word record's shape. Imported from the harvest rather than
# rebuilt here for the reason `tools.tracebench.candidates.chain_provider` gives
# for the same import: a follower graded against the chain baseline must be cut
# on the SAME coverage windows, and a second implementation of them would drift.
# `tools.pairlab.gradlab`, `landmarklab` and `bindab` take exactly this import;
# the cycle `tools.laufform.harvest` avoids is the opposite direction (it
# imports `pairlab.chain`/`anchors`/`trace`, and none of them imports back).
from tools.laufform.harvest import _chainable_runs, _grid_fits, _word_record
from tools.pairlab.analyze import FIT_DX_UNITS, FIT_DY_UNITS
from tools.pairlab.chain import (
    _REFERENCE_ANCHOR_COUNT,
    CHAIN_CONNECTOR_MAX_DELTA,
    CHAIN_CONNECTOR_SMOOTH_WEIGHT,
    CHAIN_LANDMARK_WEIGHT,
    CHAIN_MAX_ITER,
    CHAIN_OVERLAP_WEIGHT,
    ChainSegment,
    ChainWordFit,
    _ChainProblem,
    _letter_spec,
    _stroke_polylines_px,
    build_chain_problem,
    fit_word_chain,
    respec_from_solution,
)
from tools.pairlab.trace import assemble_word_strokes, cap_word_strokes
from tools.wordlab.cases import DEFAULT_FIXTURES_DIR, WordCase, iter_fixture_word_cases
from tools.wordlab.derive import WordDeriveResult, derive_word


# --------------------------------------------------------------------- weights
#
# Every constant below is read from the environment at import time, exactly as
# `chain.py` reads its own knobs, so a sweep needs no edit of this file — and
# every one of them is `KS_FOLLOW_*`, so a sweep of the FOLLOWER can never move
# the chain, the M4 fit or anything the production path renders with.

# **The proximal weight.** In the rebuilt problem the Tikhonov term prices
# displacement from the CHAIN OPTIMUM (see the module docstring), so this is a
# trust-region radius in disguise rather than a form prior.
#
# PROVISIONAL, and deliberately the chain's own λ: v1 changes exactly ONE thing
# (the reference point of the term, reg → prox), so the WEIGHT stays where the
# chain had it until §14 arm ① calibrates it against the measured term ratios at
# the solve-1 optimum (`tools/pairlab/gradlab.py`). §11c is the standing warning
# this obeys: a ladder chosen by analogy to another path's constant measured
# nothing at all. No number here is claimed to be calibrated.
FOLLOW_PROX_WEIGHT_ENV = "KS_FOLLOW_PROX_WEIGHT"
FOLLOW_PROX_WEIGHT = float(os.environ.get(FOLLOW_PROX_WEIGHT_ENV) or DEFAULT_LAMBDA_REG)
# Coverage (skeleton → path) weight. The chain default, because arm ④ is what
# moves it — with `stranded_anchors` as its MANDATORY cost column (§11a: at a
# stranded anchor the coverage force is 32x its normal strength and anti-aligned
# with the displacement, so releasing the reg term turns that force UP).
FOLLOW_COVERAGE_WEIGHT_ENV = "KS_FOLLOW_COVERAGE_WEIGHT"
FOLLOW_COVERAGE_WEIGHT = float(os.environ.get(FOLLOW_COVERAGE_WEIGHT_ENV) or DEFAULT_COVERAGE_WEIGHT)
# Samples per PLAN anchor. The chain's own ratio, expressed as the ratio rather
# than copied as a number so the two cannot drift: `build_chain_problem` uses
# `DEFAULT_N_SAMPLES / 120 x K_plan` (≈ 1.5). Arm ③ sweeps it — a follower that
# reads the field at more places between the same anchors is the cheapest
# resolution increase available without a dense snake.
FOLLOW_SAMPLES_PER_ANCHOR_ENV = "KS_FOLLOW_SAMPLES_PER_ANCHOR"
FOLLOW_SAMPLES_PER_ANCHOR = float(
    os.environ.get(FOLLOW_SAMPLES_PER_ANCHOR_ENV) or (DEFAULT_N_SAMPLES / _REFERENCE_ANCHOR_COUNT)
)
# Per-anchor travel budget (xh) of a follower round — measured FROM the chain
# optimum, which is a different reference point than the chart form and hence
# its own budget. PROVISIONAL at the chain's `core.fit.MAX_ANCHOR_DELTA`: no §14
# arm sweeps the bound, and keeping it means the BOX is not what changed between
# the two solves, so arm ① measures λ_prox against a fixed one. A follower that
# wants a genuine trust region tightens this — and then the tightening is the
# arm, declared as such.
FOLLOW_MAX_DELTA_ENV = "KS_FOLLOW_MAX_DELTA"
FOLLOW_MAX_DELTA = float(os.environ.get(FOLLOW_MAX_DELTA_ENV) or MAX_ANCHOR_DELTA)
# …and the connector interiors' own cap, at the chain's, for the same reason.
FOLLOW_CONNECTOR_MAX_DELTA_ENV = "KS_FOLLOW_CONNECTOR_MAX_DELTA"
FOLLOW_CONNECTOR_MAX_DELTA = float(os.environ.get(FOLLOW_CONNECTOR_MAX_DELTA_ENV) or CHAIN_CONNECTOR_MAX_DELTA)
# How many re-linearising rounds. 2 because the staleness the restart repairs is
# a one-step property (the chord parameterisation is re-frozen at the new
# anchors, and a second round measures whether that mattered); arm ② is the
# sweep, and the early stop below usually decides it anyway.
FOLLOW_ROUNDS_ENV = "KS_FOLLOW_ROUNDS"
FOLLOW_ROUNDS = int(os.environ.get(FOLLOW_ROUNDS_ENV) or 2)
# Below this maximum per-anchor motion (xh) a round has changed nothing worth a
# further rebuild: 0.005 xh is a quarter of the ~0.02 xh sample step the trace
# bench resamples to, i.e. below what the ruler can see at all.
FOLLOW_ROUND_EPS_UNITS_ENV = "KS_FOLLOW_ROUND_EPS_UNITS"
FOLLOW_ROUND_EPS_UNITS = float(os.environ.get(FOLLOW_ROUND_EPS_UNITS_ENV) or 0.005)
# L-BFGS-B budget per round, at the chain's own — a follower round is the same
# problem size as the solve it restarts, so it gets the same headroom (which the
# chain sweep sized so the budget never binds).
FOLLOW_MAX_ITER_ENV = "KS_FOLLOW_MAX_ITER"
FOLLOW_MAX_ITER = int(os.environ.get(FOLLOW_MAX_ITER_ENV) or CHAIN_MAX_ITER)
# The three terms the follower INHERITS from the chain — deliberately from the
# chain's live constants rather than from copies, because they are the chain's
# own terms and a follower is not a place to fork them. Exposed so arms ⑤
# (overlap {0.2, 0} — the §13 „brake" hypothesis), ⑥ (landmark) and ⑦ (width as
# a MODULATOR rather than a residual) can move them ONE at a time.
FOLLOW_OVERLAP_WEIGHT_ENV = "KS_FOLLOW_OVERLAP_WEIGHT"
FOLLOW_OVERLAP_WEIGHT = float(os.environ.get(FOLLOW_OVERLAP_WEIGHT_ENV) or CHAIN_OVERLAP_WEIGHT)
FOLLOW_LANDMARK_WEIGHT_ENV = "KS_FOLLOW_LANDMARK_WEIGHT"
FOLLOW_LANDMARK_WEIGHT = float(os.environ.get(FOLLOW_LANDMARK_WEIGHT_ENV) or CHAIN_LANDMARK_WEIGHT)
FOLLOW_WIDTH_WEIGHT_ENV = "KS_FOLLOW_WIDTH_WEIGHT"
FOLLOW_WIDTH_WEIGHT = float(os.environ.get(FOLLOW_WIDTH_WEIGHT_ENV) or DEFAULT_WIDTH_WEIGHT)
# The neighbour-binding term is FIXED at 0.0 — the one weight that does NOT
# inherit `CHAIN_LETTER_BIND_WEIGHT`. That term was measured and REJECTED on the
# chain path (§11d: it works and makes the thing that matters worse), so an
# exported chain-side sweep knob must not be able to switch it on inside the
# follower. Arm ⑧ is the only way it moves, and only after a surviving zig-zag
# has been measured, with §11d's re-measurement duty attached.
FOLLOW_BIND_WEIGHT_ENV = "KS_FOLLOW_BIND_WEIGHT"
FOLLOW_BIND_WEIGHT = float(os.environ.get(FOLLOW_BIND_WEIGHT_ENV) or 0.0)
# Retrace proximity (xh): two passes closer than this are the same ink. The
# trace bench's own number (`tools/tracebench/counters.py` RETRACE_PROX_UNITS,
# tintenfolger.md §2.3), mirrored rather than imported — the bench is the ruler
# and a measurement tool must not import it into the thing it measures.
FOLLOW_RETRACE_PROX_UNITS_ENV = "KS_FOLLOW_RETRACE_PROX_UNITS"
FOLLOW_RETRACE_PROX_UNITS = float(os.environ.get(FOLLOW_RETRACE_PROX_UNITS_ENV) or 0.15)

# The candidate file's mandatory frame literal. Re-declared rather than imported
# for the same reason `tools.tracebench.candidates` re-declares the wire caps:
# the ruler must not be imported into the candidate producer. Pinned against
# `tools.tracebench.candidates.CANDIDATE_FRAME` by a test.
CANDIDATE_FRAME = "word_registration"
# Artefact stamp, so a candidate file can always be traced back to the producer.
FOLLOW_TOOL_NAME = "pairlab.follow"
FOLLOW_ARTIFACT_VERSION = "1"

STATUS_OK = "ok"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"


@dataclass(frozen=True)
class FollowWeights:
    """One follower configuration — every knob of one §14 arm in one object.

    Frozen because a configuration travels into a process pool and is stamped
    into the artefact; nothing downstream may adjust it. `provisional` is not a
    knob but a declaration: NONE of these defaults is calibrated, and the flag
    rides along into every JSON the tool writes so a number can never be read as
    if it came from a tuned follower.
    """

    prox: float = FOLLOW_PROX_WEIGHT
    coverage: float = FOLLOW_COVERAGE_WEIGHT
    samples_per_anchor: float = FOLLOW_SAMPLES_PER_ANCHOR
    width: float = FOLLOW_WIDTH_WEIGHT
    overlap: float = FOLLOW_OVERLAP_WEIGHT
    landmark: float = FOLLOW_LANDMARK_WEIGHT
    bind: float = FOLLOW_BIND_WEIGHT
    smooth: float = CHAIN_CONNECTOR_SMOOTH_WEIGHT
    max_delta: float = FOLLOW_MAX_DELTA
    connector_max_delta: float = FOLLOW_CONNECTOR_MAX_DELTA
    rounds: int = FOLLOW_ROUNDS
    round_eps_units: float = FOLLOW_ROUND_EPS_UNITS
    max_iter: int = FOLLOW_MAX_ITER
    retrace_prox_units: float = FOLLOW_RETRACE_PROX_UNITS
    retrace_guard: bool = True
    provisional: bool = True


@dataclass
class FollowFit:
    """One RUN of joined slots after the follower's rounds.

    The `ChainWordFit` fields a consumer of the chain fit already reads, plus
    the round protocol. Two deliberate differences from `ChainWordFit`:

    * `slot_shift_units` / `global_shift_units` are the LAST round's placement
      parameters, i.e. relative to the geometry that round started from — the
      chain's own placement is already baked into the respec'd anchors. The
      per-round records carry each round's own blocks, and `chain_fit_meta`
      carries solve 1's.
    * `segments[*].fitted_anchors` are in the chart frame the templates were
      read from, exactly as `fit_word_chain` reports them (the composed
      placement offset removed), so a caller can difference them anchor for
      anchor against a chain fit.
    """

    case: WordCase
    slots: list[int]
    segments: list[ChainSegment]
    stroke_polylines_px: list[dict]
    strokes_units: list[list[list[float]]]
    slot_shift_units: dict[int, tuple[float, float]]
    slot_at_bound: dict[int, bool]
    global_shift_units: tuple[float, float]
    rounds: list[dict]
    converged: bool
    converged_local: bool
    fit_meta: dict
    problem: Any | None = None
    """The last round's solved `_ChainProblem` — only with `keep_solve=True`
    (it holds the whole field stack, see `ChainWordFit.problem`)."""
    params: np.ndarray | None = None
    """…and its argmin, in that problem's parameter layout."""


# ------------------------------------------------------------- the retrace zone


def retrace_sample_mask(
    px: np.ndarray, py: np.ndarray, stroke_starts: Sequence[int], *, prox_px: float, min_pairs: int = MIN_RETRACE_PAIRS
) -> np.ndarray:
    """`(n_s,)` bool — which SAMPLES of one path lie in a retrace zone.

    `core.geometry.detect_retrace_pairs` flags every sample whose near
    anti-parallel partner lies within `prox_px` and far enough along the path;
    contiguous flagged samples OF ONE PEN STROKE form a pass, and a pass thinner
    than `min_pairs` samples is a graze, not a retrace. That is the trace
    bench's own recipe (`tools/tracebench/counters.py::retrace_segments`),
    reproduced here rather than imported — the ruler must not be imported into
    the thing it grades — minus the zone merging, which only ever mattered for
    reporting a zone's POSITION.

    A pen lift never welds two passes into one: the stroke bounds come from the
    chain's own `stroke_of_sample`, so a run of flagged samples stops at a lift
    instead of counting the line between two pen strokes — which was never
    written — as part of the same pass. Two limbs on OPPOSITE sides of a lift
    can still be each other's partner, and should be: a `t` whose stem is
    retraced after the bar is lifted is still doubly-written ink.
    """
    px = np.asarray(px, dtype=float)
    py = np.asarray(py, dtype=float)
    mask = np.zeros(len(px), dtype=bool)
    if len(px) < 2 or prox_px <= 0.0:
        return mask
    idx, _partner = detect_retrace_pairs(px, py, list(stroke_starts), prox_px=float(prox_px))
    if not len(idx):
        return mask
    stroke_of = np.zeros(len(px), dtype=int)
    bounds = sorted({0, *(int(s) for s in stroke_starts if 0 < int(s) < len(px))})
    for s, start in enumerate(bounds):
        end = bounds[s + 1] if s + 1 < len(bounds) else len(px)
        stroke_of[start:end] = s

    run: list[int] = []
    for i in [*np.sort(idx).tolist(), None]:
        contiguous = bool(run) and i is not None and i == run[-1] + 1 and stroke_of[i] == stroke_of[run[-1]]
        if contiguous:
            run.append(i)
            continue
        if len(run) >= min_pairs:
            mask[run] = True
        run = [] if i is None else [i]
    return mask


def _stroke_starts_of(problem: _ChainProblem) -> list[int]:
    """Sample indices where a new PEN STROKE of the chain begins."""
    stroke = np.asarray(problem.stroke_of_sample, dtype=int)
    if not len(stroke):
        return [0]
    return [0, *(np.flatnonzero(np.diff(stroke) != 0) + 1).tolist()]


def retrace_anchor_mask(problem: _ChainProblem, params: np.ndarray | None = None, *, prox_units: float) -> np.ndarray:
    """`(K_free,)` bool — which FREE anchors a retrace ZONE of the path spans.

    Samples are flagged first (`retrace_sample_mask`), because the objective
    reads the field at samples and never at an anchor. Each contiguous run of
    flagged samples is then a zone, and the anchors it spans are the ones
    between the plan anchors its first and last sample belong to — attribution
    by the sampling operator's DOMINANT weight per sample, which is the only
    local reading of that operator: a cubic sampling row has a numerically
    non-zero weight on nearly every anchor of its stroke, so `sample_slice_of_
    anchor`'s support window (right for reading a field, and what `gradlab`
    uses it for) would cage the whole letter here.

    Spanning rather than dominance alone is deliberate: at ~1.5 samples per
    anchor not every anchor of a zone is some sample's dominant one, and a cage
    with holes in it is not a cage.
    """
    params = problem.x0 if params is None else np.asarray(params, dtype=float)
    px, py = problem.to_pixels(params)
    flagged = retrace_sample_mask(
        px, py, _stroke_starts_of(problem), prox_px=float(prox_units) * float(problem.unit_px)
    )
    out = np.zeros(len(problem.anchors_free), dtype=bool)
    if not flagged.any():
        return out
    dominant = np.argmax(np.abs(problem.sampling_op), axis=1)  # sample -> plan anchor
    where = np.flatnonzero(flagged)
    stroke_of = np.searchsorted(np.asarray(_stroke_starts_of(problem), dtype=int), where, side="right")
    for zone in _zone_runs(where, stroke_of):
        plan = dominant[zone]
        out[np.unique(problem.idx[int(plan.min()) : int(plan.max()) + 1])] = True
    return out


def _zone_runs(where: np.ndarray, stroke_of: np.ndarray) -> list[np.ndarray]:
    """Split flagged sample indices into zones: contiguous AND within one stroke.

    Index contiguity alone would merge two zones whose flagged samples happen
    to be adjacent across a pen lift — and a zone that straddles a lift cages
    anchors the pen never retraced (review finding on the follower PR). The
    stroke id is the second cut condition, mirroring the pen-lift separation
    `retrace_sample_mask` already enforces on the detector side.
    """
    if not len(where):
        return []
    cuts = np.flatnonzero((np.diff(where) != 1) | (np.diff(stroke_of) != 0)) + 1
    return [zone for zone in np.split(where, cuts) if len(zone)]


def apply_retrace_guard(problem: _ChainProblem, mask: np.ndarray, *, prox_weight: float) -> _ChainProblem:
    """Give the caged anchors the FULL chain λ and everything else λ_prox.

    The chain objective already carries a PER-ANCHOR Tikhonov weight
    (`_ChainProblem.reg_w`, 1 on letter anchors and 0 on connector interiors),
    so the guard needs no new machinery and no new term: the effective weight of
    an anchor is `lambda_reg · reg_w[i]`, and this pins `lambda_reg` at the
    chain's own `core.fit.DEFAULT_LAMBDA_REG` while scaling `reg_w` by
    `prox / λ_chain` everywhere the mask is False. Two consequences, both
    intended:

    * a caged anchor keeps EXACTLY the λ it had in the chain — which for a
      connector interior is still 0, because the connector is form-unregularised
      by binding constraint 3 and „full λ" there means zero;
    * λ_prox = 0 stays expressible (arm ①'s first rung), which a `lambda_reg = 0`
      formulation could not combine with a guard at all.

    `n_letter_anchors`, the term's normaliser, is deliberately NOT recomputed: it
    counts the letter anchors, so per-letter Tikhonov pressure keeps comparing
    like with like across arms.
    """
    scale = float(prox_weight) / DEFAULT_LAMBDA_REG
    problem.lambda_reg = float(DEFAULT_LAMBDA_REG)
    problem.reg_w = problem.reg_w * np.where(np.asarray(mask, dtype=bool), 1.0, scale)
    return problem


# ------------------------------------------------------------ the round engine


def _fields_of(problem: _ChainProblem) -> dict:
    """The field block `build_chain_problem` takes, read off a built problem.

    The very arrays the first solve used — including the ALREADY subsampled
    coverage targets, so a rebuild cannot silently re-draw them (the subsampling
    is idempotent below its cap) and the follower is graded on the same ink.
    """
    return {
        "dist_raw": problem.dist_raw,
        "dist_smooth": problem.dist_smooth,
        "width_raw": problem.width_raw,
        "width_smooth": problem.width_smooth,
        "cov_pts": problem.cov_pts,
        "crop_shape": (problem.crop_h, problem.crop_w),
        "skel": problem.skel,
    }


def build_follow_problem(
    problem: _ChainProblem, params: np.ndarray, weights: FollowWeights
) -> tuple[_ChainProblem, np.ndarray]:
    """The re-linearised problem for the next round, plus its retrace mask.

    `respec_from_solution` carries the chain forward with the SOLVED anchors as
    its initial ones (everything else verbatim — kinds, slots, keys, pen-lift
    bounds, corners, half-widths, seam wiring, coverage windows), and this
    rebuilds around them with the follower's weights. What that buys is stated
    in the module docstring; what it MEANS for the Tikhonov term is stated in
    `apply_retrace_guard`.
    """
    specs = respec_from_solution(problem, params)
    # `build_chain_problem`'s own plan anchor count: one plan row per anchor of
    # every spec (the seams collapse in the FREE array, not the plan one).
    k_plan = sum(len(np.asarray(s.anchors).reshape(-1, 2)) for s in specs)
    rebuilt = build_chain_problem(
        specs,
        unit_px=problem.unit_px,
        x_origin_px=problem.x_origin_px,
        baseline_y_px=problem.baseline_y_px,
        n_samples=int(round(weights.samples_per_anchor * k_plan)),
        width_weight=weights.width,
        coverage_weight=weights.coverage,
        lambda_reg=weights.prox,
        smooth_weight=weights.smooth,
        bind_weight=weights.bind,
        landmark_weight=weights.landmark,
        overlap_weight=weights.overlap,
        max_anchor_delta=weights.max_delta,
        connector_max_delta=weights.connector_max_delta,
        **_fields_of(problem),
    )
    mask = (
        retrace_anchor_mask(rebuilt, prox_units=weights.retrace_prox_units)
        if weights.retrace_guard
        else np.zeros(len(rebuilt.anchors_free), dtype=bool)
    )
    apply_retrace_guard(rebuilt, mask, prox_weight=weights.prox)
    return rebuilt, mask


def _solve_round(
    problem: _ChainProblem, weights: FollowWeights, index: int, mask: np.ndarray
) -> tuple[np.ndarray, dict]:
    """One L-BFGS-B round from `x0` = 0, plus the record it has to leave behind."""
    started = time.perf_counter()
    before = problem.energy_terms(problem.x0)
    res = minimize(
        problem.objective,
        problem.x0,
        jac=True,
        method="L-BFGS-B",
        bounds=problem.bounds,
        # 50x the iteration budget, as everywhere on this path: with an analytic
        # jacobian the EVALUATION budget must never be the binding stop.
        options={"maxiter": weights.max_iter, "maxfun": 50 * weights.max_iter},
    )
    after = problem.energy_terms(res.x)
    motion = problem.free_anchors(res.x) - problem.anchors_free
    max_motion = float(np.max(np.hypot(motion[:, 0], motion[:, 1]))) if len(motion) else 0.0
    record = {
        "round": index,
        "n_params": int(len(problem.x0)),
        "n_anchors_free": int(len(problem.anchors_free)),
        "n_samples": int(problem.n_samples),
        "n_retrace_anchors": int(np.count_nonzero(mask)),
        "energy_before": round(float(before["f"]), 6),
        "energy_after": round(float(after["f"]), 6),
        "e_geo_before": round(float(before["e_geo"]), 6),
        "e_geo_after": round(float(after["e_geo"]), 6),
        "e_reg_before": round(float(before["e_reg"]), 6),
        "e_reg_after": round(float(after["e_reg"]), 6),
        "max_anchor_motion_units": round(max_motion, 6),
        "iterations": int(res.nit),
        "n_evaluations": int(res.nfev),
        # L-BFGS-B status 1 is exactly „the budget stopped it" — a capped round
        # was still descending, so its geometry is a snapshot of an unfinished
        # descent (`chain.fit_word_chain` says the same about its own solve).
        "hit_iteration_cap": int(res.status) == 1,
        "optimizer_status": int(res.status),
        "optimizer_success": bool(res.success),
        "message": str(res.message),
        "seconds": round(time.perf_counter() - started, 3),
    }
    return res.x, record


def _restart_slots(case: WordCase) -> set[int]:
    """Slots holding a restart-class capital (`core.compose.CAP_RESTART_BASES`).

    The writer LIFTS after such a capital, so the composed connector's retrace
    prefix is a render construct rather than pen travel — `assemble_word_strokes`
    needs to know which slots those are. One expression, mirrored from
    `tools.laufform.harvest.chain_word_strokes`, so the assembled trace of the
    follower and of the chain are cut at the same places.
    """
    return {i for i, s in enumerate(case.slots) if s.key and _key_base(s.key, s.position) in CAP_RESTART_BASES}


def _registration_of(result: WordDeriveResult) -> dict:
    return {"tx": result.registration["tx"], "ty": result.registration["ty"], "baseline_row": result.baseline_row}


def _chart_frame_offsets(case: WordCase, result: WordDeriveResult, slots: Sequence[int]) -> dict[int, float]:
    """Per slot: the composed-frame x offset `_letter_spec` placed its chart row at.

    `fit_word_chain` subtracts exactly this from a letter's fitted anchors before
    reporting them, so a follower round has to subtract it too or the two fits
    would report in different frames.
    """
    out: dict[int, float] = {}
    for slot_index in slots:
        made = _letter_spec(case, result, int(slot_index))
        out[int(slot_index)] = 0.0 if made is None else float(made[1])
    return out


def follow_word_chain(
    case: WordCase,
    slots: Sequence[int],
    *,
    result: WordDeriveResult,
    windows_px: dict[int, tuple[float, float]],
    fit: ChainWordFit | None = None,
    weights: FollowWeights | None = None,
    keep_solve: bool = False,
) -> FollowFit | None:
    """Follow the ink for ONE run of joined slots: solve 1, then the rounds.

    `fit` is the run's chain fit; when None it is solved here, always with
    `keep_solve=True`, because a re-linearising restart needs the very problem
    the optimum came from (the fields, the operators, the index map) rather than
    a rebuild of it. A fit handed in WITHOUT its solve is a caller error and
    raises rather than silently re-solving something else.

    With `weights.rounds == 0` the follower is an identity: the chain fit's own
    geometry, segments and assembled trace come back unchanged. That is not a
    degenerate case but the baseline arm — it makes „the follower changed
    nothing" a testable statement instead of a claim.

    None whenever the chain itself could not be built (see `fit_word_chain`).
    """
    weights = weights or FollowWeights()
    started = time.perf_counter()
    if fit is None:
        fit = fit_word_chain(case, slots, result=result, windows_px=windows_px, keep_solve=True)
    if fit is None:
        return None
    if fit.problem is None or fit.params is None:
        raise ValueError("follow_word_chain needs the solved chain problem — call fit_word_chain(..., keep_solve=True)")

    xh = float(result.xh_px)
    registration = _registration_of(result)
    restart_slots = _restart_slots(case)
    problem: _ChainProblem = fit.problem
    params: np.ndarray = fit.params
    rounds: list[dict] = []
    stopped_early = False

    for index in range(1, int(weights.rounds) + 1):
        problem, mask = build_follow_problem(problem, params, weights)
        params, record = _solve_round(problem, weights, index, mask)
        rounds.append(record)
        if record["max_anchor_motion_units"] < weights.round_eps_units:
            stopped_early = True
            break

    if not rounds:
        # The identity arm: everything below would reproduce the chain's own
        # report term for term, so it is READ rather than recomputed.
        segments = fit.segments
        stroke_polylines = fit.stroke_polylines_px
        slot_shift = fit.slot_shift_units
        at_bound = fit.slot_at_bound
        global_shift = fit.global_shift_units
        converged, converged_local = fit.converged, fit.converged_local
    else:
        segments = problem.report_energies(params)
        offsets = _chart_frame_offsets(case, result, fit.slots)
        for seg in segments:
            if seg.fitted_anchors is not None and seg.slot_index is not None:
                seg.fitted_anchors = seg.fitted_anchors - np.array([offsets.get(int(seg.slot_index), 0.0), 0.0])
        px, py = problem.to_pixels(params)
        stroke_polylines = _stroke_polylines_px(problem, px, py)
        _, _, blocks, _ = problem.unpack(params)
        slot_shift = {slot: (float(blocks[j, 0]), float(blocks[j, 1])) for j, slot in enumerate(problem.slot_blocks)}
        at_bound = {
            slot: bool(abs(dx) >= FIT_DX_UNITS - 1e-9 or abs(dy) >= FIT_DY_UNITS - 1e-9)
            for slot, (dx, dy) in slot_shift.items()
        }
        global_shift = (float(params[0]), float(params[1]))
        letters = [seg for seg in segments if seg.kind == "letter"]
        converged = bool(letters) and all(seg.converged for seg in letters)
        converged_local = bool(letters) and all(seg.converged_local for seg in letters)

    strokes_units = assemble_word_strokes(
        stroke_polylines, traced_slots=set(fit.slots), xh=xh, registration=registration, restart_slots=restart_slots
    )
    return FollowFit(
        case=case,
        slots=list(fit.slots),
        segments=segments,
        stroke_polylines_px=stroke_polylines,
        strokes_units=strokes_units,
        slot_shift_units=slot_shift,
        slot_at_bound=at_bound,
        global_shift_units=global_shift,
        rounds=rounds,
        converged=converged,
        converged_local=converged_local,
        fit_meta={
            "fit_path": "follow",
            "weights": asdict(weights),
            "provisional": bool(weights.provisional),
            "n_rounds": len(rounds),
            "rounds_requested": int(weights.rounds),
            "stopped_early": stopped_early,
            "hit_iteration_cap": any(r["hit_iteration_cap"] for r in rounds),
            "retrace_anchors": rounds[-1]["n_retrace_anchors"] if rounds else 0,
            "n_params": int(len(problem.x0)),
            "n_samples": int(problem.n_samples),
            "geo_rmse_px": {s.key or s.kind: round(s.geo_rmse_px, 3) for s in segments},
            "cov_rmse_local_px": {s.key or s.kind: round(s.cov_rmse_local_px, 3) for s in segments},
            "chain_fit_meta": {
                k: fit.fit_meta.get(k)
                for k in ("iterations", "hit_iteration_cap", "n_params", "n_samples", "energies", "seconds")
            },
            "slots": list(fit.slots),
            "timings": {"seconds": round(time.perf_counter() - started, 3)},
        },
        problem=problem if keep_solve else None,
        params=np.asarray(params, dtype=float).copy() if keep_solve else None,
    )


# ------------------------------------------------------------------- one case


def follow_derived(
    case: WordCase, result: WordDeriveResult, *, weights: FollowWeights | None = None, chain_seed: str = "composed"
) -> dict:
    """The whole word for an ALREADY composed case — the candidate-shaped row.

    The harvest's plumbing verbatim (`tools.laufform.harvest.chain_word_strokes`
    read side by side): one EDT-backed grid fit per slot for the coverage
    windows, `_chainable_runs` to cut the word into runs the chain can carry,
    one solve per run, the pen path welded by `assemble_word_strokes` and capped
    to the wire limits, and the row shaped by the harvest's own `_word_record`
    so the registration is the one the row would be STORED with. The follower
    replaces exactly ONE thing in that pipeline — the fit each run uses — and
    nothing about the frame, the windows or the assembly.
    """
    weights = weights or FollowWeights()
    started = time.perf_counter()
    xh = result.xh_px
    registration = _registration_of(result)
    grids = _grid_fits(case, result)

    word_strokes: list[list[list[float]]] = []
    run_slots: list[list[int]] = []
    rounds_by_run: list[list[dict]] = []
    traced: set[int] = set()
    n_runs = n_failed = n_params = 0
    for run in _chainable_runs(case, grids):
        n_runs += 1
        windows = {s: grids[s]["window"] for s in run}
        seeds = {s: grids[s]["shift_units"] for s in run if not grids[s]["at_bound"]} if chain_seed == "grid" else None
        chain_fit = fit_word_chain(case, run, result=result, windows_px=windows, slot_shift_init=seeds, keep_solve=True)
        if chain_fit is None:
            n_failed += 1
            continue
        followed = follow_word_chain(case, run, result=result, windows_px=windows, fit=chain_fit, weights=weights)
        if followed is None:
            n_failed += 1
            continue
        run_slots.append(list(followed.slots))
        rounds_by_run.append(followed.rounds)
        traced.update(int(s) for s in followed.slots)
        n_params += int(followed.fit_meta.get("n_params", 0))
        word_strokes.extend(followed.strokes_units)

    meta = {
        "fit_path": "follow",
        "weights": asdict(weights),
        "provisional": bool(weights.provisional),
        "chain_seed": chain_seed,
        "runs": n_runs,
        "runs_failed": n_failed,
        "traced_slots": sorted(traced),
        "run_slots": run_slots,
        "rounds": rounds_by_run,
        "n_params": n_params,
        "timings": {"seconds": round(time.perf_counter() - started, 3)},
    }
    if not word_strokes:
        return {
            "kind": case.kind,
            "specimen_id": case.id,
            "word": case.word,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_FAILED,
            "detail": "the follower produced no pen path",
            "meta": meta,
        }
    strokes = cap_word_strokes(word_strokes, label=f"{case.id} (follow)")
    record = _word_record(case, strokes, registration, xh, {})
    return {
        "kind": record["kind"],
        "specimen_id": record["specimen_id"],
        "word": record["word"],
        "strokes": record["strokes"],
        "registration_px": record["measurements"]["registration_px"],
        "xh_px": record["measurements"]["xh_px"],
        "status": STATUS_OK,
        "detail": "",
        "meta": meta,
    }


def follow_case(case: WordCase, *, weights: FollowWeights | None = None, chain_seed: str = "composed") -> dict:
    """`follow_derived` with the composition done here — one case, one row.

    A case the fixtures froze as unscorable (an unauthored template) or a
    composition that is missing a glyph is `skipped` with the reason, never an
    exception: one word must not take a sweep down (`tracebench`'s doctrine, and
    the harvest's).
    """
    base = {"kind": case.kind, "specimen_id": case.id, "word": case.word}
    if not case.scorable:
        return {
            **base,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_SKIPPED,
            "detail": "frozen unscorable (unauthored template)",
            "meta": {},
        }
    try:
        result = derive_word(case)
    except Exception as exc:  # noqa: BLE001 — one bad case must not end the run
        return {
            **base,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_FAILED,
            "detail": f"{type(exc).__name__}: {exc}",
            "meta": {},
        }
    if result.composed.get("missing"):
        return {
            **base,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_SKIPPED,
            "detail": f"composition missing {result.composed['missing']}",
            "meta": {},
        }
    try:
        return follow_derived(case, result, weights=weights, chain_seed=chain_seed)
    except Exception as exc:  # noqa: BLE001 — a solver crash is one word's row
        return {
            **base,
            "strokes": [],
            "registration_px": {},
            "xh_px": None,
            "status": STATUS_FAILED,
            "detail": f"{type(exc).__name__}: {exc}",
            "meta": {},
        }


# ------------------------------------------------------------ the candidate file


def candidate_payload(
    infos: Sequence[dict],
    *,
    style: str,
    source_id: str,
    which: str,
    label: str = "follow",
    weights: FollowWeights | None = None,
) -> dict:
    """The rows as a `tools.tracebench` FILE-provider candidate.

    `frame` is the mandatory literal the bench refuses a file without: a trace
    in crop pixels or in a model's own grid would otherwise be measured as a
    catastrophic tracing error instead of being rejected. Rows that produced no
    trace are NOT written as empty candidates — they would fail the wire check
    and read as a scored failure — but counted by reason under `excluded`, the
    excluded-and-counted doctrine the reference loader uses.
    """
    rows = [
        {
            "kind": info.get("kind"),
            "specimen_id": info["specimen_id"],
            "word": info.get("word"),
            "registration_px": info["registration_px"],
            "xh_px": info["xh_px"],
            "strokes": info["strokes"],
            "status": info.get("status", STATUS_OK),
            "meta": info.get("meta", {}),
        }
        for info in infos
        if info.get("status") == STATUS_OK and info.get("strokes")
    ]
    excluded = [
        {"specimen_id": i["specimen_id"], "status": i.get("status"), "detail": i.get("detail", "")}
        for i in infos
        if i.get("status") != STATUS_OK or not i.get("strokes")
    ]
    return {
        "tool": FOLLOW_TOOL_NAME,
        "version": FOLLOW_ARTIFACT_VERSION,
        "label": label,
        "style": style,
        "source_id": source_id,
        "set": which,
        "frame": CANDIDATE_FRAME,
        "weights": asdict(weights or FollowWeights()),
        "provisional": bool((weights or FollowWeights()).provisional),
        "excluded": excluded,
        "rows": rows,
    }


# --------------------------------------------------------------------- the CLI


def _source_id_of(fixtures_root: Path, style: str, which: str) -> str:
    """The frozen root's own `source_id` — the manifest's, never guessed."""
    style_root = Path(fixtures_root) / style
    for manifest_path in sorted(style_root.glob("*/manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("set", "words") == which:
            return str(manifest.get("source_id", manifest_path.parent.name))
    return ""


def _load_cases(ids: list[str], *, which: str, style: str, fixtures_root: Path) -> list[WordCase]:
    """The frozen cases, or a readable exit — the labs' shared skip behaviour."""
    try:
        return iter_fixture_word_cases(which=which, style=style, only=ids or None, fixtures_root=fixtures_root)
    except KeyError as exc:
        # `_root_for`'s own sentence already names the set, the root and the
        # exporter; only the read-only alternative is added.
        raise SystemExit(f"{exc.args[0] if exc.args else exc} (or tools/wordbench/fetch_fixtures)") from None
    except OSError as exc:
        raise SystemExit(
            f"the {which!r} fixture root under {Path(fixtures_root) / style} is incomplete: {exc}"
        ) from None


def parse_sweep(spec: str) -> tuple[str, list[float]]:
    """`"prox=1.0,0.1,0"` → `("prox", [1.0, 0.1, 0.0])`, validated against the arms."""
    name, _, raw = spec.partition("=")
    name = name.strip()
    known = {f.name for f in fields(FollowWeights)}
    if name not in known:
        raise SystemExit(f"--sweep {name!r} is not a FollowWeights field; known: {', '.join(sorted(known))}")
    try:
        values = [float(v) for v in raw.split(",") if v.strip()]
    except ValueError:
        raise SystemExit(f"--sweep {spec!r}: values must be numbers") from None
    if not values:
        raise SystemExit(f"--sweep {spec!r}: no values given")
    return name, values


def _with(weights: FollowWeights, name: str, value: float) -> FollowWeights:
    """One swept arm — ints stay ints so `rounds=2.0` cannot reach the loop."""
    current = getattr(weights, name)
    return replace(
        weights, **{name: int(value) if isinstance(current, int) and not isinstance(current, bool) else value}
    )


def _run_arm(job: tuple[WordCase, FollowWeights, str]) -> dict:
    case, weights, chain_seed = job
    info = follow_case(case, weights=weights, chain_seed=chain_seed)
    rounds = [r for run in info.get("meta", {}).get("rounds", []) for r in run]
    print(
        f"  {case.id:<24} {info['status']:<8} strokes {len(info['strokes']):>3}  "
        f"rounds {len(rounds):>2}  motion {max((r['max_anchor_motion_units'] for r in rounds), default=0.0):.4f} xh  "
        f"{info.get('meta', {}).get('timings', {}).get('seconds', 0.0):.1f}s"
        + (f"  {info['detail']}" if info["detail"] else ""),
        flush=True,
    )
    return info


def run_arm(cases: Sequence[WordCase], weights: FollowWeights, *, chain_seed: str, jobs: int = 1) -> list[dict]:
    """Every case at ONE configuration, in fixture order (pooling is per case)."""
    payloads = [(c, weights, chain_seed) for c in cases]
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            return list(pool.map(_run_arm, payloads))
    return [_run_arm(p) for p in payloads]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pairlab.follow", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("ids", nargs="*", help="fixture case ids (or words); default with --all: the whole set")
    parser.add_argument("--all", action="store_true", help="every case of the set")
    parser.add_argument("--set", dest="which", default="words", choices=["words", "pairs"])
    parser.add_argument("--style", default="suetterlin")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES_DIR)
    parser.add_argument("--chain-seed", default="composed", choices=["composed", "grid"])
    parser.add_argument("--rounds", type=int, help=f"re-linearising rounds (default {FOLLOW_ROUNDS})")
    parser.add_argument("--prox", type=float, help=f"proximal weight (default {FOLLOW_PROX_WEIGHT})")
    parser.add_argument("--coverage", type=float, help=f"coverage weight (default {FOLLOW_COVERAGE_WEIGHT})")
    parser.add_argument("--samples-per-anchor", type=float, help=f"default {FOLLOW_SAMPLES_PER_ANCHOR:.4g}")
    parser.add_argument("--overlap", type=float, help=f"overlap weight (default {FOLLOW_OVERLAP_WEIGHT})")
    parser.add_argument("--landmark", type=float, help=f"landmark weight (default {FOLLOW_LANDMARK_WEIGHT})")
    parser.add_argument("--bind", type=float, help=f"letter bind weight (default {FOLLOW_BIND_WEIGHT}, rejected term)")
    parser.add_argument("--max-delta", type=float, help=f"per-anchor travel budget (default {FOLLOW_MAX_DELTA})")
    parser.add_argument("--no-retrace-guard", action="store_true", help="release the retrace zones too (a measurement)")
    parser.add_argument("--sweep", help="NAME=v1,v2 — one arm per value of a FollowWeights field")
    parser.add_argument("--jobs", type=int, default=1, help="worker processes, pooled over CASES")
    parser.add_argument("--json", type=Path, help="write the full report here")
    parser.add_argument("--candidate-out", type=Path, help="write a tracebench file-provider candidate here")
    return parser


def weights_from_args(args: argparse.Namespace) -> FollowWeights:
    overrides: dict[str, Any] = {
        "rounds": args.rounds,
        "prox": args.prox,
        "coverage": args.coverage,
        "samples_per_anchor": args.samples_per_anchor,
        "overlap": args.overlap,
        "landmark": args.landmark,
        "bind": args.bind,
        "max_delta": args.max_delta,
    }
    weights = FollowWeights(**{k: v for k, v in overrides.items() if v is not None})
    return replace(weights, retrace_guard=not args.no_retrace_guard)


def main() -> None:
    args = build_parser().parse_args()
    if not args.ids and not args.all:
        raise SystemExit("name at least one case id, or pass --all")
    started = time.perf_counter()
    cases = _load_cases(list(args.ids), which=args.which, style=args.style, fixtures_root=args.fixtures)
    if not cases:
        raise SystemExit(f"no case matched {args.ids!r} in the {args.which!r} set")

    base = weights_from_args(args)
    arms: list[tuple[str, FollowWeights]] = [("base", base)]
    if args.sweep:
        name, values = parse_sweep(args.sweep)
        arms = [(f"{name}={v:g}", _with(base, name, v)) for v in values]

    print(f"follower: {len(cases)} cases · set {args.which} · {len(arms)} arm(s) · PROVISIONAL weights")
    report: dict[str, Any] = {
        "tool": FOLLOW_TOOL_NAME,
        "version": FOLLOW_ARTIFACT_VERSION,
        "style": args.style,
        "set": args.which,
        "chain_seed": args.chain_seed,
        "arms": [],
    }
    last_infos: list[dict] = []
    last_weights = base
    for label, weights in arms:
        print(f"arm {label}: prox {weights.prox:g} · rounds {weights.rounds} · coverage {weights.coverage:g}")
        infos = run_arm(cases, weights, chain_seed=args.chain_seed, jobs=max(1, args.jobs))
        report["arms"].append({"label": label, "weights": asdict(weights), "rows": infos})
        last_infos, last_weights = infos, weights

    report["runtime_s"] = round(time.perf_counter() - started, 1)
    print(f"runtime {report['runtime_s']}s")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=1, ensure_ascii=False))
        print(f"wrote {args.json}")
    if args.candidate_out:
        if len(arms) > 1:
            print(f"  note: --sweep ran {len(arms)} arms; the candidate file holds the LAST ({arms[-1][0]})")
        payload = candidate_payload(
            last_infos,
            style=args.style,
            source_id=_source_id_of(args.fixtures, args.style, args.which),
            which=args.which,
            weights=last_weights,
        )
        args.candidate_out.parent.mkdir(parents=True, exist_ok=True)
        args.candidate_out.write_text(json.dumps(payload, ensure_ascii=False))
        print(f"wrote {args.candidate_out} ({len(payload['rows'])} rows, {len(payload['excluded'])} excluded)")


__all__ = [
    "CANDIDATE_FRAME",
    "FOLLOW_ARTIFACT_VERSION",
    "FOLLOW_BIND_WEIGHT",
    "FOLLOW_CONNECTOR_MAX_DELTA",
    "FOLLOW_COVERAGE_WEIGHT",
    "FOLLOW_LANDMARK_WEIGHT",
    "FOLLOW_MAX_DELTA",
    "FOLLOW_MAX_ITER",
    "FOLLOW_OVERLAP_WEIGHT",
    "FOLLOW_PROX_WEIGHT",
    "FOLLOW_RETRACE_PROX_UNITS",
    "FOLLOW_ROUNDS",
    "FOLLOW_ROUND_EPS_UNITS",
    "FOLLOW_SAMPLES_PER_ANCHOR",
    "FOLLOW_TOOL_NAME",
    "FOLLOW_WIDTH_WEIGHT",
    "FollowFit",
    "FollowWeights",
    "apply_retrace_guard",
    "build_follow_problem",
    "candidate_payload",
    "follow_case",
    "follow_derived",
    "follow_word_chain",
    "parse_sweep",
    "retrace_anchor_mask",
    "retrace_sample_mask",
    "run_arm",
]


if __name__ == "__main__":
    main()
