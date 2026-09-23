"""The Abzugs-Linse core: every deduction of the Gleichzug metric, located.

Pins the one promise the lens makes — the sites of a category add up to the
number the metric shows for it, to its fourth digit — and the one it keeps
by construction: the frozen metric's own result comes back unchanged. On
hand-built geometry (always run, CI included) and, where the gitignored
glyph-bench fixtures exist, over every frozen Sütterlin letter. A metric
re-baseline that this module does not follow breaks that sweep on purpose —
locally, since CI has no fixtures and skips it.
"""

from __future__ import annotations

import json

import numpy as np
import pytest
from PIL import Image

import core.quality_localize as localize
from core.extract import skeleton_and_width
from core.quality import crop_local_anchors, silhouette_mask
from core.quality_localize import (
    CATEGORIES,
    PIN_COUNT,
    RIM_PX,
    PenaltyMap,
    UnscorableInputError,
    _apportion,
    _interior_corner_anchors,
    suetterlin_penalty_sites,
    suetterlin_penalty_sites_for_glyph,
)
from core.quality_suetterlin import suetterlin_quality_for_glyph, suetterlin_quality_metrics
from tools.glyphbench.run import DEFAULT_FIXTURES_DIR


UNIT_PX = 100.0


def _units(value: float) -> int:
    return round(value * 10**4)


def _assert_sums_hold(pm: PenaltyMap) -> None:
    """The lens's contract, category by category."""
    components = pm.metrics["components"]
    for key in CATEGORIES:
        cat = pm.categories[key]
        assert cat.value == components[key]
        assert cat.in_sync, key
        # The unrounded contributions reproduce the metric's number …
        assert round(sum(site.raw for site in cat.sites), 4) == components[key], key
        # … and the shown four-place values add up to it exactly, digit for digit.
        assert sum(_units(site.value) for site in cat.sites) == _units(components[key]), key
        if cat.parts:
            assert sum(_units(v) for v in cat.parts.values()) == _units(components[key])
        if not cat.applicable:
            assert cat.value == 0.0 and not cat.sites


def _score(
    anchors_px: np.ndarray,
    half_widths_px: np.ndarray,
    stroke_starts: list[int],
    mask: np.ndarray,
    corner_anchors: list[int] | None = None,
) -> tuple[PenaltyMap, dict]:
    skel, width_map = skeleton_and_width(mask)
    args = (np.asarray(anchors_px, float), np.asarray(half_widths_px, float), stroke_starts, mask, skel, width_map)
    kwargs = {"unit_px": UNIT_PX, "corner_anchors": corner_anchors}
    return suetterlin_penalty_sites(*args, **kwargs), suetterlin_quality_metrics(*args, **kwargs)


def _reversal() -> tuple[np.ndarray, list[int]]:
    """Down, a sharp turn, up and out: a V with its apex as the declared corner."""
    down = np.column_stack([np.full(12, 60.0), np.linspace(20.0, 120.0, 12)])
    up = np.column_stack([np.linspace(60.0, 110.0, 12), np.linspace(120.0, 40.0, 12)])
    anchors = np.vstack([down, up[1:]])
    return anchors, [len(down) - 1]


# ------------------------------------------------------------- synthetic cases


def test_the_frozen_metric_comes_back_unchanged():
    anchors, corners = _reversal()
    hw = np.full(len(anchors), 4.0)
    mask = silhouette_mask(anchors + [1.5, 0.0], np.full(len(anchors), 5.0), [0], (160, 160), corner_anchors=corners)
    pm, metrics = _score(anchors, hw, [0], mask, corners)
    assert pm.metrics == metrics
    assert (pm.width, pm.height, pm.unit_px) == (160, 160, UNIT_PX)
    _assert_sums_hold(pm)


def test_each_corner_is_its_exact_term_and_carries_its_anchor():
    anchors, corners = _reversal()
    hw = np.full(len(anchors), 4.0)
    mask = silhouette_mask(anchors, hw, [0], (160, 160), corner_anchors=corners)
    pm, metrics = _score(anchors, hw, [0], mask, corners)
    corner = pm.categories["corner"]
    assert metrics["applicable"]["corners"] == 1
    assert [site.numbers["anchor"] for site in corner.sites] == corners
    (site,) = corner.sites
    # One corner is the whole mean: the literal term, marked as such.
    assert site.exact and site.kind == "corner"
    assert site.raw == pytest.approx(1.0 - site.numbers["q"], abs=1e-4)
    assert {p.role for p in site.paths} >= {"approach_in", "approach_out"}
    assert (site.x, site.y) == pytest.approx(tuple(anchors[corners[0]]), abs=0.6)


