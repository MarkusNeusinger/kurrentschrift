"""The two gates in front of a Laufform write (qualitaetsmetrik.md §14 LF7/LF8).

Same aiosqlite HTTP stack as the other API suites. The manual
`PUT …/templates/{key}/laufform` and `POST …/aggregates/apply-laufform` share
the evidence floor (`LAUFFORM_MIN_OCCURRENCES`, lowered only by an explicit
`?min_occurrences`) and the row gate (the anchor spike ratio of the row about
to be written against `LAUFFORM_SPIKE_RATIO_MAX`, no override).
"""

from __future__ import annotations

import pytest

from core.aggregate import LAUFFORM_MIN_OCCURRENCES
from core.laufform import LAUFFORM_SPIKE_RATIO_MAX, anchor_spike_ratio
from tests.api_harness import Harness


# The harness template's six anchors (see tests/test_api_aggregates.py).
CHART_ANCHORS = [[0.0, 0.0], [0.05, 0.45], [0.12, 0.62], [0.25, 0.55], [0.32, 0.25], [0.35, 0.0]]


def _shifted(dx: float) -> list[list[float]]:
    """A rigid x shift — a smooth, spike-free running form."""
    return [[round(x + dx, 4), y] for x, y in CHART_ANCHORS]


def _spiked() -> list[list[float]]:
    """One anchor left the stroke and came back — „Anker im leeren Papier"."""
    anchors = [list(a) for a in CHART_ANCHORS]
    anchors[3] = [anchors[3][0] + 2.0, anchors[3][1]]
    return anchors


def test_fixtures_sit_on_the_right_sides_of_the_gate():
    assert LAUFFORM_SPIKE_RATIO_MAX is not None
    assert anchor_spike_ratio(_shifted(0.04), [0]) < LAUFFORM_SPIKE_RATIO_MAX
    assert anchor_spike_ratio(_spiked(), [0]) > LAUFFORM_SPIKE_RATIO_MAX


async def _put(api: Harness, source_id: str, anchors, n: int, **params):
    return await api.client.request(
        "PUT",
        f"/sources/{source_id}/templates/n/laufform",
        json_body={"anchors": anchors, "n_occurrences": n},
        headers=api.admin_headers(),
        params=params or None,
    )


async def test_put_refuses_a_draft_below_the_floor_unless_the_request_lowers_it(api: Harness):
    """The K came in through this endpoint with n = 1 and nobody was asked.
    The floor now holds here too; lowering it is an explicit author statement
    in the request itself, never a default."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")

    res = await _put(api, source_id, _shifted(0.04), LAUFFORM_MIN_OCCURRENCES - 1)
    assert res.status == 422
    assert "below the floor" in res.json()["detail"]
    assert "min_occurrences=1" in res.json()["detail"]

    res = await _put(api, source_id, _shifted(0.04), LAUFFORM_MIN_OCCURRENCES)
    assert res.status == 200, res.body

    res = await _put(api, source_id, _shifted(0.06), 1, min_occurrences=1)
    assert res.status == 200, res.body
    assert res.json()["trace_meta"]["laufform"]["n_occurrences"] == 1


async def test_put_refuses_a_spiked_draft_without_any_override(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")

    res = await _put(api, source_id, _spiked(), LAUFFORM_MIN_OCCURRENCES)
    assert res.status == 422
    detail = res.json()["detail"]
    assert "anchor spike" in detail and "no override" in detail
    assert f"{LAUFFORM_SPIKE_RATIO_MAX:.2f}" in detail

    # Lowering the floor does not open the row gate — the two are different
    # questions (evidence vs. the row's own shape).
    res = await _put(api, source_id, _spiked(), 1, min_occurrences=1)
    assert res.status == 422

    # Nothing was written.
    res = await api.client.request(
        "GET", f"/sources/{source_id}/templates/n", params={"variant": 100}, headers=api.admin_headers()
    )
    assert res.status == 404


async def test_gate_off_admits_the_spiked_draft(api: Harness, monkeypatch: pytest.MonkeyPatch):
    """`None` turns the row gate off (the pre-LF8 behaviour, reachable on
    purpose for a re-measurement) — the floor still stands."""
    monkeypatch.setattr("core.laufform.LAUFFORM_SPIKE_RATIO_MAX", None)
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    res = await _put(api, source_id, _spiked(), LAUFFORM_MIN_OCCURRENCES)
    assert res.status == 200, res.body


async def test_apply_skips_a_spiked_median_and_says_why(api: Harness):
    """The aggregate path reports the row gate as a skip with the numbers —
    the same reason code the harvest's own fit gate uses (`anchor_spike`)."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    # Every occurrence carries the same spike, so the median carries it too.
    items = [
        {
            "glyph_key": "n",
            "glyph": "n",
            "position": "medial",
            "y0": 10,
            "y1": 40,
            "x0": 100 + 10 * k,
            "x1": 130 + 10 * k,
            "anchors": _spiked(),
            "measurements": {"specimen_id": "wenn", "geo_rmse_px": 1.5, "xh_px": 30.0},
        }
        for k in range(LAUFFORM_MIN_OCCURRENCES)
    ]
    body = {"hand": {"id": "test-hand", "label": "Test norm hand", "era": "1922"}, "items": items}
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/instances", json_body=body, headers=api.admin_headers()
    )
    assert res.status == 200, res.body
    await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())

    res = await api.client.request("POST", "/hands/test-hand/aggregates/apply-laufform", headers=api.admin_headers())
    assert res.status == 200, res.body
    out = res.json()
    assert out["applied"] == []
    assert len(out["skipped"]) == 1
    skip = out["skipped"][0]
    assert skip["glyph_key"] == "n" and skip["reason"] == "anchor_spike"
    assert skip["spike_max"] == LAUFFORM_SPIKE_RATIO_MAX
    assert skip["spike_ratio"] > LAUFFORM_SPIKE_RATIO_MAX
    assert skip["n_instances"] is None
