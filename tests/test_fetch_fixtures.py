"""Pure-unit cover for the API-backed word-bench fixture fetcher.

`tools/wordbench/fetch_fixtures.py` rebuilds the frozen fixture roots over the
deployed API instead of Cloud SQL. Its risky parts are the payload → fixture-row
mappers (a wrong shape breaks every consumer silently) and the wiring (a root
written where nobody reads makes the lab suites skip forever, the doctrine of
`tests/test_lab_fixture_wiring.py`). Both are checked here on hand-written
dicts — no network, no DB, no fixtures.
"""

from __future__ import annotations

import inspect
import json

import pytest

from core.database.models import LAUFFORM_VARIANT
from tools.wordbench import export_fixtures, fetch_fixtures
from tools.wordbench.fetch_fixtures import (
    DEFAULT_PLACEMENT_TOL,
    EXACT_PLACEMENT_TOL,
    NIB_EXACT,
    NIB_NONE,
    NIB_READBACK,
    ApiClient,
    _placement_tol_for,
    composition_mismatch,
    exact_nib_units,
    hand_id_for,
    laufform_row_from_payload,
    laufform_rows_from_aggregates,
    payload_mismatch,
    pooled_nib_units,
    production_row,
    resolve_nib,
    stored_laufform_rows,
    template_row_from_payload,
)


CHART_PAYLOAD = {
    "glyph_key": "a",
    "glyph": "a",
    "variant": 0,
    "advance": 1.5,
    "entry": {"xy": [0.0, 0.5], "tangent_deg": 38.3, "coupling": "baseline"},
    "exit_pt": {"xy": [1.5, 0.4], "tangent_deg": 45.0, "coupling": "baseline"},
    "anchors": [[0.0, 0.5], [0.7, 1.0], [1.5, 0.4]],
    "half_widths": [0.07, 0.08, 0.07],
    "raw_path": [{"x": 1.0, "y": 2.0}],
    "trace_meta": {"n_anchors": 3, "stroke_starts": [0]},
    "measurements": {"quality": 0.9},
}


CHART_ROW_KEYS = {
    "glyph_key",
    "glyph",
    "advance",
    "entry",
    "exit_pt",
    "anchors",
    "half_widths",
    "trace_meta",
    "updated_at",
}


def test_template_row_from_api_payload():
    row = template_row_from_payload(CHART_PAYLOAD)

    # Exactly the exporter's fixture-row shape — no raw_path, no measurements,
    # no variant: those never reach a WordCase.
    assert set(row) == CHART_ROW_KEYS
    assert row["anchors"] == CHART_PAYLOAD["anchors"]
    assert row["half_widths"] == CHART_PAYLOAD["half_widths"]
    assert row["entry"] == CHART_PAYLOAD["entry"]
    assert row["exit_pt"] == CHART_PAYLOAD["exit_pt"]
    assert row["advance"] == 1.5
    assert row["trace_meta"]["stroke_starts"] == [0]
    assert row["updated_at"] is None


def test_template_row_tolerates_null_coupling_fields():
    payload = {**CHART_PAYLOAD, "entry": None, "exit_pt": None, "trace_meta": None}
    row = template_row_from_payload(payload)
    assert row["entry"] == {} and row["exit_pt"] == {} and row["trace_meta"] == {}


def test_laufform_row_from_api_payload():
    chart = template_row_from_payload(CHART_PAYLOAD)
    # Median running form: first anchor 0.1 right / 0.05 up, last 0.2 right.
    anchors = [[0.1, 0.55], [0.7, 1.0], [1.7, 0.4]]

    row = laufform_row_from_payload(chart, anchors)

    # Same fixture shape as a chart row — the consumers read both through the
    # identical WordCase path.
    assert set(row) == CHART_ROW_KEYS
    assert row["glyph_key"] == "a"
    assert row["anchors"] == anchors
    # Everything but the anchors comes from the chart row …
    assert row["half_widths"] == CHART_PAYLOAD["half_widths"]
    assert row["trace_meta"]["stroke_starts"] == [0]
    # … and entry/exit/advance ride their end anchors' delta.
    assert row["entry"]["xy"] == pytest.approx([0.1, 0.55])
    assert row["entry"]["tangent_deg"] == 38.3
    assert row["exit_pt"]["xy"] == pytest.approx([1.7, 0.4])
    assert row["advance"] == pytest.approx(1.7)
    # The derivation is stamped where the write path stamps it.
    assert row["trace_meta"]["laufform"] == fetch_fixtures.LAUFFORM_META


