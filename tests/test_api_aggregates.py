"""The per-hand aggregate endpoints (Stufenplan H1): read + rebuild + apply.

Same in-memory aiosqlite stack as the other HTTP suites (`tests/api_harness.py`
via the `api` fixture). Occurrences are written through the real
`PUT /sources/{id}/instances` batch so the hand row is created the way
production does it. Proves the median/hull round-trip, the min_n gate, the
replace semantics, the Laufform Prüfstein, the aggregate-derived Laufform rows
and the admin gate.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from core.database import LAUFFORM_VARIANT, Hand, Template
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
    """The gate stays parameterised and keeps counting — only the DEFAULT moved
    (issue #273)."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06])

    res = await api.client.request(
        "POST", "/hands/test-hand/aggregates/rebuild", params={"min_n": 4}, headers=api.admin_headers()
    )
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


async def test_rebuild_defaults_to_min_n_one(api: Harness):
    """A key seen ONCE gets an aggregate by default (issue #273): seeing a
    median renders nothing, so the statistics layer shows every attested key —
    nearly every capital lives at n = 1..3 on the 1922 plates. The caution moved
    to `apply-laufform`, which is a separate, selectable step."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.02])

    res = await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())
    out = res.json()
    assert out["stored"] == 1
    assert out["skipped"] == {"anchor_shape": 0, "below_min_n": 0}
    assert out["keys"] == [{"glyph_key": "n", "variant": 0, "n_instances": 1, "laufform_dev_xh": None}]

    res = await api.client.request("GET", "/hands/test-hand/aggregates", headers=api.admin_headers())
    row = res.json()[0]
    # The single occurrence IS the median — and its MAD is a computed zero, not
    # a measured spread. Stored as the aggregation produces it; the consumers
    # (LensStats) drop the ± clause on an n = 1 row.
    assert row["n_instances"] == 1
    assert row["cluster_center"] == _shifted(0.02)
    assert row["hull"]["anchor_mad"] == [[0.0, 0.0]] * len(CHART_ANCHORS)


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


async def test_list_reports_the_rendered_laufform_and_its_distance(api: Harness):
    """The freshness read (issue #270): a plain GET must answer "is what the
    engine writes still what the statistics say?" — previously only a rebuild
    or an apply computed that, i.e. only DOING something told you."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())

    # No running form stored yet: nothing to compare against, and the row says
    # so with nulls rather than a fabricated zero distance.
    res = await api.client.request("GET", "/hands/test-hand/aggregates", headers=api.admin_headers())
    row = res.json()[0]
    assert row["laufform_anchors"] is None
    assert row["laufform_dev_xh"] is None

    # A running form that matches the median reads as distance 0 — and carries
    # its anchors, so the UI can draw the two on top of each other.
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/templates/n/laufform",
        json_body={"anchors": _shifted(0.04), "n_occurrences": 4},
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body
    res = await api.client.request("GET", "/hands/test-hand/aggregates", headers=api.admin_headers())
    row = res.json()[0]
    assert row["laufform_anchors"] == _shifted(0.04)
    assert row["laufform_dev_xh"] == 0.0

    # A drifted running form reads as the distance the apply step would close.
    drifted = _shifted(0.04)
    drifted[2] = [drifted[2][0] + 0.6, drifted[2][1]]
    await api.client.request(
        "PUT",
        f"/sources/{source_id}/templates/n/laufform",
        json_body={"anchors": drifted, "n_occurrences": 4},
        headers=api.admin_headers(),
    )
    res = await api.client.request("GET", "/hands/test-hand/aggregates", headers=api.admin_headers())
    assert res.json()[0]["laufform_dev_xh"] == 0.1


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


async def _stored_laufform(api: Harness, style_id: str) -> list[dict]:
    """The style's stored running-form rows as plain dicts (read inside the
    session, so nothing is touched on a closed one)."""
    async with api.session_maker() as session:
        rows = (
            (
                await session.execute(
                    select(Template).where(Template.style_id == style_id, Template.variant == LAUFFORM_VARIANT)
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "glyph_key": r.glyph_key,
                "glyph": r.glyph,
                "anchors": [list(a) for a in r.anchors],
                "half_widths": list(r.half_widths),
                "raw_path": list(r.raw_path),
                "advance": r.advance,
                "exit_pt": dict(r.exit_pt),
                "trace_meta": dict(r.trace_meta),
                "provenance_source_id": r.provenance_source_id,
            }
            for r in rows
        ]


async def test_apply_laufform_derives_the_variant_100_row_and_closes_the_pruefstein(api: Harness):
    """H1's last step: the running form becomes a DERIVATION from the stored
    aggregate — and the rebuild's Prüfstein then reads 0."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())

    res = await api.client.request("POST", "/hands/test-hand/aggregates/apply-laufform", headers=api.admin_headers())
    assert res.status == 200, res.body
    assert res.json() == {
        "hand_id": "test-hand",
        "style_id": style_id,
        # No Laufform row existed yet, so there is no distance to report.
        "applied": [{"glyph_key": "n", "variant": 0, "n_instances": 4, "laufform_dev_xh": None, "created": True}],
        "skipped": [],
        # No `glyph_keys` selection was sent, so nothing was left out by one.
        "excluded": [],
    }

    rows = await _stored_laufform(api, style_id)
    assert len(rows) == 1
    row = rows[0]
    assert row["glyph"] == "n"
    assert row["anchors"] == _shifted(0.04)
    # Everything but the anchors comes from the chart row (the ductus prior):
    # widths and topology carry over, entry/exit/advance ride the end anchors.
    assert row["half_widths"] == [0.05] * 6
    assert row["raw_path"] == []
    assert row["advance"] == pytest.approx(0.49, abs=1e-9)
    assert row["exit_pt"]["xy"] == pytest.approx([0.39, 0.0], abs=1e-9)
    assert row["trace_meta"]["laufform"] == {
        "derived_from": "hand-aggregate",
        "hand_id": "test-hand",
        "n_occurrences": 4,
    }
    assert row["provenance_source_id"] == source_id

    # The Prüfstein closes: median recomputed from the occurrences == the
    # stored running form.
    res = await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())
    assert res.json()["keys"] == [{"glyph_key": "n", "variant": 0, "n_instances": 4, "laufform_dev_xh": 0.0}]


async def test_apply_laufform_reports_the_pre_write_distance_and_is_idempotent(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())

    # A hand-written running form that drifted from the occurrences: one anchor
    # moved by 0.6 over six anchors → mean 0.1.
    drifted = _shifted(0.04)
    drifted[2] = [drifted[2][0] + 0.6, drifted[2][1]]
    res = await api.client.request(
        "PUT",
        f"/sources/{source_id}/templates/n/laufform",
        json_body={"anchors": drifted, "n_occurrences": 4},
        headers=api.admin_headers(),
    )
    assert res.status == 200, res.body

    res = await api.client.request("POST", "/hands/test-hand/aggregates/apply-laufform", headers=api.admin_headers())
    # The distance is measured BEFORE the write — it is what the apply closed.
    assert res.json()["applied"] == [
        {"glyph_key": "n", "variant": 0, "n_instances": 4, "laufform_dev_xh": 0.1, "created": False}
    ]
    rows = await _stored_laufform(api, style_id)
    assert len(rows) == 1 and rows[0]["anchors"] == _shifted(0.04)

    # Second run: an update, not a duplicate row — the unique
    # (style_id, glyph_key, variant) holds and the distance is now 0.
    res = await api.client.request("POST", "/hands/test-hand/aggregates/apply-laufform", headers=api.admin_headers())
    assert res.json()["applied"] == [
        {"glyph_key": "n", "variant": 0, "n_instances": 4, "laufform_dev_xh": 0.0, "created": False}
    ]
    rows = await _stored_laufform(api, style_id)
    assert len(rows) == 1 and rows[0]["anchors"] == _shifted(0.04)


async def test_apply_laufform_skips_and_reports_underivable_keys(api: Harness):
    """A key without a chart template, one whose anchor count disagrees with
    it, and every non-base variant are reported instead of guessed at."""
    style_id, source_id = await api.seed_style_and_source()
    # 'n' has a chart row (six anchors), 'm' has none; 'e' has one but its
    # occurrences carry four anchors.
    await api.seed_template(style_id, source_id, "n", "n")
    await api.seed_template(style_id, source_id, "e", "e")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08], glyph_key="m", glyph="m")
    short = [[0.0, 0.0], [0.1, 0.5], [0.2, 0.5], [0.3, 0.0]]
    items = [
        _instance_item(glyph_key="e", glyph="e", anchors=short, x0=300 + 10 * n, x1=330 + 10 * n) for n in range(4)
    ]
    # The reserved Laufform variant must never feed its own row; other authored
    # variants have no Laufform row to write into either.
    items += [_instance_item(variant=v, x0=400 + 10 * n, x1=430 + 10 * n) for v in (1, 100) for n in range(4)]
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/instances", json_body=_batch(items), headers=api.admin_headers()
    )
    assert res.status == 200, res.body
    await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())

    res = await api.client.request("POST", "/hands/test-hand/aggregates/apply-laufform", headers=api.admin_headers())
    out = res.json()
    assert [k["glyph_key"] for k in out["applied"]] == ["n"]
    # `n_instances` stays null for every reason no count took part in.
    assert out["skipped"] == [
        {"glyph_key": "e", "variant": 0, "reason": "anchor_count", "n_instances": None},
        {"glyph_key": "m", "variant": 0, "reason": "no_base_template", "n_instances": None},
        {"glyph_key": "n", "variant": 1, "reason": "non_base_variant", "n_instances": None},
        {"glyph_key": "n", "variant": 100, "reason": "laufform_variant", "n_instances": None},
    ]
    assert [r["glyph_key"] for r in await _stored_laufform(api, style_id)] == ["n"]


async def test_apply_laufform_writes_only_the_selected_keys(api: Harness):
    """Per-glyph selection (issue #273): with `min_n = 1` in the statistics
    layer, "all or nothing" would push a hand's one-occurrence idiosyncrasies
    into the writing path together with its well-attested medians. `glyph_keys`
    narrows the write, and the response names what it left out."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await api.seed_template(style_id, source_id, "m", "m")
    # 'n' well attested, 'm' seen exactly once — the case the selection exists
    # for, and one the default gate now aggregates.
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    await _seed_occurrences(api, source_id, [0.5], glyph_key="m", glyph="m")
    await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())

    res = await api.client.request(
        "POST", "/hands/test-hand/aggregates/apply-laufform", params={"glyph_keys": ["n"]}, headers=api.admin_headers()
    )
    assert res.status == 200, res.body
    out = res.json()
    assert [k["glyph_key"] for k in out["applied"]] == ["n"]
    # Deselected is its own report — never mixed into the "could not" skips.
    assert out["excluded"] == ["m"]
    assert out["skipped"] == []
    assert [r["glyph_key"] for r in await _stored_laufform(api, style_id)] == ["n"]

    # The thin key stays applicable — but naming it is no longer enough: the
    # floor is the endpoint's own judgement, so the request has to lower it.
    res = await api.client.request(
        "POST",
        "/hands/test-hand/aggregates/apply-laufform",
        params={"glyph_keys": ["m"], "min_occurrences": 1},
        headers=api.admin_headers(),
    )
    out = res.json()
    assert [k["glyph_key"] for k in out["applied"]] == ["m"]
    assert out["applied"][0]["n_instances"] == 1
    assert out["excluded"] == ["n"]
    assert sorted(r["glyph_key"] for r in await _stored_laufform(api, style_id)) == ["m", "n"]


async def test_apply_laufform_refuses_a_median_too_thin_to_outvote_an_outlier(api: Harness):
    """The floor the dialog's proposed selection alone could not hold.

    A re-apply names the keys that ALREADY have a Laufform row, so a key that
    once earned one from a word harvest kept being re-derived from however thin
    an aggregate it had since acquired — which is how the Sütterlin capital S
    came to be written from two occurrences. Naming a key is a request; the
    floor is the endpoint's judgement, and it holds against a bare call that
    names nothing at all."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await api.seed_template(style_id, source_id, "m", "m")
    # 'n' is well attested; 'm' has the two occurrences whose "median" is their
    # mean — one bad anchor would land in the writing path at half amplitude.
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    await _seed_occurrences(api, source_id, [0.0, 0.5], glyph_key="m", glyph="m")
    await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())

    # No selection at all — the shape of the scripted round that wrote the S.
    res = await api.client.request("POST", "/hands/test-hand/aggregates/apply-laufform", headers=api.admin_headers())
    assert res.status == 200, res.body
    out = res.json()
    assert [k["glyph_key"] for k in out["applied"]] == ["n"]
    # The count IS the reason, so the report carries it.
    assert out["skipped"] == [{"glyph_key": "m", "variant": 0, "reason": "below_min_occurrences", "n_instances": 2}]
    assert out["excluded"] == []
    assert [r["glyph_key"] for r in await _stored_laufform(api, style_id)] == ["n"]

    # Naming the thin key does not lift the floor either — it is not the
    # request's call.
    res = await api.client.request(
        "POST", "/hands/test-hand/aggregates/apply-laufform", params={"glyph_keys": ["m"]}, headers=api.admin_headers()
    )
    out = res.json()
    assert out["applied"] == []
    assert [s["reason"] for s in out["skipped"]] == ["below_min_occurrences"]
    assert [r["glyph_key"] for r in await _stored_laufform(api, style_id)] == ["n"]

    # Lowering it explicitly does, and then the request itself says so.
    res = await api.client.request(
        "POST", "/hands/test-hand/aggregates/apply-laufform", params={"min_occurrences": 2}, headers=api.admin_headers()
    )
    out = res.json()
    assert sorted(k["glyph_key"] for k in out["applied"]) == ["m", "n"]
    assert out["skipped"] == []
    assert sorted(r["glyph_key"] for r in await _stored_laufform(api, style_id)) == ["m", "n"]


async def test_apply_laufform_floor_never_relabels_an_underivable_key(api: Harness):
    """A thin aggregate that could not feed the Laufform ANYWAY keeps the more
    specific reason.

    The floor is the LAST question in the triage — after the variant AND the
    topology ones — because every other reason blocks the derivation whatever
    the count is, and the report exists to say what to do next: "author the
    chart row" and "the anchor counts disagree" are actionable, "harvest more
    occurrences" only becomes true once those are answered."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await api.seed_template(style_id, source_id, "e", "e")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    # Every underivable case ALSO thin, so each one's reason is a real choice:
    # two non-base variants, a key with no chart row ('m'), and one whose
    # occurrences carry a deviating anchor count ('e').
    items = [_instance_item(variant=v, x0=400 + 10 * v, x1=430 + 10 * v) for v in (1, LAUFFORM_VARIANT)]
    items += [_instance_item(glyph_key="m", glyph="m", x0=500, x1=530)]
    short = [[0.0, 0.0], [0.1, 0.5], [0.2, 0.5], [0.3, 0.0]]
    items += [_instance_item(glyph_key="e", glyph="e", anchors=short, x0=600, x1=630)]
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/instances", json_body=_batch(items), headers=api.admin_headers()
    )
    assert res.status == 200, res.body
    await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())

    res = await api.client.request("POST", "/hands/test-hand/aggregates/apply-laufform", headers=api.admin_headers())
    out = res.json()
    assert [k["glyph_key"] for k in out["applied"]] == ["n"]
    assert out["skipped"] == [
        {"glyph_key": "e", "variant": 0, "reason": "anchor_count", "n_instances": None},
        {"glyph_key": "m", "variant": 0, "reason": "no_base_template", "n_instances": None},
        {"glyph_key": "n", "variant": 1, "reason": "non_base_variant", "n_instances": None},
        {"glyph_key": "n", "variant": 100, "reason": "laufform_variant", "n_instances": None},
    ]


async def test_apply_laufform_selection_of_nothing_writes_nothing(api: Harness):
    """An EMPTY selection is a deliberate "write nothing", not a missing one —
    the absent parameter is what means "every key"."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())

    res = await api.client.request(
        "POST",
        "/hands/test-hand/aggregates/apply-laufform",
        # What `applyLaufform(handId, [])` sends: a present but empty selection.
        params={"glyph_keys": [""]},
        headers=api.admin_headers(),
    )
    out = res.json()
    assert out["applied"] == [] and out["skipped"] == [] and out["excluded"] == ["n"]
    assert await _stored_laufform(api, style_id) == []

    # A key the selection names but the hand has no aggregate for writes
    # nothing either — and excludes the keys it does have.
    res = await api.client.request(
        "POST",
        "/hands/test-hand/aggregates/apply-laufform",
        params={"glyph_keys": ["nope"]},
        headers=api.admin_headers(),
    )
    out = res.json()
    assert out["applied"] == [] and out["excluded"] == ["n"]
    assert await _stored_laufform(api, style_id) == []


async def test_apply_laufform_selection_precedes_the_variant_triage(api: Harness):
    """A deselected row is not reported as a skip: it never reached the
    variant/topology triage, so the two lists stay honest about their causes."""
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])
    # A second, non-base variant of the SAME key — selected, so the triage does
    # see it and reports it as before.
    items = [_instance_item(variant=1, x0=400 + 10 * n, x1=430 + 10 * n) for n in range(4)]
    items += [
        _instance_item(glyph_key="m", glyph="m", anchors=_shifted(0.3), x0=500 + 10 * n, x1=530 + 10 * n)
        for n in range(4)
    ]
    res = await api.client.request(
        "PUT", f"/sources/{source_id}/instances", json_body=_batch(items), headers=api.admin_headers()
    )
    assert res.status == 200, res.body
    await api.client.request("POST", "/hands/test-hand/aggregates/rebuild", headers=api.admin_headers())

    res = await api.client.request(
        "POST", "/hands/test-hand/aggregates/apply-laufform", params={"glyph_keys": ["n"]}, headers=api.admin_headers()
    )
    out = res.json()
    assert [k["glyph_key"] for k in out["applied"]] == ["n"]
    # 'n' variant 1 was selected and is reported as underivable; 'm' was not
    # selected at all and is only excluded.
    assert out["skipped"] == [{"glyph_key": "n", "variant": 1, "reason": "non_base_variant", "n_instances": None}]
    assert out["excluded"] == ["m"]


async def test_apply_laufform_without_aggregates_or_style_writes_nothing(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])

    # Aggregates never rebuilt: an empty summary, and no row is invented from
    # the occurrences (the rebuild is the one recompute step).
    res = await api.client.request("POST", "/hands/test-hand/aggregates/apply-laufform", headers=api.admin_headers())
    assert res.status == 200
    assert res.json() == {"hand_id": "test-hand", "style_id": style_id, "applied": [], "skipped": [], "excluded": []}
    assert await _stored_laufform(api, style_id) == []

    # A hand without a style has no templates to write into.
    async with api.session_maker() as session:
        session.add(Hand(id="styleless-hand", label="No style"))
        await session.commit()
    res = await api.client.request(
        "POST", "/hands/styleless-hand/aggregates/apply-laufform", headers=api.admin_headers()
    )
    assert res.status == 409


async def test_aggregate_endpoints_are_admin_gated_and_404_unknown_hand(api: Harness):
    style_id, source_id = await api.seed_style_and_source()
    await api.seed_template(style_id, source_id, "n", "n")
    await _seed_occurrences(api, source_id, [0.0, 0.02, 0.06, 0.08])

    # Learned geometry is never public (quellen-und-rechte.md §5).
    res = await api.client.request("GET", "/hands/test-hand/aggregates")
    assert res.status == 401
    res = await api.client.request("POST", "/hands/test-hand/aggregates/rebuild")
    assert res.status == 401
    # The apply WRITES templates — the gate matters twice over here.
    res = await api.client.request("POST", "/hands/test-hand/aggregates/apply-laufform")
    assert res.status == 401

    res = await api.client.request("GET", "/hands/nope/aggregates", headers=api.admin_headers())
    assert res.status == 404
    res = await api.client.request("POST", "/hands/nope/aggregates/rebuild", headers=api.admin_headers())
    assert res.status == 404
    res = await api.client.request("POST", "/hands/nope/aggregates/apply-laufform", headers=api.admin_headers())
    assert res.status == 404
