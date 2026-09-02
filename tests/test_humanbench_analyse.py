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
    ADOPT_CANDIDATE_SHARE,
    ADOPT_MAX_TIE_SHARE,
    DRIFT_BLOCKS,
    MIN_PAIRED_PER_CLASS,
    MIN_PAIRED_REPEATS,
    MIN_POSITIVES,
    ResultFormatError,
    analyse,
    analyse_paired,
    arm_of,
    drift,
    format_paired_report,
    hanley_mcneil_se,
    looks_paired,
    parse_gate,
    parse_paired_result,
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


# ==================================================================== the paired plan
#
# A paired round asks a preference, not a category, and its plan was written
# BEFORE any round existed: reliability first, then the side balance, then the
# pre-registered decision, then the per-class split. What is guarded here is
# that the thresholds cannot drift and that the precondition actually bites —
# a share computed from answers given by position is not a verdict.


def paired_round(answers, *, strata=None, repeats=(), mirrored=True, tag="ECHTHEIT/4"):
    """A paired round written as {uid: (order, choice)}, plus mirrored repeats.

    `repeats` names (repeat_uid, first_uid, choice) triples; their order is the
    reversed order of the first showing, which is what the builder does.
    """
    key, lines = {}, []
    for uid, (order, choice) in answers.items():
        key[uid] = {"uid": uid, "repeat_of": None, "order": list(order), "mirrored": False, "entry": uid, "text": uid}
        if strata:
            key[uid]["stratum"] = strata.get(uid, "-")
        lines.append(f"{uid}:{choice}@5s")
    for uid, first, choice in repeats:
        order = list(reversed(key[first]["order"])) if mirrored else list(key[first]["order"])
        key[uid] = {**key[first], "uid": uid, "repeat_of": first, "order": order, "mirrored": mirrored}
        lines.append(f"{uid}:{choice}@5s")
    text = f"{tag} geprueft={len(lines)} von {len(lines)}\n" + "\n".join(lines) + "\n"
    return parse_paired_result(text), key


BC = ["base", "candidate"]
CB = ["candidate", "base"]
FLIP = {"L": "R", "R": "L", "N": "N"}


def wins(n_candidate, n_base, n_tie=0, *, strata=None, repeats=0, by="arm"):
    """A round in which the candidate wins `n_candidate` of the decided screens.

    Sides alternate so the verdict cannot be read off a side preference — the
    point of drawing them from the seed in the first place. `repeats` mirrored
    repeats are appended, answered either consistently by ARM (`by="arm"`, the
    letters flip because the panels did) or consistently by SIDE (`by="side"`,
    the judge answering by position).
    """
    answers, i = {}, 0
    for count, arm in ((n_candidate, "candidate"), (n_base, "base"), (n_tie, None)):
        for _ in range(count):
            i += 1
            order = BC if i % 2 else CB
            choice = "N" if arm is None else ("L" if order[0] == arm else "R")
            answers[f"S{i:03d}"] = (order, choice)
    uids = list(answers)[: min(repeats, len(answers))]
    pairs = tuple(
        (f"R{n + 1:02d}", uid, FLIP[answers[uid][1]] if by == "arm" else answers[uid][1]) for n, uid in enumerate(uids)
    )
    return paired_round(answers, strata=strata, repeats=pairs)


def test_looks_paired_reads_the_vocabulary_off_the_file():
    """The kind of round is a property of the text, not of a flag somebody has
    to remember months later."""
    assert looks_paired("ECHTHEIT/4 geprueft=1 von 1\nS001:L@4s\n")
    assert not looks_paired(RESULT)
    assert not looks_paired("BEFUND geprueft=0 von 0\n")


def test_parse_paired_result_reads_either_question_s_tally_block():
    parsed = parse_paired_result(
        'ECHTHEIT/4 geprueft=3 von 3\nS001:L\nS002:R@7s\nS003:N "beide gleich"\n'
        "Links echter: 1\nRechts echter: 1\nKein Unterschied: 1\n"
    )
    assert [p.choice for p in parsed.preferences] == ["L", "R", "N"]
    assert parsed.preferences[1].seconds == 7
    assert parsed.preferences[2].note == "beide gleich"
    # The accuracy question's own labels read back just as well.
    assert parse_paired_result("VERGLEICH geprueft=1 von 1\nS001:L\nLinks besser: 1\n").judged == 1


@pytest.mark.parametrize(
    "text, message",
    [
        ("ECHTHEIT geprueft=1 von 1\nS001:G\n", "is not one of"),
        ("ECHTHEIT geprueft=1 von 1\nS001:LR\n", "is not one of"),
        ("ECHTHEIT geprueft=1 von 1\nS001:L#4,5\n", "category round"),
        ("ECHTHEIT geprueft=2 von 2\nS001:L\nS001:R\n", "judged twice"),
        ("ECHTHEIT geprueft=5 von 5\nS001:L\n", "header claims"),
        ("ECHTHEIT geprueft=1 von 1\nS001:L\nLinks echter: 4\n", "counted 4"),
    ],
)
def test_parse_paired_result_rejects_broken_input(text, message):
    with pytest.raises(ResultFormatError, match=message):
        parse_paired_result(text)


def test_arm_of_reads_the_mirrored_order_out_of_the_key():
    """The panel order is the ONLY record of the assignment, and a repeat carries
    its own swapped one — so the same lookup serves both showings."""
    assert arm_of({"order": BC}, "L") == "base"
    assert arm_of({"order": CB}, "L") == "candidate"
    assert arm_of({"order": BC}, "N") is None
    assert arm_of({}, "L") is None


