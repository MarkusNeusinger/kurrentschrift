"""The Streifen-Befund: what the sensor reads off written ink, and what it suggests.

The references are rasterised from a DISTANCE FIELD, not drawn with a polyline
rasteriser: a stroke drawn as a chain of rectangles has a scalloped boundary,
and the sub-pixel re-centring the Befund does faithfully reports those scallops
as wobble. A distance field gives ink whose boundary is exactly one offset of
the curve, which is what a pen makes — so a false positive here is the sensor's
and not the fixture's. Each case is the smallest thing that can carry the
defect it is named for: a clean arc, a corner, a closed loop, a broken run, a
thinner pen.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from core.continuity import KINK_THRESHOLD_DEG
from core.eigenhand import bestand as bestand_module
from core.eigenhand.befund import (
    GRUND_FEDER_DICK,
    GRUND_FEDER_DUENN,
    GRUND_KNICK,
    GRUND_KRINGEL,
    GRUND_NICHTS,
    GRUND_STRICHFOLGE,
    PLATE_PEN_HALF_WIDTH_UNITS,
    befund,
    befund_index,
    befunde_of_strip,
    body_runs_expected,
    hand_nib_median,
    loop_expectation,
    measure_strip,
    weakest_fassungen,
    word_glyph_keys,
)
from core.eigenhand.kartei import empty_kartei


PX_PER_MM = 300.0 / 25.4
BAND = {"asc_top": 30.0, "waist": 36.0, "baseline": 42.0, "desc_bot": 48.0}
ORIGIN = (12.0, 26.0)
UNIT_PX = (BAND["baseline"] - BAND["waist"]) * PX_PER_MM
NIB_HALF_PX = PLATE_PEN_HALF_WIDTH_UNITS * UNIT_PX
BOX = (14.0, 34.0)
HEIGHT = round((BAND["desc_bot"] + 4.0 - ORIGIN[1]) * PX_PER_MM)
WIDTH = round((BOX[1] - ORIGIN[0]) * PX_PER_MM) + 40


def _blank() -> np.ndarray:
    return np.full((HEIGHT, WIDTH), 0.92)


def _paint(plane: np.ndarray, curve: list[tuple[float, float]], half: float = NIB_HALF_PX) -> np.ndarray:
    """Ink a polyline as the offset of a distance field — a pen's own boundary."""
    yy, xx = np.mgrid[0 : plane.shape[0], 0 : plane.shape[1]]
    points = np.asarray(curve, dtype=float)
    distance = np.full(plane.shape, 1e9)
    for (x0, y0), (x1, y1) in zip(points[:-1], points[1:], strict=True):
        vx, vy = x1 - x0, y1 - y0
        t = np.clip(((xx - x0) * vx + (yy - y0) * vy) / max(vx * vx + vy * vy, 1e-9), 0.0, 1.0)
        distance = np.minimum(distance, np.hypot(xx - x0 - t * vx, yy - y0 - t * vy))
    np.minimum(plane, 0.92 - 0.82 * np.clip(half + 0.5 - distance, 0.0, 1.0), out=plane)
    return plane


def _y(mm: float) -> float:
    return (mm - ORIGIN[1]) * PX_PER_MM


def _x0() -> int:
    return round((BOX[0] - ORIGIN[0]) * PX_PER_MM)


def _row(word: str = "nun") -> dict:
    return {"band_mm": BAND, "boxes": [{"word": word, "x0_mm": BOX[0], "x1_mm": BOX[1]}]}


def _measure(plane: np.ndarray, word: str = "nun", catalogue: dict | None = None) -> dict:
    return measure_strip(
        plane, _row(word), crop_origin_mm=ORIGIN, px_per_mm=PX_PER_MM, catalogue=catalogue, catalogue_quelle="test"
    )


def _arc(samples: int = 400) -> list[tuple[float, float]]:
    return [
        (_x0() + 20 + i / (samples - 1) * 180, _y(42.0) - 70 * math.sin(math.pi * i / (samples - 1)))
        for i in range(samples)
    ]


def _ring(radius: float = 45.0, samples: int = 400) -> list[tuple[float, float]]:
    return [
        (
            _x0() + 90 + radius * math.cos(2 * math.pi * i / (samples - 1)),
            _y(39.0) + radius * math.sin(2 * math.pi * i / (samples - 1)),
        )
        for i in range(samples)
    ]


# ---------------------------------------------------------------- the readings


