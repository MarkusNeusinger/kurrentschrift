"""Measure a Bahn nobody followed — the sensors of a hand-drawn Streifen-Pfad.

The follower stores six of the Tintentreue's readings out of its own decode
and two it measures against the box's ink afterwards (`tools.eigenhand.pfad`).
A Bahn the AUTHOR drew in the Streifen-Editor has no decode behind it, is saved
with an empty `meta`, and so stays grey in the traffic light for want of a
single number (`core.eigenhand.tintentreue`, grey state 3). V21 of
`docs/proposals/admin-redesign.md` §12.4 closes that: a measuring pass computes
the same readings for a drawn Bahn, so it carries the same Ampel. This module
is that pass's arithmetic; `pfad --messen` is the wiring around it.

WHAT IS THE SAME AND WHAT CANNOT BE. Two of the four graded sensors are the
follower's own code, unchanged: the paper excursion and the AIoU come out of
`tools.eigenhand.pfad._paper_sensors`, handed the drawn strokes where it is
otherwise handed the delivered ones. The other two are decode counts in the
follower, and a drawing has no decode — so they are read here off the SAME
inputs the decode stands on, with the smallest rule that answers the same
question:

* **Tinte ohne Bahn** — the follower's strands (`strands_of` +
  `refine_strands`, on the ink-evidence case the decode reads), and the share
  of their length on strands the Bahn never travels. The follower counts a
  strand as travelled once a decoder state boarded it; a drawing boards
  nothing, so a strand counts as travelled here where at least
  `TRAVELLED_SHARE` of its arc lies within `VISIT_TOLERANCE_XH` of the drawn
  line. Proximity alone would not do: a Bahn that merely CROSSES a strand
  passes within any tolerance of it for a moment, and would mark the whole
  crossing stroke travelled.
* **Absetzer (Bahn)** — the follower's `paper_lifts` are the lifts it made on
  its OWN, beyond the stroke boundaries the composed seed sanctions (the
  i-dot, the umlaut dots, the u-breve). The drawn reading is the same
  difference taken on counts: the drawing's runs, minus one, minus the seed's
  own lifts (`seed_samples(...).stroke`), never below zero. A hand that joins
  where the seed lifts reads as zero, not as a negative that would pay for a
  lift somewhere else.

`jumps` and `hairpins` are decoder EVENTS — a strand change inside the chain,
a retrace turn the decode priced — and a drawing has neither. They are stored
as null, which the light reads as „not measured" and shows as such; they are
graded nowhere today. `runs` and `strands` are counts of the drawing and of
the ink and are stored like the follower's.

Nothing here moves a coordinate. Every function reads the drawn strokes and
the ink; the caller stores the readings BESIDE an entry whose strokes,
registration and letter boundaries it hands back untouched.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

from core.eigenhand.pfad import AUTHORED


# The Verfahren a measured drawn Bahn names in `meta.messung.gemessen_von`. The
# entry's own `verfahren` stays `authored` for good — `displaced_authored` and
# every Herkunft chip depend on it — so the measurement names its producer in
# a block of its own instead.
MESS_VERFAHREN = "messen"

# How near the drawn line has to run to a strand pixel for that pixel to count
# as travelled, in x-heights. A tenth of a letter body: wider than a pen line's
# half width (the skeleton is the ink's centre, the pen draws anywhere inside
# the ink), narrow enough that a neighbouring stroke of the same letter — an
# n's two stems sit half an x-height apart — is not travelled by proxy. A
# choice of this module, not a calibrated bound; the calibration round decides
# nothing about it.
VISIT_TOLERANCE_XH = 0.10
# How much of a strand's arc the drawn line must ride before the strand counts
# as travelled. A half: a crossing passes within the tolerance over roughly
# twice the tolerance of arc, which a strand of any length that matters
# exceeds; a strand the drawing rides along is covered nearly whole.
TRAVELLED_SHARE = 0.5
# Where the drawn polyline is sampled for the nearness test, in pixels. The
# stored strokes are the editor's pointer samples and can be several pixels
# apart; a strand pixel between two of them is travelled, and the densified
# line is what says so.
DENSIFY_STEP_PX = 0.5


def densify(points: Any, step_px: float = DENSIFY_STEP_PX) -> np.ndarray:
    """A polyline resampled so no two consecutive samples are more than `step_px` apart.

    The original vertices are kept, so a single-point or zero-length stroke
    comes back as it went in.
    """
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(pts) < 2:
        return pts
    out = [pts[:1]]
    for a, b in zip(pts[:-1], pts[1:], strict=True):
        n = max(1, int(np.ceil(float(np.hypot(*(b - a))) / step_px)))
        out.append(a + (b - a) * (np.arange(1, n + 1)[:, None] / n))
    return np.vstack(out)


def _arc_weights(points: np.ndarray) -> np.ndarray:
    """Per vertex, the half of the two segments beside it — the arc that vertex stands for."""
    if len(points) < 2:
        return np.zeros(len(points))
    seg = np.hypot(*np.diff(points, axis=0).T)
    weights = np.zeros(len(points))
    weights[:-1] += seg / 2
    weights[1:] += seg / 2
    return weights


def travelled(strand_points: Any, tree: cKDTree, tol_px: float, share: float = TRAVELLED_SHARE) -> bool:
    """Whether the drawn line rides this strand — `share` of its arc within `tol_px`.

    A strand of no length (one pixel) is travelled when that pixel is near
    the line: there is no arc to take a share of.
    """
    pts = np.asarray(strand_points, dtype=float).reshape(-1, 2)
    if not len(pts):
        return False
    near = tree.query(pts, k=1)[0] <= tol_px
    weights = _arc_weights(pts)
    total = float(weights.sum())
    if total <= 0.0:
        return bool(near.any())
    return float(weights[near].sum()) >= share * total


def unvisited_share(strands: Sequence[Any], drawn_px: Sequence[np.ndarray], tol_px: float) -> float | None:
    """The share of the ink skeleton's length on strands the drawn Bahn never travels.

    The follower's `ink_unvisited_share` read for a drawing: the same strands,
    the same length measure (`Strand.length`), rounded the same way. None
    where there is no ink skeleton at all — the follower gives up on such a
    box rather than reporting 0, and 0 is the best reading this sensor has.
    """
    lengths = [float(strand.length) for strand in strands]
    total = sum(lengths)
    if not strands or total <= 0.0:
        return None
    dense = [densify(stroke) for stroke in drawn_px if len(stroke)]
    if not dense:
        return 1.0
    tree = cKDTree(np.vstack(dense))
    missed = sum(
        length for strand, length in zip(strands, lengths, strict=True) if not travelled(strand.points, tree, tol_px)
    )
    return round(missed / total, 3)


def lifts_beyond_seed(runs: int, seed_lifts: int) -> int:
    """The drawing's pen lifts the composition does not sanction — never below zero."""
    return max(0, int(runs) - 1 - int(seed_lifts))


