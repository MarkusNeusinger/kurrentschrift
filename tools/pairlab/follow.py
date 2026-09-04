"""The ink follower: a re-linearising restart that pulls the chain onto the ink.

The structure-guarded run of this follower is what the duel page labels
"Kette" (owner decision 2026-08-16: the guarded variant is THE chain; see the
glossary entry "Duell-Namen").

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

**The landmark targets** (arm ⑥). The chain's crossing correspondence aims at a
skeleton BRANCH POINT, and thinning displaces that point by up to the local
stroke width — more than the anchor spacing the term is supposed to correct.
`extrapolated_targets` re-aims it at the intersection of the incident branches
extrapolated across the junction, with the local half-width as an isotropic
uncertainty that enters as a per-target `1/sigma^2` weight
(`apply_landmark_targets`). Finding those branches on real cursive ink is the
hard half and is done by a GEODESIC walk along the skeleton whose core swallows
the whole junction CLUSTER — `_incident_branches` says what a Euclidean annulus
around the branch point gets wrong, and why it refined nothing at all on the
first ten words. Refusals keep the raw branch point and say why, separating what
the ink cannot support from what the walk failed to find (`_refine_one`). All
of it is skipped at `landmark = 0`, which is the shipped default, so the ladder's
rungs are chosen from measured ratios (`--landmark-calibrate`) rather than by
analogy — §11c's standing warning.

**Guard rails** (§3, binding): strictly additive and opt-in; `KS_FOLLOW_*` never
moves a `CHAIN_*`; no chain solve changes; the harvest gets no follower path
here; nothing writes to the DB, the API, `core/` or any rendering path. Every
shipping weight below is PROVISIONAL — stamped as such into every artefact — and
acceptance is decided by `tools/tracebench`, never by the distance-transform
residual this solve minimises itself.

    uv run python -m tools.pairlab.follow die laden --rounds 2
    uv run python -m tools.pairlab.follow --all --set words --candidate-out temp/follow.json
    uv run python -m tools.pairlab.follow die --sweep prox=1.0,0.1,0.0
    uv run python -m tools.pairlab.follow --all --landmark-calibrate --json temp/lm-calib.json
    uv run python -m tools.pairlab.follow --all --landmark <w> --landmark-targets extrapolated
"""

from __future__ import annotations

import argparse
import heapq
import json
import os
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from typing import Any

import numpy as np
from scipy.ndimage import label as label_regions
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
from tools.pairlab.ink_evidence import INK_EVIDENCE_PAPER_FRACTION, InkEvidenceOptions, ink_evidence_case
from tools.pairlab.landmarks import LANDMARK_MIN_ANGLE_DEG
from tools.pairlab.trace import assemble_word_strokes, cap_word_strokes
from tools.tracebench.counters import crossing_points, structure_zones
from tools.tracebench.soll import composition_strokes
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

# --- arm ⑥: WHERE the landmark term's target sits ----------------------------
#
# The chain's correspondence (`chain._landmark_correspondence`) pulls a fitted
# crossing onto the nearest skeleton BRANCH POINT. That point is systematically
# the wrong TARGET: thinning displaces a junction's branch point by up to the
# local stroke width (tintenfolger.md §3, from the published junction
# literature), i.e. ±2–4 px on this material — LARGER than the ~1.5 px anchor
# spacing the term exists to correct, so a term aimed at it would price a
# structure error against a point that carries one of its own. The published
# correction is to extrapolate the incident centerline branches across the
# junction and to intersect them, with an isotropic uncertainty of about the
# local stroke width.
#
# Four modes, so the ladder can move ONE thing at a time (§11c/§11d):
#
# * `raw` — the chain's branch points verbatim. THE control arm: the term
#   exactly as it ships today, so „refined targets" is a paired comparison
#   against the formulation it replaces rather than against nothing.
# * `extrapolated_uniform` — refined targets, uniform weights.
# * `extrapolated` — refined targets AND the 1/σ² weighting.
# * `extrapolated_classed` — arm ⑥b: refined targets, 1/σ² weighting, and the
#   by-design non-crossings CLASSED OUT (weight 0). Arm ⑥ measured that 12 of
#   the dev words' 21 correspondences aim at ink that carries NO crossing at
#   all — the path crosses itself where the ink merely touches — which caps any
#   effect the term can have; this mode is the pre-registered answer
#   (messjournal.md §14 arm ⑥b): those classes are not crossing targets.
#
# NOTHING here is calibrated, and no weight is proposed: at `landmark == 0` the
# whole block is skipped and every solve stays byte-identical (the term's own
# inertness rule, `chain.CHAIN_LANDMARK_WEIGHT`).
FOLLOW_LANDMARK_TARGETS_ENV = "KS_FOLLOW_LANDMARK_TARGETS"
FOLLOW_LANDMARK_TARGETS = os.environ.get(FOLLOW_LANDMARK_TARGETS_ENV) or "extrapolated"
LANDMARK_TARGET_MODES = ("extrapolated", "extrapolated_uniform", "extrapolated_classed", "raw")
# The refinement reasons that state the INK at the target carries no crossing —
# `touch_point` (exactly two limbs: a stroke passing through, a retrace touch, a
# corner) and `t_junction` (exactly three limbs). They are a property of the ink,
# not a failure of the walk (`_refine_one` separates the two vocabularies), so
# `extrapolated_classed` drops these rows from the correspondence entirely; the
# walk failures keep their raw target as before, because there the ink CAN carry
# a crossing the refinement merely failed to find.
LANDMARK_NONCROSSING_REASONS = ("touch_point", "t_junction")
# FLOOR (xh) on the reach of the skeleton walk around a branch point. 0.5 xh is
# ~15 px on this material: enough beyond the excluded core for a stable
# direction, and short enough that the branch's OWN curvature does not out-bias
# the junction displacement being corrected. The proposal's sketch said 1.5–2 xh;
# that is rejected here on the geometry rather than by taste — a Sütterlin letter
# is 1–2 xh tall, so a 1.5 xh branch bends by ~5 px against its chord on a
# 0.5 xh-radius turn (L²/8R), which is larger than the ±2–4 px the correction is
# worth. Measured, a wider window is not merely wasteful but actively wrong: at
# 1.5 xh the disc reaches around whole letters, and the walk that predated the
# junction cluster welded 10 of 21 targets' limbs into a single component.
#
# It is a floor and not the reach itself: `extrapolated_targets` takes the LARGER
# of it and `cluster + core + min_branch`, because a walk that stops inside its
# own junction cluster has no limb to fit. On the dev words the cluster clause
# binds (24–31 px against this floor's 15), which is the honest statement of how
# far the walk really goes.
FOLLOW_LANDMARK_WINDOW_UNITS_ENV = "KS_FOLLOW_LANDMARK_WINDOW_UNITS"
FOLLOW_LANDMARK_WINDOW_UNITS = float(os.environ.get(FOLLOW_LANDMARK_WINDOW_UNITS_ENV) or 0.5)
# Junction core to EXCLUDE from the line fits, in local HALF-widths: 2.0 = one
# full stroke width. That is exactly the published displacement bound — the
# pixels inside it are the ones thinning can have moved, so they are the ones a
# line fitted to the undistorted branch must not see.
FOLLOW_LANDMARK_CORE_WIDTHS = 2.0
# …and its floor in px, for a hairline whose half-width rounds to well under a
# pixel: below ~2 px the "core" would exclude nothing at all and the fit would
# run straight through the junction blob it is meant to step over.
FOLLOW_LANDMARK_CORE_MIN_PX = 2.0
# Junction-CLUSTER radius, in local HALF-widths: how far along the ink the core
# absorbs further fork pixels before the limbs are cut.
#
# Thinning does not turn one shallow crossing into one branch point. It turns it
# into TWO Y-junctions bridged by a short segment, and the bridge grows as the
# crossing angle shrinks. A core that stops before the bridge therefore walks a
# real X as a T: three limbs (two real ones and the bridge), the fourth limb
# hidden behind the partner Y — and three limbs can yield at most ONE
# continuation pair, so the refinement refuses by construction, whatever the
# tolerance says. That is the mechanism behind 16 of the 21 `no_continuation_pair`
# refusals measured on the dev words.
#
# The bound is measured, not assumed: over the 16 distinct junctions the 10 dev
# words' landmark targets sit on, the partner branch point sits 9.4–13.2 px away
# by ARC where the local stroke is 6.4–8.4 px wide — 1.2–1.7 stroke widths, i.e.
# 2.4–3.4 half-widths. 4.0 half-widths (= 2 stroke widths) covers that with
# headroom and stays well inside the letter, and it is a GEODESIC radius, so a
# neighbouring stroke passing close in the image is never absorbed.
FOLLOW_LANDMARK_CLUSTER_WIDTHS = 4.0
# Minimum branch span (px) OUTSIDE the core. The walk radius is widened to
# `core + this` where the window would otherwise leave no branch to fit.
FOLLOW_LANDMARK_MIN_BRANCH_PX = 6.0
# …and the minimum pixel count of a branch. A line has 2 degrees of freedom, so
# 4 pixels is the smallest set that can disagree with it twice over; below that
# a "direction" is the quantisation grid talking.
FOLLOW_LANDMARK_MIN_BRANCH_PIXELS = 4
# How far from anti-parallel two branches may point and still count as ONE
# stroke continuing through the junction ("gute Fortsetzung"). The pairing is
# GREEDY-BEST — the smallest deviation is taken first — so this threshold only
# ever REFUSES a branch that continues into nothing; it is not what tells the
# right partner from the wrong one.
#
# It was 30°, chosen as twice `landmarks.LANDMARK_MIN_ANGLE_DEG` — an argument
# about the CROSSING angle, which is not what this number measures. What it
# measures is how far two limbs of ONE pass deviate from anti-parallel, and on a
# cursive script that is dominated by the pass's own CURVATURE, not by the
# crossing: each limb's total-least-squares direction is the tangent at its own
# midpoint, so a limb spanning arc [s0, s1] is rotated (s0+s1)/2R from the
# tangent at the junction, and the two limbs rotate opposite ways in the outward
# frame — deviation (s0+s1)/R.
#
# Measured on the dev words, for the pairs whose two limbs really do lie on one
# arc (circle fit rms < 1 px, n = 6): observed deviation median 18.7°/max 28.4°
# against a predicted median 21.5°/max 33.8°, agreeing to a median 3.8°. The
# limbs span 8.4–31.1 px and the tightest radius a continuation is written with
# is ~70 px (2.3 xh), so the bound the geometry imposes is (10+31)/70 rad ≈ 34°.
# At 30° that refused four of the eight crossings the walk resolves, each by
# 0.8–1.5°. 35° clears the geometry; the answer is then FLAT to 45° (measured),
# so it is not a threshold sitting on a knife edge, and the second pair greedy
# actually proposes at a non-crossing sits at 148° — the gap is not close.
FOLLOW_LANDMARK_CONTINUATION_TOL_DEG = 35.0
# Uncertainty floor (px) of a refined target: one pixel, because the branch
# point it is measured against is itself a centroid on a pixel grid. Without a
# floor a hairline junction would claim an arbitrarily precise target and its
# 1/σ² weight would swallow the whole term.
FOLLOW_LANDMARK_SIGMA_FLOOR_PX = 1.0
# A refined intersection farther than this many local HALF-widths from the raw
# branch point is REFUSED (2.0 = one stroke width): the published displacement
# bound is the local stroke width, so an extrapolation that lands further has
# not corrected the junction, it has found a different one — and the honest
# answer is the raw branch point plus the reason.
FOLLOW_LANDMARK_MAX_SHIFT_WIDTHS = 2.0
# Multipliers of the PARITY weight the calibration hook reports. Same reading as
# `landmarklab.calibration`: the parity weight is `e_geo / e_landmark` at the
# optimum — the weight at which the correspondence weighs as much as the
# geometry term — and a rung is a fraction of it. §11c is why a ladder is read
# off the optimum instead of chosen by analogy.
LANDMARK_CALIBRATION_MULTIPLIERS = (0.01, 0.1, 1.0)
# The modes the calibration pass reads at the inert optimum — one row per mode
# per solve, so an arm picks its rung from a parity MEASURED in its own mode
# (§11c). `extrapolated_uniform` is deliberately absent: its geometry equals
# `extrapolated` and only the weighting differs, so its parity carries no new
# information the ladder could act on.
LANDMARK_CALIBRATION_MODES = ("raw", "extrapolated", "extrapolated_classed")
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
# Arm ⑨: how often a structure-violating round is re-solved with halved travel
# bounds before it is rejected back to the previous geometry. Two is the
# pre-registered number (§14 `aug16`): a third halving leaves ~12 % of the
# budget, at which point the round IS the previous geometry plus noise.
STRUCTURE_GUARD_MAX_RETRIES = 2

