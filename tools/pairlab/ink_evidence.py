"""The ink-evidence mask: which ink components a word fit is allowed to see.

Measure K-C of the Tintenfolger campaign (`docs/reference/messjournal.md`
§14 `aug20`, the author's "Flecken" find). The chain fit and the follower read
the crop's ink at ONE place each (`tools.pairlab.chain._prepare_fields` via the
case's `skel`/`width_map`), and they read ALL of it: every connected component
of the frozen mask is a distance-field attractor AND a coverage target, so a
paper speck, a show-through fragment of the sheet's reverse, or a neighbouring
letter's diacritic pulls the nearest fitted sample toward itself. The autopsy
of 2026-08-20 measured exactly that: zwei's w-foot needle ends 0.04 xh inside
a 36-px blob, die-2's V leaves the d-loop toward the i-dot's basin, three of
Galoppieren's four excursions terminate on show-through.

What separates foreign ink from the word's own, measured over all 90 non-main
components of the 63 word fixtures: DARKNESS. A real component (an i-dot, a
u-bow, a broken-off stroke fragment) is as dark as the word body; a speck or
a show-through fragment is paper-grey. On the scale `rel = (median grey of the
component − median grey of the main ink) / (median paper grey − median grey
of the main ink)` the 46 real components lie at 0.01–0.38 and the 44 foreign
ones at 0.74–0.92 — a gap of 0.36 with nothing in it.
`INK_EVIDENCE_PAPER_FRACTION = 0.5` (`InkEvidenceOptions.paper_fraction`)
sits in the middle of that gap; any value in (0.38, 0.74) selects the same
components. The rule is therefore NOT a knob to tune but a measured class
boundary, and it needs no composition, no size floor and no hand reference.

Two invariants the helper keeps:

* the largest component (by pixel count) is the word and is always kept, so
  a faded word can never mask itself away;
* with nothing to drop — or with the measure off — the caller gets the very
  same `WordCase` object back (identity, not a copy), which is what makes the
  default byte-identical to before the measure existed.

The bench's own ruler is untouched: `ref_mask.png`/`ref_skel.npz` stay frozen,
the AIoU and every counter still grade against ALL ink. Only what the FIT is
allowed to be pulled by changes (`docs/reference/qualitaetsmetrik.md` §1:
"die Binarisierung ist die Torpfosten" — the goalposts do not move; the
follower merely stops chasing ink that is not the word's).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np
from scipy.ndimage import label as label_regions


# The class boundary on the `rel` scale (see the module docstring): a non-main
# component whose median grey lies MORE than this fraction of the way from
# the main ink toward the paper is foreign. Measured gap: real ≤ 0.38,
# foreign ≥ 0.74 over 90 components / 63 words (2026-08-20).
INK_EVIDENCE_PAPER_FRACTION = 0.5

# Below this ink-to-paper contrast (on the [0, 1] grey scale) the darkness
# scale is meaningless and the helper keeps everything rather than guess.
MIN_CONTRAST = 0.05

# 8-connectivity, the same structure `tools.pairlab.marks.ink_clusters` uses —
# a diagonal pixel step must not split one blob into two.
_STRUCTURE = np.ones((3, 3), dtype=bool)


@dataclass(frozen=True)
class InkEvidenceOptions:
    """The measure's one parameter, frozen like every other pool payload."""

    paper_fraction: float = INK_EVIDENCE_PAPER_FRACTION


@dataclass
class InkComponent:
    """One non-main component of the mask and how the rule judged it."""

    label: int
    area_px: int  # mask pixels (the component's ink area)
    skel_px: int  # skeleton pixels (what the fit would have been pulled by)
    centroid_px: tuple[float, float]  # crop pixels (x, y)
    grey_median: float  # [0, 1], 1 = white
    rel: float  # position between main ink (0) and paper (1)
    dropped: bool


@dataclass
class InkEvidenceReport:
    """What the mask did to one case — always inspectable, never silent."""

    applied: bool
    paper_fraction: float
    n_components: int
    main_area_px: int
    ink_grey_median: float
    paper_grey_median: float
    components: list[InkComponent] = field(default_factory=list)
    reason: str = ""  # why nothing was applied (contrast, missing crop, …)
    # The component label image the verdicts refer to — what the masking step
    # erases by. Carried on the report so the labelling runs once; never
    # serialised (`as_dict` lists the fields it exports explicitly).
    labels: np.ndarray | None = field(default=None, repr=False, compare=False)

    @property
    def dropped(self) -> list[InkComponent]:
        return [c for c in self.components if c.dropped]

    def as_dict(self) -> dict[str, Any]:
        return {
            "applied": self.applied,
            "paper_fraction": self.paper_fraction,
            "n_components": self.n_components,
            "main_area_px": self.main_area_px,
            "ink_grey_median": round(self.ink_grey_median, 4),
            "paper_grey_median": round(self.paper_grey_median, 4),
            "n_dropped": len(self.dropped),
            "dropped_skel_px": int(sum(c.skel_px for c in self.dropped)),
            "reason": self.reason,
            "components": [
                {
                    "area_px": c.area_px,
                    "skel_px": c.skel_px,
                    "centroid_px": [round(c.centroid_px[0], 1), round(c.centroid_px[1], 1)],
                    "grey_median": round(c.grey_median, 4),
                    "rel": round(c.rel, 3),
                    "dropped": c.dropped,
                }
                for c in self.components
            ],
        }


