"""`tools.laufform.saatkorrespondenz` — the A48 anchor correspondence, on synthetic data.

Everything here runs on plain numpy: an anchor set sampled by the REAL
`core.template` sampler, an affine image of a slice of it standing in for a
composed item, and a hand-built seed. No fixture root, no decode, no DB — the
question these tests answer is whether the bookkeeping lines up, and that is a
question about indices, not about ink.
"""

from __future__ import annotations

import numpy as np
import pytest

from core.template import build_sample_plan, sample_with_sample_plan
from tools.laufform.saatkorrespondenz import SLICE_TOL, anchor_sample_index, identify_slice, slot_correspondence


def arch(n: int = 14) -> np.ndarray:
    """A curved, ASYMMETRIC anchor row.

    Both properties matter: a straight row fits any affine, and a symmetric one
    (a half circle) is congruent to its own mirror image, so a reflected shift
    would be a second true answer and the test would be about nothing.
    """
    t = np.linspace(0.0, np.pi, n)
    return np.column_stack([np.cos(t) * -1.0 + 1.0 + 0.35 * t, np.sin(t) * (1.0 - 0.22 * t)])


def sampled(anchors: np.ndarray, stroke_starts: list[int] | None = None, n: int = 240) -> list[np.ndarray]:
    plan = build_sample_plan(anchors, stroke_starts, [], n)
    sx, sy, _ = sample_with_sample_plan(anchors, np.full(len(anchors), 0.1), plan)
    pts = np.column_stack([sx, sy])
    bounds = [*plan.sample_starts, len(pts)]
    return [pts[a:b] for a, b in zip(bounds, bounds[1:], strict=False)]


def test_anchor_sample_index_lands_on_every_anchor() -> None:
    anchors = arch()
    strokes = sampled(anchors)
    idx = anchor_sample_index(anchors, [0], [])
    assert set(idx) == set(range(len(anchors)))
    for j, (stroke, row) in idx.items():
        pts = strokes[stroke]
        lo, hi = int(np.floor(row)), min(int(np.ceil(row)), len(pts) - 1)
        w = row - lo
        # The sampler runs a cubic spline THROUGH the anchors, so reading the
        # polyline at the anchor's own parameter lands on it up to the chord
        # error of one sample step — never a whole anchor spacing away.
        place = pts[lo] + w * (pts[hi] - pts[lo])
        assert np.hypot(*(place - anchors[j])) < 0.01


def test_anchor_sample_index_ends_are_the_stroke_ends() -> None:
    anchors = arch()
    idx = anchor_sample_index(anchors, [0], [])
    assert idx[0] == (0, 0.0)
    assert idx[len(anchors) - 1][0] == 0
    assert idx[len(anchors) - 1][1] == pytest.approx(len(sampled(anchors)[0]) - 1)


def test_anchor_sample_index_splits_by_pen_stroke() -> None:
    anchors = np.vstack([arch(8), arch(8) + np.array([3.0, 0.0])])
    idx = anchor_sample_index(anchors, [0, 8], [])
    assert {idx[j][0] for j in range(8)} == {0}
    assert {idx[j][0] for j in range(8, 16)} == {1}
    assert idx[8][1] == 0.0


def test_identify_slice_proves_an_affine_slice() -> None:
    stroke = sampled(arch())[0]
    a = np.array([[1.3, 0.2], [0.0, 0.9]])
    item = stroke[40:200] @ a.T + np.array([5.0, -2.0])
    match = identify_slice(item, [stroke])
    assert match is not None
    assert match.stroke == 0
    assert match.shift == 40
    assert match.proven.all()
    assert match.resid < SLICE_TOL


def test_identify_slice_proves_a_piecewise_deformation_outside_its_seam() -> None:
    # The shape of `core/compose.py`'s ascender lean: a shear that only acts
    # above a pivot. No single affine explains the stroke; a local one does,
    # everywhere but at the seam.
    stroke = sampled(arch())[0]
    item = stroke.copy()
    item[:, 0] += 0.35 * np.maximum(0.0, item[:, 1] - 0.5)
    match = identify_slice(item, [stroke])
    assert match is not None
    assert match.shift == 0
    assert match.proven.mean() > 0.5
    assert not match.proven.all()


def test_identify_slice_refuses_a_foreign_curve() -> None:
    stroke = sampled(arch())[0]
    foreign = np.column_stack([np.linspace(0, 1, 120), np.sin(np.linspace(0, 9, 120))])
    match = identify_slice(foreign, [stroke])
    assert match is None or not match.proven.any()


def seed_over(item: np.ndarray, step: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """Sample positions along an item, as `seed_samples` would: (item index, pos)."""
    # `seed_samples` resamples each item from its first vertex to its last, so
    # the stand-in has to reach the end too.
    pos = np.unique(np.append(np.arange(0.0, len(item) - 1, step), float(len(item) - 1)))
    return np.zeros(len(pos), dtype=int), pos


def test_slot_correspondence_places_every_anchor_when_the_decode_is_complete() -> None:
    anchors = arch()
    stroke = sampled(anchors)[0]
    item = stroke.copy()
    seed_item, seed_pos = seed_over(item)
    # A decode that landed exactly on the composed form: the read must return
    # the anchors themselves.
    state_xy = np.array([item[int(round(p))] for p in seed_pos])
    sc = slot_correspondence(
        anchors=anchors,
        stroke_starts=[0],
        corner_anchors=[],
        template_strokes=[stroke],
        items=[(0, item)],
        seed_pos=seed_pos,
        seed_item=seed_item,
        state_xy=state_xy,
    )
    assert sc.complete
    assert sc.slice_resid < SLICE_TOL
    assert np.abs(sc.anchors_px - anchors).max() < 0.02


def test_slot_correspondence_leaves_a_paper_sample_uncovered() -> None:
    anchors = arch()
    stroke = sampled(anchors)[0]
    item = stroke.copy()
    seed_item, seed_pos = seed_over(item)
    state_xy = np.array([item[int(round(p))] for p in seed_pos])
    state_xy[len(state_xy) // 2 :] = np.nan  # the decode gave up half way
    sc = slot_correspondence(
        anchors=anchors,
        stroke_starts=[0],
        corner_anchors=[],
        template_strokes=[stroke],
        items=[(0, item)],
        seed_pos=seed_pos,
        seed_item=seed_item,
        state_xy=state_xy,
    )
    assert not sc.complete
    assert sc.covered.any()
    assert np.isnan(sc.anchors_px[sc.covered == False]).all()  # noqa: E712 — the mask, not a bool


def test_slot_correspondence_does_not_reach_a_trimmed_end() -> None:
    # The composition cuts the coupling stub off the letter: the anchors the
    # cut removed have no place in the composed form, and must come back
    # uncovered rather than extrapolated.
    anchors = arch()
    stroke = sampled(anchors)[0]
    item = stroke[60:]
    seed_item, seed_pos = seed_over(item)
    state_xy = np.array([item[int(round(p))] for p in seed_pos])
    sc = slot_correspondence(
        anchors=anchors,
        stroke_starts=[0],
        corner_anchors=[],
        template_strokes=[stroke],
        items=[(0, item)],
        seed_pos=seed_pos,
        seed_item=seed_item,
        state_xy=state_xy,
    )
    assert not sc.complete
    assert not sc.covered[0]
    assert sc.covered[-1]