def test_clean_stroke_has_no_kink_and_reads_the_pen_it_was_drawn_with() -> None:
    reading = _measure(_paint(_blank(), _arc()))["woerter"][0]
    assert reading["leer"] is False
    assert reading["unstetigkeit"]["kink_count"] == 0
    assert reading["unstetigkeit"]["kink_max_deg"] < KINK_THRESHOLD_DEG
    # The pen it was inked with, to within a few percent of an x-height.
    assert reading["nib_units"] == pytest.approx(PLATE_PEN_HALF_WIDTH_UNITS, rel=0.1)
    assert befund(_measure(_paint(_blank(), _arc()))).vorschlag == "sauber"


def test_a_corner_between_two_straight_runs_is_one_kink_event() -> None:
    plane = _paint(_blank(), [(_x0() + 20, _y(42.0)), (_x0() + 110, _y(34.0)), (_x0() + 200, _y(41.0))])
    reading = _measure(plane)["woerter"][0]
    assert reading["unstetigkeit"]["kink_count"] == 1
    assert reading["unstetigkeit"]["kink_max_deg"] > 2 * KINK_THRESHOLD_DEG
    assert befund(_measure(plane)).grund == GRUND_KNICK


def test_a_closed_ring_is_one_counter_with_its_clear_aperture() -> None:
    reading = _measure(_paint(_blank(), _ring()))["woerter"][0]
    assert reading["kringel"]["gefunden"] == 1
    # The ink hole is the ring's diameter minus the pen: 2·(45 − nib) in px.
    assert reading["kringel"]["weiten"][0] == pytest.approx(2 * (45 - NIB_HALF_PX) / UNIT_PX, rel=0.15)
    assert reading["teile"]["koerper"] == 1
    assert befund(_measure(_paint(_blank(), _ring()))).vorschlag == "sauber"


def test_ink_broken_into_two_runs_where_the_script_joins_is_a_ductus_finding() -> None:
    plane = _paint(_blank(), [(_x0() + 20, _y(42.0)), (_x0() + 80, _y(37.0))])
    plane = _paint(plane, [(_x0() + 140, _y(42.0)), (_x0() + 200, _y(37.0))])
    reading = _measure(plane)["woerter"][0]
    assert reading["teile"]["koerper"] == 2
    assert reading["teile"]["koerper_soll"] == 1
    verdict = befund(_measure(plane))
    assert verdict.grund == GRUND_STRICHFOLGE
    assert verdict.vorschlag == "neu schreiben"
    # Rule 3: the topology outranks the smoothness — the ink is otherwise
    # flawless here, and the ductus finding still names the strip.
    assert verdict.unstetigkeit["kink_count"] == 0


def test_a_pen_far_off_the_hands_own_is_named_thin_or_thick_but_does_not_rank() -> None:
    thin = _measure(_paint(_blank(), _arc(), half=NIB_HALF_PX * 0.5))
    thick = _measure(_paint(_blank(), _arc(), half=NIB_HALF_PX * 1.8))
    assert befund(thin, nib_referenz=PLATE_PEN_HALF_WIDTH_UNITS).grund == GRUND_FEDER_DUENN
    assert befund(thick, nib_referenz=PLATE_PEN_HALF_WIDTH_UNITS).grund == GRUND_FEDER_DICK
    # The pen is a cohort question, not a cleanliness one: it names the reason
    # and leaves the ordering to the naturalness terms.
    assert befund(thin, nib_referenz=PLATE_PEN_HALF_WIDTH_UNITS).guete > 90
    # …and against its OWN median it is simply the pen of the day.
    assert befund(thin, nib_referenz=thin["woerter"][0]["nib_units"]).grund == GRUND_NICHTS


def test_a_counter_the_catalogue_holds_open_that_shows_no_hole_is_kringel_zu() -> None:
    catalogue = {"n": [{"state": "offen"}], "u": [{"state": "punkt"}]}
    # A bare arc: no hole anywhere, but `nun` is expected to carry two open n
    # counters. Both are unaccounted for.
    verdict = befund(_measure(_paint(_blank(), _arc()), catalogue=catalogue))
    assert verdict.kringel["offen_soll"] == 2
    assert verdict.kringel["zu"] == 2
    assert verdict.kringel["zu_an"] == ["n#0", "n#0"]
    assert verdict.kringel["quelle"] == "test"
    assert verdict.grund == GRUND_KRINGEL
    assert verdict.vorschlag == "neu schreiben"
    # …and the ring HAS a hole, so one expectation is met.
    met = befund(_measure(_paint(_blank(), _ring()), catalogue={"n": [{"state": "offen"}]}))
    assert met.kringel["zu"] == 1  # `nun` expects two, the ring shows one


