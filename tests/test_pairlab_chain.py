"""Tests for the pair-scale ductus chain fit (`tools.pairlab.chain`, issue #278).

Every test here runs WITHOUT fixtures, DB or network: the chain problem is pure
(fields in, operators out), so a synthetic EDT and a rasterised synthetic ink
stroke exercise the whole model — index map, arc-length ramp, objective,
analytic gradient, per-segment gates and an end-to-end solve.

The gradient test is the load-bearing one: L-BFGS-B's line search aborts
silently when function and gradient disagree, which looks exactly like "the
chain does not converge".

The Stage-B half at the bottom does the same for the WORD chain: `chain_runs`
on hand-built slot lists, and `fit_word_chain` / `fit_pair_chain` on a fully
synthetic `WordCase` + composition whose ink is rasterised from a known path —
still no fixtures, no DB, no network.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt, gaussian_filter

from core.compose import _endpoint_tangent
from core.extract import skeleton_and_width
from core.fit import (
    CONVERGED_COVERAGE_RMSE_UNITS,
    CONVERGED_GEO_RMSE_UNITS,
    DEFAULT_MAX_ITER,
    DIST_FIELD_SIGMA_PX,
    MAX_COVERAGE_POINTS,
    WIDTH_FIELD_SIGMA_PX,
    _sampling_operator,
    _skeleton_points,
)
from core.shaping import GlyphSlot
from core.template import build_sample_plan
from tools.pairlab import chain as chain_mod
from tools.pairlab.analyze import FIT_DX_UNITS, FIT_DY_UNITS, TRACE_WINDOW_MARGIN, _generate_connector
from tools.pairlab.chain import (
    CHAIN_CONNECTOR_ANCHOR_SPACING_UNITS,
    CHAIN_CONNECTOR_MIN_SPAN_UNITS,
    CHAIN_COVERAGE_CAP_UNITS,
    CHAIN_COVERAGE_PER_SEGMENT,
    CONNECT_SAMPLES,
    ChainSegmentSpec,
    _coverage_huber,
    _letter_cut_anchors,
    _second_difference_operator,
    _segment_converged,
    build_chain_problem,
    chain_runs,
    fit_pair_chain,
    fit_word_chain,
    regularise_connector_anchors,
)
from tools.wordlab.cases import WordCase
from tools.wordlab.derive import WordDeriveResult


UNIT_PX = 20.0


# --------------------------------------------------------------- toy problems


def _toy_letter(x0: float, k: int = 6, y0: float = 0.0) -> np.ndarray:
    """A simple rising arc of `k` anchors starting at (x0, y0)."""
    t = np.linspace(0.0, 1.0, k)
    return np.column_stack([x0 + t, y0 + 0.4 * np.sin(np.pi * t)])


def _toy_connector(p0: np.ndarray, p3: np.ndarray, n: int = 5) -> np.ndarray:
    t = np.linspace(0.0, 1.0, n)[:, None]
    return p0[None, :] * (1.0 - t) + p3[None, :] * t


def _flat_fields(shape: tuple[int, int] = (60, 60)) -> dict:
    """A synthetic 60x60 EDT around a diagonal ridge plus a matching width map."""
    h, w = shape
    ink = np.zeros(shape, dtype=bool)
    for c in range(4, w - 4):
        ink[int(round(0.4 * c)) + 8, c] = True
    dist_raw = distance_transform_edt(~ink).astype(float)
    width_raw = np.full(shape, 1.5)
    return {
        "dist_raw": dist_raw,
        "dist_smooth": gaussian_filter(dist_raw, DIST_FIELD_SIGMA_PX),
        "width_raw": width_raw,
        "width_smooth": gaussian_filter(width_raw, WIDTH_FIELD_SIGMA_PX),
        "cov_pts": _skeleton_points(ink),
        "crop_shape": shape,
    }


def _toy_specs(k: int = 6, m_total: int = 5) -> list[ChainSegmentSpec]:
    """`[letter, connector, letter]` with `k`-anchor letters and an `m_total`-point
    connector (so `m_total - 2` free interior anchors)."""
    a = _toy_letter(0.2, k)
    b = _toy_letter(2.0, k)
    conn = _toy_connector(a[-1], b[0], m_total)
    return [
        ChainSegmentSpec(
            kind="letter", anchors=a, slot_index=0, key="a", half_widths=np.full(k, 0.07), seam_in=0, seam_out=k - 1
        ),
        ChainSegmentSpec(kind="connector", anchors=conn, seam_in=0, seam_out=m_total - 1),
        ChainSegmentSpec(
            kind="letter", anchors=b, slot_index=1, key="b", half_widths=np.full(k, 0.07), seam_in=0, seam_out=k - 1
        ),
    ]


def _toy_problem(**kwargs):
    return build_chain_problem(
        _toy_specs(), unit_px=UNIT_PX, x_origin_px=4.3, baseline_y_px=45.7, **_flat_fields(), **kwargs
    )


# ------------------------------------------------------------------ index map


def test_index_map_ties_the_seam() -> None:
    """The two seam anchors are ONE parameter each, not a soft penalty."""
    k, m_total = 6, 5
    m = m_total - 2  # free connector interiors
    specs = _toy_specs(k, m_total)
    problem = build_chain_problem(specs, unit_px=UNIT_PX, x_origin_px=4.3, baseline_y_px=45.7, **_flat_fields())
    cut_l, cut_r = k - 1, 0
    assert problem.idx[k] == cut_l  # the connector's first plan anchor IS L's cut
    assert problem.idx[k + m + 1] == k + m + cut_r  # …and its last IS R's cut
    assert len(problem.anchors_free) == k + m + k
    assert len(problem.idx) == k + m_total + k
    # both sides of a seam read the same coordinates by construction
    plan = problem.plan_anchors(problem.x0)
    assert plan[k] == pytest.approx(plan[cut_l])
    assert plan[k + m + 1] == pytest.approx(plan[k + m_total + cut_r])


def test_cut_indices_skip_diacritic_strokes() -> None:
    """An `i`-shaped template: the seam sits on the BODY stroke, not the dot."""
    body = np.column_stack([np.linspace(0.0, 0.5, 5), np.linspace(0.0, 0.9, 5)])
    dot = np.array([[0.3, 1.6], [0.35, 1.7]])  # entirely above the midband
    anchors = np.vstack([body, dot])
    cut_in, cut_out = _letter_cut_anchors(anchors, [0, 5])
    assert (cut_in, cut_out) == (0, 4)
    # a second BODY stroke (not floating above the midband) does carry the seam
    tail = np.array([[0.6, 0.2], [0.8, 0.1]])
    assert _letter_cut_anchors(np.vstack([body, tail]), [0, 5]) == (0, 6)


def test_chain_operator_matches_core_fit_for_a_single_letter() -> None:
    """A one-segment chain must reduce EXACTLY to `core.fit`'s own operator."""
    anchors = _toy_letter(0.2, 9)
    spec = ChainSegmentSpec(kind="letter", anchors=anchors, slot_index=0, key="a", half_widths=np.full(9, 0.07))
    problem = build_chain_problem(
        [spec], unit_px=UNIT_PX, x_origin_px=4.3, baseline_y_px=45.7, n_samples=64, **_flat_fields()
    )
    plan = build_sample_plan(anchors, [0], [], 64)
    expected = _sampling_operator(anchors, plan)
    assert problem.sampling_op.shape == expected.shape
    assert np.allclose(problem.sampling_op, expected)
    assert np.array_equal(problem.idx, np.arange(len(anchors)))


# -------------------------------------------------------------- the gradient


