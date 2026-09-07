"""Continuity of a pen path — where a direction changes at a place that is not
a ductus event. The frozen arithmetic of the Unstetigkeits-Sensor (#558).

The owner's perceptual principle (2026-09-06) states what the eye actually
reads, and it is not a shape distance:

    „Direkt ins Auge stechen Übergänge, die mitten im Übergang Wackler drin
    haben oder in einem Punkt einen Knick haben, weil sie von 30° Steigung
    plötzlich auf 40° wechseln und davor und danach eine perfekte Linie
    haben. Es kommt nicht so auf den genauen Winkel an, ob es wirklich
    gerade ist oder der Kreis einen Radius von x oder y hat — die
    plötzlichen Änderungen an Stellen, wo sie nichts zu suchen haben, weil
    da kein Richtungswechsel ist, fallen extrem als unnatürlich auf."

This module is the arithmetic alone: given ONE pen path as a polyline in
template units (1 = x-height), it answers how much turning concentrates at a
point (Knick), how much the heading oscillates (Wackler), how far the path
bows, and where a bow flattened into a chord. It knows nothing about where the
path came from, so both consumers can share it exactly:

* `tools/wordbench/continuity.py` runs it on the COMPOSED word and exempts the
  ductus events it can name from the composition (lift · crossing · retrace ·
  reversal corner);
* `core/eigenhand/befund.py` runs it on the medial axis of the author's own
  written ink, where the exemption comes for free: a skeleton EDGE ends at
  every endpoint and every fork, so a measurement window never straddles one.

WHAT IS MEASURED, precisely — everything in TEMPLATE UNITS, angles in degrees.

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
  does. Events above ``KINK_THRESHOLD_DEG`` are counted one per kink (see
  ``kink_events``: the response to a single kink spans 4·W₁ of arc, so peaks
  closer than that are one event).
* **Wackler — order 1, the oscillation.** The travel heading over W, unwrapped,
  minus its arc-length-weighted moving average over the long chord: a
  high-pass on the direction profile. A straight run and a clean arc both give
  ~0 (a linear trend survives its own centred average), a path that wanders
  left-right-left does not. Reported as the RMS in degrees.
* **Bogen und Krümmungsverlust — order 2.** ``bow`` is the Pfeilhöhe over the
  chord: the perpendicular distance from the sample to the chord between the
  two points one half of ``BOW_CHORD_UNITS`` away along the path — the same
  quantity tintenfolger.md §7.9 asks for by name in the round-6 rescue path.
  ``deficit`` is the FLAT SPOT bracketed by bow: at each sample,
  ``max(0, min(bow(s−W₂), bow(s+W₂)) − bow(s))``. Both neighbours must bow, so
  leaving an arc into a stem (a legitimate flattening) does not fire — only a
  bow that became a chord in the middle does.

Frozen: the constants below are the sensor, and they do not follow a fixture
root. ``KINK_WINDOW_UNITS`` is the half nib of the frozen Sütterlin-1922 root
(``constant_nib_units`` 0.07243…) rounded to four places ONCE — a re-export
must not be able to move a sensor that a journal entry quotes. The module
moved here from `tools/wordbench/continuity.py` with the Streifen-Befund, so
the API image (which ships `core/` and not `tools/`) can serve a reading built
on it; the arithmetic did not change with the move, and the word sensor's
numbers are the same before and after.
"""

from __future__ import annotations

import math

import numpy as np

from core.pipeline import CORNER_ANGLE_DEG, CORNER_WINDOW_UNITS


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
MIN_SAMPLES = 4


def wrap180(deg: np.ndarray) -> np.ndarray:
    """Angles folded into (−180, 180] — the same convention as `seam._wrap180`."""
    return -((180.0 - deg) % 360.0 - 180.0)


def interp_xy(pts: np.ndarray, s: np.ndarray, targets: np.ndarray) -> np.ndarray:
    """The polyline's points at given arc lengths (linear along the chords)."""
    return np.column_stack([np.interp(targets, s, pts[:, 0]), np.interp(targets, s, pts[:, 1])])


