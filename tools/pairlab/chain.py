"""Pair-scale ductus chain fit (issue #278, Stage A).

`analyze.dissect_occurrence` fits the two letters of a join INDEPENDENTLY and
then regenerates the connector between them, so neither letter ever sees the ink
of the transition it was actually written into. The chain fit replaces that with
ONE optimisation over `letter → connector → letter`: a single anchor array, a
single sampling plan, exact C0 continuity at the two seams by parameter sharing
(a shared anchor index, not a soft penalty), and per-segment residuals
afterwards. How much of the transition the glyph's own tail owns and how much
the connector owns becomes a measured quantity instead of an assumption.

Three binding constraints, from the issue:

1. **Measurement only.** Nothing here writes to the DB or the API, feeds
   `core/`, or changes rendering. `core/fit.py` stays byte-identical; this
   module reuses its primitives and thresholds so every number is comparable
   like-for-like with the independent-fit baseline.
2. **Chart-row templates only** (variant 0). The composed layout — placement,
   generated connector — is the INITIALISATION, never a target: no Laufform row
   is fitted, and the composed geometry appears in no penalty term.
3. **The connector is form-unregularised.** Its interior anchors carry no
   Tikhonov term at all; the only shape term on them penalises *change of
   curvature*, never distance to the generated Bézier — otherwise the chain
   would measure the generator against itself and `gen_chamfer` would stop being
   an audit number. That smoothness term exists solely because an unregularised
   polyline in a ~1 px-smoothed EDT degenerates into a zig-zag.

**Stage B** walks through that seam: `build_chain_problem` always took a LIST of
segments, so `fit_word_chain` assembles `[L0, C0, L1, C1, …]` for any run of
joined slots under the same index map, the same arc-length translation ramp and
the same per-segment coverage scaling, and `fit_pair_chain` is now the thin
two-letter wrapper over it that `chainbench` reads. `chain_runs` cuts a word
into those runs (a lone letter is a one-segment chain, not a skipped one).
"""

from __future__ import annotations

import bisect
import os
import time
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.optimize import minimize
from scipy.spatial import cKDTree

from core.compose import CONNECT_SAMPLES as _COMPOSE_CONNECT_SAMPLES
from core.compose import _endpoint_tangent
from core.fit import (
    CONVERGED_COVERAGE_RMSE_UNITS,
    CONVERGED_GEO_RMSE_UNITS,
    DEFAULT_COVERAGE_WEIGHT,
    DEFAULT_LAMBDA_REG,
    DEFAULT_N_SAMPLES,
    DEFAULT_WIDTH_WEIGHT,
    DIST_FIELD_SIGMA_PX,
    MAX_ANCHOR_DELTA,
    MAX_COVERAGE_POINTS,
    WIDTH_FIELD_SIGMA_PX,
    _bilinear_with_grad,
    _sampling_operator,
    _skeleton_points,
    _width_operator,
)
from core.geometry import bilinear
from core.shaping import GlyphSlot
from core.template import build_sample_plan
from tools.pairlab.analyze import (
    FIT_DX_UNITS,
    FIT_DY_UNITS,
    TRACE_WINDOW_MARGIN,
    JoinDissection,
    _body_items,
    _generate_connector,
)
from tools.wordlab.cases import WordCase
from tools.wordlab.derive import WordDeriveResult, derive_word


# Per-anchor displacement bound (xh) for the connector's interior anchors. Wider
# than the letters' `core.fit.MAX_ANCHOR_DELTA` (0.75) because the connector has
# no measured form to stay near — it must be free to leave the generated Bézier.
CHAIN_CONNECTOR_MAX_DELTA = 1.0
# Huber cap (xh) on the coverage distance: beyond it a skeleton pixel's pull
# grows linearly, not quadratically. A pair window contains ink that belongs to
# neither segment (a neighbouring letter's descender, a speck); uncapped, a
# handful of such points out-levers the whole chain.
CHAIN_COVERAGE_CAP_UNITS = 0.30
# Weight of the connector-only second-difference (curvature-change) term.
# Calibrated once on the Abb.-20 `pairs` set (34 occurrences) against the
# measured 0.2–0.4 xh per-side stub-replacement zone of
# `docs/proposals/uebergaenge-befund.md` §5, swept over 0 … 1e-2; see §5c there
# for the table. The term is what keeps the seam where the hand puts it: at 0
# the free connector swallows the left letter's tail (share median 0.70 xh,
# 54 % of sides beyond 0.4 xh), at 1e-3 and above it stiffens the shared seam
# anchors so hard that letter convergence collapses (0.50 → 0.15 at 1e-2).
# 1e-5 is the largest weight that keeps the seam inside the measured band
# (tail-share median 0.37 xh) while letter convergence is at its maximum; its
# stated systematic effect is a slightly rougher connector (M3 dconn median
# 0.197 xh vs. 0.178 at 1e-3).
CHAIN_CONNECTOR_SMOOTH_WEIGHT = 1e-5
# Coverage points per chain segment: `core.fit.MAX_COVERAGE_POINTS` (300) is a
# per-GLYPH budget, so the chain scales it as MAX_COVERAGE_POINTS × n_segments.
# Invariant (asserted in code and in a unit test): coverage density per unit of
# skeleton x-extent must not fall below the single-letter fit's.
CHAIN_COVERAGE_PER_SEGMENT = 300
# L-BFGS-B iteration budget for the CHAIN solve. Deliberately its OWN constant
# rather than `core.fit.DEFAULT_MAX_ITER` (300): that number is a per-GLYPH
# budget on a per-glyph problem, and a chain is a different problem — a 3-slot
# word carries ~820 free parameters where one letter carries a fraction of it,
# so the same budget buys proportionally fewer descent steps.
#
# Swept over the frozen words+pairs fixtures (96 solves, 344 slot rows),
# one `--diag-csv` run per budget:
#
#     cap    capped     not_conv_local   accepted   geo_rmse med   CPU
#     300    87 (91 %)      47             232        1.063 px    1942 s
#     900    63 (66 %)      38             238        1.030 px    5315 s
#    2700    10 (10 %)      35             241        1.027 px   10145 s
#    8100     0 ( 0 %)      35             241        1.027 px   10608 s
#
# At 300 the budget — not a convergence criterion — was the stop in 91 % of
# solves. That is not "a bit tight": the median chain solve takes 1211
# iterations (p25 680, p90 2518), so the old budget sat far below the point
# where one typically settles. A truncated solve is not a converged one — it
# fails `converged_local`, its occurrence is dropped, and where the truncation
# lands moves with the initialisation, which is why the harvest was not
# reproducible across the exact-nib change.
#
# The default is 8100 because a budget that binds at all is the wrong kind of
# knob: L-BFGS-B stops at its own criteria, so raising the ceiling costs
# nothing for every solve that already converged, and only the hard tail pays.
# Measured, that tail is cheap — 2700 → 8100 buys "no solve is truncated any
# more" for **+5 % CPU** (the longest solve needs 4215 iterations, so 8100 is
# ~1.9× headroom over the observed maximum).
#
# Raising it is also demonstrably harmless, which is the part worth checking
# rather than assuming: 305 of the 344 slot rows are BIT-IDENTICAL to the 2700
# run, the 39 that move belong exclusively to the ten formerly-capped
# specimens, that movement is settling noise (median +0.0010 px, worst
# +0.0240 px, 22 rows worse against 17 better), and all 344 gate verdicts are
# unchanged. The result stops being the budget's answer and becomes the
# model's, without becoming a different answer.
#
# `CHAIN_MAX_ITER_ENV` re-runs the sweep without editing this file.
CHAIN_MAX_ITER_ENV = "KS_CHAIN_MAX_ITER"
CHAIN_MAX_ITER_DEFAULT = 8100
CHAIN_MAX_ITER = int(os.environ.get(CHAIN_MAX_ITER_ENV) or CHAIN_MAX_ITER_DEFAULT)
# --- cross-segment overlap (the exclusivity term, round 2) -------------------
# The basin probe (uebergaenge-befund.md §5c) proved the placement collapse is
# a property of the OBJECTIVE: on all five probed collapsing cases the stacked
# solution scores lower on every term, because the objective checks the UNION
# of the segments against the union of the ink and is blind to attribution — a
# letter absorbing the connector's ink and a connector retracing a letter's
# stroke both read as good coverage. The overlap term encodes the physical
# statement the model was missing: a pen does not write the same stroke twice.
# Samples of DIFFERENT segments closer than the radius pay a quadratic hinge.
#
# Radius: "on the same ridge" — the pooled hairline's mask diameter is
# ~0.16 xh, so two centerlines within 0.15 xh are inside one drawn stroke.
CHAIN_OVERLAP_RADIUS_UNITS = 0.15
# Seam exemption: adjacent segments legitimately share ink near their common
# seam — §5's measured stub-replacement band is 0.2–0.4 xh per side, so the
# band's upper edge is exempt. Structural (by init arc distance to the seam
# sample), so the objective's gradient stays exact.
CHAIN_OVERLAP_SEAM_EXEMPT_UNITS = 0.4
# Weight 0.2, set by the pre-registered A/B over the frozen fixtures (weights
# 0 · 0.2 · 1.0, full words+pairs harvest each):
#
#   w      accepted   flags (38 base)   freed / new   geo_rmse p50/p90
#   0.0      241         38                —            1.027 / 1.585
#   0.2      245         34             4 / 0           1.030 / 1.622
#   1.0      242         34             6 / 2           1.034 / (geo_rmse gate 21→23)
#
# At 0.2 the term heals EXACTLY the four joins the ink adjudication (§5c) had
# identified as the guard's marginal fires (`streiten|0`, `ssi|0`, `ssi|1`,
# `regieren|3`) — and it heals them mechanically, not statistically: the seam
# retrace disappears from the solve itself (`streiten|0` seam_left 1.178 →
# 0.136 xh, `ssi|0` 1.360 → 0.258), so the guard stops firing without any
# threshold moving. Yield +4 (`longs` 3 → 6), zero new flags, `at_bound`
# 1 → 0, rmse p50 +0.003 px. 1.0 is the over-strong regime: it starts pushing
# letters off legitimately shared ink (two fresh derailments, the geo_rmse
# gate up 21 → 23) for less yield.
#
# What 0.2 does NOT fix, knowingly: the interleaved pair-drill stacks (`do`,
# `bp`, …) whose centerlines stay farther apart than the radius — by the
# radius rationale that separation is adjacent writing, not double-writing,
# and per the round-1 finding (`dk`) this hand really does tuck letters under
# crossbars, so their legitimacy needs better ground truth, not a bigger
# radius.
CHAIN_OVERLAP_WEIGHT_ENV = "KS_CHAIN_OVERLAP_WEIGHT"
CHAIN_OVERLAP_WEIGHT = float(os.environ.get(CHAIN_OVERLAP_WEIGHT_ENV) or 0.2)
# Points on the raw exit→entry connector polyline — the production sample count,
# re-exported from `core.compose` so a change there cannot silently desync. The
# two endpoints are SHARED with the letters, the interior 22 are free anchors.
CONNECT_SAMPLES = _COMPOSE_CONNECT_SAMPLES  # == 24
# Chord (xh) below which the generated connector is RE-DISCRETISED before it
# becomes the chain's initialisation (`regularise_connector_anchors`).
# `analyze._generate_connector` always emits its full Bézier subdivision,
# however little room the composed placement leaves between the two letters —
# and `_second_difference_operator`'s rows scale as 1/ds², so packing two dozen
# anchors into a 0.05 xh chord raises the connector's smoothness block by ~7
# orders of magnitude and L-BFGS-B spends its whole iteration budget there while
# the letters never move (see `regularise_connector_anchors`). The cut sits in
# the empty band the Stage-A fixture set measures: every one of the 24 affected
# occurrences has a chord ≤ 0.187 xh, every one of the other 224 ≥ 0.205 xh.
CHAIN_CONNECTOR_MIN_SPAN_UNITS = 0.20
# Target anchor spacing (xh) of a re-discretised connector — the spacing the
# smoothness weight above was calibrated at (a normal connector's ~0.30 xh chord
# over its ~23 sample intervals).
CHAIN_CONNECTOR_ANCHOR_SPACING_UNITS = 0.013