def test_analytic_gradient_matches_finite_differences() -> None:
    """The exact analytic gradient must agree with central differences.

    A wrong gradient does not crash L-BFGS-B — it stalls the line search, which
    is indistinguishable from "the chain model does not work".
    """
    problem = _toy_problem()
    rng = np.random.default_rng(278)
    params = rng.uniform(-0.05, 0.05, size=len(problem.x0))
    f0, grad = problem.objective(params)
    assert np.isfinite(f0) and np.all(np.isfinite(grad))

    eps = 1e-6
    worst = 0.0
    for i in range(len(params)):
        step = np.zeros_like(params)
        step[i] = eps
        f_plus, _ = problem.objective(params + step)
        f_minus, _ = problem.objective(params - step)
        fd = (f_plus - f_minus) / (2.0 * eps)
        err = abs(fd - grad[i]) / max(1.0, abs(fd))
        worst = max(worst, err)
        assert err < 1e-5, f"param {i}: fd={fd}, analytic={grad[i]}"
    assert worst < 1e-5


def test_gradient_is_consistent_at_the_composed_start() -> None:
    """…and at x0 itself, where the optimiser's first line search happens."""
    problem = _toy_problem()
    _, grad = problem.objective(problem.x0)
    eps = 1e-6
    for i in (0, 1, 2, 3, 4, 5, 8, 17, len(problem.x0) - 1):
        step = np.zeros_like(problem.x0)
        step[i] = eps
        fd = (problem.objective(problem.x0 + step)[0] - problem.objective(problem.x0 - step)[0]) / (2.0 * eps)
        assert abs(fd - grad[i]) < 1e-5 * max(1.0, abs(fd))


# ------------------------------------------------------- gradient decomposition


def test_decomposition_sums_to_the_objective_gradient() -> None:
    """§11's build rule: the split must re-add to the gradient the solver used.

    Not a formality — a decomposition that packs or folds differently from the
    objective diagnoses a different problem, and the whole point of the
    exercise is to name the force that balances at the found optimum.
    """
    problem = _toy_problem(smooth_weight=1e-3)
    rng = np.random.default_rng(321)
    for params in (problem.x0, rng.uniform(-0.05, 0.05, size=len(problem.x0))):
        report = chain_mod.gradient_decomposition(problem, params)  # raises on mismatch
        assert report["residual_rel"] < 1e-12
        assert set(report["terms"]) == set(chain_mod.GRADIENT_TERMS)
        head = 2 + 2 * problem.n_blocks
        assert report["per_anchor"]["total"].shape == problem.anchors_free.shape
        assert np.allclose(report["per_anchor"]["geo"], report["terms"]["geo"][head:].reshape(-1, 2))


def test_each_term_is_the_whole_gradient_when_it_is_the_only_one() -> None:
    """Isolation check: with every other weight at 0 the objective IS that term.

    Stronger than the sum check, which a consistent mislabelling would pass.
    """
    off = {"width_weight": 0.0, "coverage_weight": 0.0, "overlap_weight": 0.0, "lambda_reg": 0.0, "smooth_weight": 0.0}
    weights = {
        "width": {**off, "width_weight": 1.0},
        "coverage": {**off, "coverage_weight": 1.0},
        "reg": {**off, "lambda_reg": 1.0},
        "smooth": {**off, "smooth_weight": 1.0},
    }
    rng = np.random.default_rng(11)
    for name, kwargs in weights.items():
        problem = _toy_problem(**kwargs)
        params = rng.uniform(-0.05, 0.05, size=len(problem.x0))
        terms = problem.gradient_terms(params)
        # `geo`+`crop` are unweighted and always on, so subtract them out.
        rest = terms["total"] - terms["geo"] - terms["crop"]
        assert np.allclose(terms[name], rest, atol=1e-14), name
        for other in set(chain_mod.GRADIENT_TERMS) - {name, "geo", "crop"}:
            assert np.allclose(terms[other], 0.0), f"{other} alive at weight 0"


def test_the_tikhonov_pull_never_reaches_the_placement_parameters() -> None:
    """Placement is unregularised — so `reg` must be zero on shift and blocks."""
    problem = _toy_problem()
    params = np.random.default_rng(7).uniform(-0.05, 0.05, size=len(problem.x0))
    head = 2 + 2 * problem.n_blocks
    assert np.allclose(problem.gradient_terms(params)["reg"][:head], 0.0)


def test_the_decomposition_raises_when_it_stops_matching() -> None:
    """The guard must actually fire — otherwise it is decoration."""
    problem = _toy_problem()

    class _Drifted:
        def __init__(self, inner):
            self._inner = inner
            self.n_blocks = inner.n_blocks

        def gradient_terms(self, params):
            terms = dict(self._inner.gradient_terms(params))
            terms["geo"] = terms["geo"] * 1.01  # a 1 % mislabelled force
            return terms

        def energy_terms(self, params):
            return self._inner.energy_terms(params)

    with pytest.raises(AssertionError, match="misses the objective"):
        chain_mod.gradient_decomposition(_Drifted(problem), problem.x0)


def test_the_anchor_sample_window_is_where_the_field_is_actually_read() -> None:
    """`sample_slice_of_anchor` must return a real, ordered sample window.

    The objective reads the ink only at samples; a force „at the anchor" is a
    force the optimiser never feels (`vom-scan-zum-schreiben.md` Schritt 4).
    """
    problem = _toy_problem()
    n_s = problem.n_samples or len(problem.to_pixels(problem.x0)[0])
    seen = 0
    for i in range(len(problem.anchors_free)):
        lo, hi = chain_mod.sample_slice_of_anchor(problem, i)
        assert 0 <= lo <= hi <= n_s
        seen += hi > lo
    assert seen == len(problem.anchors_free)  # every free anchor owns samples


# ---------------------------------------------------------------- the weights


def test_slot_translation_is_unregularised() -> None:
    """A pure slot translation must cost NO Tikhonov energy (placement is free)."""
    problem = _toy_problem()
    params = problem.x0.copy()
    base = problem.energy_terms(params)["e_reg"]
    params[problem.slot_blocks[0]] = 0.3  # dx of slot 0's block
    params[problem.slot_blocks[1] + 1] = -0.1  # dy of slot 1's block
    assert problem.energy_terms(params)["e_reg"] == pytest.approx(base)
    assert base == pytest.approx(0.0)
    # …but the geometry DID move, so the slot block is a real parameter
    assert problem.energy_terms(params)["e_geo"] != pytest.approx(problem.energy_terms(problem.x0)["e_geo"])


def test_connector_anchors_are_form_unregularised() -> None:
    """The connector's interior carries no Tikhonov term — only curvature CHANGE.

    Binding constraint 3: penalising distance to the generated Bézier would make
    the chain measure the generator against itself.
    """
    problem = _toy_problem()
    n_blocks = len(problem.slot_blocks)
    off = 2 + 2 * n_blocks
    k_free = len(problem.anchors_free)
    deltas = np.zeros((k_free, 2))
    c0, c1 = problem.anchor_slices[1]
    deltas[c0:c1] = [0.25, -0.4]  # arbitrary connector displacement
    params = problem.x0.copy()
    params[off:] = deltas.ravel()
    assert problem.energy_terms(params)["e_reg"] == pytest.approx(0.0)
    # a letter delta of the same size is NOT free
    deltas[:] = 0.0
    l0, l1 = problem.anchor_slices[0]
    deltas[l0:l1] = [0.25, -0.4]
    params[off:] = deltas.ravel()
    assert problem.energy_terms(params)["e_reg"] > 0.0


def test_connector_smoothness_is_zero_on_a_straight_line() -> None:
    """`e_smooth` measures curvature CHANGE: exactly 0 for a collinear connector,
    positive as soon as an interior anchor is kinked out of line."""
    problem = _toy_problem()
    assert problem.energy_terms(problem.x0)["e_smooth"] == pytest.approx(0.0, abs=1e-12)
    n_blocks = len(problem.slot_blocks)
    off = 2 + 2 * n_blocks
    deltas = np.zeros((len(problem.anchors_free), 2))
    c0, _ = problem.anchor_slices[1]
    deltas[c0] = [0.0, 0.3]  # kink ONE interior anchor
    params = problem.x0.copy()
    params[off:] = deltas.ravel()
    assert problem.energy_terms(params)["e_smooth"] > 0.0
    # collinear but unevenly spaced still scores zero (arc-length normalised)
    pts = np.column_stack([np.array([0.0, 0.1, 0.5, 0.6, 1.4]), np.array([0.0, 0.2, 1.0, 1.2, 2.8])])
    assert np.allclose(_second_difference_operator(pts) @ pts, 0.0, atol=1e-9)


