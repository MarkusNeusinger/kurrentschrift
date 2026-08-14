"""Tests for the duel viewer (`tools.tracebench.view`).

The page is a drawing, so the things that can silently go wrong are geometric
and structural rather than numeric: ink placed by the viewer's own arithmetic
instead of the bench's, a colour that moves between rounds, a layer that is not
in the file at all — and, the one failure nobody would notice while it works,
an outbound request that turns a self-contained artifact into a page that needs
the network.

Everything runs on a hand-built fixture root in `tmp_path`: one word, one crop,
one authored reference row, one candidate file. No DB, no API, no fixtures on
disk.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from tools.tracebench.frames import BenchFrame
from tools.tracebench.view import (
    COLOR_CHAIN,
    COLOR_FOLLOWER,
    PALETTE,
    REFERENCE_LABEL,
    assign_colors,
    build_parser,
    main,
    mark_flags,
    parse_pairs,
    select_ids,
    stroke_path_data,
    trace_paths,
)


XH_PX = 20.0
BASELINE_ROW = 30.0
RECT = [10, 5, 70, 45]  # x0, y0, x1, y1 — the crop is 60x40 page pixels
REGISTRATION = {"tx": 0.0, "ty": 0.0, "baseline_row": BASELINE_ROW}

BODY = [[0.2, 0.5], [1.0, 0.5], [1.6, 0.2]]
MARK = [[0.7, 1.4], [0.75, 1.42]]  # short and floating: a delayed mark


# ------------------------------------------------------------------ geometry


def test_path_data_is_the_benchs_own_crop_pixels() -> None:
    """The overlay travels trace -> bench -> crop px, never its own arithmetic."""
    frame = BenchFrame(xh=XH_PX, baseline_row=BASELINE_ROW, entry_id="die")
    stroke = [[1.0, 0.5], [2.0, 0.0]]

    paths = trace_paths(frame, [stroke], REGISTRATION, XH_PX)

    # Hand-computed: x = u * xh, y = baseline_row - v * xh.
    assert paths[0].d == "M 20.00,20.00 L 40.00,30.00"
    # …and identical to the round trip the scorer makes.
    expected = frame.bench_to_crop_px(frame.trace_to_bench([stroke], REGISTRATION, XH_PX)[0])
    assert paths[0].d == stroke_path_data(expected)
    assert paths[0].length == pytest.approx(float(np.hypot(20.0, 10.0)))


def test_marks_are_flagged_by_the_classifier_not_by_the_viewer() -> None:
    """A floating short stroke is a mark; the first stroke never is."""
    frame = BenchFrame(xh=XH_PX, baseline_row=BASELINE_ROW, entry_id="die")
    bench = frame.trace_to_bench([BODY, MARK], REGISTRATION, XH_PX)

    assert mark_flags(bench) == [False, True]
    # A repeated geometry must not shift the walk onto the leading stroke.
    assert mark_flags(frame.trace_to_bench([MARK, MARK], REGISTRATION, XH_PX)) == [False, True]

    paths = trace_paths(frame, [BODY, MARK], REGISTRATION, XH_PX)
    assert [p.mark for p in paths] == [False, True]


# -------------------------------------------------------------------- colours


def test_candidate_colors_are_stable_and_deterministic() -> None:
    labels = ["chain", "follow-v1", "inksight-t0", "route-g"]

    first = assign_colors(labels)
    assert first == assign_colors(labels)  # same input, same colours
    assert first["chain"] == COLOR_CHAIN
    assert first["follow-v1"] == COLOR_FOLLOWER
    # Everything else takes the fixed palette in order — never a random colour.
    assert [first["inksight-t0"], first["route-g"]] == [PALETTE[0], PALETTE[1]]
    # Order of the two pinned labels does not move them.
    assert assign_colors(["follow-v1", "chain"])["chain"] == COLOR_CHAIN


def test_parse_pairs_refuses_the_ambiguous_forms() -> None:
    assert parse_pairs(["chain=a.json"], flag="--candidate") == [("chain", Path("a.json"))]
    for bad in (["chain"], ["=a.json"], ["chain="], [f"{REFERENCE_LABEL}=a.json"]):
        with pytest.raises(SystemExit):
            parse_pairs(bad, flag="--candidate")
    with pytest.raises(SystemExit):
        parse_pairs(["chain=a.json", "chain=b.json"], flag="--candidate")


# ---------------------------------------------------------------- the page


def _fixture_root(tmp_path: Path, *, strokes: list | None = None) -> Path:
    """A minimal frozen fixture root: manifest, one entry, crop, authored row."""
    root = tmp_path / "suetterlin" / "sample-source"
    entry_dir = root / "die"
    entry_dir.mkdir(parents=True, exist_ok=True)
    root.joinpath("manifest.json").write_text(json.dumps({"set": "words", "words": [{"id": "die", "word": "die"}]}))
    entry_dir.joinpath("word.json").write_text(
        json.dumps(
            {
                "id": "die",
                "word": "die",
                "kind": "word",
                "rect": RECT,
                "baseline_y": RECT[1] + BASELINE_ROW,
                "midband_y": RECT[1] + BASELINE_ROW - XH_PX,
                "slots": [{"key": "d"}, {"key": "i"}, {"key": "e"}],
            }
        )
    )
    crop = np.full((RECT[3] - RECT[1], RECT[2] - RECT[0]), 220, dtype=np.uint8)
    Image.fromarray(crop, mode="L").save(entry_dir / "crop.png")
    root.joinpath("word_instances.json").write_text(
        json.dumps(
            {
                "hand_id": "hand-x",
                "rows": [
                    {
                        "specimen_id": "die",
                        "kind": "word",
                        "word": "die",
                        "slots": ["d", "i", "e"],
                        "provenance": "authored",
                        "strokes": strokes or [BODY, MARK],
                        "measurements": {"registration_px": REGISTRATION, "xh_px": XH_PX},
                    }
                ],
            }
        )
    )
    return root


def _candidate_file(tmp_path: Path) -> Path:
    path = tmp_path / "chain.json"
    path.write_text(
        json.dumps(
            {
                "frame": "word_registration",
                "label": "chain",
                "rows": [
                    {
                        "specimen_id": "die",
                        "strokes": [[[0.25, 0.55], [1.05, 0.55], [1.65, 0.25]]],
                        "measurements": {"registration_px": REGISTRATION, "xh_px": XH_PX},
                    }
                ],
            }
        )
    )
    return path


def _report_file(tmp_path: Path) -> Path:
    path = tmp_path / "chain.report.json"
    path.write_text(
        json.dumps(
            {
                "candidate": "chain",
                "rows": [
                    {
                        "id": "die",
                        "status": "ok",
                        "dtw_xh": 0.0623,
                        "aiou": 0.412,
                        "cross_matched": 2,
                        "cross_spurious": 1,
                        "retrace_arc_ratio": 1.51,
                    }
                ],
            }
        )
    )
    return path


def _build(tmp_path: Path, out: Path) -> str:
    root = _fixture_root(tmp_path)
    assert (
        main(
            [
                "--fixtures",
                str(root.parent.parent),
                "--split",
                "all",
                "--candidate",
                f"chain={_candidate_file(tmp_path)}",
                "--rows",
                f"chain={_report_file(tmp_path)}",
                "--title",
                "arm1-prox01 · 2026-08-14",
                "--out",
                str(out),
            ]
        )
        == 0
    )
    return out.read_text(encoding="utf-8")


def test_page_carries_both_layers_and_stays_self_contained(tmp_path: Path) -> None:
    page = _build(tmp_path, tmp_path / "out" / "duell.html")

    # The word, the hand reference and the candidate are all in the artifact…
    assert 'data-id="die"' in page
    assert f'data-label="{REFERENCE_LABEL}"' in page
    assert 'data-label="chain"' in page
    assert page.count('<g class="layer"') == 2
    # …the animation is dash-driven per stroke (animation-rendering.md §1)…
    assert 'stroke-dasharray="1"' in page
    assert 'pathLength="1"' in page
    assert "data-len=" in page
    # …the crop rides along as a data: URI…
    assert "data:image/png;base64," in page
    # …the numbers of the attached report are shown…
    assert "0.0623" in page
    assert "1.51" in page
    # …and nothing on the page reaches for the network.
    assert "http://" not in page
    assert "https://" not in page


def test_page_bytes_are_deterministic(tmp_path: Path) -> None:
    """Same inputs, same bytes — otherwise a chronik entry cannot be diffed."""
    first = _build(tmp_path, tmp_path / "a.html")
    second = _build(tmp_path, tmp_path / "b.html")
    assert first == second


def test_layer_order_follows_the_arguments_not_a_set(tmp_path: Path) -> None:
    """Set iteration order is hash-seeded — it must not reach the page.

    Two processes with different `PYTHONHASHSEED` are the only way to see that
    class of bug at all: within one interpreter a set iterates consistently, so
    an in-process comparison would call a non-deterministic page deterministic.
    """
    root = _fixture_root(tmp_path)
    candidate = _candidate_file(tmp_path)
    pages = []
    for seed in ("0", "1"):
        out = tmp_path / f"seed-{seed}.html"
        done = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.tracebench.view",
                "--fixtures",
                str(root.parent.parent),
                "--split",
                "all",
                *[
                    arg
                    for label in ("chain", "follow-v1", "inksight-t0")
                    for arg in ("--candidate", f"{label}={candidate}")
                ],
                "--out",
                str(out),
            ],
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, "PYTHONHASHSEED": seed},
            capture_output=True,
            text=True,
            check=False,
        )
        assert done.returncode == 0, done.stderr
        pages.append(out.read_text(encoding="utf-8"))

    assert pages[0] == pages[1]
    assert f"Verfahren: {REFERENCE_LABEL}, chain, follow-v1, inksight-t0" in pages[0]


def test_a_failed_candidate_is_a_layer_with_a_reason(tmp_path: Path) -> None:
    """A candidate the file does not cover must not take the word off the page."""
    root = _fixture_root(tmp_path)
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"frame": "word_registration", "rows": []}))
    out = tmp_path / "duell.html"

    main(["--fixtures", str(root.parent.parent), "--split", "all", "--candidate", f"chain={empty}", "--out", str(out)])

    page = out.read_text(encoding="utf-8")
    assert 'data-label="chain"' in page
    assert "not in empty.json" in page
    assert 'data-id="die"' in page


def test_select_ids_uses_the_frozen_split_and_words_override_it(tmp_path: Path) -> None:
    from tools.tracebench.reference import load_reference

    reference = load_reference(_fixture_root(tmp_path))
    assert select_ids(reference, "dev", None) == ["die"]  # "die" is a frozen dev id
    assert select_ids(reference, "confirm", None) == []
    assert select_ids(reference, "dev", "nothing") == []
    assert select_ids(reference, "confirm", "die") == ["die"]  # --words overrides the split


def test_cli_defaults_do_not_read_a_clock() -> None:
    """The stamp is injected; the builder itself has no wall-clock input."""
    args = build_parser().parse_args([])
    assert args.title == ""
    assert args.split == "dev"
