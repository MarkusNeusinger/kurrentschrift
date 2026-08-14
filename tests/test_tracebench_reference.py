"""Tests for the reference loader (`tools.tracebench.reference`).

The loader is where a bench run can lose a word without anyone noticing, so
every test here is about what it REFUSES and how loudly: a `frame_stale` row is
excluded and counted, a row without a frozen entry the same, and the two
provenances stay separable because the run — not the loader — decides which one
is the ruler and which one the candidate.

Everything is built in `tmp_path` from plain dicts: no fixtures, no DB, no
network, so these run in CI where the real fixture roots are gitignored.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from tools.tracebench.reference import (
    EXCLUDED_FRAME_STALE,
    EXCLUDED_NO_ENTRY,
    EXCLUDED_NO_REGISTRATION,
    EXCLUDED_NO_STROKES,
    load_reference,
)


ENTRY = {"rect": [100, 200, 260, 300], "baseline_y": 270, "midband_y": 240}
STROKES = [[[0.1, 0.1], [0.6, 0.9], [1.2, 0.2]]]
MEASUREMENTS = {"registration_px": {"tx": 4.0, "ty": 0.0, "baseline_row": 70}, "xh_px": 30.0}


def write_entry(root: Path, entry_id: str, *, slots: list[str] | None = None) -> None:
    """One frozen fixture entry: `word.json` plus a small ink mask."""
    directory = root / entry_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "word.json").write_text(
        json.dumps(
            {
                "id": entry_id,
                "word": entry_id,
                "kind": "word",
                "slots": [{"key": k} for k in (slots or list(entry_id))],
                "scorable": True,
                **ENTRY,
            }
        )
    )
    mask = np.zeros((100, 160), dtype=bool)
    mask[60:70, 10:80] = True
    Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(directory / "ref_mask.png")


def row(entry_id: str, provenance: str = "authored", **extra) -> dict:
    return {
        "kind": "word",
        "specimen_id": entry_id,
        "word": entry_id,
        "slots": list(entry_id),
        "provenance": provenance,
        "strokes": STROKES,
        "measurements": dict(MEASUREMENTS),
        **extra,
    }


def write_root(tmp_path: Path, rows: list[dict], *, order: list[str] | None = None, entries: list[str] | None = None):
    root = tmp_path / "root"
    root.mkdir(parents=True, exist_ok=True)
    for entry_id in entries if entries is not None else [r["specimen_id"] for r in rows]:
        write_entry(root, entry_id)
    ids = order if order is not None else [r["specimen_id"] for r in rows]
    (root / "manifest.json").write_text(json.dumps({"set": "words", "words": [{"id": i, "word": i} for i in ids]}))
    (root / "word_instances.json").write_text(json.dumps({"hand_id": "a-hand", "rows": rows}))
    return root


# ------------------------------------------------------------------- loading


def test_a_root_loads_its_rows_with_frame_and_hand(tmp_path: Path) -> None:
    reference = load_reference(write_root(tmp_path, [row("die"), row("mit", "traced")]))
    assert reference.hand_id == "a-hand"
    assert set(reference.entries) == {"die", "mit"}
    frame = reference.entries["die"].frame
    assert frame.xh == 30.0  # baseline_y - midband_y
    assert frame.baseline_row == 70.0  # baseline_y - rect[1]
    assert reference.entries["die"].slots == ["d", "i", "e"]


def test_rows_come_back_in_manifest_order(tmp_path: Path) -> None:
    """The bench iterates in a fixed order — a report must be diffable."""
    root = write_root(tmp_path, [row("zwei"), row("die"), row("mit")], order=["die", "mit", "zwei"])
    assert load_reference(root).ids() == ["die", "mit", "zwei"]


def test_the_ink_mask_is_boolean_and_read_only_on_demand(tmp_path: Path) -> None:
    entry = load_reference(write_root(tmp_path, [row("die")])).entries["die"]
    assert entry._mask is None  # nothing decoded while only the frame was needed
    mask = entry.ink_mask()
    assert mask.dtype == np.bool_ and mask.any()
    assert entry.ink_mask() is mask  # kept, not re-decoded per column


def test_a_root_without_the_artifact_says_how_to_refill_it(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()
    with pytest.raises(FileNotFoundError, match="word_instances"):
        load_reference(root)


# ------------------------------------------------------- excluded, and counted


def test_a_frame_stale_row_is_never_scored_but_always_counted(tmp_path: Path) -> None:
    """The #334/#336 class: a rect edited under a stored trace.

    Stage A stamps the reason instead of dropping the row, and the bench must
    keep that promise — a silently missing word makes the remaining ones look
    better than the set is.
    """
    root = write_root(tmp_path, [row("die"), row("ein", frame_stale="baseline_row 61 vs expected 70±4")])
    reference = load_reference(root)
    assert set(reference.entries) == {"die"}
    assert reference.excluded[EXCLUDED_FRAME_STALE] == ["ein"]
    assert reference.excluded_counts() == {EXCLUDED_FRAME_STALE: 1}


def test_a_row_without_a_frozen_entry_is_excluded_by_its_own_reason(tmp_path: Path) -> None:
    root = write_root(tmp_path, [row("die"), row("ghost")], entries=["die"])
    reference = load_reference(root)
    assert set(reference.entries) == {"die"}
    assert reference.excluded[EXCLUDED_NO_ENTRY] == ["ghost"]


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ({"strokes": []}, EXCLUDED_NO_STROKES),
        ({"measurements": {"xh_px": 30.0}}, EXCLUDED_NO_REGISTRATION),
        ({"measurements": {"registration_px": {"baseline_row": 70}}}, EXCLUDED_NO_REGISTRATION),
    ],
)
def test_a_row_the_frame_cannot_place_is_excluded(tmp_path: Path, mutation: dict, reason: str) -> None:
    """Without a registration and an x-height the strokes are numbers, not a path."""
    reference = load_reference(write_root(tmp_path, [row("die", **mutation)]))
    assert not reference.entries
    assert reference.excluded[reason] == ["die"]


# ------------------------------------------------------------- the provenances


def test_authored_and_traced_stay_separable(tmp_path: Path) -> None:
    """The loader keeps both; the RUN decides which is the ruler (§2.4).

    A specimen holds exactly one stored row, so the two sets are disjoint by
    construction — which is why the ten hand-traced development words have no
    `traced` candidate to read and the chain baseline is recomputed instead.
    """
    root = write_root(tmp_path, [row("die"), row("mit", "traced"), row("und")], order=["die", "mit", "und"])
    reference = load_reference(root)
    assert reference.authored_ids() == ["die", "und"]
    assert reference.traced_ids() == ["mit"]
    assert reference.ids() == ["die", "mit", "und"]
    assert not set(reference.authored_ids()) & set(reference.traced_ids())
