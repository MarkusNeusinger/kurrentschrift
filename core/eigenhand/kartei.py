"""The Kartei SHAPE — one hand's bookkeeping, and the rules read off it.

A Kartei says what happened physically: which Bögen were printed (with their
rows), which Fassungen exist per Streifen (with verdicts), and what is queued
for a redo. It never stores a strip's status — that is DERIVED here, so it
cannot drift from the facts:

* ``belegt``    — at least one ``angenommen`` Fassung (not withdrawn)
* ``unterwegs`` — printed more often than reviewed (a sheet is out)
* ``geplant``   — everything else (never printed, or all attempts rejected)

The shape is the seam between the two persistences: ``tools/eigenhand`` reads
and writes it as ``kartei.json`` in the local data root, the API builds the
same dict out of the ``eigenhand_sheets`` / ``eigenhand_fassungen`` tables.
Everything downstream — print queue, Bestand, reports — takes the dict and
therefore cannot tell the two apart.
"""

from __future__ import annotations


KARTEI_FORMAT = 1


def empty_kartei(hand: str, style: str) -> dict:
    return {"format": KARTEI_FORMAT, "hand": hand, "style": style, "sheets": {}, "strips": {}, "redo": []}


def next_sheet_id(kartei: dict) -> str:
    number = max((int(sid[1:]) for sid in kartei["sheets"]), default=0) + 1
    return f"B{number:04d}"


def next_fassung_id(kartei: dict, strip: str) -> str:
    fassungen = kartei["strips"].get(strip, {}).get("fassungen", [])
    number = max((int(f["id"][1:]) for f in fassungen), default=0) + 1
    return f"F{number:02d}"


def fassungen_of(kartei: dict, strip: str) -> list[dict]:
    return kartei["strips"].get(strip, {}).get("fassungen", [])


def printed_count(kartei: dict, strip: str) -> int:
    return sum(sheet["strips"].count(strip) for sheet in kartei["sheets"].values())


def strip_state(kartei: dict, strip: str) -> str:
    """Derived state — see module docstring; never stored."""
    if any(f["status"] == "angenommen" for f in fassungen_of(kartei, strip)):
        return "belegt"
    if printed_count(kartei, strip) > len(fassungen_of(kartei, strip)):
        return "unterwegs"
    return "geplant"


def accepted_fassungen(kartei: dict) -> list[tuple[str, dict]]:
    """Every (strip, fassung) that counts as training data right now."""
    out: list[tuple[str, dict]] = []
    for strip, record in sorted(kartei["strips"].items()):
        out.extend((strip, f) for f in record.get("fassungen", []) if f["status"] == "angenommen")
    return out


def accepted_count(kartei: dict, strip: str) -> int:
    """How often this strip exists as training data — the DB's one number per strip."""
    return sum(1 for f in fassungen_of(kartei, strip) if f["status"] == "angenommen")
