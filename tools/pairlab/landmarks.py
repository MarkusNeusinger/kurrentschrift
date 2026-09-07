"""The INK counterpart of the self-crossing landmarks, and their frozen names.

A letter has a fixed STRUCTURE — loop, crossing, bowl, in a fixed order — and
what moves per occurrence and per transition is where that structure sits.
`qualitaetsmetrik.md` §13a measured exactly that on the Sütterlin `d`: the INK
self-crossing of a joined `d` sits 0.243 xh lower than a word-final one
(p = 0.005, 19x the within-word noise), while the FIT reproduces the TEMPLATE
crossing to 0.002 xh and follows the ink by 0.011 xh (p = 0.43). Every fitted
anchor is 0.019–0.046 xh from the ink, so the landmark error is ~6x the mean
anchor residual: the fit is accurate everywhere and the structure is still
wrong. That is an ASSIGNMENT problem, not an accuracy one.

Such an assignment needs two halves, and they now live in two places:

* the DUCTUS half — `landmark_crossings`, where the polyline crosses ITSELF, as
  a proper intersection of two of its chords with the two chord parameters, so
  a consumer can express the crossing as a LINEAR function of four anchors —
  moved verbatim to `core.landmarks` and re-exported below. It moved because
  the admin's Landmarken-Linse serves it over HTTP and `api/` may not import
  `tools/` (`tests/test_imports.py`); the thresholds and their §13a provenance
  travelled with it, unchanged.
* the INK half — `skeleton_branch_points` + `nearest_unique_point`, kept here,
  with an explicit refusal to guess: a crossing whose nearest branch point is
  too far away, or whose second-nearest is nearly as close, has no defensible
  correspondence and must be DROPPED rather than assigned. It stays in the
  measurement layer because only a duel has a skeleton to read.

Pure geometry either way: numpy, `scipy.ndimage` and the moved detector, no
I/O, no DB, no rendering — so any consumer (the chain objective, a census
script, a test) still reads the identical detector.

`core.geometry.detect_crossing_passages` answers a different question on the
same phenomenon — which SAMPLES sit in a crossing blob, for the width
contamination list — and returns no intersection point at all. The two are
deliberately separate; §13a's census of 43 landmarks over 26 of 34 frozen
glyph rows was taken with the thresholds the moved module carries.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import center_of_mass, label

from core.landmarks import (
    LANDMARK_MERGE_RADIUS_UNITS,
    LANDMARK_MIN_ANGLE_DEG,
    LANDMARK_MIN_ARC_SEPARATION_UNITS,
    LANDMARK_MIN_INDEX_GAP,
    SelfIntersection,
    landmark_crossings,
    polyline_self_intersections,
)


# --------------------------------------------------------------- the ink side


def skeleton_branch_points(skel: np.ndarray) -> np.ndarray:
    """`(n, 2)` `(x, y)` pixel centroids of the thinned skeleton's branch points.

    A branch point is a skeleton pixel with at least three 8-neighbours. On a
    thinned skeleton one real crossing produces a small CLUSTER of such pixels
    (an X often thins to two adjacent 3-neighbour pixels, or one 4-neighbour
    pixel), so 8-connected clusters are collapsed to their centroid — otherwise
    one crossing would offer two candidates and every assignment would look
    ambiguous.
    """
    m = np.asarray(skel, dtype=bool)
    if m.ndim != 2 or not m.any():
        return np.zeros((0, 2))
    pad = np.pad(m, 1).astype(np.int8)
    h, w = m.shape
    nb = np.zeros((h, w), dtype=np.int8)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            if dy == 1 and dx == 1:
                continue
            nb += pad[dy : dy + h, dx : dx + w]
    branch = m & (nb >= 3)
    if not branch.any():
        return np.zeros((0, 2))
    labels, n = label(branch, structure=np.ones((3, 3), dtype=int))
    centres = center_of_mass(branch, labels, range(1, n + 1))
    return np.asarray([(float(c), float(rr)) for rr, c in centres], dtype=float).reshape(-1, 2)


def nearest_unique_point(
    candidates: np.ndarray, point: tuple[float, float] | np.ndarray, *, radius: float, margin: float
) -> tuple[np.ndarray | None, str, float]:
    """The one candidate that unambiguously corresponds to `point`.

    Returns `(candidate | None, reason, distance)`. `reason` is `"ok"`,
    `"no_candidate"` (nothing within `radius`) or `"ambiguous"` (the
    second-nearest lies within `margin` of the nearest's distance, so which of
    the two the crossing belongs to is not decidable from proximity).

    A guessed correspondence is worse than none: it would state "this point
    belongs on that point" about a point picked by a coin flip, and the
    objective would then pull the structure onto the wrong pass. §13a's census
    reports the clean case — the `d` has exactly one candidate within 0.55 xh in
    14 of 14 occurrences — but explicitly warns that other glyphs are not so
    clean, which is what this refusal is for.
    """
    cand = np.asarray(candidates, dtype=float).reshape(-1, 2)
    if not len(cand):
        return None, "no_candidate", float("inf")
    d = np.hypot(cand[:, 0] - float(point[0]), cand[:, 1] - float(point[1]))
    order = np.argsort(d)
    d1 = float(d[order[0]])
    if d1 > radius:
        return None, "no_candidate", d1
    if len(order) > 1 and float(d[order[1]]) - d1 < margin:
        return None, "ambiguous", d1
    return cand[order[0]].copy(), "ok", d1


__all__ = [
    "LANDMARK_MERGE_RADIUS_UNITS",
    "LANDMARK_MIN_ANGLE_DEG",
    "LANDMARK_MIN_ARC_SEPARATION_UNITS",
    "LANDMARK_MIN_INDEX_GAP",
    "SelfIntersection",
    "landmark_crossings",
    "nearest_unique_point",
    "polyline_self_intersections",
    "skeleton_branch_points",
]
