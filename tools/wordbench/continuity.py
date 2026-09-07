"""Report-only continuity of the composed word centreline — where the pen
changes direction at a place that is not a ductus event.

The arithmetic — the Knick, the Wackler, the Pfeilhöhe and the flat spot, with
their frozen window ladder — lives in `core/continuity.py`; read the principle
and the constants there. This module is the WORD-level half: which pen strokes
a composition has, which ductus events are exempt in it, and the report columns
`tools/wordbench/run.py` prints. (The split happened with the Streifen-Befund,
which runs the same arithmetic on written ink and could not import `tools`; the
numbers this module reports are unchanged by it.)

Every ruler that judges a COMPOSED WORD measures the opposite quantity.
``bench_loss`` is a chamfer against the specimen skeleton, ``dtw_xh`` a
point-to-point distance, ``dconn``/``dspan`` a connector-shape distance: all of
them ask HOW FAR the path sits from a reference, none of them asks whether the
path is CONTINUOUS with itself. A kink and a smooth bow through the same two
endpoints score the same, which is why `stem_depart` could pass every gate in
humanbench round 6 while the judge gave 20 of 21 screens to the base arm.

The repo does own reference-free shape terms — but one level DOWN, on the
single rendered LETTER: ``core.quality_suetterlin``'s naturalness metric
(qualitaetsmetrik.md §5) scores smoothness as the smoothed second difference
of curvature, plus corner crispness and collinearity. This module is that
family's word-level relative, and deliberately not a second copy of it. Three
differences decide what it can see that §5 cannot:

* it runs on the COMPOSED word, so the generated joins — where both human word
  rounds were decided — are inside its domain at all;
* it exempts the ductus events (crossing, retrace, lift, reversal corner)
  rather than scoring through them, because at a join the question is whether
  a direction change belongs there;
* the Knick term reads a tangent DISCONTINUITY, not curvature oscillation: it
  is zero for a circular arc of any radius AND for a clean spiral, and answers
  only where turning concentrates at a point.

This module is the sensor that names the quantity. It is REPORT-ONLY in the
strict sense — consumed by tools/wordbench/run.py as extra columns, never part
of ``bench_loss``/``pair_loss``, and ``core/word_metric.py`` is untouched
(precedent: the slant column, the Gleichzug audit, the ``meas`` columns and
the seam angles).

Measured on the composed PEN STROKES (`tools.tracebench.soll.
composition_strokes`: items concatenate until one carries ``lift``, so a
stroke is one pen-down run and a lift is a stroke boundary by construction).

WHAT IS EXEMPT — the ductus events, where a direction change is the point.
A sample is dropped when it lies within ``LANDMARK_RADIUS_UNITS`` of one:

* **lift** — a pen-stroke end. The margin is the same one every window needs,
  so no measurement window ever straddles a lift.
* **crossing** — a piercing self-crossing of the composition
  (`tools.tracebench.counters.crossing_points`, the frozen v2 detector).
* **retrace turn** — the mid-point of a retrace zone
  (`tools.tracebench.counters.structure_zones`, same detector family).
* **corner (Umkehrpunkt)** — a within-stroke reversal, tested with the
  DERIVATION's own construction and constants, imported not restated:
  the turn over ``core.pipeline.CORNER_WINDOW_UNITS`` above
  ``core.pipeline.CORNER_ANGLE_DEG``. That is the same test whose stored
  output is a template's ``corner_anchors``, so "authored corner" and
  "detected corner" are one notion rather than two that can drift. Reading it
  off the COMPOSED geometry is deliberate: the composer places a letter with
  more than a translation, and reversing that transform here would be a second
  implementation of it. The test cannot swallow what the sensor hunts —
  75° is a reversal, the sensor's own threshold is 11.5°.

The four exclusions are COUNTED, never silently dropped (``excluded``), so a
word that reports few samples says why.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from core.continuity import (
    BOW_CHORD_UNITS,
    KINK_THRESHOLD_DEG,
    KINK_WINDOW_UNITS,
    LANDMARK_RADIUS_UNITS,
    kink_events,
    near_landmarks,
    stroke_profile,
)
from tools.tracebench.counters import crossing_points, structure_zones
from tools.tracebench.soll import composition_strokes
from tools.wordbench.seam import strip_overlap


__all__ = ["BOW_CHORD_UNITS", "KINK_THRESHOLD_DEG", "KINK_WINDOW_UNITS", "LANDMARK_RADIUS_UNITS", "continuity"]


def _round(value: float | None, digits: int) -> float | None:
    return None if value is None else round(float(value), digits)


def _pen_path_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The items with every connector's ``_overlap_extend`` tuck removed.

    ``core.compose`` extends each open connector end by ``CONNECT_OVERLAP``
    along the local tangent so the round cap tucks UNDER the neighbouring ink.
    That tuck is a rendering detail, not pen travel: concatenated into a pen
    stroke it reads as a ~180° fold at every seam and would be the loudest
    "kink" in the word — an artifact of the renderer, measured as a defect.
    ``seam.strip_overlap`` is the frozen remover, reused rather than restated.
    """
    out: list[dict[str, Any]] = []
    for item in items:
        if "rings" in item or not item.get("centerline"):
            out.append(item)
            continue
        trimmed = dict(item)
        trimmed["centerline"] = strip_overlap(item["centerline"])
        out.append(trimmed)
    return out


