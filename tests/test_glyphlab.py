"""Smoke tests for the glyphlab inspection toolkit (fixtures only, no DB)."""

from __future__ import annotations

import numpy as np
import pytest

from tools.glyphlab import (
    derive,
    derive_stages,
    figure,
    fixture_case,
    iter_fixture_cases,
    overlay,
    panel,
    save,
    stage_panels,
)
from tools.glyphlab.cases import DEFAULT_FIXTURES_DIR


# The glyph-bench fixtures are exported once from the DB and gitignored (derived,
# DB-sourced data), so they exist on a dev machine but not in CI. These tests
# exercise the real derivation against them; skip cleanly when they are absent.
pytestmark = pytest.mark.skipif(
    not any(DEFAULT_FIXTURES_DIR.rglob("manifest.json")), reason="glyph-bench fixtures are local-only (gitignored)"
)


def test_fixture_case_loads_constant_and_pressure() -> None:
    suet = fixture_case("i-initial")
    assert suet.glyph == "i" and suet.position == "initial"
    assert suet.is_constant  # Sütterlin Gleichzug
    assert len(suet.raw_path) > 2
    loth = fixture_case("longs-final", source_id="loth-1866")  # Kurrent ſ (pressure); ſ now exists in both sets
    assert not loth.is_constant


def test_derive_produces_aligned_arrays() -> None:
    res = derive(fixture_case("i-initial"))
    n = len(res.anchors_px)
    assert n > 2
    assert res.anchors_px.shape == (n, 2)
    assert res.half_widths_px.shape == (n,)
    assert res.stroke_starts[0] == 0
    assert res.skel.shape == res.crop.shape == res.mask.shape
    # anchors land inside the crop bounds
    h, w = res.crop.shape
    assert (res.anchors_px[:, 0] >= -1).all() and (res.anchors_px[:, 0] <= w + 1).all()
    assert (res.anchors_px[:, 1] >= -1).all() and (res.anchors_px[:, 1] <= h + 1).all()


def test_derive_stages_match_production() -> None:
    case = fixture_case("i-initial")
    stages = derive_stages(case)
    assert [s.name for s in stages] == ["1 snapped", "2 smoothed", "3 resampled", "4 verticalized"]
    final = np.concatenate(stages[-1].strokes)
    prod = derive(case).anchors_px
    assert final.shape == prod.shape
    assert np.allclose(final, prod, atol=0.05)  # stage capture mirrors the real pipeline


def test_derive_stages_rejects_pressure() -> None:
    with pytest.raises(ValueError, match="Gleichzug-only"):
        derive_stages(fixture_case("longs-final", source_id="loth-1866"))  # Kurrent (pressure) → rejected


def test_overlay_figure_and_save(tmp_path) -> None:
    res = derive(fixture_case("i-initial"))
    fig = overlay(res, title="i")
    assert fig.get_axes()  # at least one panel axes
    grid = figure([panel(res, title="spline"), panel(res, style="dots", title="dots")])
    assert len(grid.get_axes()) == 2
    path = save(grid, "smoke", out_dir=tmp_path)
    assert path.exists() and path.suffix == ".png"


def test_stage_panels_build(tmp_path) -> None:
    case = fixture_case("i-initial")
    res = derive(case)
    panels = stage_panels(res, derive_stages(case))
    assert len(panels) == 4
    path = save(figure(panels, cols=4), "stages", out_dir=tmp_path)
    assert path.exists()


def test_iter_fixture_cases_dedups_keys() -> None:
    # Keys are unique across manifests (the `seen` dedup) and sorted; the `only`
    # filter returns exactly the requested subset. Derived from the actual fixtures
    # so it survives a re-export changing which positions collapse together.
    keys = [c.key for c in iter_fixture_cases()]
    assert keys == sorted(set(keys))
    pick = keys[:2]
    assert {c.key for c in iter_fixture_cases(only=pick)} == set(pick)


def test_fixture_case_source_preference_avoids_collision() -> None:
    """A glyph_key shared by the Kurrent and Sütterlin sets resolves to the requested
    source, not the first manifest alphabetically (kurrent < suetterlin) — the old
    silent-collision bug that rendered the Kurrent glyph for a Sütterlin key."""
    case = fixture_case("longs-final", source_id="suetterlin-1922")
    assert case.origin.endswith("suetterlin-1922")
    assert case.width_resolver == "constant"  # Gleichzug → the Sütterlin ſ, not the Kurrent one