def test_laufform_rows_skip_what_cannot_be_derived():
    chart = {"a": template_row_from_payload(CHART_PAYLOAD)}
    aggregates = [
        {"glyph_key": "a", "variant": 0, "laufform_anchors": [[0.1, 0.5], [0.7, 1.0], [1.5, 0.4]]},
        {"glyph_key": "a", "variant": 1, "laufform_anchors": [[0.1, 0.5], [0.7, 1.0], [1.5, 0.4]]},
        {"glyph_key": "e", "variant": 0, "laufform_anchors": [[0.0, 0.0]]},  # no chart row
        {"glyph_key": "a", "variant": 0, "laufform_anchors": None},  # no running form yet
    ]

    rows = laufform_rows_from_aggregates(aggregates, chart)

    assert set(rows) == {"a"}
    assert rows["a"]["anchors"][0] == [0.1, 0.5]


def test_laufform_rows_skip_a_deviating_anchor_count(capsys):
    chart = {"a": template_row_from_payload(CHART_PAYLOAD)}
    rows = laufform_rows_from_aggregates([{"glyph_key": "a", "variant": 0, "laufform_anchors": [[0.0, 0.0]]}], chart)
    assert rows == {}
    assert "skip laufform a" in capsys.readouterr().out


# The stored variant-100 row as the API serves it — anchors and trace_meta of
# the APPLY step, not of today's chart row (the #311 distinction).
LAUFFORM_PAYLOAD = {
    **CHART_PAYLOAD,
    "variant": LAUFFORM_VARIANT,
    "anchors": [[0.1, 0.5], [0.8, 1.0], [1.6, 0.4]],
    "trace_meta": {"n_anchors": 3, "stroke_starts": [0], "laufform": {"derived_from": "hand-aggregate"}},
}


def test_stored_laufform_rows_read_the_variant_rows_verbatim():
    summaries = [
        {"glyph_key": "a", "variant": 0},
        {"glyph_key": "a", "variant": LAUFFORM_VARIANT},
        {"glyph_key": "e", "variant": 0},  # no Laufform row — nothing to fetch
        {"glyph_key": "x", "variant": LAUFFORM_VARIANT},  # not needed by any case
    ]
    client = _StubClient(routes={"/sources/s/templates/a": LAUFFORM_PAYLOAD})

    rows = stored_laufform_rows(client, "s", summaries, {"a", "e"})

    assert set(rows) == {"a"}
    # Verbatim: the stored anchors AND the apply step's own trace_meta — never
    # a rebuild from today's chart row.
    assert rows["a"]["anchors"] == LAUFFORM_PAYLOAD["anchors"]
    assert rows["a"]["trace_meta"]["laufform"] == {"derived_from": "hand-aggregate"}
    assert set(rows["a"]) == CHART_ROW_KEYS
    assert client.calls == [("/sources/s/templates/a", {"variant": LAUFFORM_VARIANT})]


def test_stored_laufform_rows_detect_a_deployment_without_the_variant_read():
    # An older FastAPI ignores the unknown query parameter and serves the
    # chart row; freezing THAT as a Laufform would corrupt every bench number
    # downstream — the fetcher must fall back to the reconstruction instead.
    summaries = [{"glyph_key": "a", "variant": LAUFFORM_VARIANT}]
    client = _StubClient(routes={"/sources/s/templates/a": CHART_PAYLOAD})
    assert stored_laufform_rows(client, "s", summaries, {"a"}) is None


def test_stored_laufform_rows_empty_when_no_variant_rows_exist():
    # No variant-100 summary → an empty layer IS the stored truth (and never
    # mistaken for an old deployment): no request is even issued.
    client = _StubClient(routes={})
    assert stored_laufform_rows(client, "s", [{"glyph_key": "a", "variant": 0}], {"a"}) == {}
    assert client.calls == []


def test_hand_is_derived_from_the_occurrences():
    rows = [{"hand_id": "h1"}, {"hand_id": "h1"}, {"hand_id": "h2"}, {"hand_id": None}]
    assert hand_id_for({"hand_id": None}, rows) == "h1"
    # An explicit override wins, and a source without occurrences falls back.
    assert hand_id_for({"hand_id": None}, rows, "h9") == "h9"
    assert hand_id_for({"hand_id": "h3"}, []) == "h3"
    assert hand_id_for({}, []) is None


def test_composition_mismatch_accepts_an_exact_match():
    local = [{"glyph_key": "a", "centerline": [[0.0, 0.0], [1.0, 1.0]]}, {"centerline": [[2.0, 0.0], [3.0, 0.0]]}]
    error, shape, placement = composition_mismatch(local, [dict(i) for i in local])
    assert error is None and shape == 0.0 and placement == 0.0