def test_a_corner_on_a_stroke_end_is_no_scored_corner():
    """`build_sample_plan` splits only at INTERIOR corners, so the lens must too —
    and the join to a Landmarken corner runs over the anchor number, not the index."""
    anchors, corners = _reversal()
    assert _interior_corner_anchors(len(anchors), [0], [0, *corners, len(anchors) - 1]) == corners
    two_strokes = _interior_corner_anchors(30, [0, 15], [5, 14, 15, 20])
    assert two_strokes == [5, 20]  # 14 is stroke 0's last row, 15 stroke 1's first
    hw = np.full(len(anchors), 4.0)
    mask = silhouette_mask(anchors, hw, [0], (160, 160), corner_anchors=corners)
    pm, _ = _score(anchors, hw, [0], mask, [0, *corners])
    assert [site.numbers["anchor"] for site in pm.categories["corner"].sites] == corners


def test_a_term_that_does_not_apply_has_no_sites():
    bar = np.column_stack([np.full(20, 50.0), np.linspace(10.0, 110.0, 20)])
    hw = np.full(len(bar), 4.0)
    mask = silhouette_mask(bar, hw, [0], (130, 100))
    pm, metrics = _score(bar, hw, [0], mask)
    assert metrics["applicable"]["corners"] == 0
    for key in ("corner", "collinearity", "retrace"):
        assert not pm.categories[key].applicable
        assert pm.categories[key].sites == ()
    assert pm.categories["verticality"].applicable
    _assert_sums_hold(pm)


def test_the_quantised_rim_has_no_place_but_a_real_miss_has_one():
    bar = np.column_stack([np.full(20, 50.0), np.linspace(20.0, 110.0, 20)])
    hw = np.full(len(bar), 4.0)
    rendered = silhouette_mask(bar, hw, [0], (130, 100))
    # Ink one pixel wider than the render all round, plus a blob far off it.
    ink = np.zeros_like(rendered)
    rows, cols = np.nonzero(rendered)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            ink[np.clip(rows + dr, 0, 129), np.clip(cols + dc, 0, 99)] = True
    ink[60:66, 80:86] = True
    pm, _ = _score(bar, hw, [0], ink)
    coverage = pm.categories["coverage"]
    rim = [s for s in coverage.sites if s.kind == "rim"]
    assert len(rim) == 1 and rim[0].x is None and rim[0].numbers["rim_px"] == RIM_PX
    (blob,) = [s for s in coverage.sites if s.kind == "missed_ink"]
    assert blob.x is not None and 80 <= blob.x <= 85 and 60 <= blob.y <= 65
    assert blob.numbers["pixels"] == 36
    # Unlocated sites come last, and the parts split the whole deduction.
    assert coverage.sites[-1].x is None
    assert set(coverage.parts) == {"dice", "chamfer", "geo"}
    _assert_sums_hold(pm)


def test_each_missed_retrace_pixel_counts_exactly():
    """A doubled stem rendered too narrow for its ink: the missed sides are the sites."""
    up = np.column_stack([np.full(15, 46.0), np.linspace(88.0, 12.0, 15)])
    down = np.column_stack([np.full(15, 54.0), np.linspace(12.0, 88.0, 15)])
    anchors = np.vstack([up, down])
    hw = np.full(len(anchors), 4.0)
    ink = np.zeros((100, 100), dtype=bool)
    ink[8:93, 39:62] = True  # wider than the two passes render
    pm, metrics = _score(anchors, hw, [0, len(up)], ink)
    retrace = pm.categories["retrace"]
    assert metrics["applicable"]["retrace_pairs"] >= 3
    assert retrace.exact and retrace.value > 0.0
    assert all(site.kind == "missed_ink" and site.cells for site in retrace.sites)
    missed = sum(site.numbers["pixels"] for site in retrace.sites)
    assert missed == retrace.numbers["missed_px"]
    assert sum(site.raw for site in retrace.sites) == pytest.approx(missed / retrace.numbers["zone_ink_px"])
    assert retrace.context_cells  # the zone the recall is taken over
    _assert_sums_hold(pm)


