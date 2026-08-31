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
for byte as committed. Which ink is the word's OWN is the whole question:

  * a component with the majority of its pixels inside the rect is the word's,
    UNLESS its bbox reaches more than `--band` px beyond an edge — a descender
    from the line above dips deep into a rect but starts far above it, and
    swallowing it would drag the box into the neighbouring line;
  * a SMALL component (a diacritic) near the rect's top, inside its x-range,
    is the word's even when it lies entirely outside — that is precisely the
    cut-off i-dot this tool exists for;
  * anything an `exclude` rect already covers is foreign ink by the sidecar's
    own testimony and never counts (same component-wise rule the metric uses).

The repaired rect is that ink's bbox plus `--pad`, clamped to the plate and to
the midpoint of the gap to any neighbouring specimen — a crop must never eat
its neighbour's word.

WHAT ELSE MOVES WITH A RECT (do not skip):
  * `baseline_y`/`midband_y` are PAGE coordinates and stay valid unchanged.
  * Stored word traces register in CROP-local pixels
    (`measurements.registration_px`), so a moved `x0`/`y0` shifts them out of
    place. `--registration-shift` writes the exact per-specimen correction as
    JSON; `tools/wordbench/shift_registrations.py` applies it through the admin
    API. Skipping this leaves every trace of a repaired specimen stamped
    „Rahmen veraltet" and out of the bench.
  * The wordbench fixture roots freeze these rects. A repaired plate needs a
    fixture re-export and a dated re-baseline entry in `qualitaetsmetrik.md`
    §14 — the ruler changed, and silently comparing across it is the one thing
    the frozen-reference rule forbids.

Usage:
    uv run python -m tools.wordbench.repair_boxes --report
    uv run python -m tools.wordbench.repair_boxes --sheets temp/repair
    uv run python -m tools.wordbench.repair_boxes --apply --registration-shift temp/shift.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import find_objects
from scipy.ndimage import label as cc_label

from core.extract import binarize_adaptive
from core.word_metric import EXCLUDE_COMPONENT_FRAC
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


@dataclass
class Repair:
    sample_id: str
    word: str
    page: str
    old: tuple[int, int, int, int]
    new: tuple[int, int, int, int]
    reasons: list[str]

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
        """Bounding box of the ink that belongs to this specimen.

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
        boxes = self._drop_punctuation([b for _, b in candidates], midband, xh)
        if not boxes:
            return None
        return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))

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
        boxes: list[tuple[int, int, int, int]], midband: int, xh: float
    ) -> list[tuple[int, int, int, int]]:
        """The stored `word` carries letters only (words.json says so itself),
        so a comma or period trailing the last letter must never pull the rect
        out over it — and on these plates it would, every time: every
        right-edge candidate of the first pass was a comma.

        Position decides, not size: a Sütterlin comma is as big as a diacritic,
        and it can overlap the last letter's x-range, so "sits beside the word"
        does not separate them either. What does: every LETTER reaches up into
        the x-height band, and punctuation hangs entirely below the
        Mittellinie."""
        return [b for b in boxes if b[1] <= midband + 0.3 * xh]

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
    """(repairs to apply, candidates refused for growing more than one x-height)"""
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
        box = ink.own_ink_box(w, w.get("exclude") or [])
        if box is None:
            continue

        clearance = (box[0] - rect[0], box[1] - rect[1], rect[2] - box[2], rect[3] - box[3])
        if min(clearance) >= MIN_CLEARANCE_PX:
            continue  # the ink has air on every side — leave the rect alone

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
        # A repair moves an edge by a few px to clear a diacritic or a sliced
        # stroke. A whole x-height of growth means the ink crossing the border
        # is not a fragment of this word at all — punctuation fused to the last
        # letter's exit is the case on these plates (the „regieren" comma) —
        # and a box that swallows it is worse than one that cuts it. Report,
        # never apply: the sidecar's `incomplete` flag is the honest answer
        # when the ink truly cannot be enclosed.
        cap = xh_of(w)
        grown = (rect[0] - new[0], rect[1] - new[1], new[2] - rect[2], new[3] - rect[3])
        if max(grown) > cap:
            refused.append(Repair(str(w.get("id") or w["word"]), w["word"], page, rect, new, ["over cap"]))
            continue
        sides = ("left", "top", "right", "bottom")
        reasons = [f"{s}+{d}" for s, d in zip(sides, grown, strict=True) if d]
        repairs.append(Repair(str(w.get("id") or w["word"]), w["word"], page, rect, new, reasons))
    return repairs, refused


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
    path.write_text(json.dumps(sidecar, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--pad", type=int, default=PAD_PX, help="clearance to leave around the word's own ink")
    parser.add_argument("--report", action="store_true", help="print the plan (default when nothing else is asked)")
    parser.add_argument("--sheets", type=Path, help="write one before/after tile per repair into this directory")
    parser.add_argument("--apply", action="store_true", help="write the repaired rects into words.json")
    parser.add_argument(
        "--registration-shift",
        type=Path,
        help="write the per-specimen crop-origin shift stored traces must follow (JSON)",
    )
    args = parser.parse_args()

    repairs, refused = plan_repairs(args.source, args.pad)
    if args.report or not (args.sheets or args.apply or args.registration_shift):
        print(f"{len(repairs)} specimen(s) clip their own ink\n")
        for r in repairs:
            print(f"  {r.sample_id:<18} {r.word:<14} {r.page:<18} {' '.join(r.reasons)}")
        if refused:
            print(f"\n{len(refused)} candidate(s) refused — the ink crossing the border grows the box by")
            print("more than one x-height, so it is not a fragment of this word (punctuation fused to")
            print("the last letter, a neighbour): look at these by hand.")
            for r in refused:
                print(f"  {r.sample_id:<18} {r.word:<14} {r.page:<18} {r.old} -> {r.new}")
    if args.sheets:
        draw_repair_tiles(args.source, repairs, args.sheets)
        print(f"wrote {len(repairs)} tile(s) to {args.sheets}")
    if args.registration_shift:
        payload = {
            r.sample_id: {"dx": r.registration_shift[0], "dy": r.registration_shift[1]}
            for r in repairs
            if r.registration_shift != (0, 0)
        }
        args.registration_shift.parent.mkdir(parents=True, exist_ok=True)
        args.registration_shift.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {len(payload)} registration shift(s) to {args.registration_shift}")
    if args.apply:
        apply_repairs(args.source, repairs)
        print(f"applied {len(repairs)} repair(s) to words.json — re-export the fixtures and log the re-baseline")


if __name__ == "__main__":
    main()
