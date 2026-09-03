"""tools/glyphbench/export_fixtures.py — which rows reach the frozen fixture.

The glyph bench re-derives every canonical from the chart bytes plus a stylus
path, and every row is written into the shared directory `<glyph_key>/`. A row
without a path therefore does two kinds of damage at once: it cannot be scored,
and it displaces the chart row that could. These tests pin the selection that
stops it — the defect the re-baseline of 2026-09-03 uncovered
(`qualitaetsmetrik.md` §5, "Re-Baseline 2026-09-03").
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest

from tools.glyphbench import export_fixtures
from tools.glyphbench.export_fixtures import select_exportable, write_fixture_root


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


# --------------------------------------------------------------- the swap

CHART = np.full((40, 40), 0.9, dtype=float)
MANIFEST_BASE = {"source_id": "s", "style_id": "st", "chart_path": "c.jpg", "chart_sha256": "abc"}


def _kept(*glyph_keys: str):
    return [(_template_dict_for(k), _bbox_dict_for(k), [k]) for k in glyph_keys]


def _template_dict_for(glyph_key: str) -> dict:
    t = _template(glyph_key)
    return {k: getattr(t, k) for k in ("glyph_key", "glyph", "variant", "raw_path", "updated_at")}


def _bbox_dict_for(glyph_key: str) -> dict:
    b = _bbox(glyph_key)
    return {
        k: getattr(b, k)
        for k in ("y0", "y1", "x0", "x1", "mask_strokes", "baseline_y", "midband_y", "n_anchors", "locked")
    }


def _stale_root(tmp_path):
    """A previous export, including a directory whose key died with 0017."""
    root = tmp_path / "suetterlin-1922"
    (root / "i-initial").mkdir(parents=True)
    (root / "i-initial" / "template.json").write_text("{}")
    (root / "manifest.json").write_text(json.dumps({"exported_at": "2026-06-18T20:51:32+00:00"}))
    return root


def test_the_swap_replaces_the_root_rather_than_merging_into_it(tmp_path):
    """The stale-directory half of the defect: a key from an older schema must
    not survive into the new root looking like a live fixture."""
    root = _stale_root(tmp_path)

    write_fixture_root(root, _kept("a", "b"), CHART, MANIFEST_BASE)

    assert sorted(p.name for p in root.iterdir() if p.is_dir()) == ["a", "b"]
    assert not (root / "i-initial").exists()
    assert json.loads((root / "manifest.json").read_text())["source_id"] == "s"


def test_a_failure_mid_loop_leaves_the_previous_root_untouched(tmp_path):
    """The reason the swap exists. A frozen root is the reference every quoted
    number stands on, so a crop or write failure partway through must cost
    nothing — not the old baseline, and not a half-written new one."""
    root = _stale_root(tmp_path)
    before = json.loads((root / "manifest.json").read_text())

    calls = {"n": 0}

    def explode(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] > 1:  # the first glyph writes, the second dies
            raise RuntimeError("binarization blew up")
        return export_fixtures.binarize_adaptive(*args, **kwargs)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(export_fixtures, "binarize_adaptive", explode)
        with pytest.raises(RuntimeError, match="binarization blew up"):
            write_fixture_root(root, _kept("a", "b"), CHART, MANIFEST_BASE)

    assert (root / "i-initial").exists(), "the old root was destroyed by a failed export"
    assert json.loads((root / "manifest.json").read_text()) == before
    assert not root.with_name(f"{root.name}.staging").exists(), "staging left behind"


def test_a_leftover_staging_directory_does_not_poison_the_next_export(tmp_path):
    """A hard kill (SIGKILL, full disk) can strand a staging directory that no
    `except` ever ran for. The next export must clear it, not merge into it."""
    root = tmp_path / "suetterlin-1922"
    staging = root.with_name(f"{root.name}.staging")
    (staging / "ghost").mkdir(parents=True)

    write_fixture_root(root, _kept("a"), CHART, MANIFEST_BASE)

    assert sorted(p.name for p in root.iterdir() if p.is_dir()) == ["a"]
    assert not staging.exists()
