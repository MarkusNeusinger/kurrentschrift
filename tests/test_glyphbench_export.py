"""tools/glyphbench/export_fixtures.py — which rows reach the frozen fixture.

The glyph bench re-derives every canonical from the chart bytes plus a stylus
path, and every row is written into the shared directory `<glyph_key>/`. A row
without a path therefore does two kinds of damage at once: it cannot be scored,
and it displaces the chart row that could. These tests pin the selection that
stops it — the defect the re-baseline of 2026-09-03 uncovered
(`qualitaetsmetrik.md` §5, "Re-Baseline 2026-09-03").
"""

from __future__ import annotations

from types import SimpleNamespace

from tools.glyphbench.export_fixtures import select_exportable


def _template(glyph_key: str, variant: int = 0, *, traced: bool = True):
    return SimpleNamespace(
        glyph_key=glyph_key,
        glyph=glyph_key,
        variant=variant,
        advance=1.0,
        entry={},
        exit_pt={},
        anchors=[[0.0, 0.0], [1.0, 1.0]],
        half_widths=[0.05, 0.05],
        raw_path=[{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 1.0}] if traced else [],
        trace_meta={},
        measurements={},
        updated_at=None,
    )


def _bbox(glyph_key: str, *, locked: bool = True):
    return SimpleNamespace(
        glyph_key=glyph_key,
        y0=0,
        y1=10,
        x0=0,
        x1=10,
        mask_strokes=[],
        baseline_y=8,
        midband_y=4,
        n_anchors=120,
        locked=locked,
    )


def test_the_laufform_row_never_displaces_its_chart_row():
    """The defect itself: the Laufform (variant 100) sorts after the chart row
    and shares its directory, so before this filter it overwrote a scoreable
    template with an underivable one — 22 keys and 44 crashes on the 1922
    source."""
    templates = [_template("a", 0), _template("a", 100, traced=False)]
    entries, _, no_trace = select_exportable(templates, {"a": _bbox("a")}, False)

    assert [t["variant"] for t, _ in entries] == [0]
    assert no_trace == ["a#100"]


def test_an_untraced_form_variant_is_caught_too():
    """The filter tests the PATH, not the variant number — the 1922 `i` carries
    an authored variant 1 that was never traced, and it is just as underivable
    as a Laufform."""
    templates = [_template("i", 0), _template("i", 1, traced=False)]
    entries, _, no_trace = select_exportable(templates, {"i": _bbox("i")}, False)

    assert len(entries) == 1
    assert no_trace == ["i#1"]


def test_a_traced_form_variant_is_kept():
    """The converse, so the filter cannot quietly become "variant 0 only":
    positionally sanctioned form variants are real library entries
    (architektur.md §3) and score like any other row."""
    templates = [_template("A", 0), _template("A", 1)]
    entries, _, no_trace = select_exportable(templates, {"A": _bbox("A")}, False)

    assert sorted(t["variant"] for t, _ in entries) == [0, 1]
    assert no_trace == []


def test_unlocked_rows_are_counted_and_can_be_opted_in():
    templates = [_template("a"), _template("b")]
    bboxes = {"a": _bbox("a"), "b": _bbox("b", locked=False)}

    entries, unlocked, _ = select_exportable(templates, bboxes, False)
    assert [t["glyph_key"] for t, _ in entries] == ["a"]
    assert unlocked == 1

    entries, unlocked, _ = select_exportable(templates, bboxes, True)
    assert sorted(t["glyph_key"] for t, _ in entries) == ["a", "b"]
    assert unlocked == 0


def test_a_row_without_a_bbox_is_skipped_silently():
    """No crop, nothing to score against — and unlike the cases above it is not
    a defect worth naming, so it stays out of both counters."""
    entries, unlocked, no_trace = select_exportable([_template("z")], {}, False)
    assert (entries, unlocked, no_trace) == ([], 0, [])
