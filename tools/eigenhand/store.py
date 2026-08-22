"""Shared paths and constants of the Eigenhand tool family.

Everything the tools produce lives under the gitignored data root
``data/samples/own-hand/`` (bytes are the reserved own-hand dataset,
docs/proposals/eigenhand-erfassung.md §8) — overridable with the
``EIGENHAND_DATA`` environment variable so tests run against a tmp dir.
"""

from __future__ import annotations

import os
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


def hand_dir(hand: str) -> Path:
    return data_root() / hand


def universe_path() -> Path:
    """The local Übergangsraum weight table (derived from consult-only corpora)."""
    return data_root() / "universe" / "uebergangsraum.json"


def style_of_hand(hand: str) -> str:
    """Infer the style id from a `<schreiber>-<stil>` hand id."""
    for style in STYLE_IDS:
        if hand.endswith(f"-{style}"):
            return style
    raise SystemExit(f"hand id {hand!r} does not end in a known style ({', '.join(STYLE_IDS)}); pass --style")
