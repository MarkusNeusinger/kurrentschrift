"""The calibration instrument for the Tintentreue bounds: the rule, not the round.

The round itself cannot run here and never will: it needs 30 real word boxes,
which live only in the shared database and the gitignored local store, and it
needs the author judging them blind. What IS testable is everything the round
stands on, and that is what this module pins:

* the DRAW (`TestDraw`) — stratified across the three provisional steps, the
  tail held back, the repeats spread over the steps rather than over the words;
* the BLINDNESS (`TestBlindness`) — nothing about a box in the payload, and the
  crop held against its own box rectangle so a Bahn is never drawn offset;
* the PARSER (`TestParser`) — the page's own format, with this round's
  vocabulary and a refusal for a fit verdict pasted into it;
* the PLAN (`TestPlan`) — the pre-registered evaluation in its binding order:
  reliability first, occupancy, the light against the human, and the quantile
  cut with its rounding direction and its refusals.

Everything is synthetic. A real crop is the author's own handwriting and the
reserved dataset (`docs/reference/quellen-und-rechte.md` §5), so the PNGs here
are a 1x1 pixel and the „Bahnen" are two-point lines.
"""

from __future__ import annotations

import base64
import json
import random
from pathlib import Path

import pytest

from api.schemas import EigenhandPfad, EigenhandStripBoxOut
from core.eigenhand.tintentreue import (
    SENSOR_ABSETZER,
    SENSOR_AIOU,
    SENSOR_EXKURSION,
    SENSOR_SPRUENGE,
    SENSOR_UNBESUCHT,
    STUFEN,
    VORLAEUFIG,
)
from tools.eigenhand import tintentreue_calibration as tool
from tools.eigenhand.tintentreue_calibration import (
    FAILS,
    FOLLOWS,
    MIN_PER_STEP,
    PARTLY,
    UNRATABLE,
    Box,
    against_the_light,
    bound_of,
    boxes_of_hand,
    cuts,
    dead_branches,
    drawing_of,
    insert_repeats,
    item_of,
    jumps_proposal,
    key_entry,
    occupancy,
    panel_strokes,
    parse_result,
    pen_lift_cut,
    pick_repeats,
    png_size,
    rank_value,
    reliability,
    result_tag,
    stratify,
)
from tools.humanbench.analyse import ResultFormatError


# A 1x1 PNG — nothing here judges pixels, only the wrapper around them.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def box(index: int, step: str, **readings: float) -> Box:
    """One synthetic word box with the readings a cut is drawn from."""
    return Box(
        strip=f"S{index // 4 + 1:04d}",
        fassung="F01",
        box_index=index % 4,
        word="lesen",
        step=step,
        sensor=None,
        readings={
            SENSOR_UNBESUCHT: readings.get("unbesucht"),
            SENSOR_EXKURSION: readings.get("exkursion"),
            SENSOR_AIOU: readings.get("aiou"),
            SENSOR_ABSETZER: readings.get("absetzer"),
            SENSOR_SPRUENGE: readings.get("spruenge"),
        },
        absetzer_soll=readings.get("soll"),
    )


def population(per_step: dict[str, int]) -> list[Box]:
    rows: list[Box] = []
    for step, count in per_step.items():
        rows += [box(len(rows) + n, step) for n in range(count)]
    return rows


def result_text(lines: list[str], round_label: int = 1) -> str:
    """The page's own result file — headed with the round it came out of."""
    return f"TINTENTREUE/{round_label} geprueft={len(lines)} von {len(lines)}\n" + "\n".join(lines) + "\n"


# ------------------------------------------------------------------- the draw