# The candidate file's mandatory frame literal. Re-declared rather than
# imported and pinned against `tools.tracebench.candidates.CANDIDATE_FRAME` by
# a test: the ruler's SCORING side (metric, matching, summaries) stays out of
# the candidate producer. The ruler's DETECTORS (`tools.tracebench.counters`)
# are deliberately shared since arm ⑨ — the structure guard must count exactly
# what the report counts — and that import is one-directional: the counters
# never import the follower.
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
    landmark_targets: str = FOLLOW_LANDMARK_TARGETS
    """WHERE the landmark term aims — `LANDMARK_TARGET_MODES`. Not a weight and
    therefore not sweepable by `--sweep`; it selects between formulations, and
    the arm runs one per configuration so each stays a single-factor step."""
    bind: float = FOLLOW_BIND_WEIGHT
    smooth: float = CHAIN_CONNECTOR_SMOOTH_WEIGHT
    max_delta: float = FOLLOW_MAX_DELTA
    connector_max_delta: float = FOLLOW_CONNECTOR_MAX_DELTA
    rounds: int = FOLLOW_ROUNDS
    round_eps_units: float = FOLLOW_ROUND_EPS_UNITS
    max_iter: int = FOLLOW_MAX_ITER
    retrace_prox_units: float = FOLLOW_RETRACE_PROX_UNITS
    retrace_guard: bool = True
    structure_guard: bool = True
    """Arm ⑨ (§14 `aug16`): a round-level ACCEPTANCE rule, not a force — a
    solved round whose assembled trace exceeds the initialisation's own v2.1
    structure class counts (crossings · retrace zones · touches · overlaps,
    counted by the bench's own `tools.tracebench.counters`) is re-solved with
    halved travel bounds, at most `STRUCTURE_GUARD_MAX_RETRIES` times, and
    otherwise rejected back to the previous geometry. Default True since Kette
    v5 (§14 `aug26`) together with the four fields below — the whole guard
    stack is the follower now. False (`--no-structure-guard`) is the
    archaeology path, byte-identical to the follower before the arm existed;
    it is a DIAGNOSTIC arm („Kette-frei"), never the duel candidate: freed of
    the guard it covers more ink by destroying structure (init 86 → free 125
    soll points over the 63 words, `aug26`)."""
    structure_guard_two_sided: bool = False
    """§14 „Wächter als Produktions-Kette" (`aug16`): the K0-invariant guard —
    the same acceptance rule, but the initialisation's counts bind in BOTH
    directions: a round that LOSES init structure (the ink pull collapsing a
    small loop) is rejected exactly like one that invents it. Implies the
    one-sided guard on the CLI; here it only sharpens the comparison."""
    structure_guard_ratchet: bool = True
    """K0-Z-R (§14 `aug20`): after every ACCEPTED round the guard budget
    snaps to that round's class counts, so the soll interval only ever
    tightens — movement continues toward the soll and can never legally
    fall back toward the original budget (the daß class of K0-Z). Only
    meaningful with the soll guard. Default True since Kette v5 (§14
    `aug26`); `--no-structure-guard-ratchet` is the K0-S Sprosse-1 rung."""
    structure_guard_zone_units: float = 0.55
    """K0-Z (§14 `aug20`): the ZONAL rejection radius, in x-heights. After
    the halving retries and before the full revert, the budget violations
    are localised (`_zone_violation_sites`), every free anchor within this
    radius of a violation site is pinned to the previous geometry (its
    delta bounds collapse to (0, 0); slot blocks and the global shift stay
    free — word-wide parameters have no zone), and the round is re-solved
    ONCE with the round's original bounds for the rest. Holds the budget →
    the round is accepted with its non-zonal repairs intact; otherwise the
    full revert stands. Default 0.55 since Kette v5 (§14 `aug26`) — it is
    the mechanism that carries the adoption: against the round-atomic soll
    guard, 26 of 31 moved words were a round-1 revert to the chain init,
    never followed at all; the zone rescues them (aiou median +0,073 over the
    moved words, zero losers). 0.0 = the round-atomic behaviour."""
    structure_guard_soll: bool = True
    """§14 „Wächter als Produktions-Kette" (`aug19`), rescue path (c): the
    soll-aware K0 guard. Every structure class of a round must lie in the
    closed interval between the chain optimum's count (the rounds' init,
    exactly the one-sided budget) and the COMPOSED init geometry's count
    (the trace at x0 = 0 through the same assembler and counters — the
    ductus-deterministic soll without a second implementation): movement
    only TOWARD the soll, never past it, never away; a class the two agree
    on freezes exactly (the two-sided special case). Implies the guard;
    takes precedence over `structure_guard_two_sided`."""
    ink_evidence: bool = True
    """K-C (§14 `aug20`, the author's "Flecken" find): before the grid fits and
    the solve, drop every non-main ink component that is paper-grey rather
    than ink-dark from the case's `skel`/`width_map`
    (`tools.pairlab.ink_evidence`) — specks, show-through of the sheet's
    reverse, everything the frozen binarisation kept that the word never
    wrote. The largest component (the word) and every component as dark as
    it (i-dots, u-bows, broken stroke fragments) stay. The bench's frozen
    mask is untouched; only what pulls the FIT changes. Default True since
    Kette v4 (§14 `aug21` re-baseline — all six aug20 gates passed, author's
    go); False (`--no-ink-evidence`) is the archaeology path: the case object
    passes through untouched, byte-identical to the pre-v4 follower."""
    ink_evidence_paper_fraction: float = INK_EVIDENCE_PAPER_FRACTION
    """Where on the main-ink → paper grey scale a component stops being ink.
    A measured class boundary (real ≤ 0.38, foreign ≥ 0.74 over the 63
    fixtures), not a tuning knob; stamped so an artefact records it."""
    mark_claim: bool = False
    """K-E stage 1 (§14 `aug21`, K-E2 form): the mark-claim separation — a
    diacritic stroke of the composed init (the K-A assembler criterion)
    claims its dark non-main ink component within the ruler's 0.6-xh mark
    radius, and a claim switches the two ATTRACTOR channels: the component
    leaves the body's distance field and coverage pot, the mark's samples
    read exclusively their component (`tools.pairlab.chain._prepare_fields`
    → `build_chain_problem`). The WIDTH fields stay whole — width is a
    measurement target, and K-E1 measured its split as the suspect behind
    the diffuse body-coverage loss. No claim → nothing changes; words
    without a firing claim stay byte-identical by construction. Default
    True since Kette v5 (§14 `aug26`, the measured adoption)."""
    soll_source: str = "composition"
    """K0-S (§14 `aug21`): where the soll guard's TARGET counts come from.
    `"composition"` (default since Kette v5, §14 `aug26`) = the canonical
    source: the composed items through the SHARED builder
    (`tools.tracebench.soll.composition_strokes`, restricted to the run) —
    the daß autopsy proved the init reading counts a flattened init sliver
    at the d head as ductus truth. `"init"` = the aug19 behaviour — the chain
    init at x0 = 0 through the assembler and counters; the K0-S ladder's
    base. Budget and round counts stay what they are; only the TARGET moves
    to the composition."""
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
    bench's own recipe (`tools/tracebench/counters.py`), reproduced here
    rather than imported because this mask lives on the PROBLEM's sample
    arrays and stroke map — a different data shape than the bench's assembled
    strokes (arm ⑨'s structure guard, which works on the assembled trace,
    imports the counters directly) — minus the zone merging, which only ever
    mattered for reporting a zone's POSITION.

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


# --------------------------------------------------------- the landmark targets


@dataclass(frozen=True)
class LandmarkTargeting:
    """Where the landmark term aims, and how hard, for ONE built problem.

    Row `i` corresponds to row `i` of `problem.landmark_op` — the kept
    correspondences in detection order, exactly the order `landmarklab.
    _kept_landmarks` walks. `targets` are in the problem's template units
    (composed frame, y up from the baseline, 1 unit = x-height), like
    `problem.landmark_targets`, and are the UNWHITENED points: a consumer that
    wants to know where the term aims reads them here rather than off a problem
    the whitening below has already scaled.
    """

    mode: str
    targets: np.ndarray  # (n, 2) refined (or raw) ink crossings, template units
    raw_targets: np.ndarray  # (n, 2) the skeleton branch points they came from
    sigmas: np.ndarray  # (n,) isotropic 1-sigma uncertainty, template units
    weights: np.ndarray  # (n,) relative 1/sigma^2 weights, normalised to mean 1
    reasons: list[str]  # per row: "ok", "raw", or the refusal that kept the raw point
    entries: list[dict]  # per row, everything the report needs

    @property
    def shifts_units(self) -> np.ndarray:
        """(n,) how far the refinement moved each target off its branch point."""
        if not len(self.targets):
            return np.zeros(0)
        d = np.asarray(self.targets, dtype=float) - np.asarray(self.raw_targets, dtype=float)
        return np.hypot(d[:, 0], d[:, 1])


def _to_units(problem: _ChainProblem, x_px: float, y_px: float) -> tuple[float, float]:
    """Crop px → the problem's template units (`_landmark_correspondence`'s map)."""
    return (
        (float(x_px) - problem.x_origin_px) / problem.unit_px,
        (problem.baseline_y_px - float(y_px)) / problem.unit_px,
    )


def _to_px(problem: _ChainProblem, u: float, v: float) -> tuple[float, float]:
    """…and back."""
    return (problem.x_origin_px + float(u) * problem.unit_px, problem.baseline_y_px - float(v) * problem.unit_px)


def _local_half_width_px(problem: _ChainProblem, x_px: float, y_px: float) -> float:
    """The measured ink HALF-width (px) at a crop pixel — the junction's scale.

    `chain._prepare_fields` propagates `case.width_map` (the EDT half-width of
    every ink pixel) over the whole crop by nearest ink, so the value is defined
    off the ink too. Read nearest-pixel rather than bilinear on purpose: it is a
    scale for thresholds, and interpolating it would suggest a precision the
    distance transform does not have.
    """
    field = np.asarray(problem.width_raw, dtype=float)
    if field.ndim != 2 or not field.size:
        return 0.0
    h, w = field.shape
    r = int(np.clip(round(float(y_px)), 0, h - 1))
    c = int(np.clip(round(float(x_px)), 0, w - 1))
    return float(field[r, c])


