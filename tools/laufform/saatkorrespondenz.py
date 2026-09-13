"""Saat-Korrespondenz: which chart anchor a Tintenpfad path vertex belongs to.

A Laufform row is an ANCHOR SET — one fixed anchor index per chart row,
medianised over the occurrences. The Tintenpfad decodes a BAHN, a pen path
with no anchors on it. Between the two sits exactly one piece of bookkeeping
the decoder already carries: every path vertex knows the SEED SAMPLE that
decoded it, every seed sample knows its composed draw item and its place
along that item's centerline, and the composed centerline is a sampling of
the chart row's own anchors. Walk that chain and an anchor index falls out
without anything being interpolated over the arc length of the ink — which is
the whole point of the author's decision A48 (2026-09-13, way 1 of
`docs/proposals/tintenfolger.md` §7.11).

The chain has four links, three of which are exact bookkeeping:

1. **anchor → template sample** (`anchor_sample_index`). `core.template`
   samples each sub-arc at `linspace(0, 1, k)` over the CHORD-LENGTH
   parameter, so an anchor's fractional sample index is a closed form, not a
   search.
2. **template sample → composed item point** (`identify_slice`). This is the
   one link `core/compose.py` does NOT record: it trims the coupling ends,
   prepends crest and overlap vertices, leans and scales — and hands on a
   centerline with no sample index. So the link is not estimated here, it is
   PROVEN: the item must be an exact affine image of a contiguous piece of
   the template's sample array (residual below `SLICE_TOL`). Anything the
   proof does not reach is reported as uncovered, never filled in.
3. **composed item point → seed sample** (`Seed.item` / `Seed.pos`, the exact
   inverse of the follower's own arc-length resampling of that item).
4. **seed sample → place on the ink** (`correspondence["state_xy"]`): the
   strand pixel the decoder's state for that sample boarded — the decode's
   own statement, and a point of the delivered rail. A sample left on the
   paper state has no place, and says so.

An anchor whose two bracketing seed samples did not both decode onto ink is
uncovered, and an occurrence with one uncovered anchor is no occurrence. That
is deliberate: a partial anchor set silently redefines what a Laufform
measures, and the redefinition would be invisible because every number would
still look plausible.

Measurement layer: pure geometry, no DB, no `core/` edits.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.template import build_sample_plan


# A proven slice matches to the last bits of the double the composition wrote;
# the nearest WRONG offset of the same stroke sits five orders of magnitude
# above it, so the tolerance separates a proof from a near miss rather than
# trading them off.
SLICE_TOL = 1e-6
# Below this many overlapping points an affine fit describes noise, not a slice.
MIN_OVERLAP = 24
# Half-width of the LOCAL proof window. The proof is local on purpose: not
# every deformation `core/compose.py` applies is one affine over the whole
# stroke — the ascender lean is a shear of the part ABOVE the midband only, so
# a `d` has two affine pieces and no single one. A local window asks the
# question the correspondence actually needs (is THIS point the template
# sample this index says it is) and stays free of any compose rule, which a
# richer global model would have to hard-code and then keep in sync.
PROOF_HALF = 12
# A candidate shift has to overlap at least this share of the item.
MIN_OVERLAP_SHARE = 0.6


@dataclass(frozen=True)
class SliceMatch:
    """One composed item identified as a piece of one template stroke.

    `shift` maps item index → template sample index (`template = item + shift`),
    valid over the item indices where `proven` is True; `resid` is the worst
    residual over those, in template units.
    """

    stroke: int
    shift: int
    proven: np.ndarray  # (len(item),) bool
    resid: float


@dataclass(frozen=True)
class SlotCorrespondence:
    """One slot's chart anchors as the decoded path placed them, in crop px."""

    anchors_px: np.ndarray  # (N, 2), NaN where uncovered
    covered: np.ndarray  # (N,) bool
    slice_resid: float  # worst residual of the slice proofs used
    seed_span: float  # worst bracketing seed-sample distance, in samples

    @property
    def complete(self) -> bool:
        return bool(self.covered.all()) and len(self.covered) > 0


