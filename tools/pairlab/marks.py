"""The mark refit: the i-dot and the u-bow put back on their own ink.

Measure A1 of `docs/proposals/tintenfolger.md` §7.3, and nothing else. The
measured defect (`qualitaetsmetrik.md` §14, the duel campaign): the chain fit
leaves a word's MARKS — the delayed strokes, i-dot / umlaut / u-bow — a median
0.129 xh beside the hand's own, and on `muß`/`und`/`unter`/`zwei` no mark of the
reference matches at all, while the prior-free control (`tools/routeg`, which
reads the marks straight out of the ink) reaches 0.046. The ink therefore
CARRIES the answer; the chain simply never asks for it. Its objective sees a
mark as a two-anchor segment with a handful of samples, so a body letter's data
term outvotes it, and a mark that started at its composed position tends to stay
there.

**What this module does.** After the body solve, every mark stroke is offered
the ink the body did not claim, and moved onto it by a pure TRANSLATION when
exactly one target is nameable. Not a solver term, not a re-solve, not a
re-linearisation: the mark is already its own pen-down polyline (the assembler
gives every diacritic its own stroke, `tools.pairlab.trace._is_diacritic`), so
displacing it can be done — and audited — on its own.

**Rigid, and deliberately only rigid.** Translation only: no scale, no rotation.
A mark is 3–8 skeleton pixels; there is no shape evidence in it that would
support a second parameter, and a fitted scale would be reading noise. The
composed mark's SHAPE stays the ductus prior's statement, its POSITION becomes
the ink's — which is exactly the split the project draws everywhere else.

**Refusal, never a guess** (the `tools.pairlab.anchors` doctrine, and the
`landmarks.nearest_unique_point` contract this reuses literally): a mark whose
target is not unique stays where the composition put it and says why. Three
refusals exist and each names a different situation — nothing within the search
radius (`no_candidate`), a second ink cluster within the margin of the nearest
(`ambiguous`), and two marks naming the SAME cluster (`contested`, both stay
put). A mark placed by a coin flip would be worse than a mark left alone,
because the bench would then read a small position error where the truth is that
the assignment is undecidable.

**Two things it can never do**, both structural rather than checked:

* it never moves a body anchor — only entries `_is_diacritic` accepts are
  touched, and those are exactly the ones the assembler emits as their own
  stroke; every other entry comes back as the identical object;
* it never pulls a mark into another stroke's ink — the candidate ink is the
  UNCLAIMED skeleton (everything within `body_claim_units` of the fitted body
  path is removed first), clusters above `max_ink_arc_units` are dropped as body
  the fit missed rather than a mark, and a cluster two marks both want is given
  to neither.

**Guard rails**: strictly additive and OPT-IN. Nothing here runs unless a caller
passes the flag (`tools.laufform.harvest.HarvestOptions.mark_refit`, default
False), so what the harvest stores — and therefore the trace bench's `chain`
baseline — is byte-identical until somebody asks for A1. Every constant is
`KS_MARK_*` so a sweep of this measure can never move a `CHAIN_*` or a
`KS_FOLLOW_*`. No DB, no API, no `core/`, no rendering path.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import label as label_regions
from scipy.spatial import cKDTree

from tools.pairlab.landmarks import nearest_unique_point
from tools.pairlab.trace import _is_diacritic, _px_to_word_units
from tools.tracebench.frames import MARK_MATCH_MARGIN_UNITS as _RULER_MARGIN
from tools.tracebench.frames import MARK_MATCH_RADIUS_UNITS as _RULER_RADIUS
from tools.tracebench.frames import MARK_MAX_ARC_UNITS as _RULER_MAX_ARC


# ------------------------------------------------------------------ constants
#
# Read from the environment at import time exactly as `follow.py` reads its own
# knobs, so a sweep needs no edit of this file. Every name is `KS_MARK_*`.

# **The search radius.** How far from its composed position a mark may be moved.
# It IS the bench's own mark-match radius, imported so refit and ruler stay
# coupled by construction (a refit that could move a mark further than the
# ruler is willing to call "the same mark" would not be correcting a position,
# it would be inventing a match; if the ruler is ever re-baselined, the refit
# follows visibly through that declaration instead of drifting silently). The
# measured error it has to cover is 0.129 xh median, so 0.6 is generous by a
# factor of ~4.5 and still short of the 0.8 xh at which the bench stops
# classifying a stroke as a mark at all.
MARK_SEARCH_RADIUS_UNITS_ENV = "KS_MARK_SEARCH_RADIUS_UNITS"
MARK_SEARCH_RADIUS_UNITS = float(os.environ.get(MARK_SEARCH_RADIUS_UNITS_ENV) or _RULER_RADIUS)

# **The ambiguity margin.** A second ink cluster whose distance is within this
# of the nearest makes the assignment undecidable from proximity. Imported from
# the ruler for the same reason the radius is: the refit and the ruler must
# call the same situation ambiguous.
MARK_MATCH_MARGIN_UNITS_ENV = "KS_MARK_MATCH_MARGIN_UNITS"
MARK_MATCH_MARGIN_UNITS = float(os.environ.get(MARK_MATCH_MARGIN_UNITS_ENV) or _RULER_MARGIN)

# **What the body claims.** Ink within this distance of the fitted body path is
# the body's and is removed before any mark looks for a target. 0.15 xh is the
# project's existing "these two passes are the same ink" distance
# (`follow.FOLLOW_RETRACE_PROX_UNITS`, the retrace-pair rule the trace bench
# counts with) — on the 1922 plates' ~30 px x-height that is ~4.5 px, about one
# stroke width, so a body stroke claims its own ink and not its neighbour's.
MARK_BODY_CLAIM_UNITS_ENV = "KS_MARK_BODY_CLAIM_UNITS"
MARK_BODY_CLAIM_UNITS = float(os.environ.get(MARK_BODY_CLAIM_UNITS_ENV) or 0.15)

# **How big a mark's ink can be.** A skeleton is one pixel wide, so a cluster's
# pixel count is its arc length in pixels; divided by the x-height it is the
# same number the bench classifies marks with. The cap is 2x the bench's
# `MARK_MAX_ARC_UNITS` (imported) — deliberately loose, because this one only
# has to keep a mark off ink the bench would NEVER call a mark: a missed
# ascender, an unfitted letter, a plate speck grown into a stroke.
MARK_MAX_INK_ARC_UNITS_ENV = "KS_MARK_MAX_INK_ARC_UNITS"
MARK_MAX_INK_ARC_UNITS = float(os.environ.get(MARK_MAX_INK_ARC_UNITS_ENV) or 2 * _RULER_MAX_ARC)

# Sampling step for the body path when the claim is computed. Half a pixel is
# `tracebench.metric.RASTER_STEP_PX`'s reasoning: consecutive samples are then
# closer than one pixel, so a nearest-sample distance and a nearest-polyline
# distance cannot differ by enough to move a claim verdict.
CLAIM_SAMPLE_STEP_PX = 0.5

# Pixel connectivity of an ink cluster: 8-neighbourhood, because a skeleton
# walks diagonally and a 4-neighbourhood would cut one dot into two clusters and
# then refuse it as ambiguous.
_CLUSTER_STRUCTURE = np.ones((3, 3), dtype=bool)

REASON_OK = "ok"
REASON_NO_INK = "no_ink"  # no skeleton was supplied at all
REASON_NO_CANDIDATE = "no_candidate"  # no unclaimed cluster within the radius
REASON_AMBIGUOUS = "ambiguous"  # two clusters, proximity cannot separate them
REASON_CONTESTED = "contested"  # two marks, one cluster — neither gets it


@dataclass(frozen=True)
class MarkRefitOptions:
    """The four knobs, defaulting to the module constants (hence to `KS_MARK_*`)."""

    search_radius_units: float = MARK_SEARCH_RADIUS_UNITS
    match_margin_units: float = MARK_MATCH_MARGIN_UNITS
    body_claim_units: float = MARK_BODY_CLAIM_UNITS
    max_ink_arc_units: float = MARK_MAX_INK_ARC_UNITS


@dataclass(frozen=True)
class MarkRefit:
    """One mark's verdict — what was proposed, what happened, and why.

    Positions are in the WORD's registration frame (baseline 0, 1 unit = one
    x-height), which is the frame the stored trace and `mark_pos_err_xh` live
    in, so a report line can be read against the bench column it is meant to
    move. `shift_units` is the length of the translation in x-heights.
    """

    run_index: int
    entry_index: int
    segment_index: int | None
    slot_index: int | None
    key: str | None
    stroke_index: int | None
    from_units: tuple[float, float]
    to_units: tuple[float, float]
    shift_units: float
    target_ink_px: int  # skeleton pixels of the claimed cluster (0 when refused)
    moved: bool
    reason: str


def _dense_points(polylines: Sequence[np.ndarray], step_px: float) -> np.ndarray:
    """Polylines resampled to at most `step_px` between samples, stacked.

    Segment-wise (never across a pen lift, because the caller hands in one array
    per pen-down polyline), so the body claim follows the path the pen took and
    does not bridge the air between two strokes.
    """
    chunks: list[np.ndarray] = []
    for polyline in polylines:
        pts = np.asarray(polyline, dtype=float).reshape(-1, 2)
        if not len(pts):
            continue
        if len(pts) == 1:
            chunks.append(pts)
            continue
        for a, b in zip(pts[:-1], pts[1:], strict=True):
            steps = max(1, int(np.ceil(float(np.hypot(*(b - a))) / float(step_px))))
            t = np.linspace(0.0, 1.0, steps + 1)[:, None]
            chunks.append(a[None, :] * (1.0 - t) + b[None, :] * t)
    return np.vstack(chunks) if chunks else np.zeros((0, 2))


def unclaimed_ink_mask(skeleton: np.ndarray, body_px: Sequence[np.ndarray], *, claim_px: float) -> np.ndarray:
    """The skeleton minus everything the fitted body path claims.

    "Claimed" is the simplest rule that can be argued from a picture: a skeleton
    pixel closer than `claim_px` to the body path belongs to the body. What
    survives is the ink the fit did not account for — the marks it left behind,
    and (deliberately visible rather than hidden) whatever else it missed, which
    is why the caller still has to reject clusters too big to be a mark.
    """
    ink = np.asarray(skeleton, dtype=bool)
    if ink.ndim != 2:
        raise ValueError("skeleton must be a 2-D boolean image")
    dense = _dense_points(body_px, CLAIM_SAMPLE_STEP_PX)
    if not ink.any() or not len(dense):
        return ink.copy()
    rows, cols = np.nonzero(ink)
    distance, _ = cKDTree(dense).query(np.column_stack([cols.astype(float), rows.astype(float)]))
    free = np.zeros_like(ink)
    keep = distance > float(claim_px)
    free[rows[keep], cols[keep]] = True
    return free


def ink_clusters(free: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """`(centroids, masses)` of the 8-connected clusters of an unclaimed-ink mask.

    Centroids are crop pixels `(x, y)`; masses are pixel counts, i.e. the
    cluster's arc length in pixels (a skeleton is one pixel wide).
    """
    labels, count = label_regions(np.asarray(free, dtype=bool), structure=_CLUSTER_STRUCTURE)
    if not count:
        return np.zeros((0, 2)), np.zeros(0, dtype=int)
    rows, cols = np.nonzero(labels)
    lab = labels[rows, cols]
    mass = np.bincount(lab, minlength=count + 1)[1:]
    sx = np.bincount(lab, weights=cols.astype(float), minlength=count + 1)[1:]
    sy = np.bincount(lab, weights=rows.astype(float), minlength=count + 1)[1:]
    return np.column_stack([sx / mass, sy / mass]), mass.astype(int)


def refit_word_marks(
    entries_by_run: Sequence[Sequence[dict]],
    *,
    xh: float,
    registration: dict,
    skeleton: np.ndarray | None,
    options: MarkRefitOptions | None = None,
) -> tuple[list[list[dict]], list[MarkRefit]]:
    """Move every mark of ONE WORD onto its own ink — or leave it and say why.

    `entries_by_run` are the pen-down polylines of the word's solved runs, in
    solve order, exactly as `tools.pairlab.chain._stroke_polylines_px` emits
    them (crop pixels). The whole word is taken at once on purpose: the body
    claim has to cover EVERY run, or a mark of one run could be pulled onto the
    unclaimed-looking ink of another run's letter.

    Returns `(entries_by_run, reports)`. Untouched entries come back as the same
    dict objects, so a caller can prove "nothing moved" by identity; a moved
    mark is a shallow copy with a translated `points_px` and nothing else
    changed. One report per mark, whether it moved or not — a refusal that is
    not reported is indistinguishable from a mark nobody looked at.
    """
    opts = options or MarkRefitOptions()
    out: list[list[dict]] = [list(entries) for entries in entries_by_run]

    body_px: list[np.ndarray] = []
    marks: list[tuple[int, int, dict, np.ndarray]] = []
    for run_index, entries in enumerate(out):
        for entry_index, entry in enumerate(entries):
            pts = np.asarray(entry["points_px"], dtype=float).reshape(-1, 2)
            if not len(pts):
                continue
            if _is_diacritic(entry, xh, registration):
                marks.append((run_index, entry_index, entry, pts))
            else:
                body_px.append(pts)

    if not marks:
        return out, []

    def _report(index: int, to_px: np.ndarray | None, mass: int, reason: str) -> MarkRefit:
        run_index, entry_index, entry, pts = marks[index]
        centre = pts.mean(axis=0)
        target = centre if to_px is None else np.asarray(to_px, dtype=float)
        from_units = _px_to_word_units(centre[0:1], centre[1:2], xh, registration)[0]
        to_units = _px_to_word_units(target[0:1], target[1:2], xh, registration)[0]
        return MarkRefit(
            run_index=run_index,
            entry_index=entry_index,
            segment_index=entry.get("segment_index"),
            slot_index=entry.get("slot_index"),
            key=entry.get("key"),
            stroke_index=entry.get("stroke_index"),
            from_units=(float(from_units[0]), float(from_units[1])),
            to_units=(float(to_units[0]), float(to_units[1])),
            shift_units=round(float(np.hypot(*(target - centre))) / float(xh), 6),
            target_ink_px=int(mass),
            moved=reason == REASON_OK,
            reason=reason,
        )

    if skeleton is None:
        return out, [_report(i, None, 0, REASON_NO_INK) for i in range(len(marks))]

    free = unclaimed_ink_mask(skeleton, body_px, claim_px=opts.body_claim_units * float(xh))
    centroids, masses = ink_clusters(free)
    eligible = np.flatnonzero(masses <= opts.max_ink_arc_units * float(xh))
    pool = centroids[eligible] if len(eligible) else np.zeros((0, 2))

    # Pass 1: every mark names the cluster it wants (or refuses). Pass 2 applies
    # only the uncontested ones — a cluster two marks both want is given to
    # neither, which is the same refusal doctrine one level up.
    claim: list[tuple[int, str]] = []
    for _, _, _, pts in marks:
        centre = pts.mean(axis=0)
        _, reason, _ = nearest_unique_point(
            pool, centre, radius=opts.search_radius_units * float(xh), margin=opts.match_margin_units * float(xh)
        )
        if reason != REASON_OK:
            claim.append((-1, reason))
            continue
        claim.append((int(np.argmin(np.hypot(pool[:, 0] - centre[0], pool[:, 1] - centre[1]))), REASON_OK))

    wanted = np.bincount([c for c, _ in claim if c >= 0], minlength=max(len(pool), 1))
    reports: list[MarkRefit] = []
    for index, (chosen, reason) in enumerate(claim):
        if chosen < 0:
            reports.append(_report(index, None, 0, reason))
            continue
        if wanted[chosen] > 1:
            reports.append(_report(index, None, 0, REASON_CONTESTED))
            continue
        run_index, entry_index, entry, pts = marks[index]
        target = pool[chosen]
        moved = dict(entry)
        moved["points_px"] = pts + (target - pts.mean(axis=0))
        out[run_index][entry_index] = moved
        reports.append(_report(index, target, int(masses[eligible[chosen]]), REASON_OK))
    return out, reports


def mark_refit_summary(reports: Sequence[MarkRefit]) -> dict:
    """The per-word roll-up a run report carries beside the per-mark rows."""
    moved = [r for r in reports if r.moved]
    reasons: dict[str, int] = {}
    for report in reports:
        reasons[report.reason] = reasons.get(report.reason, 0) + 1
    return {
        "marks": len(reports),
        "moved": len(moved),
        "refused": len(reports) - len(moved),
        "reasons": reasons,
        "median_shift_units": round(float(np.median([r.shift_units for r in moved])), 4) if moved else None,
        "max_shift_units": round(max((r.shift_units for r in moved), default=0.0), 4) if moved else None,
    }


__all__ = [
    "CLAIM_SAMPLE_STEP_PX",
    "MARK_BODY_CLAIM_UNITS",
    "MARK_BODY_CLAIM_UNITS_ENV",
    "MARK_MATCH_MARGIN_UNITS",
    "MARK_MATCH_MARGIN_UNITS_ENV",
    "MARK_MAX_INK_ARC_UNITS",
    "MARK_MAX_INK_ARC_UNITS_ENV",
    "MARK_SEARCH_RADIUS_UNITS",
    "MARK_SEARCH_RADIUS_UNITS_ENV",
    "REASON_AMBIGUOUS",
    "REASON_CONTESTED",
    "REASON_NO_CANDIDATE",
    "REASON_NO_INK",
    "REASON_OK",
    "MarkRefit",
    "MarkRefitOptions",
    "ink_clusters",
    "mark_refit_summary",
    "refit_word_marks",
    "unclaimed_ink_mask",
]
