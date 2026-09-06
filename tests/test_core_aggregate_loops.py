"""core/aggregate.py — the loop-faithful running form (LF13).

An elementwise median over curves whose loops disagree — about where they sit,
how big they are, or where along the loop each anchor landed — produces a loop
smaller than any of them. These tests pin the three properties the
pre-registration promised: the loops are FOUND on the chart row, registering
them recovers aperture the plain median eats, and the switch is genuinely off at
window 0 — byte for byte, so the rows LF11 and LF12 derived stay what they were.
"""

from __future__ import annotations

import numpy as np

from core.aggregate import align_loops, loop_faithful_median, loop_ranges, spline_basis_median


N_ANCHORS = 120
LOOP = slice(40, 80)


def _loop_curve(*, radius: float = 0.25, phase: float = 0.0, scale: float = 1.0, shift=(0.0, 0.0)):
    """A stroke that rises, throws one full loop and leaves — the shape of an `a`.

    `phase` slides the anchors along the loop without moving the loop, `scale`
    resizes it, `shift` moves it. Those are the three ways two tracings of the
    same letter disagree, and each of them makes an elementwise median contract.
    """
    out = []
    for i in range(N_ANCHORS):
        t = i / (N_ANCHORS - 1)
        if t < 1 / 3:
            out.append([0.5 - radius * 1.6 * (1 / 3 - t) * 3, 0.5 - radius * 2.2 * (1 / 3 - t) * 3])
        elif t > 2 / 3:
            out.append([0.5 + radius * 1.6 * (t - 2 / 3) * 3, 0.5 - radius * 2.2 * (t - 2 / 3) * 3])
        else:
            angle = 2.0 * np.pi * (t - 1 / 3) * 3.0 - np.pi / 2.0 + phase
            out.append([0.5 + radius * scale * np.cos(angle), 0.5 + radius * scale * np.sin(angle)])
    return [[x + shift[0], y + shift[1]] for x, y in out]


CHART = _loop_curve()
WIDTHS = [0.05] * N_ANCHORS
RANGES = loop_ranges(CHART, WIDTHS)


def _aperture(anchors) -> float:
    """The loop's inscribed diameter, read on its own anchors.

    Cheap and exact enough here: the loop's anchors form a ring, so the largest
    circle inside it is bounded by the ring's nearest point to its centre. The
    production ruler rasterises the DRAWN curve; this test only asks whether the
    median contracted and by how much against the occurrences.
    """
    ring = np.asarray(anchors, dtype=float)[LOOP]
    return 2.0 * float(np.min(np.linalg.norm(ring - ring.mean(axis=0), axis=1)))


def _scattered_stack(n: int = 7, *, scale_spread: float = 0.0):
    """Occurrences that disagree the way real tracings do: a different place, a
    different phase, optionally a different size."""
    rng = np.random.default_rng(7)
    return np.asarray(
        [
            _loop_curve(
                shift=(float(rng.normal(0.0, 0.04)), float(rng.normal(0.0, 0.04))),
                phase=float(rng.normal(0.0, 0.35)),
                scale=1.0 + scale_spread * float(rng.normal()),
            )
            for _ in range(n)
        ],
        dtype=float,
    )


def test_a_chart_row_with_a_loop_reports_it_and_a_straight_one_reports_none():
    assert len(RANGES) == 1
    start, end = RANGES[0]
    assert 0 < start < LOOP.start
    assert LOOP.stop < end < N_ANCHORS
    assert loop_ranges([[i / 59.0, 0.0] for i in range(60)], [0.05] * 60) == []


def test_window_zero_leaves_the_stack_and_the_median_byte_identical():
    """The switch is off by default, and off has to mean untouched — LF11's and
    LF12's rows were derived through this call and may not move by a bit."""
    stack = _scattered_stack()
    assert np.array_equal(align_loops(stack, CHART, RANGES, window=0.0), stack)
    plain, _ = spline_basis_median(stack, CHART, knot_spacing=0.16)
    faithful, notes = loop_faithful_median(stack, CHART, WIDTHS, knot_spacing=0.16, window=0.0)
    assert np.array_equal(plain, faithful)
    assert not any("registered" in note for note in notes)


def test_registration_recovers_aperture_the_plain_median_eats():
    """The point of the arm: every occurrence carries more aperture than the
    median built from them, and registering the loops first gives some back."""
    stack = _scattered_stack()
    occurrence = float(np.median([_aperture(a) for a in stack]))
    plain = _aperture(np.median(stack, axis=0))
    registered = _aperture(np.median(align_loops(stack, CHART, RANGES, window=0.25), axis=0))
    assert plain < occurrence
    assert registered > plain


def test_registering_the_size_helps_where_the_occurrences_differ_in_size():
    """The second half of the similarity. With a size spread in the stack, place
    alone leaves aperture on the table that place-and-size recovers."""
    stack = _scattered_stack(scale_spread=0.18)
    place_only = _aperture(np.median(align_loops(stack, CHART, RANGES, window=0.25, scale=False), axis=0))
    both = _aperture(np.median(align_loops(stack, CHART, RANGES, window=0.25, scale=True), axis=0))
    assert both > place_only


def test_registration_targets_the_stack_and_nothing_outside_it():
    """What the mechanism actually guarantees, pinned as such.

    NOT an aperture bound — a scalar radius is not an inscribed diameter, and
    the pointwise median of anisotropically disagreeing loops can synthesise a
    wider hole than any input (Copilot on PR #552; the `Z` and `w` rows do it on
    the real root, and so do the STORED rows). What IS guaranteed: the loops are
    brought onto the stack's OWN medians, so the registered stack's median loop
    radius is the median radius of the stack it came from — no free parameter,
    no target from outside.
    """
    stack = _scattered_stack(scale_spread=0.18)
    # Measured over the range the mechanism actually normalises — the chart's
    # loop range, not the test's convenience slice.
    ring = slice(*RANGES[0])

    def radius(anchors) -> float:
        loop = np.asarray(anchors, dtype=float)[ring]
        return float(np.median(np.linalg.norm(loop - loop.mean(axis=0), axis=1)))

    target = float(np.median([radius(a) for a in stack]))
    registered = align_loops(stack, CHART, RANGES, window=0.25)
    assert np.allclose([radius(a) for a in registered], target, atol=1e-9)


def test_the_running_form_keeps_its_place():
    """The median shift is zero by construction, so registration may not move the
    form — only stop the occurrences being medianed against each other's
    placement. Measured at the stroke ends, where no fade reaches."""
    stack = _scattered_stack()
    before = np.median(stack, axis=0)
    after = np.median(align_loops(stack, CHART, RANGES, window=0.25), axis=0)
    assert np.allclose(before[:5], after[:5], atol=1e-9)
    assert np.allclose(before[-5:], after[-5:], atol=1e-9)


def test_a_stack_that_already_agrees_is_left_alone():
    """No disagreement, no correction: identical occurrences must come back
    unchanged, or the mechanism adds aperture rather than recovering it."""
    stack = np.asarray([_loop_curve() for _ in range(4)], dtype=float)
    assert np.allclose(stack, align_loops(stack, CHART, RANGES, window=0.25), atol=1e-12)
