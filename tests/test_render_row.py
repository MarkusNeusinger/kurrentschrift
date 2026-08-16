"""The single production render-row builder (`core.database.models.template_render_row`).

Issue #289: the write path and the labs' live-DB mirror each hand-rolled this
dict and both dropped `glyph` — the field `core.pipeline._fluent_widen` keys
the round-letter body widening on — so production composed WITHOUT the widening
while the wordbench fixtures (whose rows carry `glyph`) measured WITH it. One
shared builder plus the parity pin below keep the fixture exporter and the
production row shape-identical, so this class of silent divergence cannot
recur: a render-relevant field added to one side fails here until it lands on
the other.
"""

from __future__ import annotations

from types import SimpleNamespace

from core.database.models import template_render_row
from tools.wordbench.export_fixtures import _template_dict


# The exporter's bookkeeping fields — everything else in a fixture row must be
# exactly the production render row.
FIXTURE_BOOKKEEPING = {"glyph_key", "updated_at"}


def _stub_template() -> SimpleNamespace:
    return SimpleNamespace(
        glyph_key="e",
        glyph="e",
        advance=0.45,
        entry={"xy": [0.0, 0.0], "tangent_deg": 60.0},
        exit_pt={"xy": [0.45, 0.0], "tangent_deg": -60.0},
        anchors=[[0.0, 0.0], [0.2, 1.0], [0.45, 0.0]],
        half_widths=[0.05, 0.05, 0.05],
        trace_meta={"stroke_starts": [0]},
        updated_at=None,
    )


def test_render_row_carries_the_widening_key() -> None:
    assert template_render_row(_stub_template())["glyph"] == "e"


def test_fixture_exporter_row_is_the_render_row_plus_bookkeeping() -> None:
    stub = _stub_template()
    row = template_render_row(stub)
    fixture = _template_dict(stub)
    assert set(fixture) == set(row) | FIXTURE_BOOKKEEPING
    for key, value in row.items():
        assert fixture[key] == value, key


def test_render_row_tolerates_empty_json_fields() -> None:
    stub = _stub_template()
    stub.entry = None
    stub.exit_pt = None
    stub.trace_meta = None
    row = template_render_row(stub)
    assert row["entry"] == {}
    assert row["exit_pt"] == {}
    assert row["trace_meta"] == {}
