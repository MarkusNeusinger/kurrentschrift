"""The structure counters: crossings and retraces, detected on BOTH sides.

`docs/proposals/tintenfolger.md` §2.3 asks the hard places for a number of their
own, because a distance cannot say them: a lost loop crossing and a retrace
collapsed onto one pass are STRUCTURE defects, and a structure defect vetoes any
distance gain (§2.4). So each counter follows the same contract as the mark
gate — detect on both sides with the SAME detector, match with refusal, report
`ref/cand/matched/missing/spurious/ambiguous/pos_err_xh`.

Since the v2 re-baseline (`qualitaetsmetrik.md` §14, `aug16` — the owner's
manual audit of the dev words) the counters carry the DUCTUS semantics rather
than raw geometry thresholds:

* a **crossing** exists only where one line PIERCES the other — clearly in on
  one side and out on the other, both ways (`_pierces`); a retrace that touches
  and releases on the same side is not a crossing however sharp its angle, and
  a shallow branch-off that does pierce is one however small its angle (the v1
  15-degree threshold cut through identical branch geometry at the linken k);
* a **retrace** is one stroke writing the same ink twice, so its two passes are
  arc-ADJACENT; anti-parallel proximity with a long way in between is a
  **touch** (writing past each other), a pass in another pen stroke an
  **overlap** (a mark riding the body), and a diverging cusp too short to be a
  zone is a graze. Touch and overlap are counted and reported, never part of a
  loss.

Raw self-intersections still come from the frozen
`tools.pairlab.landmarks.polyline_self_intersections`, retrace samples from the
frozen `core.geometry.detect_retrace_pairs`; only the CLASSIFICATION above them
is this module's. Both sides are resampled to one common step first: without
that, "at least three flagged samples" would mean 0.06 xh of ink on a resampled
fit and half a millimetre of pen travel on a hand trace, and the two counts
would not be comparable at all.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

import numpy as np

from core.geometry import detect_retrace_pairs, stroke_bounds
from core.quality_suetterlin import MIN_RETRACE_PAIRS
from tools.pairlab.landmarks import (
    LANDMARK_MERGE_RADIUS_UNITS,
    LANDMARK_MIN_ARC_SEPARATION_UNITS,
    polyline_self_intersections,
)
from tools.tracebench.frames import CountResult, arc_length, concat_strokes, match_points_one_to_one
from tools.tracebench.metric import resample_by_step


# Common discretisation for both detectors — the same 0.02 xh the headline DTW
# resamples to (tintenfolger.md §2.3), so a counter never reads a finer or
# coarser path than the distance does.
RESAMPLE_STEP_UNITS = 0.02
# Crossing matching, ref against cand (tintenfolger.md §2.3: "Match 0,55 xh").
# No refusal margin here: structure populations are matched one-to-one
# (`frames.match_points_one_to_one`) — the margin belongs to the single-query
# frame of the marks, and refused a trace against itself on the first
# identity run (§14).
CROSSING_MATCH_RADIUS_UNITS = 0.55
# Proximity below which two passes count as the same ink for a retrace. In bench
# units, so it is a share of the x-height rather than of a scan resolution;
# `detect_retrace_pairs` derives its along-path separation from it (3x).
RETRACE_PROX_UNITS = 0.15  # tintenfolger.md §2.3
# Fewer flagged samples than this is a coincidental touch, not a retrace —
# mirrored from `core.quality_suetterlin.MIN_RETRACE_PAIRS` so the bench and the
# Sütterlin naturalness metric call the same thing a retrace.
RETRACE_MIN_PAIRS = MIN_RETRACE_PAIRS
# Retrace segments are matched at the crossing radius: both are "one place
# in the word", and giving them separate radii would be two invented numbers.
RETRACE_MATCH_RADIUS_UNITS = CROSSING_MATCH_RADIUS_UNITS

# ---- the v2 constants (qualitaetsmetrik.md §14 `aug16`, all MEASURED on the
# ---- owner's named dev-word examples, never chosen by analogy)
#
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


@dataclass(frozen=True)
class RetraceCount(CountResult):
    """The counter contract plus the arc both sides spent retracing.

    `arc_ref` / `arc_cand` are the robust half of the retrace measurement: how
    MUCH ink was written twice survives a segmentation that splits or merges a
    zone, where the segment count does not. Callers form the ratio (§2.3's
    `retrace_arc_ratio`) rather than getting a divide-by-zero baked in here.
    """

    arc_ref: float
    arc_cand: float


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


def crossing_points(strokes_bench: list[np.ndarray], *, resample_step: float = RESAMPLE_STEP_UNITS) -> np.ndarray:
    """The PIERCING self-crossings of one trace, as `(n, 2)` bench points.

    The whole trace becomes ONE point array plus its stroke starts, so a t-bar
    crossing its own stem is found while the line between two pen strokes — never
    written — cannot fabricate one. v2 (§14 `aug16`): a raw intersection counts
    when its two passes are at least the frozen arc separation apart AND pierce
    each other (`_pierces`); co-located survivors merge to the best-conditioned
    member, exactly the frozen detector's own merge rule.
    """
    pts, starts = concat_strokes(resampled_strokes(strokes_bench, resample_step))
    if len(pts) < 2:
        return np.zeros((0, 2))
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

    def _retrace_internal(x) -> bool:
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
    kept: list = []
    for x in sorted(found, key=lambda c: (-c.angle_deg, c.seg_i, c.seg_j)):
        if any(np.hypot(x.point[0] - y.point[0], x.point[1] - y.point[1]) <= LANDMARK_MERGE_RADIUS_UNITS for y in kept):
            continue
        kept.append(x)
    kept.sort(key=lambda c: (c.seg_i, c.seg_j))
    return np.asarray([x.point for x in kept], dtype=float).reshape(-1, 2)


def count_crossings(
    ref_strokes: list[np.ndarray], cand_strokes: list[np.ndarray], *, resample_step: float = RESAMPLE_STEP_UNITS
) -> CountResult:
    """Loop crossings of the reference against those of the candidate."""
    # One-to-one assignment, no refusal margin: both sides carry the SAME
    # detector's population, and two true crossings a stroke width apart are
    # two crossings — the margin refused a trace against ITSELF on the first
    # identity run (unter/mit/linken, §14). Marks keep the refusal semantics:
    # theirs is the single-query frame the margin was built for.
    return match_points_one_to_one(
        crossing_points(ref_strokes, resample_step=resample_step),
        crossing_points(cand_strokes, resample_step=resample_step),
        radius=CROSSING_MATCH_RADIUS_UNITS,
    )


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
        if arc_length(pts[p_lo : p_hi + 1]) < RETRACE_MIN_PASS_ARC_UNITS:
            return None  # a diverging cusp's graze
        return "retrace"

    return passes, [classify(p) for p in passes], partner_of


def classified_pass_points(
    strokes_bench: list[np.ndarray], *, xh_px_equivalent: float = 1.0, resample_step: float = RESAMPLE_STEP_UNITS
) -> list[tuple[np.ndarray, str]]:
    """`(pass polyline, class)` per kept pass — display-grade access to the rule.

    The duel viewer draws exactly these, so what the page shows and what the
    counters count can never drift apart; grazes are dropped here as there.
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
    for cls in ("retrace", "touch", "overlap"):
        members_idx = [n for n, c in enumerate(cls_of) if c == cls]
        class_passes = [passes[n] for n in members_idx]
        zones = _merge_partner_passes(class_passes, partner_of)
        mids = [
            np.mean([pts[class_passes[p][len(class_passes[p]) // 2]] for p in members], axis=0)
            for members in zones
            if members
        ]
        out[cls] = np.asarray(mids, dtype=float).reshape(-1, 2)
        if cls == "retrace":
            retrace_arc = sum(arc_length(pts[p[0] : p[-1] + 1]) for p in class_passes)
    return StructureZones(
        retrace_mids=out["retrace"], retrace_arc=retrace_arc, touch_mids=out["touch"], overlap_mids=out["overlap"]
    )


def retrace_segments(
    strokes_bench: list[np.ndarray], *, xh_px_equivalent: float = 1.0, resample_step: float = RESAMPLE_STEP_UNITS
) -> tuple[np.ndarray, float]:
    """`(retrace zone midpoints, retraced arc)` — the retrace class of `structure_zones`."""
    zones = structure_zones(strokes_bench, xh_px_equivalent=xh_px_equivalent, resample_step=resample_step)
    return zones.retrace_mids, zones.retrace_arc


def _merge_partner_passes(passes: list[list[int]], partner_of: dict[int, int]) -> list[list[int]]:
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


def count_retraces(
    ref_strokes: list[np.ndarray],
    cand_strokes: list[np.ndarray],
    *,
    xh_px_equivalent: float = 1.0,
    resample_step: float = RESAMPLE_STEP_UNITS,
) -> RetraceCount:
    """Retrace zones of the reference against those of the candidate."""
    ref_mid, ref_arc = retrace_segments(ref_strokes, xh_px_equivalent=xh_px_equivalent, resample_step=resample_step)
    cand_mid, cand_arc = retrace_segments(cand_strokes, xh_px_equivalent=xh_px_equivalent, resample_step=resample_step)
    counts = match_points_one_to_one(ref_mid, cand_mid, radius=RETRACE_MATCH_RADIUS_UNITS)
    return RetraceCount(**asdict(counts), arc_ref=ref_arc, arc_cand=cand_arc)


__all__ = [
    "CROSSING_MATCH_RADIUS_UNITS",
    "PIERCE_MARGIN_UNITS",
    "PIERCE_WINDOW_UNITS",
    "RESAMPLE_STEP_UNITS",
    "RETRACE_MATCH_RADIUS_UNITS",
    "RETRACE_MAX_PARTNER_GAP_UNITS",
    "RETRACE_MIN_PAIRS",
    "RETRACE_MIN_PASS_ARC_UNITS",
    "RETRACE_PROX_UNITS",
    "RetraceCount",
    "StructureZones",
    "classified_pass_points",
    "count_crossings",
    "count_retraces",
    "crossing_points",
    "resampled_strokes",
    "retrace_segments",
    "structure_zones",
]