def _principal_direction(pts: np.ndarray) -> np.ndarray | None:
    """Unit total-least-squares direction of a pixel cloud, or None if it has none."""
    pts = np.asarray(pts, dtype=float).reshape(-1, 2)
    if len(pts) < 2:
        return None
    centred = pts - pts.mean(axis=0)
    vals, vecs = np.linalg.eigh(centred.T @ centred)
    if float(vals[-1]) <= 0.0:
        return None
    u = np.asarray(vecs[:, -1], dtype=float)
    n = float(np.hypot(u[0], u[1]))
    return u / n if n > 0.0 else None


_NEIGHBOUR_STEPS = tuple((dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0))
_ROOT2 = float(np.sqrt(2.0))


def _fork_pixels(m: np.ndarray) -> np.ndarray:
    """Skeleton pixels with ≥ 3 eight-neighbours — `skeleton_branch_points`' own test.

    Its clusters, not its centroids: the cluster is what a junction core has to
    swallow, and collapsing it first would only have to be undone here.
    """
    pad = np.pad(m, 1).astype(np.int8)
    h, w = m.shape
    nb = np.zeros((h, w), dtype=np.int8)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            if dy == 1 and dx == 1:
                continue
            nb += pad[dy : dy + h, dx : dx + w]
    return m & (nb >= 3)


def _arc_field(m: np.ndarray, sources: Sequence[tuple[int, int]], cap: float) -> np.ndarray:
    """Geodesic distance ALONG the skeleton from `sources`, capped at `cap`.

    Dijkstra over the 8-neighbourhood with √2 diagonals — the arc length the ink
    actually runs, not the straight line between two of its pixels. That
    difference is the whole point of the walk below: a limb that curls back past
    the seed is 20 px of ink away and 3 px of image away, and only the first of
    those two numbers says whether it is still the same limb.
    """
    arc = np.full(m.shape, np.inf)
    h, w = m.shape
    heap: list[tuple[float, int, int]] = []
    for r, c in sources:
        if m[r, c] and arc[r, c] > 0.0:
            arc[r, c] = 0.0
            heapq.heappush(heap, (0.0, r, c))
    while heap:
        dist, r, c = heapq.heappop(heap)
        if dist > arc[r, c] or dist > cap:
            continue
        for dy, dx in _NEIGHBOUR_STEPS:
            rr, cc = r + dy, c + dx
            if not (0 <= rr < h and 0 <= cc < w) or not m[rr, cc]:
                continue
            nd = dist + (1.0 if dy == 0 or dx == 0 else _ROOT2)
            if nd < arc[rr, cc]:
                arc[rr, cc] = nd
                heapq.heappush(heap, (nd, rr, cc))
    return arc