def test_connector_ramp_is_continuous_at_the_seam() -> None:
    """With `t_L != t_R` the connector rides an arc-length ramp between the two
    slot blocks, and its ends stay welded to the letters' cut anchors."""
    problem = _toy_problem()
    params = problem.x0.copy()
    params[problem.slot_blocks[0]] = 0.3  # t_L = (+0.3, 0)
    params[problem.slot_blocks[1]] = -0.2  # t_R = (-0.2, 0)
    plan = problem.plan_anchors(params)
    k = len(problem.specs[0].anchors)
    m_total = len(problem.specs[1].anchors)
    cut_l = problem.specs[0].seam_out
    cut_r = problem.specs[2].seam_in
    assert plan[k, 0] == pytest.approx(plan[cut_l, 0], abs=1e-12)
    assert plan[k + m_total - 1, 0] == pytest.approx(plan[k + m_total + cut_r, 0], abs=1e-12)
    # the ramp itself runs monotonically from the left block to the right one
    assert 0.0 < problem.ramp[0] < problem.ramp[-1] < 1.0
    shifts = plan[k : k + m_total, 0] - problem.anchors_free[problem.idx[k : k + m_total], 0]
    assert shifts[0] == pytest.approx(0.3)
    assert shifts[-1] == pytest.approx(-0.2)
    assert np.all(np.diff(shifts) <= 1e-12)  # monotone blend, no jump at either seam


# ----------------------------------------------------------------- robustness


def test_capped_coverage_bounds_leverage() -> None:
    """A far-off skeleton pixel keeps pulling but stops out-levering the chain."""
    cap = CHAIN_COVERAGE_CAP_UNITS * UNIT_PX
    rho, dscale = _coverage_huber(np.array([0.5 * cap, cap, 5.0 * cap]), cap)
    assert dscale[0] == pytest.approx(2.0 * 0.5 * cap)  # quadratic below the cap
    assert dscale[1] == pytest.approx(2.0 * cap)
    assert dscale[2] == pytest.approx(2.0 * cap)  # saturated, NOT 10*cap
    assert dscale[2] <= 2.0 * cap
    uncapped = 2.0 * 5.0 * cap
    assert uncapped > 2.0 * cap
    # continuity and monotonicity of the energy itself
    assert rho[1] == pytest.approx(cap**2)
    assert rho[2] > rho[1]


def test_coverage_points_scale_with_chain_length() -> None:
    """A 3-segment chain gets 3x the single-letter budget, so the coverage
    density per unit of skeleton x-extent never falls below `core.fit`'s."""
    fields = _flat_fields()
    dense = np.column_stack([np.linspace(0.0, 300.0, 4000), np.linspace(0.0, 60.0, 4000)])
    fields["cov_pts"] = dense
    problem = build_chain_problem(_toy_specs(), unit_px=UNIT_PX, x_origin_px=4.3, baseline_y_px=45.7, **fields)
    assert len(problem.cov_pts) == CHAIN_COVERAGE_PER_SEGMENT * 3
    assert len(problem.cov_pts) >= 3 * MAX_COVERAGE_POINTS

    single_extent = 100.0  # one letter's x-extent
    chain_extent = 300.0  # the same three segments end to end
    single_density = MAX_COVERAGE_POINTS / single_extent
    chain_density = len(problem.cov_pts) / chain_extent
    assert chain_density >= single_density - 1e-9


def test_per_segment_gates_are_independent() -> None:
    """A failing connector must not drag the two letters' gates down with it —
    and the thresholds are literally `core.fit`'s."""
    unit = 50.0
    good_geo = CONVERGED_GEO_RMSE_UNITS * unit - 1e-6
    good_cov = CONVERGED_COVERAGE_RMSE_UNITS * unit - 1e-6
    assert _segment_converged(good_geo, good_cov, unit)
    assert not _segment_converged(CONVERGED_GEO_RMSE_UNITS * unit + 1e-6, good_cov, unit)
    assert not _segment_converged(good_geo, CONVERGED_COVERAGE_RMSE_UNITS * unit + 1e-6, unit)
    assert _segment_converged(CONVERGED_GEO_RMSE_UNITS * unit, CONVERGED_COVERAGE_RMSE_UNITS * unit, unit)

    # …and on a real problem: put the chain onto its ink, then push ONLY the
    # connector's interior anchors off it. The two letters keep their own
    # residuals bit for bit — the seam anchors belong to THEM and did not move.
    problem, xh, _ = _straight_ink_problem()
    segments = problem.report_energies(problem.x0)
    assert segments[0].converged and segments[2].converged and segments[1].converged
    n_blocks = len(problem.slot_blocks)
    params = problem.x0.copy()
    deltas = np.zeros((len(problem.anchors_free), 2))
    c0, c1 = problem.anchor_slices[1]
    deltas[c0:c1, 1] = 0.15  # lift the connector clear of the ink it was on
    params[2 + 2 * n_blocks :] = deltas.ravel()
    broken = problem.report_energies(params)
    assert not broken[1].converged
    assert broken[1].geo_rmse_px > CONVERGED_GEO_RMSE_UNITS * xh
    assert broken[0].converged and broken[2].converged
    assert broken[0].geo_rmse_px == pytest.approx(segments[0].geo_rmse_px)
    assert broken[2].geo_rmse_px == pytest.approx(segments[2].geo_rmse_px)


# ------------------------------- the letter-local coverage gate (#278 Stage B)


def test_without_a_window_the_local_gate_is_the_union_gate() -> None:
    """`cov_window_px=None` — the default and the connector's case — must leave
    the report bit for bit as it was before the second gate existed."""
    problem = _toy_problem()
    for seg in problem.report_energies(problem.x0):
        assert seg.cov_rmse_local_px == pytest.approx(seg.cov_rmse_px)
        assert seg.n_cov_local == seg.n_cov
        assert seg.converged_local == seg.converged


def test_letter_local_window_grades_only_its_own_ink() -> None:
    """A letter's coverage gate must see the ink of ITS window, not the pair's.

    The chain's coverage points span the whole union window, so a letter is
    charged for connector ink the baseline's letter-local fit never saw. Binding
    a window to the segment drops exactly those points from the GATE — while the
    fit (objective, gradient, coverage targets) stays untouched.
    """
    problem, xh, _ = _straight_ink_problem()
    wide = problem.report_energies(problem.x0)

    # The synthetic ink IS the chain's own shape, so the letter's real window
    # (samples ± the trace margin) would drop nothing; cut it deliberately short
    # to show what a window does to the gate at all.
    px, _py = problem.to_pixels(problem.x0)
    s0, s1 = problem.sample_slices[0]
    lo, hi = float(px[s0:s1].min()), float(px[s0:s1].max())
    problem.specs[0].cov_window_px = (lo - 0.15 * xh, lo + 0.6 * (hi - lo))
    narrow = problem.report_energies(problem.x0)

    assert narrow[0].n_cov_local < narrow[0].n_cov  # union-window ink was dropped
    assert narrow[0].cov_rmse_px == pytest.approx(wide[0].cov_rmse_px)  # the union number is untouched
    assert narrow[0].geo_rmse_px == pytest.approx(wide[0].geo_rmse_px)  # …and so is the geometry half
    # only the segment that carries a window changes; the others keep both gates
    assert narrow[1].n_cov_local == narrow[1].n_cov
    assert narrow[2].n_cov_local == narrow[2].n_cov


