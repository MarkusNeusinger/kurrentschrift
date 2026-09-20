"""The per-box ink-fidelity traffic light, and the twin clamp under it.

Two kinds of test live here. The first walks the SHARED fixture
`tests/fixtures/tintentreue_cases.json`, which the SPA's reader asserts as
well (`app/src/sections/admin/eigenhand/pfadRohzahlen.test.ts`): both sides
read the same unvalidated `meta` blob in two languages with two null rules, so
without a clamp „measured" drifts against „gemessen" and the panel shows
numbers for a box the traffic light calls grey. Same pattern as
`shaping_cases.json` for `shaping.ts`/`shaping.py`.

The second kind pins what only Python has: the bounds themselves, the fold
rule and the fact that nothing here is calibrated yet.

The fixture deliberately carries NO `NaN`/`Infinity`: Python's `json` accepts
both as an extension and `JSON.parse` refuses them, so a shared file cannot
hold them. They are pinned per language instead — here, and in the TS suite's
own cases.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.eigenhand import tintentreue as modul
from core.eigenhand.tintentreue import (
    GRUND_KEIN_EINTRAG,
    GRUND_NICHTS,
    GRUND_UNVOLLSTAENDIG,
    GRUND_VON_HAND,
    SENSOR_ABSETZER,
    SENSOR_AIOU,
    SENSOR_EXKURSION,
    SENSOR_ORDER,
    SENSOR_SPRUENGE,
    SENSOR_UNBESUCHT,
    SENSOREN_MIT_SCHWELLE,
    STUFE_UNGEMESSEN,
    STUFEN,
    TINTENTREUE_FORMAT,
    VORLAEUFIG,
    Schwellen,
    rohzahlen,
    schwellen_of,
    sensoren_of,
    tintentreue,
    zaehler,
)


CASES = Path(__file__).parent / "fixtures" / "tintentreue_cases.json"
HAND = "mn-suetterlin"


def _cases() -> list[dict]:
    return json.loads(CASES.read_text(encoding="utf-8"))


def _pfad(**meta_tintenpfad) -> dict:
    """A stored path entry carrying exactly the sensors handed in."""
    return {
        "box_index": 0,
        "word": "lesen",
        "strokes": [[[0.0, 0.0], [1.0, 0.5]]],
        "registration_px": {"tx": 0.0, "ty": 0.0, "baseline_row": 90.0},
        "xh_px": 40.0,
        "verfahren": "tintenpfad",
        "konfiguration": {},
        "meta": {"tintenpfad": dict(meta_tintenpfad)},
        "erzeugt_am": "2026-09-20",
        "flecken_n": None,
    }


def _gruen(**overrides) -> dict:
    """A box every graded sensor is happy with — the base for one-knob cases."""
    sensors = {
        "jumps": 0,
        "hairpins": 0,
        "paper_lifts": 0,
        "ink_unvisited_share": 0.01,
        "paper_excursion_xh": 0.05,
        "aiou": 0.9,
    }
    sensors.update(overrides)
    return _pfad(**sensors)


def _urteil(pfad: dict, *, pfade_format: int = 2, maske_n: int | None = None):
    return tintentreue(pfad, hand=HAND, pfade_format=pfade_format, maske_n=maske_n)


# ------------------------------------------------------- the shared fixture


def test_fixture_is_not_empty():
    assert _cases(), "the shared Tintentreue fixture must not be empty"


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["name"])
def test_fixture_readings_and_verdicts(case: dict):
    pfad = case["pfad"]
    if pfad is not None:
        assert rohzahlen(pfad).as_dict() == case["rohzahlen"], case["name"]
    urteil = tintentreue(pfad, hand=case["hand"], pfade_format=case["pfade_format"], maske_n=case["maske_n"])
    assert {key: urteil.as_dict()[key] for key in case["tintentreue"]} == case["tintentreue"], case["name"]


def test_fixture_carries_no_nan_or_infinity():
    # `json.loads` would take them and `JSON.parse` would not, so a case using
    # one is a file only half the twin can read.
    assert not any(token in CASES.read_text(encoding="utf-8") for token in ("NaN", "Infinity"))


# --------------------------------------------------------------- the reading


def test_a_measured_zero_is_not_a_missing_reading():
    werte = rohzahlen(_pfad(ink_unvisited_share=0.0, paper_lifts=0, jumps=0, hairpins=0))
    assert werte.ink_unvisited_share == 0.0
    assert werte.gemessen is True


def test_nan_and_infinity_are_refused_like_strings():
    werte = rohzahlen(_pfad(ink_unvisited_share=float("nan"), paper_lifts=float("inf"), jumps="1", hairpins=True))
    assert werte.as_dict() == {
        "ink_unvisited_share": None,
        "paper_lifts": None,
        "jumps": None,
        "hairpins": None,
        "gemessen": False,
    }


@pytest.mark.parametrize("meta", [None, "keine", [1, 2, 3], 7], ids=["null", "Zeichenkette", "Liste", "Zahl"])
def test_a_meta_that_is_not_a_mapping_reads_as_no_sensors(meta: object):
    # The one place the two guards are written differently — `isinstance(…,
    # Mapping)` here, optional chaining over there — so the shared fixture
    # carries these cases too.
    pfad = _pfad()
    pfad["meta"] = meta
    assert rohzahlen(pfad).gemessen is False


def test_a_missing_meta_key_reads_as_no_sensors():
    pfad = _pfad()
    del pfad["meta"]
    assert rohzahlen(pfad).gemessen is False


# --------------------------------------------------------------- the bounds


@pytest.mark.parametrize(
    ("share", "stufe"), [(0.05, 0), (0.0501, 1), (0.15, 1), (0.1501, 2)], ids=["grün", "knapp gelb", "gelb", "rot"]
)
def test_unvisited_bounds_are_inclusive(share: float, stufe: int):
    werte = {sensor.name: sensor for sensor in sensoren_of(_gruen(ink_unvisited_share=share), VORLAEUFIG)}
    assert werte[SENSOR_UNBESUCHT].stufe == stufe


@pytest.mark.parametrize(("xh", "stufe"), [(0.20, 0), (0.35, 1), (0.36, 2)])
def test_excursion_bounds_are_inclusive(xh: float, stufe: int):
    werte = {sensor.name: sensor for sensor in sensoren_of(_gruen(paper_excursion_xh=xh), VORLAEUFIG)}
    assert werte[SENSOR_EXKURSION].stufe == stufe


@pytest.mark.parametrize(("aiou", "stufe"), [(0.75, 0), (0.74, 1), (0.65, 1), (0.64, 2)])
def test_aiou_bounds_are_inclusive_the_other_way_round(aiou: float, stufe: int):
    werte = {sensor.name: sensor for sensor in sensoren_of(_gruen(aiou=aiou), VORLAEUFIG)}
    assert werte[SENSOR_AIOU].stufe == stufe


@pytest.mark.parametrize(
    ("word", "lifts", "stufe"), [("lesen", 0, 0), ("lesen", 1, 1), ("lesen", 2, 2), ("1922", 3, 0)]
)
def test_the_absetzer_is_read_as_runs_against_the_body_runs_of_the_word(word: str, lifts: int, stufe: int):
    pfad = _gruen(paper_lifts=lifts)
    pfad["word"] = word
    werte = {sensor.name: sensor for sensor in sensoren_of(pfad, VORLAEUFIG)}
    assert werte[SENSOR_ABSETZER].stufe == stufe
    # …and the reading shown is the run count, not the lift count.
    assert werte[SENSOR_ABSETZER].wert == lifts + 1


def test_jumps_and_hairpins_are_read_but_never_graded():
    werte = {sensor.name: sensor for sensor in sensoren_of(_gruen(jumps=9, hairpins=7), VORLAEUFIG)}
    assert werte[SENSOR_SPRUENGE].wert == 16.0
    assert werte[SENSOR_SPRUENGE].stufe is None
    assert SENSOR_SPRUENGE not in SENSOREN_MIT_SCHWELLE
    # A sensor without a bound must not hold the box back either.
    assert _urteil(_gruen(jumps=9, hairpins=7)).stufe == STUFEN[0]


def test_a_half_read_jump_pair_is_no_reading_rather_than_the_measured_half():
    # Filling the missing half in with 0 would show „1" as though the hairpins
    # had been counted and found empty — the same collapse `Rohzahlen` refuses.
    werte = {sensor.name: sensor for sensor in sensoren_of(_gruen(jumps=1, hairpins=None), VORLAEUFIG)}
    assert werte[SENSOR_SPRUENGE].wert is None
    # …while the two raw readings stay apart, so the panel can still show the 1.
    zahlen = rohzahlen(_gruen(jumps=1, hairpins=None))
    assert (zahlen.jumps, zahlen.hairpins) == (1.0, None)


def test_an_integer_wider_than_a_float_is_refused_like_a_string():
    # Valid JSON both parsers accept: Python builds an arbitrary-precision int
    # (`float()` would raise), JavaScript gets `Infinity`. Both must answer
    # „no reading" — pinned jointly in the shared fixture as well.
    assert rohzahlen(_pfad(paper_lifts=10**400, jumps=0, hairpins=0)).paper_lifts is None


# ------------------------------------------------------------- the fold rule


def test_the_worst_sensor_decides_and_a_good_one_buys_nothing():
    assert _urteil(_gruen(aiou=0.51)).stufe == STUFEN[2]
    assert _urteil(_gruen()).stufe == STUFEN[0]
    assert _urteil(_gruen()).grund == GRUND_NICHTS


def test_a_tie_is_broken_by_the_sensor_order_not_by_the_larger_number():
    # Absetzer and AIoU are both red; the order names the Absetzer, although
    # the AIoU number is the more dramatic one.
    urteil = _urteil(_gruen(paper_lifts=3, aiou=0.05))
    assert urteil.stufe == STUFEN[2]
    assert urteil.sensor == SENSOR_ABSETZER
    assert SENSOR_ORDER.index(SENSOR_ABSETZER) < SENSOR_ORDER.index(SENSOR_AIOU)


def test_a_yellow_sensor_never_loses_to_a_red_one_of_higher_rank():
    # Absetzer yellow, AIoU red: severity wins over the order.
    urteil = _urteil(_gruen(paper_lifts=1, aiou=0.2))
    assert (urteil.stufe, urteil.sensor) == (STUFEN[2], SENSOR_AIOU)


# ------------------------------------------------------------ the grey states


def test_a_box_without_an_entry_has_one_grey_state_for_four_causes():
    urteil = tintentreue(None, hand=HAND, pfade_format=1, maske_n=None)
    assert (urteil.stufe, urteil.grund, urteil.sensoren) == (STUFE_UNGEMESSEN, GRUND_KEIN_EINTRAG, [])


def test_the_mask_argument_has_to_be_named_rather_than_forgotten():
    # A default would hand out a green box for an entry followed over other
    # ink; not knowing today's mask is a decision and is written as None.
    with pytest.raises(TypeError):
        tintentreue(_gruen(), hand=HAND, pfade_format=2)  # type: ignore[call-arg]


def test_format_one_stays_grey_even_with_three_perfect_sensors():
    urteil = _urteil(_gruen(), pfade_format=1)
    assert urteil.stufe == STUFE_UNGEMESSEN
    assert urteil.grund == "Format 1 — unvollständig gemessen"
    assert urteil.gemessen is False


def test_an_unmeasured_authored_bahn_is_an_origin_and_never_a_colour():
    pfad = _pfad()
    pfad["verfahren"] = "authored"
    urteil = _urteil(pfad)
    assert (urteil.stufe, urteil.grund) == (STUFE_UNGEMESSEN, GRUND_VON_HAND)


def test_a_measured_authored_bahn_carries_the_same_light():
    # V21: the tool measures a re-traced Bahn on its next run and it then
    # carries this light like any other. `verfahren` never flips back, so a
    # grey keyed on the Herkunft would stay grey forever — and the author would
    # get no feedback on exactly the trace Phase 2 exists to let him make.
    pfad = _gruen()
    pfad["verfahren"] = "authored"
    assert _urteil(pfad).stufe == STUFEN[0]
    schlecht = _gruen(aiou=0.1)
    schlecht["verfahren"] = "authored"
    assert (_urteil(schlecht).stufe, _urteil(schlecht).sensor) == (STUFEN[2], SENSOR_AIOU)


def test_the_authored_state_outranks_a_changed_mask():
    # Both apply only while the Bahn is unmeasured; „von Hand" wins because an
    # authored Bahn is not a follow at all and the mask never entered it.
    pfad = _pfad()
    pfad["verfahren"] = "authored"
    pfad["flecken_n"] = 4
    assert _urteil(pfad, maske_n=9).grund == GRUND_VON_HAND


def test_a_changed_mask_greys_the_box_and_an_unchanged_one_does_not():
    pfad = _gruen()
    pfad["flecken_n"] = 4
    assert _urteil(pfad, maske_n=9).grund == "Maske geändert"
    assert _urteil(pfad, maske_n=4).stufe == STUFEN[0]
    # Nothing known about today's mask, or nothing recorded at follow time:
    # a state is not invented out of a missing number.
    assert _urteil(pfad, maske_n=None).stufe == STUFEN[0]
    pfad["flecken_n"] = None
    assert _urteil(pfad, maske_n=9).stufe == STUFEN[0]


def test_a_hole_in_a_complete_format_greys_the_box_rather_than_guessing():
    urteil = _urteil(_gruen(aiou=None))
    assert (urteil.stufe, urteil.grund, urteil.sensor) == (STUFE_UNGEMESSEN, GRUND_UNVOLLSTAENDIG, SENSOR_AIOU)


def test_a_grey_box_still_carries_its_readings():
    # The panel shows the numbers even where the light stays grey — otherwise
    # „Format 1" would hide exactly the three sensors that WERE measured.
    urteil = _urteil(_gruen(), pfade_format=1)
    assert [sensor.name for sensor in urteil.sensoren] == list(SENSOR_ORDER)
    assert urteil.as_dict()["sensoren"][1]["wert"] == 0.01


# ------------------------------------------------- the thresholds themselves


def test_every_threshold_ships_provisional_and_none_is_calibrated_yet():
    schwellen = schwellen_of(HAND)
    assert schwellen is VORLAEUFIG
    assert schwellen.vorlaeufig is True
    assert schwellen.stand == "2026-09-20"
    assert _urteil(_gruen()).vorlaeufig is True


def test_a_calibrated_hand_would_be_used_instead(monkeypatch: pytest.MonkeyPatch):
    eigene = Schwellen(
        stand="2026-12-24",
        vorlaeufig=False,
        unbesucht_gruen=0.2,
        unbesucht_gelb=0.4,
        absetzer_gelb=2,
        exkursion_gruen_xh=0.5,
        exkursion_gelb_xh=0.8,
        aiou_gruen=0.4,
        aiou_gelb=0.2,
    )
    monkeypatch.setitem(modul.SCHWELLEN_JE_HAND, HAND, eigene)
    urteil = _urteil(_gruen(ink_unvisited_share=0.18))
    assert (urteil.stufe, urteil.vorlaeufig, urteil.schwellen_stand) == (STUFEN[0], False, "2026-12-24")


def test_the_module_carries_its_own_format_marker():
    assert TINTENTREUE_FORMAT == 1


# -------------------------------------------------------- the Fassung counter


def test_a_fassung_is_counted_and_never_coloured():
    urteile = [
        _urteil(_gruen()),
        _urteil(_gruen()),
        _urteil(_gruen(aiou=0.1)),
        _urteil(_gruen(), pfade_format=1),
        tintentreue(None, hand=HAND, pfade_format=2, maske_n=None),
    ]
    # Hand-drawn and NOT measured — V21's ungemessene half of the two counters.
    pfad = _pfad()
    pfad["verfahren"] = "authored"
    urteile.append(_urteil(pfad))
    gezaehlt = zaehler(urteile)
    assert gezaehlt.as_dict() == {"kaesten": 6, "gemessen": 3, "folgt": 2, "von_hand": 1}


def test_a_measured_hand_drawn_box_counts_as_measured_not_as_von_hand():
    pfad = _gruen()
    pfad["verfahren"] = "authored"
    gezaehlt = zaehler([_urteil(pfad)])
    assert gezaehlt.as_dict() == {"kaesten": 1, "gemessen": 1, "folgt": 1, "von_hand": 0}