class TestDraw:
    def test_the_sample_is_dealt_across_the_three_steps(self):
        """A hand in good shape is nearly all green boxes, and the bound being
        looked for lives where the cases are thin — so a prefix of the sequence
        has to span the steps rather than the strips."""
        rows = population({STUFEN[0]: 20, STUFEN[1]: 6, STUFEN[2]: 4})
        label, reserve = stratify(rows, 9, random.Random(1))
        assert len(label) == 9 and len(reserve) == 21
        assert {row.step for row in label[:6]} == set(STUFEN)

    def test_the_position_of_a_screen_does_not_name_its_step(self):
        """Dealt strictly in band order, screen 1 would be green, screen 2
        yellow, screen 3 red and round again — the position would name the very
        label gates (A) and (C) hold the judge against. So each round of the
        deal is shuffled before it is appended: every prefix stays step-balanced
        to within one box and the rhythm is gone."""
        rows = population({STUFEN[0]: 30, STUFEN[1]: 30, STUFEN[2]: 30})
        label, _ = stratify(rows, 90, random.Random(7))
        by_position = [{row.step for index, row in enumerate(label) if index % 3 == offset} for offset in range(3)]
        assert all(len(steps) > 1 for steps in by_position)

    def test_the_tail_is_the_reserve_and_nothing_is_lost(self):
        rows = population({STUFEN[0]: 5, STUFEN[1]: 5, STUFEN[2]: 5})
        label, reserve = stratify(rows, 6, random.Random(2))
        assert len(label) + len(reserve) == len(rows)
        assert {row.identity for row in label}.isdisjoint({row.identity for row in reserve})

    def test_the_draw_is_reproducible_from_the_seed(self):
        rows = population({STUFEN[0]: 8, STUFEN[1]: 8, STUFEN[2]: 8})
        first, _ = stratify(list(rows), 10, random.Random(20260921))
        second, _ = stratify(list(rows), 10, random.Random(20260921))
        assert [row.identity for row in first] == [row.identity for row in second]

    def test_repeats_are_spread_over_the_steps_not_over_the_words(self):
        """The lesson under §3.2: a reliability figure that comes only from
        agreement about the green boxes says nothing about the bound."""
        rows = population({STUFEN[0]: 12, STUFEN[1]: 6, STUFEN[2]: 6})
        label, _ = stratify(rows, 24, random.Random(3))
        picks = pick_repeats(label, 6, 8, random.Random(3))
        assert len(picks) == 6
        assert {pick.step for pick in picks} == set(STUFEN)

    def test_a_repeat_is_never_drawn_from_the_tail_it_could_not_follow(self):
        rows = population({STUFEN[0]: 4, STUFEN[1]: 4, STUFEN[2]: 4})
        label, _ = stratify(rows, 12, random.Random(4))
        picks = pick_repeats(label, 4, 8, random.Random(4))
        tail = {row.identity for row in label[-8:]}
        assert all(pick.identity not in tail for pick in picks)

    def test_the_realised_gap_is_measured_on_the_finished_sequence(self):
        """A later repeat spliced in between two showings pushes them apart, so
        the distance at insertion time is not the one the judge walks."""
        rows = population({STUFEN[0]: 10, STUFEN[1]: 10, STUFEN[2]: 10})
        label, _ = stratify(rows, 30, random.Random(5))
        items, key = [], []
        for index, row in enumerate(label):
            row.uid = f"S{index + 1:03d}"
            items.append({"id": row.uid})
            key.append(key_entry(row, row.uid))
        picks = pick_repeats(label, 8, 8, random.Random(5))
        gaps = insert_repeats(items, key, picks, lambda uid, _row: {"id": uid}, min_gap=8, rng=random.Random(5))
        assert len(gaps) == len(picks)
        assert all(gap >= 8 for gap in gaps)
        assert [entry["uid"] for entry in key] == [item["id"] for item in items]

    def test_only_measured_boxes_reach_the_population(self, monkeypatch):
        """A grey box carries no reading, so there is nothing on it to
        calibrate — and showing one would spend a screen that cannot move a
        bound."""
        answer = {
            "hand": "mn-suetterlin",
            "fassungen": [
                {
                    "strip": "S0001",
                    "fassung": "F01",
                    "kaesten": [
                        {
                            "box_index": 0,
                            "word": "lesen",
                            "absetzer_soll": 2,
                            "tintentreue": {
                                "gemessen": True,
                                "stufe": STUFEN[0],
                                "sensor": None,
                                "sensoren": [{"name": SENSOR_UNBESUCHT, "wert": 0.02}],
                            },
                        },
                        {
                            "box_index": 1,
                            "word": "das",
                            "tintentreue": {"gemessen": False, "stufe": "nicht beurteilt", "sensoren": []},
                        },
                    ],
                }
            ],
        }
        monkeypatch.setattr(tool, "request_json", lambda *a, **k: answer)
        rows = boxes_of_hand("http://127.0.0.1:1", "t", "mn-suetterlin")
        assert [row.box_index for row in rows] == [0]
        assert rows[0].readings[SENSOR_UNBESUCHT] == 0.02
        assert rows[0].absetzer_soll == 2


