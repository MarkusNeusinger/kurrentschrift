"""Die Fleckenmaske — printer specks removed as DATA, never as pixels.

The author's laser printer drops loose toner in the right part of the page
(2026-09-07: „Mein Laserdrucker macht leider im rechten Bereich unkontrolliert
schwarze Punkte, Reinigen hilft nichts"). Two places that hurts:

* inside a row's Schnittband the speck ends up INSIDE the filed strip PNG as
  foreign ink — it is measured by the Befund and it is what the eye sees;
* inside the writer's verdict box a speck can fake a tick, and a faked tick
  files a row as accepted that the writer never accepted.

**The stored bytes are never modified.** That is the two-channel doctrine the
whole capture chain runs on (owner, 2026-08-27, `crop.without_rulings` is the
model): what was captured is what is filed, and every cleanup is a DERIVED
view computed on read. A speck is therefore removed by a MASK — a list of
circles in the row crop's own millimetres — that travels beside the Fassung
in `meta.json`, in the Kartei and in `eigenhand_fassungen.flecken`. Deleting
the mask brings the raw strip back, unchanged, byte for byte.

Two halves, one mechanism (the author asked for both):

* **auto** — what this module finds: isolated dark specks that stand clear of
  the writing. The rules below are deliberately timid. A missed speck costs
  one brush click; an erased i-dot destroys ground truth that cannot be
  recovered, because the strip is the primary evidence of a reserved dataset.
* **hand** — what the author paints in the workbench with a round brush. Same
  circles, same storage, only `quelle` differs.

WHAT THE AUTOMATIC PASS WILL NOT TOUCH

1. Anything that is not SMALL (`SPECK_MAX_EXTENT_MM`, `SPECK_MAX_AREA_MM2`).
2. Anything that touches the writing — a speck fused to a letter is one ink
   component with it, and one component is never split.
3. Anything nearer to the writing than `SPECK_CLEARANCE_MM`: commas, full
   stops, the dot of an `i`, a blot from the author's own nib all live there.
4. Anything standing ABOVE a letter within its horizontal extent — the
   geometric definition of a dot (`DOT_X_SLACK_MM`, `DOT_MAX_RISE_MM`), which
   survives even where a hand sets its i-dots unusually high.
5. Anything outside the writing window or on printed geometry — the strip id,
   the ruling, the clear-text label. Printed matter is not the writer's ink
   and erasing it would be a lie about the paper.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, NamedTuple

import numpy as np
from scipy.ndimage import distance_transform_edt, find_objects, label

from core.eigenhand.befund import INK_THRESHOLD, MEASURE_PAD_MM, printed_geometry_mask


FLECKEN_FORMAT = 1
QUELLEN = ("auto", "hand")

# --------------------------------------------------------------- the physics
# A toner speck is a single loose particle fused to the paper. Calibrated on
# the first real sheet (B0001, 2026-09-07, the author's HP colour laser scanned
# at 600 DPI): the particles measure 0.25–1.0 mm across and 0.02–0.41 mm² —
# the first ceiling of 0.6 mm, set before a real scan existed, left the two
# largest to the brush. The hand's own detached ink is a different size class
# altogether: with the M nib an i-dot is 1.0–1.4 mm² over 1.7–2.0 mm, a
# u-Bogen 2.3–2.5 mm². The ceilings sit between the two, and
# `WRITING_MIN_AREA_MM2` is the floor of the hand's class — so the size rule
# alone keeps an i-dot out, before clearance and position are even asked.
# What the printer drops beyond that (a smear of 1.8 mm² over 2.3 mm on the
# same sheet) stays the brush's: a ceiling raised to catch it would sit inside
# the i-dot's class, which is the wrong direction to be generous in.
SPECK_MAX_EXTENT_MM = 1.2
SPECK_MAX_AREA_MM2 = 0.6  # a filled disc of ~0.9 mm; the measured particles are elongated, not discs
# What counts as WRITING rather than as a dot. A Sütterlin `e` at 6 mm
# x-height draws some 15 mm of ink at ~0.4 mm width — about 6 mm²; an i-dot is
# ~0.13 mm². One square millimetre sits an order of magnitude away from both,
# so no letter is ever taken for a speck and no dot for a letter.
WRITING_MIN_AREA_MM2 = 1.0
# How far a speck has to stand clear of the writing before it may be masked.
# Four times the widest speck, and wider than the gap an i-dot keeps from its
# stem. Everything inside this radius is left to the eye: it is where the
# author's own punctuation, exit strokes and accidental blots live, and the
# automatic pass may miss a speck but must never invent one.
SPECK_CLEARANCE_MM = 2.5
# The dot exemption, on top of the clearance. A dot is defined by where it
# stands: over its letter, within the letter's horizontal extent. That is
# geometric and survives a hand that sets its i-dots unusually high, where a
# purely metric rule would not.
DOT_X_SLACK_MM = 0.8
DOT_MAX_RISE_MM = 5.0

# --------------------------------------------------------------- the circles
# The painted disc reaches a little past the speck's own extent: a fused
# particle has an anti-aliased rim that the ink threshold does not see but the
# eye does.
FLECK_PAD_MM = 0.15
FLECK_MIN_R_MM = 0.1
# The largest circle the hand brush may place. A whole word is 10 mm wide, so
# anything past this is no longer „a speck" but an attempt to erase writing —
# and the mask is not the place for that decision.
FLECK_MAX_R_MM = 3.0
FLECKEN_MAX = 500
# The fill is LOCAL paper, read off a ring around the circle rather than set
# to white: the strips are scans, their paper is neither white nor even, and a
# white disc on a scanned sheet reads as a hole. The median of the ring is the
# paper level there — by construction the ring holds no writing, because an
# automatic circle stands `SPECK_CLEARANCE_MM` clear of it.
FILL_RING_MM = 1.0
FILL_PERCENTILE = 50

# ------------------------------------------------------------- the tick box
# A tick is a STROKE, a speck is a dot. Both were read as „ink in the box"
# before the Fleckenmaske, and three specks in one box came to more than the
# 4 % a tick needs. So the reading drops isolated speck-sized components
# first, and then asks for an extent no dot can have.
MARK_MIN_FRACTION = 0.04
MARK_MIN_STROKE_MM = 1.5


class MarkReading(NamedTuple):
    """What the writer's verdict box says, with the printer's specks taken out.

    `fraction` is the inked share of the box interior AFTER the specks are
    dropped, `stroke_mm` the longest extent of the largest surviving
    component, and `specks` how many were dropped — which is what makes a
    faked tick visible instead of merely absent.
    """

    tick: bool
    fraction: float
    specks: int
    stroke_mm: float


def _ink_components(ink: np.ndarray) -> tuple[np.ndarray, int, list[tuple[slice, slice]]]:
    """Label the ink 8-connected — a diagonal chain of pixels is one speck."""
    labels, count = label(ink, structure=np.ones((3, 3), dtype=int))
    return labels, int(count), list(find_objects(labels)) if count else []


def writing_window(
    shape: tuple[int, int], row: Mapping[str, Any], x0_px: int, y0_px: int, px_per_mm: float
) -> np.ndarray:
    """True where a strip crop may be masked at all — the writing band, minus print.

    A Schnittband is taller than the writing: it starts above the printed strip
    id and ends below the clear-text word label, because a cut strip has to be
    attributable on its own (`geometry.cut_box`). Neither zone is the writer's
    ink, so neither is ever erased — the window is the Befund's own measuring
    window (one `MEASURE_PAD_MM` above the ascender line and below the
    descender line), with the printed geometry inside it taken out on top.

    `x0_px`/`y0_px` are the crop's origin in the rectified page, exactly as
    `printed_geometry_mask` takes them.
    """
    height, width = shape
    band = row["band_mm"]
    to_px = lambda mm: round(mm * px_per_mm)  # noqa: E731 — `ingest._px`, kept identical
    top = max(0, min(height, to_px(band["asc_top"] - MEASURE_PAD_MM) - y0_px))
    bottom = max(0, min(height, to_px(band["desc_bot"] + MEASURE_PAD_MM) - y0_px))
    window = np.zeros(shape, dtype=bool)
    window[top:bottom, :] = True
    return window & ~printed_geometry_mask(shape, row, x0_px, y0_px, px_per_mm)


def find_flecken(
    plane: np.ndarray, *, px_per_mm: float, detectable: np.ndarray | None = None, ink_threshold: float = INK_THRESHOLD
) -> list[dict[str, Any]]:
    """The specks of one row crop as circles in the crop's own millimetres.

    `plane` is the working plane of the crop (0 = black, 1 = paper) at
    `px_per_mm` — the same plane the import detects and QC's on. `detectable`
    marks where a circle may be placed at all (`writing_window`); without it
    the whole crop counts, which is what a synthetic test wants and what a
    caller without a layout row has.

    The coordinates are the CROP's, measured from its top-left corner in
    millimetres. That is what makes them portable: the stored strip is exactly
    this rectangle, so the same numbers place the circle in the DB image, in
    the archive copy and in the admin view without a page origin anywhere.
    """
    ink = plane < ink_threshold
    if detectable is not None:
        ink = ink & detectable
    labels, count, boxes = _ink_components(ink)
    if not count:
        return []
    px_mm2 = 1.0 / (px_per_mm * px_per_mm)
    sizes = np.bincount(labels.ravel())
    writing = np.zeros(labels.shape, dtype=bool)
    letters: list[tuple[slice, slice]] = []
    candidates: list[int] = []
    for index, window in enumerate(boxes, start=1):
        area_mm2 = float(sizes[index]) * px_mm2
        if area_mm2 >= WRITING_MIN_AREA_MM2:
            writing |= labels == index
            letters.append(window)
            continue
        rows, cols = window
        extent = max(rows.stop - rows.start, cols.stop - cols.start) / px_per_mm
        if area_mm2 <= SPECK_MAX_AREA_MM2 and extent <= SPECK_MAX_EXTENT_MM:
            candidates.append(index)
    if not candidates:
        return []
    # One distance transform for the whole crop instead of a pairwise scan: it
    # answers „how far is this pixel from the nearest letter" for every
    # candidate at once, and it measures to the letter's ink rather than to its
    # bounding box — an ascender's box would otherwise reach across a speck
    # that is nowhere near the stroke itself.
    to_writing = distance_transform_edt(~writing) if writing.any() else None
    circles: list[dict[str, Any]] = []
    for index in candidates:
        window = boxes[index - 1]
        if to_writing is not None:
            patch = to_writing[window][labels[window] == index]
            if patch.size and float(patch.min()) / px_per_mm < SPECK_CLEARANCE_MM:
                continue
        if _stands_over_a_letter(window, letters, px_per_mm):
            continue
        circles.append(_circle_of(window, px_per_mm))
    return circles


def _stands_over_a_letter(
    window: tuple[slice, slice], letters: Sequence[tuple[slice, slice]], px_per_mm: float
) -> bool:
    """Is this small component a dot — over a letter, inside its x-extent?

    The one shape of punctuation the clearance alone cannot protect: a hand
    that sets its i-dots high enough puts them past any distance a speck rule
    can use. Where the component stands says what it is.
    """
    rows, cols = window
    slack = DOT_X_SLACK_MM * px_per_mm
    rise = DOT_MAX_RISE_MM * px_per_mm
    for letter_rows, letter_cols in letters:
        overlaps = cols.start <= letter_cols.stop + slack and cols.stop >= letter_cols.start - slack
        above = rows.stop <= letter_rows.start and letter_rows.start - rows.stop <= rise
        if overlaps and above:
            return True
    return False


def _circle_of(window: tuple[slice, slice], px_per_mm: float) -> dict[str, Any]:
    """A found component as a circle. Always `auto` — the brush writes its own."""
    rows, cols = window
    centre_x = (cols.start + cols.stop) / 2 / px_per_mm
    centre_y = (rows.start + rows.stop) / 2 / px_per_mm
    half = max(rows.stop - rows.start, cols.stop - cols.start) / 2 / px_per_mm
    return {
        "x_mm": round(centre_x, 3),
        "y_mm": round(centre_y, 3),
        "r_mm": round(max(FLECK_MIN_R_MM, half + FLECK_PAD_MM), 3),
        "quelle": "auto",
    }


def check_circles(raw: Iterable[Mapping[str, Any]], *, width_mm: float, height_mm: float) -> list[dict[str, Any]]:
    """Validate a mask against the strip it belongs to; raise `ValueError` on any fault.

    The centre has to lie inside the strip — a circle whose disc overhangs the
    edge is fine and is simply clipped when painted, but a centre outside it is
    a coordinate system mix-up, and silently clamping one would put an eraser
    somewhere the author did not click.
    """
    circles = list(raw)
    if len(circles) > FLECKEN_MAX:
        raise ValueError(f"a Fleckenmaske holds at most {FLECKEN_MAX} circles, this one has {len(circles)}")
    out: list[dict[str, Any]] = []
    for position, circle in enumerate(circles):
        try:
            x_mm, y_mm, r_mm = (float(circle["x_mm"]), float(circle["y_mm"]), float(circle["r_mm"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"circle {position} needs numeric x_mm, y_mm and r_mm") from exc
        quelle = str(circle.get("quelle", "hand"))
        if quelle not in QUELLEN:
            raise ValueError(f"circle {position}: quelle must be one of {', '.join(QUELLEN)}, not {quelle!r}")
        if not FLECK_MIN_R_MM <= r_mm <= FLECK_MAX_R_MM:
            raise ValueError(f"circle {position}: r_mm {r_mm} is outside {FLECK_MIN_R_MM}…{FLECK_MAX_R_MM} mm")
        if not 0.0 <= x_mm <= width_mm or not 0.0 <= y_mm <= height_mm:
            raise ValueError(
                f"circle {position}: ({x_mm}, {y_mm}) mm lies outside the strip (0…{width_mm:.1f} × 0…{height_mm:.1f})"
            )
        out.append({"x_mm": round(x_mm, 3), "y_mm": round(y_mm, 3), "r_mm": round(r_mm, 3), "quelle": quelle})
    return out


def paint_out(plane: np.ndarray, circles: Sequence[Mapping[str, Any]], px_per_mm: float) -> np.ndarray:
    """A COPY of the plane with local paper painted into every circle.

    Works on a 2-D working plane and on an H×W×3 colour image alike, each
    channel taking its own paper level. The input array is never written to:
    this is a derived view, and the caller's pixels are the filed ones.
    """
    out = np.array(plane, copy=True)
    if not circles:
        return out
    height, width = out.shape[:2]
    for circle in circles:
        cx = float(circle["x_mm"]) * px_per_mm
        cy = float(circle["y_mm"]) * px_per_mm
        radius = float(circle["r_mm"]) * px_per_mm
        if radius <= 0:
            continue
        # Only the circle's own neighbourhood is touched — the ring the paper
        # level is read from is the outer bound, and a mask of 500 circles must
        # not cost 500 passes over a 2000-pixel-wide strip.
        ring_outer = radius + max(FILL_RING_MM * px_per_mm, 1.0)
        y0 = max(0, int(np.floor(cy - ring_outer)))
        y1 = min(height, int(np.ceil(cy + ring_outer)) + 1)
        x0 = max(0, int(np.floor(cx - ring_outer)))
        x1 = min(width, int(np.ceil(cx + ring_outer)) + 1)
        if y0 >= y1 or x0 >= x1:
            continue
        yy, xx = np.ogrid[y0:y1, x0:x1]
        distance = (xx - cx) ** 2 + (yy - cy) ** 2
        disc = distance <= radius * radius
        if not disc.any():
            continue
        ring = (distance <= ring_outer * ring_outer) & ~disc
        window = out[y0:y1, x0:x1]
        source = ring if ring.any() else ~disc
        if not source.any():
            continue
        if window.ndim == 3:
            for channel in range(window.shape[2]):
                window[..., channel][disc] = np.percentile(window[..., channel][source], FILL_PERCENTILE)
        else:
            window[disc] = np.percentile(window[source], FILL_PERCENTILE)
    return out


def flecken_index(kartei: Mapping[str, Any]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """`strip → Fassung → mask` off a Kartei — the shape both persistences speak.

    The same seam `befund_index` uses: the local `kartei.json` and the rows of
    `eigenhand_fassungen` collapse into one dict, so the workbench and the
    terminal read one mask and cannot disagree about which speck is gone.
    Fassungen without a mask are absent rather than empty — „nobody has looked"
    is not „nothing to erase".
    """
    out: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for strip, record in (kartei.get("strips") or {}).items():
        for fassung in record.get("fassungen", []):
            circles = fassung.get("flecken")
            if circles is not None:
                out.setdefault(strip, {})[fassung["id"]] = list(circles)
    return out


def read_mark(patch: np.ndarray, px_per_mm: float, ink_threshold: float = INK_THRESHOLD) -> MarkReading:
    """Read one verdict box, with the printer's specks subtracted.

    `patch` is the box INTERIOR (the printed outline already inset away), so
    everything dark in it is either the writer's tick or foreign ink. Isolated
    speck-sized components are dropped from the reading and counted; what is
    left has to cover `MARK_MIN_FRACTION` of the box AND reach across
    `MARK_MIN_STROKE_MM`, because a tick is a stroke and no accumulation of
    dots is.
    """
    if patch.size == 0:
        return MarkReading(tick=False, fraction=0.0, specks=0, stroke_mm=0.0)
    ink = patch < ink_threshold
    labels, count, boxes = _ink_components(ink)
    if not count:
        return MarkReading(tick=False, fraction=0.0, specks=0, stroke_mm=0.0)
    sizes = np.bincount(labels.ravel())
    px_mm2 = 1.0 / (px_per_mm * px_per_mm)
    specks = 0
    kept = 0
    stroke_mm = 0.0
    for index, window in enumerate(boxes, start=1):
        rows, cols = window
        area_mm2 = float(sizes[index]) * px_mm2
        extent = max(rows.stop - rows.start, cols.stop - cols.start) / px_per_mm
        if area_mm2 <= SPECK_MAX_AREA_MM2 and extent <= SPECK_MAX_EXTENT_MM:
            specks += 1
            continue
        kept += int(sizes[index])
        stroke_mm = max(stroke_mm, extent)
    fraction = kept / patch.size
    tick = fraction >= MARK_MIN_FRACTION and stroke_mm >= MARK_MIN_STROKE_MM
    return MarkReading(tick=tick, fraction=float(fraction), specks=specks, stroke_mm=float(stroke_mm))
