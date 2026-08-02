"""The per-hand pair-aggregate endpoints (Stufenplan H2): read + rebuild.

Same in-memory aiosqlite stack as the other HTTP suites (`tests/api_harness.py`
via the `api` fixture). Join occurrences are written through the real
`PUT /sources/{id}/pair-instances` batch so the hand row is created the way
production does it. Proves the median/hull round-trip, the QC gate, the min_n
gate, the replace semantics, the per-hand scoping and the admin gate.
"""

from __future__ import annotations

from tests.api_harness import Harness


def _pair_item(offset: list[float], **overrides) -> dict:
    """One clean join occurrence. The connector is the straight line from the
    left glyph's exit to the placement offset, so the arc-length resampling
    stays hand-checkable: point i of n sits at offset * i / (n - 1)."""
    item = {
        "left_key": "n",
        "right_key": "e",
        "kind": "word",
        "specimen_id": "wenn",
        "slot": 1,
        "geometry": {"offset": offset, "connector": [[0.0, 0.0], list(offset)]},
        "measurements": {"fit_ok": True, "gen_chamfer": 0.2, "gap_ink": True, "a_resid": 0.1, "b_resid": 0.05},
    }
    item.update(overrides)
    return item


def _batch(items: list[dict], hand_id: str = "test-hand", **overrides) -> dict:
    body = {"hand": {"id": hand_id, "label": "Test norm hand", "era": "1922"}, "items": items}
    body.update(overrides)
    return body


async def _seed_pairs(api: Harness, source_id: str, items: list[dict], hand_id: str = "test-hand") -> None:
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/pair-instances",
        json_body=_batch(items, hand_id=hand_id),
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body


# Three occurrences of n→e: offsets 0.4 / 0.6 / 0.5 → median 0.5, MAD 0.1;
# gen_chamfer 0.2 / 0.3 / 0.4 → mean 0.3, max 0.4. The worse letter fit per
# row is 0.10 / 0.12 / 0.08 → resid mean 0.1, max 0.12.
NE_ITEMS = [
    _pair_item([0.4, 0.0]),
    _pair_item(
        [0.6, 0.0],
        slot=2,
        measurements={"fit_ok": True, "gen_chamfer": 0.3, "gap_ink": True, "a_resid": 0.04, "b_resid": 0.12},
    ),
    _pair_item(
        [0.5, 0.0],
        specimen_id="denen",
        measurements={"fit_ok": True, "gen_chamfer": 0.4, "gap_ink": False, "a_resid": 0.08, "b_resid": 0.03},
    ),
]


async def test_rebuild_stores_medians_and_hull(api: Harness):
    _, source_id = await api.seed_style_and_source()
    await _seed_pairs(api, source_id, NE_ITEMS)

    res = await api.client.request("POST", "/hands/test-hand/pair-aggregates/rebuild", headers=api.admin_headers())
    assert res.status == 200, res.body
    out = res.json()
    assert out["hand_id"] == "test-hand"
    assert out["stored"] == 1
    assert out["deleted"] == 0
    assert out["skipped"] == {"fit_bad": 0, "geometry": 0, "below_min_n": 0}
    # The audit number: how far the GENERATED connector sat from the specimen.
    assert out["pairs"] == [{"left_key": "n", "right_key": "e", "n_instances": 3, "gen_chamfer_mean": 0.3}]

    res = await api.client.request("GET", "/hands/test-hand/pair-aggregates", headers=api.admin_headers())
    assert res.status == 200
    rows = res.json()
    assert len(rows) == 1
    row = rows[0]
    assert row["left_key"] == "n" and row["right_key"] == "e"
    assert row["n_instances"] == 3
    assert row["offset_center"] == [0.5, 0.0]
    # 24 arc-length samples, endpoints preserved — and the last connector point
    # is the placement offset (the harvest's frame invariant, not enforced).
    assert len(row["connector_center"]) == 24
    assert row["connector_center"][0] == [0.0, 0.0]
    assert row["connector_center"][-1] == row["offset_center"]
    assert row["hull"]["offset_mad"] == [0.1, 0.0]
    assert len(row["hull"]["connector_mad"]) == 24
    assert row["mean_stats"]["gen_chamfer"] == {"mean": 0.3, "max": 0.4}
    # The harvest's own fit_ok quantity, pooled: how marginal these joins were.
    assert row["mean_stats"]["resid"] == {"mean": 0.1, "max": 0.12}
    assert row["mean_stats"]["gap_ink_share"] == 0.667
    assert row["mean_stats"]["kinds"] == {"word": 3}
    assert row["mean_stats"]["n_specimens"] == 2


