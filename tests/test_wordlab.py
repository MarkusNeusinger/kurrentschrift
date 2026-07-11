"""Smoke tests for the wordlab inspection toolkit (fixtures only, no DB)."""

from __future__ import annotations

import dataclasses
import json

import pytest

from tools.glyphlab.render import save, tile
from tools.wordlab import WordCase, derive_word, fixture_word_case, iter_fixture_word_cases, word_panel
from tools.wordlab.cases import DEFAULT_FIXTURES_DIR, _root_for


# The word-bench fixtures are exported once from the DB and gitignored (derived,
# DB-sourced data), so they exist on a dev machine but not in CI. These tests
# exercise the real composition + scoring against them; skip when absent.
pytestmark = pytest.mark.skipif(
    not any(DEFAULT_FIXTURES_DIR.rglob("manifest.json")), reason="word-bench fixtures are local-only (gitignored)"
)


def _first_scorable_id(which: str = "words") -> str:
    """A scorable entry id from the frozen set (derived so it survives a re-export).

    Skips (not fails) when THIS set was never exported: the module skipif only
    proves that some manifest exists, but words and pairs are exported
    separately (`--set`), so a words-only machine must skip the pairs test.
    """
    try:
        root = _root_for(DEFAULT_FIXTURES_DIR, "suetterlin", which)
    except KeyError:
        pytest.skip(f"no {which} fixture set exported (run export_fixtures --set {which})")
    manifest = json.loads((root / "manifest.json").read_text())
    for entry in manifest["words"]:
        if entry.get("scorable", not entry.get("missing_at_export")):
            return entry.get("id", entry["word"])
    raise AssertionError(f"no scorable {which} entry in {root}")


def test_fixture_word_case_loads_aligned_fields() -> None:
    case = fixture_word_case(_first_scorable_id())
    assert case.kind == "word"
    assert case.has_specimen  # a fixture always carries its specimen
    assert case.crop.ndim == 2 and case.skel.shape == case.crop.shape
    assert case.slots and all(s.text for s in case.slots)
    # the crop rect height/width match the loaded crop
    x0, y0, x1, y1 = case.rect
    assert case.crop.shape == (y1 - y0, x1 - x0)
    assert case.style_ratio and case.width_resolver
    assert case.origin.startswith("fixture:")


def test_iter_fixture_word_cases_respects_only() -> None:
    all_cases = iter_fixture_word_cases()
    assert len(all_cases) > 1
    pick = [c.id for c in all_cases[:2]]
    subset = iter_fixture_word_cases(only=pick)
    # `only` matches by id OR word (mirrors the bench filter), so a picked id that
    # is also another entry's word may pull that sibling in too: every pick is
    # present, and nothing unrelated to the picks comes back.
    assert set(pick) <= {c.id for c in subset}
    assert all(c.id in pick or c.word in pick for c in subset)


def test_derive_word_composes_scores_and_attributes() -> None:
    result = derive_word(fixture_word_case(_first_scorable_id()))

    items = result.composed["items"]
    connectors = [it for it in items if "rings" not in it]
    glyphs = [it for it in items if "rings" in it]
    assert glyphs and connectors  # a multi-letter word has both
    # provenance is on (compose_word(..., provenance=True))
    assert all("slot_index" in g and "glyph_key" in g for g in glyphs)
    assert all("pair" in c and "from_slot" in c and "to_slot" in c for c in connectors)

    assert result.report is not None and not result.report["failed"]
    reg = result.report["registration"]
    assert {"tx", "ty", "xh_px"} <= reg.keys()

    segs = result.segments
    assert segs is not None
    assert {s["kind"] for s in segs} <= {"glyph", "connector"}
    # writing order: a word opens on a glyph; it MAY close on the generated
    # word-final Endstrich/Auslauf (a connector-kind segment) — emitted for
    # joining last letters with a forward rising OR high forward exit (see
    # end_swing inside core.compose.compose_word), so the last segment's kind
    # is not an invariant.
    assert segs[0]["kind"] == "glyph"
    assert any(s["kind"] == "connector" for s in segs)
    for s in segs:
        assert 0.0 <= s["penalty"] <= 1.0
        assert len(s["x_span_px"]) == 2


def test_word_panel_tile_and_save(tmp_path) -> None:
    result = derive_word(fixture_word_case(_first_scorable_id()))
    draws = [word_panel(result, title="plain"), word_panel(result, title="heat", heatmap=True, callouts=False)]
    fig = tile(draws, cols=1, panel_size=4.5, dpi=120)
    assert len(fig.get_axes()) == 2
    path = save(fig, "wordlab_smoke", out_dir=tmp_path)
    assert path.exists() and path.suffix == ".png"


def test_pairs_set_case_loads() -> None:
    case = fixture_word_case(_first_scorable_id("pairs"), which="pairs")
    assert case.kind == "pair"
    assert case.has_specimen
    result = derive_word(case)
    assert result.report is not None


def test_no_specimen_case_skips_scoring(tmp_path) -> None:
    """A specimen-stripped case (stands in for a live case, no DB) composes but
    does not score — report and segments are None, and it still renders."""
    base = fixture_word_case(_first_scorable_id())
    synthetic = dataclasses.replace(
        base, crop=None, skel=None, rect=None, baseline_y=None, midband_y=None, origin="live:synthetic"
    )
    assert not synthetic.has_specimen
    result = derive_word(synthetic)
    assert result.composed["items"]  # it still composes
    assert result.report is None and result.segments is None
    path = save(tile([word_panel(result)], cols=1, panel_size=4.5, dpi=120), "wordlab_live", out_dir=tmp_path)
    assert path.exists()


def test_derive_word_uses_isinstance_wordcase() -> None:
    case = fixture_word_case(_first_scorable_id())
    assert isinstance(case, WordCase)
