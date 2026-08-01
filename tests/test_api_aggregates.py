"""The per-hand aggregate endpoints (Stufenplan H1): read + rebuild.

Same in-memory aiosqlite stack as the other HTTP suites (`tests/api_harness.py`
via the `api` fixture). Occurrences are written through the real
`PUT /sources/{id}/instances` batch so the hand row is created the way
production does it. Proves the median/hull round-trip, the min_n gate, the
replace semantics, the Laufform Prüfstein and the admin gate.
"""

from __future__ import annotations

from tests.api_harness import Harness


# The harness template has six anchors — the Laufform PUT requires the exact
# same count, so occurrences carry six as well.
CHART_ANCHORS = [[0.0, 0.0], [0.05, 0.45], [0.12, 0.62], [0.25, 0.55], [0.32, 0.25], [0.35, 0.0]]


def _shifted(dx: float) -> list[list[float]]:
    """The chart anchors with the last anchor's x moved — a nontrivial median.

    Rounded like the aggregation itself (4 decimals) so binary float artefacts
    of the shift do not show up as expected values."""
    anchors = [list(a) for a in CHART_ANCHORS]
    anchors[-1] = [round(anchors[-1][0] + dx, 4), anchors[-1][1]]
    return anchors


def _instance_item(**overrides) -> dict:
    item = {
        "glyph_key": "n",
        "glyph": "n",
        "position": "medial",
        "y0": 10,
        "y1": 40,
        "x0": 100,
        "x1": 130,
        "anchors": CHART_ANCHORS,
        "measurements": {"specimen_id": "wenn", "geo_rmse_px": 1.5, "xh_px": 30.0},
    }
    item.update(overrides)
    return item


def _batch(items: list[dict], **overrides) -> dict:
    body = {"hand": {"id": "test-hand", "label": "Test norm hand", "era": "1922"}, "items": items}
    body.update(overrides)
    return body


async def _seed_occurrences(api: Harness, source_id: str, anchor_shifts: list[float], **item_overrides) -> None:
    """One occurrence per shift, each at its own crop x (the identity column)."""
    items = [
        _instance_item(anchors=_shifted(dx), x0=100 + 10 * n, x1=130 + 10 * n, **item_overrides)
        for n, dx in enumerate(anchor_shifts)
    ]
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/instances", json_body=_batch(items), headers=api.admin_headers()
    )
    assert res.status == 200, res.body


async def test_rebuild_stores_medians_and_hull(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    # x shifts 0.0 / 0.02 / 0.06 / 0.08 → median 0.04, MAD 0.03.
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])

    res = await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())
    assert res.status == 200, res.body
    out = res.json()
    assert out["hand_id"] == "test-hand"
    assert out["stored"] == 1
    assert out["deleted"] == 0
    assert out["skipped"] == {"anchor_shape": 0, "below_min_n": 0}
    assert out["keys"] == [{"glyph_key": "n", "variant": 0, "n_instances": 4, "laufform_dev_xh": None}]

    res = await api.client.request("GET", "/hands/test-hand/aggregates", headers=api.admin_headers())
    assert res.status == 200
    rows = res.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["glyph_key"] == "n" and row["glyph"] == "n" and row["variant"] == 0
    assert row["n_instances"] == 4
    assert row["cluster_center"] == _shifted(0.04)
    assert row["hull"]["anchor_mad"][-1] == [0.03, 0.0]
    assert row["hull"]["anchor_mad"][0] == [0.0, 0.0]
    assert row["mean_stats"]["geo_rmse_px"] == {"mean": 1.5, "max": 1.5}
    assert row["mean_stats"]["xh_px_mean"] == 30.0
    assert row["mean_stats"]["positions"] == {"medial": 4}
    assert row["mean_stats"]["n_specimens"] == 1


async def test_rebuild_min_n_gate_skips_and_reports(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06])

    res = await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())
    out = res.json()
    assert out["stored"] == 0 and out["keys"] == []
    assert out["skipped"] == {"anchor_shape": 0, "below_min_n": 3}
    res = await api.client.request("GET", "/hands/test-hand/aggregates", headers=api.admin_headers())
    assert res.json() == []

    # A lower gate aggregates the same three occurrences.
    res = await api.client.request(
        "POST", "/hands/test-hand/aggregates/rebuild", params={"min_n": 3}, headers=api.admin_headers()
    )
    assert res.json()["stored"] == 1


async def test_rebuild_reports_the_laufform_pruefstein(api: Harness):
    """H1's check: the median recomputed from the persisted occurrences must
    reproduce the stored running form (variant 100)."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/templates/n/laufform",
        json_body={"anchors": _shifted(0.04), "n_occurrences": 4},
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body

    res = await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())
    assert res.json()["keys"] == [{"glyph_key": "n", "variant": 0, "n_instances": 4, "laufform_dev_xh": 0.0}]

    # A Laufform that does NOT match the occurrences shows up as a distance:
    # one anchor moved by 0.6 over six anchors → mean 0.1.
    drifted = _shifted(0.04)
    drifted[2] = [drifted[2][0] + 0.6, drifted[2][1]]
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/templates/n/laufform",
        json_body={"anchors": drifted, "n_occurrences": 4},
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body
    res = await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())
    assert res.json()["keys"][0]["laufform_dev_xh"] == 0.1


async def test_rebuild_replaces_stale_rows(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    res = await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())
    assert res.json()["stored"] == 1

    # A stricter gate no longer produces the key — the stale row must go, not
    # linger with its old median.
    res = await api.client.request(
        "POST", "/hands/test-hand/aggregates/rebuild", params={"min_n": 5}, headers=api.admin_headers()
    )
    out = res.json()
    assert out == {
        "hand_id": "test-hand",
        "stored": 0,
        "deleted": 1,
        "skipped": {"anchor_shape": 0, "below_min_n": 4},
        "keys": [],
    }
    res = await api.client.request("GET", "/hands/test-hand/aggregates", headers=api.admin_headers())
    assert res.json() == []


async def test_aggregate_endpoints_are_admin_gated_and_404_unknown_hand(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])

    # Learned geometry is never public (quellen-und-rechte.md §5).
    res = await api.client.request("GET", "/hands/test-hand/aggregates")
    assert res.status == 401
    res = await api.client.request("POST", "/hands/test-hand/aggregates/rebuild")
    assert res.status == 401

    res = await api.client.request("GET", "/hands/nope/aggregates", headers=api.admin_headers())
    assert res.status == 404
    res = await api.client.request("POST", "/hands/nope/aggregates/rebuild", headers=api.admin_headers())
    assert res.status == 404