# Anchor count `core.fit.DEFAULT_N_SAMPLES` was tuned against, so the chain's
# sample budget keeps the same ~1.5 samples per anchor at any chain length.
_REFERENCE_ANCHOR_COUNT = 120
# A stroke floating entirely above the midband is a diacritic (compose's rule,
# mirrored by `analyze.trace_letter_ductus`) and never carries a seam.
_DIACRITIC_MIN_Y = 1.0


@dataclass
class ChainSegmentSpec:
    """One link of the chain as INPUT to `build_chain_problem` (`ChainSegment`
    is the corresponding OUTPUT). Already placed in the composed word frame."""

    kind: str  # "letter" | "connector"
    anchors: np.ndarray  # (K, 2) composed-frame anchors, y up, baseline 0
    slot_index: int | None = None  # letters: the word slot this block translates with
    key: str | None = None  # letters: glyph key (chart row, variant 0)
    stroke_starts: Sequence[int] = (0,)  # pen-lift bounds within `anchors`
    corner_anchors: Sequence[int] = ()  # corner indices for `build_sample_plan`
    half_widths: np.ndarray | None = None  # (K,) letters only; connector samples are width-masked
    seam_in: int | None = None  # anchor index shared with the PREVIOUS segment's `seam_out`
    seam_out: int | None = None  # anchor index shared with the NEXT segment's `seam_in`
    cov_window_px: tuple[float, float] | None = None
    """Optional `(x_lo, x_hi)` crop-px window this segment's coverage GATE is
    read in — the letter-local window of `analyze.trace_letter_ductus`. The FIT
    is unaffected: coverage targets, objective and gradient keep seeing the whole
    union window (owning the connector ink is the chain's entire point). Only the
    per-segment report gains a second, like-for-like coverage residual so a chain
    letter and a single-letter M4 fit are graded on the same ink. None — the
    connector, and any caller that does not care — makes the local gate identical
    to the union one."""


@dataclass
class ChainSegment:
    """One fitted link of the chain, with its own residuals and gate."""

    kind: str  # "letter" | "connector"
    slot_index: int | None
    key: str | None
    anchor_slice: tuple[int, int]  # into the FREE anchor array
    sample_slice: tuple[int, int]  # into fitted_polyline_px
    fitted_anchors: np.ndarray | None  # letters only, template coords, chart-frame
    polyline_px: np.ndarray
    geo_rmse_px: float  # UNSMOOTHED field, template→skeleton
    cov_rmse_px: float  # UNSMOOTHED and UNCAPPED, skeleton→template, attributed by nearest sample
    n_cov: int
    cov_rmse_local_px: float  # …the same, restricted to `spec.cov_window_px` (== cov_rmse_px when None)
    n_cov_local: int
    converged: bool  # both residuals within core.fit's CONVERGED_* thresholds, UNION-window coverage
    converged_local: bool  # …the same gate on the letter-local coverage residual
    max_anchor_delta: float


@dataclass
class ChainFit:
    """One `letter → connector → letter` chain fitted onto one occurrence."""

    case: WordCase
    slot_a: int
    segments: list[ChainSegment]  # [L, C, R]
    slot_shift_units: dict[int, tuple[float, float]]  # per-slot translation block
    slot_at_bound: dict[int, bool]  # block rests on its FIT_DX/DY_UNITS bound — suspect
    global_shift_units: tuple[float, float]
    cut_indices: tuple[int, int]  # (cut_L, cut_R), the two shared seam anchors
    connector_units: np.ndarray  # composed-frame connector, for the `dconn` comparison
    converged: bool  # L and R converged; the connector's gate is reported separately
    converged_local: bool  # …judged on the LETTER-LOCAL coverage windows (the like-for-like gate)
    fit_meta: dict  # optimiser status, energies, n_params, n_cov, timings


@dataclass
class ChainWordFit:
    """One RUN of joined slots fitted as a single chain — `[L, C, L, C, …]`.

    The Stage-B generalisation of `ChainFit`, which is this restricted to two
    letters (and still the frozen public shape `chainbench` reads). Everything
    that was a left/right pair here becomes a list in writing order: one entry
    per join for `cut_indices` and `connector_units`, one dict entry per fitted
    slot for the placement blocks. A one-slot run is a legitimate chain with one
    segment, no join and an empty connector list — that is how a lone letter
    (a digit, a word of one character) enters the same code path.
    """

    case: WordCase
    slots: list[int]  # the fitted run, in writing order
    segments: list[ChainSegment]  # [L, C, L, C, …], letters at the even indices
    slot_shift_units: dict[int, tuple[float, float]]  # per-slot translation block
    slot_at_bound: dict[int, bool]  # block rests on its FIT_DX/DY_UNITS bound — suspect
    global_shift_units: tuple[float, float]
    cut_indices: list[tuple[int, int]]  # per join: (left `seam_out`, right `seam_in`)
    connector_units: list[np.ndarray]  # per join, composed-frame, for the `dconn` comparison
    stroke_polylines_px: list[dict]
    """The fitted chain as PEN-DOWN polylines in crop pixels, in writing order —
    one entry per stroke of a letter and one per connector, each naming its
    `kind` · `segment_index` · `slot_index` · `key` · `stroke_index` and
    carrying `points_px`. This is the shape a word trace is assembled from
    (`tools.laufform.harvest._strokes_to_word_units` consumes exactly one such
    polyline per pen-down stroke); consecutive entries meet exactly at the
    shared seam anchors, so a caller wanting ONE continuous pen path just
    concatenates them."""
    converged: bool  # every LETTER segment converged; the connectors' gates are reported per segment
    converged_local: bool  # …judged on the LETTER-LOCAL coverage windows (the like-for-like gate)
    fit_meta: dict  # optimiser status, energies, n_params, n_cov, timings


# ----------------------------------------------------------------- pure helpers


def _second_difference_operator(pts: np.ndarray) -> np.ndarray:
    """(m, K) arc-length-normalised second-difference operator over a polyline.

    The same construction as `core.fit._width_curvature_operator`, applied to 2D
    POSITIONS instead of the width profile: row `j` reads
    ``2/(ds_{j-1}+ds_j) · ((a_{j+1}−a_j)/ds_j − (a_j−a_{j-1})/ds_{j-1})``. A
    collinear chain therefore scores exactly zero at any spacing — the term
    measures CHANGE of curvature only and knows nothing about the generated
    Bézier it was initialised from (binding constraint 3). The spacings are
    frozen at the initial anchors, which keeps the operator linear and the
    gradient exact.
    """
    pts = np.asarray(pts, dtype=float)
    k = len(pts)
    if k < 3:
        return np.zeros((0, k))
    d = np.diff(pts, axis=0)
    ds = np.hypot(d[:, 0], d[:, 1])
    ds[ds <= 0] = 1e-6
    rows = np.zeros((k - 2, k))
    for j in range(1, k - 1):
        scale = 2.0 / (ds[j - 1] + ds[j])
        rows[j - 1, j - 1] = scale / ds[j - 1]
        rows[j - 1, j] = -scale * (1.0 / ds[j - 1] + 1.0 / ds[j])
        rows[j - 1, j + 1] = scale / ds[j]
    return rows