def _incident_branches(
    skel: np.ndarray,
    seed_px: tuple[float, float],
    *,
    radius_px: float,
    core_px: float,
    min_pixels: int,
    cluster_px: float = 0.0,
) -> list[dict] | None:
    """The junction's incident branches: `[{pixels, centroid, direction}, …]`.

    `None` — not `[]` — when the assigned point does not sit on this ink at all.
    The two are different statements and the caller reports them as different
    reasons: `None` says the correspondence points at nothing, `[]` says the walk
    found the ink and no way out of it.

    The walk follows the INK, not a disc of the image. A first version labelled
    the connected components of a Euclidean annulus around the seed, and on the
    real Sütterlin skeletons that fails in the one way that matters: two limbs of
    one junction reconnect INSIDE the annulus — around a tight loop, through the
    next junction, or simply by running parallel a few pixels apart — and become
    ONE component whose principal direction is a line through both. Measured on
    the 10 dev words at xh ≈ 30 px, that annulus is 6–9 px thick and its
    components reached 19–49 px: a 1-px skeleton arc crossing it can be 13 px at
    most, so the rest was limbs welded together. Every one of those welds became
    a refusal (`few_branches` where two limbs merged, `no_continuation_pair`
    where the merged direction pointed nowhere): 21 of 21 targets stayed raw.

    So: geodesic distance along the skeleton (`_arc_field`), limbs identified at
    the core boundary and carried outward by the arc-order predecessor, and a
    CONFLUENCE — a pixel two limbs both reach — blocked rather than assigned, so
    two limbs that meet again keep their identities instead of merging.

    `core_px` (the published junction-displacement bound) is still what cuts the
    limbs off the junction, but the core is now a geodesic ball and grows into a
    junction CLUSTER: `cluster_px` absorbs the fork pixels that lie within it.
    Thinning splits one shallow crossing into TWO Y-branch points bridged by a
    short segment, and a core that stops before the bridge sees the bridge as a
    third limb and the crossing's fourth limb not at all — which is a T-junction
    to every test downstream. Measured on the same words, that partner branch
    point sits 9.4–13.2 px away where the local stroke is 6.4–8.4 px wide, i.e.
    1.2–1.7 stroke widths; `FOLLOW_LANDMARK_CLUSTER_WIDTHS` is that bound.

    `direction` is the branch's OWN total-least-squares direction, oriented away
    from the seed — never the bearing `centroid − seed`, which is what a first
    version used and what the whole exercise forbids: the seed is a DISPLACED
    point (that is the premise), so a bearing read from it is skewed by exactly
    the error being corrected, and two limbs of one stroke can then miss each
    other's continuation by tens of degrees. The branch's own direction is
    intrinsic to the ink and carries no such bias.
    """
    m = np.asarray(skel, dtype=bool)
    if m.ndim != 2 or not m.any():
        return None
    h, w = m.shape
    cx, cy = float(seed_px[0]), float(seed_px[1])
    pad = int(np.ceil(radius_px + cluster_px)) + 2
    y0, y1 = max(0, int(np.floor(cy)) - pad), min(h, int(np.ceil(cy)) + pad + 1)
    x0, x1 = max(0, int(np.floor(cx)) - pad), min(w, int(np.ceil(cx)) + pad + 1)
    if y1 <= y0 or x1 <= x0:
        return None
    near = m[y0:y1, x0:x1]
    if not near.any():
        return None
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sy, sx = yy.astype(float), xx.astype(float)

    dist = np.where(near, np.hypot(sx - cx, sy - cy), np.inf)
    flat = int(np.argmin(dist))
    if not np.isfinite(dist.flat[flat]) or float(dist.flat[flat]) > core_px:
        # Nothing of the skeleton within the core: the assigned branch point does
        # not sit on this ink, so there is no junction here to walk.
        return None
    start = (int(flat // near.shape[1]), int(flat % near.shape[1]))

    # The walk's reach: the limbs, plus whatever the cluster absorbs on the way.
    arc = _arc_field(near, [start], radius_px + cluster_px + 1.0)
    forks = _fork_pixels(near)
    sources = [start]
    if cluster_px > 0.0:
        absorbed = forks & np.isfinite(arc) & (arc <= cluster_px)
        sources.extend((int(r), int(c)) for r, c in zip(*np.nonzero(absorbed), strict=True))
    core_arc = _arc_field(near, sources, core_px)
    core = np.isfinite(core_arc) & (core_arc <= core_px)
    if not core.any():
        return None

    structure = np.ones((3, 3), dtype=int)
    ring = np.zeros_like(near)
    for r, c in zip(*np.nonzero(core), strict=True):
        for dy, dx in _NEIGHBOUR_STEPS:
            rr, cc = r + dy, c + dx
            if 0 <= rr < near.shape[0] and 0 <= cc < near.shape[1] and near[rr, cc] and not core[rr, cc]:
                ring[rr, cc] = True
    ring_labels, n_ring = label_regions(ring, structure=structure)
    if n_ring == 0:
        return []

    limb = np.full(near.shape, -1, dtype=np.int32)
    limb[ring] = ring_labels[ring] - 1
    blocked = np.zeros_like(near)
    outside = np.isfinite(arc) & near & ~core
    for _d, r, c in sorted((float(arc[r, c]), int(r), int(c)) for r, c in zip(*np.nonzero(outside), strict=True)):
        if arc[r, c] > radius_px:
            continue
        if limb[r, c] != -1:
            continue
        owners: set[int] = set()
        best: tuple[float, int] | None = None
        for dy, dx in _NEIGHBOUR_STEPS:
            rr, cc = r + dy, c + dx
            if not (0 <= rr < near.shape[0] and 0 <= cc < near.shape[1]):
                continue
            if blocked[rr, cc] or limb[rr, cc] == -1 or arc[rr, cc] >= arc[r, c]:
                continue
            owners.add(int(limb[rr, cc]))
            if best is None or arc[rr, cc] < best[0]:
                best = (float(arc[rr, cc]), int(limb[rr, cc]))
        if best is None:
            continue
        if len(owners) > 1:
            # Two limbs of this junction have run back into each other. Neither
            # owns the confluence and neither grows through it — which is exactly
            # the weld the Euclidean annulus used to report as one branch.
            blocked[r, c] = True
            continue
        limb[r, c] = best[1]

    out: list[dict] = []
    for i in range(n_ring):
        sel = (limb == i) & ~blocked & np.isfinite(arc) & (arc <= radius_px)
        if int(np.count_nonzero(sel)) < min_pixels:
            continue
        pts = np.column_stack([sx[sel], sy[sel]])
        centroid = pts.mean(axis=0)
        away = centroid - np.array([cx, cy])
        norm = float(np.hypot(away[0], away[1]))
        if norm <= 0.0:
            continue
        direction = _principal_direction(pts)
        if direction is None:
            continue
        if float(np.dot(direction, away)) < 0.0:
            direction = -direction  # outward, so „anti-parallel" means „continues"
        out.append(
            {
                "pixels": pts,
                "centroid": centroid,
                "bearing": away / norm,
                "direction": direction,
                "arc_px": float(arc[sel].max()),
            }
        )
    return out


def _continuation_pairs(branches: Sequence[dict], *, tol_deg: float) -> list[tuple[int, int, float]]:
    """`[(i, j, deviation_deg), …]` — which branches are ONE stroke, best first.

    „Gute Fortsetzung": two branches continue through the junction when their
    outward directions are anti-parallel. The deviation from anti-parallel is the
    score, the assignment is GREEDY over it (best pair first, its two branches
    consumed) and `tol_deg` only refuses. That order matters: at a shallow
    crossing the wrong partner is only `crossing angle` degrees worse than the
    right one, so a tolerance can never separate them — the ranking can.
    """
    scored: list[tuple[float, int, int]] = []
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            cos = float(np.dot(branches[i]["direction"], branches[j]["direction"]))
            deviation = float(np.degrees(np.arccos(np.clip(-cos, -1.0, 1.0))))
            if deviation <= tol_deg:
                scored.append((deviation, i, j))
    used: set[int] = set()
    pairs: list[tuple[int, int, float]] = []
    for deviation, i, j in sorted(scored):
        if i in used or j in used:
            continue
        used.update((i, j))
        pairs.append((i, j, deviation))
    return pairs


def _intersect_lines(
    p1: np.ndarray, u1: np.ndarray, p2: np.ndarray, u2: np.ndarray, *, min_angle_deg: float
) -> np.ndarray | None:
    """Intersection of two parameterised lines, or None if it is ill-conditioned.

    `u1`/`u2` are unit vectors, so their cross product IS the sine of the angle
    between the lines and the conditioning test is the angle test. Below
    `min_angle_deg` the intersection slides freely along the shared direction —
    the same refusal, for the same reason, that `landmarks.LANDMARK_MIN_ANGLE_DEG`
    applies to a polyline's self-crossing.
    """
    denominator = float(u1[0] * u2[1] - u1[1] * u2[0])
    if abs(denominator) < np.sin(np.radians(min_angle_deg)):
        return None
    q = np.asarray(p2, dtype=float) - np.asarray(p1, dtype=float)
    t = float(q[0] * u2[1] - q[1] * u2[0]) / denominator
    return np.asarray(p1, dtype=float) + t * np.asarray(u1, dtype=float)


def _uncertainty_weights(sigmas: np.ndarray) -> np.ndarray:
    """Relative `1/sigma^2` weights over the targets, normalised to MEAN 1.

    The chain's landmark energy is `sum(r^2) / n` — a MEAN of squared residuals
    in template units. Weighting it as `sum(w·r^2) / n` with `mean(w) = 1` keeps
    that scale: a set of equally certain targets reproduces the unweighted
    energy, so a calibrated weight does not silently change meaning when the
    uncertainties happen to be uniform, and `e_landmark` stays comparable across
    words and across the two target modes.
    """
    s = np.asarray(sigmas, dtype=float).reshape(-1)
    if not len(s):
        return np.zeros(0)
    inverse = np.zeros_like(s)
    good = s > 0.0
    inverse[good] = 1.0 / (s[good] ** 2)
    total = float(inverse.sum())
    if total <= 0.0:
        return np.ones_like(s)
    return inverse * (len(s) / total)


def _sigma_units(problem: _ChainProblem, x_px: float, y_px: float, *, floor_px: float) -> tuple[float, float]:
    """`(half_width_px, sigma_units)` at a branch point — the target's uncertainty.

    σ is the local HALF-width, floored: the published displacement bound is the
    full local stroke width, which this treats as a ~2σ statement rather than as
    a 1σ one, and the floor keeps a hairline from claiming sub-pixel certainty
    about a point that is itself a pixel-grid centroid.
    """
    half_width_px = _local_half_width_px(problem, x_px, y_px)
    return half_width_px, max(half_width_px, float(floor_px)) / float(problem.unit_px)


def raw_landmark_targets(problem: _ChainProblem, *, sigma_floor_px: float = FOLLOW_LANDMARK_SIGMA_FLOOR_PX):
    """The chain's own branch points as a targeting — the A/B's control arm.

    Nothing is refined and every weight is 1, so applying this is a no-op; it
    exists so the control arm is expressed in the same object as the treatment
    and can be measured (`landmark_energy`) by the same code.
    """
    targets = np.asarray(problem.landmark_targets, dtype=float).reshape(-1, 2)
    sigmas = np.zeros(len(targets))
    entries: list[dict] = []
    for row, (u, v) in enumerate(targets):
        x_px, y_px = _to_px(problem, u, v)
        half_width_px, sigmas[row] = _sigma_units(problem, x_px, y_px, floor_px=sigma_floor_px)
        entries.append(
            {
                "row": row,
                "reason": "raw",
                "half_width_px": round(half_width_px, 3),
                "sigma_units": round(float(sigmas[row]), 4),
                "shift_units": 0.0,
            }
        )
    return LandmarkTargeting(
        mode="raw",
        targets=targets.copy(),
        raw_targets=targets.copy(),
        sigmas=sigmas,
        weights=np.ones(len(targets)),
        reasons=["raw"] * len(targets),
        entries=entries,
    )


def extrapolated_targets(
    problem: _ChainProblem,
    *,
    weighted: bool = True,
    window_units: float = FOLLOW_LANDMARK_WINDOW_UNITS,
    core_widths: float = FOLLOW_LANDMARK_CORE_WIDTHS,
    core_min_px: float = FOLLOW_LANDMARK_CORE_MIN_PX,
    min_branch_px: float = FOLLOW_LANDMARK_MIN_BRANCH_PX,
    min_branch_pixels: int = FOLLOW_LANDMARK_MIN_BRANCH_PIXELS,
    cluster_widths: float = FOLLOW_LANDMARK_CLUSTER_WIDTHS,
    continuation_tol_deg: float = FOLLOW_LANDMARK_CONTINUATION_TOL_DEG,
    min_angle_deg: float = LANDMARK_MIN_ANGLE_DEG,
    max_shift_widths: float = FOLLOW_LANDMARK_MAX_SHIFT_WIDTHS,
    sigma_floor_px: float = FOLLOW_LANDMARK_SIGMA_FLOOR_PX,
) -> LandmarkTargeting:
    """Refine every landmark target to the EXTRAPOLATED crossing of its branches.

    For each kept correspondence of `problem` (one row of `landmark_op`, aimed at
    a skeleton branch point):

    1. read the local ink half-width at the branch point (`_local_half_width_px`)
       — the junction's own scale, from which the core exclusion, the refusal
       radius and the uncertainty all follow;
    2. walk the skeleton around it and cut out the incident branches
       (`_incident_branches`), dropping everything inside the junction-distorted
       core;
    3. pair the branches that continue through the junction
       (`_continuation_pairs`), fit ONE straight line per pair through both its
       branches, and intersect the two best pairs' lines (`_intersect_lines`);
    4. accept that intersection as the target when it lies within one stroke
       width of the branch point.

    Every step REFUSES rather than guesses, and a refusal keeps the raw branch
    point with its reason recorded. The reasons separate what the ink cannot
    support from what the walk failed to find, because only the second kind is
    ever worth fixing:

    * BY DESIGN, a property of the ink at that point — `touch_point` (exactly two
      limbs: a stroke passing through, a retrace touch, a corner), `t_junction`
      (exactly three limbs, so at most one continuation pair can exist at all),
      `ill_conditioned` (the two lines are near-parallel and the intersection
      slides).
    * A REFUSAL of this refinement — `no_junction` (no skeleton, or the branch
      point does not sit on ink), `few_branches` (fewer than two limbs: the walk
      found the ink and no way out of it), `no_continuation_pair` (four or more
      limbs and still no second pair), `far_from_branch` (the extrapolation
      landed beyond the published displacement bound, so it is a different
      junction, not a correction).

    A raw target is not a failure of the term, only of the refinement; the
    correspondence itself was refused earlier, by the frozen detector, and is not
    reconsidered here.

    Pure measurement: reads `problem`, writes nothing (`apply_landmark_targets`
    is the only thing that touches a problem).
    """
    raw = np.asarray(problem.landmark_targets, dtype=float).reshape(-1, 2)
    skel = problem.skel
    targets = raw.copy()
    sigmas = np.zeros(len(raw))
    reasons: list[str] = []
    entries: list[dict] = []
    for row, (u, v) in enumerate(raw):
        x_px, y_px = _to_px(problem, u, v)
        half_width_px, sigmas[row] = _sigma_units(problem, x_px, y_px, floor_px=sigma_floor_px)
        core_px = max(core_widths * half_width_px, core_min_px)
        cluster_px = max(cluster_widths * half_width_px, core_px)
        # The reach has to clear the CLUSTER, not just the base core: once the
        # partner Y of a split crossing is absorbed, the limbs start beyond it,
        # and a radius fixed at the window would leave nothing outside to fit.
        radius_px = max(window_units * float(problem.unit_px), cluster_px + core_px + min_branch_px)
        branches = (
            None
            if skel is None
            else _incident_branches(
                skel,
                (x_px, y_px),
                radius_px=radius_px,
                core_px=core_px,
                min_pixels=min_branch_pixels,
                cluster_px=cluster_px,
            )
        )
        entry = {
            "row": row,
            "half_width_px": round(half_width_px, 3),
            "sigma_units": round(float(sigmas[row]), 4),
            "core_px": round(core_px, 2),
            "cluster_px": round(cluster_px, 2),
            "radius_px": round(radius_px, 2),
            "n_branches": 0 if branches is None else len(branches),
        }
        reason, refined, cross_angle = _refine_one(
            branches,
            continuation_tol_deg=continuation_tol_deg,
            min_angle_deg=min_angle_deg,
            max_shift_px=max(max_shift_widths * half_width_px, sigma_floor_px),
            branch_px=(x_px, y_px),
        )
        entry["cross_angle_deg"] = None if cross_angle is None else round(cross_angle, 2)
        if refined is not None:
            targets[row] = _to_units(problem, float(refined[0]), float(refined[1]))
        entry["reason"] = reason
        entry["shift_units"] = round(float(np.hypot(*(targets[row] - raw[row]))), 4)
        reasons.append(reason)
        entries.append(entry)
    weights = _uncertainty_weights(sigmas) if weighted else np.ones(len(raw))
    for entry, weight in zip(entries, weights, strict=True):
        entry["weight"] = round(float(weight), 4)
    return LandmarkTargeting(
        mode="extrapolated" if weighted else "extrapolated_uniform",
        targets=targets,
        raw_targets=raw.copy(),
        sigmas=sigmas,
        weights=weights,
        reasons=reasons,
        entries=entries,
    )


def _refine_one(
    branches: Sequence[dict] | None,
    *,
    continuation_tol_deg: float,
    min_angle_deg: float,
    max_shift_px: float,
    branch_px: tuple[float, float],
) -> tuple[str, np.ndarray | None, float | None]:
    """`(reason, refined point | None, crossing angle)` for ONE junction."""
    if branches is None:
        # No skeleton was supplied, or the assigned branch point does not sit on
        # ink at all — a different statement from „this junction has too few
        # branches", and reported as one.
        return "no_junction", None, None
    if len(branches) < 2:
        # A dead end: the walk found the ink but no way out of the junction —
        # the core swallowed every limb, or the ink simply stops there. That is
        # a failure of the WALK, not a junction class, and it keeps the bare name.
        return "few_branches", None, None
    if len(branches) == 2:
        # Two branches are a stroke passing through, not a crossing — the class
        # a retrace touch point and a sharp corner both fall in. Named rather
        # than folded into `few_branches`: this one is a property of the ink, and
        # no walk, window or tolerance will ever make it refinable. On the dev
        # words it is 5 of 21 targets, all with the two limbs 39–48° apart.
        return "touch_point", None, None
    if len(branches) == 3:
        # Three limbs make at most ONE continuation pair — `_continuation_pairs`
        # consumes two branches per pair — so a second line to intersect cannot
        # exist however the pairing is scored. A real T-junction, refused by
        # construction and counted as such, which is what separates it from a
        # four-limb crossing whose second pair the TOLERANCE refused.
        return "t_junction", None, None
    pairs = _continuation_pairs(branches, tol_deg=continuation_tol_deg)
    if len(pairs) < 2:
        return "no_continuation_pair", None, None
    lines: list[tuple[np.ndarray, np.ndarray]] = []
    for i, j, _deviation in pairs[:2]:
        pts = np.vstack([branches[i]["pixels"], branches[j]["pixels"]])
        direction = _principal_direction(pts)
        if direction is None:
            return "ill_conditioned", None, None  # a degenerate cloud has no line
        lines.append((pts.mean(axis=0), direction))
    (p1, u1), (p2, u2) = lines
    cross = abs(float(u1[0] * u2[1] - u1[1] * u2[0]))
    angle = float(np.degrees(np.arcsin(min(1.0, cross))))
    refined = _intersect_lines(p1, u1, p2, u2, min_angle_deg=min_angle_deg)
    if refined is None:
        return "ill_conditioned", None, angle
    if float(np.hypot(refined[0] - branch_px[0], refined[1] - branch_px[1])) > max_shift_px:
        return "far_from_branch", None, angle
    return "ok", refined, angle


def classed_targets(problem: _ChainProblem, **kwargs) -> LandmarkTargeting:
    """Extrapolated targets with the by-design non-crossings classed out — arm ⑥b.

    The extrapolation itself is unchanged; afterwards every row whose refinement
    reason is in `LANDMARK_NONCROSSING_REASONS` gets weight 0. Through the
    whitening in `apply_landmark_targets` a zero weight scales the operator row
    AND the target to zero, so the row pulls nothing and costs nothing — the
    correspondence is removed without touching `chain.py` or the frozen
    detector. The surviving rows' 1/σ² weights are re-normalised to mean 1 over
    the KEPT rows, so a kept correspondence weighs the same as it would in
    `extrapolated` mode with only crossings present.
    """
    base = extrapolated_targets(problem, weighted=True, **kwargs)
    dropped = np.array([reason in LANDMARK_NONCROSSING_REASONS for reason in base.reasons], dtype=bool)
    weights = np.asarray(base.weights, dtype=float).copy()
    weights[dropped] = 0.0
    kept = ~dropped
    kept_mean = float(weights[kept].mean()) if bool(kept.any()) else 0.0
    if kept_mean > 0.0:
        weights[kept] = weights[kept] / kept_mean
    entries: list[dict] = []
    for entry, out, weight in zip(base.entries, dropped, weights, strict=True):
        entry = dict(entry)
        entry["classed_out"] = bool(out)
        entry["weight"] = round(float(weight), 4)
        entries.append(entry)
    return LandmarkTargeting(
        mode="extrapolated_classed",
        targets=base.targets,
        raw_targets=base.raw_targets,
        sigmas=base.sigmas,
        weights=weights,
        reasons=list(base.reasons),
        entries=entries,
    )


def landmark_targeting(problem: _ChainProblem, mode: str, **kwargs) -> LandmarkTargeting:
    """The targeting one `FollowWeights.landmark_targets` mode asks for."""
    if mode == "raw":
        return raw_landmark_targets(problem)
    if mode in ("extrapolated", "extrapolated_uniform"):
        return extrapolated_targets(problem, weighted=(mode == "extrapolated"), **kwargs)
    if mode == "extrapolated_classed":
        return classed_targets(problem, **kwargs)
    raise ValueError(f"unknown landmark target mode {mode!r}; known: {', '.join(LANDMARK_TARGET_MODES)}")


def apply_landmark_targets(problem: _ChainProblem, targeting: LandmarkTargeting) -> _ChainProblem:
    """Aim the chain's landmark term at `targeting` — by PRE-WHITENING its rows.

    The chain prices `e_landmark = sum_i |P_i − T_i|² / n` with `P_i` a fixed
    linear map of four plan anchors. Per-target uncertainties enter it without a
    new term and without touching `chain.py`: scale row `i` of the operator AND
    target `i` by `sqrt(w_i)` and the residual becomes `sqrt(w_i)·(P_i − T_i)`,
    so the energy is `sum_i w_i·|P_i − T_i|² / n` and the gradient
    `op^T·r` folds the same weights through the exact same chain rule. It is the
    standard whitening transform, and nothing about the operator's structure
    changes: the row still touches exactly its four anchors.

    The price is that `problem.landmark_op` and `problem.landmark_targets` are no
    longer readable as „the fitted crossing" and „the ink point" once this has
    run — divide row `i` by `sqrt(weights[i])`, or (better) read the unwhitened
    geometry off the `LandmarkTargeting` itself, which is why it carries both the
    refined and the raw targets. `landmarklab.fitted_crossing` is unaffected: it
    rebuilds `P` from the frozen chord indices in `landmark_report`, which this
    only ANNOTATES (`_annotate_report`) and never rescales.

    Mutating the problem in place mirrors `apply_retrace_guard`: both are
    follower-side adjustments of a chain-built problem, applied once, right after
    the rebuild, before the solve.
    """
    if not len(targeting.targets) or not problem.landmark_op.shape[0]:
        return problem
    if len(targeting.targets) != problem.landmark_op.shape[0]:
        # A targeting built from a DIFFERENT (or outdated) problem would
        # broadcast wrongly or crash unreadably — refuse with the counts.
        raise ValueError(
            f"targeting carries {len(targeting.targets)} targets but the problem's landmark "
            f"operator has {problem.landmark_op.shape[0]} rows — build the targeting from THIS problem"
        )
    if targeting.mode != "raw":
        scales = np.sqrt(np.asarray(targeting.weights, dtype=float)).reshape(-1, 1)
        problem.landmark_op = problem.landmark_op * scales
        problem.landmark_targets = np.asarray(targeting.targets, dtype=float) * scales
    _annotate_report(problem, targeting)
    return problem


def _annotate_report(problem: _ChainProblem, targeting: LandmarkTargeting) -> None:
    """Write the refinement's provenance next to the correspondence it refines.

    `landmark_report` already carries one entry per DETECTED landmark with the
    reason it was kept or dropped — the arm's mandatory cost column. The
    refinement's own reason belongs beside it rather than in a second list that
    has to be re-joined later, so the kept entries gain `target_mode`,
    `refine_reason`, `sigma_units`, `target_weight` and `refine_shift_units`.
    Additive keys only; nothing existing is overwritten.
    """
    kept = [entry for entry in problem.landmark_report if entry.get("reason") == "ok"]
    if len(kept) != len(targeting.entries):
        # A silent partial annotation would hide a report/targeting mismatch
        # and mislead every downstream summary — refuse with the counts.
        raise ValueError(
            f"landmark report keeps {len(kept)} correspondences but the targeting carries "
            f"{len(targeting.entries)} entries — the two were built from different problems"
        )
    for entry, refined in zip(kept, targeting.entries, strict=True):
        entry["target_mode"] = targeting.mode
        entry["refine_reason"] = refined["reason"]
        entry["sigma_units"] = refined["sigma_units"]
        entry["target_weight"] = refined.get("weight", 1.0)
        entry["refine_shift_units"] = refined["shift_units"]
        if "classed_out" in refined:
            entry["classed_out"] = refined["classed_out"]


def landmark_meta(problem: _ChainProblem, *, mode: str) -> dict:
    """What one solve has to state about its landmark term.

    Counts on both sides of the refusal — the correspondences the frozen detector
    dropped (`drops`, with their reasons) and the refinements that fell back to a
    raw branch point (`refined`) — because a term that quietly aims at nothing is
    inert for a reason that must be readable off the run rather than
    reconstructed afterwards (§13a's rule for the correspondence, applied to the
    target too).
    """
    report = problem.landmark_report
    kept = [entry for entry in report if entry.get("reason") == "ok"]
    drops: dict[str, int] = {}
    refined: dict[str, int] = {}
    for entry in report:
        if entry.get("reason") != "ok":
            drops[str(entry.get("reason"))] = drops.get(str(entry.get("reason")), 0) + 1
    for entry in kept:
        if "refine_reason" in entry:
            refined[str(entry["refine_reason"])] = refined.get(str(entry["refine_reason"]), 0) + 1
    shifts = [float(entry["refine_shift_units"]) for entry in kept if "refine_shift_units" in entry]
    sigmas = [float(entry["sigma_units"]) for entry in kept if "sigma_units" in entry]
    return {
        "mode": mode,
        "applied": bool(refined),
        "n_detected": len(report),
        "n_targets": int(problem.landmark_op.shape[0]),
        "classed_out": sum(1 for entry in kept if entry.get("classed_out")),
        "drops": drops,
        "refined": refined,
        "shift_units_median": round(float(np.median(shifts)), 4) if shifts else None,
        "sigma_units_median": round(float(np.median(sigmas)), 4) if sigmas else None,
    }


def _merge_landmark_meta(metas: Sequence[dict], *, mode: str) -> dict:
    """The word's landmark block: the runs' blocks added up, reasons pooled."""
    merged = {
        "mode": mode,
        "applied": any(m.get("applied") for m in metas),
        "n_detected": sum(int(m.get("n_detected", 0)) for m in metas),
        "n_targets": sum(int(m.get("n_targets", 0)) for m in metas),
        "classed_out": sum(int(m.get("classed_out", 0)) for m in metas),
        "drops": {},
        "refined": {},
    }
    for meta in metas:
        for field_name in ("drops", "refined"):
            for reason, count in (meta.get(field_name) or {}).items():
                merged[field_name][reason] = merged[field_name].get(reason, 0) + int(count)
    shifts = [m["shift_units_median"] for m in metas if m.get("shift_units_median") is not None]
    merged["shift_units_median"] = round(float(np.median(shifts)), 4) if shifts else None
    return merged


def landmark_energy(problem: _ChainProblem, params: np.ndarray, targeting: LandmarkTargeting) -> float:
    """`mean_i w_i·|P_i(params) − T_i|²` — the term's energy for a targeting.

    The same formula `chain._ChainProblem._evaluate` prices, evaluated for a
    targeting the problem does NOT carry, so the calibration hook can read what a
    refined target WOULD cost without rebuilding or re-solving anything.

    It reads `landmark_op` as the unwhitened map, i.e. it must run on a problem
    `apply_landmark_targets` has not touched — which is exactly the calibration
    path's situation (it solves at weight 0, where nothing is ever applied).
    """
    if not problem.landmark_op.shape[0] or not len(targeting.targets):
        return 0.0
    residual = (problem.landmark_op @ problem.plan_anchors(np.asarray(params, dtype=float))) - targeting.targets
    weights = np.asarray(targeting.weights, dtype=float).reshape(-1, 1)
    return float(np.sum(weights * residual**2) / problem.landmark_op.shape[0])


def landmark_calibration(
    problem: _ChainProblem,
    params: np.ndarray,
    targeting: LandmarkTargeting,
    *,
    multipliers: Sequence[float] = LANDMARK_CALIBRATION_MULTIPLIERS,
) -> dict:
    """Read the term's SCALE at a solved optimum — never pick a weight by analogy.

    `landmarklab.calibration`'s reading, one level up: at the optimum the ratio
    `e_geo / e_landmark` is the weight at which the correspondence weighs as much
    as the geometry term (the „parity weight"), and a rung of the ladder is a
    fraction of it. The would-be energy of a rung is reported next to it, so the
    arm's rungs come out of measured ratios instead of out of a habit — §11c is
    the standing warning this obeys: a ladder chosen by analogy to another path's
    constant put a term at 0.2 % of the objective's scale and measured nothing.

    `share_of_e_geo == multiplier` holds by construction; it is printed as an
    arithmetic check, not as a finding. The informative numbers are
    `parity_weight` (what a rung means as an absolute weight) and `e_landmark`
    (how far the structure actually sits from the ink at this optimum).
    """
    terms = problem.energy_terms(np.asarray(params, dtype=float))
    e_geo = float(terms["e_geo"])
    e_landmark = landmark_energy(problem, params, targeting)
    parity = (e_geo / e_landmark) if e_landmark > 0.0 else None
    candidates = [
        {
            "multiplier": float(m),
            "weight": None if parity is None else float(m) * parity,
            "would_be_energy": None if parity is None else float(m) * parity * e_landmark,
            "share_of_e_geo": None if parity is None or e_geo <= 0.0 else float(m) * parity * e_landmark / e_geo,
        }
        for m in multipliers
    ]
    reasons: dict[str, int] = {}
    for reason in targeting.reasons:
        reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "mode": targeting.mode,
        "n_landmarks": int(problem.landmark_op.shape[0]),
        "n_detected": len(problem.landmark_report),
        "e_geo": e_geo,
        "e_landmark": e_landmark,
        "parity_weight": parity,
        "candidates": candidates,
        "reasons": reasons,
        "sigma_units_median": round(float(np.median(targeting.sigmas)), 4) if len(targeting.sigmas) else None,
        "shift_units_median": round(float(np.median(targeting.shifts_units)), 4) if len(targeting.targets) else None,
    }


# ---------------------------------------------------- the structure guard (⑨)


def structure_class_counts(strokes_units: list[list[list[float]]]) -> dict[str, int]:
    """The v2.1 structure classes of one assembled trace — the BENCH's own count.

    Counted on the word-record strokes in trace units (1 unit = x-height),
    exactly the frame the bench maps candidates through, by the very counters
    the §14 report grades with (`tools.tracebench.counters`) — the guard and
    the ruler can never disagree about what a crossing or a touch is.
    """
    strokes = [np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes_units]
    strokes = [s for s in strokes if len(s) >= 2]
    if not strokes:
        return {"cross": 0, "retrace": 0, "touch": 0, "overlap": 0}
    zones = structure_zones(strokes)
    return {
        "cross": int(len(crossing_points(strokes))),
        "retrace": int(len(zones.retrace_mids)),
        "touch": int(len(zones.touch_mids)),
        "overlap": int(len(zones.overlap_mids)),
    }


def _exceeds_budget(counts: dict[str, int], budget: dict[str, int]) -> bool:
    """True when any structure class grew beyond the initialisation's count."""
    return any(int(counts.get(key, 0)) > int(budget.get(key, 0)) for key in budget)


def _breaks_budget(
    counts: dict[str, int], budget: dict[str, int], *, two_sided: bool, soll: dict[str, int] | None = None
) -> bool:
    """The guard's acceptance test. One-sided caps inventions; two-sided also
    rejects LOSSES — the K0 invariant makes the initialisation's structure
    count binding in both directions (the aug16 full-set run measured the
    ink pull collapsing small loops on Sporn/einer/er-3 unpunished). With
    `soll` (the aug19 soll-aware form) every class must lie in the closed
    interval between budget and soll: movement only toward the soll, never
    past it, never away — the interval collapses to two-sided equality
    wherever the two counts agree."""
    if soll is not None:
        for key in budget:
            b, n = int(budget.get(key, 0)), int(counts.get(key, 0))
            s = int(soll.get(key, b))
            if not (min(b, s) <= n <= max(b, s)):
                return True
        return False
    if two_sided:
        return any(int(counts.get(key, 0)) != int(budget.get(key, 0)) for key in budget)
    return _exceeds_budget(counts, budget)


def structure_class_points(strokes_units: list[list[list[float]]]) -> dict[str, np.ndarray]:
    """The v2.1 structure classes of one assembled trace, as POINTS per class.

    The positional twin of `structure_class_counts` — same strokes, same
    counters (`crossing_points` returns the crossing points themselves, the
    zone classes their mids), so `len(points[k]) == counts[k]` always. The
    K0-Z zonal rejection localises budget violations with these.
    """
    strokes = [np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes_units]
    strokes = [s for s in strokes if len(s) >= 2]
    empty = np.zeros((0, 2))
    if not strokes:
        return {"cross": empty, "retrace": empty, "touch": empty, "overlap": empty}
    zones = structure_zones(strokes)
    return {
        "cross": np.asarray(crossing_points(strokes), dtype=float).reshape(-1, 2),
        "retrace": np.asarray(zones.retrace_mids, dtype=float).reshape(-1, 2),
        "touch": np.asarray(zones.touch_mids, dtype=float).reshape(-1, 2),
        "overlap": np.asarray(zones.overlap_mids, dtype=float).reshape(-1, 2),
    }


def _class_interval(key: str, budget: dict[str, int], soll: dict[str, int] | None, two_sided: bool) -> tuple[int, int]:
    """The per-class acceptance interval — exactly `_breaks_budget`'s rule."""
    b = int(budget.get(key, 0))
    if soll is not None:
        s = int(soll.get(key, b))
        return min(b, s), max(b, s)
    if two_sided:
        return b, b
    return 0, b


def _unmatched_points(a: np.ndarray, b: np.ndarray, radius: float) -> tuple[np.ndarray, np.ndarray]:
    """One-to-one nearest-first matching; returns (a-unmatched, b-unmatched)."""
    a = np.asarray(a, dtype=float).reshape(-1, 2)
    b = np.asarray(b, dtype=float).reshape(-1, 2)
    if not len(a) or not len(b):
        return a, b
    d = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)
    order = np.dstack(np.unravel_index(np.argsort(d, axis=None), d.shape))[0]
    used_a: set[int] = set()
    used_b: set[int] = set()
    for ai, bi in order:
        if d[ai, bi] > radius:
            break
        if int(ai) in used_a or int(bi) in used_b:
            continue
        used_a.add(int(ai))
        used_b.add(int(bi))
    return a[[i for i in range(len(a)) if i not in used_a]], b[[i for i in range(len(b)) if i not in used_b]]


