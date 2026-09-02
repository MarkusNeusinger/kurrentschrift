"""Report-only seam angles — how sharply the pen turns where a generated
connector meets the letters it leaves and reaches.

The composer joins two letters with a generated connector whose end tangents
are aligned to the coupling tangents (``core.compose._endpoint_tangent`` over
``TANGENT_WINDOW`` = 0.12 xh of arc). That alignment is a WINDOW average: over
the 0.05 xh the eye actually reads at the seam, the connector can still leave
the letter noticeably steeper than the letter's own last segment ran — a local
kink far below the resolution of the word ruler (its chamfer window is
0.05–0.12 xh) and therefore invisible to ``bench_loss``. The audit of
2026-09-02 measured it by hand on 40 connectors from 13 live payloads
(departure median +13.6°, arrival −6.8°); this module turns that one-off
measurement into a bench column so a class rule that claims to fix it has a
number to move.

What is measured, precisely — all in TEMPLATE UNITS (1 = x-height), angles in
degrees with y pointing UP, so a positive angle heads up-right:

* ``SEAM_WINDOW`` = 0.05 xh of ARC LENGTH at each end of a polyline. The
  direction is the chord from the sample the window reaches back to (or
  forward to) to the endpoint itself — the same walk
  ``core.compose._endpoint_tangent`` does, at a deliberately SMALLER window:
  0.12 xh is the window the composer aligns on, so measuring the residual kink
  there would measure the composer against its own construction. A polyline
  shorter than the window contributes its whole length.
* ``dep_deg`` — the turn at the DEPARTURE seam, in travel order:
  ``direction(connector, start) − direction(left glyph's last body stroke,
  end)``, wrapped to (−180, 180]. Positive = the pen turns counter-clockwise
  (steeper) as it leaves the letter.
* ``arr_deg`` — the turn at the ARRIVAL seam, same travel order:
  ``direction(right glyph's first body stroke, start) − direction(connector,
  end)``. Positive = the pen turns counter-clockwise as it enters the letter.

Both are "outgoing minus incoming" at the seam, so the two columns share one
sign convention and reproduce the audit's signs (+ departure, − arrival).

The frame is the same one ``pairmeas`` uses: the glyphs' BODY strokes (the
slot's non-diacritic centerlines, writing order), read off a
``compose_word(provenance=True)`` result. Two corrections make the reading
honest:

* The emitted connector is ``_overlap_extend``-ed at both ends — one extra
  sample per end, CONNECT_OVERLAP (0.05 xh) along the local tangent, so the
  round cap tucks under the neighbouring ink. That tuck is a rendering detail,
  not part of the pen path, and it is exactly one window long; the seam is
  measured on the centerline with both tuck samples removed.
* A capital's ornament retrace is PREFIXED onto the connector item
  (``cap_retrace``), so such an item starts by running BACKWARDS over ink the
  letter already laid down: its departure is a designed ~180° turnaround, not a
  seam. Those joins are excluded and counted (``excluded_retrace``), never
  silently dropped. They are recognised by the item's stated ``exit``
  provenance point: for every other connector the centerline starts exactly
  there.

Deliberately NOT excluded, because they are ductus, not defect: joins whose
letter genuinely reverses at the seam (the ſ/w/r/v descender and loop
turnarounds depart near ±180°, the t/r/f/p lead-ins arrive there). They are 18
of 206 departures and 14 of 206 arrivals on the 1922 word plate and they leave
the signed median where it was (+11.87 with them, +11.72 without) — a median
carries them; the ``abs`` aggregates read them as what they are, large turns.
An APPROVED override is likewise kept: it is a rendered join like any other,
and its seam is what the reader sees.

Report-only in the strict sense: consumed by tools/wordbench/run.py as extra
columns, never part of ``bench_loss``/``pair_loss`` (precedent: the slant
column, the Gleichzug audit and the ``meas`` columns).
"""

from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np

from core.compose import CONNECT_OVERLAP
from tools.wordbench.pairmeas import body_lines, join_pair_keys


# Arc length over which a seam direction is read, in x-height units. Smaller
# than core.compose.TANGENT_WINDOW (0.12) on purpose — see the module docstring.
SEAM_WINDOW = 0.05
# Tolerances for recognising the two structural features of an emitted
# connector. Both compare coordinates the composer wrote in the same units, so
# they are exact-match guards with room for float noise, not fitted thresholds.
_OVERLAP_TOL = 1e-6
_EXIT_TOL = 1e-6


def _wrap180(deg: float) -> float:
    """An angle difference folded into (−180, 180]."""
    return -((180.0 - deg) % 360.0 - 180.0)


