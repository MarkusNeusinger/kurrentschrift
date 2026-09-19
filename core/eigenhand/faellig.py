"""What is due AT THE MACHINE — the due list behind the Übergabekarte.

The capture chain has steps the browser cannot take: a scan lives on a disk,
the Siebung is a local page, the follower ships in ``tools/`` which the API
image does not carry. The plan's answer is to SHOW that break rather than hide
it (admin-redesign.md §5.1 Idee 11): a card per due step, with the command, and
gone again the moment the state is there.

This module is the one place that decides what „due" means. The admin view
renders the list and the terminal twin ``python -m tools.eigenhand.report
--faellig`` prints it, so the two surfaces cannot disagree — the same reason
``core.eigenhand.bestand`` exists.

Three properties the rules here are bound by:

* **Only what the SERVER sees.** A local snapshot, an ``ingest`` run or the
  local setup cache leave no trace in the DB (``EigenhandRepository.kartei``
  fills ``sheets[…]["scans"]`` with an empty list and ``redo`` with none), so
  no rule may depend on them. Where a card cannot be confirmed, it clears on
  the nearest thing the server DOES see, and its copy says so.
* **A card disappears.** A rule that can never clear is a permanent banner, and
  the plan's card is defined by going away („die verschwindet, sobald der
  Zustand da ist").
* **The command is code.** The strings are built here, in English, beside the
  rule that makes them due (§5.0: „Terminal-BEFEHLE bleiben englisch"). The
  German copy lives in the SPA's locale, keyed by the rule id, so an id this
  module does not emit renders no card at all.
* **No card copies a command that OVERWRITES.** Pushing what was written up is
  the chain's whole point, so a card may hand over a write — but the one
  eigenhand write that REPLACES an existing build is ``universe --push``
  (proposal §7.1: „der alte Bau … im DB-Snapshot davor archiviert"), and the
  one that replaces followed geometry is ``pfad --apply``. Both keep the
  snapshot in their order hint, and ``pfad`` hands over its dry run instead of
  ``--apply`` at all (author question Q9, 2026-09-19).

Phase 1 carries four rules. What is deliberately NOT here, with the reason:

* **„Bahnen fehlen" hand-wide** — needs to know which Fassung has a stored
  Streifen-Pfad. ``EigenhandRepository._STRIP_META_ONLY`` defers ``pfade``
  along with the PNG, so a listing cannot answer it and the only route that can
  is per Fassung (N+1 requests). Waits for the meta-only read (plan V5, phase
  2); until then the per-Fassung card is built in the SPA, where the path of
  the open Fassung is already loaded.
* **„Maske geändert"** — the same read, plus a comparison of the Fleckenmaske a
  path was followed under against the one the strip carries now.
* **``redo``** — ``repo.kartei`` initialises ``"redo": []`` and never fills it:
  the redo queue exists only in the local ``kartei.json``. A card for it would
  be permanently empty on the server and permanently wrong locally, so it waits
  for the queue to reach the DB.
* **``ingest``/``apply``/snapshot** — local by construction: the scan path is
  not knowable here, and the archive is not a thing the server can see at all
  (plan §9.2: „lokale Schritte kann sie nicht bestätigen"). They appear as the
  ORDER HINT of the card that precedes them, never as a card of their own.
* **``setup --pull`` on a SECOND writing machine** and **retiring a spoiled
  Bogen** — both are states the server cannot tell apart from the one it
  already shows; the two rules below say where each stops.
"""

from __future__ import annotations

from core.eigenhand.kartei import accepted_fassungen


# One rule id per card, in the order the chain runs them: the equipment before
# the first session, the Soll before a Bogen is chosen (the print queue ranks by
# weighted Soll gain), then the outstanding Bogen, then what the writing left
# behind. `report --faellig` prints them in this order for the same reason the
# view lists them in it — it is the order they are meant to be done in.
SETUP_PULL = "setup_pull"
UNIVERSE_PUSH = "universe_push"
BOGEN_PULL = "bogen_pull"
SYNC_STREIFEN = "sync_streifen"

# The ids this module can emit, in chain order. The SPA keeps the same list
# (`sections/admin/eigenhand/uebergabe.ts`) and is pinned to it by its own test:
# a card without German copy would render blank, and an id without a rule would
# be copy nobody can reach.
RULE_IDS = (SETUP_PULL, UNIVERSE_PUSH, BOGEN_PULL, SYNC_STREIFEN)

_RUN = "uv run python -m tools.eigenhand"

# How many further outstanding Bögen the card spells out before it says „…".
# A print job takes up to 20 sheets, and a list that long stops being readable.
_WEITERE_NAMED = 6