def drawn_readings(
    strands: Sequence[Any], drawn_px: Sequence[np.ndarray], xh_px: float, seed_lifts: int
) -> dict[str, float | int | None]:
    """The follower-side readings of one drawn Bahn, under the follower's own keys.

    `drawn_px` is the Bahn in the CROP's pixels (the frame the strands are
    in), `xh_px` the scale the strands were built at, `seed_lifts` the
    composition's own stroke boundaries.
    """
    runs = sum(1 for stroke in drawn_px if len(stroke))
    return {
        "runs": runs,
        "strands": len(strands),
        "jumps": None,
        "hairpins": None,
        "paper_lifts": lifts_beyond_seed(runs, seed_lifts),
        "ink_unvisited_share": unvisited_share(strands, drawn_px, VISIT_TOLERANCE_XH * float(xh_px)),
    }


def ink_and_seed(case: Any, weights: Any) -> tuple[list[Any], int, float] | None:
    """The strands the follower would decode on, the seed's own lifts, and their x-height.

    Built exactly as `tools.pairlab.tintenpfad.follow_word` builds them — the
    composition, the ink-evidence case, `strands_of` and the sub-pixel rail —
    so a drawn Bahn and a followed one are held against the SAME ink. The
    per-letter affine is left out: it moves where the seed lies, and only the
    seed's stroke boundaries are read here.

    None where the composition itself failed, which the caller names rather
    than measuring half a Bahn. The heavy imports sit inside, like the
    follower's own.
    """
    from tools.pairlab.ink_evidence import INK_EVIDENCE_PAPER_FRACTION, InkEvidenceOptions, ink_evidence_case
    from tools.pairlab.tintenpfad import refine_strands, seed_samples, strands_of
    from tools.wordlab.derive import derive_word

    result = derive_word(case)
    if result.report is None or result.report.get("failed") or not result.registration:
        return None
    xh = float(result.xh_px)
    evidence, _ = ink_evidence_case(case, InkEvidenceOptions(paper_fraction=INK_EVIDENCE_PAPER_FRACTION))
    strands = strands_of(np.asarray(evidence.skel, dtype=bool), xh, weights, {})
    if weights.rail in ("subpixel", "tentfit"):
        refine_strands(strands, np.asarray(evidence.mask, dtype=bool), weights, crop=evidence.crop)
    seed = seed_samples(result, xh, weights, None)
    stroke = np.asarray(seed.stroke, dtype=int)
    return strands, int(stroke.max()) if len(stroke) else 0, xh


def messung(today: str, stages: Mapping[str, Any]) -> dict[str, Any]:
    """The provenance block a measured drawn Bahn carries in `meta.messung`.

    Who measured (`gemessen_von`), when, that the Bahn itself is the author's
    (`herkunft`), the input stages the ink was cut with, and the two constants
    of the travelled-strand rule — so a later change to either reads as a
    different measurement, not as a better hand. The Fleckenmaske it was
    measured under is not repeated here: it goes into the entry's own
    `flecken_n`, where the light reads it.
    """
    return {
        "gemessen_von": MESS_VERFAHREN,
        "gemessen_am": today,
        "herkunft": AUTHORED,
        "eingabe": dict(stages),
        "besucht": {"toleranz_xh": VISIT_TOLERANCE_XH, "anteil": TRAVELLED_SHARE},
    }
