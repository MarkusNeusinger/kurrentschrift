"""Tests for the structure-landmark layer (`core.landmarks`).

The detectors themselves are pinned where they were measured
(`tests/test_pairlab_landmarks.py`, `tests/test_tracebench_counters.py`,
`tests/test_tracebench_kringel.py`) — those suites keep running against the
moved code through the re-exports, which is the point of the move. What is new
here is the AGGREGATION the Landmarken-Linse reads: that every kind lands with
the handle a complaint names, that the catalogue's verdict travels with the
loop it belongs to, and that a letter the detectors find nothing in says so
instead of showing an empty overlay.
"""

from __future__ import annotations

import numpy as np
import pytest

from core.landmarks import row_landmarks


def _kinds(row, kind: str) -> list:
    return [lm for lm in row.landmarks if lm.kind == kind]


# A lasso: the pen runs right along the baseline, up and back over itself, so
# the closing chord pierces the opening one at (0.5, 0) and encloses a square
# half a unit wide. One crossing, one loop, nothing else.
LASSO = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.5, 1.0], [0.5, -0.5]]


def _dense(points: list[list[float]], step: float = 0.01) -> list[list[float]]:
    """A polyline resampled densely — a rendered centerline, not a corner list.

    The detectors read what the page DRAWS (240 samples per stroke), and the
    raster loop finder rasterises it; a five-point outline would leave the
    aperture measurement reading a staircase.
    """
    pts = np.asarray(points, dtype=float)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    t = np.linspace(0.0, float(arc[-1]), max(2, int(round(float(arc[-1]) / step)) + 1))
    return np.column_stack([np.interp(t, arc, pts[:, 0]), np.interp(t, arc, pts[:, 1])]).tolist()


def _row(centerlines, *, glyph="x", stroke_starts=None, corner_anchors=None, catalogue=None):
    """`row_landmarks` over polylines, with anchors taken from the lines themselves.

    The route feeds render-space anchors and the rendered centerlines of the
    same payload; here one dense polyline plays both parts, which is enough for
    every claim below and keeps the fixtures readable.
    """
    anchors = [p for line in centerlines for p in line]
    return row_landmarks(
        glyph,
        variant=0,
        anchors=anchors,
        half_widths=[0.05] * len(anchors),
        centerlines=centerlines,
        stroke_starts=stroke_starts,
        corner_anchors=corner_anchors,
        catalogue=catalogue,
    )


def test_a_self_crossing_lasso_reports_one_crossing_and_one_loop() -> None:
    row = _row([_dense(LASSO)])

    crossings = _kinds(row, "crossing")
    assert len(crossings) == 1
    assert crossings[0].index == 0
    assert crossings[0].x == pytest.approx(0.5, abs=0.02)
    assert crossings[0].y == pytest.approx(0.0, abs=0.02)
    # One stroke crossing ITSELF — the distinction the overlay names.
    assert crossings[0].numbers["self_crossing"] is True
    assert crossings[0].numbers["stroke_i"] == crossings[0].numbers["stroke_j"] == 0
    assert crossings[0].numbers["angle_deg"] == pytest.approx(90.0, abs=2.0)

    loops = _kinds(row, "loop")
    assert len(loops) == 1
    # The enclosed square is 0.5 wide, so the inscribed diameter is 0.5.
    assert loops[0].numbers["d0"] == pytest.approx(0.5, abs=0.03)
    assert row.loop_ranges  # the raster-free ductus finder sees it too


def test_a_crossing_between_two_pen_strokes_names_both_strokes() -> None:
    stem = _dense([[0.5, -0.5], [0.5, 1.5]])
    bar = _dense([[0.0, 0.5], [1.0, 0.5]])
    row = _row([stem, bar], stroke_starts=[0, len(stem)])

    crossings = _kinds(row, "crossing")
    assert len(crossings) == 1
    assert crossings[0].numbers["self_crossing"] is False
    assert {crossings[0].numbers["stroke_i"], crossings[0].numbers["stroke_j"]} == {0, 1}
    # "Far apart along the path" is meaningless between two separate passes, so
    # the field says nothing rather than inventing a large number.
    assert crossings[0].numbers["arc_separation"] is None


def test_an_out_and_back_is_a_retrace_zone_with_the_path_it_covers() -> None:
    row = _row([_dense([[0.0, 0.0], [0.0, 1.0], [0.02, 0.0]])])

    zones = _kinds(row, "retrace")
    assert len(zones) >= 1
    assert zones[0].index == 0
    assert zones[0].numbers["arc"] > 0.3
    # The overlay shades the path itself, so the points have to travel.
    assert len(zones[0].points) > 2