def test_the_local_gate_can_pass_where_the_union_gate_fails() -> None:
    """The asymmetry Stage-B precondition 1 is about: same fit, same geometry,
    two verdicts — because the coverage window differs."""
    problem, xh, _ = _straight_ink_problem()
    # A window that admits NO coverage point at all: coverage collapses to the
    # empty-sum convention (0.0), so only the geometry half of the gate remains.
    problem.specs[0].cov_window_px = (-1e6, -1e6 + 1.0)
    segments = problem.report_energies(problem.x0)
    assert segments[0].n_cov_local == 0
    assert segments[0].cov_rmse_local_px == 0.0
    assert segments[0].converged_local is (segments[0].geo_rmse_px <= CONVERGED_GEO_RMSE_UNITS * xh)


# ------------------------------------------------------------- synthetic ink


def _rasterise(polyline_units: np.ndarray, *, xh: float, baseline_row: float, x_origin: float, width_px: int):
    """Draw a composed-frame polyline as ink and return (skel, width_map, shape)."""
    px = x_origin + polyline_units[:, 0] * xh
    py = baseline_row - polyline_units[:, 1] * xh
    w = int(px.max() + 3 * xh)
    h = int(baseline_row + 1.5 * xh)
    img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(img).line([(float(a), float(b)) for a, b in zip(px, py, strict=True)], fill=255, width=width_px)
    mask = np.asarray(img) > 127
    skel, width_map = skeleton_and_width(mask)
    return skel, width_map, (h, w)


def _chain_shape(k: int = 9, m_total: int = 24) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A smooth `letter → connector → letter` ground-truth path in composed units."""
    t = np.linspace(0.0, 1.0, k)
    left = np.column_stack([0.2 + 1.0 * t, 0.15 + 0.55 * np.sin(np.pi * t)])
    right = np.column_stack([2.1 + 1.0 * t, 0.15 + 0.55 * np.sin(np.pi * t)])
    u = np.linspace(0.0, 1.0, m_total)
    conn = np.column_stack(
        [
            left[-1, 0] + (right[0, 0] - left[-1, 0]) * u,
            left[-1, 1] + (right[0, 1] - left[-1, 1]) * u - 0.18 * np.sin(np.pi * u),
        ]
    )
    return left, conn, right


def _fields_from(skel: np.ndarray, width_map: np.ndarray) -> dict:
    dist_raw = distance_transform_edt(~skel).astype(float)
    _, ink_idx = distance_transform_edt(~np.asarray(width_map > 0), return_indices=True)
    width_raw = width_map[ink_idx[0], ink_idx[1]].astype(float)
    return {
        "dist_raw": dist_raw,
        "dist_smooth": gaussian_filter(dist_raw, DIST_FIELD_SIGMA_PX),
        "width_raw": width_raw,
        "width_smooth": gaussian_filter(width_raw, WIDTH_FIELD_SIGMA_PX),
        "cov_pts": _skeleton_points(skel),
        "crop_shape": skel.shape,
    }


def _straight_ink_problem(shift_l=(0.0, 0.0), shift_r=(0.0, 0.0), width_px: int = 5):
    """A synthetic three-segment chain over rasterised ink of its own shape.

    `shift_*` perturbs the two LETTER templates away from the truth, so the fit
    has to recover exactly that offset with its slot translation blocks.
    """
    xh, baseline_row, x_origin = 40.0, 90.0, 30.0
    left, conn, right = _chain_shape()
    skel, width_map, shape = _rasterise(
        np.vstack([left, conn[1:-1], right]), xh=xh, baseline_row=baseline_row, x_origin=x_origin, width_px=width_px
    )
    half_w = (0.5 * width_px) / xh
    specs = [
        ChainSegmentSpec(
            kind="letter",
            anchors=left + np.asarray(shift_l),
            slot_index=0,
            key="L",
            half_widths=np.full(len(left), half_w),
            seam_in=0,
            seam_out=len(left) - 1,
        ),
        ChainSegmentSpec(kind="connector", anchors=conn, seam_in=0, seam_out=len(conn) - 1),
        ChainSegmentSpec(
            kind="letter",
            anchors=right + np.asarray(shift_r),
            slot_index=1,
            key="R",
            half_widths=np.full(len(right), half_w),
            seam_in=0,
            seam_out=len(right) - 1,
        ),
    ]
    problem = build_chain_problem(
        specs, unit_px=xh, x_origin_px=x_origin, baseline_y_px=baseline_row, **_fields_from(skel, width_map)
    )
    return problem, xh, shape


def test_chain_converges_on_synthetic_ink() -> None:
    """End to end: perturb both letters by 0.2 xh, fit, and get the ink back.

    All three segments must clear `core.fit`'s convergence gate and the injected
    placement error must come back out of the translation parameters — this is
    the test that would fail first if the gradient, the index map or the ramp
    were wrong.
    """
    from scipy.optimize import minimize

    injected_l = np.array([0.20, 0.0])
    injected_r = np.array([-0.15, 0.05])
    problem, xh, _ = _straight_ink_problem(shift_l=injected_l, shift_r=injected_r)

    started = time.perf_counter()
    res = minimize(
        problem.objective,
        problem.x0,
        jac=True,
        method="L-BFGS-B",
        bounds=problem.bounds,
        options={"maxiter": DEFAULT_MAX_ITER, "maxfun": 50 * DEFAULT_MAX_ITER},
    )
    elapsed = time.perf_counter() - started
    assert elapsed < 10.0, f"one pair-chain solve took {elapsed:.1f}s"

    segments = problem.report_energies(res.x)
    assert len(segments) == 3
    for seg in segments:
        assert seg.geo_rmse_px <= CONVERGED_GEO_RMSE_UNITS * xh, (
            f"{seg.kind}/{seg.key}: geo {seg.geo_rmse_px:.2f}px > {CONVERGED_GEO_RMSE_UNITS * xh:.2f}px"
        )
    assert segments[0].fitted_anchors is not None and segments[2].fitted_anchors is not None
    assert segments[1].fitted_anchors is None  # the connector has no template form

    tx, ty, blocks, _ = problem.unpack(res.x)
    recovered_l = np.array([tx, ty]) + blocks[0]
    recovered_r = np.array([tx, ty]) + blocks[1]
    assert np.max(np.abs(recovered_l + injected_l)) <= 0.05, f"L shift {recovered_l} vs -{injected_l}"
    assert np.max(np.abs(recovered_r + injected_r)) <= 0.05, f"R shift {recovered_r} vs -{injected_r}"
    # the placement blocks did the work, not the regularised per-anchor deltas
    assert segments[0].max_anchor_delta < 0.25
    assert segments[2].max_anchor_delta < 0.25
    assert abs(blocks[0, 0]) < FIT_DX_UNITS and abs(blocks[0, 1]) < FIT_DY_UNITS


# ------------------------------------------- the degenerate connector guard


def _smoothness_energy(pts: np.ndarray) -> float:
    """`_ChainProblem._evaluate`'s `e_smooth` for one connector on its own."""
    op = _second_difference_operator(pts)
    return float(np.sum((op @ pts) ** 2)) / max(1, op.shape[0])


def _cusped_connector(gap: float, exit_deg: float = -80.0, entry_deg: float = 80.0) -> np.ndarray:
    """The production connector between two letters composed `gap` xh apart.

    At `gap <= 0` the letters touch or overlap and `_generate_connector`'s handle
    floor (0.05 xh) overrides its own design value `0.4·span`, so the cubic
    doubles back — the shape the chain must not be initialised from.
    """
    p0 = (1.20, 0.30)
    p3 = (1.20 + gap, 0.35)
    return np.asarray(_generate_connector(p0, exit_deg, p3, entry_deg), dtype=float).reshape(-1, 2)


def test_regularise_leaves_a_roomy_connector_untouched() -> None:
    """Above the chord threshold the generated connector is passed through
    byte-identically — the 224 non-degenerate Stage-A solves must not move."""
    conn = _cusped_connector(0.9)
    assert len(conn) > 3
    assert np.hypot(*(conn[-1] - conn[0])) >= CHAIN_CONNECTOR_MIN_SPAN_UNITS
    assert np.array_equal(regularise_connector_anchors(conn), conn)


