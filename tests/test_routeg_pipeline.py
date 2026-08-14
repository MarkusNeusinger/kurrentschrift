"""Unit tests for the route-G control (tools/routeg).

No network, no venv, no fixture root: the skeletons are drawn here by hand, so
the graph and the traversal are asserted against shapes whose right answer is
obvious by eye. What is pinned is exactly where a wrong answer would hide —
the node merge at a crossing, the good-continuation choice, the leftmost start,
the lift on a dead end, every edge walked once — plus the frame conversion and
the candidate contract the bench reads.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from tools.routeg.graph import build_graph, neighbour_counts
from tools.routeg.prepare import dev_ids, load_ink_mask, load_skeleton, prepare_entry, to_image
from tools.routeg.recover import DIRECTION_WINDOW, lead_direction, recover_strokes, tail_direction, traverse
from tools.routeg.to_candidate import (
    CANDIDATE_FRAME,
    MAX_STROKE_POINTS,
    MAX_WORD_STROKES,
    build_row,
    derive_set_labels,
    registration_of,
    strokes_to_word_units,
    validate_strokes,
)


def _skeleton(rows: list[str]) -> np.ndarray:
    """A skeleton drawn as text: `#` is ink, anything else is background."""
    return np.array([[char == "#" for char in row] for row in rows], dtype=bool)


# --------------------------------------------------------------------------- graph


def test_neighbour_counts_are_eight_connected() -> None:
    skel = _skeleton(["###", "..#"])
    counts = neighbour_counts(skel)
    assert counts[0, 1] == 3  # both horizontal neighbours plus the diagonal below
    assert counts[0, 0] == 1
    assert counts[1, 2] == 2


def test_plain_line_is_two_nodes_and_one_edge() -> None:
    graph = build_graph(_skeleton(["#####"]))
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert {edge.a, edge.b} == {0, 1}
    # The edge carries both node representatives, so its points span the line.
    assert len(edge.points) == 5
    assert edge.points[:, 0].min() == 0.0
    assert edge.points[:, 0].max() == 4.0


def test_fork_has_one_branch_node_and_three_leaves() -> None:
    graph = build_graph(_skeleton(["#...#", ".#.#.", "..#..", "..#..", "..#.."]))
    degrees = sorted(len(edges) for edges in graph.incident.values())
    assert degrees == [1, 1, 1, 3]
    assert len(graph.edges) == 3


def test_adjacent_branch_pixels_merge_into_one_node() -> None:
    """An X thins into TWO adjacent 3-neighbour pixels — that is one crossing.

    Without the merge the crossing would appear as two branch points joined by a
    one-pixel stub, and the traversal would spend its good-continuation decision
    on that stub instead of on the crossing.
    """
    skel = _skeleton(["#....#", ".#..#.", "..##..", ".#..#.", "#....#"])
    counts = neighbour_counts(skel)
    assert int(((counts >= 3) & skel).sum()) == 2  # the crossing really is multi-pixel
    graph = build_graph(skel)
    branch_nodes = [node for node, edges in graph.incident.items() if len(edges) >= 3]
    assert len(branch_nodes) == 1
    assert len(graph.incident[branch_nodes[0]]) == 4
    assert len(graph.edges) == 4


def test_a_one_pixel_stub_off_a_branch_point_is_swallowed() -> None:
    """An end pixel ADJACENT to a branch pixel merges into that node.

    Documented rather than fixed: a stub that short is a thinning artefact (the
    reference implementation calls those false trace points and removes them),
    and the alternative — a node-to-node edge with no pixel of its own — would
    hand the traversal a decision about nothing. The cost is that a genuine
    two-pixel stroke would be lost, which is priced by the bench's AIoU column.
    """
    skel = _skeleton(["#...#", ".#.#.", "..#..", "..#.."])
    graph = build_graph(skel)
    # The stem's own end pixel touches the fork, so the two collapse: three
    # arms of the drawing, but only two edges.
    assert len(graph.edges) == 2


def test_bare_ring_gets_a_synthetic_node_and_a_self_loop() -> None:
    graph = build_graph(_skeleton([".###.", "#...#", "#...#", "#...#", ".###."]))
    assert len(graph.nodes) == 1
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert edge.a == edge.b
    # The ring closes on its own start, and does so WITHOUT a zero-length first
    # step: the synthetic node IS the chain's first pixel, so it must not be
    # prepended a second time.
    assert edge.points[0] == pytest.approx(edge.points[-1])
    assert edge.points[0] != pytest.approx(edge.points[1])
    assert len(edge.points) == int(_skeleton([".###.", "#...#", "#...#", "#...#", ".###."]).sum()) + 1


def test_isolated_pixel_is_counted_and_yields_no_stroke() -> None:
    runs, meta = recover_strokes(_skeleton(["#####", ".....", "#...."]))
    assert meta["isolated_pixels"] == 1
    assert meta["strokes"] == 1


# --------------------------------------------------------------------------- directions


def test_lead_and_tail_directions_are_unit_and_oriented() -> None:
    points = np.array([[float(i), 0.0] for i in range(10)])
    assert lead_direction(points) == pytest.approx([1.0, 0.0])
    assert tail_direction(points) == pytest.approx([1.0, 0.0])
    assert lead_direction(points[::-1]) == pytest.approx([-1.0, 0.0])


def test_direction_window_is_bounded_by_the_polyline() -> None:
    short = np.array([[0.0, 0.0], [1.0, 0.0]])
    assert len(short) - 1 < DIRECTION_WINDOW
    assert lead_direction(short) == pytest.approx([1.0, 0.0])
    assert lead_direction(np.array([[0.0, 0.0]])) == pytest.approx([0.0, 0.0])


# --------------------------------------------------------------------------- traversal


def test_crossing_is_resolved_by_good_continuation() -> None:
    """Entering an X from the top left, the pen must leave at the bottom right.

    The other two branches are the competing choice, and picking one of them is
    precisely the failure the good-continuation rule exists to avoid.
    """
    skel = _skeleton(
        [
            "#.........#",
            ".#.......#.",
            "..#.....#..",
            "...#...#...",
            "....#.#....",
            ".....#.....",
            "....#.#....",
            "...#...#...",
            "..#.....#..",
            ".#.......#.",
            "#.........#",
        ]
    )
    runs = traverse(build_graph(skel))
    assert len(runs) == 2
    first = runs[0]
    # Started top left (the leftmost endpoint, and the upper of the two).
    assert first[0] == pytest.approx([0.0, 0.0])
    # ...and came out bottom right rather than turning back up the other arm.
    assert first[-1] == pytest.approx([10.0, 10.0])


def test_every_edge_is_walked_exactly_once() -> None:
    skel = _skeleton(["#....#", ".#..#.", "..##..", ".#..#.", "#....#"])
    graph = build_graph(skel)
    runs = traverse(graph)
    walked = sum(len(run) for run in runs)
    # Every edge contributes its points once; the shared node points are deduped
    # only where two edges meet inside one run, so the walked total is at least
    # the skeleton and at most the sum of the edge polylines.
    assert walked >= int(skel.sum())
    assert walked <= sum(len(edge.points) for edge in graph.edges)


def test_disjoint_components_are_written_left_to_right_as_separate_runs() -> None:
    skel = _skeleton(["###...###"])
    runs = traverse(build_graph(skel))
    assert len(runs) == 2
    assert runs[0][0][0] < runs[1][0][0]


def test_a_dead_end_lifts_the_pen_rather_than_teleporting() -> None:
    """A fork with a stem: the pen continues straight, then LIFTS for the rest.

    The left arm and the stem are one continuous run because they continue each
    other; the right arm is a second run, because reaching it would need a jump
    and a jump is a pen lift.
    """
    skel = _skeleton(["#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."])
    runs = traverse(build_graph(skel))
    assert len(runs) == 2
    assert all(len(run) >= 2 for run in runs)
    assert runs[0][0] == pytest.approx([0.0, 0.0])  # leftmost endpoint
    assert runs[0][-1] == pytest.approx([2.0, 5.0])  # straight on down the stem
    assert runs[1][0] == pytest.approx([4.0, 0.0])  # the right arm is its own run


def test_recover_strokes_reports_what_it_saw() -> None:
    skel = _skeleton(["#####", "..#..", "..#.."])
    runs, meta = recover_strokes(skel)
    assert meta["skeleton_px"] == int(skel.sum())
    assert meta["strokes"] == len(runs)
    assert meta["points"] == sum(len(run) for run in runs)
    assert meta["components"] == 1


def test_traversal_is_deterministic() -> None:
    skel = _skeleton(["#.....#", ".#...#.", "..###..", ".#...#.", "#.....#"])
    first, _ = recover_strokes(skel)
    second, _ = recover_strokes(skel)
    assert [run.tolist() for run in first] == [run.tolist() for run in second]


# --------------------------------------------------------------------------- prepare


def test_to_image_polarity_is_explicit() -> None:
    mask = _skeleton(["#.", ".."])
    black = np.asarray(to_image(mask, "black"))
    white = np.asarray(to_image(mask, "white"))
    assert black[0, 0] == 0 and black[0, 1] == 255
    assert white[0, 0] == 255 and white[0, 1] == 0
    with pytest.raises(ValueError, match="ink must be"):
        to_image(mask, "grey")


def test_dev_ids_match_the_bench_split() -> None:
    from tools.tracebench.sets import TRACEBENCH_DEV_IDS

    assert set(dev_ids()) == set(TRACEBENCH_DEV_IDS)


def _write_entry(root, entry_id: str, skel: np.ndarray) -> None:
    entry = root / entry_id
    entry.mkdir(parents=True)
    to_image(skel, "white").save(entry / "ref_mask.png")
    np.savez_compressed(entry / "ref_skel.npz", skel=skel, width_map=skel.astype(np.float32))
    entry.joinpath("word.json").write_text(
        json.dumps(
            {
                "id": entry_id,
                "word": entry_id,
                "kind": "word",
                "rect": [10, 20, 10 + skel.shape[1], 20 + skel.shape[0]],
                "baseline_y": 60.0,
                "midband_y": 40.0,
            }
        ),
        encoding="utf-8",
    )


def test_prepare_entry_roundtrips_the_frozen_bits(tmp_path) -> None:
    skel = _skeleton(["#####", "..#..", "..#.."])
    _write_entry(tmp_path, "wort", skel)
    record = prepare_entry(tmp_path, "wort", tmp_path / "inputs", "black")
    assert record["crop_w"] == skel.shape[1]
    assert record["crop_h"] == skel.shape[0]
    assert record["skeleton_px"] == int(skel.sum())
    assert np.array_equal(load_skeleton(tmp_path / "wort"), skel)
    assert np.array_equal(load_ink_mask(tmp_path / "wort"), skel)
    written = np.asarray(to_image(skel, "black"))
    assert set(np.unique(written).tolist()) == {0, 255}


# --------------------------------------------------------------------------- candidate


def test_registration_is_the_crop_frame() -> None:
    registration, xh = registration_of({"id": "x", "rect": [10, 20, 40, 60], "baseline_y": 55.0, "midband_y": 35.0})
    assert registration == {"tx": 0, "ty": 0, "baseline_row": 35.0}
    assert xh == 20.0
    with pytest.raises(ValueError, match="non-positive x-height"):
        registration_of({"id": "x", "rect": [0, 0, 1, 1], "baseline_y": 10.0, "midband_y": 10.0})


def test_crop_pixels_land_on_the_baseline_and_the_midband() -> None:
    registration, xh = registration_of({"id": "x", "rect": [0, 20, 40, 60], "baseline_y": 55.0, "midband_y": 35.0})
    # baseline_row is 35 crop px; the midband sits one x-height above it.
    strokes = strokes_to_word_units([[[0.0, 35.0], [0.0, 15.0]]], registration, xh)
    assert strokes[0][0] == pytest.approx([0.0, 0.0])
    assert strokes[0][1] == pytest.approx([0.0, 1.0])


def test_validate_strokes_enforces_the_wire_contract() -> None:
    assert validate_strokes([[[0.0, 0.0], [1.0, 1.0]]]) is None
    assert validate_strokes([]) == "no strokes recovered"
    assert "points" in (validate_strokes([[[0.0, 0.0]]]) or "")
    assert "coordinate range" in (validate_strokes([[[0.0, 0.0], [1000.0, 0.0]]]) or "")
    too_many = [[[0.0, 0.0], [1.0, 1.0]] for _ in range(MAX_WORD_STROKES + 1)]
    assert "wire cap" in (validate_strokes(too_many) or "")
    too_long = [[[float(i), 0.0] for i in range(MAX_STROKE_POINTS + 1)]]
    assert "points" in (validate_strokes(too_long) or "")


def test_build_row_produces_the_bench_shape() -> None:
    word_json = {"id": "die", "rect": [0, 20, 40, 60], "baseline_y": 55.0, "midband_y": 35.0}
    raw = {"id": "die", "word": "die", "strokes_px": [[[0.0, 35.0], [10.0, 15.0]]], "meta": {"nodes": 4}}
    row = build_row(raw, {"kind": "word", "word": "die"}, word_json)
    assert row["status"] == "ok"
    assert row["kind"] == "word"
    assert row["xh_px"] == 20.0
    assert row["registration_px"]["baseline_row"] == 35.0
    assert row["meta"]["nodes"] == 4


def test_a_failed_recovery_travels_as_a_failed_row() -> None:
    word_json = {"id": "die", "rect": [0, 20, 40, 60], "baseline_y": 55.0, "midband_y": 35.0}
    row = build_row({"id": "die", "word": "die", "error": "boom"}, {}, word_json)
    assert row["status"] == "failed"
    assert row["strokes"] == []
    assert row["meta"]["detail"] == "boom"


def test_a_wire_violation_keeps_the_geometry_and_fails_the_row() -> None:
    word_json = {"id": "die", "rect": [0, 20, 40, 60], "baseline_y": 55.0, "midband_y": 35.0}
    raw = {"id": "die", "word": "die", "strokes_px": [[[0.0, 35.0]]]}
    row = build_row(raw, {}, word_json)
    assert row["status"] == "failed"
    assert row["strokes"] and len(row["strokes"][0]) == 1
    assert "points" in row["meta"]["detail"]


def test_candidate_frame_matches_what_the_bench_demands() -> None:
    from tools.tracebench.candidates import CANDIDATE_FRAME as BENCH_FRAME
    from tools.tracebench.candidates import MAX_STROKE_POINTS as BENCH_MAX_POINTS
    from tools.tracebench.candidates import MAX_WORD_STROKES as BENCH_MAX_STROKES

    assert CANDIDATE_FRAME == BENCH_FRAME
    assert MAX_WORD_STROKES == BENCH_MAX_STROKES
    assert MAX_STROKE_POINTS == BENCH_MAX_POINTS


def test_derive_set_labels_reads_the_fixture_root() -> None:
    from pathlib import Path

    assert derive_set_labels(Path("x/suetterlin/suetterlin-1922")) == ("suetterlin", "suetterlin-1922", "words")
    assert derive_set_labels(Path("x/suetterlin/suetterlin-1922-pairs")) == ("suetterlin", "suetterlin-1922", "pairs")
    assert derive_set_labels(Path("x/suetterlin/suetterlin-1922-abb22")) == ("suetterlin", "suetterlin-1922", "abb22")