def test_composition_mismatch_separates_placement_from_shape():
    local = [{"glyph_key": "a", "centerline": [[0.0, 0.0], [1.0, 1.0]]}]
    # A pure translation of the whole glyph is PLACEMENT — tolerated up to the
    # documented bound, and never counted as a shape deviation.
    shifted = [{"glyph_key": "a", "centerline": [[0.01, 0.0], [1.01, 1.0]]}]
    error, shape, placement = composition_mismatch(local, shifted)
    assert error is None
    assert shape == pytest.approx(0.0)
    assert placement == pytest.approx(0.01)

    # The same magnitude as a DEFORMATION fails on the shape channel.
    deformed = [{"glyph_key": "a", "centerline": [[0.0, 0.0], [1.01, 1.0]]}]
    error, shape, _ = composition_mismatch(local, deformed)
    assert error is not None and "shape" in error
    assert shape > 0.0

    # A too-large translation still fails, on the placement channel.
    far = [{"glyph_key": "a", "centerline": [[0.5, 0.0], [1.5, 1.0]]}]
    error, _, placement = composition_mismatch(local, far)
    assert error is not None and "placement" in error and placement == pytest.approx(0.5)


def test_composition_mismatch_only_charges_letters_for_shape():
    # A connector is GENERATED from the placement, so its own reshaping counts
    # as placement jitter rather than as a letter deforming.
    local = [{"centerline": [[0.0, 0.0], [1.0, 0.0]]}]
    served = [{"centerline": [[0.0, 0.0], [1.005, 0.0]]}]
    error, shape, placement = composition_mismatch(local, served)
    assert error is None and shape == 0.0 and placement == pytest.approx(0.005)


def test_composition_mismatch_names_a_structural_difference():
    local = [{"centerline": [[0.0, 0.0], [1.0, 1.0]]}, {"centerline": [[2.0, 0.0]]}]
    error, _, _ = composition_mismatch(local, local[:1])
    assert "1 served" in error

    error, _, _ = composition_mismatch(local, [{"centerline": [[0.0, 0.0]]}, {"centerline": [[2.0, 0.0]]}])
    assert "item 0" in error


def test_production_row_drops_the_field_the_write_path_drops():
    # `glyph` keys core.pipeline._fluent_widen; the write path never passes it.
    row = template_row_from_payload(CHART_PAYLOAD)
    stripped = production_row(row)
    assert "glyph" not in stripped
    assert set(stripped) == CHART_ROW_KEYS - {"glyph"}


def test_payload_mismatch_flags_each_render_field():
    payload = {
        "advance": 1.5,
        "entry": {"xy": [0.0, 0.5]},
        "exit_pt": {"xy": [1.5, 0.4]},
        "anchors_template": [[0.0, 0.5], [1.5, 0.4]],
        "centerlines_template": [[[0.0, 0.5], [1.5, 0.4]]],
    }
    assert payload_mismatch(payload, {**payload}) is None
    assert "advance" in payload_mismatch(payload, {**payload, "advance": 1.6})
    assert "entry" in payload_mismatch(payload, {**payload, "entry": {"xy": [0.1, 0.5]}})
    assert "anchors_template" in payload_mismatch(payload, {**payload, "anchors_template": [[0.0, 0.5], [1.4, 0.4]]})
    assert "strokes" in payload_mismatch(payload, {**payload, "centerlines_template": [[[0.0, 0.5]]]})


class _StubClient:
    """Records the GETs a helper issues and replays a canned payload.

    With `routes` the answer depends on the path, and an unlisted path returns
    None — exactly what `ApiClient.get(..., allow_404=True)` yields for an
    endpoint the deployed API does not have yet.
    """

    def __init__(self, payload=None, routes: dict[str, dict] | None = None):
        self.payload = payload
        self.routes = routes
        self.calls: list[tuple[str, dict | None]] = []

    def get(self, path, params=None, **_kwargs):
        self.calls.append((path, params))
        if self.routes is not None:
            return self.routes.get(path)
        return self.payload


def test_pooled_nib_is_read_back_only_for_a_constant_source():
    client = _StubClient({"glyphs": [{"half_widths_template": [0.0731, 0.0731]}], "missing": []})
    assert pooled_nib_units(client, "s", "constant", {"a", "e"}) == pytest.approx(0.0731)
    assert client.calls == [("/sources/s/write/glyphs", {"keys": "a"})]

    # A pressure source has no pooled nib to read back — the payload would
    # carry each glyph's own measured profile, which is NOT the nib.
    pressure = _StubClient({"glyphs": [{"half_widths_template": [0.2]}], "missing": []})
    assert pooled_nib_units(pressure, "s", "pressure", {"a"}) is None
    assert pressure.calls == []


RENDER_CONTEXT = "/sources/s/render-context"
WRITE_GLYPHS = "/sources/s/write/glyphs"
# The rounded readback and the exact value differ in the 5th decimal — the
# whole point of the extra read (see fetch_fixtures' module docstring).
EXACT_NIB = 0.07313333333333334
READBACK = {"glyphs": [{"half_widths_template": [0.0731, 0.0731]}], "missing": []}