def _join_points(items: list[dict[str, Any]]) -> np.ndarray:
    """The samples of every GENERATED connector, as one point array.

    A join's neighbourhood is what tintenfolger.md §7.9 asks the Pfeilhöhe for
    („des letzten Zugs vor einem Scheitel bzw. des ersten nach einem
    Austritt, je Join"), and it is the region the owner's principle is about.
    The predicate is `score_word`'s own: an item without ``rings`` is a
    connector.
    """
    lines = [np.asarray(it["centerline"], dtype=float) for it in items if "rings" not in it and it.get("centerline")]
    return np.vstack(lines) if lines else np.zeros((0, 2))


def _empty(n_samples: int, excluded: dict[str, int]) -> dict[str, Any]:
    return {
        "n_samples": n_samples,
        "n_measured": 0,
        "excluded": excluded,
        "kink_max_deg": None,
        "kink_count": 0,
        "wobble": None,
        "bow_median": None,
        "bow_join": None,
        "curv_loss": None,
        "kinks": [],
    }


def continuity(composed: dict[str, Any]) -> dict[str, Any]:
    """Continuity columns for one composed entry.

    Args:
        composed: a ``compose_word(...)`` result. ``provenance=True`` is not
            required — the sensor reads only ``centerline``, ``lift`` and the
            presence of ``rings``.

    Returns:
        ``{"n_samples", "n_measured", "excluded", "kink_max_deg", "kink_count",
        "wobble", "bow_median", "bow_join", "curv_loss", "kinks"}``. Every
        aggregate is ``None`` when no sample survived the exclusions (a short
        word can be shorter than the margins), never a fabricated zero.
    """
    items = _pen_path_items(composed.get("items", []))
    strokes = composition_strokes(items)
    profiles = [p for st in strokes if (p := stroke_profile(st)) is not None]
    excluded = {"lift": 0, "cross": 0, "retrace": 0, "corner": 0}
    if not profiles:
        return _empty(int(sum(len(st) for st in strokes)), excluded)

    crossings = crossing_points(strokes)
    zones = structure_zones(strokes)
    joins = _join_points(items)
    kinks: list[dict] = []
    kink_vals: list[np.ndarray] = []
    wobble_vals: list[np.ndarray] = []
    bow_vals: list[np.ndarray] = []
    bow_join_vals: list[np.ndarray] = []
    deficit_vals: list[np.ndarray] = []
    n_samples = 0
    for prof in profiles:
        pts = prof["pts"]
        n_samples += len(pts)
        at_cross = near_landmarks(pts, crossings)
        at_retrace = near_landmarks(pts, zones.retrace_mids)
        at_corner = near_landmarks(pts, pts[prof["corner"]])
        measured = prof["inside"] & ~at_cross & ~at_retrace & ~at_corner
        # Counted, never silently dropped — and attributed to ONE cause each,
        # in the order lift → crossing → retrace → corner, so the four numbers
        # sum to the samples that were left out.
        excluded["lift"] += int((~prof["inside"]).sum())
        excluded["cross"] += int((prof["inside"] & at_cross).sum())
        excluded["retrace"] += int((prof["inside"] & ~at_cross & at_retrace).sum())
        excluded["corner"] += int((prof["inside"] & ~at_cross & ~at_retrace & at_corner).sum())
        if not measured.any():
            continue
        kinks.extend(kink_events(prof["kink"], measured, pts, prof["s"]))
        kink_vals.append(prof["kink"][measured])
        wobble_vals.append(prof["wobble"][measured & prof["wobble_valid"]])
        bow_vals.append(prof["bow"][measured])
        bow_join_vals.append(prof["bow"][measured & near_landmarks(pts, joins)])
        deficit_vals.append(prof["deficit"][measured & prof["deficit_valid"]])

    if not kink_vals:
        return _empty(n_samples, excluded)
    kink_all = np.concatenate(kink_vals)
    wobble_all = np.concatenate(wobble_vals)
    bow_join_all = np.concatenate(bow_join_vals)
    deficit_all = np.concatenate(deficit_vals)
    return {
        "n_samples": n_samples,
        "n_measured": int(len(kink_all)),
        "excluded": excluded,
        "kink_max_deg": _round(kink_all.max(), 2),
        "kink_count": len(kinks),
        "wobble": _round(math.sqrt(float(np.mean(wobble_all**2))), 3) if len(wobble_all) else None,
        "bow_median": _round(np.median(np.concatenate(bow_vals)), 4),
        "bow_join": _round(np.median(bow_join_all), 4) if len(bow_join_all) else None,
        "curv_loss": _round(deficit_all.max(), 4) if len(deficit_all) else None,
        "kinks": kinks,
    }