def test_pins_rank_the_costliest_located_sites():
    anchors, corners = _reversal()
    hw = np.full(len(anchors), 4.0)
    mask = silhouette_mask(anchors + [2.0, 1.0], np.full(len(anchors), 5.5), [0], (160, 160), corner_anchors=corners)
    mask[140:150, 10:20] = True
    pm, _ = _score(anchors, hw, [0], mask, corners)
    assert 1 <= len(pm.pins) <= PIN_COUNT
    assert [pin.rank for pin in pm.pins] == list(range(1, len(pm.pins) + 1))
    points = [pin.points_est for pin in pm.pins]
    assert points == sorted(points, reverse=True)
    for pin in pm.pins:
        site = pm.categories[pin.category].sites[pin.index]
        assert site.x == pin.x and site.y == pin.y and site.raw > 0.0
        # A pin always lands on a DRAWN site: its apportioned share is visible.
        assert site.value > 0.0


def test_a_recomputation_that_drifts_claims_no_places(monkeypatch: pytest.MonkeyPatch):
    """If the ruler moved and this module did not follow, the number stays and the map goes."""
    real = localize.suetterlin_quality_metrics

    def drifted(*args: object, **kwargs: object) -> dict:
        out = real(*args, **kwargs)
        out["components"] = {**out["components"], "corner": round(out["components"]["corner"] + 0.05, 4)}
        return out

    monkeypatch.setattr(localize, "suetterlin_quality_metrics", drifted)
    anchors, corners = _reversal()
    hw = np.full(len(anchors), 4.0)
    mask = silhouette_mask(anchors, hw, [0], (160, 160), corner_anchors=corners)
    skel, width_map = skeleton_and_width(mask)
    pm = suetterlin_penalty_sites(anchors, hw, [0], mask, skel, width_map, unit_px=UNIT_PX, corner_anchors=corners)
    corner = pm.categories["corner"]
    assert not corner.in_sync
    (site,) = corner.sites
    assert site.x is None and site.kind == "unlocated"
    assert site.value == corner.value
    assert pm.categories["smoothness"].in_sync  # the others are untouched


def test_a_drifted_category_draws_no_context(monkeypatch: pytest.MonkeyPatch):
    """The context came from the recomputation the map was dropped for, so it goes too."""
    anchors, corners = _reversal()
    hw = np.full(len(anchors), 4.0)
    mask = silhouette_mask(anchors, hw, [0], (160, 160), corner_anchors=corners)
    trusted, _ = _score(anchors, hw, [0], mask, corners)
    # In sync, Glätte draws its corner windows and states its jerk …
    assert trusted.categories["smoothness"].context_paths
    assert "jerk" in trusted.categories["smoothness"].numbers
    assert trusted.pins

    monkeypatch.setattr(localize, "SYNC_TOLERANCE", -1.0)  # nothing agrees any more
    drifted, _ = _score(anchors, hw, [0], mask, corners)
    for key in CATEGORIES:
        cat = drifted.categories[key]
        assert not cat.in_sync, key
        # … out of sync, only the number and its one unlocated site remain.
        assert (cat.numbers, cat.parts, cat.context_paths, cat.context_cells) == ({}, {}, (), ()), key
        (site,) = cat.sites
        assert site.x is None and site.kind == "unlocated" and site.value == cat.value
    assert drifted.pins == ()


@pytest.mark.parametrize(
    ("bad", "match"),
    [
        ({"half_width_row": 3}, "half_widths_px"),
        ({"anchor_row": 5}, "anchors_px"),
        ({"unit_px": 0.0}, "unit_px"),
        ({"unit_px": float("inf")}, "unit_px"),
    ],
)
def test_non_finite_geometry_is_refused_not_mapped(bad: dict, match: str):
    """A NaN would reach the apportionment as a NaN component; refuse it up front instead."""
    bar = np.column_stack([np.full(20, 50.0), np.linspace(10.0, 110.0, 20)])
    hw = np.full(len(bar), 4.0)
    mask = silhouette_mask(bar, hw, [0], (130, 100))
    skel, width_map = skeleton_and_width(mask)
    if "half_width_row" in bad:
        hw[bad["half_width_row"]] = np.nan
    if "anchor_row" in bad:
        bar[bad["anchor_row"], 1] = np.nan
    with pytest.raises(UnscorableInputError, match=match):
        suetterlin_penalty_sites(bar, hw, [0], mask, skel, width_map, unit_px=bad.get("unit_px", UNIT_PX))
    # Still a ValueError, which is what callers of the metric already catch.
    assert issubclass(UnscorableInputError, ValueError)


