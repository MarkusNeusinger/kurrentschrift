"""Millimetre page geometry of a Bogen (training sheet).

Python port of the band math, presets and role styles of
``app/src/lib/lineatur.ts`` — that TS file is the source of truth for the
shared constants (the unit test pins them; change both together). On top of
the port sits what the Übungsblatt does not have: per-word lineature BOXES
(band lines drawn only inside each box span, ink-free gutters between),
corner fiducials (Passmarken), row labels and the layout sidecar the
importer registers against.

Coordinates: mm, origin top-left, y downwards (lineatur.ts convention).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from core.shaping import shape_word


A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0

# Corner fiducials: solid black squares centered inside typical printer
# margins; the top-left one carries a white hole (donut) so the importer can
# recover page orientation from any rotation.
FIDUCIAL_SIZE_MM = 8.0
FIDUCIAL_HOLE_MM = 3.0
FIDUCIAL_CENTERS: dict[str, tuple[float, float]] = {
    "tl": (7.0, 7.0),
    "tr": (203.0, 7.0),
    "bl": (7.0, 290.0),
    "br": (203.0, 290.0),
}
FIDUCIAL_DONUT = "tl"

# Sheet layout constants (proposal §5): the label zone carries the clear-text
# words under the boxes, the footer zone keeps the last row off the bottom
# fiducials and leaves room for the provenance footer ("10 fits, 9 breathes").
LABEL_ZONE_MM = 4.0
# The gap between two row blocks is what the scissors get (owner, 2026-08-23:
# more room between the rows, and mark where to cut). It has to hold the two
# cut lines of the neighbouring Schnittbänder plus tolerance on both sides —
# 12 mm leaves 5 mm of free paper between them, so a cut that wanders by 2 mm
# still misses both strips.
ROW_GAP_MM = 12.0
# Schnittband — the rectangle one strip is cut to. Identical for EVERY row of a
# sheet (and every sheet of a style), so the collection ends up with strips of
# one height and one width: the width is fixed columns, never the words' extent,
# and the height is the row block plus these two paddings. The top pad is the
# wider one because it carries the printed strip id.
CUT_PAD_TOP_MM = 4.0
CUT_PAD_BOTTOM_MM = 3.0
CUT_X0_MM = 12.0  # 3 mm left of the writing area (margin 15 mm)
CUT_X1_MM = 197.0  # 2 mm right of it, and clear of the verdict column
# Cut marks sit in the page margins, never on the strip: ink inside the
# Schnittband would end up in the training data.
CUT_TICK_MM = 2.5
CUT_TICK_GAP_MM = 1.5
# The first row starts lower than the side margin: its Schnittband's top cut
# mark would otherwise sit level with the top Passmarken, and a hairline that
# blurs into a Passmarke on a scan drags its centroid — and with it every
# millimetre the importer computes.
TOP_MARGIN_MM = 26.0
# Per-row verdict box in the RIGHT margin (owner, 2026-08-23: mark each
# strip ok/not-ok with the pen right away), OUTSIDE the Schnittband: the tick
# is bookkeeping, not training data, so it must not end up on the strip. The
# writing area ends at 195 mm and the corner Passmarken only occupy the top
# and bottom of the page, so the band beyond the cut line is free at every row
# height — and it is where the hand already is. ONE box (owner,
# 2026-08-23): a cross or check in it means the row is good, an empty box
# means it is not. That keeps the sheet to a single pen movement, and the
# failure mode of a forgotten tick is the harmless one — the strip goes
# back into the print queue instead of being filed unreviewed.
MARK_BOX_MM = 5.0
MARK_COL_X0_MM = 202.0
FOOTER_ZONE_MM = 12.0
BOX_GAP_MM = 3.0
BOX_LEAD_MM = 10.0  # entry room before the first letter (Anstrich) + slack
# The packing never fills a row to the edge: the width model is an ESTIMATE
# until the Kalibrier-Schleife has seen real ink, and a row packed to
# 180.0 of 180 mm (as the first plan was) has nothing left when the estimate
# is 5 % low. This reserve is what a hand writing larger than the model gets.
PACK_SLACK_MM = 15.0
BOX_OVERHANG_MM = 1.0  # box edges extend past ascender/descender lines


@dataclass(frozen=True)
class ScriptPreset:
    """The lineature subset of a lineatur.ts preset that sheets need.

    Values are pinned against app/src/lib/lineatur.ts PRESETS by
    tests/test_eigenhand_geometry.py — the TS file is the source of truth.
    """

    style: str
    display: str
    ratio: tuple[int, int, int]  # ascender : x-height : descender
    x_height_mm: float
    slant_deg: float  # Schräglage, 90 = upright
    show_slant: bool
    slant_spacing_mm: float


PRESETS: dict[str, ScriptPreset] = {
    "kurrent": ScriptPreset("kurrent", "Kurrent", (2, 1, 2), 2.5, 65.0, True, 10.0),
    "suetterlin": ScriptPreset("suetterlin", "Sütterlin", (1, 1, 1), 6.0, 90.0, False, 10.0),
    "offenbacher": ScriptPreset("offenbacher", "Offenbacher", (2, 3, 2), 5.0, 77.0, True, 12.0),
}

# Ruling styles: the lineatur.ts `druck` theme (RULING_THEMES[0]), pinned by
# the same test. (color, width_mm, dash) — dash in mm (on, off) or None.
ROLE_STYLES: dict[str, tuple[str, float, tuple[float, float] | None]] = {
    "baseline": ("#1A1A17", 0.35, None),
    "waist": ("#6B6A63", 0.25, None),
    "ascender": ("#B8B6AE", 0.18, (1.6, 1.6)),
    "descender": ("#B8B6AE", 0.18, (1.6, 1.6)),
    "slant": ("#D6D4CB", 0.15, (1.0, 1.6)),
    "box": ("#B8B6AE", 0.18, None),  # box edges + corner ticks (sheet-only role)
    "cut": ("#1A1A17", 0.25, None),  # Schnittmarken in the margins (sheet-only role)
    "label": ("#4A4944", 0.0, None),  # clear-text word labels (color only)
    "meta": ("#6B6A63", 0.0, None),  # header/footer/row-id text (color only)
}

# What a CAPTURE sheet prints instead (owner, 2026-08-23: "the guide lines
# matter, but they can be very faint — easy to remove from the scan, no
# influence on the word statistics or the ink fitting"). The app's `druck`
# theme above is tuned for reading on screen and paper; a training sheet is
# read once, by a hand that already knows where the lines are, and then has
# to disappear.
#
# Every ruling value here is well above ingest.INK_THRESHOLD (0.55, i.e.
# #8C8C8C) in luminance, so no printed line can ever be counted as ink even
# if the masking missed it — the faintest, the Schräglage grid, sits near the
# paper. Only what the WRITER must read stays dark: labels, ids, header, the
# verdict box and the cut marks (all outside the writing band or masked).
CAPTURE_STYLES: dict[str, tuple[str, float, tuple[float, float] | None]] = {
    **ROLE_STYLES,
    "baseline": ("#A8A6A0", 0.22, None),  # the one line the hand really needs
    "waist": ("#C0BEB8", 0.15, None),
    "ascender": ("#D2D0CA", 0.12, (1.6, 1.6)),
    "descender": ("#D2D0CA", 0.12, (1.6, 1.6)),
    "slant": ("#E2E0DA", 0.10, (1.0, 1.6)),
    "box": ("#CFCDC7", 0.12, None),
}

# Slot advances in x-height units — the physical width model of the packing
# and the box generator: box = BOX_LEAD_MM + sum(advance) * x_height. Start
# values, refined by the Kalibrier-Schleife against the first written sheet
# (report --calibrate).
#
# Raised across the board on 2026-08-23 (owner: "is that enough room for a
# word like Galoppieren?"). It was not: at the old values a Sütterlin
# lowercase came to 0.85 x-height ≈ 5.1 mm, but at 6 mm x-height a round
# upright `n` with its exit stroke measures nearer 6 mm — and an unpractised
# hand writes larger, not smaller. The default is now a full x-height, and
# the packing keeps PACK_SLACK_MM in reserve on top. Too wide costs a word
# per row; too narrow costs the row.
ADVANCE_DEFAULT_XH = 1.00
ADVANCE_XH: dict[str, float] = {
    # narrow lowercase
    "i": 0.55,
    "j": 0.55,
    "l": 0.60,
    "longs": 0.60,
    "t": 0.70,
    "f": 0.70,
    "r": 0.75,
    "e": 0.75,
    "s": 0.75,
    "c": 0.80,
    # wide lowercase
    "m": 1.75,
    "w": 1.70,
    # ligatures
    "ch": 1.55,
    "ck": 1.55,
    "tz": 1.45,
    "longst": 1.35,
    "qu": 1.75,
    "sz": 1.30,
    # capitals (defaults for the rest via _advance_of)
    "M": 2.00,
    "W": 2.00,
}
ADVANCE_CAPITAL_XH = 1.60


def _advance_of(key: str) -> float:
    if key in ADVANCE_XH:
        return ADVANCE_XH[key]
    if key[:1].isupper():
        return ADVANCE_CAPITAL_XH
    return ADVANCE_DEFAULT_XH


@lru_cache(maxsize=1)
def _fugen_forms() -> dict[str, str]:
    """word → fugen-marked shaping form, for the pool words that carry one.

    Width estimation must shape the form the writer is asked to WRITE: a
    fugen marker can force the round s and block the ſt ligature, which
    changes the advance sum. Resolved centrally here so packing (pool.py)
    and box generation (sheet.py) can never disagree.
    """
    from tools.eigenhand.corpus import pool_entries  # noqa: PLC0415 — avoid import cost for non-pool callers

    return {e["word"]: e["fugen"] for e in pool_entries() if e.get("fugen")}


def estimate_word_width_mm(word: str, x_height_mm: float) -> float:
    """Estimated box width for one word at a given x-height (see ADVANCE_XH)."""
    slots = shape_word(_fugen_forms().get(word, word))
    advance = sum(_advance_of(slot.key) for slot in slots if slot.key is not None)
    return BOX_LEAD_MM + advance * x_height_mm


def row_height_mm(preset: ScriptPreset) -> float:
    """Height of one writing row (ascender + x-height + descender bands)."""
    asc, xh, desc = preset.ratio
    unit = preset.x_height_mm / xh
    return asc * unit + preset.x_height_mm + desc * unit


def row_pitch_mm(preset: ScriptPreset) -> float:
    return row_height_mm(preset) + LABEL_ZONE_MM + ROW_GAP_MM


def usable_row_width_mm(margin_mm: float = 15.0) -> float:
    return A4_WIDTH_MM - 2 * margin_mm


def max_rows(preset: ScriptPreset, margin_mm: float = 15.0) -> int:
    """How many rows fit between the margins, footer zone reserved."""
    usable = A4_HEIGHT_MM - TOP_MARGIN_MM - margin_mm - FOOTER_ZONE_MM
    pitch = row_pitch_mm(preset)
    return max(0, int((usable + ROW_GAP_MM) // pitch))


def clip_to_rect(
    x1: float, y1: float, x2: float, y2: float, xmin: float, ymin: float, xmax: float, ymax: float
) -> tuple[float, float, float, float] | None:
    """Liang–Barsky segment clip (port of lineatur.ts clipToRect)."""
    t0, t1 = 0.0, 1.0
    dx, dy = x2 - x1, y2 - y1
    p = (-dx, dx, -dy, dy)
    q = (x1 - xmin, xmax - x1, y1 - ymin, ymax - y1)
    for pi, qi in zip(p, q, strict=True):
        if pi == 0:
            if qi < 0:
                return None
        else:
            r = qi / pi
            if pi < 0:
                if r > t1:
                    return None
                t0 = max(t0, r)
            else:
                if r < t0:
                    return None
                t1 = min(t1, r)
    return (x1 + t0 * dx, y1 + t0 * dy, x1 + t1 * dx, y1 + t1 * dy)


@dataclass(frozen=True)
class RowBand:
    """The four guide-line heights of one row, mm from the page top."""

    asc_top: float
    waist: float
    baseline: float
    desc_bot: float


def row_band(preset: ScriptPreset, row_top_mm: float) -> RowBand:
    asc, xh, desc = preset.ratio
    unit = preset.x_height_mm / xh
    waist = row_top_mm + asc * unit
    baseline = waist + preset.x_height_mm
    return RowBand(row_top_mm, waist, baseline, baseline + desc * unit)


def cut_box(band: RowBand) -> tuple[float, float, float, float]:
    """The Schnittband of one row: (x0, y0, x1, y1) in mm — where to cut.

    Fixed columns and fixed paddings, so every strip of a style comes out at
    the same width and the same height no matter how many words its row
    carries. It spans the writing band AND the clear-text label below it: the
    words under the boxes are what makes a cut strip attributable on its own.
    """
    return (CUT_X0_MM, band.asc_top - CUT_PAD_TOP_MM, CUT_X1_MM, band.desc_bot + LABEL_ZONE_MM + CUT_PAD_BOTTOM_MM)


def cut_size_mm(preset: ScriptPreset) -> tuple[float, float]:
    """(width, height) of every Schnittband of this preset — the strip format."""
    return (CUT_X1_MM - CUT_X0_MM, row_height_mm(preset) + LABEL_ZONE_MM + CUT_PAD_TOP_MM + CUT_PAD_BOTTOM_MM)


def cut_ticks(cut: tuple[float, float, float, float]) -> list[tuple[float, float, float, float]]:
    """The four margin ticks of one Schnittband: (x1, y1, x2, y2) segments in mm.

    Two per cut line, left and right of the strip and never inside it. The
    vertical cut lines are the same for every row, so those are marked once per
    page (page_cut_ticks), not here.
    """
    x0, y0, x1, y1 = cut
    left_outer, left_inner = x0 - CUT_TICK_GAP_MM - CUT_TICK_MM, x0 - CUT_TICK_GAP_MM
    right_inner, right_outer = x1 + CUT_TICK_GAP_MM, x1 + CUT_TICK_GAP_MM + CUT_TICK_MM
    return [(left_outer, y, left_inner, y) for y in (y0, y1)] + [(right_inner, y, right_outer, y) for y in (y0, y1)]


def page_cut_ticks(cuts: list[tuple[float, float, float, float]]) -> list[tuple[float, float, float, float]]:
    """Ticks for the two vertical cut lines: above the first strip, in every
    gap, and below the last.

    The vertical cuts are the same x for every row, so they are marked between
    the strips rather than per row. Both ends of the page carry a pair, so it
    reads the same top and bottom (owner, 2026-08-23) — TOP_MARGIN_MM is set
    so the top pair keeps clear of the Passmarken: a hairline that blurs into
    one on a scan drags its centroid, and with it the rectification.
    """
    if not cuts:
        return []
    ordered = sorted(cuts, key=lambda c: c[1])
    half = CUT_TICK_MM / 2
    top = ordered[0][1]
    ticks: list[tuple[float, float, float, float]] = [
        (x, top - CUT_TICK_GAP_MM - CUT_TICK_MM, x, top - CUT_TICK_GAP_MM) for x in (CUT_X0_MM, CUT_X1_MM)
    ]
    for upper, lower in zip(ordered, ordered[1:], strict=False):
        middle = (upper[3] + lower[1]) / 2
        ticks += [(x, middle - half, x, middle + half) for x in (CUT_X0_MM, CUT_X1_MM)]
    bottom = ordered[-1][3]
    ticks += [(x, bottom + CUT_TICK_GAP_MM, x, bottom + CUT_TICK_GAP_MM + CUT_TICK_MM) for x in (CUT_X0_MM, CUT_X1_MM)]
    return ticks


def mark_box(band: RowBand) -> tuple[float, float, float, float]:
    """The verdict box of one row: (x0, y0, x1, y1) in mm.

    Vertically centred on the x-height band — where the pen rests at the
    end of a row — and clamped into the row block so a script with a tiny
    x-height (Kurrent, 2.5 mm) keeps the box inside its own row.
    """
    centre = (band.waist + band.baseline) / 2
    half = MARK_BOX_MM / 2
    top = min(max(centre - half, band.asc_top), band.desc_bot - MARK_BOX_MM)
    return (MARK_COL_X0_MM, top, MARK_COL_X0_MM + MARK_BOX_MM, top + MARK_BOX_MM)


def pack_words_into_rows(words: list[str], preset: ScriptPreset, margin_mm: float = 15.0) -> list[list[str]]:
    """Greedy width packing of an ordered word stream into row-sized groups.

    Used by pool.py to cut the planned word stream into Streifen. Packing runs
    against the WIDEST preset in practice (Sütterlin, 6 mm x-height) so a
    strip fits every script's rows. A 12-word lookahead window may pull a
    later word forward when it still fits — deterministic, order-stable
    otherwise.
    """
    usable = usable_row_width_mm(margin_mm) - PACK_SLACK_MM
    remaining = list(words)
    rows: list[list[str]] = []
    while remaining:
        row: list[str] = []
        width = 0.0
        index = 0
        while index < len(remaining):
            candidate = remaining[index]
            candidate_width = estimate_word_width_mm(candidate, preset.x_height_mm)
            needed = candidate_width + (BOX_GAP_MM if row else 0.0)
            if width + needed <= usable:
                row.append(candidate)
                width += needed
                remaining.pop(index)  # index now points at the next candidate
                continue
            if index >= 11:  # 12-word lookahead window exhausted
                break
            index += 1
        if not row:
            # A single word wider than the row: give it its own row anyway —
            # the box generator clamps the box to the usable width.
            rows.append([remaining.pop(0)])
            continue
        rows.append(row)
    return rows


def boxes_for_row(words: list[str], preset: ScriptPreset, margin_mm: float = 15.0) -> list[tuple[float, float]]:
    """Left/right x (mm) of each word box in one row, clamped to the margins.

    The packing left PACK_SLACK_MM unused; that reserve is handed BACK here,
    spread over the boxes in proportion to their estimated width, so every
    word gets room rather than only the last one on the line (owner,
    2026-08-23: "there has to be buffer everywhere — I don't want to ruin a
    word because I ran out of space at the end"). A long word gets the larger
    share of it, which is where the estimate can be off the most.
    """
    usable = usable_row_width_mm(margin_mm)
    widths = [min(estimate_word_width_mm(word, preset.x_height_mm), usable) for word in words]
    gaps = BOX_GAP_MM * (len(words) - 1)
    spare = usable - gaps - sum(widths)
    if spare > 0 and sum(widths) > 0:
        widths = [w + spare * w / sum(widths) for w in widths]

    x = margin_mm
    out: list[tuple[float, float]] = []
    for index, width in enumerate(widths):
        if index:
            x += BOX_GAP_MM
        x1 = min(x + width, margin_mm + usable)
        out.append((x, x1))
        x = x1
    return out
