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
`tools/tracebench/kringelcat.py` from a frozen fixture root.

Reserved dataset: the catalogue carries apertures, counts and classes — never
anchors, centerlines or any other geometry payload
(`docs/reference/quellen-und-rechte.md` §5).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np


CATALOGUE_FILE = Path(__file__).with_name("kringel_catalogue.json")

# The plate's own pen, measured in #551 as the median skeleton half width over
# all 63 word specimens of the `sep05` root (n = 39 155 skeleton pixels). Frozen:
# the size classes below are counted in multiples of it, so re-estimating it
# would silently reclassify the catalogue.
PLATE_PEN_HALF_WIDTH_UNITS = 0.0968
PLATE_PEN_WIDTH_UNITS = 2.0 * PLATE_PEN_HALF_WIDTH_UNITS

SIZE_SMALL_MAX_UNITS = 2.0 * PLATE_PEN_WIDTH_UNITS
SIZE_MEDIUM_MAX_UNITS = 4.0 * PLATE_PEN_WIDTH_UNITS

# A loop is `offen` / `punkt` when the plate agrees in at least this share of
# the occurrences; anything between is `wechselnd`.
STATE_MAJORITY = 0.8

# Below this a raster loop is a splinter of the rasterisation or a loop the
# composition has COLLAPSED — either way not a Kringel, and never something a
# plate counter may be attributed to. A twentieth of an x-height is under half
# the plate pen's own width: no pen writes an open loop there and no reader
# sees one.
SPLITTER_FLOOR_UNITS = 0.05

# Raster resolution of the aperture measurement, in pixels per x-height. At
# 1200 the reading floor is 2 px = 0.0017 xh, three orders under the smallest
# aperture the catalogue classifies.
RASTER_PX_PER_UNIT = 1200.0

# The background is labelled 4-connected so an 8-connected curve really closes a
# hole; scipy's default structure is exactly that cross.
_BG_STRUCT = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)

SIZE_CLASSES = ("klein", "mittel", "gross")
STATES = ("offen", "wechselnd", "punkt")
# The fourth mark, for a loop the plate answers in no occurrence: it gets no
# expectation rather than a guessed class. Not a class and not a state — the
# absence of both.
UNATTESTED = "unbelegt"


@dataclass(frozen=True)
class LoopAperture:
    """One enclosed loop of a polyline set, in the polylines' own units."""

    d0: float  # centerline loop aperture: the inscribed diameter of the enclosed region
    area: float
    cx: float
    cy: float

    def ink_aperture(self, half_width: float) -> float:
        """What the loop shows as INK once a Gleichzug pen of `half_width` runs it.

        The capsule union's hole is the erosion of the centerline hole by the
        half width, so the visible aperture is exactly `d0 - 2h`. Negative means
        the loop has run shut.
        """
        return self.d0 - 2.0 * half_width


def size_class(d0: float) -> str:
    """`klein` · `mittel` · `gross`, counted in widths of the plate's pen."""
    if d0 < SIZE_SMALL_MAX_UNITS:
        return "klein"
    if d0 < SIZE_MEDIUM_MAX_UNITS:
        return "mittel"
    return "gross"


def loop_state(occurrences: int, with_counter: int) -> str:
    """`offen` · `wechselnd` · `punkt` from how often the PLATE shows a hole.

    `with_counter` counts the occurrences in which the plate's ink carries a
    counter at this loop. The rule is the owner's own three-way split, and it
    is deliberately blind to how WIDE the counter is: a Punktkringel is defined
    by the plate never opening it, not by a threshold on its aperture.
    """
    if occurrences <= 0:
        raise ValueError("loop_state needs at least one occurrence")
    # The tolerance is not a third threshold: 1 - 0.8 is 0.19999999999999996 in
    # binary, so 2 of 10 would fall out of `punkt` on a representation rather
    # than on a reading. A boundary case must turn on the rule, not on the float.
    share = with_counter / occurrences
    if share >= STATE_MAJORITY - 1e-9:
        return "offen"
    if share <= (1.0 - STATE_MAJORITY) + 1e-9:
        return "punkt"
    return "wechselnd"


