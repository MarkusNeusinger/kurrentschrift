"""core/laufform.py — the smoothness sensor of a Laufform row (LF11).

The quantity no frozen ruler carries: how often a rendered running form reverses
its curvature per x-height. Both the word bench and the ink follower resample the
wobble away before they score, which is why the defect survived every green
number until the audit of 2026-09-02 measured it directly.
"""

from __future__ import annotations

from types import SimpleNamespace

from core.laufform import ZIGZAG_STEP_UNITS, ZIGZAG_TURN_MIN_DEG, smoothness_gap, zigzag_rate


def _row(anchors, stroke_starts=None, corner_anchors=None):
    meta = {"unit_px": 64.0}
    if stroke_starts is not None:
        meta["stroke_starts"] = stroke_starts
    if corner_anchors is not None:
        meta["corner_anchors"] = corner_anchors
    return SimpleNamespace(anchors=anchors, half_widths=[0.05] * len(anchors), trace_meta=meta)


STRAIGHT = [[i * 0.05, i * 0.02] for i in range(40)]
ARC = [[i * 0.05, (i * 0.05) ** 2 * 0.3] for i in range(40)]


def test_a_straight_stroke_never_reverses():
    assert zigzag_rate(_row(STRAIGHT), STRAIGHT) == 0.0


def test_a_smooth_arc_never_reverses():
    """One consistent bend is form, not defect — the sensor must not tax it."""
    assert zigzag_rate(_row(ARC), ARC) == 0.0


def test_an_alternating_wobble_is_counted():
    """The defect itself: every other anchor pushed across the path. The rate is
    per x-height of arc, so it stays comparable between a short `c` and a long
    capital."""
    wobbly = [[x, y + (0.03 if i % 2 else -0.03)] for i, (x, y) in enumerate(STRAIGHT)]
    assert zigzag_rate(_row(wobbly), wobbly) > 5.0


def test_a_wobble_below_the_turn_threshold_is_not_counted():
    """Under `ZIGZAG_TURN_MIN_DEG` a sign change is the sampler's own rounding,
    not something a reader could see."""
    faint = [[x, y + (1e-5 if i % 2 else -1e-5)] for i, (x, y) in enumerate(STRAIGHT)]
    assert zigzag_rate(_row(faint), faint) == 0.0


def test_a_pen_lift_is_not_a_reversal():
    """Two strokes far apart, each straight: the jump between them is the hand
    setting the pen down elsewhere. Counting it would tax every i for its dot."""
    body = [[i * 0.05, 0.0] for i in range(20)]
    dot = [[0.5, 2.0], [0.55, 2.0], [0.6, 2.0]]
    anchors = body + dot
    assert zigzag_rate(_row(anchors, stroke_starts=[len(body)]), anchors) == 0.0


def test_the_gap_is_measured_against_the_row_s_own_chart_form():
    """A curly capital turns more often than an `l` for reasons that are ductus;
    only the difference to its OWN drawn form is comparable across glyphs."""
    wobbly = [[x, y + (0.03 if i % 2 else -0.03)] for i, (x, y) in enumerate(ARC)]
    gap = smoothness_gap(_row(ARC), wobbly)
    assert gap["chart"] == 0.0
    assert gap["candidate"] > 5.0
    assert gap["gap"] == gap["candidate"] - gap["chart"]
    assert smoothness_gap(_row(ARC), ARC)["gap"] == 0.0


def test_the_sensor_reads_a_finer_step_than_the_nib():
    """0.02 xh is a third of the pooled 1922 nib radius: a wobble the pen could
    not have drawn has to be visible below the width that would hide it."""
    assert ZIGZAG_STEP_UNITS < 0.064 / 2
    assert ZIGZAG_TURN_MIN_DEG == 3.0


def test_a_degenerate_row_is_zero_not_an_error():
    assert zigzag_rate(_row([[0.0, 0.0]]), [[0.0, 0.0]]) == 0.0
    assert zigzag_rate(_row([[0.0, 0.0], [0.0, 0.0]]), [[0.0, 0.0], [0.0, 0.0]]) == 0.0


def test_repeated_samples_cannot_make_the_reading_ill_defined():
    """The sampler rounds to four decimals, so two samples can coincide on a
    slow, tightly curved stretch — and `np.interp` is only defined for a
    strictly increasing parameter. Duplicates are dropped before the arc is
    built, so inserting them changes nothing rather than being undefined."""
    doubled = [p for point in STRAIGHT for p in (point, list(point))]
    assert zigzag_rate(_row(doubled), doubled) == zigzag_rate(_row(STRAIGHT), STRAIGHT) == 0.0

    wobbly = [[x, y + (0.03 if i % 2 else -0.03)] for i, (x, y) in enumerate(ARC)]
    wobbly_doubled = [p for point in wobbly for p in (point, list(point))]
    assert zigzag_rate(_row(wobbly_doubled), wobbly_doubled) > 0.0
