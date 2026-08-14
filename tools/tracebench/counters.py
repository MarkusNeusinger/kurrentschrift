"""The structure counters: crossings and retraces, detected on BOTH sides.

`docs/proposals/tintenfolger.md` §2.3 asks the hard places for a number of their
own, because a distance cannot say them: a lost loop crossing and a retrace
collapsed onto one pass are STRUCTURE defects, and a structure defect vetoes any
distance gain (§2.4). So each counter follows the same contract as the mark
gate — detect on both sides with the SAME detector, match with refusal, report
`ref/cand/matched/missing/spurious/ambiguous/pos_err_xh`.

Neither detector is re-tuned here. Crossings come from
`tools.pairlab.landmarks.landmark_crossings` at its own thresholds (the census
of `qualitaetsmetrik.md` §13a was taken at them), retraces from
`core.geometry.detect_retrace_pairs`. Both read a SAMPLE sequence, so both sides
are resampled to one common step first: without that, "at least three flagged
samples" would mean 0.06 xh of ink on a resampled fit and half a millimetre of
pen travel on a hand trace, and the two counts would not be comparable at all.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from core.geometry import detect_retrace_pairs, stroke_bounds
from core.quality_suetterlin import MIN_RETRACE_PAIRS
from tools.pairlab.landmarks import landmark_crossings
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


def crossing_points(strokes_bench: list[np.ndarray], *, resample_step: float = RESAMPLE_STEP_UNITS) -> np.ndarray:
    """The well-conditioned self-crossings of one trace, as `(n, 2)` bench points.

    The whole trace becomes ONE point array plus its stroke starts, so a t-bar
    crossing its own stem is found while the line between two pen strokes — never
    written — cannot fabricate one.
    """
    pts, starts = concat_strokes(resampled_strokes(strokes_bench, resample_step))
    if len(pts) < 2:
        return np.zeros((0, 2))
    found = landmark_crossings(pts, starts)
    return np.asarray([x.point for x in found], dtype=float).reshape(-1, 2)


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


def retrace_segments(
    strokes_bench: list[np.ndarray], *, xh_px_equivalent: float = 1.0, resample_step: float = RESAMPLE_STEP_UNITS
) -> tuple[np.ndarray, float]:
    """`(retrace zone midpoints, total retraced arc)` of one trace.

    `detect_retrace_pairs` flags the SAMPLES whose near-anti-parallel partner
    lies within `RETRACE_PROX_UNITS * xh_px_equivalent` — the scale factor exists
    so a caller working in crop pixels can reuse the same rule. Contiguous
    flagged samples of one pen stroke form a PASS; a pass thinner than
    `RETRACE_MIN_PAIRS` samples is dropped as a graze.

    The two passes of one out-and-back are then MERGED into one zone, using the
    partner indices the detector already returns (a pass whose partners lie in
    another pass is the other limb of the same retrace, not a second retrace).
    Without the merge one `t` stem would report two structures whose midpoints
    sit a stroke width apart, and the refusal margin of `match_points` would
    then refuse to match a trace against ITSELF — which is exactly the identity
    gate the bench runs to prove the ruler is intact. The zone's position is the
    mean of its passes' middle samples; the arc stays the sum over the passes,
    because how much ink was written twice is a property of the pen travel, not
    of how the zones were cut.
    """
    pts, starts = concat_strokes(resampled_strokes(strokes_bench, resample_step))
    if len(pts) < 2:
        return np.zeros((0, 2)), 0.0
    idx, partner = detect_retrace_pairs(
        pts[:, 0], pts[:, 1], starts, prox_px=RETRACE_PROX_UNITS * float(xh_px_equivalent)
    )
    if not len(idx):
        return np.zeros((0, 2)), 0.0
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

    total = sum(arc_length(pts[p[0] : p[-1] + 1]) for p in passes)
    zone_of = _merge_partner_passes(passes, partner_of)
    midpoints = [
        np.mean([pts[passes[p][len(passes[p]) // 2]] for p in members], axis=0) for members in zone_of if members
    ]
    return np.asarray(midpoints, dtype=float).reshape(-1, 2), total


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
    "RESAMPLE_STEP_UNITS",
    "RETRACE_MATCH_RADIUS_UNITS",
    "RETRACE_MIN_PAIRS",
    "RETRACE_PROX_UNITS",
    "RetraceCount",
    "count_crossings",
    "count_retraces",
    "crossing_points",
    "resampled_strokes",
    "retrace_segments",
]
