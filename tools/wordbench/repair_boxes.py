"""Repair committed word/pair rects that CLIP their own ink.

The rects in `words.json` were cut ink-tight with a 3 px pad
(`propose_boxes.py`, BOX_PAD_PX). That pad is measured on the DESPECKLED mask,
and a Sütterlin diacritic — the i-Strich, the u-Bogen — is a thin, faint mark
that can fall under the despeckle floor or land right on the border. The result
is a crop whose word is missing its i-dot or whose last letter is sliced: not a
specimen anyone can trace by hand, and a reference the bench measures against a
letter that is not fully there.

This tool re-derives the rect of exactly those specimens from the RAW binarised
page (no despeckle, so the faint marks count), and leaves every other rect byte
for byte as committed. Which ink is the word's OWN is the whole question, and
this line's own lineature answers most of it:

  * ink outside the writing zone (±1.35 xh around Mittellinie/Grundlinie)
    belongs to a neighbouring line, however deep it dips into the rect — a
    descender from above is mostly INSIDE and would fool a majority test;
  * a component with the majority of its pixels inside the rect is the word's;
    a SMALL one (a diacritic) is the word's even when it lies mostly or
    entirely outside — that is precisely the cut-off i-Strich and the sliced
    u-Bogen this tool exists for;
  * punctuation hangs entirely below the Mittellinie and never counts: the
    stored `word` carries letters only, and every right-edge candidate of the
    first pass was a comma;
  * a pale candidate that is not within INK_DARKNESS_TOL of the word's own
    stroke is bleed-through or foxing;
  * anything an `exclude` rect already covers is foreign ink by the sidecar's
    own testimony (same component-wise rule the metric uses).

The repaired rect is that ink's bbox plus `--pad`, clamped to the plate and to
the midpoint of the gap to any neighbouring specimen — a crop must never eat
its neighbour's word.

The `exclude` rects move with it, in both directions:

  * ink the GROWTH newly encloses that is not the word's own gets one — the
    comma beside `regieren`'s last letter, the case the sidecar's own note
    calls "punctuation overlapping a box edge";
  * one that now hides only the word's own ink loses its job and is dropped:
    `zum`'s was anchored to the old top edge, and over the repaired crop it
    painted a white block into clean paper. An exclude still covering foreign
    ink always stays, even where it grazes the word — that is a hand-placed
    judgement about a neighbour, not this tool's to overrule.

WHAT ELSE MOVES WITH A RECT (do not skip):
  * `baseline_y`/`midband_y` are PAGE coordinates and stay valid unchanged.
  * Stored word traces register in CROP-local pixels
    (`measurements.registration_px`), so a moved `x0`/`y0` shifts them out of
    place. `tools/wordbench/shift_registrations.py --baseline <old words.json>`
    applies the correction through the admin API; it derives the delta from the
    two sidecar VERSIONS itself, so no shift list travels between the two tools
    and there is nothing to keep in step. Skipping it leaves every trace of a
    repaired specimen mis-registered — vertically that surfaces as the stale
    frame badge and drops the row from the bench, horizontally nothing catches
    it at all.
  * The wordbench fixture roots freeze these rects. A repaired plate needs a
    fixture re-export and a dated re-baseline entry in `qualitaetsmetrik.md`
    §15 — the ruler changed, and silently comparing across it is the one thing
    the frozen-reference rule forbids.

Usage:
    uv run python -m tools.wordbench.repair_boxes --report
    uv run python -m tools.wordbench.repair_boxes --sheets temp/repair

    # keep the pre-repair sidecar: the trace correction is measured against it
    git show origin/main:data/sources/suetterlin-1922/words.json > temp/old.json
    uv run python -m tools.wordbench.repair_boxes --apply
    uv run python -m tools.wordbench.shift_registrations --baseline temp/old.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import find_objects
from scipy.ndimage import label as cc_label

from core.extract import binarize_adaptive
from core.word_metric import DESPECKLE_MIN_AREA_PX, EXCLUDE_COMPONENT_FRAC
from tools.wordbench.export_fixtures import REPO_ROOT, load_page


DEFAULT_SOURCE_ID = "suetterlin-1922"

# Clearance the repaired rect leaves around the word's own ink. Twice the
# proposer's 3 px: the whole failure mode is a mark that ends up ON the border,
# and a pad that only just clears the ink reproduces it at the next re-cut.
PAD_PX = 6

# A side is repaired when its clearance falls below this — the plate's own
# standard, `propose_boxes.BOX_PAD_PX`. Measured over the committed sidecar,
# 169 of 202 specimens sit at exactly that 3 px and are left untouched; this
# tool lifts only what fell BELOW the standard, because every rect it leaves
# alone is a crop, a fixture and a trace registration it does not disturb.
MIN_CLEARANCE_PX = 3

# How far beyond an edge the word's own ink may reach, in x-heights of THIS
# specimen's own lineature rather than a fixed pixel count — the two plates
# differ in scale, and the sidecar measures the lineature per entry anyway.
# An ascender or a floating diacritic tops out around 1.3 xh above the
# Mittellinie; a descender from the line above starts higher still, which is
# what separates "my i-dot" from "the line above".
ASCENDER_XH = 1.35
DESCENDER_XH = 1.35

# Bleed-through from the verso and foxing binarise into components that look
# like diacritics but are pale. Ink this word actually carries is dark: a
# candidate must be within this factor of the word's own median ink darkness.
INK_DARKNESS_TOL = 1.25

# A mark this small is a diacritic (i-Strich, u-Bogen, umlaut), not a letter —
# the same threshold the proposer uses for its punctuation/diacritic split.
DIACRITIC_MAX_AREA_PX = 300

# Paper grain and foxing on these plates measure well under this; a real
# diacritic on Abb. 19 measures 40–230 px.
SPECK_MIN_AREA_PX = 40

# Backstop behind the rules above: growth beyond this many x-heights is
# reported rather than applied. Deliberately loose — the lineature zone, the
# darkness test and the punctuation rule are what actually decide whose ink it
# is, and a tight cap refuses genuine repairs (at 1.0 it refused „regieren",
# whose last letter is cut by 37 px = 1.2 xh).
GROWTH_CAP_XH = 2.0


@dataclass
class Repair:
    sample_id: str
    word: str
    page: str
    old: tuple[int, int, int, int]
    new: tuple[int, int, int, int]
    reasons: list[str]
    # The entry's exclude rects AFTER the repair: obsolete ones dropped, ones
    # for newly enclosed foreign ink added. Empty on a refused candidate, which
    # changes nothing about the entry at all.
    excludes: list[list[int]] = field(default_factory=list)
    added_excludes: list[list[int]] = field(default_factory=list)
    dropped_excludes: list[list[int]] = field(default_factory=list)

    @property
    def delta(self) -> tuple[int, int, int, int]:
        """Per-side growth (left, top, right, bottom), positive = outward."""
        return (
            self.old[0] - self.new[0],
            self.old[1] - self.new[1],
            self.new[2] - self.old[2],
            self.new[3] - self.old[3],
        )

    @property
    def registration_shift(self) -> tuple[int, int]:
        """What a stored CROP-local registration must move by: the origin's
        shift. `tx += dx`, `baseline_row += dy`."""
        return (self.old[0] - self.new[0], self.old[1] - self.new[1])


class PageInk:
    """Labelled ink of one plate, built once and asked per specimen."""

    def __init__(self, path: Path) -> None:
        self.gray = load_page(path)
        mask = binarize_adaptive(self.gray)
        self.labels, _ = cc_label(mask)
        self.slices = find_objects(self.labels)
        self.sizes = np.bincount(self.labels.ravel())
        self.height, self.width = mask.shape

    def darkness(self, cid: int) -> float:
        """Mean grayscale of a component — lower is darker ink."""
        ys, xs = self.slices[cid - 1]
        sub = self.labels[ys, xs] == cid
        return float(self.gray[ys, xs][sub].mean())

    def component_box(self, cid: int) -> tuple[int, int, int, int]:
        ys, xs = self.slices[cid - 1]
        return int(xs.start), int(ys.start), int(xs.stop), int(ys.stop)

    def own_ink_box(self, entry: dict, excludes: list[list[int]]) -> tuple[int, int, int, int] | None:
        """`own_ink` without the component ids — the shape most callers want."""
        return self.own_ink(entry, excludes)[0]

    def own_ink(self, entry: dict, excludes: list[list[int]]) -> tuple[tuple[int, int, int, int] | None, set[int]]:
        """Bounding box of the ink that belongs to this specimen, and which
        components it is made of — the caller needs the ids to tell what a
        grown rect newly took in that is NOT this word.

        The word's own lineature does the deciding: `midband_y`/`baseline_y`
        are page rows, so the writing zone of THIS line is known exactly, and
        anything outside it belongs to a neighbouring line whatever it looks
        like. Inside the zone, three more tests separate the word's ink from
        what merely sits next to it — an exclude rect the sidecar already
        recorded, punctuation the stored `word` deliberately leaves out, and
        pale bleed-through that binarises like a diacritic but is not ink.
        """
        rect = (int(entry["x0"]), int(entry["y0"]), int(entry["x1"]), int(entry["y1"]))
        x0, y0, x1, y1 = rect
        xh = max(1.0, float(entry["baseline_y"] - entry["midband_y"]))
        zone_top = entry["midband_y"] - ASCENDER_XH * xh
        zone_bottom = entry["baseline_y"] + DESCENDER_XH * xh
        midband = int(entry["midband_y"])

        inside = self.labels[y0:y1, x0:x1]
        core = self._core_darkness(inside)
        candidates: list[tuple[int, tuple[int, int, int, int]]] = []

        for cid in np.unique(inside):
            if cid == 0 or self.sizes[cid] < SPECK_MIN_AREA_PX:
                continue
            if self._excluded(int(cid), excludes):
                continue
            box = self.component_box(int(cid))
            if box[1] < zone_top or box[3] > zone_bottom:
                continue  # reaches into a neighbouring line's zone
            n_in = int((inside == cid).sum())
            small = self.sizes[cid] <= DIACRITIC_MAX_AREA_PX
            # Majority-inside says "this is the word's ink" for letters. It is
            # exactly wrong for a diacritic sliced by the top edge, which has
            # most of its few pixels OUTSIDE — that is the cut u-Bogen of
            # „zum", and reading it as foreign ink is what hid it.
            if n_in * 2 < int(self.sizes[cid]) and not small:
                continue
            if small and self.darkness(int(cid)) > core * INK_DARKNESS_TOL:
                continue
            candidates.append((int(cid), box))

        candidates.extend(self._floating_diacritics(rect, excludes, zone_top, core))
        keep = self._drop_punctuation(candidates, midband, xh)
        if not keep:
            return None, set()
        boxes = [b for _, b in keep]
        box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
        return box, {cid for cid, _ in keep}

    def newly_enclosed_foreign_ink(
        self, old: tuple[int, int, int, int], new: tuple[int, int, int, int], own: set[int]
    ) -> list[tuple[int, int, int, int]]:
        """Ink the GROWTH took in that is not the word's own — what an `exclude`
        has to paint back out.

        This is the „regieren" case: enclosing the last letter's exit stroke
        pulls the comma beside it into the crop, and the stored `word` carries
        letters only. Same answer `propose_boxes` gives a fresh proposal, just
        for a rect that moved.

        Only what the growth is responsible for: a speck that sat inside the
        committed rect all along is not this repair's business, and covering it
        would change a crop where nothing was wrong."""
        x0, y0, x1, y1 = new
        inside = self.labels[y0:y1, x0:x1]
        out: list[tuple[int, int, int, int]] = []
        for cid in np.unique(inside):
            if cid == 0 or int(cid) in own or self.sizes[cid] < DESPECKLE_MIN_AREA_PX:
                # Below the despeckle floor the exporter drops it from the mask
                # anyway, and a 2 px exclude sliver risks nipping real ink.
                continue
            bx0, by0, bx1, by1 = self.component_box(int(cid))
            # Only ink that reaches into the strip the repair GAINED. A
            # component that merely crossed an edge which did not move was
            # already in the committed crop, and covering it now would change a
            # crop where nothing was wrong.
            if not _reaches_growth((bx0, by0, bx1, by1), old, new):
                continue
            out.append((max(x0, bx0 - 1), max(y0, by0 - 1), min(x1, bx1 + 1), min(y1, by1 + 1)))
        return out

    def exclude_hides_own_ink(self, exclude: list[int], own: set[int]) -> bool:
        """Whether an exclude rect now sits on the word's OWN ink and hides no
        foreign ink any more — i.e. whether the repair made it wrong.

        `zum`'s did exactly that: it had been hiding the stub of a u-Bogen the
        old rect cut through, and over the repaired crop it paints a white
        block into clean paper and clips the mark the repair just rescued.

        Both halves are required, and deliberately so. An exclude that still
        covers foreign ink stays even if it grazes the word — that is a
        hand-placed judgement about a neighbour's descender, and this tool does
        not overrule it. Only an exclude that has become pure damage goes."""
        ex0, ey0, ex1, ey1 = (int(round(float(v))) for v in exclude[:4])
        if ex0 >= ex1 or ey0 >= ey1:
            return False
        region = self.labels[ey0:ey1, ex0:ex1]
        hides_own = False
        for cid in np.unique(region):
            if cid == 0:
                continue
            if int(cid) in own:
                hides_own = True
            elif self.sizes[cid] >= DESPECKLE_MIN_AREA_PX:
                return False  # still doing its job
        return hides_own

    def _core_darkness(self, inside: np.ndarray) -> float:
        """Median darkness of the biggest component inside the rect — the word's
        own pen stroke, and the yardstick every faint candidate is held to."""
        ids, counts = np.unique(inside[inside > 0], return_counts=True)
        if not len(ids):
            return 1.0
        return self.darkness(int(ids[int(np.argmax(counts))]))

    def _floating_diacritics(
        self, rect: tuple[int, int, int, int], excludes: list[list[int]], zone_top: float, core: float
    ) -> list[tuple[int, tuple[int, int, int, int]]]:
        """Marks sitting ENTIRELY above the rect that belong to its word: small,
        dark, inside its x-range, and inside this line's own ascender zone (a
        component reaching above it comes down from the line above)."""
        x0, y0, x1, _ = rect
        band_top = max(0, int(zone_top))
        out: list[tuple[int, tuple[int, int, int, int]]] = []
        for cid in np.unique(self.labels[band_top:y0, x0:x1]):
            if cid == 0:
                continue
            area = int(self.sizes[cid])
            if not (SPECK_MIN_AREA_PX <= area <= DIACRITIC_MAX_AREA_PX):
                continue
            if self._excluded(int(cid), excludes):
                continue
            bx0, by0, bx1, by1 = self.component_box(int(cid))
            if by1 > y0 or by0 < zone_top:
                continue
            if not (x0 <= (bx0 + bx1) / 2 <= x1):
                continue
            if self.darkness(int(cid)) > core * INK_DARKNESS_TOL:
                continue  # bleed-through or foxing, not this word's mark
            out.append((int(cid), (bx0, by0, bx1, by1)))
        return out

    @staticmethod
    def _drop_punctuation(
        candidates: list[tuple[int, tuple[int, int, int, int]]], midband: int, xh: float
    ) -> list[tuple[int, tuple[int, int, int, int]]]:
        """The stored `word` carries letters only (words.json says so itself),
        so a comma or period trailing the last letter must never pull the rect
        out over it — and on these plates it would, every time: every
        right-edge candidate of the first pass was a comma.

        Position decides, not size: a Sütterlin comma is as big as a diacritic,
        and it can overlap the last letter's x-range, so "sits beside the word"
        does not separate them either. What does: every LETTER reaches up into
        the x-height band, and punctuation hangs entirely below the
        Mittellinie."""
        return [(cid, b) for cid, b in candidates if b[1] <= midband + 0.3 * xh]

    def _excluded(self, cid: int, excludes: list[list[int]]) -> bool:
        """The sidecar's own verdict: a component lying at least
        EXCLUDE_COMPONENT_FRAC inside an exclude rect is foreign ink — the same
        component-wise rule `core.word_metric.clear_excluded` scores with."""
        if not excludes:
            return False
        ys, xs = self.slices[cid - 1]
        sub = self.labels[ys, xs] == cid
        total = int(sub.sum())
        if not total:
            return False
        covered = np.zeros_like(sub)
        for ex in excludes:
            ex0, ey0, ex1, ey1 = (int(round(float(v))) for v in ex[:4])
            cx0, cy0 = max(xs.start, ex0), max(ys.start, ey0)
            cx1, cy1 = min(xs.stop, ex1), min(ys.stop, ey1)
            if cx0 < cx1 and cy0 < cy1:
                covered[cy0 - ys.start : cy1 - ys.start, cx0 - xs.start : cx1 - xs.start] = True
        return int((sub & covered).sum()) >= EXCLUDE_COMPONENT_FRAC * total


def _neighbour_limits(
    rect: tuple[int, int, int, int], others: list[tuple[int, int, int, int]], page: tuple[int, int]
) -> tuple[int, int, int, int]:
    """How far the rect may grow per side before it reaches half way into a
    neighbouring specimen — a crop must never carry another word's ink."""
    h, w = page
    left, top, right, bottom = 0, 0, w, h
    x0, y0, x1, y1 = rect
    for ox0, oy0, ox1, oy1 in others:
        if oy0 < y1 and oy1 > y0:  # shares rows → a horizontal neighbour
            if ox1 <= x0:
                left = max(left, (ox1 + x0) // 2)
            if ox0 >= x1:
                right = min(right, (ox0 + x1) // 2)
        if ox0 < x1 and ox1 > x0:  # shares columns → a vertical neighbour
            if oy1 <= y0:
                top = max(top, (oy1 + y0) // 2)
            if oy0 >= y1:
                bottom = min(bottom, (oy0 + y1) // 2)
    return left, top, right, bottom


def xh_of(entry: dict) -> float:
    """This specimen's x-height in page pixels — the scale every tolerance in
    this tool is expressed in."""
    return max(1.0, float(entry["baseline_y"] - entry["midband_y"]))


def plan_repairs(source_id: str, pad: int = PAD_PX) -> tuple[list[Repair], list[Repair]]:
    """(repairs to apply, candidates refused for a runaway growth)"""
    sidecar = json.loads((REPO_ROOT / "data" / "sources" / source_id / "words.json").read_text(encoding="utf-8"))
    words = sidecar["words"]
    inks: dict[str, PageInk] = {}
    repairs: list[Repair] = []
    refused: list[Repair] = []

    for w in words:
        page = w["page"]
        if page not in inks:
            inks[page] = PageInk(REPO_ROOT / "data" / "sources" / source_id / page)
        ink = inks[page]
        rect = (int(w["x0"]), int(w["y0"]), int(w["x1"]), int(w["y1"]))
        excludes = [list(map(int, ex[:4])) for ex in (w.get("exclude") or [])]
        box, own = ink.own_ink(w, excludes)
        if box is None:
            continue

        clearance = (box[0] - rect[0], box[1] - rect[1], rect[2] - box[2], rect[3] - box[3])
        if min(clearance) >= MIN_CLEARANCE_PX:
            # The ink has air on every side, so the rect stays — but its
            # excludes are still checked. An earlier repair can have made one
            # obsolete, and a stale exclude is not a harmless leftover: the
            # exporter paints its area paper-white, so it shows up as a white
            # block in the middle of the crop (`zum`, seen by the author).
            stale = [ex for ex in excludes if ink.exclude_hides_own_ink(ex, own)]
            if stale:
                repair = Repair(str(w.get("id") or w["word"]), w["word"], page, rect, rect, ["exclude only"])
                repair.excludes = [ex for ex in excludes if ex not in stale]
                repair.dropped_excludes = stale
                repairs.append(repair)
            continue

        others = [
            (int(o["x0"]), int(o["y0"]), int(o["x1"]), int(o["y1"])) for o in words if o["page"] == page and o is not w
        ]
        lim_l, lim_t, lim_r, lim_b = _neighbour_limits(rect, others, (ink.height, ink.width))
        # Only the tight sides move: a side with air keeps its committed edge,
        # which keeps the crop — and every trace registered in it — as it was.
        new = (
            max(lim_l, min(rect[0], box[0] - pad)) if clearance[0] < MIN_CLEARANCE_PX else rect[0],
            max(lim_t, min(rect[1], box[1] - pad)) if clearance[1] < MIN_CLEARANCE_PX else rect[1],
            min(lim_r, max(rect[2], box[2] + pad)) if clearance[2] < MIN_CLEARANCE_PX else rect[2],
            min(lim_b, max(rect[3], box[3] + pad)) if clearance[3] < MIN_CLEARANCE_PX else rect[3],
        )
        if new == rect:
            continue
        # A runaway would mean the ink crossing the border is not this word's
        # at all — but the lineature zone, the darkness test and the
        # punctuation rule already decide that, one by one and for a reason.
        # The cap is only the backstop behind them, so it is generous: at one
        # x-height it refused „regieren", whose last letter really is cut by
        # 37 px, and refusing a true repair is the worse failure of the two.
        grown = (rect[0] - new[0], rect[1] - new[1], new[2] - rect[2], new[3] - rect[3])
        sides = ("left", "top", "right", "bottom")
        reasons = [f"{s}+{d}" for s, d in zip(sides, grown, strict=True) if d]
        repair = Repair(str(w.get("id") or w["word"]), w["word"], page, rect, new, reasons)
        if max(grown) > GROWTH_CAP_XH * xh_of(w):
            refused.append(repair)
            continue
        # Two things the moved edge changes about the excludes, both of which
        # the author saw before this code did:
        #   * the grown rect can take in ink that is NOT this word — enclosing
        #     „regieren"'s exit stroke pulls the comma in beside it;
        #   * an exclude anchored to the OLD edge can end up over nothing —
        #     `zum`'s hid the stub of the u-Bogen the old rect cut through, and
        #     over the repaired crop it is a white block on clean paper.
        repair.excludes = [ex for ex in excludes if not ink.exclude_hides_own_ink(ex, own)]
        repair.dropped_excludes = [ex for ex in excludes if ex not in repair.excludes]
        for ex in ink.newly_enclosed_foreign_ink(rect, new, own):
            if not any(_overlaps(ex, kept) for kept in repair.excludes):
                repair.excludes.append(list(ex))
                repair.added_excludes.append(list(ex))
        repairs.append(repair)
    return repairs, refused


def _overlaps(a: tuple[int, int, int, int] | list[int], b: list[int] | tuple[int, int, int, int]) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _reaches_growth(
    box: tuple[int, int, int, int], old: tuple[int, int, int, int], new: tuple[int, int, int, int]
) -> bool:
    """Whether `box` touches any strip the repair added to the rect — the four
    slabs between the old edges and the new ones."""
    strips = (
        (new[0], new[1], old[0], new[3]),  # left
        (new[0], new[1], new[2], old[1]),  # top
        (old[2], new[1], new[2], new[3]),  # right
        (new[0], old[3], new[2], new[3]),  # bottom
    )
    return any(s[0] < s[2] and s[1] < s[3] and _overlaps(box, s) for s in strips)


# ------------------------------------------------------------------ rendering


def draw_repair_tiles(source_id: str, repairs: list[Repair], out_dir: Path, margin: int = 45, zoom: int = 2) -> None:
    """One tile per repair: committed rect red, repaired rect green."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pages: dict[str, Image.Image] = {}
    for r in repairs:
        if r.page not in pages:
            pages[r.page] = Image.open(REPO_ROOT / "data" / "sources" / source_id / r.page).convert("RGB")
        page = pages[r.page]
        cx0 = max(0, min(r.old[0], r.new[0]) - margin)
        cy0 = max(0, min(r.old[1], r.new[1]) - margin)
        cx1 = min(page.width, max(r.old[2], r.new[2]) + margin)
        cy1 = min(page.height, max(r.old[3], r.new[3]) + margin)
        tile = page.crop((cx0, cy0, cx1, cy1)).resize(((cx1 - cx0) * zoom, (cy1 - cy0) * zoom), Image.LANCZOS)
        d = ImageDraw.Draw(tile)
        for box, colour, width in ((r.new, (20, 150, 60), 3), (r.old, (220, 20, 40), 2)):
            d.rectangle(
                [(box[0] - cx0) * zoom, (box[1] - cy0) * zoom, (box[2] - cx0) * zoom - 1, (box[3] - cy0) * zoom - 1],
                outline=colour,
                width=width,
            )
        tile.save(out_dir / f"{r.sample_id}.png")


# ----------------------------------------------------------------------- CLI


def apply_repairs(source_id: str, repairs: list[Repair]) -> None:
    """Write the repaired rects back, touching only x0/y0/x1/y1 of the repaired
    entries — `baseline_y`/`midband_y` are page coordinates and stay put."""
    path = REPO_ROOT / "data" / "sources" / source_id / "words.json"
    raw = path.read_text(encoding="utf-8")
    sidecar = json.loads(raw)
    by_id = {r.sample_id: r for r in repairs}
    for w in sidecar["words"]:
        r = by_id.get(str(w.get("id") or w["word"]))
        if r is None:
            continue
        w["x0"], w["y0"], w["x1"], w["y1"] = r.new
        if r.excludes:
            w["exclude"] = [list(ex) for ex in r.excludes]
        else:
            w.pop("exclude", None)
    path.write_text(json.dumps(sidecar, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--pad", type=int, default=PAD_PX, help="clearance to leave around the word's own ink")
    parser.add_argument("--report", action="store_true", help="print the plan (default when nothing else is asked)")
    parser.add_argument("--sheets", type=Path, help="write one before/after tile per repair into this directory")
    parser.add_argument("--apply", action="store_true", help="write the repaired rects into words.json")
    args = parser.parse_args()

    repairs, refused = plan_repairs(args.source, args.pad)
    if args.report or not (args.sheets or args.apply):
        print(f"{len(repairs)} specimen(s) clip their own ink\n")
        for r in repairs:
            extra = ""
            if r.added_excludes:
                extra += f"  +exclude {r.added_excludes}"
            if r.dropped_excludes:
                extra += f"  -exclude {r.dropped_excludes}"
            print(f"  {r.sample_id:<18} {r.word:<14} {r.page:<18} {' '.join(r.reasons)}{extra}")
        if refused:
            print(f"\n{len(refused)} candidate(s) refused — the ink crossing the border grows the box by")
            print("more than one x-height, so it is not a fragment of this word (punctuation fused to")
            print("the last letter, a neighbour): look at these by hand.")
            for r in refused:
                print(f"  {r.sample_id:<18} {r.word:<14} {r.page:<18} {r.old} -> {r.new}")
    if args.sheets:
        draw_repair_tiles(args.source, repairs, args.sheets)
        print(f"wrote {len(repairs)} tile(s) to {args.sheets}")
    if args.apply:
        apply_repairs(args.source, repairs)
        print(f"applied {len(repairs)} repair(s) to words.json — re-export the fixtures and log the re-baseline")


if __name__ == "__main__":
    main()