def test_a_non_finite_component_is_refused_even_from_finite_input(monkeypatch: pytest.MonkeyPatch):
    real = localize.suetterlin_quality_metrics

    def broken(*args: object, **kwargs: object) -> dict:
        out = real(*args, **kwargs)
        out["components"] = {**out["components"], "smoothness": float("nan")}
        return out

    monkeypatch.setattr(localize, "suetterlin_quality_metrics", broken)
    bar = np.column_stack([np.full(20, 50.0), np.linspace(10.0, 110.0, 20)])
    hw = np.full(len(bar), 4.0)
    mask = silhouette_mask(bar, hw, [0], (130, 100))
    with pytest.raises(UnscorableInputError, match="smoothness"):
        _score(bar, hw, [0], mask)


def test_apportion_is_proportional_and_exact():
    assert _apportion([1.0, 1.0, 1.0], 10) == [4, 3, 3]
    assert sum(_apportion([0.3, 0.2, 0.0005, 0.1], 1711)) == 1711
    assert _apportion([0.5, 0.5], 0) == [0, 0]
    assert _apportion([0.0, 0.0], 5) == [0, 0]
    assert _apportion([], 0) == []


# --------------------------------------------------------------- end to end


def test_for_glyph_matches_the_stored_scorer(synthetic_chart_path: str, synthetic_bbox: dict):
    from core.suetterlin import canonical_suetterlin_from_path

    path = [{"x": 400.0, "y": float(200 + 400 * i / 39), "pressure": None, "t": float(i)} for i in range(40)]
    canon = canonical_suetterlin_from_path(
        raw_path=path, bbox=synthetic_bbox, chart_path=synthetic_chart_path, glyph="i", n_anchors=20
    )
    pm = suetterlin_penalty_sites_for_glyph(canon, synthetic_bbox, synthetic_chart_path)
    assert pm.metrics == suetterlin_quality_for_glyph(canon, synthetic_bbox, synthetic_chart_path)
    assert (pm.width, pm.height) == (200, 600)
    _assert_sums_hold(pm)
    with pytest.raises(ValueError, match="pixel_anchors"):
        suetterlin_penalty_sites_for_glyph({"trace_meta": {}}, synthetic_bbox, synthetic_chart_path)


# ------------------------------------------------------------ fixture sweep


_MANIFESTS = sorted(DEFAULT_FIXTURES_DIR.rglob("manifest.json"))
_CONSTANT = [m for m in _MANIFESTS if json.loads(m.read_text()).get("width_resolver") == "constant"]


@pytest.mark.skipif(not _CONSTANT, reason="glyph-bench fixtures are local-only (gitignored)")
def test_every_frozen_suetterlin_letter_is_localized_to_its_last_digit():
    """Every frozen Sütterlin letter (62 today): zero difference allowed."""
    swept = 0
    for manifest in _CONSTANT:
        for entry in json.loads(manifest.read_text())["glyphs"]:
            glyph_dir = manifest.parent / entry["glyph_key"]
            trace_meta = json.loads((glyph_dir / "template.json").read_text())["trace_meta"]
            if not trace_meta.get("pixel_anchors"):
                continue
            bbox = json.loads((glyph_dir / "bbox.json").read_text())
            mask = np.asarray(Image.open(glyph_dir / "ref_mask.png")) > 127
            with np.load(glyph_dir / "ref_skel.npz") as refs:
                skel = refs["skel"].astype(bool)
                width_map = refs["width_map"].astype(float)
            args = (
                crop_local_anchors(trace_meta["pixel_anchors"], bbox),
                np.asarray(trace_meta["half_widths_px"], dtype=float),
                trace_meta["stroke_starts"],
                mask,
                skel,
                width_map,
            )
            kwargs = {"unit_px": float(trace_meta["unit_px"]), "corner_anchors": trace_meta.get("corner_anchors")}
            pm = suetterlin_penalty_sites(*args, **kwargs)
            assert pm.metrics == suetterlin_quality_metrics(*args, **kwargs), entry["glyph_key"]
            _assert_sums_hold(pm)
            declared = set(trace_meta.get("corner_anchors") or [])
            assert {s.numbers["anchor"] for s in pm.categories["corner"].sites} <= declared
            swept += 1
    assert swept > 0