# The K0-Z site matcher pairs candidate and previous-geometry events of one
# class before naming violations; the ruler's own crossing matcher radius.
ZONE_SITE_MATCH_RADIUS_UNITS = 0.55


def _zone_violation_sites(
    cand_points: dict[str, np.ndarray],
    prev_points: dict[str, np.ndarray],
    budget: dict[str, int],
    soll: dict[str, int] | None,
    two_sided: bool,
) -> np.ndarray:
    """K0-Z (§14 `aug20`): the trace-unit positions of the budget violations.

    Per violated class: candidate and previous-geometry events are matched
    one-to-one at the ruler radius; an over-count names the UNMATCHED
    candidate events (the inventions), an under-count the unmatched previous
    events (the losses). Classes inside their interval contribute nothing.
    """
    sites: list[np.ndarray] = []
    for key in budget:
        lo, hi = _class_interval(key, budget, soll, two_sided)
        cand = cand_points.get(key, np.zeros((0, 2)))
        n = len(cand)
        if lo <= n <= hi:
            continue
        extra_cand, lost_prev = _unmatched_points(
            cand, prev_points.get(key, np.zeros((0, 2))), ZONE_SITE_MATCH_RADIUS_UNITS
        )
        sites.append(extra_cand if n > hi else lost_prev)
    if not sites:
        return np.zeros((0, 2))
    return np.vstack(sites)


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
        # K-E: the claimed mark stacks ride into every re-linearised round —
        # the (seg, start) keys survive `respec_from_solution` verbatim, so
        # the rebuilt problem re-derives the same sample classes. Empty = off.
        "mark_fields": problem.mark_fields,
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

    The landmark targets are refined here too (arm ⑥) — but ONLY at a positive
    landmark weight: at 0 the term contributes `+ 0.0` to `f` and no gradient at
    all, so refining its targets could not move a single anchor and would buy
    nothing but a changed number in a report and a skeleton walk per landmark.
    Skipping it is what keeps every arm at `landmark = 0` byte-identical to a
    follower built before this existed.
    """
    if weights.landmark_targets not in LANDMARK_TARGET_MODES:
        raise ValueError(
            f"unknown landmark target mode {weights.landmark_targets!r}; known: {', '.join(LANDMARK_TARGET_MODES)}"
        )
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
    if weights.landmark > 0.0 and weights.landmark_targets != "raw":
        apply_landmark_targets(rebuilt, landmark_targeting(rebuilt, weights.landmark_targets))
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
        "n_landmarks": int(problem.landmark_op.shape[0]),
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

    def _assembled_counts(problem_: _ChainProblem, params_: np.ndarray) -> dict[str, int]:
        px_, py_ = problem_.to_pixels(params_)
        strokes_ = assemble_word_strokes(
            _stroke_polylines_px(problem_, px_, py_),
            traced_slots=set(fit.slots),
            xh=xh,
            registration=registration,
            restart_slots=restart_slots,
        )
        return structure_class_counts(strokes_)

    guard_budget: dict[str, int] | None = None
    guard_soll: dict[str, int] | None = None
    if weights.structure_guard:
        init_strokes = assemble_word_strokes(
            fit.stroke_polylines_px,
            traced_slots=set(fit.slots),
            xh=xh,
            registration=registration,
            restart_slots=restart_slots,
        )
        guard_budget = structure_class_counts(init_strokes)
        if weights.structure_guard_soll:
            if weights.soll_source not in ("init", "composition"):
                raise ValueError(f"unknown soll_source {weights.soll_source!r}; known: init, composition")
            if weights.soll_source == "composition":
                # K0-S (§14 `aug21`): the soll from the CANONICAL composition,
                # run-restricted, through the builder the metric's ductus_soll
                # shares — one pipeline, so guard and ruler cannot diverge (the
                # daß find: the init reading counted its own flattened sliver).
                guard_soll = structure_class_counts(composition_strokes(result.composed["items"], slots=set(fit.slots)))
            else:
                # aug19, rescue path (c): the soll is the composed INIT geometry
                # — the trace at x0 = 0 through the very assembler and counters
                # the budget and every round go through.
                guard_soll = _assembled_counts(fit.problem, np.zeros_like(fit.params))

    for index in range(1, int(weights.rounds) + 1):
        prev_problem, prev_params = problem, params
        problem, mask = build_follow_problem(prev_problem, prev_params, weights)
        params, record = _solve_round(problem, weights, index, mask)
        if guard_budget is not None:
            # Arm ⑨ (§14 `aug16`): the acceptance rule. A violating round is
            # re-solved from the SAME previous geometry with halved travel
            # bounds; past the retry budget the previous geometry stands.
            two_sided = bool(weights.structure_guard_two_sided)
            counts = _assembled_counts(problem, params)
            retries = 0
            round_weights = weights
            while (
                _breaks_budget(counts, guard_budget, two_sided=two_sided, soll=guard_soll)
                and retries < STRUCTURE_GUARD_MAX_RETRIES
            ):
                retries += 1
                round_weights = replace(
                    round_weights,
                    max_delta=round_weights.max_delta / 2.0,
                    connector_max_delta=round_weights.connector_max_delta / 2.0,
                )
                problem, mask = build_follow_problem(prev_problem, prev_params, round_weights)
                params, record = _solve_round(problem, round_weights, index, mask)
                counts = _assembled_counts(problem, params)
            zone_units = float(weights.structure_guard_zone_units or 0.0)
            if zone_units > 0.0 and _breaks_budget(counts, guard_budget, two_sided=two_sided, soll=guard_soll):
                # K0-Z (§14 `aug20`): zonal rejection. Localise the violations
                # on the FAILING candidate against the round's own previous
                # geometry (x0 = 0 through the same assembler and counters),
                # pin the free anchors around them to that geometry, and give
                # the round ONE re-solve with its ORIGINAL bounds elsewhere —
                # a bundled repair keeps its good half instead of dying whole.
                def _assembled_points(problem_: _ChainProblem, params_: np.ndarray) -> dict[str, np.ndarray]:
                    px_, py_ = problem_.to_pixels(params_)
                    strokes_ = assemble_word_strokes(
                        _stroke_polylines_px(problem_, px_, py_),
                        traced_slots=set(fit.slots),
                        xh=xh,
                        registration=registration,
                        restart_slots=restart_slots,
                    )
                    return structure_class_points(strokes_)

                sites_units = _zone_violation_sites(
                    _assembled_points(problem, params),
                    _assembled_points(problem, np.zeros_like(params)),
                    guard_budget,
                    guard_soll,
                    two_sided,
                )
                pinned: list[int] = []
                if len(sites_units) and len(problem.anchors_free):
                    # Sites are trace units; anchors live in the problem frame —
                    # compare in crop px (the assembler's own inverse transform).
                    sx = sites_units[:, 0] * xh + float(registration.get("tx", 0.0))
                    sy = (
                        float(registration["baseline_row"])
                        + float(registration.get("ty", 0.0))
                        - sites_units[:, 1] * xh
                    )
                    problem_z, mask_z = build_follow_problem(prev_problem, prev_params, weights)
                    ax = problem_z.x_origin_px + problem_z.anchors_free[:, 0] * problem_z.unit_px
                    ay = problem_z.baseline_y_px - problem_z.anchors_free[:, 1] * problem_z.unit_px
                    radius_px = zone_units * problem_z.unit_px
                    d = np.hypot(ax[:, None] - sx[None, :], ay[:, None] - sy[None, :])
                    pinned = [int(i) for i in np.flatnonzero(d.min(axis=1) <= radius_px)]
                    off = 2 + 2 * problem_z.n_blocks
                    for ai in pinned:
                        problem_z.bounds[off + 2 * ai] = (0.0, 0.0)
                        problem_z.bounds[off + 2 * ai + 1] = (0.0, 0.0)
                    if pinned:
                        params_z, record_z = _solve_round(problem_z, weights, index, mask_z)
                        counts_z = _assembled_counts(problem_z, params_z)
                        if not _breaks_budget(counts_z, guard_budget, two_sided=two_sided, soll=guard_soll):
                            problem, params, record, counts = problem_z, params_z, record_z, counts_z
                record["structure_zonal"] = {
                    "sites": int(len(sites_units)),
                    "pinned": int(len(pinned)),
                    "accepted": not _breaks_budget(counts, guard_budget, two_sided=two_sided, soll=guard_soll),
                }
            record["structure_budget"] = dict(guard_budget)
            if guard_soll is not None:
                record["structure_soll"] = dict(guard_soll)
            record["structure_counts"] = dict(counts)
            record["structure_retries"] = retries
            record["structure_rejected"] = _breaks_budget(counts, guard_budget, two_sided=two_sided, soll=guard_soll)
            if record["structure_rejected"]:
                rounds.append(record)
                problem, params = prev_problem, prev_params
                stopped_early = True
                break
            if weights.structure_guard_ratchet:
                # K0-Z-R: the accepted counts become the budget — the soll
                # interval only ever tightens across rounds.
                guard_budget = dict(counts)
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
            "landmark": landmark_meta(problem, mode=weights.landmark_targets),
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
    # K-C: the ink the fit may see — AFTER `derive_word` (the frozen wordbench
    # ruler and the registration were taken on the full ink) and BEFORE the
    # grid fits, so seed windows, solve fields and coverage targets all come
    # from ONE evidence. Off → the very same case object, nothing to diff.
    case, ink_report = ink_evidence_case(case, _ink_options(weights))
    grids = _grid_fits(case, result)

    word_strokes: list[list[list[float]]] = []
    run_slots: list[list[int]] = []
    rounds_by_run: list[list[dict]] = []
    landmarks_by_run: list[dict] = []
    traced: set[int] = set()
    n_runs = n_failed = n_params = 0
    claims_by_run: list[list[dict]] = []
    for run in _chainable_runs(case, grids):
        n_runs += 1
        windows = {s: grids[s]["window"] for s in run}
        seeds = {s: grids[s]["shift_units"] for s in run if not grids[s]["at_bound"]} if chain_seed == "grid" else None
        chain_fit = fit_word_chain(
            case,
            run,
            result=result,
            windows_px=windows,
            slot_shift_init=seeds,
            keep_solve=True,
            mark_claim=weights.mark_claim,
        )
        if chain_fit is None:
            n_failed += 1
            continue
        if weights.mark_claim:
            claims_by_run.append(chain_fit.fit_meta.get("mark_claims", []))
        followed = follow_word_chain(case, run, result=result, windows_px=windows, fit=chain_fit, weights=weights)
        if followed is None:
            n_failed += 1
            continue
        run_slots.append(list(followed.slots))
        rounds_by_run.append(followed.rounds)
        landmarks_by_run.append(followed.fit_meta.get("landmark", {}))
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
        "landmark": _merge_landmark_meta(landmarks_by_run, mode=weights.landmark_targets),
        "n_params": n_params,
        "timings": {"seconds": round(time.perf_counter() - started, 3)},
        # Only while the measure is on: the key's absence keeps an archaeology
        # artefact (`--no-ink-evidence`) byte-identical to every pre-K-C report.
        **({"ink_evidence": ink_report.as_dict()} if ink_report is not None else {}),
        # K-E's claim list per run — present exactly while the measure is on,
        # empty lists included (a word without a firing claim SAYS so; §14
        # "Kette K-E": a silent claim would make a negative unreadable).
        **({"mark_claims": claims_by_run} if weights.mark_claim else {}),
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


def _ink_options(weights: FollowWeights) -> InkEvidenceOptions | None:
    """K-C's options from a configuration — None (= identity) while the measure is off."""
    return (
        InkEvidenceOptions(paper_fraction=float(weights.ink_evidence_paper_fraction)) if weights.ink_evidence else None
    )


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


