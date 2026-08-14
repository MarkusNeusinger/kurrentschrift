"""The ductus target: what the composed word PRESCRIBES, per structure counter.

The owner's standing test (2026-08-15): loops, crossings and retrace zones are
ductus facts — the letters fix them, the join classes add a known contribution,
and none of them is a free variable of any fit. So every consumer that shows or
scores detected structures can put the EXPECTED value beside them: a hand count
outside the target is a finding (in the template, the join grammar or the
trace), a candidate count outside it is an invention.

Both target rows are counted by the SAME v2 counters as the measured sides
(`counters.crossing_points` / `counters.structure_zones`), so a disagreement is
never a units, thresholds or semantics artifact:

* **letters** — the sum over the ISOLATED letters, each slot's own strokes
  including its marks (the per-letter budget rides along for a manual check);
* **composition** — the whole composed word with its generated connectors.

The difference between the two IS the joins' contribution: an entering
connector can close a loop the isolated letter does not have (the e — and the
hand shows the same for the medial d, which the composition does not close
yet; exactly such gaps are what the target makes visible).

Report-only, shared by the duel viewer and the bench report; nothing here
touches a scored number. Composition comes from the frozen fixture cases; a
root without them degrades to no rows and a warning, never to a failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from tools.tracebench.counters import crossing_points, structure_zones


@dataclass(frozen=True)
class SollRow:
    """One ductus-expectation row (not a drawn or scored layer)."""

    label: str
    strokes: int | None  # None renders as a dash (a letter sum has no stroke count)
    crossings: int
    zones: int
    per_letter: str = ""  # the budget letter by letter, for the manual check
    touches: int = 0
    overlaps: int = 0


def ductus_soll(
    ids: Sequence[str], *, which: str, style: str, fixtures_root: Path
) -> tuple[dict[str, tuple[SollRow, ...]], list[str]]:
    """Per word: `(letters_sum, composition)` targets, or a warning per gap."""
    try:
        from tools.wordlab.cases import iter_fixture_word_cases
        from tools.wordlab.derive import derive_word

        cases = {
            c.id: c
            for c in iter_fixture_word_cases(which=which, style=style, only=list(ids), fixtures_root=fixtures_root)
        }
    except Exception as exc:  # noqa: BLE001 — the consumer must go on without Soll rather than not at all
        return {}, [f"Duktus-Soll unavailable ({type(exc).__name__}: {exc}) — rows omitted"]
    out: dict[str, tuple[SollRow, ...]] = {}
    warnings: list[str] = []
    for specimen_id in ids:
        case = cases.get(specimen_id)
        if case is None or not getattr(case, "scorable", True):
            warnings.append(f"{specimen_id}: no scorable fixture case — Duktus-Soll omitted")
            continue
        try:
            items = derive_word(case).composed["items"]
        except Exception as exc:  # noqa: BLE001 — one word must not cost the run
            warnings.append(f"{specimen_id}: derive failed ({type(exc).__name__}) — Duktus-Soll omitted")
            continue
        slots: dict[int, dict[str, Any]] = {}
        comp: list[np.ndarray] = []
        current: list[tuple[float, float]] = []
        for item in items:
            pts = [(float(x), float(y)) for x, y in item["centerline"]]
            slot = item.get("slot_index")
            if slot is not None:
                info = slots.setdefault(slot, {"key": None, "strokes": []})
                if item.get("glyph_key") and not item.get("diacritic"):
                    info["key"] = item["glyph_key"]
                info["strokes"].append(np.asarray(pts, dtype=float))
            if item.get("lift") and current:
                comp.append(np.asarray(current, dtype=float))
                current = []
            for p in pts:
                if current and abs(current[-1][0] - p[0]) < 1e-12 and abs(current[-1][1] - p[1]) < 1e-12:
                    continue
                current.append(p)
        if current:
            comp.append(np.asarray(current, dtype=float))
        sum_cross = sum_zones = sum_touch = sum_overlap = 0
        cells: list[str] = []
        for slot in sorted(slots):
            info = slots[slot]
            n_cross = int(len(crossing_points(info["strokes"])))
            letter_zones = structure_zones(info["strokes"])
            sum_cross += n_cross
            sum_zones += int(len(letter_zones.retrace_mids))
            sum_touch += int(len(letter_zones.touch_mids))
            sum_overlap += int(len(letter_zones.overlap_mids))
            cells.append(f"{info['key'] or '?'} {n_cross}/{len(letter_zones.retrace_mids)}")
        comp_zones = structure_zones(comp)
        out[specimen_id] = (
            SollRow(
                label="Duktus-Soll (Σ Buchstaben)",
                strokes=None,
                crossings=sum_cross,
                zones=sum_zones,
                per_letter="Kreuzungen/Zonen je Buchstabe: " + " · ".join(cells),
                touches=sum_touch,
                overlaps=sum_overlap,
            ),
            SollRow(
                label="Komposition (mit Verbindern)",
                strokes=len(comp),
                crossings=int(len(crossing_points(comp))),
                zones=int(len(comp_zones.retrace_mids)),
                touches=int(len(comp_zones.touch_mids)),
                overlaps=int(len(comp_zones.overlap_mids)),
            ),
        )
    return out, warnings


def soll_row_fields(rows: tuple[SollRow, ...]) -> dict[str, int]:
    """The flat report fields one word's Soll pair contributes to a bench row."""
    letters, comp = rows
    return {
        "soll_cross_letters": letters.crossings,
        "soll_zones_letters": letters.zones,
        "soll_cross": comp.crossings,
        "soll_zones": comp.zones,
        "soll_touch": comp.touches,
        "soll_overlap": comp.overlaps,
    }


__all__ = ["SollRow", "ductus_soll", "soll_row_fields"]
