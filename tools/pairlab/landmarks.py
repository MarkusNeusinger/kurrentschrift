"""Self-crossing LANDMARKS of a ductus polyline, and their ink counterpart.

A letter has a fixed STRUCTURE — loop, crossing, bowl, in a fixed order — and
what moves per occurrence and per transition is where that structure sits.
`qualitaetsmetrik.md` §13a measured exactly that on the Sütterlin `d`: the INK
self-crossing of a joined `d` sits 0.243 xh lower than a word-final one
(p = 0.005, 19x the within-word noise), while the FIT reproduces the TEMPLATE
crossing to 0.002 xh and follows the ink by 0.011 xh (p = 0.43). Every fitted
anchor is 0.019–0.046 xh from the ink, so the landmark error is ~6x the mean
anchor residual: the fit is accurate everywhere and the structure is still
wrong. That is an ASSIGNMENT problem, not an accuracy one.

This module supplies the two halves such an assignment needs, and nothing else:

* `landmark_crossings` — where the polyline crosses ITSELF, as a proper
  intersection of two of its chords with the two chord parameters, so a
  consumer can express the crossing as a LINEAR function of four anchors.
* `skeleton_branch_points` + `nearest_unique_point` — the ink counterpart, with
  an explicit refusal to guess: a crossing whose nearest branch point is too
  far away, or whose second-nearest is nearly as close, has no defensible
  correspondence and must be DROPPED rather than assigned.

Pure geometry: numpy and `scipy.ndimage` only, no project imports, no I/O, no
DB, no rendering — the same rule `anchors.py` follows, so any consumer (the
chain objective, a census script, a test) reads the identical detector.

`core.geometry.detect_crossing_passages` answers a different question on the
same phenomenon — which SAMPLES sit in a crossing blob, for the width
contamination list — and returns no intersection point at all. The two are
deliberately separate; §13a's census of 43 landmarks over 26 of 34 frozen
glyph rows was taken with the thresholds below.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import center_of_mass, label


# Minimum acute angle (degrees) between the two crossing chords. Below it the
# two passes run along each other rather than across, and the intersection
# point slides freely along the shared direction — an ill-conditioned landmark.
# 15 deg is the threshold §13a's census was taken at (43 landmarks over 26 of
# the 34 frozen v0 rows, stable to 0.015 xh across the v0 -> v100 derivation).
LANDMARK_MIN_ANGLE_DEG = 15.0
# Minimum arc-length separation (xh) between the two passes, along the polyline,
# for a crossing WITHIN one pen stroke. It separates a real return-and-cross
# (a d's loop closing over its own downstroke) from a tight wiggle that happens
# to fold over itself. Same census, same provenance as the angle above.
LANDMARK_MIN_ARC_SEPARATION_UNITS = 0.35
# Chords closer than this many indices apart are not tested at all: neighbours
# share an anchor by construction, and a gap of 1 would report every corner.
LANDMARK_MIN_INDEX_GAP = 2
# Two qualifying crossings closer together than this (xh) are ONE crossing of
# the letter's structure, reported twice: where a pass grazes another almost
# tangentially, several chord pairs of the same geometric crossing satisfy the
# test (the `k`'s stem/loop, the `p`'s shoulder, the `f`'s stem). Merging them
# is not cosmetic — the term below normalises by the landmark count, so a
# double-reported crossing would silently weigh twice. The best-conditioned
# member (largest crossing angle) survives.
#
# The merge is also what reproduces §13a's census EXACTLY: over the 34 frozen
# v0 rows the raw detector finds 47 qualifying crossings on 26 rows, and after
# the merge it finds the reported 43 on the same 26 rows.
LANDMARK_MERGE_RADIUS_UNITS = 0.05
# Chords shorter than this (in the anchor array's own units) carry no reliable
# direction; a template's anchors are stored rounded to 4 decimals, so a
# coincident pair is a real possibility.
_MIN_CHORD = 1e-9


@dataclass(frozen=True)
class SelfIntersection:
    """One proper self-intersection of a polyline.

    `seg_i` / `seg_j` are chord indices (chord `k` runs from anchor `k` to
    anchor `k + 1`), `t_i` / `t_j` the parameters along them, so

        point == (1 - t_i)·A[seg_i] + t_i·A[seg_i + 1]
              == (1 - t_j)·A[seg_j] + t_j·A[seg_j + 1]

    up to float noise. That form is the whole point: freeze the four indices
    and the two parameters and the crossing becomes a LINEAR function of four
    anchors, with an exact gradient.
    """

    seg_i: int
    seg_j: int
    t_i: float
    t_j: float
    point: tuple[float, float]
    angle_deg: float  # acute angle between the two chords, 90 = perpendicular
    arc_separation: float  # along-path distance between the two passes (inf across strokes)


def _stroke_bounds(k: int, stroke_starts: Sequence[int] | None) -> list[tuple[int, int]]:
    """`[(lo, hi), …]` anchor ranges of the pen strokes — `anchors.py`' rule."""
    bounds = sorted({0, *(int(s) for s in (stroke_starts or []) if 0 < int(s) < k), k})
    return list(zip(bounds[:-1], bounds[1:], strict=False))


