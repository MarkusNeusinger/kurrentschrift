"""Stranded-anchor detection and repair — pure geometry, no I/O.

One module because three consumers need the SAME detector and must never
drift apart: `gradlab` (the force diagnosis), `bindab` (the A/B) and the
harvest (the repair). It imports nothing project-side, so the harvest can use
it without the import cycle `harvest -> gradlab -> harvest`.

The detector is the measured shape of the defect (`qualitaetsmetrik.md` §11):
an anchor BOTH of whose steps are at least `STRANDED_STEP_RATIO` times the
median step of its own pen-stroke. On the author-marked outliers it hits the
marked anchor in 16 of 17 cases.

The repair replaces a flagged anchor by the linear interpolation of its
nearest unflagged neighbours within the same stroke — never snapping to ink
(§8's rejected hinge showed why: at a crossing the nearest ink is the wrong
stroke) and never crossing a pen lift. It exists because four objective-side
attempts were measured and rejected (§7, §8, §10, §11d): no term removes the
excursion without collateral, so the excursion is removed where it lands, as a
LOGGED repair. The owner's explicit trade (2026-08-10): an interpolated anchor
slightly off the ink is the lesser defect; the peak is the one that must go.

The gate still judges the UNREPAIRED geometry — a repair is a near-rejection,
never a pass (§11's condition). What changes is only what an ACCEPTED
occurrence contributes to `instances` and the per-anchor Laufform medians.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


# An anchor counts as STRANDED when BOTH of its steps are at least this many
# times the median step of its own pen-stroke. This is the measured SHAPE of the
# defect rather than a tuned threshold (`qualitaetsmetrik.md` §11): 17 of the
# author's 22 marked outliers sit on an anchor of exactly this form, and where
# the marked anchor is genuinely beside the ink the excursion is exactly one
# anchor long in 12 of 12 cases — which is why a single interior anchor, not a
# stretch of chain, is what the repair below replaces. Deliberately NOT the
# harvest gate's `MAX_ANCHOR_SPIKE_RATIO` (8.0): the gate asks "is this
# occurrence unusable", this asks "is this one anchor a lone excursion".
STRANDED_STEP_RATIO = 3.0
# Below this many steps a stroke has no meaningful median to compare against.
MIN_STROKE_STEPS = 4

# LF14 (`messjournal.md` §14 „Laufform LF14 `sep06`"): skip the repair where the
# row's own ductus writes a LOOP. Default False — off, and then this module
# behaves exactly as it did before the switch existed, whatever a caller passes.
#
# Why the exception is not special pleading. The detector asks „is this one
# anchor a lone excursion" and answers it from step lengths alone: an anchor
# both of whose steps are three times its stroke's median step. Inside a tight
# counter that description also fits the apex the loop is MADE of — the anchors
# there turn through a large angle over a short arc, so the fit widening the
# loop by a few hundredths lengthens both steps at once. The repair then chords
# the apex to its neighbours, which lie on the two strands, and the counter
# closes: measured on the `sep05` root, of the five repaired occurrences of the
# five counter-carrying keys the worst loses 0.1068 xh of aperture, and the `g`
# of „Sprünge" alone drags its stored row down by 0.0883.
#
# The exception is deliberately NARROW. It does not soften the detector, does
# not touch the gate (which judges the unrepaired geometry either way), and does
# not reach a single anchor outside a loop range the CHART row draws — the same
# occurrence-independent ranges `core.aggregate.loop_ranges` hands the running
# form. Its cost is named: a genuine excursion whose anchor happens to land
# inside a counter now survives into the occurrence. That is the trade the
# owner's 2026-08-10 rule already frames — the peak is the defect that must go —
# read the other way round where the peak is the letter.
LOOP_AWARE_REPAIR = False


def _stroke_bounds(k: int, stroke_starts: Sequence[int] | None) -> list[tuple[int, int]]:
    bounds = sorted({0, *(int(s) for s in (stroke_starts or []) if 0 < int(s) < k), k})
    return list(zip(bounds[:-1], bounds[1:], strict=False))


def stranded_anchors(anchors: np.ndarray, stroke_starts: Sequence[int] | None) -> dict[int, tuple[float, float]]:
    """`{anchor index: (prev step ratio, next step ratio)}` of the strandings.

    Per pen-stroke, never across a lift — a lift is the hand setting down
    somewhere else, and pricing it would flag every multi-stroke glyph for
    writing its own ductus.
    """
    k = len(anchors)
    out: dict[int, tuple[float, float]] = {}
    for a, b in _stroke_bounds(k, stroke_starts):
        seg = anchors[a:b]
        if len(seg) < MIN_STROKE_STEPS + 1:
            continue
        steps = np.hypot(*np.diff(seg, axis=0).T)
        med = float(np.median(steps))
        if not med > 0.0:
            continue
        for i in range(1, len(seg) - 1):
            r_prev, r_next = float(steps[i - 1] / med), float(steps[i] / med)
            if r_prev >= STRANDED_STEP_RATIO and r_next >= STRANDED_STEP_RATIO:
                out[a + i] = (r_prev, r_next)
    return out


def repair_stranded_anchors(
    anchors: np.ndarray,
    stroke_starts: Sequence[int] | None,
    loop_ranges: Sequence[tuple[int, int]] | None = None,
    *,
    loop_aware: bool = LOOP_AWARE_REPAIR,
) -> tuple[np.ndarray, list[int]]:
    """Interpolate every stranded anchor from its unflagged stroke neighbours.

    Returns `(repaired copy, sorted flagged indices actually repaired)`. With
    no stranding the input array is returned UNCHANGED (the same object), so a
    caller can use identity to skip logging.

    A maximal run of consecutive flagged anchors is replaced as one piece:
    each flagged anchor moves onto the chord between the nearest unflagged
    neighbour on each side, at its index-proportional position — never
    interpolated from a flagged neighbour, which would place it against the
    excursion it is there to remove. A run touching a stroke's edge has no
    neighbour on one side and is left untouched (the detector only flags
    interior anchors, but a run may still reach index 0's or the last index's
    neighbourhood). Every position is read off the UNREPAIRED geometry, so no
    repair cascades into the next one.

    **Interpolation only — never a snap to nearby ink.** That distinction is
    the whole reason this is not the hinge rejected in §8: "snap to the nearest
    ink" has to choose a branch, and at a crossing it chooses the wrong one. A
    midpoint has no branch to choose. What the repaired anchor claims is
    narrower and honest — *the fit put this anchor somewhere the ink did not
    constrain, so report the chain without that excursion rather than with an
    invented detour* — at the price that it may sit slightly off the ink where
    the true stroke curves. That is the accepted trade.

    It stays a repair of a MEASUREMENT and is therefore only legitimate under
    the conditions §11 set out: logged per repair (the returned indices, and
    the distance moved is readable from the two arrays), and the gate must
    judge the UNREPAIRED geometry, so a repair is a near-rejection and never a
    pass.

    `loop_ranges` are the `[start, end)` anchor ranges over which the row's own
    ductus closes a loop (`core.aggregate.loop_ranges`, passed in so that this
    module keeps importing nothing project-side). They are read ONLY while
    `loop_aware` is on — it defaults to the module switch `LOOP_AWARE_REPAIR`,
    which is False — and then a flagged anchor inside one is left alone. With
    the switch off the argument changes nothing, which is what keeps every
    stored occurrence reproducible.
    """
    flags = sorted(stranded_anchors(anchors, stroke_starts))
    if loop_aware and loop_ranges:
        flags = [i for i in flags if not any(int(a) <= i < int(b) for a, b in loop_ranges)]
    if not flags:
        return anchors, []
    flagged = set(flags)
    repaired = anchors.astype(float, copy=True)
    done: list[int] = []
    for a, b in _stroke_bounds(len(anchors), stroke_starts):
        i = a
        while i < b:
            if i not in flagged:
                i += 1
                continue
            j = i
            while j + 1 < b and (j + 1) in flagged:
                j += 1
            left, right = i - 1, j + 1
            if left >= a and right < b:
                for m in range(i, j + 1):
                    t = (m - left) / (right - left)
                    repaired[m] = (1.0 - t) * anchors[left] + t * anchors[right]
                    done.append(m)
            i = j + 1
    if not done:
        return anchors, []
    return repaired, sorted(done)


__all__ = [
    "LOOP_AWARE_REPAIR",
    "MIN_STROKE_STEPS",
    "STRANDED_STEP_RATIO",
    "repair_stranded_anchors",
    "stranded_anchors",
]