def test_a_second_stroke_riding_the_first_is_the_merge_indicator() -> None:
    body = _dense([[0.0, 0.0], [0.0, 1.0]])
    mark = _dense([[0.02, 1.0], [0.02, 0.0]])
    row = _row([body, mark], stroke_starts=[0, len(body)])

    assert _kinds(row, "overlap"), "two strokes writing the same ink are an overlap, not a retrace"
    assert not _kinds(row, "retrace")


def test_lifts_are_the_pen_downs_after_the_first_and_corners_come_from_the_trace() -> None:
    first = _dense([[0.0, 0.0], [1.0, 0.0]])
    second = _dense([[2.0, 0.0], [3.0, 0.0]])
    row = _row([first, second], stroke_starts=[0, len(first)], corner_anchors=[3, 3, 7])

    lifts = _kinds(row, "lift")
    assert len(lifts) == 1, "the first pen-down is where the letter begins, not a lift"
    assert lifts[0].numbers["stroke"] == 1
    assert lifts[0].x == pytest.approx(2.0, abs=1e-6)

    corners = _kinds(row, "corner")
    assert [c.numbers["anchor"] for c in corners] == [3, 7], "duplicates collapse, order is the anchor order"


def test_the_catalogue_verdict_travels_with_the_loop_it_belongs_to() -> None:
    catalogue = {
        "d": [
            {
                "glyph": "d",
                "loop": 0,
                "size_class": "mittel",
                "state": "offen",
                "d0_plate": 0.6264,
                "occurrences": 14,
                "with_counter": 14,
            }
        ]
    }
    row = _row([_dense(LASSO)], glyph="d", catalogue=catalogue)

    loop = _kinds(row, "loop")[0]
    assert loop.numbers["state"] == "offen"
    assert loop.numbers["size_class"] == "mittel"
    assert loop.numbers["d0_plate"] == 0.6264
    assert loop.numbers["occurrences"] == 14
    # Matched, so nothing is left over to report as unseen.
    assert row.unmatched_catalogue == ()
    # The loop knows which anchor range the ductus finder gave it.
    assert loop.numbers["anchor_range"] is not None


def test_a_loop_the_catalogue_does_not_know_is_unbekannt_not_a_punktkringel() -> None:
    row = _row([_dense(LASSO)], glyph="d", catalogue={})

    loop = _kinds(row, "loop")[0]
    assert loop.numbers["state"] == "unbekannt"
    # The size class is still measurable without the plate — it is a property of
    # the pen, not of the catalogue.
    assert loop.numbers["size_class"] in ("klein", "mittel", "gross")


def test_a_letter_without_a_detected_loop_reports_the_catalogue_rows_unmatched() -> None:
    """The `t` case: the plate holds counters the detectors find no loop for.

    Showing nothing would claim the letter has no Kringel — so the rows come
    back unmatched and the lens can say „kein Schleifenbereich erkannt".
    """
    rows = [{"glyph": "t", "loop": i, "size_class": "klein", "state": "offen"} for i in range(3)]
    row = _row([_dense([[0.0, 0.0], [1.0, 1.0]])], glyph="t", catalogue={"t": rows})

    assert _kinds(row, "loop") == []
    assert row.loop_ranges == ()
    assert [entry["loop"] for entry in row.unmatched_catalogue] == [0, 1, 2]


def test_the_tools_re_export_the_moved_detectors_rather_than_copies() -> None:
    """The measurement layer and the lens must read the SAME function object.

    A copy would drift on the first threshold change, and the two would then
    disagree about a letter while both claiming to detect crossings.
    """
    from core import landmarks as core_landmarks
    from tools.pairlab import landmarks as pairlab_landmarks
    from tools.tracebench import counters, kringel

    assert pairlab_landmarks.landmark_crossings is core_landmarks.landmark_crossings
    assert pairlab_landmarks.polyline_self_intersections is core_landmarks.polyline_self_intersections
    assert counters.crossing_points is core_landmarks.crossing_points
    assert counters.structure_zones is core_landmarks.structure_zones
    assert counters.classified_pass_points is core_landmarks.classified_pass_points
    assert kringel.loop_apertures is core_landmarks.loop_apertures
    assert kringel.size_class is core_landmarks.size_class
    assert kringel.load_catalogue is core_landmarks.load_catalogue
