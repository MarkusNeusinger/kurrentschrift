"""Unit tests for tools/humanbench/analyse.py.

Everything here is synthetic: the real pass carries per-occurrence geometry and
per-occurrence metrics, which stay out of this repo (quellen-und-rechte.md §5).
The rules under test are the plan's, not the data's — the exclusion of
„komplett daneben", the unset marker that is not a datum, the multi-finding
screen that cannot be attributed, and the reliability number that must not be
read as reliability when the repeats never carried the category.
"""

from __future__ import annotations

import math

import pytest

from tools.humanbench.analyse import (
    DRIFT_BLOCKS,
    MIN_POSITIVES,
    ResultFormatError,
    analyse,
    drift,
    hanley_mcneil_se,
    parse_gate,
    parse_result,
    parse_union,
    roc_auc,
)


# One tiny pass, written out in presentation order. S007 is „komplett daneben"
# with the highest metric value of all, so any step that forgets to exclude it
# changes its number visibly.
RESULT = """BEFUND/2 geprueft=9 von 9
S001:A#40,50@12s
S002:A@8s
S003:WB#20,30@30s "eckiger kringel"
S004:E#10,12@5s
S005:G@4s
R01:A@6s
S006:G@3s
S007:K#60,60@9s
S008:G@2s
"""

KEY = [
    {"uid": "S001", "repeat_of": None, "glyph": "a", "word": "aal"},
    {"uid": "S002", "repeat_of": None, "glyph": "a", "word": "aas"},
    {"uid": "S003", "repeat_of": None, "glyph": "w", "word": "wo"},
    {"uid": "S004", "repeat_of": None, "glyph": "t", "word": "tat"},
    {"uid": "S005", "repeat_of": None, "glyph": "e", "word": "eis"},
    {"uid": "R01", "repeat_of": "S001", "glyph": "a", "word": "aal"},
    {"uid": "S006", "repeat_of": None, "glyph": "e", "word": "ehe"},
    {"uid": "S007", "repeat_of": None, "glyph": "s", "word": "so"},
    {"uid": "S008", "repeat_of": None, "glyph": "n", "word": "nun"},
]

ROWS = [
    {"uid": "S001", "spike": 9.0, "peak": 0.30, "at_edge": False},
    {"uid": "S002", "spike": 2.0, "peak": 0.20, "at_edge": False},
    {"uid": "S003", "spike": 8.5, "peak": 0.25, "at_edge": False},
    {"uid": "S004", "spike": 1.0, "peak": 0.15, "at_edge": True},
    {"uid": "S005", "spike": 1.1, "peak": 0.05, "at_edge": False},
    {"uid": "S006", "spike": 1.2, "peak": 0.04, "at_edge": False},
    {"uid": "S007", "spike": 99.0, "peak": 0.90, "at_edge": True},
    {"uid": "S008", "spike": 1.3, "peak": 0.03, "at_edge": False},
]

SPOTS = [
    {"uid": "S001", "idx": 10, "rel": 0.50, "edge_dist": 9, "argmax_idx": 11},
    {"uid": "S003", "idx": 2, "rel": 0.05, "edge_dist": 2, "argmax_idx": 20},
    {"uid": "S004", "idx": 1, "rel": 0.02, "edge_dist": 1, "argmax_idx": 1},
    {"uid": "S007", "idx": 5, "rel": 0.50, "edge_dist": 5, "argmax_idx": 30},
]


def run(**kwargs):
    parsed = parse_result(RESULT)
    key = {e["uid"]: e for e in KEY}
    rows = {e["uid"]: e for e in ROWS}
    geometry = {e["uid"]: {**rows.get(e["uid"], {}), **e} for e in SPOTS}
    return analyse(parsed, key, rows, geometry, metrics=("spike", "peak"), **kwargs)


# ------------------------------------------------------------------- parsing


def test_parse_result_reads_every_optional_field():
    parsed = parse_result(RESULT)
    assert parsed.tag == "BEFUND/2"
    assert (parsed.judged, parsed.total) == (9, 9)
    first = parsed.verdicts[0]
    assert (first.uid, first.codes, first.spot, first.seconds, first.note) == ("S001", ("A",), (40, 50), 12, None)
    noted = parsed.verdicts[2]
    assert noted.codes == ("W", "B") and noted.note == "eckiger kringel"
    assert parsed.verdicts[1].spot is None  # no marker means no marker, not (0, 0)
    assert parsed.verdicts[4].seconds == 4 and parsed.verdicts[4].codes == ("G",)