def test_an_empty_box_is_stated_never_scored() -> None:
    reading = _measure(_blank())["woerter"][0]
    assert reading["leer"] is True
    assert "unstetigkeit" not in reading
    verdict = befund(_measure(_blank()))
    assert verdict.vorschlag == "neu schreiben"
    assert verdict.guete == 0.0


def test_no_measurement_at_all_reads_as_no_befund() -> None:
    assert befund(None) is None
    assert befund({}) is None


# -------------------------------------------------------------------- the Soll


def test_the_word_soll_comes_from_the_shaping_not_from_a_table() -> None:
    assert word_glyph_keys("lesen") == ["l", "e", "longs", "e", "n"]  # repeats kept
    assert body_runs_expected("lesen") == 1
    assert body_runs_expected("1922") == 4  # digits carry joins: false
    assert body_runs_expected("ja!") == 2
    expectation = loop_expectation("lesen", {"e": [{"state": "offen"}, {"state": "punkt"}]})
    assert expectation == {"offen": ["e#0", "e#0"], "wechselnd": 0, "punkt": 2}


# ----------------------------------------------------------------- the ranking


def _kartei_with(*measurements: tuple[str, dict], strip: str = "S0001") -> dict:
    kartei = empty_kartei("mn-suetterlin", "suetterlin")
    kartei["sheets"]["B0001"] = {"printed": "2026-09-07", "strips": [strip], "layout_sha256": "x", "scans": []}
    kartei["strips"][strip] = {
        "fassungen": [
            {"id": fid, "sheet": "B0001", "row_index": 0, "status": "angenommen", "befund": measurement}
            for fid, measurement in measurements
        ]
    }
    return kartei


def test_fassungen_of_one_strip_are_ranked_and_a_better_later_one_supersedes() -> None:
    weak = _measure(_paint(_blank(), [(_x0() + 20, _y(42.0)), (_x0() + 110, _y(34.0)), (_x0() + 200, _y(41.0))]))
    strong = _measure(_paint(_blank(), _arc()))
    ranked = befunde_of_strip(_kartei_with(("F01", weak), ("F02", strong)), "S0001")
    assert ranked["F02"].rang == 1
    assert ranked["F01"].rang == 2
    assert ranked["F01"].von == 2
    # The replacement loop made visible — and nothing more: the weak Fassung
    # is still an accepted Beleg until the author retires it explicitly.
    assert ranked["F01"].abgeloest_von == "F02"
    assert ranked["F02"].abgeloest_von is None


def test_an_equally_good_rewrite_does_not_supersede() -> None:
    same = _measure(_paint(_blank(), _arc()))
    ranked = befunde_of_strip(_kartei_with(("F01", same), ("F02", dict(same))), "S0001")
    assert ranked["F01"].abgeloest_von is None
    assert ranked["F02"].abgeloest_von is None


def test_later_is_a_number_not_a_spelling() -> None:
    """`F100` comes AFTER `F99` — as text it would not, and only here it matters."""
    weak = _measure(_paint(_blank(), [(_x0() + 20, _y(42.0)), (_x0() + 110, _y(34.0)), (_x0() + 200, _y(41.0))]))
    strong = _measure(_paint(_blank(), _arc()))
    ranked = befunde_of_strip(_kartei_with(("F99", weak), ("F100", strong)), "S0001")
    assert ranked["F99"].abgeloest_von == "F100"
    assert ranked["F100"].abgeloest_von is None


def test_the_hands_own_pen_is_the_reference_and_the_index_carries_it() -> None:
    thin = _measure(_paint(_blank(), _arc(), half=NIB_HALF_PX * 0.5))
    kartei = _kartei_with(("F01", thin), ("F02", dict(thin)))
    median = hand_nib_median(kartei)
    assert median == pytest.approx(thin["woerter"][0]["nib_units"], rel=1e-6)
    # Every Fassung was written with the same thin pen, so none of them is the
    # odd one out — even though all of them are thin for the 1922 plate.
    index = befund_index(kartei)
    assert [b.grund for b in index["S0001"].values()] == [GRUND_NICHTS, GRUND_NICHTS]
    assert all(b.nib["zur_tafel"] < 0.7 for b in index["S0001"].values())


