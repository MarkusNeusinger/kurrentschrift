"""Pair-scale ductus chain fit (issue #278, Stage A) — CONTRACT STUB.

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

**Stage-B seam:** `build_chain_problem` takes a LIST of segments, never a
hard-coded triple — a whole word is `[L0, C0, L1, C1, …]` under the same index
map, the same arc-length translation ramp and the same per-segment coverage
scaling. `fit_pair_chain` is a thin two-letter wrapper over that.

Nothing below is implemented yet; this file freezes the contract that the model
(Track B) and the evaluation harness (Track C) are written against.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from core.compose import CONNECT_SAMPLES as _COMPOSE_CONNECT_SAMPLES
from core.fit import DEFAULT_COVERAGE_WEIGHT, DEFAULT_LAMBDA_REG, DEFAULT_WIDTH_WEIGHT
from tools.pairlab.analyze import JoinDissection
from tools.wordlab.cases import WordCase
from tools.wordlab.derive import WordDeriveResult


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
# Starting value; calibrated once on the Abb.-20 `pairs` set against the
# measured 0.2–0.4 xh per-side stub-replacement zone, then reported as a chosen
# model parameter with a stated systematic effect.
CHAIN_CONNECTOR_SMOOTH_WEIGHT = 1e-3
# Coverage points per chain segment: `core.fit.MAX_COVERAGE_POINTS` (300) is a
# per-GLYPH budget, so the chain scales it as MAX_COVERAGE_POINTS × n_segments.
# Invariant (asserted in code and in a unit test): coverage density per unit of
# skeleton x-extent must not fall below the single-letter fit's.
CHAIN_COVERAGE_PER_SEGMENT = 300
# Points on the raw exit→entry connector polyline — the production sample count,
# re-exported from `core.compose` so a change there cannot silently desync. The
# two endpoints are SHARED with the letters, the interior 22 are free anchors.
CONNECT_SAMPLES = _COMPOSE_CONNECT_SAMPLES  # == 24


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
    converged: bool  # both residuals within core.fit's CONVERGED_* thresholds
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
    fit_meta: dict  # optimiser status, energies, n_params, n_cov, timings


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
    x0: np.ndarray  # initial parameter vector (all zeros: the composed layout)
    bounds: list[tuple[float, float]]  # global shift, slot blocks, per-anchor deltas

    def objective(self, params: np.ndarray) -> tuple[float, np.ndarray]:
        """Total energy and its exact gradient at `params`.

        `f = e_geo + w_wid·e_wid + w_cov·e_cov_capped + λ·e_reg_letters
             + μ·e_smooth_connector`, all on the SMOOTHED fields. Anchor
        gradients fold back through the index map with
        `np.add.at(g_free, idx, g_plan)`, so the shared seam anchors receive the
        contributions of both sides.
        """
        raise NotImplementedError("Stage A Track B")

    def report_energies(self, params: np.ndarray) -> list[ChainSegment]:
        """Per-segment residuals and gates on the UNSMOOTHED fields.

        Coverage is attributed by the KD query's nearest-sample index (sharper
        than `core.word_metric.score_word_segments`' x-span rule) and reported
        UNCAPPED; the gates are literally `core.fit.CONVERGED_GEO_RMSE_UNITS`
        and `CONVERGED_COVERAGE_RMSE_UNITS`, so a chain segment and a
        single-letter fit are judged by the same yardstick.
        """
        raise NotImplementedError("Stage A Track B")


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
    * **Weights.** `reg_w` is 1 on letter anchors, 0 on connector interiors
      (binding constraint 3), normalised by the letter-anchor count so per-letter
      Tikhonov pressure equals a single-letter fit's; `width_mask` is 0 on
      connector samples, which have no stored width measurement.

    Fields arrive already prepared (smoothed with `core.fit.DIST_FIELD_SIGMA_PX`
    / `WIDTH_FIELD_SIGMA_PX`, raw kept for the report), so the problem stays
    testable against a synthetic 60×60 EDT.
    """
    raise NotImplementedError("Stage A Track B")


def fit_pair_chain(
    case: WordCase, slot_a: int, dissection: JoinDissection, *, result: WordDeriveResult | None = None
) -> ChainFit | None:
    """Fit the `slot_a → slot_a + 1` join of `case` as one chain. None when the
    composition is missing a template or the join has no usable initialisation.

    Thin wrapper over `build_chain_problem`: it only turns one occurrence into
    the three `ChainSegmentSpec`s and maps the solution back.

    * **Frame.** The metric's own registration — `x_origin_px = result.registration["tx"]`,
      `baseline_y_px = result.baseline_row + result.registration["ty"]`,
      `unit_px = result.xh_px` — so chain, independent trace and
      `tools.wordbench.pairmeas` all live in one frame.
    * **Initialisation.** Chart-row anchors (variant 0) shifted by the composed
      placement, recovered exactly as `analyze.trace_letter_ductus` recovers it;
      the connector is `analyze._generate_connector` at the composed placement,
      with NO overlap extension, NO capital retrace prefix and NO entry trim —
      the trimmed lead-in stub is precisely the ownership question the seam
      calibration measures, so the chain must see it. The known Laufform wrinkle
      in that recovery is preserved, not fixed, so chain and baseline share one
      init and the shape-delta metric stays honest.
    * **Seams.** `cut_L` = last anchor of the left letter's last NON-diacritic
      stroke, `cut_R` = first anchor of the right letter's first non-diacritic
      stroke (the diacritic rule of `analyze.trace_letter_ductus`).
    * **`result`** may be passed in to reuse a `derive_word` already computed for
      this case — a word with five joins must not compose itself five times.

    `dissection` supplies the baseline this fit is measured against and the
    per-occurrence geometry (independent fits, ink extents, the specimen's own
    join) the harness pairs with the chain's segments.
    """
    raise NotImplementedError("Stage A Track B")