def test_side_reliability_separates_arm_agreement_from_side_agreement():
    """On a mirrored pair the two are almost exclusive: naming the same ARM means
    the letters flipped, naming the same SIDE means they did not."""
    parsed, key = paired_round(
        {"S001": (BC, "L"), "S002": (BC, "R")}, repeats=(("R01", "S001", "R"), ("R02", "S002", "R"))
    )
    rel = analyse_paired(parsed, key)["reliability"]
    assert rel["pairs"] == 2 and rel["mirrored"] == 2
    assert rel["arm_agree"] == 1  # S001 L then R = base twice
    assert rel["side_agree"] == 1  # S002 R then R = two different arms
    assert rel["too_few_pairs"] is True and rel["carries_a_verdict"] is False


def test_the_verdict_uses_the_pre_registered_thresholds():
    parsed, key = wins(40, 10, 5, repeats=8)
    result = analyse_paired(parsed, key)
    ver = result["verdict"]
    assert ver["candidate"] == "candidate"
    assert ver["per_arm"] == {"base": 10, "candidate": 40}
    assert ver["candidate_share"] == pytest.approx(40 / 50)
    assert ver["tie_share"] == pytest.approx(5 / 55)
    assert ver["meets_thresholds"] is True
    assert result["reliability"]["carries_a_verdict"] is True
    assert ver["adopt"] is True
    assert "ADOPT" in format_paired_report(result)


def test_a_candidate_below_the_share_is_not_adopted():
    parsed, key = wins(29, 21, 0, repeats=8)
    ver = analyse_paired(parsed, key)["verdict"]
    assert ver["candidate_share"] == pytest.approx(0.58)  # just under 60 %
    assert ver["meets_thresholds"] is False and ver["adopt"] is False


def test_too_many_ties_block_adoption_even_when_the_candidate_wins():
    """The second condition asks a different question — is the difference
    visible often enough to be worth changing what everybody renders?"""
    parsed, key = wins(30, 5, 20, repeats=8)
    ver = analyse_paired(parsed, key)["verdict"]
    assert ver["candidate_share"] == pytest.approx(30 / 35)  # far past the share
    assert ver["tie_share"] > ADOPT_MAX_TIE_SHARE
    assert ver["adopt"] is False


def test_unreliable_answers_block_adoption_at_any_share():
    """A per-arm share built from answers given by POSITION is a coin toss with
    a percentage sign; the mirrored repeats are what catches that."""
    parsed, key = wins(40, 10, 5, repeats=8, by="side")
    result = analyse_paired(parsed, key)
    assert result["reliability"]["band"] == "coin flip"
    assert result["verdict"]["meets_thresholds"] is True
    assert result["verdict"]["adopt"] is False
    assert "decide nothing" in format_paired_report(result)


def test_too_few_repeats_block_adoption_however_clean_they_are():
    parsed, key = wins(40, 10, 5, repeats=2)
    result = analyse_paired(parsed, key)
    assert result["reliability"]["pairs"] < MIN_PAIRED_REPEATS
    assert result["verdict"]["adopt"] is False


def test_the_class_table_splits_the_verdict_and_names_thin_classes():
    """Pre-registered, not fished for: a candidate that loses overall while
    carrying one class is the normal shape of a result, and partial adoption is
    legitimate — but only if the split existed before the numbers."""
    strata = {f"S{i:03d}": ("naht" if i <= 20 else "breite") for i in range(1, 41)}
    parsed, key = wins(20, 20, 0, strata=strata, repeats=8)
    classes = analyse_paired(parsed, key)["classes"]
    assert set(classes) == {"naht", "breite"}
    assert sum(cell["n"] for cell in classes.values()) == 40
    assert all(cell["too_few"] is False for cell in classes.values())
    thin = analyse_paired(*wins(2, 2, 0, strata={"S001": "naht"}, repeats=8))["classes"]
    assert thin["naht"]["too_few"] is True


def test_repeats_never_enter_the_verdict():
    """They measure the judge, not the arms — counting them would weight a
    dozen words twice."""
    parsed, key = wins(40, 10, 5, repeats=8)
    result = analyse_paired(parsed, key)
    assert result["verdict"]["n"] == 55  # not 63
    assert sum(b["n"] for b in result["drift"]["blocks"]) == 55


def test_side_balance_is_reported_and_never_decisive():
    parsed, key = wins(40, 10, 5, repeats=8)
    sides = analyse_paired(parsed, key)["sides"]
    assert sides["left"] + sides["right"] + sides["tie"] == 55
    assert sides["lopsided"] is False


def test_an_unknown_screen_in_a_paired_result_is_an_error():
    parsed, key = wins(2, 2)
    with pytest.raises(ResultFormatError, match="the key does not know"):
        analyse_paired(parsed, {uid: entry for uid, entry in key.items() if uid != "S001"})


def test_the_paired_thresholds_are_the_pre_registered_ones():
    """Pinned so a later round cannot quietly soften the bar it failed."""
    assert (ADOPT_CANDIDATE_SHARE, ADOPT_MAX_TIE_SHARE) == (0.60, 0.25)
    assert (MIN_PAIRED_REPEATS, MIN_PAIRED_PER_CLASS) == (6, 8)
