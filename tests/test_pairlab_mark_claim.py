"""K-E stage 1, the mark-claim separation (`tools.pairlab.chain`, §14 `aug21`).

Pins the measure's four promises without fixtures, DB or network: (1) the
claim rule — a composed mark stroke claims exactly the dark component within
the ruler's mark radius, never the main body, never a far blob; (2) a claim
splits BOTH pull channels (field lookup and coverage assignment) per sample
class while the analytic gradient stays exact; (3) with no claim — flag off,
no diacritic stroke, or no component in reach — every path hands back the
unsplit block, which is what the byte-identity gates of the pre-registration
rest on; (4) the knob defaults off everywhere.
"""

from __future__ import annotations

import numpy as np

from tools.laufform.harvest import HarvestOptions
from tools.pairlab.chain import (
    MARK_CLAIM_RADIUS_UNITS,
    ChainSegmentSpec,
    _field_stack,
    _prepare_fields,
    build_chain_problem,
    fit_word_chain,
)
from tools.pairlab.follow import FollowWeights
from tools.tracebench.frames import MARK_MATCH_RADIUS_UNITS
from tools.wordlab.cases import WordCase


UNIT_PX = 20.0


# --------------------------------------------------------------- toy material


def _toy_case(*, dot_at: tuple[int, int] | None = (12, 30)) -> WordCase:
    """A case whose ink is a horizontal body stroke plus an optional dot blob."""
    skel = np.zeros((60, 90), dtype=bool)
    skel[40, 5:80] = True  # the body ridge
    width = np.where(skel, 2.0, 0.0)
    if dot_at is not None:
        r, c = dot_at
        skel[r, c : c + 3] = True
        width[r - 1 : r + 2, c - 1 : c + 4] = 2.0
    return WordCase(
        id="toy",
        word="i",
        kind="word",
        slots=[],
        templates={},
        style_ratio=[1, 1, 1],
        width_resolver="constant",
        nib_units=0.07,
        skel=skel,
        width_map=width,
    )


def _mark_stroke(points_px: np.ndarray, seg: int = 0, start: int = 6) -> dict:
    return {"seg": seg, "start": start, "key": "i", "points_px": np.asarray(points_px, dtype=float)}


# ------------------------------------------------------------- the claim rule


def test_the_radius_is_the_rulers_mark_radius() -> None:
    """Mirrored, not imported — and pinned so the two can never drift."""
    assert MARK_CLAIM_RADIUS_UNITS == MARK_MATCH_RADIUS_UNITS


def test_a_near_mark_stroke_claims_the_dot_and_the_fields_split() -> None:
    case = _toy_case()
    stroke = _mark_stroke(np.array([[29.0, 13.5], [33.0, 13.5]]))  # ~1.5 px from the blob
    fields = _prepare_fields(case, 0, 89, mark_strokes_px=[stroke], unit_px=UNIT_PX)
    assert fields is not None and len(fields["mark_fields"]) == 1
    assert [c["key"] for c in fields["mark_claims"]] == ["i"]
    assert fields["mark_claims"][0]["dist_units"] <= MARK_CLAIM_RADIUS_UNITS
    # both channels split: the body stack no longer contains the dot …
    assert fields["dist_raw"][12, 31] > 3.0  # the dot row reads far-from-ink in the body field
    assert not fields["skel"][12, 31]
    assert not (fields["cov_pts"][:, 1] < 20).any()  # no body coverage target in the dot's rows
    # … and the mark stack contains ONLY the dot
    mark = fields["mark_fields"][0]
    assert (mark["seg"], mark["start"]) == (0, 6)
    assert mark["dist_raw"][12, 31] == 0.0 and mark["dist_raw"][40, 40] > 10.0
    assert (mark["cov_pts"][:, 1] < 20).all()
    # K-E2: the width channel is NOT split — the mark stack carries no width,
    # and the body width field still propagates from ALL kept ink (the dot).
    assert "width_raw" not in mark and "width_smooth" not in mark
    assert fields["width_raw"][12, 31] > 0.0


def test_a_far_blob_is_not_claimed_and_the_block_stays_unsplit() -> None:
    case = _toy_case()
    stroke = _mark_stroke(np.array([[60.0, 5.0], [64.0, 5.0]]))  # > 0.6 xh from the blob
    fields = _prepare_fields(case, 0, 89, mark_strokes_px=[stroke], unit_px=UNIT_PX)
    assert fields is not None and "mark_fields" not in fields
    assert fields["mark_claims"] == []
    assert fields["skel"][12, 31]  # the blob stays body evidence


def test_off_and_no_stroke_hand_back_the_historical_block() -> None:
    case = _toy_case()
    plain = _prepare_fields(case, 0, 89)
    with_flag = _prepare_fields(case, 0, 89, mark_strokes_px=None, unit_px=UNIT_PX)
    assert plain is not None and "mark_claims" not in plain and "mark_fields" not in plain
    assert np.array_equal(plain["dist_raw"], with_flag["dist_raw"])
    assert np.array_equal(plain["cov_pts"], with_flag["cov_pts"])


# ------------------------------------------- the problem: classes and gradient


