"""The reference side of the bench: frozen entries + the traces stored over them.

Stage A froze the stored word traces beside the specimens they were drawn over
(`word_instances.json`, one row per `(kind, specimen_id)`, with the frame gate's
`frame_stale` stamp on a row whose registration no longer describes its rect).
This module turns that artifact plus the per-entry `word.json` into the objects
the ruler is fed: one `BenchFrame` per entry, the row's own strokes, and the ink
mask the AIoU column grades against — loaded lazily, because a run over ten
words must not read sixty-three PNGs.

Two rules that are not defaults but doctrine:

* **Excluded-and-counted** (the `pairmeas` doctrine). A `frame_stale` row is
  never scored, and a row whose specimen has no frozen entry cannot be scored at
  all — both are counted by reason in `Reference.excluded` rather than dropped
  in silence. A ruler that quietly loses a word reports a better number for it.
* **Provenance is the CALLER's filter.** The loader keeps `authored` and
  `traced` rows side by side; which one is the reference and which one is a
  candidate is a decision of the run (`--candidate`), not of the loader. The
  bench's reference is `authored` — the manually re-traced ground truth — and
  the same artifact supplies the `traced` harvest rows as a candidate.

No DB, no API, no writes: everything here comes out of the frozen fixture root.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from tools.tracebench.frames import BenchFrame


# Where the frozen fixture roots live: the WORDBENCH's own export directory,
# because the trace bench draws over exactly the crops the word bench scores
# against (one export, one frozen population). `tests/test_lab_fixture_wiring.py`
# pins this against `tools.wordbench.export_fixtures.DEFAULT_OUT_DIR`.
DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parents[1] / "wordbench" / "fixtures"

# The frozen artifact names. `word_instances.json` is pinned on BOTH sides —
# here and in `tools/wordbench/export_fixtures.py` — by
# `tests/test_lab_fixture_wiring.py`, so a rename on either end fails a test
# instead of turning every tracebench run into "no rows found".
WORD_INSTANCES_FILE = "word_instances.json"
ENTRY_FILE = "word.json"
INK_MASK_FILE = "ref_mask.png"
MANIFEST_FILE = "manifest.json"

# Exclusion reasons, named once so the report and the tests speak one vocabulary.
EXCLUDED_FRAME_STALE = "frame_stale"
EXCLUDED_NO_ENTRY = "no_entry"
EXCLUDED_NO_REGISTRATION = "no_registration"
EXCLUDED_NO_STROKES = "no_strokes"


@dataclass(frozen=True)
class ReferenceRow:
    """One stored `word_instances` row, as the artifact holds it."""

    specimen_id: str
    kind: str
    word: str
    slots: list[str]
    provenance: str
    strokes: list[list[list[float]]]
    registration_px: dict[str, Any]
    xh_px: float | None
    fit_path: str | None = None


@dataclass
class ReferenceEntry:
    """One scoreable specimen: its frozen entry, its bench frame and its trace.

    The ink mask is read on first use and kept — a candidate and its reference
    are scored on the same entry, and re-decoding the PNG per column would cost
    the run more than the whole DTW does.
    """

    specimen_id: str
    entry: dict[str, Any]  # the frozen `word.json`
    frame: BenchFrame
    row: ReferenceRow
    directory: Path
    _mask: np.ndarray | None = field(default=None, repr=False, compare=False)

    @property
    def word(self) -> str:
        return str(self.entry.get("word", self.row.word))

    @property
    def kind(self) -> str:
        return str(self.entry.get("kind", self.row.kind))

    @property
    def slots(self) -> list[str]:
        """The frozen slot keys — the shaping the export pinned, not today's."""
        return [str(s.get("key")) for s in self.entry.get("slots", []) if s.get("key")]

    def ink_mask(self) -> np.ndarray:
        """The frozen binarised ink of this crop as a boolean image."""
        if self._mask is None:
            with Image.open(self.directory / INK_MASK_FILE) as img:
                self._mask = np.asarray(img.convert("L")) > 127
        return self._mask


@dataclass(frozen=True)
class Reference:
    """Everything one fixture root offers the bench."""

    root: Path
    hand_id: str | None
    entries: dict[str, ReferenceEntry]
    order: list[str]  # manifest order — the bench's iteration order
    excluded: dict[str, list[str]] = field(default_factory=dict)

    def ids(self, provenance: str | None = None) -> list[str]:
        """Scoreable specimen ids in manifest order, optionally by provenance."""
        return [i for i in self.order if provenance is None or self.entries[i].row.provenance == provenance]

    def authored_ids(self) -> list[str]:
        """The manually re-traced rows — the bench's ground truth (§2.4)."""
        return self.ids("authored")

    def traced_ids(self) -> list[str]:
        return self.ids("traced")

    def excluded_counts(self) -> dict[str, int]:
        return {reason: len(ids) for reason, ids in sorted(self.excluded.items())}