def direction_deg(line: Sequence[Sequence[float]], at_end: bool, window: float = SEAM_WINDOW) -> float | None:
    """Travel direction (degrees, y up) entering (start) or leaving (end) a polyline.

    Walks ``window`` of arc length inward from the endpoint and returns the
    chord's heading IN TRAVEL ORDER. ``None`` when the polyline is degenerate
    (fewer than two samples, or zero length within the window) — a report
    column must never raise out of a scoring run.
    """
    n = len(line)
    if n < 2:
        return None
    tip = line[n - 1] if at_end else line[0]
    far = line[n - 2] if at_end else line[1]
    acc = 0.0
    if at_end:
        for i in range(n - 1, 0, -1):
            acc += math.hypot(line[i][0] - line[i - 1][0], line[i][1] - line[i - 1][1])
            far = line[i - 1]
            if acc >= window:
                break
    else:
        for i in range(n - 1):
            acc += math.hypot(line[i + 1][0] - line[i][0], line[i + 1][1] - line[i][1])
            far = line[i + 1]
            if acc >= window:
                break
    if acc <= 1e-12:
        return None
    a, b = (far, tip) if at_end else (tip, far)
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def strip_overlap(line: Sequence[Sequence[float]]) -> list[list[float]]:
    """An emitted connector centerline without its ``_overlap_extend`` tuck samples.

    ``core.compose._overlap_extend`` inserts ONE sample at each open end,
    CONNECT_OVERLAP away from the original endpoint along the local tangent.
    An end is stripped only when its first segment measures exactly that —
    so a connector the composer left unextended (a degenerate line it passed
    through untouched) keeps all of its samples.
    """
    out = [list(p) for p in line]
    if len(out) >= 4 and abs(math.dist(out[0], out[1]) - CONNECT_OVERLAP) <= _OVERLAP_TOL:
        out = out[1:]
    if len(out) >= 3 and abs(math.dist(out[-1], out[-2]) - CONNECT_OVERLAP) <= _OVERLAP_TOL:
        out = out[:-1]
    return out


def _median(values: list[float]) -> float | None:
    return round(float(np.median(values)), 2) if values else None


def seam_angles(composed: dict, slots: Sequence[Any]) -> dict:
    """Seam turn angles for every generated join of one composed entry.

    Args:
        composed: a ``compose_word(..., provenance=True)`` result — its glyph
            items carry ``slot_index`` (+ ``diacritic``) and its connectors
            ``pair``/``from_slot``/``to_slot`` (+ the stated ``exit``).
        slots: the entry's frozen slots, for the join's base-key labels.

    Returns:
        ``{"n_joins", "n_matched", "excluded_retrace", "dep_median",
        "arr_median", "joins"}`` — the medians SIGNED over this entry's matched
        joins, ``joins`` one ``{"slot", "pair", "dep_deg", "arr_deg"}`` per
        matched join. A join whose adjoining body strokes are missing or whose
        geometry is degenerate counts as unmatched rather than raising.
    """
    bodies = body_lines(composed)
    joins: list[dict] = []
    n_joins = 0
    excluded_retrace = 0
    for item in composed.get("items", []):
        pair = item.get("pair")
        if not pair or pair[1] is None:  # a glyph stroke or the word-final Endstrich
            continue
        n_joins += 1
        centerline = strip_overlap(item.get("centerline") or [])
        if len(centerline) < 2:
            continue
        stated_exit = item.get("exit")
        if stated_exit is not None and math.dist(centerline[0], stated_exit) > _EXIT_TOL:
            # A capital's ornament retrace was prefixed — the item starts by
            # running back over the letter's own ink, so its "departure" is a
            # designed turnaround rather than a seam.
            excluded_retrace += 1
            continue
        from_body = bodies.get(item.get("from_slot"))
        to_body = bodies.get(item.get("to_slot"))
        if not from_body or not to_body:
            continue  # no provenance-tagged bodies -> no comparable frame
        left_out = direction_deg(from_body[-1], at_end=True)
        conn_in = direction_deg(centerline, at_end=False)
        conn_out = direction_deg(centerline, at_end=True)
        right_in = direction_deg(to_body[0], at_end=False)
        if None in (left_out, conn_in, conn_out, right_in):
            continue
        left_key, right_key = join_pair_keys(slots, item)
        joins.append(
            {
                "slot": item.get("from_slot"),
                "pair": [left_key, right_key],
                "dep_deg": round(_wrap180(conn_in - left_out), 2),
                "arr_deg": round(_wrap180(right_in - conn_out), 2),
            }
        )
    return {
        "n_joins": n_joins,
        "n_matched": len(joins),
        "excluded_retrace": excluded_retrace,
        "dep_median": _median([j["dep_deg"] for j in joins]),
        "arr_median": _median([j["arr_deg"] for j in joins]),
        "joins": joins,
    }