def anchor_sample_index(
    anchors: np.ndarray, stroke_starts: list[int] | None, corner_anchors: list[int] | None, n: int = 240
) -> dict[int, tuple[int, float]]:
    """Per chart anchor: `(pen stroke, fractional sample index in that stroke)`.

    Mirrors `core.template.sample_with_sample_plan` exactly — including its
    dropping of a coincident anchor pair, which shifts every later chord
    parameter of that sub-arc.
    """
    anchors = np.asarray(anchors, dtype=float)
    plan = build_sample_plan(anchors, stroke_starts, corner_anchors, n)
    drops = np.asarray(sorted(plan.drop_rows), dtype=float)
    starts = list(plan.sample_starts)

    out: dict[int, tuple[int, float]] = {}
    pre = 0
    for (a, b), k in zip(plan.slices, plan.alloc, strict=True):
        if b - a >= 2:
            seg = anchors[a:b]
            chord = np.hypot(*np.diff(seg, axis=0).T)
            t = np.concatenate([[0.0], np.cumsum(chord)])
            if t[-1] > 0:
                keep = np.concatenate([[True], chord > 0])
                # A dropped anchor shares its predecessor's parameter: it IS
                # the same point, so it is the same place on the curve.
                t = np.where(keep, t, np.nan)
                t = _forward_fill(t)
                t = t / t[-1]
                rows = pre + t * (k - 1)
            else:
                rows = np.full(b - a, float(pre))
        else:
            rows = np.full(max(b - a, 1), float(pre))
        for p, row in zip(range(a, b), rows, strict=False):
            if p in out:
                # A corner anchor belongs to two sub-arcs; the earlier one's
                # last sample is the row that SURVIVES the duplicate drop.
                continue
            post = row - float(np.searchsorted(drops, row, side="left"))
            s = max(0, int(np.searchsorted(starts, post, side="right")) - 1)
            out[p] = (s, post - starts[s])
        pre += k
    return out


def _forward_fill(values: np.ndarray) -> np.ndarray:
    out = values.copy()
    last = 0.0
    for i, v in enumerate(out):
        if np.isnan(v):
            out[i] = last
        else:
            last = v
    return out


def _affine_residuals(item: np.ndarray, tmpl_seg: np.ndarray) -> np.ndarray:
    design = np.column_stack([tmpl_seg, np.ones(len(tmpl_seg))])
    sol, *_ = np.linalg.lstsq(design, item, rcond=None)
    return np.linalg.norm(design @ sol - item, axis=1)


def identify_slice(item: np.ndarray, strokes: list[np.ndarray]) -> SliceMatch | None:
    """Prove the composed item to be a contiguous piece of one template stroke.

    The shift is ranked by `_shift_score` — the same LOCAL question the proof
    asks, sampled at a handful of places — and the best few are then proven
    point by point. The shift that proves the most points wins; `None` means no
    stroke carried a proof at all, and the caller then has no correspondence
    for that item and says so.
    """
    item = np.asarray(item, dtype=float).reshape(-1, 2)
    # A shift whose overlap is a short piece of a nearly straight stroke fits
    # ANY affine (the design matrix goes rank-deficient) and would otherwise
    # crowd the real shift out of the ranking — so a candidate has to explain
    # most of the item, not a corner of it.
    need = max(MIN_OVERLAP, int(MIN_OVERLAP_SHARE * len(item)))
    candidates: list[tuple[float, int, int]] = []
    for si, tmpl in enumerate(strokes):
        tmpl = np.asarray(tmpl, dtype=float).reshape(-1, 2)
        for shift in range(-(len(item) - need), len(tmpl) - need + 1):
            lo, hi = max(0, -shift), min(len(item), len(tmpl) - shift)
            if hi - lo < need:
                continue
            candidates.append((_shift_score(item, tmpl, shift, lo, hi), si, shift))
    # The proof is expensive, the ranking is not: prove only the shifts that
    # could plausibly be the right one.
    best: SliceMatch | None = None
    for _score, si, shift in sorted(candidates, key=lambda c: c[0])[:4]:
        proven, resid = _local_proof(item, np.asarray(strokes[si], dtype=float).reshape(-1, 2), shift)
        if not proven.any():
            continue
        if best is None or proven.sum() > best.proven.sum():
            best = SliceMatch(stroke=si, shift=shift, proven=proven, resid=resid)
    return best


def _shift_score(item: np.ndarray, tmpl: np.ndarray, shift: int, lo: int, hi: int) -> float:
    """How well a shift holds up LOCALLY: the median worst residual over a few
    proof-sized windows spread across the overlap.

    One affine over the whole overlap would be the cheaper ranking and is the
    wrong question: where `core/compose.py` deformed the stroke piecewise, the
    TRUE shift scores badly on it while a partial alignment of the undeformed
    piece scores well — and the ranking would hand the proof a shift that then
    proves a piece of it and places the anchors somewhere else entirely.
    """
    width = 2 * PROOF_HALF + 1
    if hi - lo < width:
        return float("inf")
    starts = np.unique(np.linspace(lo, hi - width, 5).astype(int))
    worst = [float(_affine_residuals(item[a : a + width], tmpl[a + shift : a + width + shift]).max()) for a in starts]
    return float(np.median(worst))


