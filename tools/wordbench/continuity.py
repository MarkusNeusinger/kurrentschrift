"""Report-only continuity of the composed word centreline — where the pen
changes direction at a place that is not a ductus event.

The owner's perceptual principle (2026-09-06) states what the eye actually
reads, and it is not a shape distance:

    „Direkt ins Auge stechen Übergänge, die mitten im Übergang Wackler drin
    haben oder in einem Punkt einen Knick haben, weil sie von 30° Steigung
    plötzlich auf 40° wechseln und davor und danach eine perfekte Linie
    haben. Es kommt nicht so auf den genauen Winkel an, ob es wirklich
    gerade ist oder der Kreis einen Radius von x oder y hat — die
    plötzlichen Änderungen an Stellen, wo sie nichts zu suchen haben, weil
    da kein Richtungswechsel ist, fallen extrem als unnatürlich auf."

Every frozen ruler in the repo measures the opposite quantity. ``bench_loss``
is a chamfer against the specimen skeleton, ``dtw_xh`` a point-to-point
distance, ``dconn``/``dspan`` a connector-shape distance: all of them ask HOW
FAR the path sits from a reference, none of them asks whether the path is
CONTINUOUS with itself. A kink and a smooth bow through the same two endpoints
score the same, which is why `stem_depart` could pass every gate in
humanbench round 6 while the judge gave 20 of 21 screens to the base arm.

This module is the sensor that names the quantity. It is REPORT-ONLY in the
strict sense — consumed by tools/wordbench/run.py as extra columns, never part
of ``bench_loss``/``pair_loss``, and ``core/word_metric.py`` is untouched
(precedent: the slant column, the Gleichzug audit, the ``meas`` columns and
the seam angles).

WHAT IS MEASURED, precisely — everything in TEMPLATE UNITS (1 = x-height),
angles in degrees, on the composed PEN STROKES (`tools.tracebench.soll.
composition_strokes`: items concatenate until one carries ``lift``, so a
stroke is one pen-down run and a lift is a stroke boundary by construction).

One scale ladder, anchored on the pen and frozen (see the constants below):
half a nib (``KINK_WINDOW_UNITS`` 0.0725) · one nib (the margin and landmark
radius, 0.145) · two nibs (``BOW_CHORD_UNITS`` 0.29).

* **Knick — order 1, the tangent discontinuity.** At each sample, the SIGNED
  turn between the chord reaching back one window and the chord running
  forward one window is taken at TWO windows, W and 2W, and combined as

      kink = |2 · turn(W) − turn(2W)|

  which is the turn CONCENTRATED at the point. It is exactly 0 for a circular
  arc of ANY radius (turn grows linearly with the window), and exactly the
  kink angle for a corner between two straight lines. That is the owner's
  sentence made arithmetic: the radius does not matter, the sudden change
  does. Reported as ``kink_max_deg`` and ``kink_count`` — the events above
  ``KINK_THRESHOLD_DEG``, one per kink (see ``_events``: the response to a
  single kink spans 4·W₁ of arc, so peaks closer than that are one event).
* **Wackler — order 1, the oscillation.** The travel heading over W, unwrapped,
  minus its arc-length-weighted moving average over the long chord: a
  high-pass on the direction profile. A straight run and a clean arc both give
  ~0 (a linear trend survives its own centred average), a path that wanders
  left-right-left does not. Reported as ``wobble``, the RMS in degrees.
* **Bogen und Krümmungsverlust — order 2.** ``bow`` is the Pfeilhöhe over the
  chord: the perpendicular distance from the sample to the chord between the
  two points one half of ``BOW_CHORD_UNITS`` away along the path — the same
  quantity tintenfolger.md §7.9 asks for by name in the round-6 rescue path.
  ``curv_loss`` is the deepest FLAT SPOT bracketed by bow: at each sample,
  ``max(0, min(bow(s−W₂), bow(s+W₂)) − bow(s))``, maximised over the word.
  Both neighbours must bow, so leaving an arc into a stem (a legitimate
  flattening) does not fire — only a bow that became a chord in the middle
  does, which is precisely what the round-6 handover did to the Anstrich.

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

Frozen: the constants below are the sensor, and they do not follow a fixture
root. ``KINK_WINDOW_UNITS`` is the half nib of the frozen Sütterlin-1922 root
(``constant_nib_units`` 0.07243…) rounded to four places ONCE — a re-export
must not be able to move a sensor that a §14 entry quotes.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from core.pipeline import CORNER_ANGLE_DEG, CORNER_WINDOW_UNITS
from tools.tracebench.counters import crossing_points, structure_zones
from tools.tracebench.soll import composition_strokes
from tools.wordbench.seam import strip_overlap


# --------------------------------------------------------------- the constants
# Half the pen's ink width, in x-height units: the frozen Sütterlin-1922 root
# writes at `constant_nib_units` = 0.07243… as a HALF width, so the ink is
# 0.145 xh wide. Half a nib is the shortest stretch over which a direction can
# be read at all — below it the stroke's own thickness masks the change — and
# it sits deliberately BELOW `core.compose.TANGENT_WINDOW` (0.12), the window
# the composer aligns its connector launches on, so the sensor never measures
# the composer against its own construction (the same reasoning as
# `seam.SEAM_WINDOW`).
KINK_WINDOW_UNITS = 0.0725
# Two nib widths: the chord the Pfeilhöhe is taken over. Shorter than this a
# bow is not a bow but a thickened line, because a sagitta under half a nib
# hides inside the ink.
BOW_CHORD_UNITS = 4.0 * KINK_WINDOW_UNITS
# One nib width. Three jobs, one number by construction (2·W₁ = W₂/2): the
# arc-length margin every window needs at a stroke end, the radius around a
# landmark, and therefore the guarantee that no measurement window contains
# either.
LANDMARK_RADIUS_UNITS = 2.0 * KINK_WINDOW_UNITS
# A direction change counts as a Knick once the path leaves its smooth
# continuation by a TENTH of the ink width over one reading window. The ratio
# is nib-independent by construction: the deviation is W₁·sin(θ) and the ink is
# 2·W₁ wide, so 0.1·(2·W₁)/W₁ = 0.2 whatever the pen. arcsin(0.2) = 11.537°.
KINK_THRESHOLD_DEG = math.degrees(math.asin(0.2))
# Below this many samples a stroke carries no window at all.
_MIN_SAMPLES = 4


def _wrap180(deg: np.ndarray) -> np.ndarray:
    """Angles folded into (−180, 180] — the same convention as `seam._wrap180`."""
    return -((180.0 - deg) % 360.0 - 180.0)


def _interp_xy(pts: np.ndarray, s: np.ndarray, targets: np.ndarray) -> np.ndarray:
    """The polyline's points at given arc lengths (linear along the chords)."""
    return np.column_stack([np.interp(targets, s, pts[:, 0]), np.interp(targets, s, pts[:, 1])])


