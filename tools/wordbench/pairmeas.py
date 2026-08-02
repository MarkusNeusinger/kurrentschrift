"""Report-only "gemessen vs. komponiert" — the composed joins against the
specimen's dissected ones (handmodell H2 read surfaces).

The pair layer already knows what the writer actually did at every letter
join: `pair_instances` holds one dissected occurrence per adjacent joined pair
of the SAME fixture specimens the bench scores (harvested by
tools/pairlab/harvest.py, so the slot spaces coincide), in the `glyph_pairs`
frame — connector centerline and placement offset relative to the LEFT glyph's
exit, baseline-locked, template units. The composer generates its own join for
the same slot. Holding the two side by side turns "the word looks off" into a
number per join, without touching the ruler:

* ``doff``  — how far the composed placement puts the right glyph HORIZONTALLY
  from where the specimen put it: ``|Δx_composed − offset_x_measured|``, with
  ``Δx_composed`` read in the SAME frame the harvest measured in — the two
  letters' BODY endpoints (the left glyph's last non-diacritic stroke end, the
  right glyph's first non-diacritic stroke start; tools/pairlab/analyze.py
  ``a_exit_line[-1]``/``b_first_line[0]``).
* ``dconn`` — how differently the connector is SHAPED: the mean pointwise
  distance between the two centerlines, each arc-length-resampled to the pair
  aggregation's point count (``core.aggregate.PAIR_CONNECTOR_POINTS``) and then
  shifted so its own first sample sits at the origin. Start-aligned, hence
  translation-free: placement is ``doff``'s job alone, this column reports
  shape and sweep.

Why the frame matters — and why ``doff`` is x-only:

* The composer's coupling anchors (``exit``/``entry``, stated by
  ``compose_word(provenance=True)``) are NOT the body endpoints: a capital's
  ornament exit or a trimmed lead-in moves them by up to ~2 xh. Measuring the
  composed offset there against a body-frame measurement reports a pure frame
  artifact — on the Sütterlin word set that made a quarter of all joins read
  ≥80 % artifact (``Of`` 2.04 measured as 2.06, the six capital-S words ~1.8).
  So ``doff`` uses the body endpoints and never those keys. They stay in the
  compose payload (tested, additive) for overlay work that wants the actual
  coupling geometry.
* The measured offset's y component carries NO specimen information: the
  harvest cancels the relative vertical fit shift (``end_dy``,
  tools/pairlab/harvest.py) because the composer places both glyphs
  baseline-locked, so ``offset_y`` is by construction the composed body Δy at
  harvest time. Comparing it would measure the composer against itself. The
  horizontal delta is also exactly the quantity uebergaenge-befund.md Befund 1
  found dominant (median required correction 0.19 xh).
* Remaining, deliberately accepted caveat on ``doff``: a HIGH entry trims
  lead-in samples off the right glyph's first stroke (``entry_trim``), and
  that cut is the composer's own decision — a composition change that moves it
  moves the composed body start against a frozen measurement. Small, and
  visible as a shift of the whole column rather than of one join.
* Deliberately accepted caveat on ``dconn``: the composed centerline is the
  EMITTED one, so it carries the overlap extension (``CONNECT_OVERLAP`` reaches
  back into the previous ink) and, after a capital, the prefixed ornament
  retrace. Start-alignment removes the resulting TRANSLATION but not that extra
  head, which the measured connector does not have (the six Sütterlin capital-S
  words sit near 0.82 on it). ``dconn`` is therefore not a calibrated absolute
  distance — it is a monotone signal: same join, smaller number = closer to the
  specimen. That is all a report column needs (precedent: the slant column and
  the Gleichzug audit).

Excluded from the comparison (counted, never silently dropped):

* a measured row whose dissection the harvest itself distrusts
  (``measurements.fit_ok`` not set — the same gate the pair-aggregate rebuild
  applies in ``core.aggregate.aggregate_pair_instances``): 11 of 199 word rows
  and 3 of 33 pair rows on the 1922 plates. A median must not rest on them.
* a join the composer rendered from an APPROVED override: an override IS a
  harvested centerline, so comparing it against its own source specimen
  measures the harvest's round-trip, not the generator. Same doctrine as
  "an override run is its own number, never the headline".

Report-only in the strict sense: consumed by tools/wordbench/run.py as extra
columns, never part of ``bench_loss``/``pair_loss``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from core.aggregate import PAIR_CONNECTOR_POINTS, _resample_polyline
from core.compose import _key_base


def load_measured(fixture_root: Path) -> dict | None:
    """The frozen measured joins of one fixture root, or None.

    A fixture set exported before the artifact existed simply has no file —
    the caller then reports no columns at all instead of zeros, so an old
    fixture set keeps running unchanged. An unreadable or malformed file is
    treated the SAME way, with one warning line: a report artifact must never
    be able to take a scoring run down.
    """
    path = fixture_root / "pair_instances.json"
    if not path.exists():
        return None
    try:
        artifact = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        print(f"warning: ignoring {path} ({type(exc).__name__}: {exc}) — meas columns absent")
        return None
    if not isinstance(artifact, dict):
        print(f"warning: ignoring {path} (not a JSON object) — meas columns absent")
        return None
    return artifact


def rows_for_entry(artifact: dict | None, kind: str, specimen_id: str) -> list[dict]:
    """The measured joins of ONE bench entry — `(kind, specimen_id)` is the
    occurrence identity the harvest wrote (the word plates and the Abb.-20
    drills are separate id namespaces of the same source)."""
    if not artifact:
        return []
    rows = artifact.get("rows", [])
    if not isinstance(rows, list):
        return []
    # Tolerant row access: one malformed row in a hand-edited artifact must
    # not raise out of the helper — the runner treats the artifact as a
    # report-only input that can never take the scoring down.
    return [r for r in rows if isinstance(r, dict) and r.get("kind") == kind and r.get("specimen_id") == specimen_id]


def _base_key(slots: Sequence[Any], index: int | None) -> str:
    if index is None or not (0 <= index < len(slots)):
        return ""
    slot = slots[index]
    return _key_base(slot.key, slot.position)


def _body_lines(composed: dict) -> dict[int, list[list]]:
    """slot_index -> the slot's NON-diacritic glyph centerlines, writing order.

    The composer emits a slot's body strokes consecutively and holds its
    diacritics back (``flush_diacritics``), so the first/last entry here are
    the glyph's first stroke start and last stroke end — the frame
    tools/pairlab/analyze.py fitted and harvested in. Connector items carry
    ``from_slot``/``to_slot`` but no ``slot_index`` and never appear.
    """
    lines: dict[int, list[list]] = {}
    for item in composed.get("items", []):
        if "slot_index" not in item or item.get("diacritic"):
            continue
        centerline = item.get("centerline")
        if centerline is not None and len(centerline):
            lines.setdefault(int(item["slot_index"]), []).append(centerline)
    return lines


def _mean(values: list[float]) -> float | None:
    return round(float(np.mean(values)), 3) if values else None


def compare_joins(composed: dict, slots: Sequence[Any], measured: Iterable[dict]) -> dict:
    """Compare every composed join of one entry with its measured occurrence.

    Args:
        composed: a ``compose_word(..., provenance=True)`` result — its glyph
            items carry ``slot_index`` (+ ``diacritic``) and its connectors
            ``pair``/``from_slot``/``to_slot`` (+ ``override``).
        slots: the entry's frozen slots (for the base-key agreement check).
        measured: the `pair_instances` rows of this entry (rows_for_entry).

    Returns:
        ``{"n_joins", "n_matched", "excluded_fit", "excluded_override",
        "doff_mean", "dconn_mean", "joins"}``. A join with no measured row, a
        disagreeing letter pair, missing body strokes or a degenerate
        connector counts as unmatched — never a crash: the specimen coverage
        is partial by nature (a flagged dissection was never stored), and a
        report column must not be able to take the run down.
    """
    by_slot = {int(r["slot"]): r for r in measured}
    bodies = _body_lines(composed)
    joins: list[dict] = []
    n_joins = 0
    excluded_fit = 0
    excluded_override = 0
    for item in composed.get("items", []):
        pair = item.get("pair")
        if not pair or pair[1] is None:  # a glyph stroke or the word-final Endstrich
            continue
        n_joins += 1
        if item.get("override"):
            # An approved override is itself a harvested centerline — against
            # its own source specimen it would measure ~0 by construction.
            excluded_override += 1
            continue
        row = by_slot.get(item.get("from_slot"))
        if row is None:
            continue
        left = _base_key(slots, item.get("from_slot"))
        right = _base_key(slots, item.get("to_slot"))
        if (row["left_key"], row["right_key"]) != (left, right):
            continue  # the frozen slots moved under the harvest — not comparable
        if not (row.get("measurements") or {}).get("fit_ok"):
            excluded_fit += 1  # the harvest's own QC gate rejected this dissection
            continue
        from_body = bodies.get(item.get("from_slot"))
        to_body = bodies.get(item.get("to_slot"))
        if not from_body or not to_body:
            continue  # no provenance-tagged bodies → no comparable frame
        measured_connector = np.asarray(row["geometry"]["connector"], dtype=float)
        composed_connector = np.asarray(item["centerline"], dtype=float)
        if len(composed_connector) < 2 or len(measured_connector) < 2:
            continue
        # Placement in the harvest's BODY frame, horizontal component only.
        body_exit_x = float(from_body[-1][-1][0])
        body_entry_x = float(to_body[0][0][0])
        measured_offset_x = float(row["geometry"]["offset"][0])
        # Shape, start-aligned: each curve relative to its own first sample.
        a = _resample_polyline(composed_connector, PAIR_CONNECTOR_POINTS)
        b = _resample_polyline(measured_connector, PAIR_CONNECTOR_POINTS)
        joins.append(
            {
                "slot": int(row["slot"]),
                "pair": [left, right],
                "doff": round(abs((body_entry_x - body_exit_x) - measured_offset_x), 3),
                "dconn": round(float(np.linalg.norm((a - a[0]) - (b - b[0]), axis=1).mean()), 3),
            }
        )
    return {
        "n_joins": n_joins,
        "n_matched": len(joins),
        "excluded_fit": excluded_fit,
        "excluded_override": excluded_override,
        "doff_mean": _mean([j["doff"] for j in joins]),
        "dconn_mean": _mean([j["dconn"] for j in joins]),
        "joins": joins,
    }
