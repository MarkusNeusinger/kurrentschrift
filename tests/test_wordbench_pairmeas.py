"""Unit tests for the "gemessen vs. komponiert" report columns
(tools/wordbench/pairmeas.py, handmodell H2).

Pure functions, no DB and no fixtures: synthetic joins whose distances are
computable by hand, so a numpy or resampling change cannot silently redefine
what the column means. The columns are report-only — the point of pinning them
is that they stay a MONOTONE, comparable signal across bench runs.

Two of these tests exist because a review found the first version measuring a
frame artifact: ``doff`` compared the composer's COUPLING anchors against an
offset harvested from the two letters' BODY endpoints. The cases below
therefore give every join coupling anchors that disagree with its bodies — if
the implementation ever reads them again, the hand-computed numbers break.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.shaping import GlyphSlot
from tools.wordbench.export_fixtures import pair_instances_payload
from tools.wordbench.pairmeas import compare_joins, load_measured, rows_for_entry


def _slots(*keys: str) -> list[GlyphSlot]:
    return [GlyphSlot(key=k, text=k, position=None, ligature=False, space=False) for k in keys]


def _glyph(slot_index: int, key: str, centerline: list, diacritic: bool = False) -> dict:
    item = {"centerline": centerline, "slot_index": slot_index, "glyph_key": key}
    if diacritic:
        item["diacritic"] = True
    return item


def _join(from_slot: int, to_slot: int, pair: list, centerline: list, **extra) -> dict:
    """A composed connector. The coupling anchors are deliberately WRONG for
    the bodies of every test word — ``doff`` must not read them."""
    return {
        "centerline": centerline,
        "stroke_width": 0.1,
        "pair": pair,
        "from_slot": from_slot,
        "to_slot": to_slot,
        "exit": [99.0, 9.0],
        "entry": [99.9, 9.0],
        **extra,
    }


def _row(slot: int, left: str, right: str, offset: list, connector: list, fit_ok: bool = True) -> dict:
    return {
        "left_key": left,
        "right_key": right,
        "kind": "word",
        "specimen_id": "wenn",
        "slot": slot,
        "geometry": {"offset": offset, "connector": connector},
        "measurements": {"fit_ok": fit_ok, "gen_chamfer": 0.02},
    }


# ------------------------------------------------------------------- distances


def test_horizontal_join_offset_and_connector_distances_are_hand_computable():
    """Body Δx 1.4 − 0.9 = 0.5 vs measured offset x 0.4 → doff = 0.1.

    The join's coupling anchors would give Δx = 0.9 (and doff 0.5): the frame
    is the BODY endpoints, exactly the one the harvest measured in.

    Both connectors are straight horizontal lines, so the arc-length
    resampling puts sample i of 24 at 0.5·i/23 resp. 0.4·i/23 once each curve
    is shifted onto its own start — the pointwise distance grows linearly to
    0.1 and its mean is 0.05.
    """
    composed = {
        "items": [
            _glyph(0, "n", [[0.0, 0.0], [0.9, 0.0]]),
            _join(0, 1, ["n", "e"], [[1.0, 0.0], [1.25, 0.0], [1.5, 0.0]]),
            _glyph(1, "e", [[1.4, 0.0], [2.0, 0.0]]),
        ]
    }
    measured = [_row(0, "n", "e", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]])]
    out = compare_joins(composed, _slots("n", "e"), measured)
    assert (out["n_joins"], out["n_matched"]) == (1, 1)
    assert out["doff_mean"] == 0.1
    assert out["dconn_mean"] == 0.05
    assert out["joins"][0]["pair"] == ["n", "e"]
    assert (out["excluded_fit"], out["excluded_override"]) == (0, 0)


def test_the_measured_offsets_y_component_is_ignored():
    """`offset[1]` is by construction the composed body Δy at harvest time
    (harvest.py cancels the relative vertical fit shift), so it carries no
    specimen information — comparing it would measure the composer against
    itself. Same word as above, absurd measured y: doff must not move."""
    composed = {
        "items": [
            _glyph(0, "n", [[0.0, 0.0], [0.9, 0.0]]),
            _join(0, 1, ["n", "e"], [[1.0, 0.0], [1.5, 0.0]]),
            _glyph(1, "e", [[1.4, 0.7], [2.0, 0.7]]),
        ]
    }
    measured = [_row(0, "n", "e", [0.4, -5.0], [[0.0, 0.0], [0.4, 0.0]])]
    out = compare_joins(composed, _slots("n", "e"), measured)
    assert out["doff_mean"] == 0.1


def test_the_body_frame_is_the_last_and_first_non_diacritic_stroke():
    """A multi-stroke glyph (u's two downstrokes) exits on its LAST body
    stroke, and the next glyph enters on its FIRST — its diacritic (i-dot,
    emitted out of writing order because the composer defers marks) must never
    stand in for that entry. Δx = 1.5 − 1.1 = 0.4, measured 0.25 → doff 0.15."""
    composed = {
        "items": [
            _glyph(0, "u", [[0.0, 0.0], [0.5, 0.0]]),
            _glyph(0, "u", [[0.6, 0.0], [1.1, 0.0]]),
            _join(0, 1, ["u", "i"], [[1.1, 0.0], [1.5, 0.0]]),
            _glyph(1, "i", [[0.9, 1.4], [1.2, 1.4]], diacritic=True),
            _glyph(1, "i", [[1.5, 0.0], [1.8, 0.0]]),
            _glyph(1, "i", [[1.9, 0.0], [2.1, 0.0]]),
        ]
    }
    measured = [_row(0, "u", "i", [0.25, 0.0], [[0.0, 0.0], [0.4, 0.0]])]
    out = compare_joins(composed, _slots("u", "i"), measured)
    assert out["n_matched"] == 1
    assert out["doff_mean"] == 0.15


def test_the_shape_distance_is_arc_length_based_and_translation_free():
    """A connector that turns back down, sampled DIFFERENTLY on both sides and
    sitting somewhere else entirely.

    Geometrically the SAME polyline — the measured one just carries a
    collinear extra vertex per segment, and the composed one is translated by
    [2, 1] (an emitted centerline starts wherever the overlap extension put
    it). Arc-length resampling lines the two up and the start alignment
    removes the translation: dconn = 0. An index-parameterised comparison
    would spread 3 and 5 vertices over the 24 samples differently and report a
    phantom deviation; a non-aligned one would report the translation.
    The bodies place the entry 0.3 to the right of the exit, measured 0.1 —
    doff = 0.2, and placement lives THERE, not in dconn.
    """
    shape = [[0.0, 0.0], [0.1, 0.4], [0.4, 0.0]]
    dense = [[0.0, 0.0], [0.05, 0.2], [0.1, 0.4], [0.25, 0.2], [0.4, 0.0]]
    composed = {
        "items": [
            _glyph(0, "n", [[0.4, 0.0], [1.0, 0.0]]),
            _join(0, 1, ["n", "e"], [[2.0 + x, 1.0 + y] for x, y in shape]),
            _glyph(1, "e", [[1.3, 0.0], [1.9, 0.0]]),
        ]
    }
    measured = [_row(0, "n", "e", [0.1, 0.0], dense)]
    out = compare_joins(composed, _slots("n", "e"), measured)
    assert out["n_matched"] == 1
    assert out["dconn_mean"] == 0.0
    assert out["doff_mean"] == pytest.approx(0.2, abs=5e-4)


# ------------------------------------------------------------------- matching


def test_the_endstrich_and_glyph_strokes_are_not_joins():
    """Only a connector with a right glyph is a join: the word-final Endstrich
    (pair[1] is None) and the letter bodies never count."""
    composed = {
        "items": [
            _glyph(0, "n", [[0.0, 0.0], [0.9, 0.0]]),
            {"centerline": [[1.0, 0.0], [1.4, 0.2]], "pair": ["n", None], "from_slot": 0, "to_slot": None},
        ]
    }
    out = compare_joins(composed, _slots("n"), [])
    assert (out["n_joins"], out["n_matched"], out["doff_mean"]) == (0, 0, None)


def test_a_letter_pair_mismatch_counts_unmatched_instead_of_comparing():
    """The slot index alone is not identity — if the frozen slots moved under
    the harvest, the row describes a DIFFERENT transition and is dropped."""
    composed = {
        "items": [
            _glyph(0, "n", [[0.0, 0.0], [0.9, 0.0]]),
            _join(0, 1, ["n", "e"], [[1.0, 0.0], [1.5, 0.0]]),
            _glyph(1, "e", [[1.4, 0.0], [2.0, 0.0]]),
        ]
    }
    measured = [_row(0, "u", "e", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]])]
    out = compare_joins(composed, _slots("n", "e"), measured)
    assert (out["n_joins"], out["n_matched"]) == (1, 0)
    assert out["doff_mean"] is None and out["dconn_mean"] is None


def test_a_join_without_a_measured_row_is_reported_not_dropped():
    """Specimen coverage is partial by design (a flagged dissection was never
    stored) — the denominator must still show the join."""
    composed = {
        "items": [
            _glyph(0, "n", [[0.0, 0.0], [0.9, 0.0]]),
            _join(0, 1, ["n", "e"], [[1.0, 0.0], [1.5, 0.0]]),
            _glyph(1, "e", [[1.4, 0.0], [2.0, 0.0]]),
        ]
    }
    out = compare_joins(composed, _slots("n", "e"), [])
    assert (out["n_joins"], out["n_matched"]) == (1, 0)


def test_a_degenerate_measured_connector_is_skipped_without_crashing():
    composed = {
        "items": [
            _glyph(0, "n", [[0.0, 0.0], [0.9, 0.0]]),
            _join(0, 1, ["n", "e"], [[1.0, 0.0], [1.5, 0.0]]),
            _glyph(1, "e", [[1.4, 0.0], [2.0, 0.0]]),
        ]
    }
    measured = [_row(0, "n", "e", [0.4, 0.0], [[0.0, 0.0]])]
    out = compare_joins(composed, _slots("n", "e"), measured)
    assert (out["n_joins"], out["n_matched"]) == (1, 0)


def test_a_composed_run_without_provenance_bodies_matches_nothing():
    """Without provenance the glyph items carry no ``slot_index``, so there is
    no body frame to measure the placement in — the comparison stays silent
    rather than falling back to the coupling anchors."""
    composed = {
        "items": [
            {"centerline": [[0.0, 0.0], [0.9, 0.0]]},
            _join(0, 1, ["n", "e"], [[1.0, 0.0], [1.5, 0.0]]),
            {"centerline": [[1.4, 0.0], [2.0, 0.0]]},
        ]
    }
    out = compare_joins(composed, _slots("n", "e"), [_row(0, "n", "e", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]])])
    assert (out["n_joins"], out["n_matched"]) == (1, 0)


# ------------------------------------------------------------------ exclusions


@pytest.mark.parametrize("measurements", [{"fit_ok": False, "gen_chamfer": 0.02}, {}])
def test_a_dissection_the_harvest_distrusts_is_excluded_and_counted(measurements: dict):
    """The harvest stores every dissection, clean or not; its own QC flag is
    the gate (11 of 199 word rows on the 1922 plates fail it). A median must
    not rest on those — and a MISSING flag is not an approval either, exactly
    as in core.aggregate.aggregate_pair_instances."""
    composed = {
        "items": [
            _glyph(0, "n", [[0.0, 0.0], [0.9, 0.0]]),
            _join(0, 1, ["n", "e"], [[1.0, 0.0], [1.5, 0.0]]),
            _glyph(1, "e", [[1.4, 0.0], [2.0, 0.0]]),
        ]
    }
    row = _row(0, "n", "e", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]]) | {"measurements": measurements}
    out = compare_joins(composed, _slots("n", "e"), [row])
    assert (out["n_joins"], out["n_matched"], out["excluded_fit"]) == (1, 0, 1)
    assert out["doff_mean"] is None


def test_an_override_rendered_join_is_excluded_and_counted():
    """An APPROVED override IS a harvested centerline — against its own source
    specimen it would report ~0 by construction and dilute the median. Same
    doctrine as 'an override run is its own number, never the headline'."""
    composed = {
        "items": [
            _glyph(0, "n", [[0.0, 0.0], [0.9, 0.0]]),
            _join(0, 1, ["n", "e"], [[1.0, 0.0], [1.5, 0.0]], override=True),
            _glyph(1, "e", [[1.4, 0.0], [2.0, 0.0]]),
        ]
    }
    measured = [_row(0, "n", "e", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]])]
    out = compare_joins(composed, _slots("n", "e"), measured)
    assert (out["n_joins"], out["n_matched"]) == (1, 0)
    assert (out["excluded_override"], out["excluded_fit"]) == (1, 0)
    assert out["doff_mean"] is None


# ------------------------------------------------------------------- artifact


def test_a_fixture_set_without_the_artifact_reports_nothing(tmp_path: Path):
    """An older fixture export has no pair_instances.json — the column is then
    absent entirely, never a row of zeros pretending to be a measurement."""
    assert load_measured(tmp_path) is None
    assert rows_for_entry(None, "word", "wenn") == []


@pytest.mark.parametrize("content", ["{not json", "[1, 2, 3]"])
def test_a_corrupt_artifact_warns_and_behaves_like_an_absent_one(tmp_path: Path, capsys, content: str):
    """A report artifact must never be able to take a scoring run down: a
    truncated or wrongly-shaped file costs the meas columns and one warning
    line, nothing else."""
    (tmp_path / "pair_instances.json").write_text(content)
    assert load_measured(tmp_path) is None
    assert "warning" in capsys.readouterr().out


def test_rows_are_selected_by_kind_and_specimen(tmp_path: Path):
    artifact = {
        "hand_id": "suetterlin-1922-norm",
        "rows": [
            _row(0, "n", "e", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]]),
            _row(1, "e", "n", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]]) | {"specimen_id": "unter"},
            _row(0, "b", "i", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]]) | {"kind": "pair", "specimen_id": "wenn"},
        ],
    }
    (tmp_path / "pair_instances.json").write_text(json.dumps(artifact))
    loaded = load_measured(tmp_path)
    assert loaded == artifact
    rows = rows_for_entry(loaded, "word", "wenn")
    assert [(r["left_key"], r["right_key"]) for r in rows] == [("n", "e")]


def test_the_export_payload_stays_lean_and_scoped_to_its_set():
    """The frozen artifact carries only what the columns read: a custom set
    (abb22 — a DIFFERENT writer) shares the 'word' kind with the default set,
    so the specimen ids decide, and the QC travels trimmed to the two flags."""
    rows = [
        _row(0, "n", "e", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]]) | {"hand_id": "norm"},
        _row(1, "e", "n", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]]) | {"hand_id": "norm", "specimen_id": "a22-Wind"},
        _row(0, "b", "i", [0.4, 0.0], [[0.0, 0.0], [0.4, 0.0]]) | {"hand_id": "norm", "kind": "pair"},
    ]
    rows[0]["measurements"] = {"fit_ok": True, "gen_chamfer": 0.02, "a_resid": 0.03, "trace_converged": True}
    payload = pair_instances_payload(rows, {"word"}, {"wenn"})
    assert payload["hand_id"] == "norm"
    assert [(r["specimen_id"], r["slot"]) for r in payload["rows"]] == [("wenn", 0)]
    assert payload["rows"][0]["measurements"] == {"fit_ok": True, "gen_chamfer": 0.02}