def test_parse_result_rejects_a_paired_pass():
    with pytest.raises(ResultFormatError, match="paired-mode"):
        parse_result("VERGLEICH geprueft=1 von 1\nS001:L@4s\n")


def test_parse_result_reads_the_pages_tally_block():
    """The page prints its counts under the verdicts — the natural paste has them."""
    parsed = parse_result("BEFUND geprueft=3 von 3\nS001:A\nS002:G\nS003:WB\nGut: 1\nGewackel: 1\nBereich: 1\n")
    assert [v.codes for v in parsed.verdicts] == [("A",), ("G",), ("W", "B")]
    assert [v.position for v in parsed.verdicts] == [0, 1, 2]


def test_parse_result_catches_a_paste_that_lost_lines():
    """A tally that outruns the verdicts is a truncated clipboard, not a round."""
    with pytest.raises(ResultFormatError, match="counted 4"):
        parse_result("BEFUND geprueft=2 von 2\nS001:G\nS002:G\nGut: 4\n")


@pytest.mark.parametrize(
    "text, message",
    [
        ("S001:A\n", "no header"),
        ("BEFUND geprueft=1 von 1\nS001:X\n", "unknown category"),
        ("BEFUND geprueft=2 von 2\nS001:A\nS001:G\n", "judged twice"),
        ("BEFUND geprueft=5 von 5\nS001:A\n", "header claims"),
        ("BEFUND geprueft=1 von 1\nnonsense\n", "does not parse"),
        ("BEFUND geprueft=2 von 2\nS001:G\nGut: 1\nS002:G\n", "behind the tally block"),
        ("BEFUND geprueft=1 von 1\nS001:G\nGut: 1\nGut: 1\n", "given twice"),
    ],
)
def test_parse_result_rejects_broken_input(text, message):
    with pytest.raises(ResultFormatError, match=message):
        parse_result(text)


def test_parse_gate_reads_metric_operator_and_target():
    assert parse_gate("spike>=8.0:A") == ("spike", ">=", 8.0, "A")
    assert parse_gate("cov<=0.02") == ("cov", "<=", 0.02, None)
    with pytest.raises(ValueError, match="not <metric>"):
        parse_gate("spike 8")


# ------------------------------------------------------------------- statistics


def test_roc_auc_splits_ties_down_the_middle():
    assert roc_auc([1.0, 2.0], [0.0, 1.0]) == pytest.approx(0.875)
    assert roc_auc([1.0], [1.0]) == pytest.approx(0.5)
    assert roc_auc([], [1.0]) is None


def test_hanley_mcneil_se_matches_the_closed_form_and_shrinks_with_n():
    assert hanley_mcneil_se(0.8, 2, 2) == pytest.approx(0.25386, abs=1e-5)
    assert hanley_mcneil_se(0.8, 22, 123) == pytest.approx(0.05892, abs=1e-5)
    assert hanley_mcneil_se(0.8, 220, 1230) < hanley_mcneil_se(0.8, 22, 123)
    assert not math.isnan(hanley_mcneil_se(1.0, 5, 5))


# ------------------------------------------------------------------- the steps


def test_reliability_says_when_the_repeats_never_carried_a_category():
    rel = run()["reliability"]
    assert rel["pairs"] == 1 and rel["exact"] == 1
    assert rel["per_category"]["A"] == {
        "agree": 1,
        "pairs": 1,
        "rate": 1.0,
        "yes": 1,
        "no": 0,
        "disagree": 0,
        "carried": 1,
        "band": "reliable",
        "too_few_positives": True,  # one positive pair proves nothing about A
    }
    # A perfect agreement built entirely on the negatives is flagged as such.
    assert rel["per_category"]["E"]["agree"] == 1
    assert rel["per_category"]["E"]["carried"] == 0
    assert rel["per_category"]["E"]["too_few_positives"] is True


def test_occupancy_counts_the_pass_without_the_repeats():
    occ = run()["occupancy"]
    assert occ["total"] == 8  # nine screens, one of them a blind repeat
    assert occ["per_category"]["A"]["n"] == 2
    assert occ["per_category"]["G"]["n"] == 3
    assert occ["per_category"]["K"]["n"] == 1
    assert all(cell["too_few"] for cell in occ["per_category"].values())  # nothing reaches MIN_POSITIVES here
    assert occ["flagged"] == 5  # two A, one WB, one E, one K
    assert occ["good_with_finding"] == 0
    assert occ["verdict_sizes"] == {1: 7, 2: 1}
    assert occ["marker_on_flagged"] == 4
    assert occ["overlap"]["W&B"] == {"both": 1, "union": 1, "share": 1.0}


