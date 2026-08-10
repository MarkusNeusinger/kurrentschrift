"""Unit tests for the A/B evaluation in `tools.pairlab.bindab`.

These functions produced a published REJECTION (`qualitaetsmetrik.md` §11d), so
an error here would not fail loudly — it would quietly decide a term's fate.
The solving half needs the frozen fixtures and hours of CPU; the deciding half
is pure and is pinned here.
"""

from __future__ import annotations

import math

import pytest

from tools.pairlab.bindab import evaluate, mcnemar


def _row(weight: float, slot: int, **over) -> dict:
    """One occurrence row with everything `evaluate` reads."""
    base = {
        "set": "words",
        "weight": weight,
        "specimen": "das",
        "run": "0-1-2",
        "slot": slot,
        "key": "d",
        "gate": "ok",
        "accepted": 1,
        "geo_rmse_px": 1.0,
        "cov_rmse_local_px": 1.0,
        "off_ink_share": 0.10,
        "n_off_ink": 12,
        "n_anchors": 120,
        "n_stranded": 1,
        "anchor_spike_ratio": 3.0,
        "iterations": 1000,
        "hit_iteration_cap": 0,
    }
    return {**base, **over}


# ------------------------------------------------------------------- McNemar


def test_mcnemar_ignores_the_concordant_pairs() -> None:
    """The test is about the FLIPS — agreement carries no information.

    This is why §11 correction 3 replaced „rejections under 23": a count of
    rejections moves with occurrences that never changed side.
    """
    flips = [(True, True)] * 200 + [(False, False)] * 200 + [(False, True)] * 3
    out = mcnemar(flips)
    assert (out["gained"], out["lost"]) == (3, 0)
    assert out["p"] == pytest.approx(0.25)  # 2 * (1/2)^3


def test_mcnemar_is_symmetric_and_exact() -> None:
    a = mcnemar([(False, True)] * 9 + [(True, False)] * 1)
    b = mcnemar([(False, True)] * 1 + [(True, False)] * 9)
    assert a["p"] == pytest.approx(b["p"])
    assert a["p"] == pytest.approx(2 * (1 + 10) / 2**10)  # k=1: (C(10,0)+C(10,1))/2^10, doubled
    assert mcnemar([])["p"] == 1.0
    assert mcnemar([(True, True)])["p"] == 1.0


# ------------------------------------------------------- the benefit measure


def test_a_clean_baseline_that_the_arm_spoils_is_not_reported_as_unchanged() -> None:
    """The regression Copilot found: 0 % would read as „nothing happened".

    A baseline with no off-ink anchors and an arm that introduces them is an
    unbounded regression, and it must never satisfy the pre-registered fall.
    """
    rows = [_row(0.0, 0, off_ink_share=0.0, n_off_ink=0), _row(1.0, 0, off_ink_share=0.2, n_off_ink=24)]
    out = evaluate(rows, 0.0, 1.0)
    assert out["off_ink_rel_pct"] == math.inf
    assert out["benefit_ok"] is False


def test_no_off_ink_anchors_on_either_side_is_not_a_pass() -> None:
    """Nothing to improve is not an improvement — `nan`, and never `benefit_ok`."""
    rows = [_row(0.0, 0, off_ink_share=0.0, n_off_ink=0), _row(1.0, 0, off_ink_share=0.0, n_off_ink=0)]
    out = evaluate(rows, 0.0, 1.0)
    assert math.isnan(out["off_ink_rel_pct"])
    assert out["benefit_ok"] is False


def test_the_pre_registered_fall_is_what_passes() -> None:
    rows = [_row(0.0, 0, off_ink_share=0.10), _row(1.0, 0, off_ink_share=0.07)]
    assert evaluate(rows, 0.0, 1.0)["benefit_ok"] is True  # −30 %
    rows = [_row(0.0, 0, off_ink_share=0.10), _row(1.0, 0, off_ink_share=0.08)]
    assert evaluate(rows, 0.0, 1.0)["benefit_ok"] is False  # −20 %, short of −25 %


# ----------------------------------------------------------------- the costs


def test_a_single_ruined_occurrence_is_not_averaged_away() -> None:
    """§11 correction 3: the bounds are per occurrence, with a p90.

    Nine untouched occurrences and one wrecked one leave the MEDIAN at zero —
    the quantile bound is the whole reason it is not judged on the median
    alone.
    """
    rows = [_row(0.0, i) for i in range(10)]
    rows += [_row(1.0, i, geo_rmse_px=1.0) for i in range(9)]
    rows += [_row(1.0, 9, geo_rmse_px=2.0)]  # one occurrence doubles its residual
    out = evaluate(rows, 0.0, 1.0)
    assert out["geo_rmse"]["median_pct"] == pytest.approx(0.0)
    assert out["geo_rmse"]["p90_pct"] == pytest.approx(100.0)
    assert out["geo_rmse"]["worse"] == 1
    assert out["cost_ok"] is False  # p90 blows the +10 % bound


def test_losing_accepted_occurrences_fails_the_cost_side() -> None:
    """No net loss of yield is a pre-registered bound, not a nice-to-have."""
    rows = [_row(0.0, i, accepted=1) for i in range(4)]
    rows += [_row(1.0, i, accepted=1) for i in range(3)] + [_row(1.0, 3, accepted=0, gate="geo_rmse")]
    out = evaluate(rows, 0.0, 1.0)
    assert (out["accepted_base"], out["accepted_arm"]) == (4, 3)
    assert out["cost_ok"] is False


def test_the_pairing_only_uses_occurrences_present_in_both_arms() -> None:
    """An arm that silently loses a solve must not shrink the comparison base."""
    rows = [_row(0.0, 0), _row(0.0, 1), _row(1.0, 0)]
    out = evaluate(rows, 0.0, 1.0)
    assert out["n_occurrences"] == 1
    assert out["accepted_base"] == 1  # …and the baseline count is over the PAIRED set


def test_identical_arms_cost_nothing_and_benefit_nothing() -> None:
    """The baseline against itself — the shape of the weight-0 row in the report."""
    rows = [_row(0.0, i) for i in range(5)] + [_row(0.0, i) for i in range(5)]
    out = evaluate(rows, 0.0, 0.0)
    assert out["off_ink_rel_pct"] == pytest.approx(0.0)
    assert out["geo_rmse"]["median_pct"] == pytest.approx(0.0)
    assert out["gate_flips"] == {"gained": 0, "lost": 0, "p": 1.0}
    assert out["cost_ok"] is True
    assert out["benefit_ok"] is False
