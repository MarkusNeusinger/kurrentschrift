"""The local Streifenkartei — one hand's manifest as a file.

``data/samples/own-hand/<hand>/kartei.json`` records what happened
physically: which Bogen were printed (with their layout hashes), which
Fassungen exist per Streifen (with verdicts, sessions and checksums), and
the redo queue. It is NEVER committed (reserved dataset).

The SHAPE and the rules read off it live in ``core.eigenhand.kartei`` —
derived strip states, id minting, accepted-Fassung selection — because the
API builds the same dict out of the ``eigenhand_*`` tables. This module is
only the file half: where it lives, and how it is read and written (atomic
tmp file + ``os.replace``; apply.py is idempotent on top of that). The pure
helpers are re-exported so the tool family keeps importing them from here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from core.eigenhand.kartei import (
    KARTEI_FORMAT,
    accepted_count,
    accepted_fassungen,
    empty_kartei,
    fassungen_of,
    next_fassung_id,
    next_sheet_id,
    printed_count,
    strip_state,
)
from tools.eigenhand.store import hand_dir, style_of_hand


__all__ = [
    "KARTEI_FORMAT",
    "accepted_count",
    "accepted_fassungen",
    "empty_kartei",
    "fassungen_of",
    "kartei_path",
    "load_kartei",
    "next_fassung_id",
    "next_sheet_id",
    "printed_count",
    "save_kartei",
    "strip_state",
]


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
    return empty_kartei(hand, style or style_of_hand(hand))


def save_kartei(hand: str, kartei: dict) -> Path:
    path = kartei_path(hand)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(kartei, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path
