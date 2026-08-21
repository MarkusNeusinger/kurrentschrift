"""K-C, the ink-evidence mask (`tools.pairlab.ink_evidence`).

Pins the two things the measure promises: the darkness rule separates a
paper-grey blob from ink-dark components (and keeps the word and its marks),
and every path that does not drop anything hands the SAME case object back —
the identity the byte-identical default rests on.
"""

from __future__ import annotations

import numpy as np
import pytest

from core.extract import skeleton_and_width
from tools.laufform.harvest import HarvestOptions
from tools.pairlab.follow import FollowWeights
from tools.pairlab.ink_evidence import (
    INK_EVIDENCE_PAPER_FRACTION,
    InkEvidenceOptions,
    classify_components,
    ink_evidence_case,
)
from tools.wordlab.cases import WordCase


def _crop(*, speck_grey: float | None = 0.82, dot_grey: float | None = 0.32) -> np.ndarray:
    """A grey picture in [0, 1]: a dark stroke, optionally a dark i-dot and a faint blob."""
    crop = np.full((60, 140), 0.95)
    crop[30:36, 10:120] = 0.30  # the word body — 6 px thick, 110 px long
    if dot_grey is not None:
        crop[12:18, 96:103] = dot_grey  # a dark mark 12 px above the body
    if speck_grey is not None:
        crop[8:14, 40:47] = speck_grey  # a paper-grey blob, same size, same height band
    return crop


def _case(crop: np.ndarray | None) -> WordCase:
    if crop is None:
        return WordCase(
            id="live",
            word="x",
            kind="word",
            slots=[],
            templates={},
            style_ratio=[1, 1, 1],
            width_resolver="constant",
            nib_units=0.07,
        )
    mask = crop < 0.9
    skel, width_map = skeleton_and_width(mask)
    return WordCase(
        id="synthetic",
        word="x",
        kind="word",
        slots=[],
        templates={},
        style_ratio=[1, 1, 1],
        width_resolver="constant",
        nib_units=0.07,
        crop=crop,
        skel=skel,
        width_map=width_map,
    )


def test_the_darkness_rule_drops_the_speck_and_keeps_the_mark() -> None:
    case = _case(_crop())
    report = classify_components(case.skel, case.width_map, case.crop)
    assert report.applied and report.n_components == 3
    by_y = sorted(report.components, key=lambda c: c.centroid_px[0])
    speck, dot = by_y
    assert speck.dropped and speck.rel > 0.7
    assert not dot.dropped and dot.rel < 0.1
    assert report.main_area_px == 6 * 110


def test_the_masked_case_loses_exactly_the_speck_pixels() -> None:
    case = _case(_crop())
    masked, report = ink_evidence_case(case, InkEvidenceOptions())
    assert masked is not case and report is not None and len(report.dropped) == 1
    # the speck's pixels are gone from both arrays, nothing else moved
    assert not masked.skel[8:14, 40:47].any() and not (masked.width_map[8:14, 40:47] > 0).any()
    assert masked.skel.sum() == case.skel.sum() - report.dropped[0].skel_px
    assert ((masked.width_map > 0).sum()) == (case.width_map > 0).sum() - report.dropped[0].area_px
    assert np.array_equal(masked.skel[30:36], case.skel[30:36])  # the word body untouched
    assert (masked.width_map[12:18, 96:103] > 0).any()  # the mark survives
    assert masked.crop is case.crop  # the picture is never touched
    assert report.as_dict()["n_dropped"] == 1


@pytest.mark.parametrize("fraction", [0.4, 0.5, 0.7])
def test_the_boundary_is_a_gap_not_a_knob(fraction: float) -> None:
    """Any fraction inside the measured gap selects the same components."""
    case = _case(_crop())
    _, report = ink_evidence_case(case, InkEvidenceOptions(paper_fraction=fraction))
    assert [c.dropped for c in sorted(report.components, key=lambda c: c.centroid_px[0])] == [True, False]


def test_off_is_the_identity() -> None:
    case = _case(_crop())
    same, report = ink_evidence_case(case, None)
    assert same is case and report is None


def test_nothing_foreign_is_the_identity_too() -> None:
    case = _case(_crop(speck_grey=None))
    same, report = ink_evidence_case(case, InkEvidenceOptions())
    assert same is case and report is not None and report.applied and not report.dropped


def test_a_live_case_and_a_flat_picture_pass_through() -> None:
    live = _case(None)
    same, report = ink_evidence_case(live, InkEvidenceOptions())
    assert same is live and report is not None and not report.applied and report.reason == "no specimen"
    # ink and paper at the same grey: no darkness scale, so nothing is judged
    flat_mask = np.zeros((20, 40), dtype=bool)
    flat_mask[4:8, 5:30] = True
    flat_mask[12:15, 33:37] = True
    skel, width_map = skeleton_and_width(flat_mask)
    flat = _case(_crop(speck_grey=None, dot_grey=None))
    flat.crop = np.full((20, 40), 0.5)
    flat.skel, flat.width_map = skel, width_map
    same, report = ink_evidence_case(flat, InkEvidenceOptions())
    assert same is flat and not report.applied and "contrast" in report.reason


def test_the_measure_defaults_on_everywhere() -> None:
    """Kette v4 (§14 `aug21`): the mask is the default on follower and harvest alike."""
    assert FollowWeights().ink_evidence is True
    assert FollowWeights().ink_evidence_paper_fraction == INK_EVIDENCE_PAPER_FRACTION
    assert HarvestOptions().ink_evidence is True
