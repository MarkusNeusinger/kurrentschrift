"""The due list behind the Übergabekarte — pure derivation over a Kartei.

What the rules have to get right is not arithmetic but honesty: a card appears
only where the SERVER can see the step is open, it names the parameters the
command actually needs, and it goes away again. The cases below are one per
rule plus the two that would be easy to get wrong — the OLDEST outstanding
Bogen (not the newest printed one) and a chain order that stays the order the
steps are done in.
"""

from __future__ import annotations

import re
from pathlib import Path

from core.eigenhand.faellig import RULE_IDS, faellig
from core.eigenhand.kartei import empty_kartei


HAND = "mn-suetterlin"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _kartei() -> dict:
    return empty_kartei(HAND, "suetterlin")


def _print(kartei: dict, sheet: str, strips: list[str]) -> dict:
    kartei["sheets"][sheet] = {"printed": "2026-09-19", "strips": list(strips), "layout_sha256": "", "scans": []}
    return kartei


def _judge(kartei: dict, strip: str, sheet: str, row_index: int, status: str = "angenommen", fassung: str = "F01"):
    record = kartei["strips"].setdefault(strip, {"fassungen": []})
    record["fassungen"].append({"id": fassung, "sheet": sheet, "row_index": row_index, "status": status})
    return kartei


def _due(kartei: dict, *, setup: bool = False, stored: set[tuple[str, str]] | None = None, soll: bool = True):
    return faellig(kartei, setup=setup, stored=stored or set(), soll=soll)


def _ids(rows: list[dict]) -> list[str]:
    return [row["id"] for row in rows]


class TestNothingDue:
    def test_a_hand_with_nothing_open_gets_no_card_at_all(self):
        # The empty list is the normal state — the cards are invisible while
        # nothing waits at the machine.
        assert _due(_kartei()) == []

    def test_a_hand_without_a_saved_setup_is_not_asked_to_pull_one(self):
        """No row means the due step is a FORM in the browser, not a command."""
        assert _ids(_due(_kartei(), setup=False)) == []


class TestRules:
    def test_a_saved_setup_is_due_on_the_writing_machine_until_something_is_written(self):
        due = _due(_kartei(), setup=True)
        assert _ids(due) == ["setup_pull"]
        assert due[0]["befehl"] == f"uv run python -m tools.eigenhand.setup --hand {HAND} --pull"

        # The server cannot see the local cache; the first Fassung of the hand
        # is the nearest thing it CAN see, so that is what clears the card.
        written = _judge(_print(_kartei(), "B0001", ["S0001"]), "S0001", "B0001", 0)
        assert "setup_pull" not in _ids(_due(written, setup=True, stored={("S0001", "F01")}))

    def test_a_missing_uebergangsraum_is_a_card_and_a_stored_one_is_not(self):
        assert _ids(_due(_kartei(), soll=False)) == ["universe_push"]
        assert _due(_kartei(), soll=True) == []

    def test_a_printed_bogen_nobody_judged_names_the_sheet_and_the_open_rows(self):
        kartei = _print(_kartei(), "B0001", ["S0001", "S0002", "S0003"])
        _judge(kartei, "S0001", "B0001", 0)
        [card] = _due(kartei, stored={("S0001", "F01")})
        assert card["id"] == "bogen_pull"
        assert card["befehl"] == f"uv run python -m tools.eigenhand.pull --hand {HAND} --sheet B0001"
        assert card["params"] == {"hand": HAND, "sheet": "B0001", "offen": 2, "weitere": 0}

    def test_the_oldest_outstanding_bogen_is_named_not_the_newest_printed_one(self):
        # A stack leaves several Bögen out at once. `sheets.last` would point at
        # B0003 and send the author past the one that has been lying around
        # longest — which is the whole reason this rule sorts by id.
        kartei = _kartei()
        for sheet in ("B0001", "B0002", "B0003"):
            _print(kartei, sheet, ["S0001"])
        _judge(kartei, "S0001", "B0002", 0)
        [card] = _due(kartei, stored={("S0001", "F01")})
        assert card["params"]["sheet"] == "B0001"

    def test_the_further_open_boegen_are_named_so_one_cannot_hide_the_others(self):
        """A spoiled B0001 nobody will ever write must not swallow today's Bogen.

        Nothing retires a sheet and the print queue ignores outstanding ones, so
        the oldest can sit in front forever. One card still — `pull` takes one
        `--sheet` and a stack may be 20 — but the rest are named on it.
        """
        kartei = _kartei()
        for sheet in ("B0001", "B0002", "B0005"):
            _print(kartei, sheet, ["S0001"])
        [card] = _due(kartei)
        assert card["params"]["sheet"] == "B0001"
        assert card["params"]["weitere"] == 2
        assert card["params"]["weitere_boegen"] == "B0002 · B0005"

    def test_a_single_open_bogen_says_none_are_further_out(self):
        # `weitere` is always there so the SPA can decide without a lookup, and
        # the id list is absent rather than empty: „Auch offen: " with nothing
        # behind it is worse than no line.
        kartei = _print(_kartei(), "B0001", ["S0001"])
        [card] = _due(kartei)
        assert card["params"]["weitere"] == 0
        assert "weitere_boegen" not in card["params"]

    def test_a_long_stack_stops_naming_and_says_so(self):
        kartei = _kartei()
        for n in range(1, 11):
            _print(kartei, f"B{n:04d}", ["S0001"])
        [card] = _due(kartei)
        assert card["params"]["weitere"] == 9
        assert card["params"]["weitere_boegen"].endswith("…")
        assert card["params"]["weitere_boegen"].count("·") == 5

    def test_a_fully_judged_bogen_is_no_longer_outstanding(self):
        kartei = _print(_kartei(), "B0001", ["S0001", "S0002"])
        _judge(kartei, "S0001", "B0001", 0)
        _judge(kartei, "S0002", "B0001", 1, status="verworfen")
        # A rejected row is judged too: the sheet is done, the strip is not.
        assert "bogen_pull" not in _ids(_due(kartei, stored={("S0001", "F01")}))

    def test_an_accepted_fassung_without_a_stored_image_asks_for_mit_streifen(self):
        kartei = _print(_kartei(), "B0001", ["S0001", "S0002"])
        _judge(kartei, "S0001", "B0001", 0)
        _judge(kartei, "S0002", "B0001", 1)
        [card] = _due(kartei, stored={("S0001", "F01")})
        assert card["id"] == "sync_streifen"
        assert card["befehl"] == f"uv run python -m tools.eigenhand.sync --hand {HAND} --mit-streifen"
        # The count is the point: „4 of 37" is a sentence the all-or-nothing
        # „no strips at all" of the strips panel could never say.
        assert card["params"]["ohne_bild"] == 1
        assert _due(kartei, stored={("S0001", "F01"), ("S0002", "F01")}) == []

    def test_a_rejected_or_withdrawn_fassung_never_asks_for_its_image(self):
        kartei = _print(_kartei(), "B0001", ["S0001", "S0002"])
        _judge(kartei, "S0001", "B0001", 0, status="verworfen")
        _judge(kartei, "S0002", "B0001", 1, status="zurueckgezogen")
        assert _due(kartei) == []


