"""Unit cover for the evidence floor of the candidate-card builder.

`tools/laufform/smoothrow.py` builds the rows a write path WOULD produce. Since
LF12 (`messjournal.md` §14 `sep04`) it applies the write path's own floor,
`LAUFFORM_MIN_OCCURRENCES`, while it builds: a key whose fresh harvest is
thinner than the floor is not re-derived from too little evidence, and drops
out of the map entirely, so „PUT je Glyph" over the file can never meet a row
the endpoint refuses with a 422. `--keep-stored` puts the copies back for a map
that is meant as a snapshot rather than a write list.

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
from tools.laufform.smoothrow import build_candidates, occurrences_by_key


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