def test_occupancy_threshold_is_the_pre_registered_one():
    assert MIN_POSITIVES == 8


def test_gate_excludes_the_unratable_screen():
    gate = run()["gate"]
    assert gate["evaluated"] == 7  # S007 (K) is not a case the gate may be graded on
    assert gate["rejected"] == 2  # S001 and S003; S007's 99.0 never enters
    assert gate["targets"]["A"]["precision"] == pytest.approx(0.5)
    assert gate["targets"]["A"]["recall"] == pytest.approx(0.5)
    assert gate["targets"]["A"]["missed_values"] == [2.0]
    assert gate["targets"]["any finding"]["precision"] == pytest.approx(1.0)


def test_coverage_matrix_excludes_the_unratable_screen_and_names_thin_categories():
    cov = run()["coverage"]
    assert cov["evaluated"] == 7
    assert cov["columns"] == ["any"]  # no finding reaches MIN_POSITIVES in this toy pass
    assert cov["too_few"] == ["A", "W", "B", "E"]
    assert cov["metrics"]["spike"]["any"]["n_pos"] == 4
    assert cov["metrics"]["spike"]["any"]["n_neg"] == 3
    # Three of the four findings outrank every „gut" screen, the fourth ranks below all of them.
    assert cov["metrics"]["spike"]["any"]["auc"] == pytest.approx(0.75)
    assert cov["metrics"]["peak"]["any"]["auc"] == pytest.approx(1.0)
    assert cov["missing_metrics"] == []


def test_coverage_reports_boolean_row_fields_as_two_rates():
    cov = run()["coverage"]
    # at_edge is set on S004 (a finding) and on S007 (K, excluded from both sides).
    assert cov["flags"]["at_edge"]["any"] == {"set": 1, "n_pos": 4, "set_elsewhere": 0, "n_neg": 3}


# --------------------------------------------- the union fallback (plan step 6)


def synthetic_pass(rows: list[tuple[str, str, float]]):
    """A pass written as (uid, codes, metric value) triples.

    The tiny fixture above cannot carry this step: a union only earns a column
    once it clears `MIN_POSITIVES`, which needs more screens than nine.
    """
    text = f"BEFUND/9 geprueft={len(rows)} von {len(rows)}\n" + "".join(f"{uid}:{codes}@5s\n" for uid, codes, _ in rows)
    key = {uid: {"uid": uid, "repeat_of": None, "glyph": "e", "word": "wenn"} for uid, _, _ in rows}
    metrics = {uid: {"uid": uid, "m": value} for uid, _, value in rows}
    return parse_result(text), key, metrics


# Five W and five B — neither reaches MIN_POSITIVES on its own, together they do.
# The metric ranks every finding above every „gut", so the union's AUC is 1.0.
SPLIT = [(f"S{i:03d}", "W" if i % 2 else "B", 0.5 + i) for i in range(1, 11)]
SPLIT += [(f"S{i:03d}", "G", 0.0) for i in range(11, 25)]


def test_two_categories_too_thin_alone_can_be_scored_as_their_union():
    """The plan's fallback: confusability costs resolution, it does not destroy
    the statement."""
    parsed, key, rows = synthetic_pass(SPLIT)
    cov = analyse(parsed, key, rows, {}, metrics=("m",), unions=(("W", "B"),))["coverage"]
    assert "W∪B" in cov["columns"]
    assert cov["too_few"] == ["A", "W", "B", "E"]  # the members stay named as too thin
    assert cov["metrics"]["m"]["W∪B"]["n_pos"] == 10
    assert cov["metrics"]["m"]["W∪B"]["n_neg"] == 14
    assert cov["metrics"]["m"]["W∪B"]["auc"] == pytest.approx(1.0)


def test_a_screen_carrying_both_categories_counts_once_in_their_union():
    parsed, key, rows = synthetic_pass([*SPLIT, ("S025", "WB", 9.0)])
    cov = analyse(parsed, key, rows, {}, metrics=("m",), unions=(("W", "B"),))["coverage"]
    assert cov["metrics"]["m"]["W∪B"]["n_pos"] == 11  # 10 + the one screen, not 12


def test_a_union_that_stays_too_thin_gets_no_column_either():
    thin = [("S001", "W", 1.0), ("S002", "B", 2.0), *[(f"S{i:03d}", "G", 0.0) for i in range(3, 12)]]
    parsed, key, rows = synthetic_pass(thin)
    cov = analyse(parsed, key, rows, {}, metrics=("m",), unions=(("W", "B"),))["coverage"]
    assert cov["columns"] == ["any"]
    assert "W∪B" in cov["too_few"]