@pytest.mark.parametrize("gap", [0.04, 0.0, -0.05, -0.12])
def test_regularise_thins_a_connector_with_no_room(gap: float) -> None:
    """Zero or negative ink gap: the same curve, re-discretised to a point count
    its chord can carry — endpoints exact, smoothness back in its calibrated
    range, and every operator it feeds finite."""
    conn = _cusped_connector(gap)
    assert len(conn) > 3
    span = float(np.hypot(*(conn[-1] - conn[0])))
    assert span < CHAIN_CONNECTOR_MIN_SPAN_UNITS

    out = regularise_connector_anchors(conn)
    assert 3 <= len(out) < len(conn)
    assert len(out) == max(3, round(span / CHAIN_CONNECTOR_ANCHOR_SPACING_UNITS) + 1)
    # the seam anchors are shared with the two letters and must survive exactly
    assert np.allclose(out[0], conn[0], atol=1e-12)
    assert np.allclose(out[-1], conn[-1], atol=1e-12)
    assert np.isfinite(out).all()
    # the whole point: the sample clustering that scaled the smoothness block by
    # 1/ds² is gone, and with it the block's dominance
    ds_raw = np.hypot(*np.diff(conn, axis=0).T)
    ds_out = np.hypot(*np.diff(out, axis=0).T)
    assert ds_out.min() > 3.0 * ds_raw.min()
    assert _smoothness_energy(out) < _smoothness_energy(conn) / 1.5
    assert np.isfinite(_second_difference_operator(out)).all()


def test_regularise_survives_a_fully_collapsed_connector() -> None:
    """Two body endpoints on top of each other — zero arc, zero chord.

    The two seam anchors survive and nothing sits between them: an interior
    anchor would only hand `_second_difference_operator` coincident points to
    divide by, which is where its 1e-6 spacing floor produces 1e12 rows.
    """
    conn = np.tile(np.array([1.2, 0.3]), (CONNECT_SAMPLES + 1, 1))
    out = regularise_connector_anchors(conn)
    assert len(out) == 2
    assert np.isfinite(out).all()
    assert _second_difference_operator(out).shape[0] == 0
    # …and such a connector still assembles into a finite chain problem
    problem = build_chain_problem(
        [
            ChainSegmentSpec(
                kind="letter",
                anchors=_toy_letter(0.2, 6),
                slot_index=0,
                key="a",
                half_widths=np.full(6, 0.07),
                seam_in=0,
                seam_out=5,
            ),
            ChainSegmentSpec(kind="connector", anchors=out, seam_in=0, seam_out=1),
            ChainSegmentSpec(
                kind="letter",
                anchors=_toy_letter(1.2, 6),
                slot_index=1,
                key="b",
                half_widths=np.full(6, 0.07),
                seam_in=0,
                seam_out=5,
            ),
        ],
        unit_px=UNIT_PX,
        x_origin_px=4.3,
        baseline_y_px=45.7,
        **_flat_fields(),
    )
    value, grad = problem.objective(problem.x0)
    assert np.isfinite(value) and np.all(np.isfinite(grad))
    assert problem.energy_terms(problem.x0)["e_smooth"] == 0.0


def _overlapping_pair_problem(*, regularise: bool, gap: float = 0.0):
    """A synthetic pair whose two letters touch, with the PRODUCTION connector.

    The ink is the two letters only (they overlap, so the plate shows no join),
    which is exactly the `base_empty_join` regime the degenerate Stage-A solves
    live in. `regularise=False` reproduces the pre-fix initialisation.
    """
    xh, baseline_row, x_origin = 40.0, 90.0, 30.0
    t = np.linspace(0.0, 1.0, 9)
    left = np.column_stack([0.2 + 1.0 * t, 0.15 + 0.55 * np.sin(np.pi * t)])
    right = np.column_stack([left[-1, 0] + gap + 1.0 * t, 0.15 + 0.55 * np.sin(np.pi * t)])
    conn = np.asarray(_generate_connector(tuple(left[-1]), -80.0, tuple(right[0]), 80.0), dtype=float).reshape(-1, 2)
    if regularise:
        conn = regularise_connector_anchors(conn)

    skel, width_map, _ = _rasterise(
        np.vstack([left, right]), xh=xh, baseline_row=baseline_row, x_origin=x_origin, width_px=5
    )
    half_w = 2.5 / xh
    shift = np.array([0.12, 0.0])  # placement error both letters have to undo
    specs = [
        ChainSegmentSpec(
            kind="letter",
            anchors=left + shift,
            slot_index=0,
            key="L",
            half_widths=np.full(len(left), half_w),
            seam_in=0,
            seam_out=len(left) - 1,
        ),
        ChainSegmentSpec(kind="connector", anchors=conn, seam_in=0, seam_out=len(conn) - 1),
        ChainSegmentSpec(
            kind="letter",
            anchors=right + shift,
            slot_index=1,
            key="R",
            half_widths=np.full(len(right), half_w),
            seam_in=0,
            seam_out=len(right) - 1,
        ),
    ]
    problem = build_chain_problem(
        specs, unit_px=xh, x_origin_px=x_origin, baseline_y_px=baseline_row, **_fields_from(skel, width_map)
    )
    return problem, xh


@pytest.mark.parametrize("gap", [0.0, -0.02])
def test_overlapping_pair_solves_instead_of_stalling(gap: float) -> None:
    """The regression this guard exists for.

    With the raw 24-point cusp the smoothness term dwarfs every data term at
    `x0`, L-BFGS-B spends its whole budget unbending the connector and the
    letters come out of the solve where they went in. Re-discretised, the same
    occurrence has a finite objective, a solve that actually moves its
    parameters, and letters that land on their ink.
    """
    from scipy.optimize import minimize

    from core.fit import DEFAULT_MAX_ITER

    def solve(problem):
        return minimize(
            problem.objective,
            problem.x0,
            jac=True,
            method="L-BFGS-B",
            bounds=problem.bounds,
            options={"maxiter": DEFAULT_MAX_ITER, "maxfun": 50 * DEFAULT_MAX_ITER},
        )

    raw, _ = _overlapping_pair_problem(regularise=False, gap=gap)
    fixed, xh = _overlapping_pair_problem(regularise=True, gap=gap)

    e_raw = raw.energy_terms(raw.x0)
    e_fixed = fixed.energy_terms(fixed.x0)
    assert all(np.isfinite(v) for v in e_raw.values())  # never non-finite, before or after
    assert all(np.isfinite(v) for v in e_fixed.values())
    # before: the connector's smoothness IS the objective; after: a data term is
    assert e_raw["e_smooth"] * fixed.smooth_weight > 5.0 * e_raw["e_geo"]
    assert e_fixed["e_smooth"] * fixed.smooth_weight < e_fixed["e_geo"]

    res_raw = solve(raw)
    res_fixed = solve(fixed)
    assert np.isfinite(res_fixed.fun)
    assert res_fixed.status != 2, f"line search aborted: {res_fixed.message}"

    seg_raw = raw.report_energies(res_raw.x)
    seg_fixed = fixed.report_energies(res_fixed.x)
    # the parameters moved — and the letters, not just the connector
    assert np.max(np.abs(res_fixed.x)) > 0.01
    for i in (0, 2):
        assert seg_fixed[i].max_anchor_delta > seg_raw[i].max_anchor_delta
        assert seg_fixed[i].geo_rmse_px <= CONVERGED_GEO_RMSE_UNITS * xh, (
            f"segment {i}: geo {seg_fixed[i].geo_rmse_px:.2f}px"
        )
    # …and the stalled solve is the one that leaves its letters where they were
    assert max(seg_raw[0].max_anchor_delta, seg_raw[2].max_anchor_delta) < 0.02