class TestOrder:
    def test_the_cards_come_in_chain_order_and_only_with_known_ids(self):
        kartei = _print(_kartei(), "B0001", ["S0001", "S0002"])
        _judge(kartei, "S0001", "B0001", 0)
        due = _due(kartei, setup=True, soll=False)
        # setup_pull is absent here — something IS written — and the rest stands
        # in the order the steps are done in.
        assert _ids(due) == ["universe_push", "bogen_pull", "sync_streifen"]
        assert set(_ids(due)) <= set(RULE_IDS)

    def test_every_rule_id_is_reachable_so_the_spa_copy_cannot_go_stale(self):
        """The SPA keeps the same four ids; an unreachable one would be dead copy."""
        empty = _kartei()
        seen = set(_ids(_due(empty, setup=True))) | set(_ids(_due(empty, soll=False)))
        kartei = _print(_kartei(), "B0001", ["S0001", "S0002"])
        _judge(kartei, "S0001", "B0001", 0)
        seen |= set(_ids(_due(kartei)))
        assert seen == set(RULE_IDS)


class TestTypeScriptTwin:
    """One rule list, two languages — the same pin `lesarten` carries.

    Without this, adding a rule here and forgetting the SPA is green in every
    suite: the server emits the id, `uebergabeKarte` finds no copy and returns
    `null`, and the card the author is waiting for silently never appears.
    """

    def test_the_spa_knows_exactly_the_ids_this_module_emits(self):
        src = (REPO_ROOT / "app" / "src" / "sections" / "admin" / "eigenhand" / "uebergabe.ts").read_text(
            encoding="utf-8"
        )
        block = src.split("FAELLIG_IDS = [")[1].split("]")[0]
        assert tuple(re.findall(r"'([^']+)'", block)) == RULE_IDS

    def test_every_rule_has_german_copy_in_the_catalogue(self):
        src = (REPO_ROOT / "app" / "src" / "locales" / "de" / "admin.ts").read_text(encoding="utf-8")
        block = src.split("      karten: {")[1].split("\n      },")[0]
        keyed = set(re.findall(r"^        (\w+): \{", block, re.M))
        # `bahn_folgen` is the card the browser builds itself, so the catalogue
        # holds one key more than this module emits — never one less.
        assert set(RULE_IDS) <= keyed
