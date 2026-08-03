"""Degeneracy detector for a chain-fitted connector (issue #278, Stage B).

`docs/proposals/uebergaenge-befund.md` §5c closes on a named, unguarded failure:
on the isolated letter-pair drills of Abb. 20 the chain connector derails in
**11 of 23** occurrences — a long straight diagonal drawn clean through both
letters, in part running backwards — and *not one of those rows is caught by
today's QC*. They all report `chain_c_converged` and `chain_connector_yielded`
true and sit on no bound, because both gates ask only whether the segment's own
residual is small: a straight line laid across two letters has plenty of ink
under it and fits itself perfectly. The failure is not in the residual, it is in
the connector's **shape and reach** — which is what this module measures.

Four signals, each a geometric statement about the curve rather than about its
fit (the plan's §B.2 design):

1. **seam share** — arc lying outside the specimen's ink gap, i.e. left of the
   left letter's ink edge plus right of the right letter's. A join legitimately
   reaches into both stub zones; §5 measured that replacement zone at 0.2–0.4 xh
   per side. The plan's starting threshold was 0.8 xh *total* (twice the upper
   band edge, summed over both sides), but calibration showed sound joins
   routinely claim ~1.1 xh, so the calibrated default is
   `QcThresholds.max_seam_total_units = 1.3`. Beyond that the connector is no
   longer joining two letters, it is redrawing them.
2. **backward arc** — net rightward progress per unit of arc. A German cursive
   join runs left to right and has to *arrive*; the §5c failure does not. The
   plan proposed this as the share of arc travelling with dx < 0, and that form
   was calibrated and rejected: on the word plates a healthy join dips back all
   the time (every loop exit, every overlapping pair), so the share separates
   nothing — median 0.45 on the sound pair drills against 0.74 on the failed
   ones, with sound rows at 1.00. Measured at the endpoints instead it is decisive
   (see `ConnectorSignals.forward_ratio`).
3. **arc vs. gap** — total arc against the space there was to cross,
   `gap + 2 × 0.4 xh` (the gap plus both stub zones, i.e. the most arc an honest
   join can need). More than twice that is a detour.
4. **straightness × length** — arc/chord ≈ 1 *and* arc ≥ 1 xh. Either alone is
   innocent: a short connector is often nearly straight, and a long one that
   curves is just a long join. Together they are the §5c phenomenon verbatim —
   the long straight diagonal.

Pure: numpy in, reason code out. No I/O, no DB, no `core/`, and deliberately no
`ChainFit` — the caller hands over a plain polyline and two ink extents, so the
harvest can run the same check without building a chain fit first.

Calibration — pre-registered, and **in-sample on 23 pair-drill rows**
------------------------------------------------------------------
Run: `chainbench --set all --jobs 8` (248 occurrences). Labels: the 11 pair-drill
occurrences §5c names, taken as the worst 11 of the 23 pair rows carrying a
matched-arc M3 number — a clean break (0.164 against the 12th at 0.113) that
reproduces the "11 von 23" exactly. Control: the 214 word-plate rows, where §5c
measures the same failure at ~3 %.

    known-bad (11)     flagged 11/11 — 10 backward_arc, 1 seam_share
    word rows (214)    flagged  9/214 = 4.2 %
      … of those 9:    6 are among the 8 WORST word rows by the independent M3
                       label (0.658 · 0.478 · 0.382 · 0.178 · 0.159 · 0.142,
                       against a word-plate median of 0.032)
                       2 carry no matched M3 at all — unlabelable, not judged
                       1 (`streiten` slot 0, M3 0.021) is a real false positive
    demonstrable FP    1/179 labelable word rows = 0.6 %
    other pair rows    flagged 5/23 — unlabelled; §5c calls 12 of 23 sound, so
                       some of these are over-flagging and some are the same
                       failure below the M3 cut. Not claimed either way.

The pre-registered line was "≥10 of 11 at ≤3 % on the word rows". On the raw
flag rate this **misses it, at 4.2 %** — stated plainly rather than re-framed.
The 3 % line is reachable (`min_forward_ratio` −0.05, `max_seam_total_units` 1.5
→ 10/11 known-bad, 4/214 = 1.9 %), but only by dropping detections that the
independent M3 label calls genuine, and a guard whose job is to keep a
contaminated join out of `pair_aggregates` should prefer recall. Both settings
are one `dataclasses.replace` apart.

Two of the four signals — **arc vs. gap** and **straightness × length** — never
fire on any of the 248 occurrences. Their thresholds are therefore the plan's
starting values, carry no evidence, and are kept only as cheap guards against
failure modes this corpus does not contain.

Everything here is fitted on 11 positives. It is a guard tuned to a known
failure, not an independently validated classifier.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# Per-side arc (xh) of the stub-replacement zone measured in
# `docs/proposals/uebergaenge-befund.md` §5 — the band a healthy join is allowed
# to claim on each letter. Both the seam-share and the arc-vs-gap threshold are
# expressed as multiples of it rather than as free constants.
SEAM_BAND_UNITS = 0.4


@dataclass(frozen=True)
class QcThresholds:
    """The four signals' trip points plus the size gate, in xh units and shares.

    Frozen so a caller cannot mutate the shared `DEFAULTS` instance by accident;
    override with `dataclasses.replace` or by constructing a new one.

    Calibrated in-sample on the 248 chainbench occurrences (`--set all`), against
    the 11 labelled pair-drill failures of §5c; see the module docstring for the
    confusion table and for which of these numbers carry evidence and which do
    not.
    """

    # Endpoint distance below which a connector is a stub and NOT rated at all:
    # every signal here is a statement about a curve's course, and a quarter
    # x-height of travel is too little course to have one. Calibrated, and the
    # single most valuable threshold in the set — without it the direction rule
    # alone costs 12 % of the word rows, with it 4 %.
    min_chord_units: float = 0.25
    # Total arc (both sides summed) allowed outside the ink gap. The plan's
    # starting value was 2 × the §5 stub-replacement band (0.8 xh); the
    # calibration raised it to 1.3, because sound joins routinely claim ~1.1 xh
    # across both letters and the failures are not distinguished by reach.
    max_seam_total_units: float = 1.3
    # Net rightward progress per unit of arc below which the connector counts as
    # not having arrived (see `ConnectorSignals.forward_ratio`). Zero is not a
    # tuned value but the natural one: a join that ends to the LEFT of where it
    # started has not joined anything.
    min_forward_ratio: float = 0.0
    # Arc against `gap + 2 × SEAM_BAND_UNITS` — the most arc an honest join needs.
    # UNCALIBRATED: never fires on the 248-occurrence corpus (word-plate P99 is
    # 1.48), so this is still the plan's starting value, kept as a cheap guard
    # against a detour the corpus happens not to contain.
    max_arc_vs_gap: float = 2.0
    # arc/chord at or below this counts as "straight" …
    max_straight_ratio: float = 1.02
    # … and only matters from this arc length on. Also UNCALIBRATED: the pair
    # together never fire on the corpus either.
    min_straight_arc_units: float = 1.0


DEFAULTS = QcThresholds()


@dataclass(frozen=True)
class ConnectorSignals:
    """The four raw measurements behind a reason code, all in xh units.

    Reported alongside the verdict so a flagged row can be argued with rather
    than only believed — and so the thresholds can be re-calibrated from stored
    numbers instead of a re-run.
    """

    arc_units: float
    chord_units: float
    net_dx_units: float
    seam_left_units: float
    seam_right_units: float
    backward_frac: float
    gap_units: float

    @property
    def seam_total_units(self) -> float:
        return self.seam_left_units + self.seam_right_units

    @property
    def forward_ratio(self) -> float:
        """Net rightward progress per unit of arc — 1.0 for a straight rightward
        stroke, 0 for one that ends where it began, negative for one that ends to
        the LEFT of its start.

        This is the calibrated form of the plan's "backward arc" signal. The
        share-of-arc form (`backward_frac`) turned out not to separate: on the
        word plates a healthy join dips back constantly (every loop exit does,
        every overlapping letter pair does), so its median share is not far off a
        degenerate one's. What the §5c failure actually does is fail to *arrive* —
        the `ds` drill's connector leaves at x 1.68 and ends at x 1.21, a
        near-vertical slide down the d's own stem — and that is an endpoint
        statement, not an arc-share one.
        """
        return self.net_dx_units / self.arc_units if self.arc_units > 0 else 0.0

    @property
    def straightness(self) -> float:
        """arc/chord — 1.0 for a straight line, larger the more the curve bends.

        `inf` for a closed curve (zero chord), which is degenerate by any reading
        but is not *this* signal's business: the straightness rule only fires
        together with a length, and an infinite ratio never passes `<=`.
        """
        return self.arc_units / self.chord_units if self.chord_units > 0 else float("inf")

    @property
    def arc_vs_gap(self) -> float:
        return self.arc_units / (self.gap_units + 2.0 * SEAM_BAND_UNITS)


def _arc_outside(pts: np.ndarray, x_split: float, *, keep_left: bool) -> float:
    """Arc length of the part of a polyline on one side of a vertical line,
    crossing segments split by linear interpolation.

    `chainbench.arc_share`'s rule, re-implemented here rather than imported so
    this module stays free of the harness (and of the harness' imports of
    `core/`, `scipy` and the fixture loader).
    """
    total = 0.0
    for p, q in zip(pts[:-1], pts[1:], strict=True):
        seg = float(np.hypot(q[0] - p[0], q[1] - p[1]))
        if seg == 0.0:
            continue
        inside_p = (p[0] < x_split) if keep_left else (p[0] > x_split)
        inside_q = (q[0] < x_split) if keep_left else (q[0] > x_split)
        if inside_p and inside_q:
            total += seg
        elif inside_p or inside_q:
            t = (x_split - p[0]) / (q[0] - p[0])
            total += seg * abs(t if inside_p else 1.0 - t)
    return total


def connector_signals(
    connector_units: np.ndarray, a_max_x: float, b_min_x: float, xh_units: float = 1.0
) -> ConnectorSignals | None:
    """The four raw signals for one connector, or None when there is no curve.

    `connector_units` is the connector polyline and `a_max_x` / `b_min_x` the two
    letters' facing ink edges, all in the SAME frame; `xh_units` is that frame's
    x-height, so a caller working in composed units passes the default 1.0 and one
    working in crop px passes `xh_px`. Nothing here reads a fit object — the
    harvest can call this with an ink-read polyline just as well.
    """
    pts = np.asarray(connector_units, dtype=float).reshape(-1, 2)
    if len(pts) < 2 or not (xh_units > 0):
        return None
    steps = pts[1:] - pts[:-1]
    seg = np.hypot(steps[:, 0], steps[:, 1])
    arc = float(seg.sum())
    if arc <= 0.0:
        return None
    back = float(seg[steps[:, 0] < 0.0].sum())
    return ConnectorSignals(
        arc_units=arc / xh_units,
        chord_units=float(np.hypot(*(pts[-1] - pts[0]))) / xh_units,
        net_dx_units=float(pts[-1, 0] - pts[0, 0]) / xh_units,
        seam_left_units=_arc_outside(pts, float(a_max_x), keep_left=True) / xh_units,
        seam_right_units=_arc_outside(pts, float(b_min_x), keep_left=False) / xh_units,
        backward_frac=back / arc,
        gap_units=max(0.0, (float(b_min_x) - float(a_max_x)) / xh_units),
    )


def degenerate_reason(signals: ConnectorSignals, *, thresholds: QcThresholds = DEFAULTS) -> str | None:
    """First tripped signal for an already-measured connector, or None.

    Fixed priority — seam share · backward arc · arc vs. gap · straight-and-long —
    so a row's reason code is stable across runs and the per-reason histogram in
    the report counts each row once. A degenerate curve usually trips several;
    the code names the one that is most directly a statement about the seam.

    Ahead of all four sits the size gate: a connector whose endpoints are less
    than `min_chord_units` apart is a stub, and „it drifted 0.1 xh leftwards" is
    noise rather than a verdict.
    """
    if signals.chord_units < thresholds.min_chord_units:
        return None
    if signals.seam_total_units > thresholds.max_seam_total_units:
        return "seam_share"
    if signals.forward_ratio < thresholds.min_forward_ratio:
        return "backward_arc"
    if signals.arc_vs_gap > thresholds.max_arc_vs_gap:
        return "arc_vs_gap"
    if signals.straightness <= thresholds.max_straight_ratio and signals.arc_units >= thresholds.min_straight_arc_units:
        return "straight_long"
    return None


def connector_degenerate(
    connector_units: np.ndarray,
    a_max_x: float,
    b_min_x: float,
    xh_units: float = 1.0,
    *,
    thresholds: QcThresholds = DEFAULTS,
) -> str | None:
    """Reason code for a degenerate chain connector, or None if it looks healthy.

    The one-call form of `connector_signals` + `degenerate_reason`. A curve too
    short to measure (fewer than two points, zero arc) is **not** flagged: this
    detector answers „did the connector run away", and „there is no connector"
    is a different question the chain's own `n_cov` gate already asks.
    """
    signals = connector_signals(connector_units, a_max_x, b_min_x, xh_units)
    if signals is None:
        return None
    return degenerate_reason(signals, thresholds=thresholds)
