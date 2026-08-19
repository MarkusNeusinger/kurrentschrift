"""The distance measures of the trace bench — pure geometry, nothing else.

`docs/proposals/tintenfolger.md` §2.3 defines them; this module implements them
and NOTHING above them: no fixtures, no candidate providers, no units. Every
function works in the caller's coordinates (the bench feeds xh units, the
rasteriser crop pixels), so a unit mistake cannot hide in here.

Deliberately ZERO project imports — numpy and scipy only. The ruler must be
readable and testable without the engine it grades, and a `core` import would
tie a measurement to the thing being measured (`tests/test_tracebench_metric.py`
pins that property by parsing this file's imports).

The three measures and why each exists:

* `dtw` — the headline `dtw_xh`. Unconstrained DTW with the Euclidean local
  distance, normalised by the length of the OPTIMAL warping path (PEN-Net's
  LDTW normalisation, ACCV 2022). Forward only: writing DIRECTION is ductus
  truth, so a candidate that runs a stroke backwards must be punished, not
  silently re-aligned. Because both sides are arc-length resampled first and
  the unit is x-heights, the number is NOT comparable with published LDTW
  values — hence the project's own name for it.
* `aiou` — the paper-faithful Adaptive IoU: the candidate rasterised 1 px wide
  and dilated with a 3x3 element until the IoU against the INK MASK peaks. It
  grades against the image, never against a reference trace, which is what lets
  the column cover specimens nobody has traced by hand.
* `chamfer` — both directions, kept apart. A missing i-dot inflates exactly one
  of the two halves; a symmetric mean would hide precisely that.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import binary_dilation
from scipy.spatial import cKDTree


# Rasterisation step for `rasterise_strokes`: dense parameter sampling at half a
# pixel, then rounding to the grid. Chosen over a Bresenham line walk because it
# is four lines of numpy and provably gap-free (consecutive samples are at most
# 0.5 px apart, so their rounded pixels are equal or 4-neighbours), and because
# "sample, round, deduplicate" is exactly reproducible across platforms.
RASTER_STEP_PX = 0.5
# Hard stop for the AIoU dilation sweep. The IoU is unimodal in the dilation
# count in practice (the candidate first fills the stroke, then floods past it),
# and the loop already stops at the first decrease — this cap is only there so a
# pathological input cannot turn a measurement into an infinite loop.
AIOU_MAX_DILATIONS = 64

# Backtracking markers of the DTW step matrix.
_STEP_START = np.int8(0)
_STEP_DIAG = np.int8(1)  # (i-1, j-1)
_STEP_UP = np.int8(2)  # (i-1, j)
_STEP_LEFT = np.int8(3)  # (i, j-1)


@dataclass(frozen=True)
class DtwResult:
    """`mean_xh` is the headline: accumulated cost / warping path length."""

    mean_xh: float
    path_len: int  # T — the number of matched pairs on the optimal path
    max_absorption: int  # most points of one side absorbed by ONE point of the other
    # The optimal warping path itself, `(path_len, 2)` int32 `(i, j)` pairs in
    # forward order — display-grade access to the alignment the numbers above
    # summarise (the `counters.classified_pass_points` pattern: a viewer that
    # re-derived the alignment could drift from the ruler). Excluded from
    # equality/repr; it changes NO measured value.
    pairs: np.ndarray = field(compare=False, repr=False, default_factory=lambda: np.zeros((0, 2), dtype=np.int32))


@dataclass(frozen=True)
class AiouResult:
    """`value` is the maximum IoU over the dilation sweep, reached at `k`."""

    value: float
    k: int
    iou_k0: float  # the undilated IoU — how much the bare 1-px line already hits


def resample_by_step(points: np.ndarray, step: float) -> np.ndarray:
    """Arc-length-uniform resampling of a polyline, endpoints exact.

    `n = max(2, round(total_arc / step) + 1)` samples, evenly spaced along the
    path. The endpoints are reproduced exactly (they are the first and last
    interpolation node), so resampling never shortens a stroke.

    A degenerate polyline — one point, or several coincident ones — has no arc
    to walk along and returns its two endpoints, which for a single point are
    that point twice. Callers get a well-formed 2-point array instead of an
    exception, because a stray zero-length stroke is a data property, not a
    programming error.
    """
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(pts) == 0:
        raise ValueError("resample_by_step needs at least one point")
    if len(pts) == 1:
        return np.repeat(pts, 2, axis=0)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    arc = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(arc[-1])
    if total <= 0.0 or step <= 0.0:
        return np.vstack([pts[0], pts[-1]])
    n = max(2, int(round(total / float(step))) + 1)
    t = np.linspace(0.0, total, n)
    return np.column_stack([np.interp(t, arc, pts[:, 0]), np.interp(t, arc, pts[:, 1])])


def dtw(a: np.ndarray, b: np.ndarray) -> DtwResult:
    """Unconstrained DTW between two point sequences, normalised by path length.

    Euclidean local distance (NOT squared — the headline must stay in the input's
    own unit), symmetric-1 steps {(i-1,j), (i,j-1), (i-1,j-1)}, both endpoints
    anchored, no band and no direction handling: `dtw(a, b)` compares `a` and `b`
    as WRITTEN, and a caller who wants to know whether the reverse reads better
    calls it again with a reversed argument.

    The row recurrence `D[i,j] = d[i,j] + min(D[i-1,j], D[i-1,j-1], D[i,j-1])`
    carries a sequential dependency in `j` through its own row. It is unrolled
    into a running minimum: with `S = cumsum(d[i])` and `p[j] = min(D[i-1,j],
    D[i-1,j-1])`,

        D[i,j] = S[j] + min_{k <= j} (p[k] - S[k-1])

    which `np.minimum.accumulate` evaluates in one pass, so only the row loop
    stays in Python. The prefix sums cost ~1e-14 of absolute accuracy against the
    textbook nested loop (pinned by a test against a naive reference), five
    orders of magnitude below anything the bench reports.

    Only the `int8` step matrix is kept (n*m bytes), never the full cost matrix.
    """
    pa = np.asarray(a, dtype=float).reshape(-1, 2)
    pb = np.asarray(b, dtype=float).reshape(-1, 2)
    n, m = len(pa), len(pb)
    if n == 0 or m == 0:
        raise ValueError("dtw needs two non-empty sequences")

    back = np.empty((n, m), dtype=np.int8)
    cur = np.cumsum(np.hypot(pb[:, 0] - pa[0, 0], pb[:, 1] - pa[0, 1]))
    back[0, :] = _STEP_LEFT
    back[0, 0] = _STEP_START

    for i in range(1, n):
        prev = cur
        d = np.hypot(pb[:, 0] - pa[i, 0], pb[:, 1] - pa[i, 1])
        best_prev = np.empty(m)
        best_prev[0] = prev[0]
        if m > 1:
            best_prev[1:] = np.minimum(prev[1:], prev[:-1])
        s = np.cumsum(d)
        cur = s + np.minimum.accumulate(best_prev - (s - d))
        # Which predecessor the value came from. Ties prefer the previous row
        # over a sideways step, and the diagonal over the vertical, so the path
        # is reproducible rather than merely optimal.
        left = np.empty(m)
        left[0] = np.inf
        left[1:] = cur[:-1]
        diag = np.empty(m)
        diag[0] = np.inf
        diag[1:] = prev[:-1]
        back[i] = np.where(left < best_prev, _STEP_LEFT, np.where(diag <= prev, _STEP_DIAG, _STEP_UP))

    i, j = n - 1, m - 1
    rows, cols = [i], [j]
    while True:
        step = back[i, j]
        if step == _STEP_START:
            break
        if step == _STEP_DIAG:
            i, j = i - 1, j - 1
        elif step == _STEP_UP:
            i -= 1
        else:
            j -= 1
        rows.append(i)
        cols.append(j)

    path_len = len(rows)
    absorption = max(int(np.bincount(rows).max()), int(np.bincount(cols).max()))
    pairs = np.column_stack([rows[::-1], cols[::-1]]).astype(np.int32)
    return DtwResult(mean_xh=float(cur[m - 1]) / path_len, path_len=path_len, max_absorption=absorption, pairs=pairs)


def rasterise_strokes(strokes: list[np.ndarray], shape: tuple[int, int]) -> np.ndarray:
    """Draw pen strokes as 1-px-wide polylines on an `(H, W)` boolean grid.

    Line segments are drawn only BETWEEN consecutive points of one stroke — a
    pen lift is never bridged, so a candidate is not credited with ink along a
    line the hand did not write. Each segment is sampled every `RASTER_STEP_PX`
    and the samples are rounded to the grid (deterministic, gap-free); points
    outside the grid are dropped rather than clamped, because clamping would
    smear an out-of-crop excursion along the border as if it were ink.
    """
    height, width = int(shape[0]), int(shape[1])
    out = np.zeros((height, width), dtype=bool)
    for stroke in strokes:
        pts = np.asarray(stroke, dtype=float).reshape(-1, 2)
        if len(pts) == 0:
            continue
        if len(pts) == 1:
            samples = pts
        else:
            chunks = []
            for k in range(len(pts) - 1):
                p0, p1 = pts[k], pts[k + 1]
                steps = max(1, int(np.ceil(float(np.hypot(*(p1 - p0))) / RASTER_STEP_PX)))
                t = np.linspace(0.0, 1.0, steps + 1)[:, None]
                chunks.append(p0[None, :] * (1.0 - t) + p1[None, :] * t)
            samples = np.vstack(chunks)
        ix = np.rint(samples[:, 0]).astype(int)
        iy = np.rint(samples[:, 1]).astype(int)
        keep = (ix >= 0) & (ix < width) & (iy >= 0) & (iy < height)
        out[iy[keep], ix[keep]] = True
    return out


def aiou(cand_strokes_px: list[np.ndarray], ink_mask: np.ndarray) -> AiouResult:
    """Adaptive IoU of a candidate trace against an ink mask (PEN-Net §3.1).

    The candidate is rasterised 1 px wide on the mask's own grid and then dilated
    with a 3x3 structuring element step by step; the reported value is the
    maximum IoU over that sweep. This is the paper's construction and it grades
    against the IMAGE: no reference trace is needed, and no measured half-width
    field enters — the width channel stays out of the geometry number by design
    (`docs/proposals/tintenfolger.md` §5).

    The sweep stops at the first decrease (the IoU is unimodal in practice: the
    dilation first fills the stroke, then floods past it) and is capped at
    `AIOU_MAX_DILATIONS` regardless.
    """
    ink = np.asarray(ink_mask, dtype=bool)
    if ink.ndim != 2:
        raise ValueError("ink_mask must be a 2-D boolean image")
    cand = rasterise_strokes(cand_strokes_px, ink.shape)
    if not cand.any():
        return AiouResult(value=0.0, k=0, iou_k0=0.0)

    element = np.ones((3, 3), dtype=bool)
    best, best_k, iou_k0 = -1.0, 0, 0.0
    current = cand
    for k in range(AIOU_MAX_DILATIONS + 1):
        union = int(np.count_nonzero(ink | current))
        iou = float(np.count_nonzero(ink & current)) / union if union else 0.0
        if k == 0:
            iou_k0 = iou
        if iou > best:
            best, best_k = iou, k
        elif iou < best:
            break
        if k < AIOU_MAX_DILATIONS:
            current = binary_dilation(current, structure=element)
    return AiouResult(value=best, k=best_k, iou_k0=iou_k0)


def chamfer(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """`(mean nearest distance from a to b, mean nearest distance from b to a)`.

    Deliberately asymmetric and deliberately unaveraged: the caller decides which
    side is candidate (precision) and which is reference (recall), and a missing
    stroke shows up in exactly one of the two halves.
    """
    pa = np.asarray(a, dtype=float).reshape(-1, 2)
    pb = np.asarray(b, dtype=float).reshape(-1, 2)
    if not len(pa) or not len(pb):
        raise ValueError("chamfer needs two non-empty point sets")
    d_ab, _ = cKDTree(pb).query(pa)
    d_ba, _ = cKDTree(pa).query(pb)
    return float(np.mean(d_ab)), float(np.mean(d_ba))


__all__ = [
    "AIOU_MAX_DILATIONS",
    "RASTER_STEP_PX",
    "AiouResult",
    "DtwResult",
    "aiou",
    "chamfer",
    "dtw",
    "rasterise_strokes",
    "resample_by_step",
]
