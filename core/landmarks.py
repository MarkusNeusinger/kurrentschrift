"""Structure landmarks of one ductus row — crossings, retraces, lifts, loops.

A letter has a fixed STRUCTURE — a loop here, a crossing there, a stretch the
pen writes twice — and that structure is a ductus fact, not a free variable of
any fit (`docs/proposals/optimierungs-werkbank.md` §3: the letters fix it, the
join classes add a known contribution). Until now only the measurement layer
could see it: the Tintenfolger counters detect it on both sides of a duel, the
Kringel sensor prints it beside the Duktus-Soll. The author, who authors the
ductus, could not — so a wrong crossing or a Kringel classified as a Punkt was
invisible on the very surface where it is authored.

This module is the shared home of the detectors, so the admin's Landmarken-Linse
(`/sources/{id}/templates/{key}/landmarks`) shows the SAME landmarks the bench
counts. It lives in `core/` for one hard reason: `core/`, `api/` and `alembic/`
must never import `tools/`, because the API image does not ship it
(`tests/test_imports.py`). Everything here was MOVED, not rewritten — the three
tools modules that owned it now re-export from here:

* `tools/pairlab/landmarks.py` — the self-intersection half (§13a's census);
* `tools/tracebench/counters.py` — the v2 pierce test and the retrace/touch/
  overlap classification (`messjournal.md` §14 `aug16`, the owner's audit);
* `tools/tracebench/kringel.py` — the loop aperture, its size class and its
  plate-read state (§14 `sep06`).

**Every threshold below is frozen measurement provenance.** Changing one does
not tune an admin overlay, it re-baselines the Tintenfolger and the Kringel
catalogue — read the entry named at the constant before touching it.

The catalogue file itself stays where it was built (`tools/tracebench/`), a
frozen artefact of the measurement layer, and is READ by path rather than
imported — the same arrangement the quiz seed data has. A missing or unreadable
catalogue costs the verdict column, never the answer.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from core.geometry import concat_strokes, detect_retrace_pairs, polyline_length, resample_by_step, stroke_bounds
from core.quality_suetterlin import MIN_RETRACE_PAIRS


# --------------------------------------------------------- self-crossings (§13a)

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
    for s, (lo, hi) in enumerate(stroke_bounds(k, stroke_starts)):
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


# ------------------------------------------ the v2 counters (§14 `aug16`)

# Common discretisation for both detectors — the same 0.02 xh the headline DTW
# resamples to (tintenfolger.md §2.3), so a counter never reads a finer or
# coarser path than the distance does.
RESAMPLE_STEP_UNITS = 0.02
# Proximity below which two passes count as the same ink for a retrace. In bench
# units, so it is a share of the x-height rather than of a scan resolution;
# `detect_retrace_pairs` derives its along-path separation from it (3x).
RETRACE_PROX_UNITS = 0.15  # tintenfolger.md §2.3
# Fewer flagged samples than this is a coincidental touch, not a retrace —
# mirrored from `core.quality_suetterlin.MIN_RETRACE_PAIRS` so the bench and the
# Sütterlin naturalness metric call the same thing a retrace.
RETRACE_MIN_PAIRS = MIN_RETRACE_PAIRS

# The pierce test's local window each side of an intersection, per pass, never
# across a stroke boundary. 0.25 xh reads the passes where they still describe
# THIS place in the word.
PIERCE_WINDOW_UNITS = 0.25
# Both window ends of the other pass must sit at least this far out on OPPOSITE
# sides of the local line: about half a stroke width — the other line has to
# come out beyond the ink's own body to have gone THROUGH it. Measured: every
# clean crossing clears 0.057, every owner-disputed tangency stays under 0.045.
PIERCE_MARGIN_UNITS = 0.05
# A retrace pass whose partner interval lies farther than this along the path
# is writing PAST the other line, not over it. Measured: genuine out-and-backs
# sit at 0.38–0.66 xh (the turnaround), the owner's touch cases at 1.16–8.34.
RETRACE_MAX_PARTNER_GAP_UNITS = 1.0
# A same-stroke pass shorter than this is a diverging cusp's graze, not a zone.
# Measured: cusps (laden l–a, linken l–i) flag 0.04–0.24 xh, genuine zones
# 0.36 xh and up.
RETRACE_MIN_PASS_ARC_UNITS = 0.30
# v2.1 (§14 `aug16`, Nachtrag): a ring whose two chords are each other's
# anti-parallel PARTNERS is the incidental self-crossing of one
# out-and-back-with-release — retrace-internal, not a structure crossing (the
# owner's rule „Retrace, bei dem sich eine Linie löst, ist keine Kreuzung",
# now applied to the ring the release itself draws). A chord "partners into"
# the other pass when flagged samples within this arc of it point there —
# the detector's own proximity radius, rounded up to whole samples. A retrace
# crossing FOREIGN ink (the linken Kringel passages) stays: its chords partner
# with their own return limbs, not with each other. Measured: exactly the
# owner's rings fall (unter-t 44,8°, mit-t 35,0°, zwei-w 24,0°, linken-k-exit
# 53,1°, partner-hits 4–13 both ways), every kept ring reads 0/0.
CROSS_PARTNER_NEAR_UNITS = 0.16
CROSS_PARTNER_MIN_HITS = 2

# The three meanings one anti-parallel-proximity detector carries (§14 v2).
PASS_CLASSES = ("retrace", "touch", "overlap")


def resampled_strokes(strokes: list[np.ndarray], step: float = RESAMPLE_STEP_UNITS) -> list[np.ndarray]:
    """Every stroke arc-length-resampled to one common step (lifts preserved)."""
    return [resample_by_step(s, step) for s in strokes if len(np.asarray(s).reshape(-1, 2))]


def _window_of(seg: int, bounds: list[tuple[int, int]], n_window: int) -> tuple[int, int]:
    """The sample window around chord `seg`, clipped to its own pen stroke."""
    lo, hi = next((a, b) for a, b in bounds if a <= seg < b)
    return max(lo, seg - n_window), min(hi - 1, seg + 1 + n_window)


def _pierces(
    pts: np.ndarray, bounds: list[tuple[int, int]], seg_i: int, seg_j: int, *, n_window: int, margin_units: float
) -> bool:
    """Does each pass go THROUGH the other's local line — in one side, out the other?

    A TLS line through each pass's window; the other pass's window ends must lie
    on opposite sides, both at least `margin_units` out. Coming in along the
    line and leaving to one side (the retrace release) fails on the near-zero
    end; a tangency fails on both.
    """
    for a_seg, b_seg in ((seg_i, seg_j), (seg_j, seg_i)):
        a_lo, a_hi = _window_of(a_seg, bounds, n_window)
        cloud = pts[a_lo : a_hi + 1]
        centre = cloud.mean(axis=0)
        _u, _s, v = np.linalg.svd(cloud - centre, full_matrices=False)
        direction = v[0]
        b_lo, b_hi = _window_of(b_seg, bounds, n_window)
        d0 = float(direction[0] * (pts[b_lo] - centre)[1] - direction[1] * (pts[b_lo] - centre)[0])
        d1 = float(direction[0] * (pts[b_hi] - centre)[1] - direction[1] * (pts[b_hi] - centre)[0])
        if not (d0 * d1 < 0.0 and abs(d0) >= margin_units and abs(d1) >= margin_units):
            return False
    return True


def crossing_landmarks(
    strokes_bench: list[np.ndarray], *, resample_step: float = RESAMPLE_STEP_UNITS
) -> list[SelfIntersection]:
    """The PIERCING self-crossings of one trace, kept as full landmarks.

    The whole trace becomes ONE point array plus its stroke starts, so a t-bar
    crossing its own stem is found while the line between two pen strokes — never
    written — cannot fabricate one. v2 (§14 `aug16`): a raw intersection counts
    when its two passes are at least the frozen arc separation apart AND pierce
    each other (`_pierces`); co-located survivors merge to the best-conditioned
    member, exactly the frozen detector's own merge rule.

    `crossing_points` below is this function reduced to the coordinate pairs the
    bench counts. The lens needs the rest — which two passes met, and how sharply
    — so the detector hands back the whole landmark and the counter takes its
    share, rather than the two answering the same question twice.
    """
    pts, starts = concat_strokes(resampled_strokes(strokes_bench, resample_step))
    if len(pts) < 2:
        return []
    bounds = stroke_bounds(len(pts), starts)
    n_window = max(2, int(round(PIERCE_WINDOW_UNITS / resample_step)))
    idx, partner = detect_retrace_pairs(pts[:, 0], pts[:, 1], starts, prox_px=RETRACE_PROX_UNITS)
    partner_of = dict(zip(idx.tolist(), partner.tolist(), strict=True))
    near = max(1, math.ceil(CROSS_PARTNER_NEAR_UNITS / resample_step))

    def _partners_into(a_seg: int, b_seg: int) -> int:
        return sum(
            1
            for k in range(max(0, a_seg - near), a_seg + near + 1)
            if partner_of.get(k) is not None and abs(int(partner_of[k]) - b_seg) <= near
        )

    def _retrace_internal(x: SelfIntersection) -> bool:
        return (
            _partners_into(x.seg_i, x.seg_j) >= CROSS_PARTNER_MIN_HITS
            and _partners_into(x.seg_j, x.seg_i) >= CROSS_PARTNER_MIN_HITS
        )

    found = [
        x
        for x in polyline_self_intersections(pts, starts)
        if x.arc_separation >= LANDMARK_MIN_ARC_SEPARATION_UNITS
        and not _retrace_internal(x)
        and _pierces(pts, bounds, x.seg_i, x.seg_j, n_window=n_window, margin_units=PIERCE_MARGIN_UNITS)
    ]
    kept: list[SelfIntersection] = []
    for x in sorted(found, key=lambda c: (-c.angle_deg, c.seg_i, c.seg_j)):
        if any(np.hypot(x.point[0] - y.point[0], x.point[1] - y.point[1]) <= LANDMARK_MERGE_RADIUS_UNITS for y in kept):
            continue
        kept.append(x)
    kept.sort(key=lambda c: (c.seg_i, c.seg_j))
    return kept


def crossing_points(strokes_bench: list[np.ndarray], *, resample_step: float = RESAMPLE_STEP_UNITS) -> np.ndarray:
    """The PIERCING self-crossings of one trace, as `(n, 2)` bench points."""
    kept = crossing_landmarks(strokes_bench, resample_step=resample_step)
    return np.asarray([x.point for x in kept], dtype=float).reshape(-1, 2)


def crossing_stroke_pair(landmark: SelfIntersection, bounds: Sequence[tuple[int, int]]) -> tuple[int, int]:
    """Which two pen strokes met at a crossing — the pair the lens names.

    Equal indices mean one stroke crossing ITSELF (the `d`'s loop over its own
    downstroke); different ones mean two passes met (the `t`'s bar over its
    stem), which is the distinction the author reads off the overlay.
    """

    def _stroke_of(seg: int) -> int:
        return next((s for s, (lo, hi) in enumerate(bounds) if lo <= seg < hi), 0)

    return _stroke_of(landmark.seg_i), _stroke_of(landmark.seg_j)


def _classified_passes(
    pts: np.ndarray, starts: list[int], *, prox_px: float, resample_step: float
) -> tuple[list[list[int]], list[str | None], dict[int, int]]:
    """`(passes, class per pass, partner map)` — the ONE place the class rule lives.

    Class per pass (§14 v2): "overlap" (partner in another pen stroke), "touch"
    (same stroke, partner interval farther than `RETRACE_MAX_PARTNER_GAP_UNITS`
    along the path), None (a diverging cusp's graze, shorter than
    `RETRACE_MIN_PASS_ARC_UNITS`), else "retrace".
    """
    if len(pts) < 2:
        return [], [], {}
    idx, partner = detect_retrace_pairs(pts[:, 0], pts[:, 1], starts, prox_px=prox_px)
    if not len(idx):
        return [], [], {}
    stroke_of = np.zeros(len(pts), dtype=int)
    for s, (lo, hi) in enumerate(stroke_bounds(len(pts), starts)):
        stroke_of[lo:hi] = s
    partner_of = dict(zip(idx.tolist(), partner.tolist(), strict=True))

    passes: list[list[int]] = []
    run: list[int] = []
    for i in [*np.sort(idx).tolist(), None]:
        contiguous = bool(run) and i is not None and i == run[-1] + 1 and stroke_of[i] == stroke_of[run[-1]]
        if contiguous:
            run.append(i)
            continue
        if len(run) >= RETRACE_MIN_PAIRS:
            passes.append(run)
        run = [] if i is None else [i]

    def classify(members: list[int]) -> str | None:
        partners = sorted(int(partner_of[k]) for k in members)
        if any(stroke_of[q] != stroke_of[members[0]] for q in partners):
            return "overlap"
        p_lo, p_hi = members[0], members[-1]
        q_lo, q_hi = partners[0], partners[-1]
        gap_samples = q_lo - p_hi if q_lo > p_hi else (p_lo - q_hi if p_lo > q_hi else 0)
        if gap_samples * resample_step > RETRACE_MAX_PARTNER_GAP_UNITS:
            return "touch"
        if polyline_length(pts[p_lo : p_hi + 1]) < RETRACE_MIN_PASS_ARC_UNITS:
            return None  # a diverging cusp's graze
        return "retrace"

    return passes, [classify(p) for p in passes], partner_of


def classified_pass_points(
    strokes_bench: list[np.ndarray], *, xh_px_equivalent: float = 1.0, resample_step: float = RESAMPLE_STEP_UNITS
) -> list[tuple[np.ndarray, str]]:
    """`(pass polyline, class)` per kept pass — display-grade access to the rule.

    The duel viewer and the admin's Landmarken-Linse draw exactly these, so what
    a page shows and what the counters count can never drift apart; grazes are
    dropped here as there.
    """
    pts, starts = concat_strokes(resampled_strokes(strokes_bench, resample_step))
    passes, cls_of, _partner_of = _classified_passes(
        pts, starts, prox_px=RETRACE_PROX_UNITS * float(xh_px_equivalent), resample_step=resample_step
    )
    return [(pts[p[0] : p[-1] + 1].copy(), cls) for p, cls in zip(passes, cls_of, strict=True) if cls is not None]


@dataclass(frozen=True)
class StructureZones:
    """One trace's classified anti-parallel-proximity structures (§14 v2)."""

    retrace_mids: np.ndarray = field(default_factory=lambda: np.zeros((0, 2)))
    retrace_arc: float = 0.0
    touch_mids: np.ndarray = field(default_factory=lambda: np.zeros((0, 2)))
    overlap_mids: np.ndarray = field(default_factory=lambda: np.zeros((0, 2)))