async def test_pair_listing_narrows_by_left_and_right_key(api: Harness):
    """The report consumers ask for ONE transition's statistics, not the hand's
    whole matrix — the repository filters are reachable from the endpoint."""
    _, source_id = await api.seed_style_and_source()
    await _seed_pairs(
        api,
        source_id,
        [
            *NE_ITEMS,
            _pair_item([0.3, 0.0], right_key="a", slot=3),
            _pair_item([0.2, 0.0], left_key="e", right_key="n", slot=4),
        ],
    )
    res = await api.client.request("POST", "/hands/test-hand/pair-aggregates/rebuild", headers=api.admin_headers())
    assert res.json()["stored"] == 3

    res = await api.client.request(
        "GET",
        "/hands/test-hand/pair-aggregates",
        params={"left_key": "n", "right_key": "e"},
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body
    assert [(r["left_key"], r["right_key"]) for r in res.json()] == [("n", "e")]

    # One key alone narrows to every join of that letter.
    res = await api.client.request(
        "GET", "/hands/test-hand/pair-aggregates", params={"left_key": "n"}, headers=api.admin_headers()
    )
    assert [(r["left_key"], r["right_key"]) for r in res.json()] == [("n", "a"), ("n", "e")]


async def test_rebuild_min_n_gate_skips_and_reports(api: Harness):
    _, source_id = await api.seed_style_and_source()
    await _seed_pairs(api, source_id, [*NE_ITEMS, _pair_item([0.3, 0.0], left_key="e", right_key="n", slot=3)])

    res = await api.client.request(
        "POST", "/hands/test-hand/pair-aggregates/rebuild", params={"min_n": 2}, headers=api.admin_headers()
    )
    out = res.json()
    assert out["stored"] == 1
    assert out["skipped"] == {"fit_bad": 0, "geometry": 0, "below_min_n": 1}
    assert [(p["left_key"], p["right_key"]) for p in out["pairs"]] == [("n", "e")]

    # The default gate of 1 keeps the singleton — pairs are sparse.
    res = await api.client.request("POST", "/hands/test-hand/pair-aggregates/rebuild", headers=api.admin_headers())
    out = res.json()
    assert out["stored"] == 2 and out["deleted"] == 1
    assert [(p["left_key"], p["right_key"]) for p in out["pairs"]] == [("e", "n"), ("n", "e")]


async def test_rebuild_excludes_occurrences_the_harvest_qc_failed(api: Harness):
    _, source_id = await api.seed_style_and_source()
    await _seed_pairs(
        api, source_id, [*NE_ITEMS, _pair_item([9.0, 9.0], slot=4, measurements={"fit_ok": False, "gen_chamfer": 9.0})]
    )

    res = await api.client.request("POST", "/hands/test-hand/pair-aggregates/rebuild", headers=api.admin_headers())
    out = res.json()
    assert out["skipped"] == {"fit_bad": 1, "geometry": 0, "below_min_n": 0}
    assert out["pairs"] == [{"left_key": "n", "right_key": "e", "n_instances": 3, "gen_chamfer_mean": 0.3}]
    res = await api.client.request("GET", "/hands/test-hand/pair-aggregates", headers=api.admin_headers())
    # The rejected occurrence would have dragged the median far off.
    assert res.json()[0]["offset_center"] == [0.5, 0.0]


async def test_rebuild_replaces_stale_pairs(api: Harness):
    _, source_id = await api.seed_style_and_source()
    await _seed_pairs(api, source_id, [*NE_ITEMS, _pair_item([0.3, 0.0], left_key="e", right_key="n", slot=3)])
    res = await api.client.request("POST", "/hands/test-hand/pair-aggregates/rebuild", headers=api.admin_headers())
    assert res.json()["stored"] == 2

    # A stricter gate no longer produces e→n — the stale row must go, not
    # linger with its old median.
    res = await api.client.request(
        "POST", "/hands/test-hand/pair-aggregates/rebuild", params={"min_n": 3}, headers=api.admin_headers()
    )
    assert res.json() == {
        "hand_id": "test-hand",
        "stored": 1,
        "deleted": 2,
        "skipped": {"fit_bad": 0, "geometry": 0, "below_min_n": 1},
        "pairs": [{"left_key": "n", "right_key": "e", "n_instances": 3, "gen_chamfer_mean": 0.3}],
    }
    res = await api.client.request("GET", "/hands/test-hand/pair-aggregates", headers=api.admin_headers())
    assert [(r["left_key"], r["right_key"]) for r in res.json()] == [("n", "e")]


async def test_aggregates_are_scoped_to_one_hand(api: Harness):
    """Statistics are a property of the writer — a second hand's occurrences on
    the same plate never enter this hand's medians (quellen-und-rechte.md §7)."""
    _, source_id = await api.seed_style_and_source()
    await _seed_pairs(api, source_id, NE_ITEMS)
    await _seed_pairs(
        api,
        source_id,
        [
            _pair_item([2.0, 0.0], specimen_id="fremd", slot=9),
            _pair_item([2.0, 0.0], left_key="e", right_key="n", slot=8),
        ],
        hand_id="other-hand",
    )

    res = await api.client.request("POST", "/hands/test-hand/pair-aggregates/rebuild", headers=api.admin_headers())
    assert res.json()["pairs"] == [{"left_key": "n", "right_key": "e", "n_instances": 3, "gen_chamfer_mean": 0.3}]
    res = await api.client.request("GET", "/hands/test-hand/pair-aggregates", headers=api.admin_headers())
    assert res.json()[0]["offset_center"] == [0.5, 0.0]

    # The other writer aggregates separately, and rebuilding it leaves the
    # first hand's rows alone (the wholesale replace is per hand).
    res = await api.client.request("POST", "/hands/other-hand/pair-aggregates/rebuild", headers=api.admin_headers())
    assert res.json()["stored"] == 2
    res = await api.client.request("GET", "/hands/other-hand/pair-aggregates", headers=api.admin_headers())
    assert [r["offset_center"] for r in res.json()] == [[2.0, 0.0], [2.0, 0.0]]
    res = await api.client.request("GET", "/hands/test-hand/pair-aggregates", headers=api.admin_headers())
    assert len(res.json()) == 1


async def test_pair_aggregate_endpoints_are_admin_gated_and_404_unknown_hand(api: Harness):
    _, source_id = await api.seed_style_and_source()
    await _seed_pairs(api, source_id, NE_ITEMS)

    # Learned geometry is never public (quellen-und-rechte.md §5).
    res = await api.client.request("GET", "/hands/test-hand/pair-aggregates")
    assert res.status == 401
    res = await api.client.request("POST", "/hands/test-hand/pair-aggregates/rebuild")
    assert res.status == 401

    res = await api.client.request("GET", "/hands/nope/pair-aggregates", headers=api.admin_headers())
    assert res.status == 404
    res = await api.client.request("POST", "/hands/nope/pair-aggregates/rebuild", headers=api.admin_headers())
    assert res.status == 404
