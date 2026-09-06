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
"""

from __future__ import annotations

import json
from pathlib import Path


PLAN_FORMAT = 2

# Next to this module, so it ships wherever core ships (the API image copies
# `core/` wholesale — a plan the server cannot read is a Bogen it cannot print).
STREIFEN_JSON = Path(__file__).resolve().parent / "streifen.json"


def load_plan(path: Path | None = None) -> dict:
    target = path or STREIFEN_JSON
    plan = json.loads(target.read_text(encoding="utf-8"))
    if plan.get("format") != PLAN_FORMAT:
        raise SystemExit(f"{target}: unsupported format {plan.get('format')!r}")
    return plan


def dump_plan(plan: dict) -> str:
    return json.dumps(plan, ensure_ascii=False, indent=1) + "\n"


def empty_plan() -> dict:
    return {"format": PLAN_FORMAT, "waves": [], "strips": {}, "forms": {}, "pins": []}


def strip_id(number: int) -> str:
    return f"S{number:04d}"


def pinned_strips(plan: dict) -> list[str]:
    """The strips that lead the plan, in the order they were pinned."""
    return [sid for sid in plan.get("pins", []) if sid in plan["strips"]]


def ordered_strips(plan: dict) -> list[str]:
    """Strip ids in plan order — the order the print queue and the progression use.

    Pinned strips first (in pin order), then every other strip ascending. The
    pin is expressed HERE rather than in the print queue so that every reader
    of the plan agrees on what comes first: the queue, the coverage
    progression and the Bestand all walk this one order.
    """
    pinned = pinned_strips(plan)
    rest = sorted((sid for sid in plan["strips"] if sid not in set(pinned)), key=lambda sid: int(sid[1:]))
    return pinned + rest


def forms_of(plan: dict) -> dict[str, str]:
    """word → the form to shape: the Fugen-marked one where the plan carries it."""
    return dict(plan.get("forms", {}))


def shaping_form_of(plan: dict, word: str) -> str:
    return plan.get("forms", {}).get(word, word)


def words_of(plan: dict, strip: str) -> list[str]:
    return list(plan["strips"][strip]["words"])