def loop_apertures(
    lines: Sequence[Sequence[Sequence[float]]],
    *,
    px_per_unit: float = RASTER_PX_PER_UNIT,
    floor: float = SPLITTER_FLOOR_UNITS,
    pad: float = 0.05,
) -> list[LoopAperture]:
    """Every enclosed loop of a polyline set, largest-x first, splinters dropped.

    The raster-based twin of the ductus loop finder `core.aggregate.loop_ranges`
    (#552): that one reads the SELF-CROSSINGS of the chart row and merges
    overlapping spans, which is what a per-anchor registration needs and what a
    per-loop aperture must not have. This one asks the complementary question —
    which regions does the drawn curve actually enclose, and how wide is each —
    and it sees a loop the ductus finder merges away as well as one it never had
    a range for (the `t`, the capitals).

    Ordering is by `(cx, cy)`, i.e. reading order, because that is the identity
    the catalogue is keyed on: the caller's n-th loop of a glyph is the
    catalogue's n-th entry for it.
    """
    from PIL import Image, ImageDraw  # noqa: PLC0415 — heavy import, one call site
    from scipy.ndimage import distance_transform_edt  # noqa: PLC0415
    from scipy.ndimage import label as cc_label  # noqa: PLC0415

    arrays = [np.asarray(line, dtype=float) for line in lines]
    arrays = [a for a in arrays if a.ndim == 2 and len(a) >= 2]
    if not arrays:
        return []
    allp = np.vstack(arrays)
    x0, y0 = allp.min(axis=0) - pad
    x1, y1 = allp.max(axis=0) + pad
    width = max(8, int(np.ceil((x1 - x0) * px_per_unit)) + 1)
    height = max(8, int(np.ceil((y1 - y0) * px_per_unit)) + 1)
    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)
    for line in arrays:
        draw.line([((x - x0) * px_per_unit, (y - y0) * px_per_unit) for x, y in line], fill=255, width=1)
    curve = np.asarray(img) > 0
    labels, count = cc_label(~curve, structure=_BG_STRUCT)
    border = set(labels[0, :]) | set(labels[-1, :]) | set(labels[:, 0]) | set(labels[:, -1])
    edt = distance_transform_edt(~curve)
    out: list[LoopAperture] = []
    for i in range(1, count + 1):
        if i in border:
            continue
        sel = labels == i
        dist = np.where(sel, edt, -1.0)
        idx = int(np.argmax(dist))
        d0 = 2.0 * float(dist.flat[idx]) / px_per_unit
        if d0 < floor:
            continue
        cy, cx = np.unravel_index(idx, dist.shape)
        out.append(
            LoopAperture(
                d0=d0, area=float(sel.sum()) / px_per_unit**2, cx=x0 + cx / px_per_unit, cy=y0 + cy / px_per_unit
            )
        )
    return sorted(out, key=lambda lp: (lp.cx, lp.cy))


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


def catalogue_source(path: Path | None = None) -> dict[str, Any]:
    """The `_source` header of a catalogue file: which root and style it was read on."""
    payload = json.loads((path or CATALOGUE_FILE).read_text(encoding="utf-8"))
    source = payload.get("_source")
    if not isinstance(source, dict):
        raise ValueError("kringel catalogue: no '_source' header")
    return source


def load_catalogue(path: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """`{glyph key: [loop row, …]}` in loop order, from the frozen catalogue file.

    Every failure mode here is a `ValueError` — including a row with a missing
    or misspelled field — because the caller's contract is „a catalogue that
    cannot be read costs the column, never the run", and a `KeyError` escaping
    this function would abort the whole bench instead.
    """
    payload = json.loads((path or CATALOGUE_FILE).read_text(encoding="utf-8"))
    rows = payload.get("loops")
    if not isinstance(rows, list):
        raise ValueError("kringel catalogue: no 'loops' array")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"kringel catalogue: row {i} is not an object")
        missing = [f for f in ("glyph", "loop", "size_class", "state") if f not in row]
        if missing:
            raise ValueError(f"kringel catalogue: row {i} lacks {', '.join(missing)}")
        if not isinstance(row["glyph"], str) or not isinstance(row["loop"], int) or isinstance(row["loop"], bool):
            raise ValueError(f"kringel catalogue: row {i} has a non-comparable glyph/loop key")
        # The vocabulary is checked HERE rather than trusted: a word the sensor
        # does not know silently becomes "no expectation", which reads exactly
        # like a Punktkringel and would hide a whole class of loops.
        if row["size_class"] not in (*SIZE_CLASSES, UNATTESTED):
            raise ValueError(f"kringel catalogue: {row['glyph']}#{row['loop']} has size class {row['size_class']!r}")
        if row["state"] not in (*STATES, UNATTESTED):
            raise ValueError(f"kringel catalogue: {row['glyph']}#{row['loop']} has state {row['state']!r}")
    out: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(rows, key=lambda r: (r["glyph"], r["loop"])):
        out.setdefault(row["glyph"], []).append(row)
    for glyph, loops in out.items():
        if [row["loop"] for row in loops] != list(range(len(loops))):
            raise ValueError(f"kringel catalogue: loop indices of {glyph!r} are not 0..n-1")
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