def test_exact_nib_is_preferred_over_the_rounded_readback():
    client = _StubClient(routes={RENDER_CONTEXT: {"constant_nib_units": EXACT_NIB, "width_resolver": "constant"}})

    nib, precision = resolve_nib(client, "s", "constant", {"a", "e"})

    assert nib == EXACT_NIB
    assert precision == NIB_EXACT
    # No readback needed — one admin read answers it.
    assert [path for path, _ in client.calls] == [RENDER_CONTEXT]


def test_nib_falls_back_to_the_readback_on_an_api_without_the_endpoint():
    # The deployed API 404s the render-context read until this change ships;
    # the fetcher must keep producing a usable root meanwhile.
    client = _StubClient(routes={WRITE_GLYPHS: READBACK})

    nib, precision = resolve_nib(client, "s", "constant", {"a", "e"})

    assert nib == pytest.approx(0.0731)
    assert precision == NIB_READBACK
    assert [path for path, _ in client.calls] == [RENDER_CONTEXT, WRITE_GLYPHS]


def test_nib_falls_back_when_the_context_carries_no_nib():
    """A render context without the field (an older shape, or a source whose
    templates are all unauthored) is not an exact answer — read back instead."""
    client = _StubClient(routes={RENDER_CONTEXT: {"width_resolver": "constant"}, WRITE_GLYPHS: READBACK})

    nib, precision = resolve_nib(client, "s", "constant", {"a"})

    assert nib == pytest.approx(0.0731)
    assert precision == NIB_READBACK


def test_no_pooled_nib_for_a_pressure_source():
    client = _StubClient(routes={})
    assert resolve_nib(client, "s", "pressure", {"a"}) == (None, NIB_NONE)
    # Neither read is even issued: a pressure source has no pooled nib.
    assert client.calls == []


def test_exact_nib_read_tolerates_a_missing_endpoint():
    assert exact_nib_units(_StubClient(routes={}), "s") is None


def test_placement_tolerance_follows_the_frozen_nib_precision(tmp_path):
    """The payoff of the exact nib: a root frozen with it must reproduce
    bit-for-bit, while an older root keeps its documented jitter allowance."""
    root = tmp_path / "root"
    root.mkdir()
    manifest = root / "manifest.json"

    manifest.write_text(json.dumps({"nib_precision": NIB_EXACT}))
    assert _placement_tol_for(root) == EXACT_PLACEMENT_TOL

    manifest.write_text(json.dumps({"nib_precision": NIB_READBACK}))
    assert _placement_tol_for(root) == DEFAULT_PLACEMENT_TOL

    # A DB-exported root carries no such stamp — conservative bound, no crash.
    manifest.write_text(json.dumps({"style_id": "suetterlin"}))
    assert _placement_tol_for(root) == DEFAULT_PLACEMENT_TOL
    manifest.unlink()
    assert _placement_tol_for(root) == DEFAULT_PLACEMENT_TOL


def test_admin_read_without_a_token_fails_without_naming_a_secret():
    client = ApiClient("https://api.example.test", token=None)
    with pytest.raises(SystemExit) as excinfo:
        client.get("/sources/x/templates/a", admin=True)
    assert "ADMIN_TOKEN" in str(excinfo.value)


def test_client_refuses_a_non_https_base():
    with pytest.raises(SystemExit) as excinfo:
        ApiClient("http://api.example.test", token="t")
    assert "https" in str(excinfo.value)


def test_client_never_follows_a_redirect():
    from tools.wordbench.fetch_fixtures import _NoRedirectHandler

    handler = _NoRedirectHandler()
    assert handler.redirect_request(None, None, 302, "Found", {}, "https://elsewhere.test") is None


def test_fetcher_writes_where_the_consumers_read():
    # Same doctrine as tests/test_lab_fixture_wiring.py: the API-backed sibling
    # must fill the very roots the DB exporter fills, or wordlab/pairlab and
    # the bench keep skipping on absent fixtures.
    assert fetch_fixtures.DEFAULT_OUT_DIR.resolve() == export_fixtures.DEFAULT_OUT_DIR.resolve()
    source = inspect.getsource(fetch_fixtures)
    assert "manifest.json" in source
    assert "pair_instances.json" in source


def test_fetcher_issues_no_write_verbs():
    # The moat rule: this module reads the deployed system and must never be
    # able to mutate it, not even by a typo.
    source = inspect.getsource(fetch_fixtures)
    for verb in ('"POST"', '"PUT"', '"PATCH"', '"DELETE"'):
        assert verb not in source
    assert 'method="GET"' in source
