"""Pen deconvolution at a counter: the EVIDENCE the ink term reads, corrected.

Rescue path (4) of the R3 row in `tintenfolger.md` §7.9 — the one R3c
(`sep07`) raised from „offen" to „the promising way" — and the arm R4 of §14.

WHY THE EVIDENCE AND NOT THE TRACE. The follower's ink term is the distance
transform of the frozen mask's SKELETON (`chain._field_stack`:
`distance_transform_edt(~skel)`), so the skeleton is the attractor every
sample is pulled onto. Around a small counter that skeleton is not the pen
path: two pen capsules that pass within a couple of pixels of each other paint
one ribbon, and the medial axis of that ribbon hugs the hole more tightly than
either pass did. Measured over the 202 plate counters the pinch is
`(D0_skel − counter) / 2·w_pen` = 0.689 in the median (§14 „Laufform LF14",
the R4 indicator), i.e. the attractor asks for a loop about 0.06 xh narrower
than the hand wrote. R3 pushed the finished trace off the hole and broke its
smoothness; R3c priced the same condition inside the solve and could not break
a symmetric configuration, because the ink term itself sits on the lump axis at
a fused spot. **Both arms argued against the evidence. This one corrects it.**

THE CORRECTION, stated once. A Gleichzug pen of half width `w` paints the
Minkowski sum of its path with a disc of radius `w`, so a counter the plate
holds open proves that no pen sample came closer to it than `w`. The same
sentence read on the raster: **no skeleton pixel of a counter's neighbourhood
may lie closer to that counter than `w_pen`.** Every one that does is dropped,
and in its place goes the level set `w_pen + 0.5 px` of that counter's own
distance field, clipped to the ink and reaching only as far around the hole as
the dropped pixels did. The level set is a construction, not a fit: every point
of it lies one pen half width from the hole, which is where a pen that left the
hole open must have run, so the corrected loop carries the aperture
`counter + 2·w_pen` the catalogue expects. No fade length has to be chosen —
the SOLVER does the smoothing, which is exactly what R3 could not buy and R3c
bought for free.

WHY THE LUMP IS REAL AND THE RASTER IS NOT TO BLAME. The diagnostic of this
round settled that before the arm was built: the crop is an unscaled slice of
the committed plate (`export_fixtures.freeze_entry`), so the crops ARE the
plate's own 30-33 px per x-height; a global 50 % level set of the grey reads the
same counter as the frozen adaptive mask (median difference 0.0000 xh), and at
4x sub-pixel it reads a slightly SMALLER one (0.1118 against 0.1290 xh, half a
plate pixel across — the direction and the size the declared half-pixel
convention predicts, and the opposite of a hole the binarisation eats). The
medial-axis pinch survives the 4x reading almost unchanged (indicator +0.011).
The fusion is ink, not raster — so the honest correction is to take the pen out
of the evidence, not to look for a sharper picture.

THREE RULES, and each is a refusal rather than a knob:

* **Never invent ink.** The level set is clipped to the frozen mask, and what
  the clip cut away is counted (`band_clipped`). The plate's own ribbon reads
  locally thinner than a full pen at the tightest counters (#551's H0: half
  width 0.0667 against 0.0968), so this binds and has to be visible rather than
  quietly absorbed.
* **Never lose the loop.** If the corrected skeleton no longer encloses the
  counter, the whole correction of that counter is reverted. That is R3's
  `REFUSAL_CLOSURE_LOST` moved to the evidence, where it costs a loop and not a
  round — the granularity R3c's §14 entry names as its first conversion. The
  guard is re-read on every counter ACCEPTED so far, not only on the current
  one: two counters of one letter can sit within a pen width of each other,
  and a later drop set then reaches into an earlier one's arc.
* **Never widen what is already right.** A counter whose skeleton keeps its
  distance already carries the statement; nothing is dropped and nothing is
  painted, so the arm is inert exactly where it has nothing to say — and the
  radial shadow keeps that true ARC BY ARC on a large counter, not only
  counter by counter.

SCOPE is R3's and R3c's, unchanged, so this is a single-factor step against the
round it converts: catalogue loops (`tools/tracebench/kringel_catalogue.json`,
#556) with state `offen` and size class `klein` or `mittel`, matched to their
plate counter by #556's Slot-Lineal through `zweizuege.catalogue_targets` —
never a flat proximity search, which hands a loop the NEIGHBOUR's hole (#553).

Measurement layer only: no DB, no `core/` byte, no ruler. The bench's frozen
`ref_mask.png` / `ref_skel.npz` are untouched — the AIoU and every counter
still grade against ALL the ink, exactly as under the K-C ink-evidence mask
(`tools.pairlab.ink_evidence`), whose case-replacement shape this module
follows deliberately: one evidence for the seed windows, the solve fields and
the coverage targets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any

import numpy as np

from tools.pairlab.zweizuege import (
    MIN_COUNTER_PX,
    RASTER_HALF_PIXEL,
    ZweiZuegeOptions,
    catalogue_targets,
    plate_counters,
)
from tools.tracebench.kringel import PLATE_PEN_HALF_WIDTH_UNITS, SIZE_CLASSES, STATES, catalogue_source, load_catalogue


# R3's own two, and for R3's own reason (`counterfield.COUNTER_SIZE_CLASSES`):
# three quarters of a `gross` counter survives any pen, so a correction there
# moves evidence without moving a defect. `offen` and nothing else: `wechselnd`
# is a loop the PLATE closes in some occurrences and `punkt` has no aperture to
# hold, so correcting either would be the instrument overruling the evidence.
COUNTER_EVIDENCE_STATES = ("offen",)
COUNTER_EVIDENCE_SIZE_CLASSES = ("klein", "mittel")
COUNTER_EVIDENCE_SIZE_CLASSES_ALL = tuple(SIZE_CLASSES)

REFUSAL_NO_MASK = "no frozen ink mask on the case"
REFUSAL_NO_SKELETON = "no frozen skeleton on the case"
REFUSAL_FOREIGN_HAND = "the catalogue belongs to another hand"
REFUSAL_NO_TARGET = "no catalogue counter of this word is in scope"
REFUSAL_ALREADY_CLEAR = "the skeleton already keeps its distance from this counter"
REFUSAL_LOOP_LOST = "the correction opened the skeleton's own loop — reverted"
REFUSAL_NO_BAND = "the plate carries no ink at one pen half width from this counter"
REFUSAL_NOTHING_CORRECTED = "no in-scope counter of this word could be corrected"


@dataclass(frozen=True)
class CounterEvidenceOptions:
    """One configuration of the correction — frozen, stamped into every artefact.

    The two class tuples are checked rather than trusted, for
    `CounterFieldOptions`'s reason: `catalogue_targets` filters by MEMBERSHIP,
    so a misspelt `mitel` silently narrows the scope while the artefact still
    says the arm ran, and a measurement that quietly measures nothing is worse
    than one that fails.
    """

    half_width_units: float = PLATE_PEN_HALF_WIDTH_UNITS
    states: tuple[str, ...] = COUNTER_EVIDENCE_STATES
    size_classes: tuple[str, ...] = COUNTER_EVIDENCE_SIZE_CLASSES
    min_counter_px: int = MIN_COUNTER_PX

    def __post_init__(self) -> None:
        for name, given, known in (
            ("states", self.states, STATES),
            ("size_classes", self.size_classes, COUNTER_EVIDENCE_SIZE_CLASSES_ALL),
        ):
            if not given:
                raise ValueError(f"{name} must name at least one value; known: {', '.join(known)}")
            unknown = [v for v in given if v not in known]
            if unknown:
                raise ValueError(f"unknown {name} {', '.join(map(repr, unknown))}; known: {', '.join(known)}")


@dataclass
class CounterUnfold:
    """One catalogue loop of one occurrence, and what the correction did to it."""

    slot: int
    glyph: str | None
    loop: int
    size_class: str
    state: str
    counter_units: float | None = None  # the plate counter, the catalogue's way (2 · max EDT)
    target_d0_units: float | None = None  # counter + 2·w_pen — the aperture the corrected loop carries
    pixels_dropped: int = 0  # skeleton pixels that sat closer than w_pen to the counter
    pixels_added: int = 0  # pen-path pixels the counter's own level set put in their place
    band_clipped: int = 0  # level-set pixels the plate carries no ink for — the ribbon read thin
    reason: str = ""  # empty exactly when the loop was corrected

    @property
    def corrected(self) -> bool:
        return not self.reason

    def as_dict(self) -> dict[str, Any]:
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in asdict(self).items()}


@dataclass
class CounterEvidenceReport:
    """What the correction did to ONE word — always inspectable, never silent."""

    applied: bool
    options: dict[str, Any]
    target_px: float = 0.0
    pixels_dropped: int = 0
    pixels_added: int = 0
    band_clipped: int = 0
    # Connected components of the CORRECTED skeleton. A reading, not a gate: a
    # level set the ink clip or the radial shadow cut into can leave an island,
    # and an island in the attractor is something a reader has to be able to
    # see rather than infer.
    n_components: int = 0
    reason: str = ""  # why nothing was applied at all
    loops: list[CounterUnfold] = field(default_factory=list)

    @property
    def corrected(self) -> list[CounterUnfold]:
        return [lp for lp in self.loops if lp.corrected]

    def as_dict(self) -> dict[str, Any]:
        return {
            "applied": self.applied,
            "options": self.options,
            "target_px": round(float(self.target_px), 4),
            "pixels_dropped": self.pixels_dropped,
            "pixels_added": self.pixels_added,
            "band_clipped": self.band_clipped,
            "n_components": self.n_components,
            "n_corrected": len(self.corrected),
            "n_refused": len(self.loops) - len(self.corrected),
            "reason": self.reason,
            "loops": [lp.as_dict() for lp in self.loops],
        }


def _encloses(skel: np.ndarray, centre_px: tuple[float, float]) -> bool:
    """Does this skeleton still enclose the point? — the loop-survival guard.

    `plate_counters` labels the background 4-connected and drops every component
    that touches the border, which is precisely „is this point inside a closed
    curve of the set". The minimum area is 1: a one-pixel hole is still a loop,
    and the splinter floor of the catalogue is a statement about APERTURE, not
    about topology.
    """
    labels, holes = plate_counters(skel, min_px=1)
    if not holes:
        return False
    row = int(round(centre_px[1]))
    col = int(round(centre_px[0]))
    if not (0 <= row < labels.shape[0] and 0 <= col < labels.shape[1]):
        return False
    return int(labels[row, col]) in {h.label for h in holes}


def unfold_pen_at_counter(
    skel: np.ndarray, ink: np.ndarray, counter_mask: np.ndarray, *, target_px: float
) -> tuple[np.ndarray, int, int, int]:
    """Replace the skeleton's pinched arc at one counter by the pen's own level set.

    Pure raster geometry, so a synthetic annulus is a first-class caller.

    * **What goes.** Every skeleton pixel closer to the counter than
      `target_px` — each one is a pen position that would have inked the hole,
      so the plate itself says the pen was not there.
    * **What comes.** The level set `|φ − target_px| ≤ ½ px` of the counter's
      own distance field, clipped to the ink. Every point of it lies one pen
      half width from the hole, which is where a pen that left this hole open
      must have run, so the arc carries the aperture `counter + 2·w_pen` by
      construction rather than by fitting.
    * **How far it reaches.** Only into the RADIAL SHADOW of what went: a level
      set pixel is added exactly where some dropped pixel shares its nearest
      counter pixel. Where the skeleton already kept its distance the ink is
      thicker than one pen there, and painting a pen path into it would be the
      correction inventing a stroke rather than deconvolving one.

    An earlier version pushed each pinched pixel outward along its own ray. It
    is the same statement and it fails on the raster: the target arc is longer
    than the pinched one, so N pixels land on it with gaps, the loop falls open
    and the survival guard reverts every counter. Measured on `das`, `Zorn`,
    `muß-2`, `Galoppieren` and `der`: 0 of 13 counters survived the push, 13 of
    13 survive the level set. The level set is one connected arc by
    construction, which is why.

    Returns `(corrected skeleton, pixels dropped, pixels added, level-set pixels
    the plate carries no ink for)`.
    """
    from scipy.ndimage import distance_transform_edt  # noqa: PLC0415 — heavy import, few call sites

    counter = np.asarray(counter_mask, dtype=bool)
    skel = np.asarray(skel, dtype=bool)
    ink = np.asarray(ink, dtype=bool)
    phi, idx = distance_transform_edt(~counter, return_indices=True)
    hot = skel & (phi < target_px)
    if not hot.any():
        return skel, 0, 0, 0
    annulus = (phi >= target_px - RASTER_HALF_PIXEL) & (phi <= target_px + RASTER_HALF_PIXEL)
    nearest = idx[0] * skel.shape[1] + idx[1]
    shadow = np.isin(nearest, np.unique(nearest[hot]))
    wanted = annulus & shadow
    band = wanted & ink
    out = (skel & ~hot) | band
    return out, int(hot.sum()), int(band.sum()), int((wanted & ~ink).sum())


def unfold_case_evidence(
    *,
    skel: np.ndarray | None,
    mask: np.ndarray | None,
    composed_items: Any,
    catalogue: dict[str, list[dict[str, Any]]],
    xh_px: float,
    tx: float,
    ty: float,
    baseline_row: float,
    options: CounterEvidenceOptions | None = None,
) -> tuple[np.ndarray | None, CounterEvidenceReport]:
    """The corrected skeleton of ONE word, plus the reading that produced it.

    Pure geometry on the frozen mask, the frozen skeleton and the frozen
    catalogue — no case object, no fixture root, no DB.
    """
    from scipy.ndimage import distance_transform_edt  # noqa: PLC0415
    from scipy.ndimage import label as cc_label

    opts = options or CounterEvidenceOptions()
    stamp = {
        "half_width_units": opts.half_width_units,
        "states": list(opts.states),
        "size_classes": list(opts.size_classes),
        "min_counter_px": opts.min_counter_px,
    }
    if mask is None:
        return skel, CounterEvidenceReport(False, stamp, reason=REFUSAL_NO_MASK)
    if skel is None:
        return skel, CounterEvidenceReport(False, stamp, reason=REFUSAL_NO_SKELETON)
    ink = np.asarray(mask, dtype=bool)
    labels, counters = plate_counters(ink, min_px=opts.min_counter_px)
    targets, rows = catalogue_targets(
        composed_items,
        catalogue,
        counters,
        distance_transform_edt(ink),
        xh_px=xh_px,
        tx=tx,
        ty=ty,
        baseline_row=baseline_row,
        options=ZweiZuegeOptions(
            half_width_units=opts.half_width_units,
            states=tuple(opts.states),
            size_classes=tuple(opts.size_classes),
            min_counter_px=opts.min_counter_px,
        ),
    )
    unfolds = [
        CounterUnfold(
            slot=row.slot,
            glyph=row.glyph,
            loop=row.loop,
            size_class=row.size_class,
            state=row.state,
            counter_units=row.counter_units,
            target_d0_units=row.target_d0_units,
            reason=row.reason,
        )
        for row in rows
    ]
    by_key = {(u.slot, u.loop): u for u in unfolds}
    # The same declared half pixel as R3 and R3c, and for the same reason: a
    # distance transform measures centre to centre, so a hole's raster reading
    # is half a pixel generous on each side and the level the push aims at has
    # to be read the same generous way.
    target_px = float(opts.half_width_units) * float(xh_px) + RASTER_HALF_PIXEL
    report = CounterEvidenceReport(bool(targets), stamp, target_px=target_px, loops=unfolds)
    if not targets:
        report.reason = REFUSAL_NO_TARGET
        return skel, report
    out = np.asarray(skel, dtype=bool).copy()
    # The counters ACCEPTED so far, so the survival guard can be re-read on all
    # of them after every candidate. Two counters of one letter can lie within
    # a pen width of each other (`k`#1/#2, `t`#0/#1, `h`#0/#1 in the shipped
    # catalogue), and the later one's drop set then reaches into the arc the
    # earlier one added — checking only the current counter would let an
    # accepted loop fall open again and still be reported as corrected.
    accepted: list[tuple[float, float]] = []
    for counter, entry, _centre in targets:
        unfold = by_key.get((entry.slot, entry.loop))
        if unfold is None:
            continue
        counter_mask = labels == counter.label
        candidate, dropped, added, clipped = unfold_pen_at_counter(out, ink, counter_mask, target_px=target_px)
        if dropped == 0:
            unfold.reason = REFUSAL_ALREADY_CLEAR
            continue
        if added == 0:
            unfold.reason = REFUSAL_NO_BAND
            continue
        centre = (counter.cx, counter.cy)
        if not all(_encloses(candidate, seen) for seen in [centre, *accepted]):
            unfold.reason = REFUSAL_LOOP_LOST
            continue
        out = candidate
        accepted.append(centre)
        unfold.pixels_dropped = dropped
        unfold.pixels_added = added
        unfold.band_clipped = clipped
        report.pixels_dropped += dropped
        report.pixels_added += added
        report.band_clipped += clipped
    if report.pixels_added == 0:
        report.applied = False
        # Every in-scope loop said its own reason above; the word-level one only
        # names the sum, so an artefact can be read without the loop list — and
        # it never restates one loop's reason as if it were the word's.
        report.reason = REFUSAL_NOTHING_CORRECTED
        return skel, report
    _components, n_components = cc_label(out, structure=np.ones((3, 3), dtype=bool))
    report.n_components = int(n_components)
    return out, report


def counter_evidence_case(
    case: Any, result: Any, options: CounterEvidenceOptions | None = None
) -> tuple[Any, CounterEvidenceReport | None]:
    """The case with the counters' pen taken out of its skeleton, plus the report.

    `options=None` means the arm is OFF: the case comes back untouched and the
    report is None — the identity the default path relies on, exactly as in
    `ink_evidence.ink_evidence_case`. With the arm on and nothing to correct the
    case object is ALSO returned as is (not a copy), so „applied but pushed
    nothing" is byte-identical too.

    Two refusals live here rather than in the geometry, as in
    `zweizuege.correct_case_strokes` and `counterfield.counter_field_for_case`:
    a catalogue that cannot be read, and a catalogue read off ANOTHER hand. The
    Kringel catalogue is one hand with one pen. Neither costs the caller its
    run; both cost the correction and say why.
    """
    if options is None:
        return case, None
    # Two separate refusals, because they mean different things to a reader: a
    # live case has neither, a case whose skeleton failed to load has only one.
    if getattr(case, "mask", None) is None:
        return case, CounterEvidenceReport(False, {}, reason=REFUSAL_NO_MASK)
    if case.skel is None:
        return case, CounterEvidenceReport(False, {}, reason=REFUSAL_NO_SKELETON)
    try:
        catalogue = load_catalogue()
        source = catalogue_source()
    except (OSError, ValueError) as exc:  # noqa: BLE001 — a missing catalogue is a refusal, not a crash
        return case, CounterEvidenceReport(False, {}, reason=f"catalogue unavailable ({type(exc).__name__}: {exc})")
    measured_on = str((source.get("measured_on") or [{}])[0].get("name", ""))
    origin = str(getattr(case, "origin", "") or "").split(":", 1)[-1]
    if measured_on != origin:
        return case, CounterEvidenceReport(
            False, {}, reason=f"{REFUSAL_FOREIGN_HAND}: catalogue on {measured_on or '?'}, case from {origin or '?'}"
        )
    skel, report = unfold_case_evidence(
        skel=case.skel,
        mask=case.mask,
        composed_items=result.composed["items"],
        catalogue=catalogue,
        xh_px=float(result.xh_px),
        tx=float(result.registration["tx"]),
        ty=float(result.registration["ty"]),
        baseline_row=float(result.baseline_row),
        options=options,
    )
    if skel is None or not report.applied:
        return case, report
    return replace(case, skel=np.asarray(skel, dtype=bool)), report