# -------------------------------------------------------------- the blindness


class TestBlindness:
    def test_the_payload_carries_nothing_but_the_crop_and_the_bahn(self):
        """Strip, Fassung, word, readings and above all the step the light
        would have given the box stay in the key (§3.8). A judge who opens the
        page source finds a picture and a polyline."""
        drawing = tool.Drawing(width=40, height=20, png=PNG, strokes=[[[0.0, 0.0], [10.0, 5.0]]])
        item = item_of("S001", drawing)
        assert set(item) == {"id", "w", "h", "img", "strokes"}
        serialised = json.dumps(item)
        assert "S0001" not in serialised and STUFEN[0] not in serialised

    def test_the_bahn_lands_in_the_crop_s_own_frame(self):
        """`px = (u·xh + tx, baseline + ty − v·xh)` is the STRIP's frame; the
        crop's is that minus the box rectangle."""
        entry = {
            "strokes": [[[0.0, 0.0], [1.0, 1.0]]],
            "registration_px": {"tx": 100.0, "ty": 0.0, "baseline_row": 60.0},
            "xh_px": 20.0,
        }
        strokes = panel_strokes(entry, [80, 0, 200, 90])
        assert strokes == [[[20.0, 60.0], [40.0, 40.0]]]

    def test_every_pen_run_stays_its_own_polyline(self):
        """Bridged, the page would show a stroke the hand never made — and the
        „Absetzer falsch" mark would get its positives from the renderer."""
        entry = {
            "strokes": [[[0.0, 0.0], [1.0, 0.0]], [[2.0, 0.0], [3.0, 0.0]]],
            "registration_px": {"tx": 0.0, "baseline_row": 0.0},
            "xh_px": 10.0,
        }
        assert len(panel_strokes(entry, [0, 0, 100, 50])) == 2

    def test_a_crop_that_does_not_match_its_rectangle_is_refused(self, monkeypatch):
        """The crop comes from one route and the rectangle from another. If
        they ever disagree, every Bahn on the page is offset by the difference —
        invisibly, because a misplaced line looks like a wrong one."""
        monkeypatch.setattr(tool, "fetch_crop", lambda *a, **k: PNG)  # 1x1
        paths = {
            "pfade": [
                {
                    "box_index": 0,
                    "strokes": [[[0.0, 0.0], [1.0, 1.0]]],
                    "registration_px": {"tx": 0.0, "baseline_row": 10.0},
                    "xh_px": 10.0,
                }
            ],
            "boxes": [{"index": 0, "rect_px": [0, 0, 40, 20]}],
        }
        with pytest.raises(SystemExit, match="drawn offset"):
            drawing_of("http://127.0.0.1:1", "t", "mn-suetterlin", box(0, STUFEN[0]), paths)

    def test_a_box_without_a_rectangle_is_refused_by_name(self):
        paths = {"pfade": [{"box_index": 0, "strokes": [[[0, 0], [1, 1]]]}], "boxes": []}
        with pytest.raises(SystemExit, match="no box rectangle"):
            drawing_of("http://127.0.0.1:1", "t", "mn-suetterlin", box(0, STUFEN[0]), paths)

    def test_the_two_lists_of_one_answer_key_the_same_box_differently(self):
        """`GET …/pfade` answers with `pfade[]` keyed `box_index` and `boxes[]`
        keyed `index` — one address, two spellings. Reading the wrong one makes
        the rectangle lookup miss EVERY box and abort the build with a wrong
        diagnosis, and only against the real API, which is the one place this
        instrument can ever run. So the fakes above are held to the wire type."""
        assert "index" in EigenhandStripBoxOut.model_fields
        assert "box_index" not in EigenhandStripBoxOut.model_fields
        assert "box_index" in EigenhandPfad.model_fields

    def test_a_non_png_answer_is_refused_rather_than_judged(self):
        with pytest.raises(SystemExit, match="did not answer with a PNG"):
            png_size(b"<html>not a picture</html>")

    def test_png_size_reads_the_header(self):
        assert png_size(PNG) == (1, 1)


