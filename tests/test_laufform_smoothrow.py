"""Unit cover for the evidence floor of the candidate-card builder.

`tools/laufform/smoothrow.py` builds the rows a write path WOULD produce. Since
LF12 (`messjournal.md` §14 `sep04`) it applies the write path's own floor,
`LAUFFORM_MIN_OCCURRENCES`, while it builds: a key whose fresh harvest is
thinner than the floor is not re-derived from too little evidence, and drops
out of the map entirely, so „PUT je Glyph" over the file can never meet a row
the endpoint refuses with a 422. `--keep-stored` puts the copies back for a map
that is meant as a snapshot rather than a write list, and `write_blockers`
answers which of the two a finished map is — against all THREE gates the
endpoint stands on, since a row can clear the floor and still carry a spike.

Pure: hand-built chart/laufform dicts under `tmp_path`, no fixtures, no DB, no
network. The estimator is pinned to the per-anchor median (`knot_spacing=0`) —
this file is about WHICH keys get re-derived, never about the shape that comes
out.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.aggregate import LAUFFORM_MIN_OCCURRENCES
from tools.laufform.smoothrow import build_candidates, occurrences_by_key, write_blockers


CHART_ROW = {
    "glyph_key": "a",
    "glyph": "a",
    "advance": 1.5,
    "entry": {"xy": [0.0, 0.5], "tangent_deg": 38.3, "coupling": "baseline"},
    "exit_pt": {"xy": [1.5, 0.4], "tangent_deg": 45.0, "coupling": "baseline"},
    "anchors": [[0.0, 0.5], [0.7, 1.0], [1.5, 0.4]],
    "half_widths": [0.07, 0.08, 0.07],
    "trace_meta": {"n_anchors": 3, "stroke_starts": [0]},
    "updated_at": None,
}

# What the frozen root holds today: a row visibly apart from the chart row, so
# "kept verbatim" and "re-derived" can never be confused for one another.
STORED = {"anchors": [[9.0, 9.0], [9.0, 9.0], [9.0, 9.0]], "trace_meta": {"laufform": {"n_occurrences": 4}}}


def _root(tmp_path: Path, keys: tuple[str, ...] = ("a", "e")) -> Path:
    root = tmp_path / "root"
    root.mkdir()
    templates = {k: {**CHART_ROW, "glyph_key": k, "glyph": k} for k in keys}
    (root / "templates.json").write_text(json.dumps(templates))
    (root / "templates_laufform.json").write_text(json.dumps(dict.fromkeys(keys, STORED)))
    return root


def _occ(key: str, n: int) -> list[dict]:
    return [
        {"glyph_key": key, "variant": 0, "anchors": [[0.1 * i, 0.5], [0.7, 1.0], [1.5, 0.4]]} for i in range(1, n + 1)
    ]


def test_a_key_under_the_floor_drops_out_of_the_map(tmp_path: Path):
    root = _root(tmp_path)
    occurrences = _occ("a", LAUFFORM_MIN_OCCURRENCES - 1) + _occ("e", LAUFFORM_MIN_OCCURRENCES)

    rows, report = build_candidates(root, occurrences, 0.0)

    # Every row that survives is one `put_laufform` accepts — that is what makes
    # the map safe to walk with a PUT per key.
    assert set(rows) == {"e"}, "a thin key must not be re-derived, and must not be carried either"
    assert rows["e"] != STORED, "a key at the floor is re-derived"
    assert rows["e"]["trace_meta"]["laufform"]["n_occurrences"] == LAUFFORM_MIN_OCCURRENCES
    # The report has to say WHICH reason applies — a gap in the evidence reads
    # differently from a gap in the harvest.
    assert any(f"n={LAUFFORM_MIN_OCCURRENCES - 1} < floor {LAUFFORM_MIN_OCCURRENCES}" in line for line in report)


def test_keep_stored_carries_the_dropped_key_verbatim(tmp_path: Path):
    root = _root(tmp_path)
    occurrences = _occ("a", LAUFFORM_MIN_OCCURRENCES - 1) + _occ("e", LAUFFORM_MIN_OCCURRENCES)

    rows, report = build_candidates(root, occurrences, 0.0, keep_stored=True)

    assert rows["a"] == STORED, "the snapshot mode copies the row an overlay would have used anyway"
    assert any("kept verbatim" in line for line in report)


def test_floor_one_is_the_author_statement_and_re_derives_the_thin_key(tmp_path: Path):
    root = _root(tmp_path)
    occurrences = _occ("a", 1)

    rows, _ = build_candidates(root, occurrences, 0.0, floor=1)

    assert rows["a"] != STORED
    assert rows["a"]["trace_meta"]["laufform"]["n_occurrences"] == 1


def test_a_key_without_fits_drops_out_and_says_so(tmp_path: Path):
    root = _root(tmp_path)

    rows, report = build_candidates(root, _occ("e", 5), 0.0)

    assert set(rows) == {"e"}
    assert any("no usable fits" in line for line in report)


def test_an_unstored_key_under_the_floor_is_left_out_entirely(tmp_path: Path):
    root = _root(tmp_path)
    (root / "templates_laufform.json").write_text(json.dumps({}))

    rows, report = build_candidates(root, _occ("a", 1), 0.0, keys="harvested")

    assert rows == {}, "nothing to keep and not enough to derive — the key stays out of the card"
    assert any("left out of the map" in line for line in report)


def test_write_blockers_names_the_floor_and_the_row_gates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = _root(tmp_path)

    # A row that satisfies the floor can still be refused by a row gate, so the
    # floor alone must never be reported as "writable".
    thin = {"anchors": CHART_ROW["anchors"], "trace_meta": {"laufform": {"n_occurrences": 1}}}
    spiked = {"anchors": CHART_ROW["anchors"], "trace_meta": {"laufform": {"n_occurrences": 9}}}
    monkeypatch.setattr("tools.laufform.smoothrow.spike_gate", lambda *_: {"exceeded": True, "ratio": 3.9, "max": 2.95})
    monkeypatch.setattr(
        "tools.laufform.smoothrow.head_gate", lambda *_: {"exceeded": False, "deviation": 1.0, "max": 15}
    )

    blocked = write_blockers(root, {"a": thin, "e": spiked}, LAUFFORM_MIN_OCCURRENCES)

    assert any(b.startswith("a (") and "floor" in b for b in blocked)
    assert any(b.startswith("e (") and "spike" in b for b in blocked)


def test_write_blockers_is_empty_when_every_gate_is_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = _root(tmp_path)
    row = {"anchors": CHART_ROW["anchors"], "trace_meta": {"laufform": {"n_occurrences": 9}}}
    monkeypatch.setattr(
        "tools.laufform.smoothrow.spike_gate", lambda *_: {"exceeded": False, "ratio": 1.0, "max": 2.95}
    )
    monkeypatch.setattr(
        "tools.laufform.smoothrow.head_gate", lambda *_: {"exceeded": False, "deviation": 1.0, "max": 15}
    )

    assert write_blockers(root, {"a": row}, LAUFFORM_MIN_OCCURRENCES) == []


def test_occurrences_of_a_deviating_anchor_count_are_dropped():
    rows = occurrences_by_key(
        [
            {"glyph_key": "a", "variant": 0, "anchors": [[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]]},
            {"glyph_key": "a", "variant": 0, "anchors": [[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]]},
            {"glyph_key": "a", "variant": 0, "anchors": [[0.0, 0.0], [2.0, 0.0]]},
            {"glyph_key": "a", "variant": 100, "anchors": [[0.0, 0.0], [1.0, 1.0], [2.0, 0.0]]},
        ]
    )

    # A different anchor sampling is a different measurement and cannot be
    # stacked; the Laufform variant is not an occurrence at all.
    assert [len(a) for a in rows["a"]] == [3, 3]


def _loop_chart(n: int = 120, *, phase: float = 0.0, shift: float = 0.0) -> list[list[float]]:
    """A stroke that rises, throws one full loop and leaves — something to register."""
    import math

    out = []
    for i in range(n):
        t = i / (n - 1)
        if t < 1 / 3:
            out.append([0.5 - 0.4 * (1 / 3 - t) * 3, 0.5 - 0.55 * (1 / 3 - t) * 3])
        elif t > 2 / 3:
            out.append([0.5 + 0.4 * (t - 2 / 3) * 3, 0.5 - 0.55 * (t - 2 / 3) * 3])
        else:
            angle = 2.0 * math.pi * (t - 1 / 3) * 3.0 - math.pi / 2.0 + phase
            out.append([0.5 + 0.25 * math.cos(angle), 0.5 + 0.25 * math.sin(angle)])
    return [[x + shift, y] for x, y in out]


def test_the_loop_window_reaches_the_per_anchor_control_arm_too(tmp_path: Path):
    """The registration happens BEFORE the median, so `--knots 0` must feel it.

    Until PR #552 the control arm took the plain median of the RAW stack while
    the run header announced a registered arm — the one combination in which the
    label and the file disagreed.
    """
    chart = {**CHART_ROW, "anchors": _loop_chart(), "half_widths": [0.05] * 120}
    chart["trace_meta"] = {"n_anchors": 120, "stroke_starts": [0]}
    root = tmp_path / "loop-root"
    root.mkdir()
    (root / "templates.json").write_text(json.dumps({"a": chart}))
    (root / "templates_laufform.json").write_text(json.dumps({"a": STORED}))
    occurrences = [
        {"glyph_key": "a", "variant": 0, "anchors": _loop_chart(phase=0.3 * i, shift=0.02 * i)} for i in range(-2, 3)
    ]

    off, _ = build_candidates(root, occurrences, 0.0, loop_window=0.0)
    on, report = build_candidates(root, occurrences, 0.0, loop_window=0.25)

    assert off["a"]["anchors"] != on["a"]["anchors"], "the control arm ignored the registration"
    assert any("registered" in line for line in report)


@pytest.mark.parametrize("floor", [0, -1])
def test_a_floor_below_one_is_refused(tmp_path: Path, floor: int, monkeypatch: pytest.MonkeyPatch):
    from tools.laufform import smoothrow

    occ = tmp_path / "occ.json"
    occ.write_text(json.dumps(_occ("a", 3)))
    monkeypatch.setattr(
        "sys.argv",
        ["smoothrow", "--occurrences", str(occ), "--knots", "0", "--floor", str(floor), "--out", str(tmp_path / "o")],
    )

    with pytest.raises(SystemExit, match="floor must be at least 1"):
        smoothrow.main()