def _chords(anchors: np.ndarray, stroke_starts: Sequence[int] | None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Real chords of the polyline: `(indices, stroke id, arc at the chord start)`.

    A chord that would bridge a PEN LIFT is not a chord — the hand set the pen
    down somewhere else, and the straight line between the two strokes was never
    written. Excluding it here is what keeps a phantom segment from producing a
    phantom crossing.
    """
    k = len(anchors)
    idx: list[int] = []
    sid: list[int] = []
    arc0: list[float] = []
    for s, (lo, hi) in enumerate(_stroke_bounds(k, stroke_starts)):
        seg = anchors[lo:hi]
        if len(seg) < 2:
            continue
        steps = np.hypot(*np.diff(seg, axis=0).T)
        arc = np.concatenate([[0.0], np.cumsum(steps)])
        for m in range(len(seg) - 1):
            idx.append(lo + m)
            sid.append(s)
            arc0.append(float(arc[m]))
    return np.asarray(idx, dtype=int), np.asarray(sid, dtype=int), np.asarray(arc0, dtype=float)


def polyline_self_intersections(
    anchors: np.ndarray, stroke_starts: Sequence[int] | None = None, *, min_index_gap: int = LANDMARK_MIN_INDEX_GAP
) -> list[SelfIntersection]:
    """Every proper self-intersection of the anchor polyline, in writing order.

    Two chords intersect properly when their parameters both lie in `[0, 1)` —
    half-open on purpose: a crossing landing exactly on an anchor is then
    reported by the chord that STARTS there and by no other, so it is counted
    once instead of twice or not at all.

    Pairs are skipped when they are closer than `min_index_gap` chords apart
    (neighbours share an anchor, so their "intersection" is that anchor) and
    when either chord would bridge a pen lift (`_chords`). Pairs from DIFFERENT
    pen strokes are tested — a t's crossbar over its stem is a genuine crossing
    — and get an infinite arc separation, since "far apart along the path" is
    meaningless between two separate passes.
    """
    anchors = np.asarray(anchors, dtype=float).reshape(-1, 2)
    idx, sid, arc0 = _chords(anchors, stroke_starts)
    if len(idx) < 2:
        return []
    p = anchors[idx]
    r = anchors[idx + 1] - p
    length = np.hypot(r[:, 0], r[:, 1])
    lo = np.minimum(p, p + r)
    hi = np.maximum(p, p + r)

    out: list[SelfIntersection] = []
    for a in range(len(idx)):
        if length[a] < _MIN_CHORD:
            continue
        for b in range(a + 1, len(idx)):
            if length[b] < _MIN_CHORD:
                continue
            if sid[a] == sid[b] and idx[b] - idx[a] < min_index_gap:
                continue
            if (hi[a] < lo[b]).any() or (hi[b] < lo[a]).any():
                continue  # disjoint bounding boxes
            denom = r[a, 0] * r[b, 1] - r[a, 1] * r[b, 0]
            if abs(denom) < _MIN_CHORD:
                continue  # parallel (or one chord degenerate)
            q = p[b] - p[a]
            t_a = (q[0] * r[b, 1] - q[1] * r[b, 0]) / denom
            t_b = (q[0] * r[a, 1] - q[1] * r[a, 0]) / denom
            if not (0.0 <= t_a < 1.0 and 0.0 <= t_b < 1.0):
                continue
            cos = abs(float(np.dot(r[a], r[b])) / (length[a] * length[b]))
            angle = float(np.degrees(np.arccos(min(1.0, cos))))
            if sid[a] == sid[b]:
                sep = abs((arc0[b] + t_b * length[b]) - (arc0[a] + t_a * length[a]))
            else:
                sep = float("inf")
            point = p[a] + t_a * r[a]
            out.append(
                SelfIntersection(
                    seg_i=int(idx[a]),
                    seg_j=int(idx[b]),
                    t_i=float(t_a),
                    t_j=float(t_b),
                    point=(float(point[0]), float(point[1])),
                    angle_deg=angle,
                    arc_separation=float(sep),
                )
            )
    return out


def landmark_crossings(
    anchors: np.ndarray,
    stroke_starts: Sequence[int] | None = None,
    *,
    min_angle_deg: float = LANDMARK_MIN_ANGLE_DEG,
    min_arc_units: float = LANDMARK_MIN_ARC_SEPARATION_UNITS,
    min_index_gap: int = LANDMARK_MIN_INDEX_GAP,
    merge_radius: float = LANDMARK_MERGE_RADIUS_UNITS,
) -> list[SelfIntersection]:
    """The WELL-CONDITIONED self-intersections — the landmarks of §13a's census.

    A crossing qualifies when the two chords meet at an acute angle of at least
    `min_angle_deg` AND, within one pen stroke, the two passes are at least
    `min_arc_units` apart along the path. Co-located qualifying crossings are
    merged to their best-conditioned member (`merge_radius`). None of the three
    thresholds is tuned here; each carries its provenance at the module's
    constants.
    """
    found = [
        x
        for x in polyline_self_intersections(anchors, stroke_starts, min_index_gap=min_index_gap)
        if x.angle_deg >= min_angle_deg and x.arc_separation >= min_arc_units
    ]
    kept: list[SelfIntersection] = []
    for x in sorted(found, key=lambda c: (-c.angle_deg, c.seg_i, c.seg_j)):
        if any(np.hypot(x.point[0] - y.point[0], x.point[1] - y.point[1]) <= merge_radius for y in kept):
            continue
        kept.append(x)
    return sorted(kept, key=lambda c: (c.seg_i, c.seg_j))


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
    "LANDMARK_MIN_ANGLE_DEG",
    "LANDMARK_MIN_ARC_SEPARATION_UNITS",
    "LANDMARK_MIN_INDEX_GAP",
    "SelfIntersection",
    "landmark_crossings",
    "nearest_unique_point",
    "polyline_self_intersections",
    "skeleton_branch_points",
]