# ------------------------------------------------------------------ the parser


class TestParser:
    def test_the_page_s_own_format_reads_back(self):
        verdicts = parse_result(result_text(["S001:FO@7s", 'S002:NP "zwei Stellen"', "R01:T"]))
        assert [verdict.uid for verdict in verdicts] == ["S001", "S002", "R01"]
        assert verdicts[0].step == FOLLOWS and verdicts[0].details == ("O",)
        assert verdicts[0].seconds == 7
        assert verdicts[1].note == "zwei Stellen"

    def test_a_fit_verdict_pasted_in_here_is_refused(self):
        """Both rounds emit the same line shape, so a paste from the wrong one
        parses perfectly and means something else entirely."""
        with pytest.raises(ResultFormatError, match="not a Tintentreue code"):
            parse_result(result_text(["S001:GW"]))

    def test_a_result_headed_by_another_round_is_refused(self):
        """The vocabulary alone does not separate the rounds: both mint `S###`
        and `R##` ids, and `A`, `U` and `-` are legal in either. The header
        names the round the file came out of, so it is held against this one."""
        assert result_tag(1) == "TINTENTREUE/1"
        with pytest.raises(ResultFormatError, match="wrong round"):
            parse_result(result_text(["S001:F"]), "TINTENTREUE/2")
        with pytest.raises(ResultFormatError, match="wrong round"):
            parse_result("BEFUND/1 geprueft=1 von 1\nS001:F\n", "TINTENTREUE/1")
        assert parse_result(result_text(["S001:F"]), "TINTENTREUE/1")[0].step == FOLLOWS

    def test_a_screen_judged_twice_is_refused(self):
        with pytest.raises(ResultFormatError, match="judged twice"):
            parse_result(result_text(["S001:F", "S001:N"]))

    def test_the_unsure_modifier_rides_along_with_its_step(self):
        verdict = parse_result(result_text(["S001:TU"]))[0]
        assert verdict.step == PARTLY and verdict.unsure

    def test_the_mapping_covers_the_light_s_three_steps_and_no_more(self):
        """The identity mapping is the whole point (§8b), so it is pinned: a
        fourth step on either side has to break here rather than pair three of
        four silently."""
        assert tool.STEP_OF_CODE == {FOLLOWS: STUFEN[0], PARTLY: STUFEN[1], FAILS: STUFEN[2]}
        assert UNRATABLE not in tool.STEP_OF_CODE
        assert set(tool.SENSOR_OF_DETAIL) == set(tool.DETAIL_CODES)


# -------------------------------------------------------------------- the plan


def judged(*pairs: tuple[str, str]) -> list[tool.Verdict]:
    return [
        tool.Verdict(uid=uid, codes=tuple(codes), seconds=None, note=None, position=n)
        for n, (uid, codes) in enumerate(pairs)
    ]