# ============================================================ Stage B: the word
#
# `chain_runs` and `fit_word_chain` take a `WordCase` and a composition instead
# of bare specs. Both are plain dataclasses, so the whole input is hand-built
# here: one template letter, one composed item per slot at a known placement,
# and ink rasterised from that same geometry displaced by a known per-slot
# shift. Still no fixtures, no DB, no network.


WORD_XH = 40.0
WORD_BASELINE_ROW = 110.0
WORD_X_ORIGIN = 30.0
LETTER_ADVANCE = 1.6  # xh between two composed letters' origins


def _slot(key: str | None = "a", *, space: bool = False, joins: bool = True) -> GlyphSlot:
    return GlyphSlot(key=key, text=key or " ", position="medial", ligature=False, space=space, joins=joins)


def _bare_case(slots: list[GlyphSlot]) -> WordCase:
    """A `WordCase` with nothing but its slots — all `chain_runs` reads."""
    return WordCase(
        id="synthetic",
        word="".join(s.text for s in slots),
        kind="word",
        slots=list(slots),
        templates={},
        style_ratio=[1.0, 1.0, 1.0],
        width_resolver="constant",
        nib_units=0.07,
    )


# ------------------------------------------------------------------ chain_runs


def test_chain_runs_breaks_at_spaces_and_keyless_slots() -> None:
    slots = [_slot("a"), _slot("n"), _slot(None, space=True), _slot("b"), _slot("u")]
    assert chain_runs(_bare_case(slots)) == [[0, 1], [3, 4]]
    # a keyless but non-space slot (a character with no glyph at all) breaks too
    slots[2] = _slot(None)
    assert chain_runs(_bare_case(slots)) == [[0, 1], [3, 4]]


def test_chain_runs_isolates_non_joining_glyphs() -> None:
    """A digit renders but no Übergang ever enters or leaves it (§4)."""
    assert chain_runs(_bare_case([_slot("a"), _slot("1", joins=False), _slot("b")])) == [[0], [1], [2]]
    assert chain_runs(_bare_case([_slot("1", joins=False), _slot("2", joins=False)])) == [[0], [1]]


def test_chain_runs_returns_a_lone_letter_as_a_one_slot_run() -> None:
    """Not skipped: `fit_word_chain` fits it as a one-segment chain."""
    assert chain_runs(_bare_case([_slot("a")])) == [[0]]
    assert chain_runs(_bare_case([])) == []
    assert chain_runs(_bare_case([_slot(None, space=True)])) == []


def test_chain_runs_partitions_every_keyed_slot() -> None:
    slots = [_slot("l"), _slot("e"), _slot(None, space=True), _slot("1", joins=False), _slot("s"), _slot("t")]
    runs = chain_runs(_bare_case(slots))
    assert runs == [[0, 1], [3], [4, 5]]
    flat = [i for run in runs for i in run]
    assert flat == sorted(flat)  # writing order, no slot in two runs
    assert set(flat) == {i for i, s in enumerate(slots) if s.key and not s.space}


# --------------------------------------------- a synthetic case + composition


def _letter_anchors(k: int = 9) -> np.ndarray:
    """The one template letter: an arc whose first anchor sits at x = 0, so the
    placement offset `_letter_spec` recovers is exactly the item's first x."""
    t = np.linspace(0.0, 1.0, k)
    return np.column_stack([0.9 * t, 0.15 + 0.55 * np.sin(np.pi * t)])


def _synthetic_word(shifts: list[tuple[float, float]], *, width_px: int = 5, k: int = 9):
    """`(case, result, windows_px, truth_px)` for a run of `len(shifts)` letters.

    The COMPOSITION places the same template every `LETTER_ADVANCE`; the INK is
    that composition displaced per slot by `shifts[i]`, joined by the production
    connector between the displaced endpoints. So the chain starts at the
    undisplaced layout and has to recover exactly `shifts` in its translation
    parameters, per slot.
    """
    anchors = _letter_anchors(k)
    n = len(shifts)
    placed = [anchors + np.array([i * LETTER_ADVANCE, 0.0]) for i in range(n)]
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
    skel, width_map, shape = _rasterise(
        np.vstack(path), xh=WORD_XH, baseline_row=WORD_BASELINE_ROW, x_origin=WORD_X_ORIGIN, width_px=width_px
    )

    half_w = (0.5 * width_px) / WORD_XH
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
        baseline_y=int(WORD_BASELINE_ROW),
        midband_y=int(WORD_BASELINE_ROW - WORD_XH),
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
        xh_px=WORD_XH,
        baseline_row=WORD_BASELINE_ROW,
        registration={"tx": WORD_X_ORIGIN, "ty": 0.0, "xh_px": WORD_XH},
    )
    truth_px = [
        np.column_stack([WORD_X_ORIGIN + t[:, 0] * WORD_XH, WORD_BASELINE_ROW - t[:, 1] * WORD_XH]) for t in truth
    ]
    windows_px = {
        i: (float(p[:, 0].min()) - TRACE_WINDOW_MARGIN * WORD_XH, float(p[:, 0].max()) + TRACE_WINDOW_MARGIN * WORD_XH)
        for i, p in enumerate(truth_px)
    }
    return case, result, windows_px, truth_px


def _recovered(fit, slot: int) -> np.ndarray:
    """Total displacement of one slot: the global shift plus its own block."""
    return np.asarray(fit.global_shift_units) + np.asarray(fit.slot_shift_units[slot])


# --------------------------------------------------------------- fit_word_chain


def test_word_chain_fits_three_letters_and_recovers_every_slot_shift() -> None:
    """[L, C, L, C, L] in one solve: three letters on their ink, two joins, and
    each letter's injected displacement back out of its own block."""
    injected = [(0.10, 0.0), (-0.08, 0.04), (0.05, -0.03)]
    case, result, windows, _ = _synthetic_word(injected)

    fit = fit_word_chain(case, [0, 1, 2], result=result, windows_px=windows)
    assert fit is not None
    assert fit.slots == [0, 1, 2]
    assert [s.kind for s in fit.segments] == ["letter", "connector", "letter", "connector", "letter"]
    assert [s.slot_index for s in fit.segments] == [0, None, 1, None, 2]
    assert len(fit.cut_indices) == 2
    assert len(fit.connector_units) == 2
    assert fit.converged

    for slot, injected_shift in enumerate(injected):
        assert np.max(np.abs(_recovered(fit, slot) - np.asarray(injected_shift))) <= 0.05, (
            f"slot {slot}: {_recovered(fit, slot)} vs {injected_shift}"
        )
    for seg in fit.segments:
        if seg.kind == "letter":
            assert seg.geo_rmse_px <= CONVERGED_GEO_RMSE_UNITS * WORD_XH
            assert seg.fitted_anchors is not None
        else:
            assert seg.fitted_anchors is None


def test_word_chain_reports_pen_down_polylines_in_writing_order() -> None:
    """`stroke_polylines_px` is what a word trace is assembled from: every
    sample of the chain exactly once, labelled by segment and slot."""
    case, result, windows, _ = _synthetic_word([(0.05, 0.0), (0.0, 0.0), (-0.05, 0.0)])
    fit = fit_word_chain(case, [0, 1, 2], result=result, windows_px=windows)
    assert fit is not None
    strokes = fit.stroke_polylines_px
    # one entry per single-stroke letter and one per connector, in order
    assert [s["kind"] for s in strokes] == ["letter", "connector", "letter", "connector", "letter"]
    assert [s["slot_index"] for s in strokes] == [0, None, 1, None, 2]
    assert [s["segment_index"] for s in strokes] == [0, 1, 2, 3, 4]
    assert {s["stroke_index"] for s in strokes} == {0}
    assert sum(len(s["points_px"]) for s in strokes) == fit.fit_meta["n_samples"]
    for entry, seg in zip(strokes, fit.segments, strict=True):
        assert np.allclose(entry["points_px"], seg.polyline_px)