# ----------------------------------------------------- the calibration hook (⑥)


def calibrate_case(
    case: WordCase,
    *,
    weights: FollowWeights | None = None,
    chain_seed: str = "composed",
    multipliers: Sequence[float] = LANDMARK_CALIBRATION_MULTIPLIERS,
) -> dict:
    """One case's landmark SCALE — a normal follower solve at weight 0, then read.

    The whole point is that nothing is solved twice: the follower runs exactly as
    an arm would (same windows, same runs, same rounds), with the landmark weight
    forced to 0 so the term is inert and the optimum is the arm's own baseline.
    Both targetings are then evaluated ON THAT optimum — the raw branch points
    the chain aims at today and the extrapolated intersections of arm ⑥ — so the
    rungs of the ladder come out of the two measured ratios rather than out of an
    analogy (§11c).

    The weight is forced rather than trusted: a calibration read off a solve the
    term already moved would report the scale of its own effect.
    """
    weights = replace(weights or FollowWeights(), landmark=0.0)
    base = {"kind": case.kind, "specimen_id": case.id, "word": case.word}
    if not case.scorable:
        return {**base, "status": STATUS_SKIPPED, "detail": "frozen unscorable (unauthored template)", "runs": []}
    try:
        result = derive_word(case)
    except Exception as exc:  # noqa: BLE001 — one bad case must not end the run
        return {**base, "status": STATUS_FAILED, "detail": f"{type(exc).__name__}: {exc}", "runs": []}
    if result.composed.get("missing"):
        return {
            **base,
            "status": STATUS_SKIPPED,
            "detail": f"composition missing {result.composed['missing']}",
            "runs": [],
        }

    case, _ink_report = ink_evidence_case(case, _ink_options(weights))  # K-C, the same evidence as `follow_derived`
    grids = _grid_fits(case, result)
    runs: list[dict] = []
    for run in _chainable_runs(case, grids):
        windows = {s: grids[s]["window"] for s in run}
        seeds = {s: grids[s]["shift_units"] for s in run if not grids[s]["at_bound"]} if chain_seed == "grid" else None
        chain_fit = fit_word_chain(
            case,
            run,
            result=result,
            windows_px=windows,
            slot_shift_init=seeds,
            keep_solve=True,
            mark_claim=weights.mark_claim,
        )
        if chain_fit is None:
            continue
        followed = follow_word_chain(
            case, run, result=result, windows_px=windows, fit=chain_fit, weights=weights, keep_solve=True
        )
        if followed is None or followed.problem is None or followed.params is None:
            continue
        runs.append(
            {
                "slots": list(followed.slots),
                "modes": {
                    mode: landmark_calibration(
                        followed.problem,
                        followed.params,
                        landmark_targeting(followed.problem, mode),
                        multipliers=multipliers,
                    )
                    for mode in LANDMARK_CALIBRATION_MODES
                },
            }
        )
    return {**base, "status": STATUS_OK, "detail": "", "runs": runs}


