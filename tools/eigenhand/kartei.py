"""The Streifenkartei — the local manifest of one hand, single state source.

``data/samples/own-hand/<hand>/kartei.json`` records what happened
physically: which Bogen were printed (with their layout hashes), which
Fassungen exist per Streifen (with verdicts, sessions and checksums), and
the redo queue. It is NEVER committed (reserved dataset) and NEVER holds a
stored strip status — a strip's state is derived from the facts so it
cannot drift:

* ``belegt``    — at least one ``angenommen`` Fassung (not withdrawn)
* ``unterwegs`` — printed more often than reviewed (a sheet is out)
* ``geplant``   — everything else (never printed, or all attempts rejected)

Writes are atomic (tmp file + ``os.replace``); apply.py is idempotent on
top of this.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from tools.eigenhand.store import hand_dir, style_of_hand


KARTEI_FORMAT = 1


def kartei_path(hand: str) -> Path:
    return hand_dir(hand) / "kartei.json"


def load_kartei(hand: str, style: str | None = None) -> dict:
    """Load the hand's Kartei, creating the empty structure on first use."""
    path = kartei_path(hand)
    if path.exists():
        kartei = json.loads(path.read_text(encoding="utf-8"))
        if kartei.get("format") != KARTEI_FORMAT:
            raise SystemExit(f"{path}: unsupported format {kartei.get('format')!r}")
        return kartei
    return {
        "format": KARTEI_FORMAT,
        "hand": hand,
        "style": style or style_of_hand(hand),
        "sheets": {},
        "strips": {},
        "redo": [],
    }


def save_kartei(hand: str, kartei: dict) -> Path:
    path = kartei_path(hand)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(kartei, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


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
