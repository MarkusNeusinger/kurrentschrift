"""The bench frame, and the stroke bookkeeping that has to happen inside it.

The load-bearing decision of `docs/proposals/tintenfolger.md` §2.1: stored
`(u, v)` trace coordinates are NOT canonical. `tx` comes out of the composer's
grid search (it moves when the composer moves), and the word editor folds its
`ty` into `baseline_row`. Comparing two traces in their own labels would report
registration bookkeeping as tracing error.

So the bench frame is the CROP PIXEL GRID re-expressed in x-heights, derived
only from the frozen fixture entry (`word.json`):

    xh           = baseline_y - midband_y
    baseline_row = baseline_y - rect[1]

and every path — reference AND candidate — travels through its OWN stored
registration back to crop pixels and from there into the bench frame. Two rows
whose registrations differ but describe the same pixels then land on the same
bench points, which is the property `tests/test_tracebench_frames.py` pins.

Above the frame sit the three pieces of stroke bookkeeping the metric cannot do
for itself: splitting marks (i-dot, umlaut, u-bow) off the body before the body
DTW, concatenating the body in writing order, and comparing pen lifts as
positions rather than as DTW cost.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from tools.laufform.harvest import DIACRITIC_MIN_Y
from tools.pairlab.landmarks import nearest_unique_point


# A stroke floating entirely above the midband is a diacritic — the rule of
# `tools.pairlab.chain._letter_cut_anchors`, imported here through
# `tools.laufform.harvest.DIACRITIC_MIN_Y` so the bench classifies exactly what
# the harvest classifies. Arc length caps it: a long stroke that happens to stay
# in the Oberlänge (a capital's ornament, an ascender loop) is body, not a mark.
MARK_MAX_ARC_UNITS = 0.8  # tintenfolger.md §2.3 ("Bogenlänge <= 0,8 xh")
# Mark matching, centroid to centroid, with the refusal semantics of
# `landmarks.nearest_unique_point`: nothing within the radius is a miss, a
# second candidate within the margin of the nearest is a refusal, never a guess.
MARK_MATCH_RADIUS_UNITS = 0.6  # tintenfolger.md §2.3
MARK_MATCH_MARGIN_UNITS = 0.25  # tintenfolger.md §2.3
# Pen lifts are compared as POSITIONS (they stay outside the DTW cost, §2.3), so
# a lift matches a lift only when they sit at the same place in the word.
LIFT_MATCH_RADIUS_UNITS = 0.6  # tintenfolger.md §2.3 ("0,6-xh-Deckel")


@dataclass(frozen=True)
class CountResult:
    """The §2.3 counter contract: detect on both sides, match with refusal.

    `matched + missing == ref` always; `ambiguous` is the subset of `missing`
    the matcher REFUSED to decide rather than failed to find. `pos_err_xh` is
    the median offset over the matched pairs, `None` when nothing matched.
    """

    ref: int
    cand: int
    matched: int
    missing: int
    spurious: int
    ambiguous: int
    pos_err_xh: float | None


# A mark match is that same contract — one name for one shape, so the mark gate
# and the crossing/retrace counters are read the same way.
MarkMatch = CountResult


@dataclass(frozen=True)
class BenchFrame:
    """The comparison frame of ONE fixture entry: crop pixels, measured in xh."""

    xh: float  # crop pixels per x-height (Grundlinie -> Mittellinie)
    baseline_row: float  # crop row of the Grundlinie (bench v = 0)
    entry_id: str | None = None

    @classmethod
    def from_entry(cls, entry: dict[str, Any]) -> BenchFrame:
        """Build the frame from a frozen `word.json` entry — and from nothing else.

        The whole point is that the frame does not depend on any stored trace: a
        re-tracing, a re-fit or a composer change cannot move it.
        """
        xh = float(entry["baseline_y"]) - float(entry["midband_y"])
        if not np.isfinite(xh) or xh <= 0.0:
            raise ValueError(f"entry {entry.get('id')!r} has a non-positive x-height ({xh})")
        return cls(xh=xh, baseline_row=float(entry["baseline_y"]) - float(entry["rect"][1]), entry_id=entry.get("id"))

    def crop_px_to_bench(self, points: np.ndarray) -> np.ndarray:
        """Crop pixels (y down) -> bench units (baseline 0, y up, 1 unit = xh)."""
        pts = np.asarray(points, dtype=float).reshape(-1, 2)
        return np.column_stack([pts[:, 0] / self.xh, (self.baseline_row - pts[:, 1]) / self.xh])

    def bench_to_crop_px(self, points: np.ndarray) -> np.ndarray:
        """Bench units -> crop pixels — the inverse, for the AIoU rasteriser."""
        pts = np.asarray(points, dtype=float).reshape(-1, 2)
        return np.column_stack([pts[:, 0] * self.xh, self.baseline_row - pts[:, 1] * self.xh])

    def trace_to_bench(
        self, strokes: list[Any], registration_px: dict[str, Any] | None, xh_px: float | None
    ) -> list[np.ndarray]:
        """A stored word trace in ITS registration -> this entry's bench frame.

        Trace units go back to crop pixels exactly as the app draws them
        (`app/src/sections/admin/belege/registration.ts::traceToCrop`):

            x = u * xh_px + tx
            y = (baseline_row + ty) - v * xh_px

        `ty` is folded into the baseline row per the stored convention (the word
        editor writes the row shift into `baseline_row` and leaves `ty` at 0 for
        an authored row; a harvested row carries both). Missing fields fall back
        the way the app falls back: no `xh_px` means the entry's own x-height, no
        registration means the entry's own baseline and a zero origin.
        """
        registration = registration_px or {}
        row_xh = float(xh_px) if xh_px else self.xh
        if not np.isfinite(row_xh) or row_xh <= 0.0:
            raise ValueError(f"trace on {self.entry_id!r} has a non-positive xh_px ({xh_px})")
        tx = float(registration.get("tx") or 0.0)
        baseline = float(registration["baseline_row"]) if "baseline_row" in registration else self.baseline_row
        baseline += float(registration.get("ty") or 0.0)
        out: list[np.ndarray] = []
        for stroke in strokes:
            uv = np.asarray(stroke, dtype=float).reshape(-1, 2)
            px = np.column_stack([uv[:, 0] * row_xh + tx, baseline - uv[:, 1] * row_xh])
            out.append(self.crop_px_to_bench(px))
        return out


def arc_length(points: np.ndarray) -> float:
    """Total chord length of a polyline (0 for fewer than two points)."""
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(pts) < 2:
        return 0.0
    return float(np.hypot(*np.diff(pts, axis=0).T).sum())


def classify_strokes(strokes_bench: list[np.ndarray]) -> tuple[list[np.ndarray], list[np.ndarray]]:
    """Split a trace into `(body, marks)` — the delayed strokes come out.

    A stroke is a MARK when all three hold: it is not the first stroke (a word
    does not open with its own diacritic), every one of its points sits above
    `DIACRITIC_MIN_Y`, and its arc is at most `MARK_MAX_ARC_UNITS`. Everything
    else is body — a t-crossbar dips through the midband, an ascender loop is
    too long, and both belong in the body DTW.

    Pulling the marks out before the body DTW is standard delayed-stroke
    practice, and it defuses the engine's own deferred-diacritic ordering: the
    body sequences then compare in writing order without an i-dot appended at
    the end of one side and in the middle of the other.
    """
    body: list[np.ndarray] = []
    marks: list[np.ndarray] = []
    for index, stroke in enumerate(strokes_bench):
        pts = np.asarray(stroke, dtype=float).reshape(-1, 2)
        floating = len(pts) > 0 and bool((pts[:, 1] > DIACRITIC_MIN_Y).all())
        is_mark = index > 0 and floating and arc_length(pts) <= MARK_MAX_ARC_UNITS
        (marks if is_mark else body).append(pts)
    return body, marks


def concat_strokes(strokes: list[np.ndarray]) -> tuple[np.ndarray, list[int]]:
    """`(points, stroke_starts)` of a stroke list — the pen-lift-aware packing.

    Every consumer that hands a whole trace to a detector needs exactly this
    pair, and needs it identical on both sides: the concatenated points plus the
    indices where a new pen stroke begins, so nothing downstream bridges a lift.
    """
    kept = [np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes]
    kept = [s for s in kept if len(s)]
    if not kept:
        return np.zeros((0, 2)), []
    starts: list[int] = []
    at = 0
    for s in kept:
        starts.append(at)
        at += len(s)
    return np.vstack(kept), starts


def concat_body(body: list[np.ndarray]) -> np.ndarray:
    """The body strokes as ONE point sequence in writing order.

    The order IS the truth (§2.3), so this concatenates rather than sorts, and
    the pen lifts between the strokes leave no trace in the sequence — they are
    reported separately by `lift_stats`.
    """
    return concat_strokes(body)[0]


def lift_positions(body: list[np.ndarray]) -> np.ndarray:
    """Where the pen left the paper: the last point of every body stroke but the last."""
    ends = [np.asarray(s, dtype=float).reshape(-1, 2)[-1] for s in body if len(s)]
    return np.asarray(ends[:-1], dtype=float).reshape(-1, 2)


def lift_stats(body_ref: list[np.ndarray], body_cand: list[np.ndarray]) -> dict[str, Any]:
    """Pen lifts compared as positions, never as DTW cost.

    `lift_delta` is signed, candidate minus reference: a fragmented candidate
    reports a positive delta, one that welds two strokes together a negative
    one. Lifts are matched greedily by nearest neighbour and REFUSED beyond
    `LIFT_MATCH_RADIUS_UNITS` — a lift half a word away is a different lift, and
    pairing it up would report a small position error for a large mistake.
    """
    ref = lift_positions(body_ref)
    cand = lift_positions(body_cand)
    errors: list[float] = []
    free = list(range(len(cand)))
    for i in range(len(ref)):
        if not free:
            break
        d = np.hypot(cand[free, 0] - ref[i, 0], cand[free, 1] - ref[i, 1])
        best = int(np.argmin(d))
        if float(d[best]) > LIFT_MATCH_RADIUS_UNITS:
            continue
        errors.append(float(d[best]))
        free.pop(best)
    return {
        "lift_ref": len(ref),
        "lift_cand": len(cand),
        "lift_delta": len(cand) - len(ref),
        "lift_matched": len(errors),
        "lift_unmatched_ref": len(ref) - len(errors),
        "lift_unmatched_cand": len(cand) - len(errors),
        "lift_pos_err_xh": float(np.median(errors)) if errors else None,
    }


def match_points(ref: np.ndarray, cand: np.ndarray, *, radius: float, margin: float) -> CountResult:
    """Match two point sets with refusal — the shared body of every §2.3 counter.

    Reference points are walked in writing order; each takes the one candidate
    `landmarks.nearest_unique_point` is willing to name, and a claimed candidate
    leaves the pool (so two reference marks cannot both land on one blot). A
    refusal is counted as `ambiguous` AND as `missing`: the structure was not
    found, and saying WHY is what separates "the candidate lost the crossing"
    from "there are two crossings here and proximity cannot tell them apart".
    """
    ref_pts = np.asarray(ref, dtype=float).reshape(-1, 2)
    cand_pts = np.asarray(cand, dtype=float).reshape(-1, 2)
    free = list(range(len(cand_pts)))
    errors: list[float] = []
    ambiguous = 0
    for i in range(len(ref_pts)):
        pool = cand_pts[free] if free else np.zeros((0, 2))
        _, reason, distance = nearest_unique_point(pool, ref_pts[i], radius=radius, margin=margin)
        if reason == "ambiguous":
            ambiguous += 1
            continue
        if reason != "ok":
            continue
        errors.append(distance)
        free.pop(int(np.argmin(np.hypot(pool[:, 0] - ref_pts[i, 0], pool[:, 1] - ref_pts[i, 1]))))
    matched = len(errors)
    return CountResult(
        ref=len(ref_pts),
        cand=len(cand_pts),
        matched=matched,
        missing=len(ref_pts) - matched,
        spurious=len(cand_pts) - matched,
        ambiguous=ambiguous,
        pos_err_xh=float(np.median(errors)) if errors else None,
    )


def mark_centroids(marks: list[np.ndarray]) -> np.ndarray:
    """One point per mark — its centroid, which is what a dot HAS instead of a shape."""
    centres = [np.asarray(m, dtype=float).reshape(-1, 2).mean(axis=0) for m in marks if len(m)]
    return np.asarray(centres, dtype=float).reshape(-1, 2)


def match_marks(marks_ref: list[np.ndarray], marks_cand: list[np.ndarray]) -> MarkMatch:
    """The mark gate: which diacritics of the reference the candidate wrote.

    `missing` is a CO-PRIMARY gate of the bench (§2.4) — a lost i-dot is not
    buyable back with a better body distance, which is why it is counted here
    and never folded into a weighted loss.
    """
    return match_points(
        mark_centroids(marks_ref),
        mark_centroids(marks_cand),
        radius=MARK_MATCH_RADIUS_UNITS,
        margin=MARK_MATCH_MARGIN_UNITS,
    )


__all__ = [
    "LIFT_MATCH_RADIUS_UNITS",
    "MARK_MATCH_MARGIN_UNITS",
    "MARK_MATCH_RADIUS_UNITS",
    "MARK_MAX_ARC_UNITS",
    "BenchFrame",
    "CountResult",
    "MarkMatch",
    "arc_length",
    "classify_strokes",
    "concat_body",
    "concat_strokes",
    "lift_positions",
    "lift_stats",
    "mark_centroids",
    "match_marks",
    "match_points",
]
