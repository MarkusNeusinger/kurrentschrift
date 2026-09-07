"""The structure counters: crossings and retraces, MATCHED between two traces.

`docs/proposals/tintenfolger.md` §2.3 asks the hard places for a number of their
own, because a distance cannot say them: a lost loop crossing and a retrace
collapsed onto one pass are STRUCTURE defects, and a structure defect vetoes any
distance gain (§2.4). So each counter follows the same contract as the mark
gate — detect on both sides with the SAME detector, match with refusal, report
`ref/cand/matched/missing/spurious/ambiguous/pos_err_xh`.

Since the v2 re-baseline (`messjournal.md` §14, `aug16` — the owner's
manual audit of the dev words) the counters carry the DUCTUS semantics rather
than raw geometry thresholds:

* a **crossing** exists only where one line PIERCES the other — clearly in on
  one side and out on the other, both ways; a retrace that touches and releases
  on the same side is not a crossing however sharp its angle, and a shallow
  branch-off that does pierce is one however small its angle (the v1
  15-degree threshold cut through identical branch geometry at the linken k);
* a **retrace** is one stroke writing the same ink twice, so its two passes are
  arc-ADJACENT; anti-parallel proximity with a long way in between is a
  **touch** (writing past each other), a pass in another pen stroke an
  **overlap** (a mark riding the body), and a diverging cusp too short to be a
  zone is a graze. Touch and overlap are counted and reported, never part of a
  loss.

**The DETECTION half of all that now lives in `core.landmarks`** and is
re-exported here under its old names, so every consumer (`soll.py`,
`summary.py`, `k0eval.py`, `excursions.py`, `tools.wordbench.continuity`) reads
exactly what it always read. It moved for one reason: the admin's
Landmarken-Linse serves the same detectors over HTTP, and `api/` may not import
`tools/` because the API image does not ship it (`tests/test_imports.py`). Every
threshold and its measured provenance travelled with the code, unchanged.

What stays HERE is what only a duel needs: the two match radii and the
one-to-one assignment of a reference population against a candidate one.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from core.landmarks import (
    CROSS_PARTNER_MIN_HITS,
    CROSS_PARTNER_NEAR_UNITS,
    PIERCE_MARGIN_UNITS,
    PIERCE_WINDOW_UNITS,
    RESAMPLE_STEP_UNITS,
    RETRACE_MAX_PARTNER_GAP_UNITS,
    RETRACE_MIN_PAIRS,
    RETRACE_MIN_PASS_ARC_UNITS,
    RETRACE_PROX_UNITS,
    StructureZones,
    classified_pass_points,
    crossing_points,
    resampled_strokes,
    retrace_segments,
    structure_zones,
)
from tools.tracebench.frames import CountResult, match_points_one_to_one


# Crossing matching, ref against cand (tintenfolger.md §2.3: "Match 0,55 xh").
# No refusal margin here: structure populations are matched one-to-one
# (`frames.match_points_one_to_one`) — the margin belongs to the single-query
# frame of the marks, and refused a trace against itself on the first
# identity run (§14).
CROSSING_MATCH_RADIUS_UNITS = 0.55
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
    "CROSS_PARTNER_MIN_HITS",
    "CROSS_PARTNER_NEAR_UNITS",
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