def _fassungen(kartei: dict) -> list[dict]:
    return [f for record in kartei["strips"].values() for f in record.get("fassungen", [])]


def _outstanding_sheets(kartei: dict) -> list[tuple[str, int]]:
    """Every Bogen with printed rows nobody has judged yet, oldest first.

    Sheet ids are minted in print order (``B0001`` …), so sorting by id is
    sorting by age. The card names the OLDEST, not ``bestand["sheets"]["last"]``
    (the newest printed one), because a stack printed in one job leaves several
    outstanding at once and the sheet lying around longest is the one to clear.
    The REST are named too, for the case that makes the difference visible: a
    spoiled sheet nobody will ever write stays outstanding — no route retires a
    Bogen, and the print queue deliberately ignores outstanding ones — and would
    otherwise hide the Bogen just printed behind itself. It clears the way every
    other one does, by its rows being judged; a ``verworfen`` Fassung counts, so
    a spoiled sheet is closed by filing it as spoiled. A retire path is phase 2.
    """
    judged: dict[str, int] = {}
    for fassung in _fassungen(kartei):
        sheet = fassung.get("sheet")
        if sheet:
            judged[sheet] = judged.get(sheet, 0) + 1
    outstanding = []
    for sheet in sorted(kartei["sheets"]):
        printed = len(kartei["sheets"][sheet]["strips"])
        offen = printed - judged.get(sheet, 0)
        if offen > 0:
            outstanding.append((sheet, offen))
    return outstanding


def faellig(kartei: dict, *, setup: bool, stored: set[tuple[str, str]], soll: bool) -> list[dict]:
    """The due local steps of one hand, in chain order.

    Pure: a Kartei-shaped dict plus three facts the caller reads off its own
    persistence — whether a standing setup row exists, which ``(strip,
    fassung)`` pairs have a stored Streifen image, and whether the Übergangsraum
    table is there. Each entry is ``{"id", "befehl", "params"}``; the caller
    turns the id into copy.
    """
    hand = kartei["hand"]
    due: list[dict] = []

    # The standing setup is typed in the browser and read back LOCALLY by
    # `ingest`, so it has to be pulled once per writing machine. The server
    # cannot see that cache — what it can see is whether anything has been
    # written under this hand at all, which is why the card is bound to the
    # first Fassung: it appears once a setup is saved for a hand that has not
    # written yet, and clears when the first Fassung arrives. Two cases this
    # cannot see, both phase 2: a setup CHANGED mid-campaign (it would need the
    # Fassung's own effective values compared against the standing row), and a
    # SECOND writing machine set up once the hand has already written — the
    # server sees one hand, not the machines, so that one stays documented
    # (`werkzeuge.md`, `setup --help`) rather than shown as a card that could
    # never go away again.
    if setup and not _fassungen(kartei):
        due.append({"id": SETUP_PULL, "befehl": f"{_RUN}.setup --hand {hand} --pull", "params": {"hand": hand}})

    # No weight table, no Quoten — and the print queue falls back to an
    # unweighted order. The corpora stay local (licence), the derived table is
    # what travels.
    if not soll:
        due.append({"id": UNIVERSE_PUSH, "befehl": f"{_RUN}.universe --push", "params": {"hand": hand}})

    outstanding = _outstanding_sheets(kartei)
    if outstanding:
        sheet, offen = outstanding[0]
        # One card, the oldest sheet's command — `pull` takes one `--sheet` and
        # a stack of up to 20 would otherwise be 20 cards. The others are NAMED
        # instead, because the failure of naming only the oldest is that the
        # Bogen just printed is invisible while an abandoned one sits in front
        # of it, and the copy button then hands over the wrong `--sheet`.
        weitere = [rest for rest, _offen in outstanding[1:]]
        params: dict[str, str | int] = {"hand": hand, "sheet": sheet, "offen": offen, "weitere": len(weitere)}
        if weitere:
            named = weitere[:_WEITERE_NAMED]
            params["weitere_boegen"] = " · ".join(named) + (" …" if len(weitere) > len(named) else "")
        due.append({"id": BOGEN_PULL, "befehl": f"{_RUN}.pull --hand {hand} --sheet {sheet}", "params": params})

    # An accepted Fassung whose image never came up. The count is the honest
    # trigger: the all-or-nothing „no strips at all" the strips panel used could
    # not say „4 of 37".
    ohne_bild = sum(1 for strip, fassung in accepted_fassungen(kartei) if (strip, fassung["id"]) not in stored)
    if ohne_bild:
        due.append(
            {
                "id": SYNC_STREIFEN,
                "befehl": f"{_RUN}.sync --hand {hand} --mit-streifen",
                "params": {"hand": hand, "ohne_bild": ohne_bild},
            }
        )

    return due