class TestPlan:
    def test_reliability_counts_the_pairs_and_the_far_disagreements(self):
        key = {
            "S001": {"uid": "S001"},
            "S002": {"uid": "S002"},
            "R01": {"uid": "R01", "repeat_of": "S001"},
            "R02": {"uid": "R02", "repeat_of": "S002"},
        }
        seen = reliability(judged(("S001", "F"), ("S002", "F"), ("R01", "F"), ("R02", "N")), key)
        assert seen["pairs"] == 2 and seen["agree"] == 1 and seen["far"] == 1
        assert not seen["enough"]  # two pairs is under the floor anyway

    def test_a_repeat_is_never_counted_twice_in_the_quantiles(self):
        key = {"S001": {"uid": "S001"}, "R01": {"uid": "R01", "repeat_of": "S001"}}
        rows = tool._first_showings(judged(("S001", "F"), ("R01", "F")), key)
        assert [verdict.uid for verdict in rows] == ["S001"]

    def test_an_unratable_box_falls_out_of_everything(self):
        key = {"S001": {"uid": "S001"}, "S002": {"uid": "S002"}}
        rows = tool._first_showings(judged(("S001", FOLLOWS), ("S002", UNRATABLE)), key)
        assert [verdict.uid for verdict in rows] == ["S001"]
        assert occupancy(rows) == {FOLLOWS: 1, PARTLY: 0, FAILS: 0}

    def test_the_light_is_held_against_the_human_with_its_three_numbers(self):
        key = {
            "S001": {"uid": "S001", "stufe": STUFEN[0]},
            "S002": {"uid": "S002", "stufe": STUFEN[0]},
            "S003": {"uid": "S003", "stufe": STUFEN[2]},
        }
        seen = against_the_light(judged(("S001", "F"), ("S002", "N"), ("S003", "N")), key)
        assert seen["agreement"] == pytest.approx(2 / 3)
        assert seen["false_green"] == 1
        assert seen["monotone"]

    def test_the_false_green_rate_is_reported_over_the_green_boxes_too(self):
        """The share over ALL judged boxes moves with the draw — the round is
        stratified by the light's own step, so how many green boxes it holds is
        a property of the draw, not of the hand. The share over the green ones
        alone is invariant under that, so gate (C) is read on it."""
        key = {
            "S001": {"uid": "S001", "stufe": STUFEN[0]},
            "S002": {"uid": "S002", "stufe": STUFEN[0]},
            "S003": {"uid": "S003", "stufe": STUFEN[2]},
            "S004": {"uid": "S004", "stufe": STUFEN[2]},
        }
        seen = against_the_light(judged(("S001", "F"), ("S002", "N"), ("S003", "N"), ("S004", "N")), key)
        assert seen["n_green"] == 2
        assert seen["false_green_of_green"] == pytest.approx(0.5)
        assert seen["false_green_share"] == pytest.approx(0.25)

    def test_a_sensor_that_names_no_box_is_a_dead_branch(self):
        """Gate (B). A graded sensor nothing ever routes through would get a
        frozen bound with no case behind it, so the round dies at two of four
        rather than calibrating around them."""
        key = {
            "S001": {"uid": "S001", "sensor": SENSOR_UNBESUCHT},
            "S002": {"uid": "S002", "sensor": SENSOR_EXKURSION},
            "S003": {"uid": "S003", "sensor": None},
        }
        seen = dead_branches(judged(("S001", "N"), ("S002", "T"), ("S003", "F")), key)
        assert seen["counts"][SENSOR_UNBESUCHT] == 1
        assert set(seen["dead"]) == {SENSOR_ABSETZER, SENSOR_AIOU}
        assert seen["kill"]

    def test_a_repeat_does_not_name_its_sensor_a_second_time(self):
        """Counted on the first showings, like every other figure here."""
        key = {
            "S001": {"uid": "S001", "sensor": SENSOR_UNBESUCHT},
            "R01": {"uid": "R01", "sensor": SENSOR_UNBESUCHT, "repeat_of": "S001"},
        }
        rows = tool._first_showings(judged(("S001", "N"), ("R01", "N")), key)
        assert dead_branches(rows, key)["counts"][SENSOR_UNBESUCHT] == 1

    def test_the_rank_is_nearest_and_never_interpolated(self):
        """An interpolated quantile would invent a reading between two boxes,
        and at thirty boxes that invented number would BE the bound."""
        values = [0.01, 0.02, 0.03, 0.04, 0.10]
        assert rank_value(values, 0.9) == 0.10
        assert rank_value(values, 0.5) == 0.03

    def test_a_ceiling_rounds_down_and_a_floor_rounds_up(self):
        """Stricter in both directions: a bound loosened by a rounding step is
        exactly the false green gate (C) is about."""
        assert bound_of([0.0, 0.0, 0.0, 0.0, 0.1234], smaller_is_better=True) == 0.12
        assert bound_of([0.7791, 0.9, 0.9, 0.9, 0.9], smaller_is_better=False) == 0.78

    def test_the_bound_of_a_thin_step_stays_borrowed_and_says_so(self):
        key = {f"S{n:03d}": {"uid": f"S{n:03d}", "readings": {SENSOR_UNBESUCHT: 0.01}} for n in range(3)}
        rows = judged(*((uid, "F") for uid in key))
        row = cuts(rows, key, VORLAEUFIG)[SENSOR_UNBESUCHT]
        assert row["green"] is None and "geborgt" in row["why"]
        assert row["borrowed"] == (VORLAEUFIG.unbesucht_gruen, VORLAEUFIG.unbesucht_gelb)

    def test_a_pair_that_does_not_come_out_strictly_ordered_is_refused(self):
        """Green has to stay STRICTLY stricter than yellow. Equal bounds are the
        ordinary way that fails — the sensor does not separate the two steps —
        and a yellow band of zero width would quietly turn the three-step light
        into a two-step one. Inverted labels fail the same way."""
        equal = {f"G{n}": {"uid": f"G{n}", "readings": {SENSOR_UNBESUCHT: 0.30}} for n in range(MIN_PER_STEP)}
        equal |= {f"T{n}": {"uid": f"T{n}", "readings": {SENSOR_UNBESUCHT: 0.30}} for n in range(MIN_PER_STEP)}
        rows = judged(*[(f"G{n}", "F") for n in range(MIN_PER_STEP)]) + judged(
            *[(f"T{n}", "T") for n in range(MIN_PER_STEP)]
        )
        row = cuts(rows, equal, VORLAEUFIG)[SENSOR_UNBESUCHT]
        assert row["green"] is None and "nicht geordnet" in row["why"]

        inverted = {f"G{n}": {"uid": f"G{n}", "readings": {SENSOR_UNBESUCHT: 0.30}} for n in range(MIN_PER_STEP)}
        inverted |= {f"T{n}": {"uid": f"T{n}", "readings": {SENSOR_UNBESUCHT: 0.01}} for n in range(50)}
        rows = judged(*[(f"G{n}", "F") for n in range(MIN_PER_STEP)]) + judged(*[(f"T{n}", "T") for n in range(50)])
        row = cuts(rows, inverted, VORLAEUFIG)[SENSOR_UNBESUCHT]
        assert row["green"] is None and "nicht geordnet" in row["why"]

    def test_a_clean_round_yields_the_two_bounds(self):
        key = {}
        for n in range(MIN_PER_STEP):
            key[f"G{n}"] = {"uid": f"G{n}", "readings": {SENSOR_UNBESUCHT: 0.02 + n / 1000}}
            key[f"T{n}"] = {"uid": f"T{n}", "readings": {SENSOR_UNBESUCHT: 0.12 + n / 1000}}
        rows = judged(*[(f"G{n}", "F") for n in range(MIN_PER_STEP)]) + judged(
            *[(f"T{n}", "T") for n in range(MIN_PER_STEP)]
        )
        row = cuts(rows, key, VORLAEUFIG)[SENSOR_UNBESUCHT]
        assert row["green"] == 0.02 and row["yellow"] == 0.12
        assert row["why"] == "gemessen"

    def test_the_absetzer_is_a_rule_and_not_a_quantile(self):
        key = {
            f"S{n:03d}": {"uid": f"S{n:03d}", "readings": {SENSOR_ABSETZER: 3.0}, "absetzer_soll": 2.0}
            for n in range(6)
        }
        rows = judged(*[(uid, "N") for uid in key])
        tightened = pen_lift_cut(rows, key, VORLAEUFIG)
        assert tightened["n"] == 6 and tightened["gelb"] == 0

        few = dict(list(key.items())[:3])
        stays = pen_lift_cut(judged(*[(uid, "N") for uid in few]), few, VORLAEUFIG)
        assert stays["gelb"] == VORLAEUFIG.absetzer_gelb

    def test_jumps_stay_ungraded_unless_the_split_is_clean(self):
        """The one sensor with no anchor: a bound is proposed only where the
        marked boxes do not overlap the rest at all."""
        overlapping = {
            "S001": {"uid": "S001", "readings": {SENSOR_SPRUENGE: 4.0}},
            "S002": {"uid": "S002", "readings": {SENSOR_SPRUENGE: 9.0}},
        }
        seen = jumps_proposal(judged(("S001", "NH"), ("S002", "F")), overlapping)
        assert seen["proposed"] is None and not seen["clean"]

        clean = {f"S{n:03d}": {"uid": f"S{n:03d}", "readings": {SENSOR_SPRUENGE: 20.0}} for n in range(5)}
        clean["S999"] = {"uid": "S999", "readings": {SENSOR_SPRUENGE: 2.0}}
        rows = judged(*[(uid, "NH") for uid in clean if uid != "S999"], ("S999", "F"))
        seen = jumps_proposal(rows, clean)
        assert seen["clean"] and seen["proposed"] == 11.0