def classify_components(
    skel: np.ndarray, width_map: np.ndarray, crop: np.ndarray, *, paper_fraction: float = INK_EVIDENCE_PAPER_FRACTION
) -> InkEvidenceReport:
    """Judge every non-main component of `width_map > 0` by its darkness.

    `width_map > 0` IS the frozen binarised mask (the exporter's
    `distance_transform_edt(mask)` is positive exactly on mask pixels), so the
    components labelled here are the ones `ref_mask.png` holds — no new file
    read, no re-binarisation. `crop` is the grey picture in [0, 1] (1 = paper).
    """
    mask = np.asarray(width_map) > 0
    skel = np.asarray(skel, dtype=bool)
    crop = np.asarray(crop, dtype=float)
    if mask.shape != crop.shape or mask.shape != skel.shape:
        raise ValueError("skel, width_map and crop must share one shape")
    labels, count = label_regions(mask, structure=_STRUCTURE)
    if count == 0:
        return InkEvidenceReport(False, paper_fraction, 0, 0, 0.0, 1.0, reason="no ink")
    areas = np.bincount(labels.ravel(), minlength=count + 1)[1:]
    main = int(np.argmax(areas)) + 1
    ink_med = float(np.median(crop[labels == main]))
    paper = ~mask
    paper_med = float(np.median(crop[paper])) if paper.any() else 1.0
    contrast = paper_med - ink_med
    report = InkEvidenceReport(True, paper_fraction, int(count), int(areas[main - 1]), ink_med, paper_med)
    if contrast < MIN_CONTRAST:
        report.applied = False
        report.reason = f"contrast {contrast:.3f} below {MIN_CONTRAST}"
        return report
    rows, cols = np.nonzero(labels)
    lab = labels[rows, cols]
    sx = np.bincount(lab, weights=cols.astype(float), minlength=count + 1)[1:]
    sy = np.bincount(lab, weights=rows.astype(float), minlength=count + 1)[1:]
    skel_counts = np.bincount(labels[skel].ravel(), minlength=count + 1)[1:]
    for k in range(1, count + 1):
        if k == main:
            continue
        sel = labels == k
        g = float(np.median(crop[sel]))
        rel = (g - ink_med) / contrast
        report.components.append(
            InkComponent(
                label=k,
                area_px=int(areas[k - 1]),
                skel_px=int(skel_counts[k - 1]),
                centroid_px=(float(sx[k - 1] / areas[k - 1]), float(sy[k - 1] / areas[k - 1])),
                grey_median=g,
                rel=float(rel),
                dropped=bool(rel > paper_fraction),
            )
        )
    report.labels = labels
    return report


def ink_evidence_case(case: Any, options: InkEvidenceOptions | None = None) -> tuple[Any, InkEvidenceReport | None]:
    """The case with foreign ink removed from `skel` and `width_map`, plus the report.

    `options=None` means the measure is OFF: the case comes back untouched and
    the report is None — the identity every default path relies on. With the
    measure on and nothing foreign in the crop the case object is ALSO returned
    as is (not a copy), so "applied but dropped nothing" is byte-identical too.
    A case without a specimen (a live case: no crop, no skeleton) is returned
    untouched with a report that says why.
    """
    if options is None:
        return case, None
    if case.skel is None or case.width_map is None or case.crop is None:
        return case, InkEvidenceReport(False, options.paper_fraction, 0, 0, 0.0, 1.0, reason="no specimen")
    report = classify_components(case.skel, case.width_map, case.crop, paper_fraction=options.paper_fraction)
    dropped = report.dropped
    if not report.applied or not dropped or report.labels is None:
        return case, report
    drop = np.isin(report.labels, [c.label for c in dropped])
    skel = np.asarray(case.skel, dtype=bool) & ~drop
    width_map = np.where(drop, 0, np.asarray(case.width_map)).astype(np.asarray(case.width_map).dtype)
    return replace(case, skel=skel, width_map=width_map), report