def test_the_rewrite_list_is_the_not_clean_ones_worst_first() -> None:
    weak = _measure(_paint(_blank(), [(_x0() + 20, _y(42.0)), (_x0() + 110, _y(34.0)), (_x0() + 200, _y(41.0))]))
    clean = _measure(_paint(_blank(), _arc()))
    rows = weakest_fassungen(befund_index(_kartei_with(("F01", weak), ("F02", clean))))
    assert [(strip, fid) for strip, fid, _ in rows] == [("S0001", "F01")]


def test_no_reading_ever_becomes_a_verdict() -> None:
    """Nothing auto-rejects: the Befund never touches a Fassung's status."""
    weak = _measure(_blank())
    kartei = _kartei_with(("F01", weak))
    befund_index(kartei)
    assert kartei["strips"]["S0001"]["fassungen"][0]["status"] == "angenommen"


# --------------------------------------------------------- the moved modules
# Three pure modules moved into `core/` so the Befund could use them across the
# `core` ↛ `tools` boundary. Each move must be a move and not a copy: the tool
# side has to be the SAME object, or the frozen sensor quietly becomes two.


def test_the_word_sensor_reads_the_same_continuity_arithmetic() -> None:
    import core.continuity as core_continuity
    import tools.wordbench.continuity as word_continuity

    assert word_continuity.KINK_THRESHOLD_DEG == core_continuity.KINK_THRESHOLD_DEG == math.degrees(math.asin(0.2))
    assert word_continuity.KINK_WINDOW_UNITS == core_continuity.KINK_WINDOW_UNITS == 0.0725
    assert word_continuity.BOW_CHORD_UNITS == core_continuity.BOW_CHORD_UNITS
    assert word_continuity.LANDMARK_RADIUS_UNITS == core_continuity.LANDMARK_RADIUS_UNITS


def test_routeg_and_the_befund_walk_the_same_skeleton_graph() -> None:
    import core.skeleton_graph as core_graph
    import tools.routeg.graph as routeg_graph

    assert routeg_graph.build_graph is core_graph.build_graph
    assert routeg_graph.Edge is core_graph.Edge
    assert routeg_graph.SkeletonGraph is core_graph.SkeletonGraph


def test_the_plate_pen_the_befund_reads_against_is_the_landmark_one() -> None:
    """One frozen number, not a copy beside the Kringel catalogue's own."""
    import core.eigenhand.befund as befund_module
    import core.landmarks as landmarks
    from tools.tracebench.kringel import PLATE_PEN_HALF_WIDTH_UNITS as tools_pen

    assert befund_module.PLATE_PEN_HALF_WIDTH_UNITS is landmarks.PLATE_PEN_HALF_WIDTH_UNITS
    assert tools_pen is landmarks.PLATE_PEN_HALF_WIDTH_UNITS
    assert landmarks.PLATE_PEN_HALF_WIDTH_UNITS == 0.0968


def test_the_import_and_the_befund_read_the_same_ink() -> None:
    from core.eigenhand.befund import INK_THRESHOLD
    from tools.eigenhand.ingest import INK_THRESHOLD as ingest_threshold

    assert ingest_threshold is INK_THRESHOLD == 0.55


# ------------------------------------------------------- the standing doctrine


def test_the_bestand_still_counts_every_accepted_fassung_as_a_beleg() -> None:
    """Not "the latest accepted one" — the Ausbau-Quote is built on repeats.

    The two-tier Soll (`coverage.target_for_weight`) asks for up to twenty
    Belege of a frequent item, and the print queue ranks repetition candidates
    by weighted Soll gain: a second accepted Fassung of a strip IS a second
    Beleg. Taking one out of the training data stays the author's explicit
    `tools.eigenhand.redo --retire` (status `zurueckgezogen`), never a
    consequence of a Befund. Pinned here because the Befund's own
    `abgeloest_von` reads like a replacement and must not be mistaken for one.
    """
    plan = {"format": 2, "strips": {"S0001": {"words": ["nun"]}}, "forms": {}, "pins": []}
    kartei = _kartei_with(("F01", {}), ("F02", {}))
    counts = bestand_module.ist_counts(kartei, plan)
    assert counts["n>u"] == 2
    assert counts["n@initial"] == 2
    kartei["strips"]["S0001"]["fassungen"][0]["status"] = "zurueckgezogen"
    assert bestand_module.ist_counts(kartei, plan)["n>u"] == 1