def _calibrate_job(job: tuple[WordCase, FollowWeights, str]) -> dict:
    case, weights, chain_seed = job
    row = calibrate_case(case, weights=weights, chain_seed=chain_seed)
    for run in row["runs"]:
        for mode, calibration in run["modes"].items():
            parity = calibration["parity_weight"]
            print(
                f"  {case.id:<20} slots {'-'.join(str(s) for s in run['slots']):<7} {mode:<13} "
                f"n {calibration['n_landmarks']:>2}/{calibration['n_detected']:<2} "
                f"e_geo {calibration['e_geo']:.4g}  e_lm {calibration['e_landmark']:.4g}  "
                f"parity {('%.4g' % parity) if parity is not None else '--':>10}",
                flush=True,
            )
    if not row["runs"]:
        print(f"  {case.id:<20} {row['status']:<8} {row['detail'] or 'no run carried a chain solve'}", flush=True)
    return row


def calibration_report(rows: Sequence[dict], *, multipliers: Sequence[float]) -> dict:
    """Pool the per-run readings into the table an arm picks its rungs from.

    Medians, never means: one word whose correspondence collapsed onto a nearby
    branch point would otherwise set the ladder for all ten.
    """
    pooled: dict[str, dict] = {}
    for mode in LANDMARK_CALIBRATION_MODES:
        readings = [run["modes"][mode] for row in rows for run in row["runs"] if run["modes"].get(mode)]
        parities = [r["parity_weight"] for r in readings if r["parity_weight"] is not None]
        energies = [r["e_landmark"] for r in readings if r["n_landmarks"]]
        geos = [r["e_geo"] for r in readings if r["n_landmarks"]]
        reasons: dict[str, int] = {}
        for reading in readings:
            for reason, count in reading["reasons"].items():
                reasons[reason] = reasons.get(reason, 0) + int(count)
        parity_median = float(np.median(parities)) if parities else None
        pooled[mode] = {
            "n_solves": len(readings),
            "n_solves_with_landmark": sum(1 for r in readings if r["n_landmarks"]),
            "n_landmarks": sum(int(r["n_landmarks"]) for r in readings),
            "e_geo_median": float(np.median(geos)) if geos else None,
            "e_landmark_median": float(np.median(energies)) if energies else None,
            "parity_weight_median": parity_median,
            "reasons": reasons,
            "rungs": [
                {"multiplier": float(m), "weight": None if parity_median is None else float(m) * parity_median}
                for m in multipliers
            ],
        }
    return {"multipliers": [float(m) for m in multipliers], "modes": pooled}


