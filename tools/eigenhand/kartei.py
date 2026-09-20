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

ONE field is local-only and has no twin on the server: ``fassung["pfade"]``,
the hand-drawn Bahnen ``tools.eigenhand.pull --pfade`` brings DOWN out of the
shared database (author decision A, 2026-09-20). It rides in the Kartei rather
than in the Fassung directory because ``snapshot.py`` copies the Kartei in FULL
on every run while a filed Fassung directory is an immutable copy unit it skips
by relative path — a file written into an already-archived Fassung would never
reach the archive, and the run would still report success. The Fleckenmaske
takes the same route for the same reason. The record carries its own format
version so a later reader can tell what it is holding, and the wire format the
API declared the entries under beside it.
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
    "PFAD_ARCHIVE_FORMAT",
    "accepted_count",
    "accepted_fassungen",
    "archived_pfade",
    "empty_kartei",
    "fassung_record",
    "fassungen_of",
    "kartei_path",
    "load_kartei",
    "next_fassung_id",
    "next_sheet_id",
    "pfad_record",
    "pfad_wire_format",
    "pfade_of",
    "printed_count",
    "save_kartei",
    "strip_state",
]


# The Kartei's own envelope around a pulled hand-drawn Bahn — versioned apart
# from KARTEI_FORMAT on purpose. Bumping the Kartei's version would make every
# older tool refuse the whole file (`load_kartei` below); this record is purely
# additive, so an older tool simply does not see it, while a reader that DOES
# look can tell which shape it is holding.
PFAD_ARCHIVE_FORMAT = 1


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


def fassung_record(kartei: dict, strip: str, fassung: str) -> dict | None:
    """One Fassung's Kartei row, or None where this machine does not know it."""
    for record in kartei.get("strips", {}).get(strip, {}).get("fassungen", []):
        if record.get("id") == fassung:
            return record
    return None


def pfad_record(entries: list[dict], pfad_format: int, pulled_on: str) -> dict:
    """The Kartei envelope around the hand-drawn Bahnen of one Fassung.

    ``pfad_format`` is the API's own ``PFAD_FORMAT`` as it answered with it,
    not this file's version: the two move independently, and a restore has to
    declare the entries under the format they were written in.
    """
    return {
        "format": PFAD_ARCHIVE_FORMAT,
        "pfad_format": int(pfad_format),
        "pulled_on": pulled_on,
        "entries": [dict(entry) for entry in entries],
    }


def pfade_of(fassung: dict) -> list[dict]:
    """The hand-drawn Bahnen this machine has pulled for one Fassung.

    A record in an unknown shape is REFUSED rather than read as empty: the
    whole point of the version is that a reader knows what it is holding, and
    „no Bahn here" is the one answer a restore must not be given wrongly.
    """
    record = fassung.get("pfade")
    if record is None:
        return []
    if not isinstance(record, dict):
        raise SystemExit(f"Kartei: `pfade` of Fassung {fassung.get('id')!r} is not a record — refusing to read it")
    if record.get("format") != PFAD_ARCHIVE_FORMAT:
        raise SystemExit(
            f"Kartei: Fassung {fassung.get('id')!r} carries Bahnen in archive format "
            f"{record.get('format')!r}, this tool reads {PFAD_ARCHIVE_FORMAT} — update the tools before reading it"
        )
    entries = record.get("entries")
    if not isinstance(entries, list):
        return []
    for entry in entries:
        index = entry.get("box_index") if isinstance(entry, dict) else None
        if not isinstance(index, int) or isinstance(index, bool):
            raise SystemExit(
                f"Kartei: a Bahn of Fassung {fassung.get('id')!r} names no word box — refusing to read the record"
            )
    return list(entries)


def pfad_wire_format(fassung: dict) -> int:
    """The API format the pulled Bahnen of one Fassung were answered under.

    Separate from `PFAD_ARCHIVE_FORMAT`: the envelope's version says how to
    READ this file, this one says what the entries inside it mean — and a
    restore has to declare it back to the API it pushes them to.
    """
    declared = (fassung.get("pfade") or {}).get("pfad_format")
    if not isinstance(declared, int) or isinstance(declared, bool):
        raise SystemExit(
            f"Kartei: the Bahnen of Fassung {fassung.get('id')!r} declare no Streifen-Pfad format "
            f"({declared!r}) — pull them again before restoring them"
        )
    return declared


def archived_pfade(kartei: dict, strip: str, fassung: str) -> dict[int, dict]:
    """The pulled hand-drawn Bahnen of one Fassung, by box index.

    What `--replace-authored` is held against: a box whose drawing exists
    nowhere but in the database is not one the terminal may give up
    (author decision B, 2026-09-20).
    """
    record = fassung_record(kartei, strip, fassung)
    return {} if record is None else {entry["box_index"]: entry for entry in pfade_of(record)}