# ------------------------------------------------------------------ the files


class TestRound:
    def test_the_whole_build_runs_against_a_fake_api(self, tmp_path: Path, monkeypatch, capsys):
        """One pass over the wiring: state read, paths read, crops fetched,
        round written. The real one cannot run anywhere but on the author's
        machine — it reads the reserved own-hand pixels out of the shared
        database — so this is the only place the plumbing is exercised at all."""
        state = {
            "hand": "mn-suetterlin",
            "fassungen": [
                {
                    "strip": "S0001",
                    "fassung": "F01",
                    "kaesten": [
                        {
                            "box_index": index,
                            "word": "lesen",
                            "absetzer_soll": 2,
                            "tintentreue": {
                                "gemessen": True,
                                "stufe": STUFEN[index % 3],
                                "sensor": None,
                                "sensoren": [{"name": SENSOR_UNBESUCHT, "wert": 0.01 * index}],
                            },
                        }
                        for index in range(12)
                    ],
                }
            ],
        }
        paths = {
            "pfade": [
                {
                    "box_index": index,
                    "strokes": [[[0.0, 0.0], [1.0, 1.0]]],
                    "registration_px": {"tx": 0.0, "ty": 0.0, "baseline_row": 1.0},
                    "xh_px": 1.0,
                }
                for index in range(12)
            ],
            # `index`, not `box_index`: that is what `EigenhandStripBoxOut`
            # puts on the wire, and the one test below holds this fake to it.
            "boxes": [{"index": index, "rect_px": [0, 0, 1, 1]} for index in range(12)],
        }
        monkeypatch.setattr(tool, "request_json", lambda _m, url, *a, **k: paths if url.endswith("/pfade") else state)
        monkeypatch.setattr(tool, "request_bytes", lambda *a, **k: PNG)
        code = tool.main(
            [
                "build",
                "--hand",
                "mn-suetterlin",
                "--round",
                "1",
                "--api",
                "http://127.0.0.1:1",
                "--token",
                "x",
                "--n-label",
                "8",
                "--repeats",
                "1",
                "--min-repeat-gap",
                "1",
                "--out",
                str(tmp_path),
            ]
        )
        assert code == 0
        room = tmp_path / "r1"
        payload = json.loads((room / "payload.json").read_text(encoding="utf-8"))
        key = json.loads((room / "key.json").read_text(encoding="utf-8"))
        stamp = json.loads((room / "provenance.json").read_text(encoding="utf-8"))
        assert payload["question"] == "tintentreue"
        assert len(payload["items"]) == len(key) == 9  # eight boxes plus one repeat
        assert [entry for entry in key if entry.get("repeat_of")]
        # The stamp carries the numbers the draw was stratified under — nothing
        # else could reconstruct it once they are replaced.
        assert stamp["schwellen"]["unbesucht_gruen"] == VORLAEUFIG.unbesucht_gruen
        assert json.loads((room / "reserve.json").read_text(encoding="utf-8"))
        assert (room / "seite.html").exists()
        assert "never publish it" in capsys.readouterr().out
        # A repeat is the same screen down to the pixel — anything else is a
        # tell the judge could learn before anyone noticed it existed.
        shown = {item["id"]: item for item in payload["items"]}
        repeat = next(entry for entry in key if entry.get("repeat_of"))
        assert shown[repeat["uid"]] | {"id": repeat["repeat_of"]} == shown[repeat["repeat_of"]]

    def test_the_evaluation_runs_in_its_pre_registered_order(self, tmp_path: Path, capsys):
        """The report is the round's whole output, so it is pinned end to end:
        reliability first, then occupancy, the light against the human, the
        bounds — and under the reliability floor, no bound at all."""
        room = tmp_path / "r1"
        room.mkdir()
        key = []
        lines = []
        for n in range(12):
            uid = f"S{n + 1:03d}"
            step = (FOLLOWS, PARTLY, FAILS)[n % 3]
            key.append(
                {
                    "uid": uid,
                    "strip": "S0001",
                    "fassung": "F01",
                    "box_index": n,
                    "word": "lesen",
                    "stufe": STUFEN[n % 3],
                    "sensor": None,
                    "readings": {SENSOR_UNBESUCHT: 0.01 * (n + 1), SENSOR_AIOU: 0.9 - 0.01 * n},
                    "absetzer_soll": 2,
                }
            )
            lines.append(f"{uid}:{step}")
        for n in range(6):  # six repeats, all answered the same way
            key.append({**key[n], "uid": f"R{n + 1:02d}", "repeat_of": key[n]["uid"]})
            lines.append(f"R{n + 1:02d}:{lines[n].split(':')[1]}")
        (room / "key.json").write_text(json.dumps(key), encoding="utf-8")
        (room / "provenance.json").write_text(
            json.dumps({"round": 1, "hand": "mn-suetterlin", "schwellen": {"stand": "2026-09-20", "vorlaeufig": True}}),
            encoding="utf-8",
        )
        (room / "urteile.txt").write_text(result_text(lines), encoding="utf-8")

        assert tool.main(["analyse", "--round-dir", str(room), "--result", str(room / "urteile.txt")]) == 0
        out = capsys.readouterr().out
        assert out.index("1 Verlässlichkeit") < out.index("2 Besetzung") < out.index("4 Ampel gegen Mensch")
        assert "Übereinstimmung 100%" in out
        assert "SCHWELLEN_JE_HAND" in out
        # Bounds stayed borrowed on this synthetic round, so the block has to
        # say so per value AND keep the label: a set that drops „vorläufig"
        # while half its numbers come off the plate claims a calibration that
        # did not happen.
        assert "geborgt" in out
        assert "vorlaeufig=True" in out and "vorlaeufig=False" not in out

    def test_no_bound_is_set_under_the_reliability_floor(self, tmp_path: Path, capsys):
        room = tmp_path / "r2"
        room.mkdir()
        key = [
            {"uid": "S001", "stufe": STUFEN[0], "readings": {}, "absetzer_soll": 2},
            {"uid": "R01", "repeat_of": "S001", "stufe": STUFEN[0], "readings": {}, "absetzer_soll": 2},
        ]
        (room / "key.json").write_text(json.dumps(key), encoding="utf-8")
        (room / "provenance.json").write_text(json.dumps({"round": 2, "hand": "mn-suetterlin"}), encoding="utf-8")
        (room / "urteile.txt").write_text(result_text(["S001:F", "R01:N"], round_label=2), encoding="utf-8")
        assert tool.main(["analyse", "--round-dir", str(room), "--result", str(room / "urteile.txt")]) == 0
        out = capsys.readouterr().out
        assert "Keine Grenze gesetzt" in out and "SCHWELLEN_JE_HAND" not in out

    def test_a_round_is_written_once(self, tmp_path: Path):
        built = tool.Built(
            items=[
                {"id": "S001", "w": 1, "h": 1, "img": base64.b64encode(PNG).decode(), "strokes": [[[0, 0], [1, 1]]]}
            ],
            key=[{"uid": "S001"}],
            reserve=[],
            stamp={"round": 1, "hand": "mn-suetterlin"},
        )
        page = tool.write_round(tmp_path / "r1", built, force=False)
        assert page.exists() and (tmp_path / "r1" / "key.json").exists()
        with pytest.raises(SystemExit, match="written once"):
            tool.write_round(tmp_path / "r1", built, force=False)

    def test_the_store_key_changes_when_the_drawing_does(self):
        """A rebuilt page whose drawing moved must start clean rather than
        replay old verdicts by index onto new screens (§3.10)."""
        stamp = {"round": 1, "hand": "mn-suetterlin", "seed": 1}
        first = tool.round_store(stamp, [{"id": "S001", "strokes": [[[0, 0], [1, 1]]]}])
        same = tool.round_store({**stamp, "built_at": "later"}, [{"id": "S001", "strokes": [[[0, 0], [1, 1]]]}])
        moved = tool.round_store(stamp, [{"id": "S001", "strokes": [[[0, 0], [2, 2]]]}])
        assert first == same and first != moved