def _row_from(raw: dict[str, Any]) -> ReferenceRow:
    measurements = raw.get("measurements") or {}
    xh = measurements.get("xh_px")
    return ReferenceRow(
        specimen_id=str(raw.get("specimen_id", "")),
        kind=str(raw.get("kind", "word")),
        word=str(raw.get("word", "")),
        slots=[str(s) for s in raw.get("slots", [])],
        provenance=str(raw.get("provenance", "")),
        strokes=raw.get("strokes") or [],
        registration_px=dict(measurements.get("registration_px") or {}),
        xh_px=float(xh) if xh is not None else None,
        fit_path=measurements.get("fit_path"),
    )


def _manifest_order(root: Path) -> list[str]:
    """Entry ids in the order the manifest lists them (empty when there is none).

    The bench iterates in this order so a run is reproducible and a `--jobs`
    run reports the same rows in the same places as a serial one.
    """
    path = root / MANIFEST_FILE
    if not path.exists():
        return []
    manifest = json.loads(path.read_text())
    return [str(w.get("id", w["word"])) for w in manifest.get("words", [])]


def load_reference(fixture_root: Path) -> Reference:
    """Load a fixture root's stored word traces into scoreable entries.

    Raises `FileNotFoundError` when the root carries no `word_instances.json` —
    an export predating stage A, which the CLI turns into a named message
    naming the `--only word-instances` refill rather than a traceback.
    """
    root = Path(fixture_root)
    path = root / WORD_INSTANCES_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"no {WORD_INSTANCES_FILE} in {root} — refill it with "
            "`uv run python -m tools.wordbench.export_fixtures --only word-instances` "
            "(or fetch_fixtures over the API)"
        )
    artifact = json.loads(path.read_text())
    rows = artifact.get("rows") or []

    order_all = _manifest_order(root)
    rank = {entry_id: i for i, entry_id in enumerate(order_all)}
    excluded: dict[str, list[str]] = {}

    def exclude(reason: str, specimen_id: str) -> None:
        excluded.setdefault(reason, []).append(specimen_id)

    entries: dict[str, ReferenceEntry] = {}
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        row = _row_from(raw)
        # The frame gate's verdict is authoritative and comes FIRST: a stale
        # registration makes every number downstream meaningless, whatever else
        # the row looks like.
        if raw.get("frame_stale"):
            exclude(EXCLUDED_FRAME_STALE, row.specimen_id)
            continue
        entry_path = root / row.specimen_id / ENTRY_FILE
        if not entry_path.exists():
            exclude(EXCLUDED_NO_ENTRY, row.specimen_id)
            continue
        if not row.strokes:
            exclude(EXCLUDED_NO_STROKES, row.specimen_id)
            continue
        if "baseline_row" not in row.registration_px or row.xh_px is None:
            exclude(EXCLUDED_NO_REGISTRATION, row.specimen_id)
            continue
        entry = json.loads(entry_path.read_text())
        entries[row.specimen_id] = ReferenceEntry(
            specimen_id=row.specimen_id,
            entry=entry,
            frame=BenchFrame.from_entry(entry),
            row=row,
            directory=root / row.specimen_id,
        )

    # Manifest order, with anything the manifest does not mention appended in
    # artifact order rather than dropped — a row the bench can score is never
    # lost to a bookkeeping mismatch.
    order = sorted(entries, key=lambda i: (rank.get(i, len(rank)), i))
    return Reference(root=root, hand_id=artifact.get("hand_id"), entries=entries, order=order, excluded=excluded)


__all__ = [
    "DEFAULT_FIXTURES_DIR",
    "ENTRY_FILE",
    "EXCLUDED_FRAME_STALE",
    "EXCLUDED_NO_ENTRY",
    "EXCLUDED_NO_REGISTRATION",
    "EXCLUDED_NO_STROKES",
    "INK_MASK_FILE",
    "MANIFEST_FILE",
    "WORD_INSTANCES_FILE",
    "Reference",
    "ReferenceEntry",
    "ReferenceRow",
    "load_reference",
]