def _local_proof(item: np.ndarray, tmpl: np.ndarray, shift: int) -> tuple[np.ndarray, float]:
    """Per item point: is it the template sample `shift` says it is?

    The verdict is read from ONE affine fitted to the point's own
    `PROOF_HALF` neighbourhood, so a stroke `core/compose.py` deformed
    piecewise proves everywhere except across the seam of the pieces.
    """
    proven = np.zeros(len(item), dtype=bool)
    worst = 0.0
    lo, hi = max(0, -shift), min(len(item), len(tmpl) - shift)
    width = 2 * PROOF_HALF + 1
    if hi - lo < max(MIN_OVERLAP, width):
        return proven, worst
    for i in range(lo, hi):
        # Clamped rather than skipped at the item's ends: a point near the end
        # is proven by its neighbours on one side, and the ends are where the
        # letter meets its joins — the half of the row this arm is about.
        a = min(max(lo, i - PROOF_HALF), hi - width)
        b = a + width
        resid = _affine_residuals(item[a:b], tmpl[a + shift : b + shift])
        if resid[i - a] <= SLICE_TOL:
            proven[i] = True
            worst = max(worst, float(resid[i - a]))
    return proven, worst


def slot_correspondence(
    *,
    anchors: np.ndarray,
    stroke_starts: list[int] | None,
    corner_anchors: list[int] | None,
    template_strokes: list[np.ndarray],
    items: list[tuple[int, np.ndarray]],
    seed_pos: np.ndarray,
    seed_item: np.ndarray,
    state_xy: np.ndarray,
    n: int = 240,
) -> SlotCorrespondence:
    """One slot's anchors, read off the decoded path through the seed.

    `items` are this slot's composed draw items as `(item index in the seed's
    item space, centerline in composed units)`; `state_xy` is the follower's
    per-sample decode (`correspondence["state_xy"]`, NaN on the paper state).
    """
    anchors = np.asarray(anchors, dtype=float)
    by_anchor = anchor_sample_index(anchors, stroke_starts, corner_anchors, n)
    out = np.full((len(anchors), 2), np.nan)
    covered = np.zeros(len(anchors), dtype=bool)
    worst_resid = 0.0
    worst_span = 0.0

    for m, centerline in items:
        match = identify_slice(centerline, template_strokes)
        if match is None:
            continue
        worst_resid = max(worst_resid, match.resid)
        in_item = np.flatnonzero(seed_item == m)
        if len(in_item) < 2:
            continue
        pos = seed_pos[in_item]
        for j, (stroke, row) in by_anchor.items():
            if covered[j] or stroke != match.stroke:
                continue
            target = row - match.shift
            t0, t1 = int(np.floor(target)), int(np.ceil(target))
            if t0 < 0 or t1 >= len(match.proven) or not (match.proven[t0] and match.proven[t1]):
                continue
            place = _read_at(target, pos, in_item, state_xy)
            if place is None:
                continue
            xy, span = place
            out[j] = xy
            covered[j] = True
            worst_span = max(worst_span, span)
    return SlotCorrespondence(anchors_px=out, covered=covered, slice_resid=worst_resid, seed_span=worst_span)


def _read_at(
    target: float, pos: np.ndarray, sample_ids: np.ndarray, state_xy: np.ndarray
) -> tuple[np.ndarray, float] | None:
    """The decoded place at a fractional item index, read between two ADJACENT
    seed samples — a linear read over at most one seed step (0.03 xh), never a
    redistribution over the letter's arc."""
    if target < pos[0] - 1e-9 or target > pos[-1] + 1e-9:
        # Outside the seed's own range there is no bracketing pair, and
        # clamping to the nearest end would be an extrapolation wearing a
        # reading's clothes.
        return None
    hi = int(np.searchsorted(pos, target, side="left"))
    hi = max(1, min(hi, len(pos) - 1))
    k0, k1 = int(sample_ids[hi - 1]), int(sample_ids[hi])
    a, b = state_xy[k0], state_xy[k1]
    if k1 != k0 + 1 or not np.isfinite(a).all() or not np.isfinite(b).all():
        return None
    p0, p1 = pos[hi - 1], pos[hi]
    w = 0.0 if p1 <= p0 else float(np.clip((target - p0) / (p1 - p0), 0.0, 1.0))
    return a + w * (b - a), float(abs(k1 - k0))
