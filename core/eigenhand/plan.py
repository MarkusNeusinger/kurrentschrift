"""The Streifenplan — the frozen, committed strip → words directory.

``streifen.json`` is the reproducibility anchor of the whole capture chain:
strip ids are assigned once and never renumbered (append-never, enforced by
the builder in ``tools/eigenhand/pool.py``), so a strip id means the same
words forever — on the sheet, in the Kartei, in the DB and in the Bestand.

It lives in ``core`` because the server reads it: the Bogen printer and the
Bestand both resolve strip ids to words, and both now run behind the API as
well as in the terminal. ``forms`` carries the shaping form of every word that
has one (``Amts|zeit`` for ``Amtszeit``) — without it the plan alone could not
be shaped correctly and every reader would need the curation source in
``tools/eigenhand/corpus.py``, which is exactly the dependency the API must
not have.

``pins`` names strips that are written FIRST, whatever their number: plan
order is pinned strips, then the rest ascending. It is the one way a word can
reach the top of the print queue after the plan is frozen — the strips
themselves stay untouchable, a pin only appends its own strip and says it
leads (``tools.eigenhand.pool pin``, proposal §4). An optional, additive
block: a plan without it reads exactly as before, which is why the format
number stays 2.

``alltag`` names the Grundwortschatz strips, and they do not lead — they
INTERLEAVE. The coverage builder rewards long words (a word's benefit grows
with the joins it carries), so the frozen head of the plan is compounds and
loanwords while ``ich``, ``ist`` and ``und`` went unplanned; the everyday
words were appended as their own wave to repair that. Putting them all in
front would only move the wall, so plan order alternates them with the frozen
strips (owner decision 2026-09-21) and every printed Bogen carries both.
Additive like ``pins`` for the same reason, and the format stays 2.
"""

from __future__ import annotations

import json
from pathlib import Path


PLAN_FORMAT = 2

# Next to this module, so it ships wherever core ships (the API image copies
# `core/` wholesale — a plan the server cannot read is a Bogen it cannot print).
STREIFEN_JSON = Path(__file__).resolve().parent / "streifen.json"

# How many everyday rows and how many frozen rows alternate in plan order
# (owner decision 2026-09-21: "gemischt, feste Quote je Bogen"). A Bogen holds
# seven rows, so 5 + 2 means every sheet is mostly easy and still moves the
# coverage work along — and the 77 Grundwortschatz strips stretch across
# about 15 sheets instead of filling eleven with nothing else.
ALLTAG_PATTERN = (5, 2)


def load_plan(path: Path | None = None) -> dict:
    target = path or STREIFEN_JSON
    plan = json.loads(target.read_text(encoding="utf-8"))
    if plan.get("format") != PLAN_FORMAT:
        raise SystemExit(f"{target}: unsupported format {plan.get('format')!r}")
    return plan


def dump_plan(plan: dict) -> str:
    return json.dumps(plan, ensure_ascii=False, indent=1) + "\n"


def empty_plan() -> dict:
    return {"format": PLAN_FORMAT, "waves": [], "strips": {}, "forms": {}, "pins": [], "alltag": []}


def strip_id(number: int) -> str:
    return f"S{number:04d}"


def pinned_strips(plan: dict) -> list[str]:
    """The strips that lead the plan, in the order they were pinned."""
    return [sid for sid in plan.get("pins", []) if sid in plan["strips"]]


def alltag_strips(plan: dict) -> list[str]:
    """The Grundwortschatz strips, in the order the everyday wave built them."""
    pinned = set(plan.get("pins", []))
    return [sid for sid in plan.get("alltag", []) if sid in plan["strips"] and sid not in pinned]


def _interleave(lead: list[str], rest: list[str], pattern: tuple[int, int]) -> list[str]:
    """Alternate two ordered lists in ``pattern`` chunks, keeping both orders.

    Whichever list runs out first simply stops contributing; the other streams
    on in its own chunks, which is the same sequence it would have had alone.
    """
    take_lead, take_rest = pattern
    if take_lead + take_rest <= 0:
        raise ValueError(f"ALLTAG_PATTERN must take something: {pattern!r}")
    out: list[str] = []
    i = j = 0
    while i < len(lead) or j < len(rest):
        out += lead[i : i + take_lead]
        i += take_lead
        out += rest[j : j + take_rest]
        j += take_rest
    return out


def ordered_strips(plan: dict) -> list[str]:
    """Strip ids in plan order — the order the print queue and the progression use.

    Pinned strips first (in pin order), then the Grundwortschatz strips and the
    remaining ones alternating in ``ALLTAG_PATTERN`` chunks. Ordering is
    expressed HERE rather than in the print queue so that every reader of the
    plan agrees on what comes first: the queue, the coverage progression and
    the Bestand all walk this one order.

    The queue drops strips that are already written, so the ratio a printed
    Bogen ends up with drifts from the pattern once writing runs ahead in one
    of the two lists. That is deliberate: the pattern shapes the PLAN, and the
    sheet takes the first unwritten rows of it.
    """
    pinned = pinned_strips(plan)
    led = set(pinned)
    alltag = [sid for sid in alltag_strips(plan) if sid not in led]
    spoken_for = led | set(alltag)
    rest = sorted((sid for sid in plan["strips"] if sid not in spoken_for), key=lambda sid: int(sid[1:]))
    return pinned + _interleave(alltag, rest, ALLTAG_PATTERN)


def forms_of(plan: dict) -> dict[str, str]:
    """word → the form to shape: the Fugen-marked one where the plan carries it."""
    return dict(plan.get("forms", {}))


def shaping_form_of(plan: dict, word: str) -> str:
    return plan.get("forms", {}).get(word, word)


def words_of(plan: dict, strip: str) -> list[str]:
    return list(plan["strips"][strip]["words"])