def test_word_chain_fits_a_one_slot_run() -> None:
    """A lone letter is a one-SEGMENT chain — no join, no connector, same solve."""
    case, result, windows, _ = _synthetic_word([(0.12, -0.03)])
    fit = fit_word_chain(case, [0], result=result, windows_px=windows)
    assert fit is not None
    assert [s.kind for s in fit.segments] == ["letter"]
    assert fit.cut_indices == []
    assert fit.connector_units == []
    assert fit.fit_meta["connector_converged"] is None
    assert fit.converged
    assert np.max(np.abs(_recovered(fit, 0) - np.array([0.12, -0.03]))) <= 0.05


def test_word_chain_rejects_a_non_consecutive_run() -> None:
    """A run is an adjacency statement; a gap in it is a caller bug, not a fit."""
    case, result, windows, _ = _synthetic_word([(0.0, 0.0)] * 3)
    with pytest.raises(ValueError, match="CONSECUTIVE"):
        fit_word_chain(case, [0, 2], result=result, windows_px=windows)
    with pytest.raises(ValueError):
        fit_word_chain(case, [], result=result, windows_px=windows)


def test_word_chain_needs_a_coverage_window() -> None:
    """Without one window there is no band to cut — the caller's placement
    diagnosis decides the fallback, this function does not invent one."""
    case, result, _windows, _ = _synthetic_word([(0.0, 0.0), (0.0, 0.0)])
    assert fit_word_chain(case, [0, 1], result=result, windows_px={}) is None


# ------------------------------------------------- fit_pair_chain as a wrapper


def test_fit_pair_chain_is_the_two_slot_word_chain() -> None:
    """The frozen pair entry point must be the SAME fit, only narrowed.

    `fit_pair_chain` reads exactly three things off the dissection: the cached
    composition and the two letters' independently placed body ink (whose
    x-extent becomes the coverage window), so a stand-in carrying those is a
    complete input — and its result must agree with the word chain field for
    field, with the list-per-join fields collapsed to the pair's singletons.
    """
    injected = [(0.09, 0.02), (-0.06, -0.03)]
    case, result, windows, truth_px = _synthetic_word(injected)
    word = fit_word_chain(case, [0, 1], result=result, windows_px=windows)
    assert word is not None

    dissection = SimpleNamespace(
        result=result, a=SimpleNamespace(body_px=[truth_px[0]]), b=SimpleNamespace(body_px=[truth_px[1]])
    )
    pair = fit_pair_chain(case, 0, dissection)
    assert pair is not None
    assert pair.slot_a == 0
    assert pair.cut_indices == word.cut_indices[0]
    assert np.allclose(pair.connector_units, word.connector_units[0])
    assert pair.slot_shift_units == word.slot_shift_units
    assert pair.slot_at_bound == word.slot_at_bound
    assert pair.global_shift_units == word.global_shift_units
    assert pair.converged == word.converged
    assert pair.converged_local == word.converged_local
    for a, b in zip(pair.segments, word.segments, strict=True):
        assert (a.kind, a.slot_index, a.key) == (b.kind, b.slot_index, b.key)
        assert a.geo_rmse_px == pytest.approx(b.geo_rmse_px)
        assert a.cov_rmse_px == pytest.approx(b.cov_rmse_px)
        assert a.cov_rmse_local_px == pytest.approx(b.cov_rmse_local_px)
        assert (a.n_cov, a.n_cov_local) == (b.n_cov, b.n_cov_local)
        assert a.converged == b.converged and a.converged_local == b.converged_local
    assert pair.fit_meta["energies"] == word.fit_meta["energies"]
    # …and the one thing the pair harness reads differently
    assert set(pair.fit_meta["cov_window_px"]) == {"left", "right"}
    assert pair.fit_meta["cov_window_px"]["left"] == [round(v, 1) for v in windows[0]]
    assert pair.fit_meta["cov_window_px"]["right"] == [round(v, 1) for v in windows[1]]


def test_fit_pair_chain_recovers_the_two_injected_shifts() -> None:
    """The pair path end to end on synthetic ink — the Stage-A guarantee the
    refactor must not have moved."""
    injected = [(0.09, 0.02), (-0.06, -0.03)]
    case, result, _windows, truth_px = _synthetic_word(injected)
    dissection = SimpleNamespace(
        result=result, a=SimpleNamespace(body_px=[truth_px[0]]), b=SimpleNamespace(body_px=[truth_px[1]])
    )
    fit = fit_pair_chain(case, 0, dissection)
    assert fit is not None and fit.converged
    for slot, injected_shift in enumerate(injected):
        assert np.max(np.abs(_recovered(fit, slot) - np.asarray(injected_shift))) <= 0.05


def test_the_chain_iteration_budget_is_its_own_knob(monkeypatch: pytest.MonkeyPatch) -> None:
    """The chain gets its OWN iteration budget, read from the environment.

    Deliberately not `core.fit.DEFAULT_MAX_ITER`: that is a per-GLYPH budget on
    a per-glyph problem, and a word chain carries an order of magnitude more
    free parameters, so the same number buys proportionally fewer descent
    steps. Sharing it would also mean a measurement sweep on the chain silently
    re-tuned the production M4 fit.
    """
    import importlib

    import tools.pairlab.chain as chain_mod

    # Hermetic against a developer's exported sweep knob: the module reads the
    # env var at import time, so clear it and reload before asserting defaults.
    monkeypatch.delenv(chain_mod.CHAIN_MAX_ITER_ENV, raising=False)
    chain_mod = importlib.reload(chain_mod)

    assert chain_mod.CHAIN_MAX_ITER == chain_mod.CHAIN_MAX_ITER_DEFAULT
    # The whole point: it is NOT core.fit's per-glyph budget any more.
    assert chain_mod.CHAIN_MAX_ITER_DEFAULT > DEFAULT_MAX_ITER

    monkeypatch.setenv(chain_mod.CHAIN_MAX_ITER_ENV, "1234")
    reloaded = importlib.reload(chain_mod)
    try:
        assert reloaded.CHAIN_MAX_ITER == 1234
        # core.fit is untouched by the sweep knob — the production fit behind
        # the wizard, /fit and /diagnostic must not move because someone
        # measured the chain.
        import core.fit

        assert core.fit.DEFAULT_MAX_ITER == DEFAULT_MAX_ITER
    finally:
        monkeypatch.delenv(chain_mod.CHAIN_MAX_ITER_ENV)
        importlib.reload(chain_mod)


def test_a_capped_solve_is_reported_as_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    """`hit_iteration_cap` has to be true exactly when the BUDGET stopped the
    solve — a capped solve is still descending, so every energy, gate and
    anchor it reports is a snapshot of an unfinished descent rather than a
    result. Squeezing the budget to one iteration makes that state reachable
    without waiting for a hard case.
    """
    import importlib

    import tools.pairlab.chain as chain_mod

    # Hermetic against an exported KS_CHAIN_MAX_ITER (read at import time).
    monkeypatch.delenv(chain_mod.CHAIN_MAX_ITER_ENV, raising=False)
    chain_mod = importlib.reload(chain_mod)

    case, result, windows, _truth = _synthetic_word([(0.09, 0.02), (-0.06, -0.03), (0.04, -0.01)])
    generous = chain_mod.fit_word_chain(case, [0, 1, 2], result=result, windows_px=windows)
    assert generous is not None
    assert generous.fit_meta["hit_iteration_cap"] is False
    assert generous.fit_meta["max_iter"] == chain_mod.CHAIN_MAX_ITER_DEFAULT

    importlib.reload(chain_mod)
    chain_mod.CHAIN_MAX_ITER = 1
    starved = chain_mod.fit_word_chain(case, [0, 1, 2], result=result, windows_px=windows)
    importlib.reload(chain_mod)
    assert starved is not None
    assert starved.fit_meta["hit_iteration_cap"] is True
    assert starved.fit_meta["iterations"] <= 1