def print_calibration(report: dict) -> None:
    print()
    print("LANDMARK CALIBRATION — read at the follower optimum with the term INERT (weight 0)")
    print(f"{'mode':<14}{'solves':>8}{'with lm':>9}{'targets':>9}{'e_geo':>12}{'e_landmark':>13}{'parity w':>12}")
    for mode, block in report["modes"].items():
        print(
            f"{mode:<14}{block['n_solves']:>8}{block['n_solves_with_landmark']:>9}{block['n_landmarks']:>9}"
            f"{(block['e_geo_median'] or 0.0):>12.4g}{(block['e_landmark_median'] or 0.0):>13.4g}"
            f"{(block['parity_weight_median'] or 0.0):>12.4g}"
        )
    print()
    print("RUNGS — a fraction of the parity weight (the weight at which the term equals e_geo)")
    header = f"{'mode':<14}" + "".join(f"{m:>14g}" for m in report["multipliers"])
    print(header)
    for mode, block in report["modes"].items():
        line = f"{mode:<14}"
        for rung in block["rungs"]:
            line += f"{rung['weight']:>14.4g}" if rung["weight"] is not None else f"{'--':>14}"
        print(line)
    print()
    print("REFINEMENT — why a target stayed on its raw branch point")
    for mode, block in report["modes"].items():
        print(f"  {mode:<14}{block['reasons'] or '(no target)'}")
    print()
    print("A READING, NOT A DEFAULT: no weight is adopted here. The arm runs the rungs")
    print("against the frozen tracebench baseline and the §14 criteria decide.")


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
    """`"prox=1.0,0.1,0"` → `("prox", [1.0, 0.1, 0.0])`, validated against the arms.

    NUMERIC knobs only. A sweep is a ladder of one weight; the two non-numeric
    fields select a formulation (`landmark_targets`) or switch a guard off
    (`retrace_guard`), and running those as a "ladder" would compare two
    different objectives under one label.
    """
    name, _, raw = spec.partition("=")
    name = name.strip()
    defaults = FollowWeights()
    known = {
        f.name
        for f in fields(FollowWeights)
        if isinstance(getattr(defaults, f.name), (int, float)) and not isinstance(getattr(defaults, f.name), bool)
    }
    if name not in known:
        raise SystemExit(f"--sweep {name!r} is not a numeric FollowWeights field; known: {', '.join(sorted(known))}")
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
    parser.add_argument(
        "--landmark-targets",
        choices=list(LANDMARK_TARGET_MODES),
        default=FOLLOW_LANDMARK_TARGETS,
        help="where the landmark term aims: extrapolated junction crossings (default), "
        "the same without the 1/sigma^2 weighting, the same with by-design non-crossings "
        "classed out (arm 6b), or the raw branch points (the control arm)",
    )
    parser.add_argument(
        "--landmark-calibrate",
        action="store_true",
        help="solve with the term INERT and report e_geo / e_landmark per case — the rungs, measured",
    )
    parser.add_argument("--bind", type=float, help=f"letter bind weight (default {FOLLOW_BIND_WEIGHT}, rejected term)")
    parser.add_argument("--max-delta", type=float, help=f"per-anchor travel budget (default {FOLLOW_MAX_DELTA})")
    parser.add_argument("--no-retrace-guard", action="store_true", help="release the retrace zones too (a measurement)")
    parser.add_argument(
        "--structure-guard",
        action="store_true",
        help="LEGACY NO-OP since Kette v5: the guard is on by default (arm 9 — reject rounds whose assembled "
        "trace exceeds the initialisation's structure class counts). Kept so the K0-ladder command lines in "
        "§14 still parse; to switch the guard OFF use --no-structure-guard",
    )
    parser.add_argument(
        "--structure-guard-two-sided",
        action="store_true",
        help="the K0-invariant guard: also reject rounds that LOSE initialisation structure (implies --structure-guard)",
    )
    parser.add_argument(
        "--structure-guard-soll",
        action="store_true",
        help="LEGACY NO-OP since Kette v5: the soll-aware K0 guard (aug19 — every class may move only "
        "TOWARD the soll count, never past it, never away) is on by default. Kept so older command lines "
        "parse; --no-structure-guard switches the whole stack off",
    )
    parser.add_argument(
        "--structure-guard-ratchet",
        action="store_true",
        help="LEGACY NO-OP since Kette v5: the K0-Z-R ratchet (aug20 — after every accepted round the "
        "budget snaps to its class counts, the soll interval only tightens) is on by default. Kept so "
        "older command lines parse; --no-structure-guard-ratchet is the K0-S Sprosse-1 rung without it",
    )
    parser.add_argument(
        "--structure-guard-zone",
        type=float,
        default=FollowWeights.structure_guard_zone_units,
        help="K0-Z (aug20): zonal rejection radius in x-heights — pin only the anchors around the "
        "violating zone and re-solve once instead of rejecting the whole round (0 = round-atomic; "
        "default 0.55 since Kette v5)",
    )
    parser.add_argument(
        "--no-structure-guard",
        action="store_true",
        help="switch the whole structure guard OFF — the follower before arm 9 existed, byte-identical. "
        'A DIAGNOSTIC arm („Kette-frei"), never the duel candidate: freed of the guard it covers more '
        "ink by destroying structure (init 86 -> free 125 soll points over 63 words, aug26)",
    )
    parser.add_argument(
        "--no-structure-guard-ratchet",
        action="store_true",
        help="K0-S Sprosse 1: the soll guard without the ratchet (the round-atomic interval)",
    )
    parser.add_argument(
        "--no-ink-evidence",
        action="store_true",
        help="switch the K-C ink-evidence mask OFF (the Kette v4 default drops paper-grey non-main "
        "components — specks, show-through — from the evidence the fit is pulled by; the frozen bench "
        "mask stays as it is). Off = the pre-v4 follower, byte-identical, for archaeology runs",
    )
    parser.add_argument(
        "--ink-evidence-paper-fraction",
        type=float,
        default=INK_EVIDENCE_PAPER_FRACTION,
        help=f"K-C class boundary on the main-ink→paper grey scale (default {INK_EVIDENCE_PAPER_FRACTION})",
    )
    parser.add_argument(
        "--soll-source",
        choices=["init", "composition"],
        default=FollowWeights.soll_source,
        help="K0-S (aug21): where the soll guard's target counts come from — the canonical composition "
        "through the shared ductus_soll builder (default since Kette v5; one pipeline with the metric) "
        "or the chain init through the assembler (the aug19 behaviour, the K0-S ladder's base)",
    )
    parser.add_argument(
        "--mark-claim",
        action="store_true",
        help="K-E stage 1 (aug21): a composed mark stroke claims its dark ink component within the "
        "ruler's 0.6-xh mark radius — the component leaves the body's fields and coverage pot, the "
        "mark's samples read only their component; words without a firing claim are byte-identical",
    )
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
        "landmark_targets": args.landmark_targets,
        "bind": args.bind,
        "max_delta": args.max_delta,
    }
    weights = FollowWeights(**{k: v for k, v in overrides.items() if v is not None})
    return replace(
        weights,
        retrace_guard=not args.no_retrace_guard,
        # Since Kette v5 the guard stack IS the follower: the positive flags
        # are kept so every script and §14 command line from the K0 ladder
        # still parses, and `--no-structure-guard` is the one archaeology
        # switch that turns the whole stack off (the „Kette-frei" arm).
        structure_guard=not args.no_structure_guard,
        structure_guard_two_sided=bool(args.structure_guard_two_sided) and not args.no_structure_guard,
        structure_guard_soll=not args.no_structure_guard,
        structure_guard_zone_units=0.0 if args.no_structure_guard else float(args.structure_guard_zone),
        structure_guard_ratchet=not (args.no_structure_guard or args.no_structure_guard_ratchet),
        ink_evidence=not args.no_ink_evidence,
        ink_evidence_paper_fraction=float(args.ink_evidence_paper_fraction),
        mark_claim=bool(args.mark_claim),
        soll_source=str(args.soll_source),
    )


def main() -> None:
    args = build_parser().parse_args()
    if not args.ids and not args.all:
        raise SystemExit("name at least one case id, or pass --all")
    started = time.perf_counter()
    cases = _load_cases(list(args.ids), which=args.which, style=args.style, fixtures_root=args.fixtures)
    if not cases:
        raise SystemExit(f"no case matched {args.ids!r} in the {args.which!r} set")

    base = weights_from_args(args)
    if args.landmark_calibrate:
        print(f"landmark calibration: {len(cases)} cases · set {args.which} · term INERT (weight 0)")
        jobs = [(c, base, args.chain_seed) for c in cases]
        if args.jobs > 1:
            with ProcessPoolExecutor(max_workers=max(1, args.jobs)) as pool:
                rows = list(pool.map(_calibrate_job, jobs))
        else:
            rows = [_calibrate_job(j) for j in jobs]
        report = calibration_report(rows, multipliers=LANDMARK_CALIBRATION_MULTIPLIERS)
        print_calibration(report)
        print(f"runtime {round(time.perf_counter() - started, 1)}s")
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(
                json.dumps(
                    {
                        "tool": FOLLOW_TOOL_NAME,
                        "version": FOLLOW_ARTIFACT_VERSION,
                        "style": args.style,
                        "set": args.which,
                        "mode": "landmark-calibrate",
                        "weights": asdict(replace(base, landmark=0.0)),
                        "provisional": True,
                        "summary": report,
                        "cases": rows,
                    },
                    indent=1,
                    ensure_ascii=False,
                )
            )
            print(f"wrote {args.json}")
        return

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
        print(
            f"arm {label}: prox {weights.prox:g} · rounds {weights.rounds} · coverage {weights.coverage:g}"
            + (f" · landmark {weights.landmark:g} ({weights.landmark_targets})" if weights.landmark else "")
        )
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
    "FOLLOW_LANDMARK_CONTINUATION_TOL_DEG",
    "FOLLOW_LANDMARK_CORE_WIDTHS",
    "FOLLOW_LANDMARK_MAX_SHIFT_WIDTHS",
    "FOLLOW_LANDMARK_SIGMA_FLOOR_PX",
    "FOLLOW_LANDMARK_TARGETS",
    "FOLLOW_LANDMARK_WEIGHT",
    "FOLLOW_LANDMARK_WINDOW_UNITS",
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
    "LANDMARK_CALIBRATION_MODES",
    "LANDMARK_CALIBRATION_MULTIPLIERS",
    "LANDMARK_NONCROSSING_REASONS",
    "LANDMARK_TARGET_MODES",
    "STRUCTURE_GUARD_MAX_RETRIES",
    "FollowFit",
    "FollowWeights",
    "LandmarkTargeting",
    "apply_landmark_targets",
    "apply_retrace_guard",
    "build_follow_problem",
    "calibrate_case",
    "calibration_report",
    "candidate_payload",
    "classed_targets",
    "extrapolated_targets",
    "follow_case",
    "follow_derived",
    "follow_word_chain",
    "landmark_calibration",
    "landmark_energy",
    "landmark_meta",
    "landmark_targeting",
    "parse_sweep",
    "print_calibration",
    "raw_landmark_targets",
    "retrace_anchor_mask",
    "retrace_sample_mask",
    "run_arm",
    "structure_class_counts",
]


if __name__ == "__main__":
    main()