def _dotted_specs() -> list[ChainSegmentSpec]:
    """One letter whose second pen stroke floats above the diacritic line."""
    t = np.linspace(0.0, 1.0, 6)
    body = np.column_stack([0.2 + t, 0.4 * np.sin(np.pi * t)])
    dot = np.array([[0.45, 1.25], [0.5, 1.3], [0.55, 1.25]])
    return [
        ChainSegmentSpec(
            kind="letter",
            anchors=np.vstack([body, dot]),
            slot_index=0,
            key="i",
            stroke_starts=(0, 6),
            half_widths=np.full(9, 0.07),
        )
    ]


def _dotted_problem():
    from scipy.ndimage import distance_transform_edt, gaussian_filter  # noqa: PLC0415

    from core.fit import DIST_FIELD_SIGMA_PX, WIDTH_FIELD_SIGMA_PX, _skeleton_points  # noqa: PLC0415

    shape = (60, 60)
    ink = np.zeros(shape, dtype=bool)
    for c in range(4, 56):
        ink[int(round(0.4 * c)) + 8, c] = True
    dist_raw = distance_transform_edt(~ink).astype(float)
    body_fields = {
        "dist_raw": dist_raw,
        "dist_smooth": gaussian_filter(dist_raw, DIST_FIELD_SIGMA_PX),
        "width_raw": np.full(shape, 1.5),
        "width_smooth": gaussian_filter(np.full(shape, 1.5), WIDTH_FIELD_SIGMA_PX),
        "cov_pts": _skeleton_points(ink),
        "crop_shape": shape,
    }
    # the dot's own component sits where the composed dot lands (~14, 21);
    # width keys stripped exactly as `_prepare_fields` ships them (K-E2)
    dot_ink = np.zeros(shape, dtype=bool)
    dot_ink[20:23, 13:16] = True
    stack = {k: v for k, v in _field_stack(dot_ink, np.where(dot_ink, 1.5, 0.0)).items() if "width" not in k}
    mark = {"seg": 0, "start": 6, **stack}
    return build_chain_problem(
        _dotted_specs(),
        unit_px=UNIT_PX,
        x_origin_px=4.3,
        baseline_y_px=45.7,
        n_samples=48,
        **body_fields,
        mark_fields=[mark],
    )


def test_the_dot_stroke_reads_its_own_field_and_nothing_else() -> None:
    problem = _dotted_problem()
    assert problem.field_of_sample is not None and len(problem.mark_fields) == 1
    dot_rows = problem.field_of_sample == 1
    assert dot_rows.any() and (~dot_rows).any()
    # the class boundary is exactly the pen stroke: dot samples are the second stroke
    assert set(problem.stroke_of_sample[dot_rows]) == {1}
    assert set(problem.stroke_of_sample[~dot_rows]) == {0}
    terms = problem.energy_terms(problem.x0)
    assert np.isfinite(terms["f"])


def test_the_class_aware_gradient_stays_exact() -> None:
    """The load-bearing check of `test_pairlab_chain`, on the SPLIT problem."""
    problem = _dotted_problem()
    rng = np.random.default_rng(414)
    params = rng.uniform(-0.05, 0.05, size=len(problem.x0))
    f0, grad = problem.objective(params)
    assert np.isfinite(f0) and np.all(np.isfinite(grad))
    eps = 1e-6
    for i in range(len(params)):
        step = np.zeros_like(params)
        step[i] = eps
        fd = (problem.objective(params + step)[0] - problem.objective(params - step)[0]) / (2.0 * eps)
        assert abs(fd - grad[i]) / max(1.0, abs(fd)) < 1e-5, f"param {i}: fd={fd}, analytic={grad[i]}"


def test_without_mark_fields_the_problem_is_the_historical_one() -> None:
    problem = _dotted_problem()
    plain = build_chain_problem(
        _dotted_specs(),
        unit_px=UNIT_PX,
        x_origin_px=4.3,
        baseline_y_px=45.7,
        n_samples=48,
        **{k: getattr(problem, k) for k in ("dist_raw", "dist_smooth", "width_raw", "width_smooth", "cov_pts")},
        crop_shape=(problem.crop_h, problem.crop_w),
    )
    assert plain.field_of_sample is None and plain.mark_fields == []
    # identical structure, and the single-field code path serves the lookups
    assert np.array_equal(plain.seg_of_sample, problem.seg_of_sample)


# ------------------------------------------------------- end-to-end word chain


def test_a_word_without_a_diacritic_is_byte_identical_under_the_flag() -> None:
    from tests.test_laufform_harvest import _synthetic_word  # noqa: PLC0415

    case, result = _synthetic_word([(0.06, 0.0), (-0.04, 0.03)])
    windows = {0: (0.0, float(case.skel.shape[1])), 1: (0.0, float(case.skel.shape[1]))}
    off = fit_word_chain(case, [0, 1], result=result, windows_px=windows, keep_solve=True)
    on = fit_word_chain(case, [0, 1], result=result, windows_px=windows, keep_solve=True, mark_claim=True)
    assert off is not None and on is not None
    assert np.array_equal(off.params, on.params)
    assert on.fit_meta["mark_claims"] == []  # the flag SAYS nothing fired
    assert "mark_claims" not in off.fit_meta  # the default artefact stays untouched


def test_the_defaults_are_off_everywhere() -> None:
    assert FollowWeights().mark_claim is False
    assert HarvestOptions().mark_claim is False
