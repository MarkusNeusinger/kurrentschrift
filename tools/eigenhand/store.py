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
# dashes. Everything under the data root is addressed through it, so a value
# carrying path components (or an absolute path) would let a typo — or a
# tampered Kartei — write outside the gitignored reserved tree.
_HAND_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+$")


def check_hand_id(hand: str) -> str:
    """Return the hand id, or refuse it if it is not a plain `<schreiber>-<stil>` name."""
    if not _HAND_ID.match(hand):
        raise SystemExit(
            f"hand id {hand!r} must be a plain `<schreiber>-<stil>` name (lowercase ASCII, "
            "digits and dashes), e.g. mn-suetterlin"
        )
    return hand


def hand_dir(hand: str) -> Path:
    return data_root() / check_hand_id(hand)


def check_crop_name(crop: str) -> str:
    """Return the crop file name, or refuse it if it carries path components.

    ``payload.json`` names the row crops, and both readers of that field turn
    the name into a path — page.py embeds the file, apply.py copies it into
    the reserved dataset. A tampered (or simply buggy) payload must not be
    able to reach outside the sheet's own import directory. Same guard as the
    public crop endpoint's `page` field (core/chart.py::load_word_samples).
    """
    if Path(crop).name != crop:
        raise SystemExit(f"payload crop {crop!r} carries path components — refusing")
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