def signed_turn_deg(pts: np.ndarray, s: np.ndarray, window: float) -> np.ndarray:
    """Signed turn between the chord reaching back and the chord running forward.

    The construction `core.pipeline._detect_corners` uses (chords spanning
    `window` of arc on either side), kept signed so turns at two windows can be
    subtracted — a circular arc must cancel, and it only does with a sign.
    """
    back = interp_xy(pts, s, s - window)
    fwd = interp_xy(pts, s, s + window)
    din = pts - back
    dout = fwd - pts
    ang = np.arctan2(dout[:, 1], dout[:, 0]) - np.arctan2(din[:, 1], din[:, 0])
    return np.degrees(np.arctan2(np.sin(ang), np.cos(ang)))


def moving_mean(values: np.ndarray, s: np.ndarray, width: float) -> np.ndarray:
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


def bow_heights(pts: np.ndarray, s: np.ndarray, chord: float) -> np.ndarray:
    """Pfeilhöhe: distance from each sample to the chord between the two points
    half a `chord` away along the path (0 on a straight run, the sagitta on an
    arc)."""
    a = interp_xy(pts, s, s - 0.5 * chord)
    b = interp_xy(pts, s, s + 0.5 * chord)
    ab = b - a
    ap = pts - a
    length = np.hypot(ab[:, 0], ab[:, 1])
    cross = np.abs(ab[:, 0] * ap[:, 1] - ab[:, 1] * ap[:, 0])
    return np.divide(cross, length, out=np.zeros_like(cross), where=length > 1e-12)


def stroke_profile(pts: np.ndarray) -> dict[str, np.ndarray] | None:
    """The per-sample profiles of one pen stroke, or None if it is too short.

    Each measured quantity ships with the validity mask its own window chain
    needs; the shared `inside` mask is only the one every window needs.
    """
    if len(pts) < MIN_SAMPLES:
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
    if len(pts) < MIN_SAMPLES:
        return None

    w = KINK_WINDOW_UNITS
    # The turn concentrated at the point: zero for an arc of any radius, the
    # kink angle for a corner between two straight lines. Wrapped like every
    # other angle difference here, so the arbitrary sign a near-180° reversal
    # gives its two constituents cannot inflate the combination.
    kink = np.abs(wrap180(2.0 * signed_turn_deg(pts, s, w) - signed_turn_deg(pts, s, 2.0 * w)))
    # Travel heading over the centred window, high-passed against its own trend.
    span = interp_xy(pts, s, s + w) - interp_xy(pts, s, s - w)
    heading = np.degrees(np.unwrap(np.arctan2(span[:, 1], span[:, 0])))
    wobble = heading - moving_mean(heading, s, BOW_CHORD_UNITS)
    bow = bow_heights(pts, s, BOW_CHORD_UNITS)
    # The flat spot bracketed by bow, one full chord away on BOTH sides — a
    # single-sided flattening (leaving an arc into a stem) is ductus, not loss.
    deficit = np.maximum(
        0.0, np.minimum(np.interp(s - BOW_CHORD_UNITS, s, bow), np.interp(s + BOW_CHORD_UNITS, s, bow)) - bow
    )

    # The corner (Umkehrpunkt) test, with the derivation's own window and
    # angle — and only where that window FITS. Where it runs off the stroke,
    # `interp_xy` clamps to the endpoint and the incoming chord degenerates
    # to near-zero, whose direction is noise: every stroke end would flag as a
    # corner and its exemption radius would swallow real kinks a nib away.
    # `_detect_corners` excludes the same band by construction.
    corner = (np.abs(signed_turn_deg(pts, s, CORNER_WINDOW_UNITS)) >= CORNER_ANGLE_DEG) & (
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


def near_landmarks(pts: np.ndarray, marks: np.ndarray) -> np.ndarray:
    """Which samples lie within one nib of any landmark point."""
    if len(marks) == 0:
        return np.zeros(len(pts), dtype=bool)
    d = np.hypot(pts[:, None, 0] - marks[None, :, 0], pts[:, None, 1] - marks[None, :, 1])
    return d.min(axis=1) < LANDMARK_RADIUS_UNITS


def kink_events(kink: np.ndarray, measured: np.ndarray, pts: np.ndarray, s: np.ndarray) -> list[dict]:
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


__all__ = [
    "BOW_CHORD_UNITS",
    "KINK_THRESHOLD_DEG",
    "KINK_WINDOW_UNITS",
    "LANDMARK_RADIUS_UNITS",
    "MIN_SAMPLES",
    "bow_heights",
    "interp_xy",
    "kink_events",
    "moving_mean",
    "near_landmarks",
    "signed_turn_deg",
    "stroke_profile",
    "wrap180",
]