def _signed_turn_deg(pts: np.ndarray, s: np.ndarray, window: float) -> np.ndarray:
    """Signed turn between the chord reaching back and the chord running forward.

    The construction `core.pipeline._detect_corners` uses (chords spanning
    `window` of arc on either side), kept signed so turns at two windows can be
    subtracted — a circular arc must cancel, and it only does with a sign.
    """
    back = _interp_xy(pts, s, s - window)
    fwd = _interp_xy(pts, s, s + window)
    din = pts - back
    dout = fwd - pts
    ang = np.arctan2(dout[:, 1], dout[:, 0]) - np.arctan2(din[:, 1], din[:, 0])
    return np.degrees(np.arctan2(np.sin(ang), np.cos(ang)))


def _moving_mean(values: np.ndarray, s: np.ndarray, width: float) -> np.ndarray:
    """Arc-length-weighted centred moving average of `values` over `width`.

    Via the cumulative integral, so it is exact for the non-uniform sampling a
    composed centreline has and costs one pass rather than a window per sample.
    """
    integral = np.concatenate([[0.0], np.cumsum(0.5 * (values[:-1] + values[1:]) * np.diff(s))])
    lo = np.clip(s - 0.5 * width, s[0], s[-1])
    hi = np.clip(s + 0.5 * width, s[0], s[-1])
    span = hi - lo
    span[span <= 0] = 1.0
    return (np.interp(hi, s, integral) - np.interp(lo, s, integral)) / span


