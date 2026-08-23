"""Shared paths and constants of the Eigenhand tool family.

The captured material — sheets, scans, Fassungen, the Kartei, the local
weight table — lives under the gitignored data root
``data/samples/own-hand/`` (bytes are the reserved own-hand dataset,
docs/proposals/eigenhand-erfassung.md §8), overridable with the
``EIGENHAND_DATA`` environment variable so tests run against a tmp dir. The
one produced artefact that is COMMITTED is the strip plan
(``STREIFEN_JSON``), which sits next to this code: it is the frozen,
append-only output the whole chain reproduces against.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from core.config import REPO_ROOT


# The known style ids (styles table seed, migration 0004) — a hand id is
# `<schreiber>-<stil>` and the style is inferred from its suffix.
STYLE_IDS = ("kurrent", "suetterlin", "offenbacher")

STREIFEN_JSON = Path(__file__).resolve().parent / "streifen.json"
CORPORA_DIR = REPO_ROOT / "data" / "corpora" / "frequencywords-2018"


def data_root() -> Path:
    """The local own-hand data root (gitignored; env-overridable for tests)."""
    override = os.environ.get("EIGENHAND_DATA")
    return Path(override) if override else REPO_ROOT / "data" / "samples" / "own-hand"


# A hand id is a plain `<schreiber>-<stil>` name: lowercase ASCII, digits and
# dashes, ending in a KNOWN style. Everything under the data root is addressed
# through it, so a value carrying path components (or an absolute path) would
# let a typo — or a tampered Kartei — write outside the gitignored reserved
# tree. Requiring the style suffix here also stops a misspelled style
# (`mn-suetterln`) from silently creating a directory for a hand that
# style_of_hand() will later refuse to interpret.
#
# All three guards in this module match with `fullmatch`: `$` also matches
# BEFORE a trailing newline, so `re.match("...$", "mn-suetterlin\n")` succeeds
# and a value read from a file with its line ending still attached would pass.
_HAND_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*-(?:" + "|".join(STYLE_IDS) + r")")


def check_hand_id(hand: str) -> str:
    """Return the hand id, or refuse it if it is not a plain `<schreiber>-<stil>` name."""
    if not _HAND_ID.fullmatch(hand):
        raise SystemExit(
            f"hand id {hand!r} must be a plain `<schreiber>-<stil>` name (lowercase ASCII, "
            f"digits and dashes) ending in a known style ({', '.join(STYLE_IDS)}), e.g. mn-suetterlin"
        )
    return hand


def hand_dir(hand: str) -> Path:
    return data_root() / check_hand_id(hand)


def crop_name(row_index: int) -> str:
    """The file name of one row crop — the single definition of that shape.

    ingest.py writes it, page.py and apply.py read it back. Keeping it in one
    place is what lets the readers VERIFY the payload instead of trusting it.
    """
    return f"row-{row_index:02d}.png"


# A Bogen id is what kartei.next_sheet_id() mints: `B` plus a zero-padded
# number. It reaches the CLIs as `--sheet` and is interpolated into paths in
# ingest, page and apply, so it needs the same guard as the hand id and the
# crop name — a mistyped or tampered value with path components would read and
# write outside `<hand>/blaetter/`. `[0-9]` rather than `\d`, which also
# matches non-ASCII digits — `B٠٠٠١` is not a path escape, but it is not an id
# next_sheet_id() can ever count on either.
_SHEET_ID = re.compile(r"B[0-9]{4,}")


def check_sheet_id(sheet: str) -> str:
    """Return the sheet id, or refuse anything that is not a plain `B<nnnn>`."""
    if not _SHEET_ID.fullmatch(sheet):
        raise SystemExit(f"sheet id {sheet!r} must be a plain `B<nnnn>` name, e.g. B0001")
    return sheet


def sheet_dir(hand: str, sheet: str) -> Path:
    """The Bogen directory — both parts of the path checked in one place."""
    return hand_dir(hand) / "blaetter" / check_sheet_id(sheet)


def check_crop_name(crop: str, row_index: int) -> str:
    """Return the crop name, or refuse anything that is not THIS row's crop.

    ``payload.json`` names the row crops, and both readers turn that field
    into a path — page.py embeds the file, apply.py copies it into the
    reserved dataset. Deriving the expected name from the row index leaves a
    tampered (or simply buggy) payload nothing to aim at: not another
    directory, and not the sheet's own page.png or header.png, which must
    never become dataset files. Same doctrine as the public crop endpoint's
    `page` field (core/chart.py::load_word_samples).
    """
    expected = crop_name(row_index)
    if crop != expected:
        raise SystemExit(f"payload crop {crop!r} is not row {row_index}'s crop {expected!r} — refusing")
    return crop


def universe_path() -> Path:
    """The local Übergangsraum weight table (derived from consult-only corpora)."""
    return data_root() / "universe" / "uebergangsraum.json"


def style_of_hand(hand: str) -> str:
    """Infer the style id from a `<schreiber>-<stil>` hand id."""
    for style in STYLE_IDS:
        if hand.endswith(f"-{style}"):
            return style
    raise SystemExit(
        f"hand id {hand!r} must follow the `<schreiber>-<stil>` convention with a known style suffix "
        f"({', '.join(STYLE_IDS)}), e.g. mn-suetterlin — sheet.py additionally accepts --style as an override"
    )
