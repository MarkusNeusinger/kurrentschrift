"""Unit cover for the word bench's ``--laufform`` overlay (tools/wordbench/run.py).

The flag is the Laufform twin of ``--overrides``: it composes with CANDIDATE
running forms so a Laufform experiment can be measured without re-freezing the
fixtures — and, under the same discipline (qualitaetsmetrik.md §6), its result
is its own number, never the headline. Two properties therefore have to hold
mechanically rather than by care:

* it is an OVERLAY — every key the file does not name keeps its frozen row, so
  the run measures the candidate rather than the absence of the other running
  forms, and an empty overlay is a no-op (the baseline stays byte-identical);
* a draft's anchors become a row through the ONE shared derivation
  (``fetch_fixtures.laufform_row_from_payload`` → ``build_laufform_canonical``),
  never through arithmetic restated here.

Pure: hand-built chart/laufform dicts, no fixtures, no DB, no network.
"""

from __future__ import annotations

import pytest

from tools.wordbench.run import LAUFFORM_OVERLAY_META, build_parser, overlay_laufform_rows


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

TEMPLATES = {"a": CHART_ROW, "e": {**CHART_ROW, "glyph_key": "e", "glyph": "e"}}

# A frozen fixture row: what templates_laufform.json holds today.
FROZEN_A = {**CHART_ROW, "anchors": [[0.02, 0.5], [0.72, 1.0], [1.52, 0.4]]}


def test_a_draft_is_derived_through_the_shared_builder():
    draft = {"a": {"anchors": [[0.1, 0.55], [0.7, 1.0], [1.7, 0.4]], "n_occurrences": 7}}

    rows = overlay_laufform_rows({}, draft, TEMPLATES)

    row = rows["a"]
    # Same fixture-row shape the frozen file carries — the runner renders both
    # through the identical render_payload_for_template path.
    assert set(row) == set(CHART_ROW)
    assert row["anchors"] == draft["a"]["anchors"]
    # Everything but the anchors rides the chart row …
    assert row["half_widths"] == CHART_ROW["half_widths"]
    assert row["trace_meta"]["stroke_starts"] == [0]
    # … and entry/exit/advance follow their end anchors' delta.
    assert row["entry"]["xy"] == pytest.approx([0.1, 0.55])
    assert row["exit_pt"]["xy"] == pytest.approx([1.7, 0.4])
    assert row["advance"] == pytest.approx(1.7)
    # Provenance says this row came from an overlay run, with the draft's own
    # evidence count — the frozen rows carry the apply step's stamp instead.
    assert row["trace_meta"]["laufform"] == {
        **LAUFFORM_OVERLAY_META,
        "n_occurrences": 7,
        # The builder stamps its end-blend window and mode (§14 LF5/LF6; the
        # window is 0 — off — until a rung passes its gates).
        "end_window": 0.0,
        "end_mode": "transverse",
    }


def test_a_full_row_passes_through_verbatim():
    """A file of full rows (anchors + trace_meta) is already derived —
    re-deriving would overwrite its widths with the chart row's."""
    candidate = {**CHART_ROW, "half_widths": [0.2, 0.2, 0.2], "anchors": [[0.0, 0.5], [0.7, 1.1], [1.5, 0.4]]}

    rows = overlay_laufform_rows({}, {"a": candidate}, TEMPLATES)

    assert rows["a"] is candidate
    assert rows["a"]["half_widths"] == [0.2, 0.2, 0.2]


def test_absent_keys_keep_their_frozen_row():
    frozen = {"a": FROZEN_A, "e": {**FROZEN_A, "glyph_key": "e"}}
    draft = {"a": {"anchors": [[0.1, 0.55], [0.7, 1.0], [1.7, 0.4]]}}

    rows = overlay_laufform_rows(frozen, draft, TEMPLATES)

    # Overlay, not replacement: 'e' still composes exactly as the headline does.
    assert rows["e"] is frozen["e"]
    assert rows["a"]["anchors"] == draft["a"]["anchors"]
    # …and the caller's frozen dict is never mutated.
    assert frozen["a"] is FROZEN_A


def test_an_empty_overlay_is_a_no_op():
    # The baseline guarantee at unit scale: without the flag the runner passes
    # an empty payload and must hand the frozen rows straight back.
    frozen = {"a": FROZEN_A}
    assert overlay_laufform_rows(frozen, {}, TEMPLATES) is frozen


def test_a_deviating_anchor_count_is_skipped_by_name(capsys):
    frozen = {"a": FROZEN_A}

    rows = overlay_laufform_rows(frozen, {"a": {"anchors": [[0.0, 0.0]]}}, TEMPLATES)

    # Skipped, not guessed — the same guard the apply endpoint applies before
    # writing, and the frozen row stays in force.
    assert rows["a"] is FROZEN_A
    out = capsys.readouterr().out
    assert "skip laufform a" in out
    assert "1 overlay anchors vs 3" in out


def test_an_empty_draft_entry_is_skipped_by_name(capsys):
    rows = overlay_laufform_rows({}, {"a": {"n_occurrences": 0}}, TEMPLATES)
    assert rows == {}
    assert "skip laufform a" in capsys.readouterr().out


def test_a_key_without_a_chart_row_is_skipped_quietly(capsys):
    # A candidate file usually spans the whole hand while a fixture set only
    # composes part of the alphabet — that is not a defect worth a warning.
    rows = overlay_laufform_rows({}, {"zzz": {"anchors": [[0.0, 0.0]]}}, TEMPLATES)
    assert rows == {}
    assert capsys.readouterr().out == ""


def test_the_flag_parses_as_a_path():
    args = build_parser().parse_args(["--set", "pairs", "--laufform", "draft.json"])
    assert args.laufform.name == "draft.json"
    assert args.no_laufform is False


def test_the_overlay_and_the_chart_only_run_are_mutually_exclusive():
    # One drops the running forms, the other substitutes candidates; a run that
    # did both would report a number nobody could attribute.
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--laufform", "draft.json", "--no-laufform"])


def test_a_malformed_overlay_file_fails_fast_by_name(tmp_path):
    from tools.wordbench.run import load_laufform_payload

    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not json")
    with pytest.raises(SystemExit, match="bad.json"):
        load_laufform_payload(bad_json)

    a_list = tmp_path / "list.json"
    a_list.write_text('[{"glyph_key": "a"}]')
    with pytest.raises(SystemExit, match="object mapping glyph_key"):
        load_laufform_payload(a_list)

    scalar_value = tmp_path / "scalar.json"
    scalar_value.write_text('{"a": 5}')
    with pytest.raises(SystemExit, match="object mapping glyph_key"):
        load_laufform_payload(scalar_value)

    missing = tmp_path / "missing.json"
    with pytest.raises(SystemExit, match="missing.json"):
        load_laufform_payload(missing)