def test_without_a_union_the_pre_registered_matrix_is_unchanged():
    """The fallback is asked for, never default — a plan step that quietly
    reshaped the default matrix would be a different analysis."""
    parsed, key, rows = synthetic_pass(SPLIT)
    plain = analyse(parsed, key, rows, {}, metrics=("m",))["coverage"]
    assert plain["columns"] == ["any"] and "W∪B" not in plain["too_few"]


@pytest.mark.parametrize(
    "spec, message",
    [("W", "at least two"), ("W,Z", "not a finding category"), ("W,W", "twice"), ("G,W", "not a finding category")],
)
def test_parse_union_refuses_what_would_not_mean_anything(spec, message):
    with pytest.raises(ValueError, match=message):
        parse_union(spec)


def test_parse_union_normalises_the_spec():
    assert parse_union(" w , b ") == ("W", "B")


def test_place_check_ignores_unmarked_screens_and_multi_finding_ones():
    place = run()["place"]
    assert place["marked"] == 4 and place["usable"] == 4
    assert place["without_geometry"] == []
    # S002 carries A but no marker: it must not appear in A's row, and must not
    # count as „nothing wrong there" anywhere.
    assert place["per_category"]["A"]["n"] == 1
    # S003 carries W and B with a single point, so it is out of both rows.
    assert place["per_category"]["W"]["n"] == 0
    assert place["per_category"]["B"]["n"] == 0
    assert place["single_finding"] == 2
    assert place["per_category"]["E"] == {"n": 1, "head": 1, "middle": 0, "tail": 0, "at_boundary": 1, "too_few": True}
    # The overall question still counts every click, multi-finding and K alike.
    assert place["argmax_hits"] == 2
    assert place["at_boundary"] == 2


def test_place_check_reports_markers_it_has_no_geometry_for():
    parsed = parse_result(RESULT)
    key = {e["uid"]: e for e in KEY}
    rows = {e["uid"]: e for e in ROWS}
    result = analyse(parsed, key, rows, {}, metrics=("spike",))
    assert result["place"]["marked"] == 4
    assert result["place"]["usable"] == 0
    assert sorted(result["place"]["without_geometry"]) == ["S001", "S003", "S004", "S007"]


def test_drift_splits_the_shown_sequence_evenly():
    parsed = parse_result(RESULT)
    key = {e["uid"]: e for e in KEY}
    blocks = drift(parsed.verdicts, key, blocks=2)["blocks"]
    assert [b["range"] for b in blocks] == [[0, 4], [4, 8]]
    assert [b["n"] for b in blocks] == [4, 4]
    assert blocks[0]["categories"]["A"] == 2  # the repeat R01 is not in the sequence
    assert blocks[0]["marked"] == 3 and blocks[1]["marked"] == 1
    assert blocks[0]["median_seconds"] == pytest.approx(10.0)
    assert blocks[1]["timed"] == 4


def test_default_drift_block_count_is_the_reported_one():
    assert DRIFT_BLOCKS == 3
    blocks = run()["drift"]["blocks"]
    assert sum(b["n"] for b in blocks) == 8


def test_notes_carry_their_screen_and_verdict():
    assert run()["notes"] == [{"uid": "S003", "glyph": "w", "word": "wo", "codes": "WB", "note": "eckiger kringel"}]


def test_unknown_screen_in_the_result_is_an_error():
    parsed = parse_result(RESULT)
    key = {e["uid"]: e for e in KEY if e["uid"] != "S008"}
    with pytest.raises(ResultFormatError, match="the key does not know"):
        analyse(parsed, key, {e["uid"]: e for e in ROWS}, {})


def test_drop_unsure_removes_those_verdicts_from_every_step():
    text = RESULT.replace("S002:A@8s", "S002:AU@8s")
    parsed = parse_result(text)
    key = {e["uid"]: e for e in KEY}
    rows = {e["uid"]: e for e in ROWS}
    with_unsure = analyse(parsed, key, rows, {}, metrics=("spike",))
    without = analyse(parsed, key, rows, {}, metrics=("spike",), drop_unsure=True)
    assert with_unsure["occupancy"]["per_category"]["A"]["n"] == 2
    assert without["occupancy"]["per_category"]["A"]["n"] == 1
    assert without["pass"]["dropped_unsure"] == ["S002"]