def structure_zones(
    strokes_bench: list[np.ndarray], *, xh_px_equivalent: float = 1.0, resample_step: float = RESAMPLE_STEP_UNITS
) -> StructureZones:
    """Zones per CLASS: retrace, touch, overlap — one detector, three meanings.

    `detect_retrace_pairs` flags the SAMPLES whose near-anti-parallel partner
    lies within `RETRACE_PROX_UNITS * xh_px_equivalent` — the scale factor exists
    so a caller working in crop pixels can reuse the same rule. Contiguous
    flagged samples of one pen stroke form a PASS; a pass thinner than
    `RETRACE_MIN_PAIRS` samples is dropped outright.

    Each pass is then classified (§14 v2, the owner's audit): a partner in
    ANOTHER pen stroke makes it an **overlap**; a same-stroke partner interval
    farther than `RETRACE_MAX_PARTNER_GAP_UNITS` along the path makes it a
    **touch** (writing past, not over); a same-stroke pass shorter than
    `RETRACE_MIN_PASS_ARC_UNITS` is a diverging cusp's graze and no zone at
    all; what remains is a **retrace**. Passes merge into zones per class via
    the partner relation (two limbs of one out-and-back are ONE zone —
    without the merge a `t` stem would report two structures a stroke width
    apart and the identity gate would refuse a trace against itself). The
    retrace arc stays the sum over the retrace passes: how much ink was
    written twice is a property of the pen travel, not of the zone cut.
    """
    pts, starts = concat_strokes(resampled_strokes(strokes_bench, resample_step))
    passes, cls_of, partner_of = _classified_passes(
        pts, starts, prox_px=RETRACE_PROX_UNITS * float(xh_px_equivalent), resample_step=resample_step
    )
    if not passes:
        return StructureZones()
    out: dict[str, np.ndarray] = {}
    retrace_arc = 0.0
    for cls in PASS_CLASSES:
        members_idx = [n for n, c in enumerate(cls_of) if c == cls]
        class_passes = [passes[n] for n in members_idx]
        zones = merge_partner_passes(class_passes, partner_of)
        mids = [
            np.mean([pts[class_passes[p][len(class_passes[p]) // 2]] for p in members], axis=0)
            for members in zones
            if members
        ]
        out[cls] = np.asarray(mids, dtype=float).reshape(-1, 2)
        if cls == "retrace":
            retrace_arc = sum(polyline_length(pts[p[0] : p[-1] + 1]) for p in class_passes)
    return StructureZones(
        retrace_mids=out["retrace"], retrace_arc=retrace_arc, touch_mids=out["touch"], overlap_mids=out["overlap"]
    )


def retrace_segments(
    strokes_bench: list[np.ndarray], *, xh_px_equivalent: float = 1.0, resample_step: float = RESAMPLE_STEP_UNITS
) -> tuple[np.ndarray, float]:
    """`(retrace zone midpoints, retraced arc)` — the retrace class of `structure_zones`."""
    zones = structure_zones(strokes_bench, xh_px_equivalent=xh_px_equivalent, resample_step=resample_step)
    return zones.retrace_mids, zones.retrace_arc


def merge_partner_passes(passes: list[list[int]], partner_of: dict[int, int]) -> list[list[int]]:
    """Group pass indices into zones — two passes that are each other's ink are one.

    Union-find over "a sample of pass A has its retrace partner in pass B". A
    triple pass (the rare stacked retrace) collapses into ONE zone by the same
    rule, which is what a zone means: a place the pen went over more than once.
    """
    owner = list(range(len(passes)))

    def root(a: int) -> int:
        while owner[a] != a:
            owner[a] = owner[owner[a]]
            a = owner[a]
        return a

    pass_of = {i: p for p, members in enumerate(passes) for i in members}
    for p, members in enumerate(passes):
        for i in members:
            other = pass_of.get(partner_of.get(i, -1))
            if other is not None and root(other) != root(p):
                owner[root(other)] = root(p)
    zones: dict[int, list[int]] = {}
    for p in range(len(passes)):
        zones.setdefault(root(p), []).append(p)
    return [zones[k] for k in sorted(zones)]


# ---------------------------------------------- the Kringel landmark (§14 `sep06`)

# The frozen catalogue is a measurement artefact and stays where it was built.
# READ by path, never imported: `core/` may not import `tools/` (the API image
# does not ship it), and the API's Dockerfile copies this one file in the same
# way it already copies the quiz seed data.
KRINGEL_CATALOGUE_FILE = Path(__file__).resolve().parents[1] / "tools" / "tracebench" / "kringel_catalogue.json"

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
# What a loop of THIS row gets when the catalogue has no row for it at all — a
# loop the catalogue never saw, which is a finding rather than a Punktkringel.
UNKNOWN = "unbekannt"


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


def catalogue_source(path: Path | None = None) -> dict[str, Any]:
    """The `_source` header of a catalogue file: which root and style it was read on."""
    payload = json.loads((path or KRINGEL_CATALOGUE_FILE).read_text(encoding="utf-8"))
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
    payload = json.loads((path or KRINGEL_CATALOGUE_FILE).read_text(encoding="utf-8"))
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


# ------------------------------------------------- the lens: one row's landmarks


@dataclass(frozen=True)
class Landmark:
    """One detected structure of a row, in TEMPLATE units (baseline 0, y up).

    `kind` is the vocabulary the Landmarken-Linse draws and the Auftragskorb
    files against: `crossing` · `retrace` · `touch` · `overlap` · `lift` ·
    `corner` · `loop`. `index` counts within the kind and is the handle a
    complaint names, so „Kringel #1 falsch klassiert" points at one thing.

    `numbers` carries the kind's own measured values (a crossing's angle, a
    loop's aperture, a zone's arc) — flat, JSON-safe and ready to travel into a
    work item so a session can reproduce what the author saw.
    """

    kind: str
    index: int
    x: float
    y: float
    numbers: dict[str, float | int | str | None]
    # The path a zone covers, in template units — empty for a point landmark.
    points: tuple[tuple[float, float], ...] = ()


@dataclass(frozen=True)
class RowLandmarks:
    """Every landmark of ONE stored template row, plus what stayed unseen.

    `unmatched_catalogue` is the honest half: the catalogue's Kringel rows that
    no loop of this row could be paired with. The `t` is the standing example —
    the plate holds three counters, the ductus finder has no loop range at all
    and the raster finder sees none on the isolated row — and an overlay that
    silently showed nothing there would be claiming the letter has no Kringel.
    """

    variant: int
    strokes: int
    n_anchors: int
    landmarks: tuple[Landmark, ...]
    loop_ranges: tuple[tuple[int, int], ...]
    unmatched_catalogue: tuple[dict[str, Any], ...]


def _loop_range_for(
    centre: tuple[float, float], anchors: np.ndarray, ranges: Sequence[tuple[int, int]]
) -> list[int] | None:
    """The anchor range whose own anchors sit closest to a loop's centre.

    The two finders answer different questions (`loop_apertures` rasterises the
    drawn curve, `core.aggregate.loop_ranges` reads the anchor polyline's
    self-crossings), so their outputs are matched by PROXIMITY rather than by
    rank — a rank match would hand the `p`'s belly range to its Kringel the
    moment one finder sees a loop the other merged away. `None` when there is
    no range at all, which is a finding, not a gap to fill.
    """
    if not len(ranges):
        return None
    best, best_d = None, float("inf")
    for lo, hi in ranges:
        seg = anchors[lo:hi]
        if not len(seg):
            continue
        d = float(np.hypot(*(seg.mean(axis=0) - np.asarray(centre, dtype=float))))
        if d < best_d:
            best, best_d = [int(lo), int(hi)], d
    return best


def row_landmarks(
    glyph_key: str,
    *,
    variant: int,
    anchors: Sequence[Sequence[float]],
    half_widths: Sequence[float],
    centerlines: Sequence[Sequence[Sequence[float]]],
    stroke_starts: Sequence[int] | None,
    corner_anchors: Sequence[int] | None,
    catalogue: Mapping[str, list[dict[str, Any]]] | None = None,
) -> RowLandmarks:
    """Every structure landmark of one stored row, ready for the lens.

    `centerlines` are the RENDERED per-stroke centerlines the page draws
    (`core.pipeline.render_payload_for_template`), so a marker sits on the ink
    the author is looking at rather than on the anchor polyline underneath it.
    The crossings and zones are therefore the same numbers the per-letter
    Duktus-Soll reports (`tools/tracebench/soll.py` counts exactly these two
    detectors over a slot's strokes) — the lens and the bench cannot disagree.

    The two ANCHOR-indexed kinds keep their anchor index: a lift is a pen
    stroke's first anchor, a corner one of `trace_meta.corner_anchors`. Both are
    authored facts of the chart ductus, which is why they are shown at all — the
    author is the only one who can say a corner is missing.
    """
    from core.aggregate import loop_ranges  # noqa: PLC0415 — one call site, keeps the import graph flat

    pts = np.asarray(anchors, dtype=float).reshape(-1, 2)
    # Kept UNFILTERED so index `i` still names pen stroke `i` when a lift is
    # placed on it below; the detectors get the drawable subset separately.
    all_strokes = [np.asarray(line, dtype=float).reshape(-1, 2) for line in centerlines]
    strokes = [s for s in all_strokes if len(s) >= 2]
    out: list[Landmark] = []

    resampled, starts = concat_strokes(resampled_strokes(strokes))
    bounds = stroke_bounds(len(resampled), starts)
    for i, cross in enumerate(crossing_landmarks(strokes)):
        stroke_i, stroke_j = crossing_stroke_pair(cross, bounds)
        out.append(
            Landmark(
                kind="crossing",
                index=i,
                x=round(cross.point[0], 4),
                y=round(cross.point[1], 4),
                numbers={
                    "angle_deg": round(cross.angle_deg, 1),
                    # `inf` is not JSON: two passes in DIFFERENT strokes have no
                    # along-path distance at all, and `null` says that, where a
                    # large number would invent one.
                    "arc_separation": (
                        None if not np.isfinite(cross.arc_separation) else round(cross.arc_separation, 4)
                    ),
                    "stroke_i": stroke_i,
                    "stroke_j": stroke_j,
                    "self_crossing": stroke_i == stroke_j,
                },
            )
        )

    per_class: dict[str, int] = {}
    for line, cls in classified_pass_points(strokes):
        index = per_class.get(cls, 0)
        per_class[cls] = index + 1
        mid = line[len(line) // 2]
        out.append(
            Landmark(
                kind=cls,
                index=index,
                x=round(float(mid[0]), 4),
                y=round(float(mid[1]), 4),
                numbers={"arc": round(polyline_length(line), 4), "samples": int(len(line))},
                points=tuple((round(float(x), 4), round(float(y), 4)) for x, y in line),
            )
        )

    for i, (lo, _hi) in enumerate(stroke_bounds(len(pts), stroke_starts)):
        if i == 0 or lo >= len(pts):
            continue  # the first pen-down is where the letter begins, not a lift
        head = all_strokes[i][0] if i < len(all_strokes) and len(all_strokes[i]) else pts[lo]
        out.append(
            Landmark(
                kind="lift",
                index=i - 1,
                x=round(float(head[0]), 4),
                y=round(float(head[1]), 4),
                numbers={"anchor": int(lo), "stroke": i},
            )
        )

    for i, anchor in enumerate(sorted({int(a) for a in (corner_anchors or []) if 0 <= int(a) < len(pts)})):
        out.append(
            Landmark(
                kind="corner",
                index=i,
                x=round(float(pts[anchor][0]), 4),
                y=round(float(pts[anchor][1]), 4),
                numbers={"anchor": anchor},
            )
        )

    ranges = loop_ranges(anchors, half_widths, stroke_starts, corner_anchors)
    rows = list((catalogue or {}).get(glyph_key, []))
    matched: set[int] = set()
    for i, loop in enumerate(loop_apertures([s.tolist() for s in strokes])):
        # Rank pairing is the catalogue's own identity rule („the caller's n-th
        # loop of a glyph is the catalogue's n-th entry"), and it holds only as
        # far as both sides see the same loops — which is exactly what the
        # unmatched rows below make visible instead of hiding.
        entry = rows[i] if i < len(rows) else None
        if entry is not None:
            matched.add(i)
        out.append(
            Landmark(
                kind="loop",
                index=i,
                x=round(loop.cx, 4),
                y=round(loop.cy, 4),
                numbers={
                    "d0": round(loop.d0, 4),
                    "area": round(loop.area, 5),
                    "size_class": entry["size_class"] if entry else size_class(loop.d0),
                    "state": entry["state"] if entry else UNKNOWN,
                    "d0_plate": entry.get("d0_plate") if entry else None,
                    "occurrences": entry.get("occurrences") if entry else None,
                    "with_counter": entry.get("with_counter") if entry else None,
                    "anchor_range": _fmt_range(_loop_range_for((loop.cx, loop.cy), pts, ranges)),
                },
            )
        )

    return RowLandmarks(
        variant=variant,
        strokes=len(strokes),
        n_anchors=len(pts),
        landmarks=tuple(out),
        loop_ranges=tuple((int(lo), int(hi)) for lo, hi in ranges),
        unmatched_catalogue=tuple(row for i, row in enumerate(rows) if i not in matched),
    )


def _fmt_range(span: list[int] | None) -> str | None:
    """`"12–19"` for a loop's anchor range — one flat field, or None where the
    ductus finder has no range for this loop at all (the `t`, the capitals)."""
    return None if span is None else f"{span[0]}–{span[1]}"


__all__ = [
    "CROSS_PARTNER_MIN_HITS",
    "CROSS_PARTNER_NEAR_UNITS",
    "KRINGEL_CATALOGUE_FILE",
    "LANDMARK_MERGE_RADIUS_UNITS",
    "LANDMARK_MIN_ANGLE_DEG",
    "LANDMARK_MIN_ARC_SEPARATION_UNITS",
    "LANDMARK_MIN_INDEX_GAP",
    "PASS_CLASSES",
    "PIERCE_MARGIN_UNITS",
    "PIERCE_WINDOW_UNITS",
    "PLATE_PEN_HALF_WIDTH_UNITS",
    "PLATE_PEN_WIDTH_UNITS",
    "RASTER_PX_PER_UNIT",
    "RESAMPLE_STEP_UNITS",
    "RETRACE_MAX_PARTNER_GAP_UNITS",
    "RETRACE_MIN_PAIRS",
    "RETRACE_MIN_PASS_ARC_UNITS",
    "RETRACE_PROX_UNITS",
    "SIZE_CLASSES",
    "SIZE_MEDIUM_MAX_UNITS",
    "SIZE_SMALL_MAX_UNITS",
    "SPLITTER_FLOOR_UNITS",
    "STATES",
    "STATE_MAJORITY",
    "UNATTESTED",
    "UNKNOWN",
    "Landmark",
    "LoopAperture",
    "RowLandmarks",
    "SelfIntersection",
    "StructureZones",
    "catalogue_source",
    "classified_pass_points",
    "crossing_landmarks",
    "crossing_points",
    "crossing_stroke_pair",
    "landmark_crossings",
    "load_catalogue",
    "loop_apertures",
    "loop_state",
    "merge_partner_passes",
    "polyline_self_intersections",
    "resampled_strokes",
    "retrace_segments",
    "row_landmarks",
    "size_class",
    "structure_zones",
]