def _bow(pts: np.ndarray, s: np.ndarray, chord: float) -> np.ndarray:
    """Pfeilhöhe: distance from each sample to the chord between the two points
    half a `chord` away along the path (0 on a straight run, the sagitta on an
    arc)."""
    a = _interp_xy(pts, s, s - 0.5 * chord)
    b = _interp_xy(pts, s, s + 0.5 * chord)
    ab = b - a
    ap = pts - a
    length = np.hypot(ab[:, 0], ab[:, 1])
    cross = np.abs(ab[:, 0] * ap[:, 1] - ab[:, 1] * ap[:, 0])
    return np.divide(cross, length, out=np.zeros_like(cross), where=length > 1e-12)


def _stroke_profile(pts: np.ndarray) -> dict[str, np.ndarray] | None:
    """The per-sample profiles of one pen stroke, or None if it is too short.

    Each measured quantity ships with the validity mask its own window chain
    needs; the shared `inside` mask is only the one every window needs.
    """
    if len(pts) < _MIN_SAMPLES:
        return None
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(s[-1])
    if total <= 2.0 * LANDMARK_RADIUS_UNITS:
        return None
    # Strictly increasing arc length: `np.interp` needs it, and a composed
    # centreline can repeat a point where two items meet.
    keep = np.concatenate([[True], np.diff(s) > 1e-12])
    pts, s = pts[keep], s[keep]
    if len(pts) < _MIN_SAMPLES:
        return None

    w = KINK_WINDOW_UNITS
    # The turn concentrated at the point: zero for an arc of any radius, the
    # kink angle for a corner between two straight lines. Wrapped like every
    # other angle difference here, so the arbitrary sign a near-180° reversal
    # gives its two constituents cannot inflate the combination.
    kink = np.abs(_wrap180(2.0 * _signed_turn_deg(pts, s, w) - _signed_turn_deg(pts, s, 2.0 * w)))
    # Travel heading over the centred window, high-passed against its own trend.
    span = _interp_xy(pts, s, s + w) - _interp_xy(pts, s, s - w)
    heading = np.degrees(np.unwrap(np.arctan2(span[:, 1], span[:, 0])))
    wobble = heading - _moving_mean(heading, s, BOW_CHORD_UNITS)
    bow = _bow(pts, s, BOW_CHORD_UNITS)
    # The flat spot bracketed by bow, one full chord away on BOTH sides — a
    # single-sided flattening (leaving an arc into a stem) is ductus, not loss.
    deficit = np.maximum(
        0.0, np.minimum(np.interp(s - BOW_CHORD_UNITS, s, bow), np.interp(s + BOW_CHORD_UNITS, s, bow)) - bow
    )

    # The corner (Umkehrpunkt) test, with the derivation's own window and
    # angle — and only where that window FITS. Where it runs off the stroke,
    # `_interp_xy` clamps to the endpoint and the incoming chord degenerates
    # to near-zero, whose direction is noise: every stroke end would flag as a
    # corner and its exemption radius would swallow real kinks a nib away.
    # `_detect_corners` excludes the same band by construction.
    corner = (np.abs(_signed_turn_deg(pts, s, CORNER_WINDOW_UNITS)) >= CORNER_ANGLE_DEG) & (
        (s >= CORNER_WINDOW_UNITS) & (s <= total - CORNER_WINDOW_UNITS)
    )
    # Every window fits: this is the lift margin, and it covers 2·W₁ and W₂/2.
    inside = (s >= LANDMARK_RADIUS_UNITS) & (s <= total - LANDMARK_RADIUS_UNITS)
    # Each statistic states the margin its OWN window chain needs, rather than
    # inflating the shared one — an end margin costs samples everywhere.
    # `wobble` detrends the heading, and the heading itself already spans ±W₁,
    # so its trend window needs W₂/2 + W₁ = 3·W₁ of clean path on either side;
    # inside that the average would be taken over headings whose chord ran off
    # the stroke, and a clean arc would read as a wobble.
    wobble_valid = (s >= 3.0 * KINK_WINDOW_UNITS) & (s <= total - 3.0 * KINK_WINDOW_UNITS)
    # `deficit` reads `bow` a full chord out on either side, and outside the
    # stroke `np.interp` would clamp to an end value taken over a chord that
    # ran off the path. Only where both neighbours are real is it a reading.
    deficit_valid = (s >= BOW_CHORD_UNITS + LANDMARK_RADIUS_UNITS) & (
        s <= total - BOW_CHORD_UNITS - LANDMARK_RADIUS_UNITS
    )
    return {
        "pts": pts,
        "s": s,
        "kink": kink,
        "bow": bow,
        "wobble": wobble,
        "wobble_valid": wobble_valid,
        "deficit": deficit,
        "deficit_valid": deficit_valid,
        "corner": corner,
        "inside": inside,
    }