def _overlapping_specs(k: int = 6) -> list[ChainSegmentSpec]:
    """Two letters whose arcs run on top of each other — the collapse geometry."""
    a = _toy_letter(0.2, k)
    b = _toy_letter(0.35, k)  # 0.15 right of a: extended parallel proximity
    conn = _toy_connector(a[-1], b[0], 5)
    return [
        ChainSegmentSpec(
            kind="letter", anchors=a, slot_index=0, key="a", half_widths=np.full(k, 0.07), seam_in=0, seam_out=k - 1
        ),
        ChainSegmentSpec(kind="connector", anchors=conn, seam_in=0, seam_out=4),
        ChainSegmentSpec(
            kind="letter", anchors=b, slot_index=1, key="b", half_widths=np.full(k, 0.07), seam_in=0, seam_out=k - 1
        ),
    ]


def test_overlap_term_charges_stacked_segments_and_default_off_is_identical() -> None:
    """The exclusivity term (round 2): stacked letters pay, and at the default
    weight 0 the objective is BYTE-identical to before — the frozen Stage-A
    chainbench surface must not move because the term exists."""
    fields = _flat_fields()
    on = build_chain_problem(
        _overlapping_specs(), unit_px=UNIT_PX, x_origin_px=4.3, baseline_y_px=45.7, overlap_weight=1.0, **fields
    )
    terms_on, _ = on._evaluate(on.x0, want_grad=False)
    assert terms_on["e_overlap"] > 0.0, "stacked letters must be charged"

    apart = build_chain_problem(
        _toy_specs(), unit_px=UNIT_PX, x_origin_px=4.3, baseline_y_px=45.7, overlap_weight=1.0, **fields
    )
    terms_apart, _ = apart._evaluate(apart.x0, want_grad=False)
    assert terms_apart["e_overlap"] == 0.0, "letters a full advance apart share no ridge"

    off = build_chain_problem(
        _overlapping_specs(), unit_px=UNIT_PX, x_origin_px=4.3, baseline_y_px=45.7, overlap_weight=0.0, **fields
    )
    terms_off, _ = off._evaluate(off.x0, want_grad=False)
    assert terms_off["e_overlap"] == 0.0
    assert terms_off["f"] == pytest.approx(terms_on["f"] - 1.0 * terms_on["e_overlap"], abs=1e-12), (
        "weight 0 must reproduce the old objective exactly"
    )


def test_overlap_gradient_matches_finite_differences() -> None:
    """The load-bearing test, run ON an overlapping configuration: with the
    term active and paying, the analytic gradient must still agree with central
    differences — a wrong gradient stalls the line search silently."""
    problem = build_chain_problem(
        _overlapping_specs(), unit_px=UNIT_PX, x_origin_px=4.3, baseline_y_px=45.7, overlap_weight=0.5, **_flat_fields()
    )
    rng = np.random.default_rng(279)
    params = rng.uniform(-0.03, 0.03, size=len(problem.x0))
    terms, _ = problem._evaluate(params, want_grad=False)
    assert terms["e_overlap"] > 0.0, "the perturbed config must still overlap, or the test tests nothing"

    f0, grad = problem.objective(params)
    assert np.isfinite(f0) and np.all(np.isfinite(grad))
    eps = 1e-6
    for i in range(len(params)):
        step = np.zeros_like(params)
        step[i] = eps
        f_plus, _ = problem.objective(params + step)
        f_minus, _ = problem.objective(params - step)
        fd = (f_plus - f_minus) / (2.0 * eps)
        assert abs(fd - grad[i]) / max(1.0, abs(fd)) < 1e-5, f"param {i}: fd={fd}, analytic={grad[i]}"


def test_overlap_seam_band_is_exempt_for_adjacent_segments() -> None:
    """Samples inside the §5 stub band around a shared seam are the overlap the
    hand REALLY writes — adjacent segments must not be billed for them, while
    letter-letter proximity (two segments apart) never gets the exemption."""
    problem = build_chain_problem(
        _overlapping_specs(), unit_px=UNIT_PX, x_origin_px=4.3, baseline_y_px=45.7, overlap_weight=1.0, **_flat_fields()
    )
    assert problem.overlap_exempt.any(), "seam bands must mark some samples"
    # Rebuild the kept pair set exactly as _evaluate does and assert no kept
    # pair is an exempt adjacent one, while letter-letter pairs survive.
    from scipy.spatial import cKDTree

    ap = problem.plan_anchors(problem.x0)
    px = problem.x_origin_px + (problem.sampling_op @ ap[:, 0]) * problem.unit_px
    py = problem.baseline_y_px - (problem.sampling_op @ ap[:, 1]) * problem.unit_px
    pts = np.column_stack([px, py])
    pairs = cKDTree(pts).query_pairs(problem.overlap_radius_px, output_type="ndarray")
    si, sj = problem.seg_of_sample[pairs[:, 0]], problem.seg_of_sample[pairs[:, 1]]
    cross = pairs[si != sj]
    si, sj = problem.seg_of_sample[cross[:, 0]], problem.seg_of_sample[cross[:, 1]]
    adjacent_exempt = (np.abs(si - sj) == 1) & problem.overlap_exempt[cross[:, 0]] & problem.overlap_exempt[cross[:, 1]]
    assert adjacent_exempt.any(), "the toy seam neighbourhood must produce exempt adjacent pairs"
    assert (np.abs(si - sj) == 2).any(), "letter-letter pairs must remain billable"


def test_a_block_seed_changes_the_start_not_the_objective() -> None:
    """`slot_shift_init` is the round-2 counter to the placement collapse:
    it may only move WHERE the descent starts, never what is measured.

    Three properties the A/B rests on: an absent seed and an all-zero seed are
    the same solve; a seed at the injected truth still recovers that truth (the
    objective's optimum did not move); and the applied seed is recorded in
    `fit_meta` for the diagnostics.
    """
    injected = [(0.10, 0.0), (-0.08, 0.04), (0.05, -0.03)]
    case, result, windows, _ = _synthetic_word(injected)

    plain = fit_word_chain(case, [0, 1, 2], result=result, windows_px=windows)
    zeroed = fit_word_chain(
        case, [0, 1, 2], result=result, windows_px=windows, slot_shift_init={0: (0.0, 0.0), 1: (0.0, 0.0)}
    )
    assert plain is not None and zeroed is not None
    # Identical start → identical solve, down to the reported energies.
    assert plain.fit_meta["energies"] == zeroed.fit_meta["energies"]
    assert plain.fit_meta["slot_shift_init"] == {}
    assert zeroed.fit_meta["slot_shift_init"] == {"0": [0.0, 0.0], "1": [0.0, 0.0]}

    seeded = fit_word_chain(
        case, [0, 1, 2], result=result, windows_px=windows, slot_shift_init=dict(enumerate(injected))
    )
    assert seeded is not None and seeded.converged
    for slot, injected_shift in enumerate(injected):
        assert np.max(np.abs(_recovered(seeded, slot) - np.asarray(injected_shift))) <= 0.05
    # Starting AT the truth, the blocks barely move from their seed.
    for slot, (sx, sy) in enumerate(injected):
        got = np.asarray(seeded.slot_shift_units[slot])
        assert np.max(np.abs(got - np.array([sx, sy]))) <= 0.05


def test_a_block_seed_is_clipped_inside_the_bounds() -> None:
    """A wild grid delta must not start a solve already at `slot_at_bound` —
    the seed is clipped strictly inside ±FIT_DX/DY_UNITS, and a slot the run
    does not contain is ignored rather than crashing the solve."""
    case, result, windows, _ = _synthetic_word([(0.05, 0.0), (0.0, 0.0)])

    fit = fit_word_chain(
        case, [0, 1], result=result, windows_px=windows, slot_shift_init={0: (99.0, -99.0), 7: (0.1, 0.1)}
    )
    assert fit is not None
    sx, sy = fit.fit_meta["slot_shift_init"]["0"]
    assert abs(sx) < FIT_DX_UNITS and abs(sy) < FIT_DY_UNITS
    assert "7" not in fit.fit_meta["slot_shift_init"]