def regularise_connector_anchors(
    conn: np.ndarray,
    *,
    min_span_units: float = CHAIN_CONNECTOR_MIN_SPAN_UNITS,
    spacing_units: float = CHAIN_CONNECTOR_ANCHOR_SPACING_UNITS,
) -> np.ndarray:
    """Re-discretise a generated connector that is too short for its point count.

    `analyze._generate_connector` emits its full `CONNECT_SAMPLES` Bézier
    subdivision whatever the composed placement leaves between the two letters,
    and floors its handle at 0.05 xh. Where two letters are composed nearly on
    top of each other that floor overrides the generator's own design value
    `0.4·span`, so the cubic reaches further from the exit than the entry is
    away and doubles back: every point inside ~0.05 xh of arc, neighbouring
    samples 8e-5 xh apart.

    That is a harmless RENDERING fallback — the composer draws the stub and
    moves on — but a hostile INITIALISATION. `_second_difference_operator`'s
    rows scale as 1/ds², so the connector's block of the objective enters the
    Hessian ~10⁷× stiffer than on a normal join: measured on the Stage-A fixture
    set, `e_smooth(x0)` is 5.2e6 (median) on the 24 affected occurrences against
    53.7 on the other 224, `f(x0)` 51.9 against 0.026, and every one of the 24
    ends at ``STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT`` with `e_geo`,
    `e_cov` and `e_wid` unchanged to six decimals from `x0` — the whole budget
    goes into unbending the connector and the letters never move at all.

    The repair is a DISCRETISATION one, not a shape one: below `min_span_units`
    of chord the same curve is resampled by uniform arc length to as many
    anchors as `spacing_units` allows (at least 3, never more than it already
    has; a fully collapsed connector keeps its two seam anchors and nothing in
    between), which brings ds back into the range
    `CHAIN_CONNECTOR_SMOOTH_WEIGHT` was calibrated at. The generated SHAPE is
    preserved — the endpoints exactly, the interior by arc-length interpolation
    — so nothing here trades the generator against itself (binding constraint
    3), and a connector at or above the threshold is returned untouched.
    """
    pts = np.asarray(conn, dtype=float).reshape(-1, 2)
    if len(pts) < 3:
        return pts
    span = float(np.hypot(pts[-1, 0] - pts[0, 0], pts[-1, 1] - pts[0, 1]))
    if span >= min_span_units:
        return pts
    seg = np.hypot(*np.diff(pts, axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    if arc[-1] <= 0:
        # Fully collapsed (the two body endpoints coincide): the two seam
        # anchors and nothing between them. An interior anchor here would only
        # give `_second_difference_operator` coincident points to divide by.
        return pts[[0, -1]]
    n = int(min(len(pts), max(3, round(span / max(spacing_units, 1e-9)) + 1)))
    if n >= len(pts):
        return pts
    at = np.linspace(0.0, arc[-1], n)
    return np.column_stack([np.interp(at, arc, pts[:, 0]), np.interp(at, arc, pts[:, 1])])


def _coverage_huber(dist: np.ndarray, cap: float) -> tuple[np.ndarray, np.ndarray]:
    """Huber energy ρ(d) and its scalar derivative ρ'(d), capped at `cap`.

    ``ρ(d) = d²`` up to the cap and ``cap·(2d − cap)`` beyond it, so a skeleton
    pixel that belongs to neither segment (a neighbour's descender, a speck)
    keeps pulling but can no longer out-lever the whole chain: its gradient
    magnitude saturates at ``2·cap`` instead of growing with the distance.
    """
    dist = np.asarray(dist, dtype=float)
    inside = dist <= cap
    rho = np.where(inside, dist**2, cap * (2.0 * dist - cap))
    dscale = np.where(inside, 2.0 * dist, 2.0 * cap)
    return rho, dscale


def _letter_cut_anchors(anchors: np.ndarray, stroke_starts: Sequence[int] | None) -> tuple[int, int]:
    """`(cut_in, cut_out)` — the two seam anchors of one letter.

    `cut_out` is the LAST anchor of the letter's last non-diacritic stroke and
    `cut_in` the FIRST anchor of its first non-diacritic stroke, using
    `analyze.trace_letter_ductus`' diacritic rule verbatim: a stroke that is not
    the first and floats entirely above the midband is a diacritic and must
    never carry the join (the i's dot does not connect to the next letter).
    """
    anchors = np.asarray(anchors, dtype=float)
    k = len(anchors)
    starts = [int(s) for s in (stroke_starts or [0]) if int(s) < k]
    bounds = [*starts, k] if starts else [0, k]
    diacritic = [
        si > 0 and bool((anchors[a:b, 1] > _DIACRITIC_MIN_Y).all())
        for si, (a, b) in enumerate(zip(bounds[:-1], bounds[1:], strict=True))
    ]
    body = [i for i, d in enumerate(diacritic) if not d] or [0]
    return bounds[body[0]], bounds[body[-1] + 1] - 1


def _segment_converged(geo_rmse_px: float, cov_rmse_px: float, unit_px: float) -> bool:
    """`core.fit`'s own convergence gate, applied per chain segment.

    Literally `CONVERGED_GEO_RMSE_UNITS` / `CONVERGED_COVERAGE_RMSE_UNITS`, so a
    chain segment and a single-letter M4 fit are judged by the same yardstick.
    """
    return bool(
        geo_rmse_px <= CONVERGED_GEO_RMSE_UNITS * unit_px and cov_rmse_px <= CONVERGED_COVERAGE_RMSE_UNITS * unit_px
    )


@dataclass
class _ChainProblem:
    """Frozen inputs + operators of one chain solve — the chain twin of
    `core.fit._InstanceFit`. Everything is fixed at the initial anchors so
    `objective` has an exactly analytic gradient (L-BFGS-B's line search
    requires function and gradient to agree to machine precision), and the
    per-segment report runs on the UNSMOOTHED fields.
    """

    specs: list[ChainSegmentSpec]  # the chain in writing order
    anchors_free: np.ndarray  # (K_free, 2) initial free anchors, concatenated per segment
    idx: np.ndarray  # (K_plan,) free → plan anchor index map; ties the seams
    anchor_slices: list[tuple[int, int]]  # per segment, into `anchors_free`
    sample_slices: list[tuple[int, int]]  # per segment, into the sample array
    slot_blocks: dict[int, int]  # slot_index → parameter offset of its 2-vector translation block
    ramp: np.ndarray  # (K_conn,) arc-length weights blending the two neighbouring slot blocks
    reg_w: np.ndarray  # (K_free,) Tikhonov weight — 1 on letters, 0 on connector interiors
    width_mask: np.ndarray  # (n_s,) 1 on letter samples, 0 on connector samples
    sampling_op: np.ndarray  # plan anchors → centerline samples
    sw_px: np.ndarray  # target half-widths per sample (px)
    dist_raw: np.ndarray
    dist_smooth: np.ndarray
    width_raw: np.ndarray
    width_smooth: np.ndarray
    cov_pts: np.ndarray  # coverage targets over the UNION pair window
    unit_px: float
    x_origin_px: float
    baseline_y_px: float
    crop_h: int
    crop_w: int
    cov_cap_px: float
    width_weight: float
    coverage_weight: float
    lambda_reg: float
    smooth_weight: float
    overlap_weight: float
    overlap_radius_px: float
    overlap_exempt: np.ndarray  # (n_s,) True where a sample sits in a seam band
    x0: np.ndarray  # initial parameter vector (all zeros: the composed layout)
    bounds: list[tuple[float, float]]  # global shift, slot blocks, per-anchor deltas
    # ---- internals (not part of the Track-C contract) ----
    block_op: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    """(K_free, n_blocks) weight of every slot translation block on every free
    anchor: 1 on the block's own letter, the arc-length ramp on a connector
    interior, 0 elsewhere. Linear ⇒ the ramp's gradient is exact."""
    smooth_op: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    """(M, K_plan) second differences of the connector blocks only."""
    plan_slices: list[tuple[int, int]] = field(default_factory=list)
    """per segment, into the PLAN anchor array (seam anchors included)."""
    n_letter_anchors: float = 1.0
    n_samples: int = 0
    seg_of_sample: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=int))
    """(n_s,) segment index of every sample — the axis `sample_slices` and the
    per-segment report are cut along."""
    stroke_of_sample: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=int))
    """(n_s,) chain-wide PEN-STROKE index of every sample. The chain is sampled
    exactly as a multi-stroke glyph is, so a pen lift inside a letter (the u's
    two downstrokes) splits its samples here — which is what lets a caller read
    the fitted chain back out as pen-down polylines instead of one blob."""

    # ------------------------------------------------------------------ mapping

    @property
    def n_blocks(self) -> int:
        return self.block_op.shape[1]

    def unpack(self, params: np.ndarray) -> tuple[float, float, np.ndarray, np.ndarray]:
        """`(tx, ty, slot blocks (n_blocks, 2), per-anchor deltas (K_free, 2))`."""
        nb = self.n_blocks
        blocks = np.asarray(params[2 : 2 + 2 * nb], dtype=float).reshape(nb, 2)
        deltas = np.asarray(params[2 + 2 * nb :], dtype=float).reshape(-1, 2)
        return float(params[0]), float(params[1]), blocks, deltas

    def free_anchors(self, params: np.ndarray) -> np.ndarray:
        """Effective free anchors: initial + delta + slot ramp + global shift."""
        tx, ty, blocks, deltas = self.unpack(params)
        return self.anchors_free + deltas + (self.block_op @ blocks) + np.array([tx, ty])

    def plan_anchors(self, params: np.ndarray) -> np.ndarray:
        """Effective PLAN anchors — the free array re-expanded through the index
        map, so both sides of a seam read the exact same coordinates."""
        return self.free_anchors(params)[self.idx]

    def to_pixels(self, params: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        ap = self.plan_anchors(params)
        px = self.x_origin_px + (self.sampling_op @ ap[:, 0]) * self.unit_px
        py = self.baseline_y_px - (self.sampling_op @ ap[:, 1]) * self.unit_px
        return px, py

    def out_of_crop(self, px: np.ndarray, py: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Signed distance of each sample beyond the crop border (0 inside) —
        the clamped fields would otherwise report a flattering residual with no
        gradient at all outside the crop (`core.fit._InstanceFit.out_of_crop`)."""
        return px - np.clip(px, 0.0, self.crop_w - 1.0), py - np.clip(py, 0.0, self.crop_h - 1.0)

    # ---------------------------------------------------------------- objective

    def _evaluate(self, params: np.ndarray, want_grad: bool) -> tuple[dict[str, float], np.ndarray | None]:
        """Shared core of `objective` and `energy_terms` (see their docstrings)."""
        unit_sq = self.unit_px**2
        _, _, _, deltas = self.unpack(params)
        ap = self.plan_anchors(params)
        px = self.x_origin_px + (self.sampling_op @ ap[:, 0]) * self.unit_px
        py = self.baseline_y_px - (self.sampling_op @ ap[:, 1]) * self.unit_px
        n_s = len(px)

        # --- geometry: chain centerline on the skeleton (+ out-of-crop pull) ---
        d, d_dx, d_dy = _bilinear_with_grad(self.dist_smooth, px, py)
        ox, oy = self.out_of_crop(px, py)
        e_geo = float(np.mean(d**2) + np.mean(ox**2 + oy**2)) / unit_sq
        g_px = 2.0 * (d * d_dx + ox) / (n_s * unit_sq)
        g_py = 2.0 * (d * d_dy + oy) / (n_s * unit_sq)

        # --- width: letter samples only (the connector has no measurement) ---
        wm, w_dx, w_dy = _bilinear_with_grad(self.width_smooth, px, py)
        wr = (wm - self.sw_px) * self.width_mask
        n_w = max(1.0, float(self.width_mask.sum()))
        e_wid = float(np.sum(wr**2)) / (n_w * unit_sq)
        g_px = g_px + self.width_weight * 2.0 * wr * w_dx / (n_w * unit_sq)
        g_py = g_py + self.width_weight * 2.0 * wr * w_dy / (n_w * unit_sq)

        # --- coverage: capped, over the WHOLE pair window (ICP-frozen) ---
        pts = np.column_stack([px, py])
        # One tree per evaluation, shared with the overlap term below — the
        # points are identical, and the build is the O(n log n) part.
        tree = cKDTree(pts)
        cdist, cidx = tree.query(self.cov_pts)
        n_cov = max(1, len(self.cov_pts))
        rho, dscale = _coverage_huber(cdist, self.cov_cap_px)
        e_cov = float(np.mean(rho)) / unit_sq
        e_cov_raw = float(np.mean(cdist**2)) / unit_sq
        diff = pts[cidx] - self.cov_pts
        safe = np.where(cdist > 0.0, cdist, 1.0)
        g_cov = np.zeros((n_s, 2))
        np.add.at(g_cov, cidx, (dscale / safe)[:, None] * diff / (n_cov * unit_sq))
        g_px = g_px + self.coverage_weight * g_cov[:, 0]
        g_py = g_py + self.coverage_weight * g_cov[:, 1]

        # --- cross-segment overlap: a pen does not write a stroke twice ---
        # Quadratic hinge on sample PAIRS of different segments closer than the
        # radius, seam bands exempt for ADJACENT segments (the §5 stub zone is
        # ink the hand really shares). The pair set is recomputed per
        # evaluation and piecewise-constant in the parameters — the same
        # a.e.-exact treatment as the coverage assignment above.
        e_ovl = 0.0
        if self.overlap_weight > 0.0:
            pairs = tree.query_pairs(self.overlap_radius_px, output_type="ndarray")
            if len(pairs):
                si, sj = self.seg_of_sample[pairs[:, 0]], self.seg_of_sample[pairs[:, 1]]
                keep = si != sj
                exempt = (np.abs(si - sj) == 1) & self.overlap_exempt[pairs[:, 0]] & self.overlap_exempt[pairs[:, 1]]
                pairs = pairs[keep & ~exempt]
            if len(pairs):
                dvec = pts[pairs[:, 0]] - pts[pairs[:, 1]]
                r = np.hypot(dvec[:, 0], dvec[:, 1])
                safe_r = np.where(r > 0.0, r, 1.0)
                h = self.overlap_radius_px - r
                e_ovl = float(np.sum(h**2)) / (n_s * unit_sq)
                pull = (-2.0 * h / safe_r)[:, None] * dvec / (n_s * unit_sq)
                g_ovl = np.zeros((n_s, 2))
                np.add.at(g_ovl, pairs[:, 0], pull)
                np.add.at(g_ovl, pairs[:, 1], -pull)
                g_px = g_px + self.overlap_weight * g_ovl[:, 0]
                g_py = g_py + self.overlap_weight * g_ovl[:, 1]

        # --- Tikhonov on the LETTER anchors only (binding constraint 3) ---
        e_reg = float(np.sum(self.reg_w * np.sum(deltas**2, axis=1))) / self.n_letter_anchors

        # --- connector curvature-CHANGE only (never distance to the Bézier) ---
        if self.smooth_op.shape[0]:
            r = self.smooth_op @ ap
            m_d2 = self.smooth_op.shape[0]
            e_smooth = float(np.sum(r**2)) / m_d2
        else:
            r = np.zeros((0, 2))
            m_d2 = 1
            e_smooth = 0.0

        f = (
            e_geo
            + self.width_weight * e_wid
            + self.coverage_weight * e_cov
            + self.lambda_reg * e_reg
            + self.smooth_weight * e_smooth
            + self.overlap_weight * e_ovl
        )
        terms = {
            "e_geo": e_geo,
            "e_wid": e_wid,
            "e_cov": e_cov,
            "e_cov_uncapped": e_cov_raw,
            "e_reg": e_reg,
            "e_smooth": e_smooth,
            "e_overlap": e_ovl,
            "f": f,
        }
        if not want_grad:
            return terms, None

        # Chain rule: samples → plan anchors → free anchors → parameters.
        g_plan = np.column_stack(
            [self.unit_px * (self.sampling_op.T @ g_px), -self.unit_px * (self.sampling_op.T @ g_py)]
        )
        if self.smooth_op.shape[0]:
            g_plan = g_plan + self.smooth_weight * 2.0 * (self.smooth_op.T @ r) / m_d2
        g_free = np.zeros_like(self.anchors_free)
        np.add.at(g_free, self.idx, g_plan)

        grad = np.empty_like(params)
        grad[0] = float(g_free[:, 0].sum())
        grad[1] = float(g_free[:, 1].sum())
        nb = self.n_blocks
        if nb:
            grad[2 : 2 + 2 * nb] = (self.block_op.T @ g_free).ravel()
        grad[2 + 2 * nb :] = (
            g_free + self.lambda_reg * 2.0 * self.reg_w[:, None] * deltas / self.n_letter_anchors
        ).ravel()
        return terms, grad

    def objective(self, params: np.ndarray) -> tuple[float, np.ndarray]:
        """Total energy and its exact gradient at `params`.

        `f = e_geo + w_wid·e_wid + w_cov·e_cov_capped + λ·e_reg_letters
             + μ·e_smooth_connector`, all on the SMOOTHED fields. Anchor
        gradients fold back through the index map with
        `np.add.at(g_free, idx, g_plan)`, so the shared seam anchors receive the
        contributions of both sides.
        """
        terms, grad = self._evaluate(np.asarray(params, dtype=float), want_grad=True)
        return terms["f"], np.zeros_like(params) if grad is None else grad

    def energy_terms(self, params: np.ndarray) -> dict[str, float]:
        """The individual (unweighted) energies at `params`, on the SMOOTHED
        fields — what the objective sees, split up for reporting and tests."""
        terms, _ = self._evaluate(np.asarray(params, dtype=float), want_grad=False)
        return terms

    # ------------------------------------------------------------- per-segment

    def report_energies(self, params: np.ndarray) -> list[ChainSegment]:
        """Per-segment residuals and gates on the UNSMOOTHED fields.

        Coverage is attributed by the KD query's nearest-sample index (sharper
        than `core.word_metric.score_word_segments`' x-span rule) and reported
        UNCAPPED; the gates are literally `core.fit.CONVERGED_GEO_RMSE_UNITS`
        and `CONVERGED_COVERAGE_RMSE_UNITS`, so a chain segment and a
        single-letter fit are judged by the same yardstick.

        **Two coverage gates, both reported** (issue #278 Stage-B precondition 1):
        `cov_rmse_px`/`converged` count every attributed point of the UNION pair
        window, `cov_rmse_local_px`/`converged_local` only those inside the
        segment's own `cov_window_px`. The union number grades a letter against
        connector ink the letter-local window of `analyze.trace_letter_ductus`
        never showed the baseline fit, so „chain converges at least as often" is
        only a like-for-like statement on the LOCAL gate. The fit itself is
        identical under both — the windows enter the report, never the objective.

        `fitted_anchors` come out in the COMPOSED word frame (initial anchors
        plus their per-anchor deltas, translations excluded exactly as
        `core.fit.FitResult.anchors` excludes its global shift); `fit_pair_chain`
        maps them back into the chart frame the templates were read from.
        """
        params = np.asarray(params, dtype=float)
        _, _, _, deltas = self.unpack(params)
        px, py = self.to_pixels(params)
        ox, oy = self.out_of_crop(px, py)
        d_eff = bilinear(self.dist_raw, px, py) + np.hypot(ox, oy)
        cdist, cidx = cKDTree(np.column_stack([px, py])).query(self.cov_pts)

        segments: list[ChainSegment] = []
        for spec, (a0, a1), (s0, s1) in zip(self.specs, self.anchor_slices, self.sample_slices, strict=True):
            geo_rmse = float(np.sqrt(np.mean(d_eff[s0:s1] ** 2))) if s1 > s0 else 0.0
            sel = (cidx >= s0) & (cidx < s1)
            n_cov = int(sel.sum())
            # A segment with NO attributed coverage point scores 0.0 and therefore
            # passes the coverage half of its gate on its own: an empty sum has no
            # residual, and inventing a failure here would punish e.g. a connector
            # whose ink the two letters happen to own entirely. The gate stays a
            # statement about the residual only — consumers that need "the segment
            # actually saw ink" (M2's `chain_connector_yielded`) MUST check
            # `n_cov > 0` separately.
            cov_rmse = float(np.sqrt(np.mean(cdist[sel] ** 2))) if n_cov else 0.0
            win = spec.cov_window_px
            if win is None:
                n_cov_local, cov_rmse_local = n_cov, cov_rmse
            else:
                sel_local = sel & (self.cov_pts[:, 0] >= win[0]) & (self.cov_pts[:, 0] <= win[1])
                n_cov_local = int(sel_local.sum())
                cov_rmse_local = float(np.sqrt(np.mean(cdist[sel_local] ** 2))) if n_cov_local else 0.0
            seg_deltas = deltas[a0:a1]
            max_delta = float(np.max(np.hypot(seg_deltas[:, 0], seg_deltas[:, 1]))) if a1 > a0 else 0.0
            fitted = self.anchors_free[a0:a1] + seg_deltas if spec.kind == "letter" else None
            segments.append(
                ChainSegment(
                    kind=spec.kind,
                    slot_index=spec.slot_index,
                    key=spec.key,
                    anchor_slice=(a0, a1),
                    sample_slice=(s0, s1),
                    fitted_anchors=fitted,
                    polyline_px=np.column_stack([px[s0:s1], py[s0:s1]]),
                    geo_rmse_px=geo_rmse,
                    cov_rmse_px=cov_rmse,
                    n_cov=n_cov,
                    cov_rmse_local_px=cov_rmse_local,
                    n_cov_local=n_cov_local,
                    converged=_segment_converged(geo_rmse, cov_rmse, self.unit_px),
                    converged_local=_segment_converged(geo_rmse, cov_rmse_local, self.unit_px),
                    max_anchor_delta=max_delta,
                )
            )
        return segments


# ------------------------------------------------------------------- assembly


def _seam_ownership(specs: Sequence[ChainSegmentSpec]) -> dict[tuple[int, int], tuple[int, int]]:
    """`{(borrower segment, local anchor): (owner segment, local anchor)}`.

    Each `seam_out`/`seam_in` pair collapses to ONE free anchor. The LETTER side
    owns it whenever exactly one side is a letter (the connector must not carry
    a copy of the glyph's own tail anchor), otherwise the earlier segment wins.
    """
    borrowed: dict[tuple[int, int], tuple[int, int]] = {}
    for i in range(len(specs) - 1):
        left, right = specs[i], specs[i + 1]
        if left.seam_out is None or right.seam_in is None:
            continue
        left_side, right_side = (i, int(left.seam_out)), (i + 1, int(right.seam_in))
        if right.kind == "letter" and left.kind != "letter":
            borrowed[left_side] = right_side
        else:
            borrowed[right_side] = left_side
    return borrowed


def build_chain_problem(
    specs: Sequence[ChainSegmentSpec],
    *,
    dist_smooth: np.ndarray,
    dist_raw: np.ndarray,
    width_smooth: np.ndarray,
    width_raw: np.ndarray,
    cov_pts: np.ndarray,
    unit_px: float,
    x_origin_px: float,
    baseline_y_px: float,
    crop_shape: tuple[int, int],
    n_samples: int | None = None,
    width_weight: float = DEFAULT_WIDTH_WEIGHT,
    coverage_weight: float = DEFAULT_COVERAGE_WEIGHT,
    lambda_reg: float = DEFAULT_LAMBDA_REG,
    smooth_weight: float = CHAIN_CONNECTOR_SMOOTH_WEIGHT,
    coverage_cap_units: float = CHAIN_COVERAGE_CAP_UNITS,
    overlap_weight: float | None = None,
    overlap_radius_units: float = CHAIN_OVERLAP_RADIUS_UNITS,
) -> _ChainProblem:
    """Assemble the chain optimisation problem. Pure: no I/O, no DB, no case.

    `specs` is a LIST in writing order — `[letter, connector, letter]` in Stage
    A, `[L0, C0, L1, C1, …]` in Stage B — and every rule below is written per
    segment, never per "left/right".

    Assembly:

    * **Index map.** Free anchors are the concatenated per-segment anchors MINUS
      the anchors a neighbour owns: each `seam_out`/`seam_in` pair collapses to
      ONE free anchor, and `anchors_plan = anchors_free[idx]` re-expands it, so
      seam continuity is exact by construction rather than penalised.
    * **Sampling.** `core.template.build_sample_plan` over the concatenated
      `stroke_starts` / `corner_anchors` of the whole chain — a chain is sampled
      exactly as a multi-stroke glyph is; `n_samples` defaults to
      `core.fit.DEFAULT_N_SAMPLES / 120 × K_plan` (≈ 1.5 per anchor).
    * **Parameters.** `[tx, ty, (dx, dy) per slot block…, δ per free anchor…]`.
      Slot blocks are keyed by `slot_index` and unregularised, bounded by
      `analyze.FIT_DX_UNITS` / `FIT_DY_UNITS` so chain and independent grid
      search enjoy identical placement freedom. A connector gets NO block of its
      own — it rides the arc-length ramp `t(s_i) = (1 − s_i)·t_prev + s_i·t_next`
      between its neighbours (linear, hence exact gradient); a third block would
      double-count placement.
    * **Bounds.** `core.fit.MAX_ANCHOR_DELTA` on letter anchors,
      `CHAIN_CONNECTOR_MAX_DELTA` on connector interiors,
      `max(crop_h, crop_w) / unit_px` on the global shift.
    * **Coverage.** `cov_pts` are the caller's union-window skeleton points,
      subsampled to `CHAIN_COVERAGE_PER_SEGMENT × len(specs)`; the objective
      applies the Huber cap `coverage_cap_units · unit_px`, ICP-frozen assignment.
      A spec's optional `cov_window_px` narrows only the REPORTED per-segment
      coverage gate (see `report_energies`), never the targets the objective sees.
    * **Weights.** `reg_w` is 1 on letter anchors, 0 on connector interiors
      (binding constraint 3), normalised by the letter-anchor count so per-letter
      Tikhonov pressure equals a single-letter fit's; `width_mask` is 0 on
      connector samples, which have no stored width measurement.

    Fields arrive already prepared (smoothed with `core.fit.DIST_FIELD_SIGMA_PX`
    / `WIDTH_FIELD_SIGMA_PX`, raw kept for the report), so the problem stays
    testable against a synthetic 60×60 EDT.
    """
    specs = [
        ChainSegmentSpec(
            kind=s.kind,
            anchors=np.asarray(s.anchors, dtype=float).reshape(-1, 2),
            slot_index=s.slot_index,
            key=s.key,
            stroke_starts=tuple(int(v) for v in (s.stroke_starts or (0,))),
            corner_anchors=tuple(int(v) for v in (s.corner_anchors or ())),
            half_widths=None if s.half_widths is None else np.asarray(s.half_widths, dtype=float),
            seam_in=s.seam_in,
            seam_out=s.seam_out,
            cov_window_px=None if s.cov_window_px is None else (float(s.cov_window_px[0]), float(s.cov_window_px[1])),
        )
        for s in specs
    ]
    if not specs:
        raise ValueError("a chain needs at least one segment")
    if unit_px <= 0:
        raise ValueError(f"unit_px must be positive, got {unit_px}")
    if CHAIN_COVERAGE_PER_SEGMENT < MAX_COVERAGE_POINTS:
        # Invariant: the chain's coverage density per unit of skeleton x-extent
        # must never fall below the single-letter fit's (plan §2.5).
        raise ValueError(
            f"CHAIN_COVERAGE_PER_SEGMENT ({CHAIN_COVERAGE_PER_SEGMENT}) must not be thinner than "
            f"core.fit.MAX_COVERAGE_POINTS ({MAX_COVERAGE_POINTS})"
        )

    # ---- free anchors + index map (the seam is a shared parameter) ----
    borrowed = _seam_ownership(specs)
    free_index: dict[tuple[int, int], int] = {}
    anchor_slices: list[tuple[int, int]] = []
    anchors_free_rows: list[np.ndarray] = []
    reg_rows: list[float] = []
    hw_rows: list[float] = []
    cursor = 0
    for i, spec in enumerate(specs):
        start = cursor
        for j in range(len(spec.anchors)):
            if (i, j) in borrowed:
                continue
            free_index[(i, j)] = cursor
            anchors_free_rows.append(spec.anchors[j])
            reg_rows.append(1.0 if spec.kind == "letter" else 0.0)
            hw_rows.append(float(spec.half_widths[j]) if spec.half_widths is not None else 0.0)
            cursor += 1
        anchor_slices.append((start, cursor))
    anchors_free = np.asarray(anchors_free_rows, dtype=float).reshape(-1, 2)
    reg_w = np.asarray(reg_rows, dtype=float)
    half_widths_free = np.asarray(hw_rows, dtype=float)
    k_free = len(anchors_free)

    idx_rows: list[int] = []
    plan_slices: list[tuple[int, int]] = []
    plan_cursor = 0
    for i, spec in enumerate(specs):
        plan_slices.append((plan_cursor, plan_cursor + len(spec.anchors)))
        plan_cursor += len(spec.anchors)
        for j in range(len(spec.anchors)):
            owner = borrowed.get((i, j), (i, j))
            idx_rows.append(free_index[owner])
    idx = np.asarray(idx_rows, dtype=int)
    anchors_plan0 = anchors_free[idx]
    k_plan = len(idx)

    # ---- sampling plan over the whole chain (a chain is a multi-stroke glyph)
    stroke_starts_plan: list[int] = []
    corner_anchors_plan: list[int] = []
    for spec, (p0, _) in zip(specs, plan_slices, strict=True):
        if spec.kind == "letter":
            stroke_starts_plan += [p0 + int(s) for s in spec.stroke_starts if 0 <= int(s) < len(spec.anchors)]
        else:
            stroke_starts_plan.append(p0)
        corner_anchors_plan += [p0 + int(c) for c in spec.corner_anchors if 0 <= int(c) < len(spec.anchors)]
    stroke_starts_plan = sorted(set(stroke_starts_plan) | {0})

    if n_samples is None:
        n_samples = int(round(DEFAULT_N_SAMPLES / _REFERENCE_ANCHOR_COUNT * k_plan))
    n_samples = max(2 * len(stroke_starts_plan), int(n_samples))
    plan = build_sample_plan(anchors_plan0, stroke_starts_plan, corner_anchors_plan, n_samples)
    sampling_op = _sampling_operator(anchors_plan0, plan)
    sw_px = (_width_operator(anchors_plan0, plan) @ half_widths_free[idx]) * unit_px
    n_s = sampling_op.shape[0]

    # ---- per-sample segment attribution (segments own contiguous plan ranges)
    seg_of_row: list[int] = []
    stroke_of_row: list[int] = []
    for (a, _), m in zip(plan.slices, plan.alloc, strict=True):
        seg = next(i for i, (p0, p1) in enumerate(plan_slices) if p0 <= a < p1)
        seg_of_row += [seg] * m
        # Which pen stroke of the whole chain this plan row belongs to — the
        # same bounds `build_sample_plan` sampled between, so no sample ever
        # bridges a pen lift.
        stroke_of_row += [bisect.bisect_right(stroke_starts_plan, a) - 1] * m
    seg_of_sample = (
        np.delete(np.asarray(seg_of_row, dtype=int), plan.drop_rows)
        if plan.drop_rows
        else np.asarray(seg_of_row, dtype=int)
    )
    stroke_of_sample = (
        np.delete(np.asarray(stroke_of_row, dtype=int), plan.drop_rows)
        if plan.drop_rows
        else np.asarray(stroke_of_row, dtype=int)
    )
    sample_slices: list[tuple[int, int]] = []
    for i in range(len(specs)):
        where = np.flatnonzero(seg_of_sample == i)
        sample_slices.append((int(where[0]), int(where[-1]) + 1) if len(where) else (0, 0))
    width_mask = np.zeros(n_s)
    for i, spec in enumerate(specs):
        if spec.kind == "letter" and spec.half_widths is not None:
            s0, s1 = sample_slices[i]
            width_mask[s0:s1] = 1.0

    # ---- slot translation blocks + the connector's arc-length ramp ----
    slot_order = [s.slot_index for s in specs if s.kind == "letter" and s.slot_index is not None]
    slot_blocks = {slot: 2 + 2 * j for j, slot in enumerate(dict.fromkeys(slot_order))}
    block_col = {slot: j for j, slot in enumerate(dict.fromkeys(slot_order))}
    block_op = np.zeros((k_free, len(block_col)))
    ramp_rows: list[float] = []
    for i, spec in enumerate(specs):
        a0, a1 = anchor_slices[i]
        if spec.kind == "letter":
            if spec.slot_index is not None:
                block_op[a0:a1, block_col[spec.slot_index]] = 1.0
            continue
        prev_slot = next((specs[j].slot_index for j in range(i - 1, -1, -1) if specs[j].kind == "letter"), None)
        next_slot = next((specs[j].slot_index for j in range(i + 1, len(specs)) if specs[j].kind == "letter"), None)
        seg = np.diff(spec.anchors, axis=0)
        arcs = np.concatenate([[0.0], np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))])
        total = arcs[-1] if arcs[-1] > 0 else 1.0
        s_of_local = arcs / total
        for j in range(len(spec.anchors)):
            row = free_index.get((i, j))
            if row is None:  # a seam anchor: the neighbouring letter's block owns it
                continue
            s = float(s_of_local[j])
            ramp_rows.append(s)
            if prev_slot is not None and next_slot is not None:
                block_op[row, block_col[prev_slot]] = 1.0 - s
                block_op[row, block_col[next_slot]] = s
            elif prev_slot is not None:
                block_op[row, block_col[prev_slot]] = 1.0
            elif next_slot is not None:
                block_op[row, block_col[next_slot]] = 1.0
    ramp = np.asarray(ramp_rows, dtype=float)

    # ---- connector curvature-change operator (over its PLAN block) ----
    smooth_rows = np.zeros((0, k_plan))
    blocks: list[np.ndarray] = []
    for i, spec in enumerate(specs):
        if spec.kind == "letter":
            continue
        p0, p1 = plan_slices[i]
        d2 = _second_difference_operator(anchors_plan0[p0:p1])
        if not d2.shape[0]:
            continue
        block = np.zeros((d2.shape[0], k_plan))
        block[:, p0:p1] = d2
        blocks.append(block)
    if blocks:
        smooth_rows = np.vstack(blocks)

    # ---- coverage targets over the whole pair window ----
    cov_pts = np.asarray(cov_pts, dtype=float).reshape(-1, 2)
    n_cov_max = CHAIN_COVERAGE_PER_SEGMENT * len(specs)
    if len(cov_pts) > n_cov_max:
        cov_pts = cov_pts[np.linspace(0, len(cov_pts) - 1, n_cov_max).astype(int)]

    # ---- seam bands for the overlap term (structural: INIT geometry only) ----
    # A sample is "in band" when the initial layout puts it within the §5
    # stub-replacement reach of a seam its segment participates in. Adjacent
    # segments legitimately share ink there; the exclusivity term must not
    # bill the very overlap the hand actually writes. Computed from the init
    # samples, so the mask is parameter-independent and the objective's
    # analytic gradient stays exact.
    s_xy0 = np.column_stack([sampling_op @ anchors_plan0[:, 0], sampling_op @ anchors_plan0[:, 1]])
    overlap_exempt = np.zeros(n_s, dtype=bool)
    for i, spec in enumerate(specs):
        if spec.kind != "connector":
            continue
        c0, c1 = sample_slices[i]
        if c1 <= c0:
            continue
        for seam_pt, neighbour in ((s_xy0[c0], i - 1), (s_xy0[c1 - 1], i + 1)):
            for j in (i, neighbour):
                if not (0 <= j < len(specs)):
                    continue
                j0, j1 = sample_slices[j]
                if j1 <= j0:
                    continue
                near = np.hypot(*(s_xy0[j0:j1] - seam_pt).T) < CHAIN_OVERLAP_SEAM_EXEMPT_UNITS
                overlap_exempt[j0:j1] |= near

    crop_h, crop_w = int(crop_shape[0]), int(crop_shape[1])
    max_shift_units = float(max(crop_h, crop_w)) / unit_px
    bounds: list[tuple[float, float]] = [(-max_shift_units, max_shift_units)] * 2
    bounds += [(-FIT_DX_UNITS, FIT_DX_UNITS), (-FIT_DY_UNITS, FIT_DY_UNITS)] * len(block_col)
    for i, spec in enumerate(specs):
        a0, a1 = anchor_slices[i]
        cap = MAX_ANCHOR_DELTA if spec.kind == "letter" else CHAIN_CONNECTOR_MAX_DELTA
        bounds += [(-cap, cap)] * (2 * (a1 - a0))
    x0 = np.zeros(2 + 2 * len(block_col) + 2 * k_free)

    return _ChainProblem(
        specs=specs,
        anchors_free=anchors_free,
        idx=idx,
        anchor_slices=anchor_slices,
        sample_slices=sample_slices,
        slot_blocks=slot_blocks,
        ramp=ramp,
        reg_w=reg_w,
        width_mask=width_mask,
        sampling_op=sampling_op,
        sw_px=sw_px,
        dist_raw=np.asarray(dist_raw, dtype=float),
        dist_smooth=np.asarray(dist_smooth, dtype=float),
        width_raw=np.asarray(width_raw, dtype=float),
        width_smooth=np.asarray(width_smooth, dtype=float),
        cov_pts=cov_pts,
        unit_px=float(unit_px),
        x_origin_px=float(x_origin_px),
        baseline_y_px=float(baseline_y_px),
        crop_h=crop_h,
        crop_w=crop_w,
        cov_cap_px=float(coverage_cap_units * unit_px),
        width_weight=float(width_weight),
        coverage_weight=float(coverage_weight),
        lambda_reg=float(lambda_reg),
        smooth_weight=float(smooth_weight),
        overlap_weight=float(CHAIN_OVERLAP_WEIGHT if overlap_weight is None else overlap_weight),
        overlap_radius_px=float(overlap_radius_units * unit_px),
        overlap_exempt=overlap_exempt,
        x0=x0,
        bounds=bounds,
        block_op=block_op,
        smooth_op=smooth_rows,
        plan_slices=plan_slices,
        n_letter_anchors=max(1.0, float(reg_w.sum())),
        n_samples=n_s,
        seg_of_sample=seg_of_sample,
        stroke_of_sample=stroke_of_sample,
    )


# ------------------------------------------------------------- one occurrence


def _slots_join(s0: GlyphSlot, s1: GlyphSlot) -> bool:
    """Is there a written Übergang between these two adjacent slots?

    The adjacency predicate of `analyze.find_occurrences` and
    `pairlab.harvest._adjacent_joined`, verbatim: no space on either side, a
    glyph key on both, and both of the detached-class flags clear (a digit or a
    punctuation mark renders but no Übergang ever enters or leaves it —
    architektur.md §4). Mirrored rather than imported so `chain` keeps depending
    on nothing above itself.
    """
    return not (s0.space or s1.space or not s0.key or not s1.key or not (s0.joins and s1.joins))


def chain_runs(case: WordCase) -> list[list[int]]:
    """The case's keyed slots partitioned into maximal runs of JOINED neighbours.

    Every keyed, non-space slot appears in exactly one run, in writing order —
    so the runs are a partition of what a word-level harvest has to fit, not a
    selection from it. A run breaks wherever `_slots_join` says the pen lifts:
    at a space, at a keyless slot, and around a detached glyph (a digit is a run
    of its own). A lone letter is therefore a one-slot run, which
    `fit_word_chain` fits as a one-segment chain rather than skipping.
    """
    runs: list[list[int]] = []
    current: list[int] = []
    for i, slot in enumerate(case.slots):
        if slot.space or not slot.key:
            if current:
                runs.append(current)
                current = []
            continue
        if current and current[-1] == i - 1 and _slots_join(case.slots[i - 1], slot):
            current.append(i)
            continue
        if current:
            runs.append(current)
        current = [i]
    if current:
        runs.append(current)
    return runs


def _letter_spec(case: WordCase, result: WordDeriveResult, slot_index: int) -> tuple[ChainSegmentSpec, float] | None:
    """One letter as a chain segment, plus the chart→composed x offset.

    The chart row (variant 0) is shifted into word coordinates by the composed
    placement, recovered with `analyze.trace_letter_ductus`' EXACT four lines —
    including its known Laufform wrinkle (a flowing run may compose the running
    form, whose first sample is not the chart row's): the residual offset is
    absorbed by the fit's global translation, and preserving the wrinkle keeps
    chain and baseline on ONE initialisation so the shape-delta metric stays
    honest (plan §2.7).
    """
    slot = case.slots[slot_index]
    row = case.templates.get(slot.key) if slot.key else None
    items = _body_items(result, slot_index)
    if row is None or not items:
        return None
    anchors = np.asarray(row["anchors"], dtype=float)
    if len(anchors) < 2:
        return None
    half_widths = np.asarray(row["half_widths"], dtype=float)
    meta = row.get("trace_meta") or {}

    payload = result.payloads.get(slot.key) or {}
    first_template = (payload.get("centerlines_template") or [[[0.0, 0.0]]])[0][0]
    first_item = items[0]["centerline"][0]
    dx = first_item[0] - first_template[0]

    offset = dx - float(anchors[0, 0])  # composed_x = chart_x + offset
    placed = anchors.copy()
    placed[:, 0] += offset
    stroke_starts = [int(s) for s in (meta.get("stroke_starts") or [0])]
    cut_in, cut_out = _letter_cut_anchors(placed, stroke_starts)
    spec = ChainSegmentSpec(
        kind="letter",
        anchors=placed,
        slot_index=slot_index,
        key=slot.key,
        stroke_starts=stroke_starts,
        corner_anchors=[int(c) for c in (meta.get("corner_anchors") or [])],
        half_widths=half_widths,
        seam_in=cut_in,
        seam_out=cut_out,
    )
    return spec, offset


def _connector_spec(result: WordDeriveResult, slot_a: int) -> ChainSegmentSpec | None:
    """The generated join between slots `slot_a` and `slot_a + 1` as a segment.

    `analyze._generate_connector` at the COMPOSED placement, read in the same
    body-endpoint frame `analyze.dissect_occurrence` and
    `tools.wordbench.pairmeas._body_lines` use, with NO overlap extension, NO
    capital retrace prefix and NO entry trim — the trimmed lead-in stub is
    exactly the ownership question the seam calibration measures, so the chain
    must see it. The generated SHAPE is used verbatim; only the point COUNT is
    repaired where the chord leaves no room for all of them
    (`regularise_connector_anchors`). This is the INITIALISATION, never a
    target: no penalty term ever measures the fitted connector against it.

    Deliberately free of `JoinDissection` — a word chain has one of these per
    join and no dissection anywhere.
    """
    a_items = _body_items(result, slot_a)
    b_items = _body_items(result, slot_a + 1)
    if not a_items or not b_items:
        return None
    a_line = a_items[-1]["centerline"]
    b_line = b_items[0]["centerline"]
    exit_deg = _endpoint_tangent([tuple(p) for p in a_line], at_end=True)
    entry_deg = _endpoint_tangent([tuple(p) for p in b_line], at_end=False)
    conn = np.asarray(
        _generate_connector(tuple(a_line[-1]), exit_deg, tuple(b_line[0]), entry_deg), dtype=float
    ).reshape(-1, 2)
    if len(conn) < 3:
        return None
    conn = regularise_connector_anchors(conn)
    return ChainSegmentSpec(kind="connector", anchors=conn, seam_in=0, seam_out=len(conn) - 1)


def _prepare_fields(case: WordCase, x_lo: float, x_hi: float) -> dict | None:
    """The chain's distance and width fields over the crop columns `[x_lo, x_hi]`.

    The band is the UNION of the run's per-letter coverage windows: the chain
    must own the ink between its letters, so cutting per letter (as the
    independent trace does) would hide exactly the transition it measures.
    Returned as the keyword block `build_chain_problem` takes — smoothed with
    `core.fit`'s own sigmas, the raw fields kept for the per-segment report.
    None when the band holds no skeleton pixel at all.
    """
    cols = np.arange(case.skel.shape[1])
    keep = (cols >= x_lo) & (cols <= x_hi)
    skel_local = case.skel & keep[None, :]
    if not skel_local.any():
        return None
    width_local = np.where(keep[None, :], case.width_map, 0.0)
    dist_raw = distance_transform_edt(~skel_local).astype(float)
    _, ink_idx = distance_transform_edt(~np.asarray(width_local > 0), return_indices=True)
    width_raw = width_local[ink_idx[0], ink_idx[1]].astype(float)
    return {
        "dist_raw": dist_raw,
        "dist_smooth": gaussian_filter(dist_raw, DIST_FIELD_SIGMA_PX),
        "width_raw": width_raw,
        "width_smooth": gaussian_filter(width_raw, WIDTH_FIELD_SIGMA_PX),
        "cov_pts": _skeleton_points(skel_local),
        "crop_shape": skel_local.shape,
    }


def _stroke_polylines_px(problem: _ChainProblem, px: np.ndarray, py: np.ndarray) -> list[dict]:
    """The fitted chain cut back into pen-down polylines (crop px), in order.

    One entry per maximal run of samples sharing a segment AND a pen stroke: a
    letter written with a pen lift inside it yields one entry per stroke, a
    connector exactly one. Runs are additionally cut at segment boundaries, so
    an entry always names one segment — a caller wanting the continuous pen path
    across a seam concatenates neighbours (they meet exactly: the seam anchor is
    one shared parameter).
    """
    seg = np.asarray(problem.seg_of_sample, dtype=int)
    stroke = np.asarray(problem.stroke_of_sample, dtype=int)
    if not len(seg) or len(seg) != len(px) or len(stroke) != len(seg):
        return []
    cuts = np.flatnonzero((np.diff(seg) != 0) | (np.diff(stroke) != 0)) + 1
    bounds = [0, *cuts.tolist(), len(seg)]
    per_segment: dict[int, int] = {}
    out: list[dict] = []
    for a, b in zip(bounds[:-1], bounds[1:], strict=True):
        i = int(seg[a])
        spec = problem.specs[i]
        n = per_segment.get(i, 0)
        per_segment[i] = n + 1
        out.append(
            {
                "kind": spec.kind,
                "segment_index": i,
                "slot_index": spec.slot_index,
                "key": spec.key,
                "stroke_index": n,
                "points_px": np.column_stack([px[a:b], py[a:b]]),
            }
        )
    return out


def fit_word_chain(
    case: WordCase,
    slots: Sequence[int],
    *,
    result: WordDeriveResult,
    windows_px: dict[int, tuple[float, float]],
    slot_shift_init: dict[int, tuple[float, float]] | None = None,
) -> ChainWordFit | None:
    """Fit a run of consecutive slots as ONE chain `[L, C, L, C, …]`.

    The Stage-B generalisation of `fit_pair_chain` (which is now a two-slot
    wrapper over this): every letter of the run is a segment with its own
    unregularised translation block, every join between them is a
    form-unregularised connector segment welded to its neighbours by a shared
    seam anchor, and one L-BFGS-B solve moves all of them at once. A one-slot
    run is a legitimate chain of one segment with no connector at all.

    * **Frame.** The metric's own registration — `x_origin_px = result.registration["tx"]`,
      `baseline_y_px = result.baseline_row + result.registration["ty"]`,
      `unit_px = result.xh_px` — so chain, independent trace and
      `tools.wordbench.pairmeas` all live in one frame.
    * **Initialisation.** Chart-row anchors (variant 0) shifted by the composed
      placement (`_letter_spec`, including its known Laufform wrinkle, preserved
      on purpose so chain and baseline share one init) and the generated
      connectors at that same placement (`_connector_spec`).
    * **Seams.** Per join: the last anchor of the left letter's last
      NON-diacritic stroke and the first anchor of the right letter's first
      non-diacritic stroke (`_letter_cut_anchors`, the diacritic rule of
      `analyze.trace_letter_ductus`) become ONE shared parameter each.
    * **`windows_px`** maps a slot index to the crop-pixel column window its
      coverage GATE is read in — for `fit_pair_chain` the two letter-local
      windows of `analyze.trace_letter_ductus`, for a word-level caller the
      window around its own per-slot grid fit. Their UNION is the band the fit
      itself sees (`_prepare_fields`); a slot without an entry keeps the union
      gate. With no window at all there is no band to cut and the call returns
      None — the caller's placement diagnosis is what decides the fallback.
    * **`result`** is required: a word with five joins must compose itself once,
      not once per run.
    * **`slot_shift_init`** (xh units, per slot) seeds a slot's translation
      BLOCK away from zero. The default None keeps the historical start — every
      block at the composed placement. The round-2 adjudication showed why a
      caller wants this: on high-exit joins the composed start sits in a basin
      where stacking the two letters lets their strokes claim the connector's
      ink, the solve collapses the pair's ink gap to zero although the specimen
      ink runs forward, and the connector doubles back (the placement collapse
      of uebergaenge-befund.md §5c). Seeding each block at the letter's OWN
      grid placement starts the descent where the letter's ink actually is —
      the OBJECTIVE is untouched, so this changes which basin is entered, never
      what is measured. Values are clipped just inside the block bounds so a
      seed can never start a solve already at `slot_at_bound`.

    None whenever the chain cannot be built at all — an unfitted composition, a
    slot without a template or composed body strokes, a join whose connector
    degenerates, or a coverage band without ink. A run of non-consecutive slots
    is a caller bug and raises.
    """
    started = time.perf_counter()
    run = [int(s) for s in slots]
    if not run or any(b != a + 1 for a, b in zip(run[:-1], run[1:], strict=True)):
        raise ValueError(f"fit_word_chain needs a run of CONSECUTIVE slots, got {list(slots)!r}")
    if case.skel is None or case.width_map is None:
        return None
    if result.composed["missing"] or result.report is None or result.report.get("failed"):
        return None
    if run[0] < 0 or run[-1] >= len(case.slots):
        return None

    xh = float(result.xh_px)
    tx, ty = float(result.registration["tx"]), float(result.registration["ty"])
    x_origin_px = tx
    baseline_y_px = float(result.baseline_row) + ty

    # ---- the chain in writing order: letter, join, letter, join, letter … ----
    specs: list[ChainSegmentSpec] = []
    offsets: dict[int, float] = {}
    for n, slot_index in enumerate(run):
        made = _letter_spec(case, result, slot_index)
        if made is None:
            return None
        spec, offset = made
        window = windows_px.get(slot_index)
        spec.cov_window_px = None if window is None else (float(window[0]), float(window[1]))
        if n:
            conn = _connector_spec(result, run[n - 1])
            if conn is None:
                return None
            specs.append(conn)
        specs.append(spec)
        offsets[slot_index] = offset

    # The fit runs against the UNION window (owning the joins' ink is the whole
    # point); the per-letter windows above stay on the specs, where they narrow
    # the REPORTED gate only.
    wins = [w for w in (windows_px.get(s) for s in run) if w is not None]
    if not wins:
        return None
    fields = _prepare_fields(case, min(float(w[0]) for w in wins), max(float(w[1]) for w in wins))
    if fields is None:
        return None

    problem = build_chain_problem(specs, unit_px=xh, x_origin_px=x_origin_px, baseline_y_px=baseline_y_px, **fields)
    # Seed the translation blocks BEFORE the initial energies, so `e0` states
    # the energy of the start the solve actually descends from. Clipped just
    # inside the bounds: the `slot_at_bound` check reads |dx| >= bound - 1e-9,
    # and a seed must not be able to pre-trip it.
    applied_seed: dict[int, tuple[float, float]] = {}
    for slot_index, (sx, sy) in (slot_shift_init or {}).items():
        offset_ix = problem.slot_blocks.get(int(slot_index))
        if offset_ix is None:
            continue
        cx = float(np.clip(sx, -(FIT_DX_UNITS - 1e-6), FIT_DX_UNITS - 1e-6))
        cy = float(np.clip(sy, -(FIT_DY_UNITS - 1e-6), FIT_DY_UNITS - 1e-6))
        problem.x0[offset_ix] = cx
        problem.x0[offset_ix + 1] = cy
        # 6 decimals, not 4: the clip parks a wild seed 1e-6 INSIDE the bound,
        # and the record must show that property instead of rounding onto it.
        applied_seed[int(slot_index)] = (round(cx, 6), round(cy, 6))
    e0 = problem.energy_terms(problem.x0)
    res = minimize(
        problem.objective,
        problem.x0,
        jac=True,
        method="L-BFGS-B",
        bounds=problem.bounds,
        # `maxfun` stays 50x the iteration budget, as in
        # `core.fit.fit_template_to_instance`: with the analytic jacobian the
        # EVALUATION budget must never be the binding stop.
        options={"maxiter": CHAIN_MAX_ITER, "maxfun": 50 * CHAIN_MAX_ITER},
    )

    segments = problem.report_energies(res.x)
    # Letters report in the chart frame the templates were read from (the
    # composed placement offset removed), so a caller can difference them
    # against `DuctusTrace.fr.anchors` anchor for anchor.
    for seg in segments:
        if seg.fitted_anchors is not None and seg.slot_index is not None:
            seg.fitted_anchors = seg.fitted_anchors - np.array([offsets[seg.slot_index], 0.0])

    _, _, blocks, _ = problem.unpack(res.x)
    slot_shift = {slot: (float(blocks[j, 0]), float(blocks[j, 1])) for j, slot in enumerate(problem.slot_blocks)}
    at_bound = {
        slot: bool(abs(dx) >= FIT_DX_UNITS - 1e-9 or abs(dy) >= FIT_DY_UNITS - 1e-9)
        for slot, (dx, dy) in slot_shift.items()
    }
    px, py = problem.to_pixels(res.x)
    connector_units = [
        np.column_stack([(px[s0:s1] - x_origin_px) / xh, (baseline_y_px - py[s0:s1]) / xh])
        for s0, s1 in (seg.sample_slice for seg in segments if seg.kind == "connector")
    ]
    # Letters sit at the even positions of `specs`, so join `j` welds
    # `specs[2j]`'s exit seam to `specs[2j + 2]`'s entry seam.
    cut_indices = [(int(specs[k].seam_out), int(specs[k + 2].seam_in)) for k in range(0, len(specs) - 2, 2)]
    letters = [seg for seg in segments if seg.kind == "letter"]
    connectors = [seg for seg in segments if seg.kind == "connector"]
    terms = problem.energy_terms(res.x)

    return ChainWordFit(
        case=case,
        slots=run,
        segments=segments,
        slot_shift_units=slot_shift,
        slot_at_bound=at_bound,
        global_shift_units=(float(res.x[0]), float(res.x[1])),
        cut_indices=cut_indices,
        connector_units=connector_units,
        stroke_polylines_px=_stroke_polylines_px(problem, px, py),
        converged=bool(letters) and all(seg.converged for seg in letters),
        converged_local=bool(letters) and all(seg.converged_local for seg in letters),
        fit_meta={
            "optimizer_success": bool(res.success),
            "message": str(res.message),
            "iterations": int(res.nit),
            # Whether the BUDGET stopped the solve rather than a convergence
            # criterion — L-BFGS-B status 1 is exactly that stop (iteration OR
            # evaluation limit; 0 is convergence, 2 an abnormal abort). NOT
            # `nit >= CHAIN_MAX_ITER`, which would also accuse a solve that
            # legitimately converges on the final allowed iteration. Read it
            # before believing any geometry below: a capped solve was still
            # descending, so its energies, its gates and the anchors it hands
            # the harvest are a snapshot of an unfinished descent, and where
            # that snapshot lands moves with the init.
            "hit_iteration_cap": int(res.status) == 1,
            "max_iter": CHAIN_MAX_ITER,
            "n_evaluations": int(res.nfev),
            "n_params": int(len(problem.x0)),
            "n_anchors_free": int(len(problem.anchors_free)),
            "n_anchors_plan": int(len(problem.idx)),
            "n_samples": int(problem.n_samples),
            "n_cov": int(len(problem.cov_pts)),
            "connector_converged": bool(all(seg.converged for seg in connectors)) if connectors else None,
            "cov_window_px": {
                str(slot): [round(float(v), 1) for v in windows_px[slot]] for slot in run if slot in windows_px
            },
            "energies": {k: round(v, 6) for k, v in terms.items()},
            "energies_initial": {k: round(v, 6) for k, v in e0.items()},
            "geo_rmse_px": {s.key or s.kind: round(s.geo_rmse_px, 3) for s in segments},
            "cov_rmse_px": {s.key or s.kind: round(s.cov_rmse_px, 3) for s in segments},
            "cov_rmse_local_px": {s.key or s.kind: round(s.cov_rmse_local_px, 3) for s in segments},
            "slot_shift_init": {str(k): list(v) for k, v in applied_seed.items()},
            "smooth_weight": problem.smooth_weight,
            "overlap_weight": problem.overlap_weight,
            "coverage_cap_px": round(problem.cov_cap_px, 3),
            "seconds": round(time.perf_counter() - started, 3),
            "slots": run,
        },
    )


def fit_pair_chain(
    case: WordCase, slot_a: int, dissection: JoinDissection, *, result: WordDeriveResult | None = None
) -> ChainFit | None:
    """Fit the `slot_a → slot_a + 1` join of `case` as one chain. None when the
    composition is missing a template or the join has no usable initialisation.

    The two-slot case of `fit_word_chain`, kept as its own entry point because
    the pair harness (`tools.pairlab.chainbench`) is written against exactly
    this shape: `ChainFit` carries ONE `cut_indices` tuple and ONE connector
    instead of a list per join. Everything the model does — frame,
    initialisation, seams, gates — lives in `fit_word_chain`; this wrapper only
    reads the two coverage windows off the dissection and narrows the result.

    * **Gates.** The fit sees the UNION window; each letter additionally carries
      its own `analyze.trace_letter_ductus` window as `cov_window_px`, so
      `ChainSegment.converged_local` / `ChainFit.converged_local` grade it on the
      same ink the independent M4 trace was graded on (Stage-B precondition 1).
    * **`result`** may be passed in to reuse a `derive_word` already computed for
      this case — a word with five joins must not compose itself five times.

    `dissection` supplies the baseline this fit is measured against and the
    per-occurrence geometry (independent fits, ink extents, the specimen's own
    join) the harness pairs with the chain's segments. Only its two letter fits'
    `body_px` and its cached composition are read here.
    """
    # The dissection already composed this case; reuse it rather than compose
    # the word a second time (and a fifth time for a word with five joins).
    if result is None:
        result = dissection.result if dissection is not None else derive_word(case)
    if case.skel is None or case.width_map is None:
        return None
    if result.composed["missing"] or result.report is None or result.report.get("failed"):
        return None
    if not 0 <= slot_a < len(case.slots) - 1:
        return None

    # The two letter-local windows of `trace_letter_ductus`, at the INDEPENDENT
    # placements the dissection found. `fit_word_chain` closes the hole between
    # them for the fit itself and keeps each one as its letter's reported gate.
    xh = float(result.xh_px)
    body_a = np.vstack(dissection.a.body_px)
    body_b = np.vstack(dissection.b.body_px)
    win_a = (float(body_a[:, 0].min()) - TRACE_WINDOW_MARGIN * xh, float(body_a[:, 0].max()) + TRACE_WINDOW_MARGIN * xh)
    win_b = (float(body_b[:, 0].min()) - TRACE_WINDOW_MARGIN * xh, float(body_b[:, 0].max()) + TRACE_WINDOW_MARGIN * xh)

    fit = fit_word_chain(case, [slot_a, slot_a + 1], result=result, windows_px={slot_a: win_a, slot_a + 1: win_b})
    if fit is None or not fit.cut_indices or not fit.connector_units:
        return None

    meta = dict(fit.fit_meta)
    # The pair harness reads the windows as left/right, not per slot index.
    meta["cov_window_px"] = {"left": [round(v, 1) for v in win_a], "right": [round(v, 1) for v in win_b]}
    return ChainFit(
        case=case,
        slot_a=slot_a,
        segments=fit.segments,
        slot_shift_units=fit.slot_shift_units,
        slot_at_bound=fit.slot_at_bound,
        global_shift_units=fit.global_shift_units,
        cut_indices=fit.cut_indices[0],
        connector_units=fit.connector_units[0],
        converged=fit.converged,
        converged_local=fit.converged_local,
        fit_meta=meta,
    )


__all__ = [
    "CHAIN_CONNECTOR_ANCHOR_SPACING_UNITS",
    "CHAIN_CONNECTOR_MAX_DELTA",
    "CHAIN_CONNECTOR_MIN_SPAN_UNITS",
    "CHAIN_CONNECTOR_SMOOTH_WEIGHT",
    "CHAIN_COVERAGE_CAP_UNITS",
    "CHAIN_COVERAGE_PER_SEGMENT",
    "CONNECT_SAMPLES",
    "ChainFit",
    "ChainSegment",
    "ChainSegmentSpec",
    "ChainWordFit",
    "build_chain_problem",
    "chain_runs",
    "fit_pair_chain",
    "fit_word_chain",
    "regularise_connector_anchors",
]