def _near(pts: np.ndarray, marks: np.ndarray) -> np.ndarray:
    """Which samples lie within one nib of any landmark point."""
    if len(marks) == 0:
        return np.zeros(len(pts), dtype=bool)
    d = np.hypot(pts[:, None, 0] - marks[None, :, 0], pts[:, None, 1] - marks[None, :, 1])
    return d.min(axis=1) < LANDMARK_RADIUS_UNITS


def _events(kink: np.ndarray, measured: np.ndarray, pts: np.ndarray, s: np.ndarray) -> list[dict]:
    """One event per kink, at its sharpest sample.

    A single kink does not answer at a single sample: while the reading window
    slides across it, one of the two chords straddles it, so the response is
    supported over 2·W₁ on either side and can dip below the threshold inside
    that support. The whole response to ONE kink therefore lives in 4·W₁ of arc
    — which is ``BOW_CHORD_UNITS`` — so peaks closer together than that are one
    event, resolved greedily in favour of the sharpest. Same construction as
    the derivation's own non-max suppression, at this sensor's window.
    """
    flag = measured & (kink > KINK_THRESHOLD_DEG)
    if not flag.any():
        return []
    edges = np.flatnonzero(np.diff(np.concatenate([[False], flag, [False]]).astype(np.int8)))
    peaks = [a + int(np.argmax(kink[a:b])) for a, b in zip(edges[::2], edges[1::2], strict=True)]
    kept: list[int] = []
    for peak in sorted(peaks, key=lambda i: -kink[i]):
        if all(abs(s[peak] - s[other]) >= BOW_CHORD_UNITS for other in kept):
            kept.append(peak)
    return [
        {"deg": round(float(kink[i]), 2), "at": [round(float(pts[i, 0]), 4), round(float(pts[i, 1]), 4)]}
        for i in sorted(kept)
    ]


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
    profiles = [p for st in strokes if (p := _stroke_profile(st)) is not None]
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
        at_cross = _near(pts, crossings)
        at_retrace = _near(pts, zones.retrace_mids)
        at_corner = _near(pts, pts[prof["corner"]])
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
        kinks.extend(_events(prof["kink"], measured, pts, prof["s"]))
        kink_vals.append(prof["kink"][measured])
        wobble_vals.append(prof["wobble"][measured & prof["wobble_valid"]])
        bow_vals.append(prof["bow"][measured])
        bow_join_vals.append(prof["bow"][measured & _near(pts, joins)])
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
