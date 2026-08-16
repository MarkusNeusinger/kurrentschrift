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

from core.database.models import Template, template_render_row
from tools.wordbench.export_fixtures import _template_dict


# The exporter's bookkeeping fields — everything else in a fixture row must be
# exactly the production render row.
FIXTURE_BOOKKEEPING = {"glyph_key", "updated_at"}


def _transient_template() -> Template:
    # A real (never-flushed) ORM instance: what both builders actually consume.
    return Template(
        style_id="teststyle",
        glyph_key="e",
        glyph="e",
        variant=0,
        advance=0.45,
        entry={"xy": [0.0, 0.0], "tangent_deg": 60.0, "coupling": "baseline"},
        exit_pt={"xy": [0.45, 0.0], "tangent_deg": -60.0, "coupling": "baseline"},
        anchors=[[0.0, 0.0], [0.2, 1.0], [0.45, 0.0]],
        half_widths=[0.05, 0.05, 0.05],
        raw_path=[],
        trace_meta={"stroke_starts": [0]},
        measurements={},
    )


def test_render_row_carries_the_widening_key() -> None:
    assert template_render_row(_transient_template())["glyph"] == "e"


def test_fixture_exporter_row_is_the_render_row_plus_bookkeeping() -> None:
    template = _transient_template()
    row = template_render_row(template)
    fixture = _template_dict(template)
    assert set(fixture) == set(row) | FIXTURE_BOOKKEEPING
    for key, value in row.items():
        assert fixture[key] == value, key


def test_render_row_tolerates_empty_json_fields() -> None:
    template = _transient_template()
    template.entry = None
    template.exit_pt = None
    template.trace_meta = None
    row = template_render_row(template)
    assert row["entry"] == {}
    assert row["exit_pt"] == {}
    assert row["trace_meta"] == {}
