"""The Kringel landmark: which loop of which letter has to stay open, and why.

The owner's design input of 2026-09-06 turned a global threshold into a
per-letter fact. „Dieser Kringel muss offen bleiben" is not one number for the
whole hand — it is a property of ONE loop of ONE letter, read off the plate:
how big the loop is, and, where it is small, whether the plate holds it open at
all. Small loops come in three states, and only one of them is a defect when it
closes:

* **offen** — the plate shows a counter in at least 80 % of the occurrences.
  A composed loop that closes here has LOST something the hand had.
* **wechselnd** — open in some occurrences, closed in others. Ink decides, not
  the ductus; a closing occurrence is inside the plate's own variation.
* **punkt** — closed in at least 80 % of the occurrences. A Punktkringel is a
  dot by construction and can never be a loss.

The size class is a property of the WRITING INSTRUMENT, not of this sample. A
Gleichzug pen of half width `h` erodes a centerline loop by exactly its full
width `W = 2h` (`docs/reference/glossar.md`, „Öffnungsweite · `D0`"), so the
classes are counted in pen widths of the plate's own pen (`W = 0.1936 xh`,
measured in #551 over all 63 word specimens):

* **klein** `D0 < 2W` — less than one pen width of hole is left over, so the
  instrument decides whether the loop is open;
* **mittel** `2W <= D0 < 4W`;
* **groß** `D0 >= 4W` — three quarters of the hole survive any pen.

This module is the SENSOR half: pure functions over the catalogue that
`tools/tracebench/run.py` prints beside the Duktus-Soll, report-only. Nothing
here touches a scored number, and a missing or unreadable catalogue degrades to
a warning rather than to a failure. The catalogue itself is built by
`tools/tracebench/kringelcat.py` from a frozen fixture root and stays a file of
THIS package.

**The per-loop half — `loop_apertures`, `size_class`, `loop_state` and the
catalogue reader — now lives in `core.landmarks`** and is re-exported here under
its old names. It moved because the admin's Landmarken-Linse serves those same
loops over HTTP and `api/` may not import `tools/` (`tests/test_imports.py`);
the pen width, the class boundaries and the 80 % majority travelled with the
code, unchanged. What stays here is what needs a composed WORD: which strokes
belong to a slot, which loops a word contributes, and the bench row fields.

Reserved dataset: the catalogue carries apertures, counts and classes — never
anchors, centerlines or any other geometry payload
(`docs/reference/quellen-und-rechte.md` §5).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np

from core.landmarks import (
    KRINGEL_CATALOGUE_FILE,
    PLATE_PEN_HALF_WIDTH_UNITS,
    PLATE_PEN_WIDTH_UNITS,
    SIZE_CLASSES,
    SIZE_MEDIUM_MAX_UNITS,
    SIZE_SMALL_MAX_UNITS,
    SPLITTER_FLOOR_UNITS,
    STATE_MAJORITY,
    STATES,
    UNATTESTED,
    LoopAperture,
    catalogue_source,
    load_catalogue,
    loop_apertures,
    loop_state,
    size_class,
)


# The catalogue's own path, under its historical name. `core.landmarks` reads
# the same file — it is a measurement artefact of this package and stays here.
CATALOGUE_FILE: Path = KRINGEL_CATALOGUE_FILE


def body_items(items: Sequence[dict[str, Any]]) -> dict[int, list[int]]:
    """`{slot: item indices of its BODY strokes}` — deferred marks excluded.

    A delayed mark carries its slot's `slot_index` but is flushed at the END of
    the word (`core/compose.py`, `flush_diacritics`), so a slot's index range
    read naively spans from its body to somewhere past the last letter. Two
    things break on that: „the item after the slot's last" then picks a foreign
    connector instead of this letter's, and the mark itself joins the stroke set
    a loop is measured on. Neither an i-dot nor a u-Deckstrich encloses
    anything, so they are dropped rather than moved.
    """
    out: dict[int, list[int]] = {}
    for i, item in enumerate(items):
        slot = item.get("slot_index")
        if slot is not None and not item.get("diacritic"):
            out.setdefault(int(slot), []).append(i)
    return out


def slot_loop_lines(items: Sequence[dict[str, Any]]) -> dict[int, tuple[str | None, list[np.ndarray]]]:
    """Per slot: `(glyph key, its body strokes plus the connector each side)`.

    The letter as the reader meets it. An entering connector can close a loop
    the isolated row does not have — `tools/tracebench/soll.py` names the same
    case for the crossing counters — so a catalogue built on the bare row would
    have no entry for exactly the loops the plate shows. Connectors carry no
    `slot_index`, so „the item directly before the slot's first BODY stroke and
    directly after its last" is the whole rule.
    """
    body = body_items(items)
    out: dict[int, tuple[str | None, list[np.ndarray]]] = {}
    for slot, idxs in body.items():
        take = set(idxs)
        lo, hi = min(idxs), max(idxs)
        if lo - 1 >= 0 and items[lo - 1].get("slot_index") is None:
            take.add(lo - 1)
        if hi + 1 < len(items) and items[hi + 1].get("slot_index") is None:
            take.add(hi + 1)
        key = next((items[i].get("glyph_key") for i in idxs if items[i].get("glyph_key")), None)
        out[slot] = (key, [np.asarray(items[i]["centerline"], dtype=float) for i in sorted(take)])
    return out


def word_kringel(
    items: Sequence[dict[str, Any]], catalogue: dict[str, list[dict[str, Any]]], half_width: float
) -> list[dict[str, Any]]:
    """One row per composed loop of the word, with its catalogue verdict.

    Judged at `half_width` — the pen the CALLER selected, which is not the
    root's delivered nib unless it was asked for.

    `honoured` is `True` when that pen leaves the loop open, `False`
    when it runs shut, and `None` where the catalogue registers no expectation
    (`punkt`, `unbelegt`, or a loop the catalogue does not know).
    """
    out: list[dict[str, Any]] = []
    for slot, (key, lines) in sorted(slot_loop_lines(items).items()):
        rows = catalogue.get(key or "", [])
        for rank, loop in enumerate(loop_apertures(lines)):
            entry = rows[rank] if rank < len(rows) else None
            state = entry["state"] if entry else "unbekannt"
            ink = loop.ink_aperture(half_width)
            out.append(
                {
                    "slot": slot,
                    "glyph": key,
                    "loop": rank,
                    "d0": round(loop.d0, 4),
                    "ink": round(ink, 4),
                    "size_class": entry["size_class"] if entry else "unbekannt",
                    "state": state,
                    "honoured": (ink > 0.0) if state in ("offen", "wechselnd") else None,
                }
            )
    return out


def kringel_row_fields(
    items: Sequence[dict[str, Any]], catalogue: dict[str, list[dict[str, Any]]], half_width: float
) -> dict[str, Any]:
    """The flat report fields one word contributes to a bench row.

    `kringel_lost` counts ONLY the `offen` loops that the SELECTED pen
    (`half_width`, not necessarily the root's delivered nib) runs shut — the
    honest defect count. `wechselnd` closures are carried in their own field
    because the plate itself closes those, and `punkt` loops are exempt by
    construction, never counted anywhere.
    """
    rows = word_kringel(items, catalogue, half_width)
    lost = [r for r in rows if r["state"] == "offen" and r["honoured"] is False]
    return {
        "kringel_loops": len(rows),
        "kringel_offen": sum(1 for r in rows if r["state"] == "offen"),
        "kringel_lost": len(lost),
        "kringel_wechselnd_zu": sum(1 for r in rows if r["state"] == "wechselnd" and r["honoured"] is False),
        "kringel_punkt": sum(1 for r in rows if r["state"] == "punkt"),
        "kringel_unbekannt": sum(1 for r in rows if r["state"] == "unbekannt"),
        "kringel_lost_at": " ".join(f"{r['glyph']}#{r['loop']}" for r in lost),
    }


def kringel_by_word(
    ids: Sequence[str],
    *,
    which: str,
    style: str,
    fixtures_root: Path,
    half_width: float,
    root_name: str | None = None,
    catalogue_path: Path | None = None,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Per word: the Kringel fields, or a warning per gap.

    Mirrors `tools/tracebench/soll.py::ductus_soll` — same composition source,
    same „one word must not cost the run" contract, same report-only status.

    The catalogue is read off ONE hand with ONE pen, so it is applied to that
    hand only: a run on another style or another source would otherwise publish
    Sütterlin-1922 expectations under a foreign hand's name, and every class in
    it is counted in the width of THIS plate's pen. On a mismatch the column is
    omitted with a warning rather than guessed at.
    """
    try:
        catalogue = load_catalogue(catalogue_path)
        source = catalogue_source(catalogue_path)
    except (OSError, ValueError) as exc:  # noqa: BLE001 — a sensor never fails a run
        return {}, [f"Kringel-Landmarke unavailable ({type(exc).__name__}: {exc}) — column omitted"]
    measured = source.get("measured_on") or [{}]
    on_root, on_style = str(measured[0].get("name", "")), str(source.get("style", ""))
    if on_style != style or (root_name is not None and on_root != root_name):
        return {}, [
            f"Kringel-Landmarke was measured on {on_style}/{on_root or '?'}, this run is "
            f"{style}/{root_name or '?'} — a catalogue belongs to ONE hand, column omitted"
        ]
    try:
        from tools.wordlab.cases import iter_fixture_word_cases  # noqa: PLC0415
        from tools.wordlab.derive import derive_word  # noqa: PLC0415

        cases = {
            c.id: c
            for c in iter_fixture_word_cases(which=which, style=style, only=list(ids), fixtures_root=fixtures_root)
        }
    except Exception as exc:  # noqa: BLE001
        return {}, [f"Kringel-Landmarke unavailable ({type(exc).__name__}: {exc}) — column omitted"]
    out: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    for specimen_id in ids:
        case = cases.get(specimen_id)
        if case is None or not getattr(case, "scorable", True):
            warnings.append(f"{specimen_id}: no scorable fixture case — Kringel-Landmarke omitted")
            continue
        try:
            # The measurement stays INSIDE the boundary, not just the derive:
            # rasterising a degenerate stroke set is as able to raise as the
            # composition is, and „one word must not cost the run" has to cover
            # the whole of one word's work to mean anything.
            items = derive_word(case).composed["items"]
            out[specimen_id] = kringel_row_fields(items, catalogue, half_width)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{specimen_id}: {type(exc).__name__} — Kringel-Landmarke omitted")
    return out, warnings


__all__ = [
    "CATALOGUE_FILE",
    "LoopAperture",
    "PLATE_PEN_HALF_WIDTH_UNITS",
    "PLATE_PEN_WIDTH_UNITS",
    "SIZE_CLASSES",
    "SIZE_MEDIUM_MAX_UNITS",
    "SIZE_SMALL_MAX_UNITS",
    "SPLITTER_FLOOR_UNITS",
    "STATES",
    "STATE_MAJORITY",
    "UNATTESTED",
    "kringel_by_word",
    "kringel_row_fields",
    "load_catalogue",
    "loop_apertures",
    "loop_state",
    "size_class",
    "slot_loop_lines",
    "word_kringel",
]
