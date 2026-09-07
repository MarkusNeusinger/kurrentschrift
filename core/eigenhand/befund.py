"""Der Streifen-Befund — what one written Fassung looks like, in numbers.

The owner's question of 2026-09-07: „Ist es gut oder schlecht, wenn ich auch
nicht perfekte Buchstabenstreifen hochlade und wir mit unseren Tools eine
Sauberkeits-Analyse haben, und dann nach und nach Streifen durch sauberere
ersetzt werden?" — good, with a loop: write · scan · Befund · tick · rewrite
the weak ones. This module is the Befund half of it.

Three rules bind everything below.

1. **Nothing rejects automatically.** The Befund produces a `vorschlag`
   (`sauber` · `brauchbar` · `neu schreiben`) and the ONE reason that
   dominates it. The verdict on a Fassung stays the tick on the paper and the
   Siebung; no code here writes a status, and `status` is never read from a
   number (proposal §6, owner 2026-08-26).
2. **Cleanliness is judged the way the eye judges it.** Not absolute geometry
   against a template: continuity between the ductus landmarks (`core
   .continuity`, the frozen #558 arithmetic), whether the counters the script
   holds open are open, whether the ink is one run where the script joins.
   Distance to a reference letterform is deliberately NOT measured — the
   author's hand is the target, not a deviation from the plate.
3. **Ductus fidelity outranks smoothness.** What the follower (Phase 5) needs
   first is the right topology: the right counters, one body run per joined
   word. A smooth word with a shut `e` is worse training material than a
   slightly wobbly one with its loop open, and the dominance order below says
   so.

WHAT IT MEASURES, AND ON WHAT

The capture chain has no traced centreline yet — the fit/harvest connection is
Phase 5 and deferred (proposal §9). So the Befund reads the INK, which is what
a scanned strip actually carries: the binarised writing of one word box, its
medial axis, and the holes the ink encloses. Six fields:

* **`nib`** — the median half width on the medial axis, in x-heights. Read
  against the plate's own pen (`PLATE_PEN_HALF_WIDTH_UNITS`, the #551
  measurement) and, more importantly, against the hand's OWN median: a Fassung
  that differs from the rest of the campaign was written with a different pen
  or a different pressure, and photometric cohorts are exactly what the
  standing setup exists to keep whole (proposal §7.2).
* **`unstetigkeit`** — Knick, Wackler, Bogen and Krümmungsverlust from
  `core.continuity`, run per PEN RUN — the spur-pruned, re-spliced medial axis
  between two genuine topological events. That is what makes the sensor
  landmark-aware here for free: a run ends at an endpoint or a fork, so a
  measurement window can never straddle a crossing, a stroke end or a branch
  — the exemptions the word-level sensor has to compute are boundaries by
  construction. Getting a direction off written ink at all takes three steps
  with their own constants below (mask smoothing · spur pruning · sub-pixel
  re-centring on the grayscale); the last of them is what separates a real
  corner from the pixel raster, and the numbers that show it are at
  `RECENTRE_SEARCH_NIBS`.
* **`kringel`** — the loops the ink encloses, against the frozen per-loop
  expectation of the Kringel catalogue (#556): a counter the script holds
  `offen` that ran shut is a lost letter feature, a `wechselnd` one that
  closed is inside the tradition's own variation, a `punkt` one is a dot by
  construction. The expectation is the 1922 plate's, not this hand's — same
  script, another writer — and the payload says so (`quelle`), because an
  expectation from a foreign hand must never travel unlabelled.
* **`duktus`** — the topology agreement that a static scan CAN answer: how
  many separate body runs the ink has where the script joins into one, and how
  many counters were found against how many were expected. Crossings and
  retrace zones are deliberately absent: a retrace leaves one stroke of ink, so
  a picture cannot show one, and a crossing count off a scan skeleton is
  dominated by thinning artefacts. Both become measurable when the follower
  traces a strip (Phase 5) — that is the field's rescue path, not a gap to
  paper over.
* **`deckung`** — the gate, in the role §5's coverage gate plays for the
  Sütterlin metric: is this the right thing in the right place at all. Ink
  inside the ruled band, ink above and below it, and how dark the ink is (the
  `blass` axis the import already flags).
* **`lesbarkeit`** — the §5-SHAPED composite, `100 · G**0.5 · N`: the gate has
  to be decent, then naturalness drives the ranking. It is the number the
  Fassungen of one strip are ordered by, and nothing else. Note the deviation,
  which is deliberate and stated rather than hidden: §5 scores a RENDER
  against ink; here there is no render, so the ink is scored against the
  ruling and against itself. Same role, different reference.

NOT A BENCH NUMBER. No headline of any bench reads this — proposal §12
Prüfstein 2 („Trainingsdaten, kein Mess-Satz") holds unchanged, and the two
script metrics (`core.quality`, `core.quality_suetterlin`) are untouched. The
Befund orders one hand's own Fassungen against each other and says which one
to write again.

MEASURED VS DERIVED. What is stored per Fassung is the MEASUREMENT alone
(`measure_strip`, JSON-ready). `vorschlag`, `grund`, `guete` and the rank are
DERIVED on read (`befund`, `befunde_of_strip`) — the same doctrine as
`kartei.strip_state`: a rank changes the moment a better Fassung arrives, and
a stored rank would be wrong from that moment on. Terminal and workbench call
the same functions on the same Kartei-shaped dict, so they cannot disagree.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from core.continuity import KINK_THRESHOLD_DEG, kink_events, stroke_profile
from core.eigenhand.kartei import fassungen_of
from core.landmarks import PLATE_PEN_HALF_WIDTH_UNITS
from core.shaping import shape_word
from core.skeleton_graph import build_graph


BEFUND_FORMAT = 1

# --------------------------------------------------------------- reading ink
# Grayscale below this counts as ink. THE threshold of the capture chain, and
# the reason the sheet asks for black or brown ink: measured on the working
# plane, black sits at 0.10 and iron-gall brown at 0.14, while blue ink lands
# at 0.55 — exactly here (proposal §6). `tools/eigenhand/ingest.py` reads its
# QC flags with the same constant, imported from here rather than restated:
# two thresholds for "this is ink" is one threshold too many.
INK_THRESHOLD = 0.55
# Printed geometry (guide lines, box edges) is masked with this half width in
# mm before the import counts ink for its QC flags — the rulings are pale cyan
# and above the threshold anyway, but for a COUNT the mask is what makes that a
# guarantee instead of a hope.
LINE_MASK_MM = 0.4
# The Befund does NOT use that mask, and the reason is worth stating: a band
# line runs the whole width of a box, so masking it cuts every stroke that
# crosses it — which in joined handwriting is nearly every stroke. It would
# break the medial axis into pieces at four heights and destroy exactly the
# loops the Kringel field is about. The rulings do not need masking anyway:
# they are printed ABOVE the ink threshold on purpose (`geometry.CAPTURE_STYLES`
# — 0.91 to 0.97 in the blue plane against 0.55), so they are not ink by
# construction. What DOES have to be kept out is printed TEXT — the strip id in
# the Schnittband's top pad, the clear-text word label below the band — and the
# import's own QC window already excludes both. The Befund measures in that
# same window, one pad above the ascender line and one below the descender
# line, so ink that overshoots the ruling is still seen and printed matter
# never is. An overshoot beyond the pad is what the `beschnitten` QC flag says.
MEASURE_PAD_MM = 2.0

# ------------------------------------------------------- the measured floors
# A hole smaller than this in the raster is paper grain inside the ink, not a
# counter (`tools/tracebench/kringelcat.py` counts the plate's own with it).
HOLE_MIN_PX = 3
# …and a counter narrower than this is not one the eye sees. The same floor
# `tools/tracebench/kringel.py` drops raster splinters at — under half the
# plate pen's own width, where no pen writes an open loop and no reader sees
# one.
LOOP_MIN_INK_UNITS = 0.05
# A pen mark is at least as big as the disc the pen itself makes. Half of that
# disc is the floor for an ink component to count as a part rather than as a
# speck — generous, because the question a part count answers is "did the pen
# lift", and a speck must never answer it.
PART_MIN_DISC_FRACTION = 0.5
# The medial axis is quantised to the pixel raster, and a staircase of ±½ px
# read over the half-nib window of `core.continuity` is a heading noise of
# several degrees — enough to fake a Knick. So a skeleton edge is resampled to
# one point per pixel of arc and smoothed with a Gaussian of this many pixels
# before any direction is read. The residual staircase is then ~0.14 px, i.e.
# under 2° at the reading window, against an 11.5° threshold. The trade is
# stated rather than hidden: a real Knick is spread over ~4 px = 0.056 xh,
# still inside the 0.0725 xh reading window, so the sensor under-reads a sharp
# kink slightly and over-reads nothing — the conservative direction for a
# measurement that suggests rewriting a strip.
SKELETON_SMOOTH_PX = 2.0
# …and then the samples are re-centred SUB-PIXEL on the grayscale: at each
# sample the ink weight (`INK_THRESHOLD` minus the plane, clipped at zero) is
# integrated along the normal and the point moves to that cross-section's
# centroid, capped at one half width so a bad section cannot fling it away.
# This is the two-channel doctrine paying off — the anti-aliased intensity
# knows where the middle of the stroke is to a fraction of a pixel, which a
# binary thinning by construction cannot. It is what makes the sensor usable
# on written ink at all: on distance-field references at 300 dpi, smoothing
# alone left a clean arc at 15° of "Knick" (two false events) while reading a
# real 53° corner as 9° — under the threshold, so the one defect the owner
# names first would have been missed. With re-centring the same four
# references read 2.9° / 3.5° / 0.6° on the clean arc, circle and straight run
# (no events) and 36° on the corner (one event). A light second pass takes the
# noise the shift itself carries.
RECENTRE_SEARCH_NIBS = 1.5  # how far along the normal the cross-section is read
RECENTRE_SMOOTH_PX = 1.0
# Before that, the MASK itself is smoothed — by a Gaussian of this fraction of
# the measured half width, re-thresholded at ½. A pen cannot write a boundary
# feature finer than its own width, so smoothing at an eighth of the ink width
# removes only what no pen could have made; a Gaussian plus a ½ threshold is
# curvature-limited and leaves a straight or gently curved edge where it was.
# What it buys is not cosmetic: on one clean drawn arc the raw thinning gave
# 111 graph edges and a median half width of 4.1 px against a true 6.9 (the
# hairs sit near the boundary and drag the median down); at this scale it gives
# ONE edge and 6.7 px. It is applied ONLY where a DIRECTION is read — loops,
# parts, ink coverage and the empty test all run on the ink as captured, because
# a smoothing wide enough to unhair a skeleton is also wide enough to close the
# narrowest counter, and closing a counter is the very defect being measured.
MASK_SMOOTH_NIBS = 0.25
# Thinning a wide stroke whose boundary is a scan's jagged edge grows a SPUR at
# every bump: one clean drawn arc came out of `skeletonize` as 111 graph edges,
# of which the longest held a sixth of the path and two spurs read 17° and 21°
# of "Knick" that no pen ever wrote. A boundary bump of depth d grows a spur of
# about d, so a branch that ends free and is shorter than one full ink width is
# a thinning artefact and nothing else. Pruned iteratively — a spur can hide
# behind a spur — and the branches left over are then spliced back through the
# nodes the pruning freed, or the medial axis stays in pieces and every splice
# point becomes a stroke end the sensor cannot measure across.
SPUR_MAX_NIBS = 2.0

# ------------------------------------------------- the pre-registered bounds
# Every threshold below is anchored on a physical scale or on an existing,
# already-calibrated constant of this repo. None of them is fitted to the
# author's strips — there were none when they were written.
#
# Knick: the frozen #558 threshold, 11.537° — the angle at which a path leaves
# its smooth continuation by a tenth of the ink width over one reading window.
# One Knick in a word is worth a mention, three (or one at twice the angle) is
# a word to write again.
KINK_COUNT_NOTED = 1
KINK_COUNT_SEVERE = 3
KINK_ANGLE_SEVERE_FACTOR = 2.0
# Wackler: the same angle used as the yardstick for an RMS. A heading that
# wanders by half a Knick on average is noticeable; by a whole one, the line
# is not a line any more.
WOBBLE_NOTED_DEG = 0.5 * KINK_THRESHOLD_DEG
WOBBLE_SEVERE_DEG = KINK_THRESHOLD_DEG
# Krümmungsverlust: a flat spot shallower than half the ink width hides inside
# the stroke; one as deep as the whole ink width is a bow that became a chord.
CURV_NOTED_NIBS = 1.0  # in HALF widths, i.e. half the ink width
CURV_SEVERE_NIBS = 2.0
# Feder: nib sizes step by about 40 % at the bottom of the commercial ladder
# (0.5 → 0.7 mm). Half of the smallest step a pen change can produce is no
# longer „the same pen, another day"; a whole step is a different pen.
NIB_NOTED_DEVIATION = 0.20
NIB_SEVERE_DEVIATION = 0.40
# Kringel: one lost counter is a defect worth naming, two is a word whose
# letters have run shut.
LOOP_LOST_NOTED = 1
LOOP_LOST_SEVERE = 2
# Deckung: ink outside the ruled band. A tenth is a long ascender leaving the
# ruling, a third is a word that missed its line.
BAND_OUTSIDE_NOTED = 0.15
BAND_OUTSIDE_SEVERE = 0.30
# …and the darkness. `blass` is flagged by the import at a mean ink level of
# 0.45; above `INK_THRESHOLD` there is barely ink left to measure.
BLASS_NOTED = 0.45
BLASS_SEVERE = INK_THRESHOLD

# ------------------------------------------------------------- the composite
# The naturalness weights, in the shape of the §5 metric: the term that always
# applies and that the eye reads first carries the most.
W_KINK = 0.40
W_WOBBLE = 0.25
W_KRINGEL = 0.20
W_CURV = 0.15
# Decays: each maps a penalty onto a 0–1 quality through exp(−·).
KINK_COUNT_DECAY = 2.0  # two Knicke in one word cost a factor e
WOBBLE_DECAY_DEG = KINK_THRESHOLD_DEG  # an RMS of one Knick costs a factor e
CURV_DECAY_NIBS = 1.0  # a flat spot half the ink width deep costs a factor e
LOOP_LOST_PENALTY = 0.6  # per counter that ran shut
BAND_DECAY = 0.15  # a seventh of the ink outside the ruling costs a factor e
# The `blass` flag of the import lands exactly at a factor e: 0.45 is
# BLASS_TARGET + BLASS_DECAY. One number, two surfaces.
BLASS_TARGET = 0.25
BLASS_DECAY = BLASS_NOTED - BLASS_TARGET
BODY_BREAK_PENALTY = 0.5  # per body run more than the script joins into
GATE_EXPONENT = 0.5  # G**0.5 — as in the §5 composite

# The verdict vocabulary. German, because it is shown in the German admin and
# printed by the German report — and the author's own words for the defects.
VORSCHLAEGE = ("sauber", "brauchbar", "neu schreiben")
GRUND_NICHTS = "nichts fällt auf"
GRUND_STRICHFOLGE = "Strichfolge weicht ab"
GRUND_KRINGEL = "Kringel zu"
GRUND_KNICK = "Knick im Übergang"
GRUND_WACKELIG = "wackelig"
GRUND_FEDER_DUENN = "Feder zu dünn"
GRUND_FEDER_DICK = "Feder zu dick"
GRUND_ZEILE = "läuft aus der Zeile"
GRUND_BLASS = "zu blass"
# Rule 3 made executable: the topology comes first, the smoothness after it.
# A tie on severity is broken by this order, never by which number happened to
# be larger — the two are not on one scale.
GRUND_ORDER = (
    GRUND_STRICHFOLGE,
    GRUND_KRINGEL,
    GRUND_ZEILE,
    GRUND_KNICK,
    GRUND_WACKELIG,
    GRUND_BLASS,
    GRUND_FEDER_DUENN,
    GRUND_FEDER_DICK,
)


# ------------------------------------------------------------------ geometry


def printed_geometry_mask(shape: tuple[int, int], row: dict, x0_px: int, y0_px: int, px_per_mm: float) -> np.ndarray:
    """True where a rectified crop shows PRINTED geometry, not handwriting.

    The band lines and the box edges within `LINE_MASK_MM`, plus everything
    above the ascender line: that frame carries the strip id the sheet prints
    into the Schnittband's top pad, and counting its pixels would fake ink.
    `x0_px`/`y0_px` are the crop's origin in the rectified page, so the same
    function serves the import's QC crop and the Befund's word box.
    """
    mask = np.zeros(shape, dtype=bool)
    band = row["band_mm"]
    # Rounded, not truncated: this is `ingest._px`, and the QC mask and the
    # Befund mask have to fall on the same pixel row.
    to_px = lambda mm: round(mm * px_per_mm)  # noqa: E731 — one expression, used ten times below
    height, width = shape
    clamp_x = lambda value: max(0, min(width, value))  # noqa: E731
    clamp_y = lambda value: max(0, min(height, value))  # noqa: E731
    half = to_px(LINE_MASK_MM)
    above_band = to_px(band["asc_top"]) - y0_px - half
    if above_band > 0:
        mask[:above_band, :] = True
    # Both slice bounds are clamped, not just the lower one: the import's QC
    # crop spans every box of the row, so its box edges always land inside the
    # crop, but the Befund cuts ONE box — where a neighbouring box's edge sits
    # off the crop entirely and a raw negative stop would mask nearly all of it.
    for box in row["boxes"]:
        bx0, bx1 = to_px(box["x0_mm"]) - x0_px, to_px(box["x1_mm"]) - x0_px
        for y_mm in (band["asc_top"], band["waist"], band["baseline"], band["desc_bot"]):
            y = to_px(y_mm) - y0_px
            mask[clamp_y(y - half) : clamp_y(y + half + 1), clamp_x(bx0 - half) : clamp_x(bx1 + half + 1)] = True
        for x in (bx0, bx1):
            mask[:, clamp_x(x - half) : clamp_x(x + half + 1)] = True
    return mask


def _recentred(base: np.ndarray, plane: np.ndarray, half_px: float) -> np.ndarray:
    """Every sample moved onto its own ink cross-section's centroid.

    The normals come from the already-smoothed line, never from the raw
    samples: a normal read off a pixel staircase jitters, and a jittering
    search direction turns a sub-pixel correction into sub-pixel noise (it
    did, measurably — the same references got worse, not better).
    """
    from core.geometry import bilinear  # noqa: PLC0415 — core-internal, kept beside its one use

    step = np.gradient(base, axis=0)
    normal = np.column_stack([-step[:, 1], step[:, 0]])
    normal /= np.maximum(np.hypot(normal[:, 0], normal[:, 1]), 1e-9)[:, None]
    reach = max(RECENTRE_SEARCH_NIBS * half_px, 2.0)
    offsets = np.arange(-reach, reach + 1e-9, 0.5)
    weights = np.zeros((len(base), len(offsets)))
    for index, offset in enumerate(offsets):
        probe = base + normal * offset
        weights[:, index] = np.clip(INK_THRESHOLD - bilinear(plane, probe[:, 0], probe[:, 1]), 0.0, None)
    total = weights.sum(axis=1)
    shift = np.clip((weights * offsets).sum(axis=1) / np.where(total > 0, total, 1.0), -half_px, half_px)
    return base + normal * shift[:, None]


def _centreline(points: np.ndarray, plane: np.ndarray, half_px: float, unit_px: float) -> np.ndarray | None:
    """One pen run as a centreline in x-heights, raster noise taken out.

    Resampled to one sample per pixel of arc, Gaussian-smoothed over
    `SKELETON_SMOOTH_PX`, re-centred on the grayscale ink and lightly smoothed
    again — see the constants for why a direction cannot be read off the raw
    medial axis at all. Returns None for a run too short to carry a window.
    """
    from scipy.ndimage import gaussian_filter1d  # noqa: PLC0415 — scipy is heavy, this is one call site

    points = np.asarray(points, dtype=float)
    if len(points) < 2:
        return None
    seg = np.hypot(*np.diff(points, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(s[-1])
    if total < 2.0:  # under two pixels of arc there is no direction to read
        return None
    targets = np.linspace(0.0, total, max(2, int(round(total)) + 1))
    dense = np.column_stack([np.interp(targets, s, points[:, 0]), np.interp(targets, s, points[:, 1])])
    if len(dense) < 3:
        return dense / unit_px
    # `nearest` at the ends: `reflect` would fold the path back on itself and
    # invent a turn at every stroke end, which is where the ends are excluded
    # anyway — but an invented turn moves the samples INSIDE too.
    base = gaussian_filter1d(dense, SKELETON_SMOOTH_PX, axis=0, mode="nearest")
    centred = gaussian_filter1d(_recentred(base, plane, half_px), RECENTRE_SMOOTH_PX, axis=0, mode="nearest")
    return centred / unit_px


# ------------------------------------------------------------- the readings


def _ink_stats(plane: np.ndarray, ink: np.ndarray, band_px: tuple[int, int]) -> dict[str, float]:
    """Where the ink sits against the ruling, and how dark it is."""
    total = int(ink.sum())
    if not total:
        return {"tinte_px": 0, "im_band": 0.0, "ueber": 0.0, "unter": 0.0, "tinte_mittel": 1.0}
    top, bottom = band_px
    per_row = ink.sum(axis=1)
    above = int(per_row[: max(0, top)].sum())
    below = int(per_row[max(0, bottom) + 1 :].sum())
    return {
        "tinte_px": total,
        "im_band": round((total - above - below) / total, 4),
        "ueber": round(above / total, 4),
        "unter": round(below / total, 4),
        "tinte_mittel": round(float(plane[ink].mean()), 4),
    }


def _loops(ink: np.ndarray, unit_px: float) -> list[dict[str, float]]:
    """Every counter the ink encloses, with its clear aperture in x-heights.

    The ink hole, not the centreline loop: what the eye reads is the hole that
    is left, and that is what a written strip can show. The background is
    labelled 4-connected so an 8-connected curve really closes a hole — the
    same convention the plate's own counters are read with.
    """
    from scipy.ndimage import distance_transform_edt  # noqa: PLC0415
    from scipy.ndimage import label as cc_label  # noqa: PLC0415

    background = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)
    labels, count = cc_label(~ink, structure=background)
    if not count:
        return []
    border = set(labels[0, :]) | set(labels[-1, :]) | set(labels[:, 0]) | set(labels[:, -1])
    edt = distance_transform_edt(~ink)
    out: list[dict[str, float]] = []
    for index in range(1, count + 1):
        if index in border:
            continue
        sel = labels == index
        if int(sel.sum()) < HOLE_MIN_PX:
            continue
        dist = np.where(sel, edt, -1.0)
        flat = int(np.argmax(dist))
        aperture = 2.0 * float(dist.flat[flat]) / unit_px
        if aperture < LOOP_MIN_INK_UNITS:
            continue
        cy, cx = np.unravel_index(flat, dist.shape)
        out.append({"weite": round(aperture, 4), "x": round(float(cx) / unit_px, 4)})
    return sorted(out, key=lambda loop: loop["x"])


def _parts(ink: np.ndarray, unit_px: float, nib_px: float, band_px: tuple[int, int], waist_px: int) -> dict[str, int]:
    """The ink's connected components, split into body runs and floating marks.

    A component that reaches into the writing band is body — a letter run. One
    that floats entirely above the waist is a MARK (an i-dot, a u-Deckstrich,
    an umlaut), which the script writes with a lift by construction and which
    therefore says nothing about a broken run.
    """
    from scipy.ndimage import find_objects  # noqa: PLC0415
    from scipy.ndimage import label as cc_label  # noqa: PLC0415

    labels, count = cc_label(ink, structure=np.ones((3, 3), dtype=bool))
    floor = PART_MIN_DISC_FRACTION * np.pi * max(nib_px, 1.0) ** 2
    body = marks = other = 0
    top, bottom = band_px
    for index, window in enumerate(find_objects(labels), start=1):
        if window is None or int((labels[window] == index).sum()) < floor:
            continue
        y0, y1 = window[0].start, window[0].stop - 1
        if y1 < waist_px:
            marks += 1
        elif y1 >= top and y0 <= bottom:
            body += 1
        else:
            other += 1
    return {"koerper": body, "marken": marks, "sonstige": other, "unit_px": round(unit_px, 2)}


def _arc_px(points: np.ndarray) -> float:
    return float(np.hypot(*np.diff(np.asarray(points, dtype=float), axis=0).T).sum())


def _pruned_edges(skel: np.ndarray, spur_max_px: float) -> list[tuple[int, int, np.ndarray]]:
    """The skeleton's edges with the thinning spurs taken off, iteratively.

    A spur is a branch that ends FREE (one of its nodes carries no other edge)
    and is shorter than `spur_max_px`. Removing one can free the next, so the
    pass repeats until nothing more falls; an edge that is the last one left on
    its component is kept whatever its length — a short stroke is still a
    stroke, and only a BRANCH can be an artefact.
    """
    edges = [(edge.a, edge.b, edge.points) for edge in build_graph(skel).edges]
    while True:
        degree: dict[int, int] = {}
        for a, b, _points in edges:
            degree[a] = degree.get(a, 0) + 1
            degree[b] = degree.get(b, 0) + 1
        doomed = {
            index
            for index, (a, b, points) in enumerate(edges)
            if a != b
            and (degree[a] == 1 or degree[b] == 1)
            and max(degree[a], degree[b]) > 1
            and _arc_px(points) < spur_max_px
        }
        if not doomed:
            return edges
        edges = [edge for index, edge in enumerate(edges) if index not in doomed]


def _merged_paths(edges: list[tuple[int, int, np.ndarray]]) -> list[np.ndarray]:
    """Maximal pen runs: edges spliced through every node of degree two.

    After pruning, a node that used to carry a spur carries only two edges —
    and the medial axis through it is one continuous run. Splicing there is
    what turns a hairy graph back into the few long lines a sensor can read;
    without it, every removed spur would leave two stroke ends behind and the
    margins would eat the path.
    """
    incident: dict[int, list[int]] = {}
    for index, (a, b, _points) in enumerate(edges):
        incident.setdefault(a, []).append(index)
        if b != a:
            incident.setdefault(b, []).append(index)
    used: set[int] = set()
    out: list[np.ndarray] = []
    for start in range(len(edges)):
        if start in used:
            continue
        used.add(start)
        head, tail, chain = edges[start][0], edges[start][1], [edges[start][2]]
        for forward in (True, False):
            while True:
                node = tail if forward else head
                free = [i for i in incident.get(node, []) if i not in used]
                if len(incident.get(node, [])) != 2 or not free:
                    break
                used.add(free[0])
                a, b, points = edges[free[0]]
                if forward:
                    chain.append(points if a == node else points[::-1])
                    tail = b if a == node else a
                else:
                    chain.insert(0, points if b == node else points[::-1])
                    head = a if b == node else b
                if head == tail:
                    break
        line = np.vstack(chain)
        keep = np.concatenate([[True], np.abs(np.diff(line, axis=0)).sum(axis=1) > 1e-12])
        out.append(line[keep])
    return out


def _pen_runs(ink: np.ndarray) -> tuple[list[np.ndarray], float]:
    """The ink's readable medial axis, and the pen width measured on it.

    Three steps, each with its own constant above: smooth the mask at an eighth
    of the ink width so the thinning has no boundary hairs to follow, prune the
    spurs it still grows, splice what is left through the nodes the pruning
    freed. The nib is then read on THOSE pixels — the medial axis of the real
    runs — and not over every skeleton pixel, most of which belong to hairs
    when the hairs are still there.
    """
    from scipy.ndimage import distance_transform_edt, gaussian_filter  # noqa: PLC0415

    from core.extract import skeleton_and_width  # noqa: PLC0415 — pulls scikit-image

    edt = distance_transform_edt(ink)
    # The scale seed: for a stroke of half width h the distance transform runs
    # from 0 to h across the ink, so a high percentile of it is h up to a few
    # percent — an estimate that needs no skeleton and therefore cannot be
    # dragged down by the hairs the smoothing is there to prevent.
    seed_half = float(np.percentile(edt[ink], 95)) if ink.any() else 0.0
    sigma = MASK_SMOOTH_NIBS * seed_half
    smoothed = gaussian_filter(ink.astype(float), sigma) > 0.5 if sigma > 0.3 else ink
    if not smoothed.any():
        return [], seed_half
    skel, width_map = skeleton_and_width(smoothed)
    if not skel.any():
        return [], seed_half
    paths = _merged_paths(_pruned_edges(skel, SPUR_MAX_NIBS * 2.0 * max(seed_half, 1.0)))
    on_axis = [
        width_map[int(round(y)), int(round(x))]
        for path in paths
        for x, y in path
        if 0 <= int(round(y)) < width_map.shape[0] and 0 <= int(round(x)) < width_map.shape[1]
    ]
    nib_px = float(np.median(on_axis)) if on_axis else float(np.median(width_map[skel]))
    return paths, nib_px


def _continuity(paths: list[np.ndarray], plane: np.ndarray, half_px: float, unit_px: float) -> dict[str, Any]:
    """Knick · Wackler · Bogen · Krümmungsverlust over the medial axis.

    One reading per pen RUN — the spur-pruned, spliced medial axis between two
    genuine topological events (a stroke end or a fork). That is what makes
    the sensor landmark-aware here without computing an exemption: a run ends
    where the ductus event is, so no measurement window straddles one. A run
    too short to carry a window is not measured (`stroke_profile` returns
    None).
    """
    n_kinks = 0
    kink_vals: list[np.ndarray] = []
    wobble_vals: list[np.ndarray] = []
    bow_vals: list[np.ndarray] = []
    deficit_vals: list[np.ndarray] = []
    arc = 0.0
    for points in paths:
        line = _centreline(points, plane, half_px, unit_px)
        if line is None:
            continue
        profile = stroke_profile(line)
        if profile is None:
            continue
        measured = profile["inside"]
        if not measured.any():
            continue
        arc += float(profile["s"][-1])
        n_kinks += len(kink_events(profile["kink"], measured, profile["pts"], profile["s"]))
        kink_vals.append(profile["kink"][measured])
        wobble_vals.append(profile["wobble"][measured & profile["wobble_valid"]])
        bow_vals.append(profile["bow"][measured])
        deficit_vals.append(profile["deficit"][measured & profile["deficit_valid"]])
    if not kink_vals:
        return {
            "n_measured": 0,
            "bogenlaenge": 0.0,
            "kink_max_deg": None,
            "kink_count": 0,
            "wobble": None,
            "bow_median": None,
            "curv_loss": None,
        }
    kink_all = np.concatenate(kink_vals)
    wobble_all = np.concatenate(wobble_vals)
    deficit_all = np.concatenate(deficit_vals)
    return {
        "n_measured": int(len(kink_all)),
        "bogenlaenge": round(arc, 3),
        "kink_max_deg": round(float(kink_all.max()), 2),
        "kink_count": int(n_kinks),
        "wobble": round(float(np.sqrt(np.mean(wobble_all**2))), 3) if len(wobble_all) else None,
        "bow_median": round(float(np.median(np.concatenate(bow_vals))), 4),
        "curv_loss": round(float(deficit_all.max()), 4) if len(deficit_all) else None,
    }


# ------------------------------------------------------------------ the Soll


def word_glyph_keys(word: str) -> list[str]:
    """The word's glyph keys IN ORDER, repeats kept.

    Not `shaping.glyph_keys_of`, which dedupes — that answers "which templates
    does the composer fetch", and a Befund asks "which letters stand on the
    paper". `lesen` has two `e` there, and each of them carries its own loop.
    """
    return [slot.key for slot in shape_word(word) if slot.key and not slot.space]


def body_runs_expected(word: str) -> int:
    """How many joined runs the script writes this word in.

    The shaping's own `joins` flag decides: letters and ligatures join into one
    run, digits and punctuation are detached by construction (architektur.md
    §4 — connections are generated between letters only). So `lesen` is one
    run, `1922` is four and `ja!` is two — and a word whose ink falls into more
    pieces than that had a pen lift the ductus does not call for.
    """
    runs = 0
    joined = False
    for slot in shape_word(word):
        if slot.key is None or slot.space:
            joined = False
            continue
        if not (slot.joins and joined):
            runs += 1
        joined = slot.joins
    return max(1, runs)


def loop_expectation(word: str, catalogue: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    """The word's counters as the catalogue registers them, in reading order.

    `offen` is what a lost counter is counted against; `wechselnd` is tolerated
    open or shut (the plate itself closes those); `punkt` never enters, being a
    dot by construction. A glyph the catalogue does not know contributes
    nothing rather than a guess.
    """
    offen: list[str] = []
    tolerant = punkt = 0
    for key in word_glyph_keys(word):
        for index, row in enumerate(catalogue.get(key, ())):
            state = row.get("state")
            if state == "offen":
                offen.append(f"{key}#{index}")
            elif state == "wechselnd":
                tolerant += 1
            elif state == "punkt":
                punkt += 1
    return {"offen": offen, "wechselnd": tolerant, "punkt": punkt}


# --------------------------------------------------------------- measurement


def measure_word(
    plane: np.ndarray,
    row: dict,
    box_index: int,
    *,
    crop_origin_mm: Sequence[float],
    px_per_mm: float,
    catalogue: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Everything one written word box of a rectified strip says about itself.

    `plane` is the strip crop's working plane (0 = black, 1 = paper) at
    `px_per_mm`, `row` the Bogen's layout row (band + boxes in mm) and
    `crop_origin_mm` where the crop starts on the page — the same three the
    word-crop arithmetic of `core.eigenhand.crop` runs on.

    The box is cut WITHOUT padding: the box is where the word is supposed to
    stand, and a pad would pull the neighbour's ink into this word's reading.
    An exit stroke that reaches past the edge is measured with the next word
    instead — the union over the boxes is still the whole strip.
    """
    band = row["band_mm"]
    box = row["boxes"][box_index]
    word = str(box.get("word", ""))
    to_px = lambda mm: round(mm * px_per_mm)  # noqa: E731 — `ingest._px`, see above
    x_origin, y_origin = float(crop_origin_mm[0]), float(crop_origin_mm[1])
    height, width = plane.shape[:2]
    x0 = max(0, min(width - 1, to_px(box["x0_mm"] - x_origin)))
    x1 = max(x0 + 1, min(width, to_px(box["x1_mm"] - x_origin)))
    # The vertical window is the import's own QC window (see MEASURE_PAD_MM):
    # printed text is outside it, an overshooting ascender still inside.
    y0 = max(0, min(height - 1, to_px(band["asc_top"] - MEASURE_PAD_MM - y_origin)))
    y1 = max(y0 + 1, min(height, to_px(band["desc_bot"] + MEASURE_PAD_MM - y_origin)))
    cut = plane[y0:y1, x0:x1]
    ink = cut < INK_THRESHOLD

    unit_px = (band["baseline"] - band["waist"]) * px_per_mm
    band_px = (to_px(band["asc_top"] - y_origin) - y0, to_px(band["desc_bot"] - y_origin) - y0)
    waist_px = to_px(band["waist"] - y_origin) - y0
    out: dict[str, Any] = {
        "wort": word,
        "box": box_index,
        "unit_px": round(float(unit_px), 2),
        "deckung": _ink_stats(cut, ink, band_px),
    }
    if unit_px <= 0 or not ink.any():
        # An empty box is not measured further and is not scored: „leer" is a
        # QC flag the Siebung already shows, and inventing a naturalness for
        # no ink would rank a blank row against written ones.
        out["leer"] = True
        return out

    paths, nib_px = _pen_runs(ink)
    out["leer"] = False
    out["nib_units"] = round(nib_px / unit_px, 5)
    out["unstetigkeit"] = _continuity(paths, cut, nib_px, unit_px)
    out["teile"] = _parts(ink, unit_px, nib_px, band_px, waist_px)
    out["teile"]["koerper_soll"] = body_runs_expected(word) if word else 1
    found = _loops(ink, unit_px)
    out["kringel"] = {"gefunden": len(found), "weiten": [loop["weite"] for loop in found]}
    if catalogue is not None:
        expectation = loop_expectation(word, catalogue)
        # An order-preserving two-pointer match, not a per-loop identification:
        # within a word both the catalogue's loops and the ink's holes run in
        # reading order, so the holes consume the expected loops from the left
        # and whatever is left over could not be found. Naming WHICH counter
        # ran shut this way is a plausible attribution, never a measurement —
        # a per-loop identification needs the follower (Phase 5).
        budget = len(found)
        shut: list[str] = []
        for name in expectation["offen"]:
            if budget > 0:
                budget -= 1
            else:
                shut.append(name)
        out["kringel"].update(
            {
                "offen_soll": len(expectation["offen"]),
                "wechselnd_soll": expectation["wechselnd"],
                "punkt_soll": expectation["punkt"],
                "zu": len(shut),
                "zu_an": shut,
                "unerwartet": max(0, len(found) - len(expectation["offen"]) - expectation["wechselnd"]),
            }
        )
    return out


def measure_strip(
    plane: np.ndarray,
    row: dict,
    *,
    crop_origin_mm: Sequence[float],
    px_per_mm: float,
    catalogue: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    catalogue_quelle: str | None = None,
) -> dict[str, Any]:
    """The stored measurement of one Fassung: every word box of its strip.

    JSON-ready and nothing but numbers — this is what `apply` files beside the
    Fassung, what `sync` pushes and what the DB column holds. The verdict is
    NOT in here: it is derived on read (`befund`), so a rank can never go stale
    in storage.
    """
    words = [
        measure_word(plane, row, index, crop_origin_mm=crop_origin_mm, px_per_mm=px_per_mm, catalogue=catalogue)
        for index in range(len(row.get("boxes") or []))
    ]
    return {
        "format": BEFUND_FORMAT,
        "kringel_quelle": catalogue_quelle if catalogue is not None else None,
        "woerter": words,
    }


# ------------------------------------------------------------- the aggregate


def _weighted(values: list[tuple[float, float]]) -> float:
    """Weighted mean over the terms that applied, renormalised (as in §5)."""
    if not values:
        return 1.0
    return sum(weight * quality for weight, quality in values) / sum(weight for weight, _ in values)


def _summarise(measurement: Mapping[str, Any]) -> dict[str, Any]:
    """The per-word rows folded into one reading for the whole Fassung.

    The word that decides is the WORST one, not the average: a strip is
    rewritten because one word on it came out badly, and an average over four
    good words would hide exactly that. Only the pen width is a median — it is
    a property of the sitting, not of a word.
    """
    words = [w for w in measurement.get("woerter", []) if not w.get("leer", True)]
    leer = sum(1 for w in measurement.get("woerter", []) if w.get("leer"))
    if not words:
        return {"leer": leer, "gemessen": 0}
    nibs = [w["nib_units"] for w in words if w.get("nib_units")]

    def worst(path: tuple[str, ...], default: float = 0.0) -> float:
        found = []
        for word in words:
            node: Any = word
            for key in path:
                node = (node or {}).get(key) if isinstance(node, dict) else None
            if node is not None:
                found.append(float(node))
        return max(found) if found else default

    kinks = sum(int((w.get("unstetigkeit") or {}).get("kink_count") or 0) for w in words)
    zu = sum(int((w.get("kringel") or {}).get("zu") or 0) for w in words)
    offen_soll = sum(int((w.get("kringel") or {}).get("offen_soll") or 0) for w in words)
    unerwartet = sum(int((w.get("kringel") or {}).get("unerwartet") or 0) for w in words)
    body_extra = sum(
        max(0, int((w.get("teile") or {}).get("koerper") or 0) - int((w.get("teile") or {}).get("koerper_soll") or 1))
        for w in words
    )
    ink_total = sum(int((w.get("deckung") or {}).get("tinte_px") or 0) for w in words) or 1
    outside = sum(
        int((w.get("deckung") or {}).get("tinte_px") or 0)
        * (float((w.get("deckung") or {}).get("ueber") or 0.0) + float((w.get("deckung") or {}).get("unter") or 0.0))
        for w in words
    )
    darkness = sum(
        int((w.get("deckung") or {}).get("tinte_px") or 0) * float((w.get("deckung") or {}).get("tinte_mittel") or 1.0)
        for w in words
    )
    return {
        "leer": leer,
        "gemessen": len(words),
        "nib_units": round(float(np.median(nibs)), 5) if nibs else None,
        "kink_max_deg": worst(("unstetigkeit", "kink_max_deg")),
        "kink_count": kinks,
        "wobble": worst(("unstetigkeit", "wobble")),
        "curv_loss": worst(("unstetigkeit", "curv_loss")),
        "kringel_offen_soll": offen_soll,
        "kringel_zu": zu,
        "kringel_zu_an": [name for w in words for name in ((w.get("kringel") or {}).get("zu_an") or [])],
        "kringel_unerwartet": unerwartet,
        "koerper_zusaetzlich": body_extra,
        "ausserhalb": round(outside / ink_total, 4),
        "tinte_mittel": round(darkness / ink_total, 4),
        "tinte_px": ink_total,
    }


@dataclass(frozen=True)
class Befund:
    """One Fassung's verdict sheet — measured numbers plus the ONE reason.

    `vorschlag` is a SUGGESTION and never a status: the tick on the paper and
    the Siebung stay the verdict (proposal §6). `rang` is the Fassung's place
    among the accepted Fassungen of the SAME strip, best first; `abgeloest_von`
    names a later, better one where there is one, which is what makes the
    replacement loop visible without retiring anything by itself.
    """

    vorschlag: str
    grund: str
    guete: float
    nib: dict[str, Any] = field(default_factory=dict)
    unstetigkeit: dict[str, Any] = field(default_factory=dict)
    kringel: dict[str, Any] = field(default_factory=dict)
    duktus: dict[str, Any] = field(default_factory=dict)
    deckung: dict[str, Any] = field(default_factory=dict)
    lesbarkeit: dict[str, Any] = field(default_factory=dict)
    rang: int | None = None
    von: int | None = None
    abgeloest_von: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _decay(value: float, scale: float) -> float:
    return float(np.exp(-max(0.0, value) / scale)) if scale > 0 else 1.0


def befund(measurement: Mapping[str, Any] | None, *, nib_referenz: float | None = None) -> Befund | None:
    """Derive the verdict sheet from a stored measurement.

    `nib_referenz` is the hand's own median pen width; without one the plate's
    pen stands in, which answers "is this a plausible Sütterlin nib" rather
    than "is this the pen the rest of the campaign was written with". Returns
    None for a Fassung with no measurement at all (one filed before the Befund
    existed) — a missing reading is stated, never filled in.
    """
    if not measurement:
        return None
    summary = _summarise(measurement)
    if not summary.get("gemessen"):
        return Befund(vorschlag="neu schreiben", grund=GRUND_ZEILE, guete=0.0, deckung={"leer": summary.get("leer", 0)})

    reference = nib_referenz or PLATE_PEN_HALF_WIDTH_UNITS
    nib_units = summary["nib_units"] or 0.0
    zur_hand = nib_units / reference if reference else None
    nib = {
        "units": nib_units,
        "zur_tafel": round(nib_units / PLATE_PEN_HALF_WIDTH_UNITS, 3) if nib_units else None,
        "zur_hand": round(zur_hand, 3) if zur_hand else None,
        "referenz": round(reference, 5),
    }

    # --- the four naturalness terms, each a 0–1 quality ---
    q_kink = _decay(summary["kink_count"], KINK_COUNT_DECAY)
    q_wobble = _decay(summary["wobble"], WOBBLE_DECAY_DEG)
    q_curv = _decay(summary["curv_loss"] / max(nib_units, 1e-6), CURV_DECAY_NIBS)
    q_kringel = LOOP_LOST_PENALTY ** summary["kringel_zu"]
    terms = [(W_KINK, q_kink), (W_WOBBLE, q_wobble), (W_CURV, q_curv)]
    if summary["kringel_offen_soll"]:
        terms.append((W_KRINGEL, q_kringel))
    naturalness = _weighted(terms)

    # --- the gate: right thing, right place, dark enough ---
    q_band = _decay(summary["ausserhalb"], BAND_DECAY)
    q_dark = _decay(summary["tinte_mittel"] - BLASS_TARGET, BLASS_DECAY)
    q_body = BODY_BREAK_PENALTY ** summary["koerper_zusaetzlich"]
    gate = q_band * q_dark * q_body
    guete = 100.0 * (gate**GATE_EXPONENT) * naturalness

    # --- the defects, each with its severity; the worst one names the strip ---
    findings: list[tuple[int, str]] = []
    if summary["koerper_zusaetzlich"]:
        findings.append((2, GRUND_STRICHFOLGE))
    elif summary["kringel_unerwartet"]:
        findings.append((1, GRUND_STRICHFOLGE))
    if summary["kringel_zu"] >= LOOP_LOST_SEVERE:
        findings.append((2, GRUND_KRINGEL))
    elif summary["kringel_zu"] >= LOOP_LOST_NOTED:
        findings.append((1, GRUND_KRINGEL))
    if summary["kink_count"] >= KINK_COUNT_SEVERE or summary["kink_max_deg"] >= (
        KINK_ANGLE_SEVERE_FACTOR * KINK_THRESHOLD_DEG
    ):
        findings.append((2, GRUND_KNICK))
    elif summary["kink_count"] >= KINK_COUNT_NOTED:
        findings.append((1, GRUND_KNICK))
    if summary["wobble"] >= WOBBLE_SEVERE_DEG:
        findings.append((2, GRUND_WACKELIG))
    elif summary["wobble"] >= WOBBLE_NOTED_DEG:
        findings.append((1, GRUND_WACKELIG))
    if nib_units:
        curv_nibs = summary["curv_loss"] / nib_units
        if curv_nibs >= CURV_SEVERE_NIBS:
            findings.append((2, GRUND_WACKELIG))
        elif curv_nibs >= CURV_NOTED_NIBS:
            findings.append((1, GRUND_WACKELIG))
    if zur_hand:
        deviation = abs(zur_hand - 1.0)
        thin = GRUND_FEDER_DUENN if zur_hand < 1.0 else GRUND_FEDER_DICK
        if deviation >= NIB_SEVERE_DEVIATION:
            findings.append((2, thin))
        elif deviation >= NIB_NOTED_DEVIATION:
            findings.append((1, thin))
    if summary["ausserhalb"] >= BAND_OUTSIDE_SEVERE:
        findings.append((2, GRUND_ZEILE))
    elif summary["ausserhalb"] >= BAND_OUTSIDE_NOTED:
        findings.append((1, GRUND_ZEILE))
    if summary["tinte_mittel"] >= BLASS_SEVERE:
        findings.append((2, GRUND_BLASS))
    elif summary["tinte_mittel"] >= BLASS_NOTED:
        findings.append((1, GRUND_BLASS))

    severity = max((level for level, _ in findings), default=0)
    grund = (
        min((name for level, name in findings if level == severity), key=GRUND_ORDER.index)
        if findings
        else GRUND_NICHTS
    )
    return Befund(
        vorschlag=VORSCHLAEGE[severity],
        grund=grund,
        guete=round(guete, 1),
        nib=nib,
        unstetigkeit={
            "kink_max_deg": round(summary["kink_max_deg"], 2),
            "kink_count": summary["kink_count"],
            "wobble": round(summary["wobble"], 2),
            "curv_loss": round(summary["curv_loss"], 4),
        },
        kringel={
            "offen_soll": summary["kringel_offen_soll"],
            "zu": summary["kringel_zu"],
            "zu_an": summary["kringel_zu_an"],
            "unerwartet": summary["kringel_unerwartet"],
            "quelle": measurement.get("kringel_quelle"),
        },
        duktus={
            "koerper_zusaetzlich": summary["koerper_zusaetzlich"],
            "kringel_fehlend": summary["kringel_zu"],
            "kringel_zusaetzlich": summary["kringel_unerwartet"],
        },
        deckung={
            "ausserhalb": summary["ausserhalb"],
            "tinte_mittel": summary["tinte_mittel"],
            "tinte_px": summary["tinte_px"],
            "leer": summary["leer"],
            "gate": round(gate, 4),
        },
        lesbarkeit={"score": round(guete, 1), "natuerlichkeit": round(naturalness, 4), "gate": round(gate, 4)},
    )


# ------------------------------------------------------------------ ordering


def hand_nib_median(kartei: Mapping[str, Any]) -> float | None:
    """The hand's own pen width — the median over every measured Fassung.

    The consistency reference: a Fassung is compared against the campaign it
    belongs to, not against a plate written by somebody else a century ago.
    None while the hand has no measured Fassung yet, in which case the plate
    stands in and the Befund says so.
    """
    widths = [
        summary["nib_units"]
        for record in (kartei.get("strips") or {}).values()
        for f in record.get("fassungen", [])
        if f.get("status") == "angenommen"
        and (summary := _summarise(f.get("befund") or {}))
        and summary.get("nib_units")
    ]
    return float(np.median(widths)) if widths else None


def befunde_of_strip(kartei: Mapping[str, Any], strip: str, *, nib_referenz: float | None = None) -> dict[str, Befund]:
    """Every accepted Fassung of one strip, ranked best first.

    The rank is DERIVED here and never stored: a new Fassung reorders the
    strip, and a stored rank would be stale from the moment it arrives.
    `abgeloest_von` names the LATER Fassung that beats this one — the
    replacement loop made visible. It changes no count: the Bestand keeps
    counting every accepted Fassung as a Beleg (proposal §7), and taking one
    out of the training data stays the author's explicit
    `tools.eigenhand.redo --retire`.
    """
    accepted = [f for f in fassungen_of(kartei, strip) if f.get("status") == "angenommen"]
    scored = [(f["id"], befund(f.get("befund"), nib_referenz=nib_referenz)) for f in accepted]
    ranked = sorted(((fid, b) for fid, b in scored if b is not None), key=lambda pair: (-pair[1].guete, pair[0]))
    out: dict[str, Befund] = {}
    for place, (fid, scored_befund) in enumerate(ranked, start=1):
        # `ranked` runs best first, so the FIRST later id that also scores
        # higher is the best one that supersedes this Fassung. Equal scores do
        # not supersede: a rewrite that came out the same is not a replacement.
        better_later = next((other for other, ob in ranked if other > fid and ob.guete > scored_befund.guete), None)
        out[fid] = Befund(
            **{**scored_befund.as_dict(), "rang": place, "von": len(ranked), "abgeloest_von": better_later}
        )
    return out


def befund_index(kartei: Mapping[str, Any]) -> dict[str, dict[str, Befund]]:
    """`{strip: {fassung: Befund}}` for a whole hand, ranks and all.

    ONE call for both surfaces: the terminal report prints it, the API states
    it beside every stored strip. The pen reference is the hand's own median,
    computed once over the whole Kartei — so a Fassung's „Feder zu dünn" means
    thin for THIS hand.
    """
    reference = hand_nib_median(kartei)
    return {
        strip: found
        for strip in sorted(kartei.get("strips") or {})
        if (found := befunde_of_strip(kartei, strip, nib_referenz=reference))
    }


def weakest_fassungen(index: Mapping[str, Mapping[str, Befund]]) -> list[tuple[str, str, Befund]]:
    """`(strip, fassung, Befund)` worst first — the rewrite list.

    Only what the loop is about: a Fassung whose suggestion is not `sauber`.
    Sorted by suggestion severity, then by the composite, so the first rows of
    the report are the strips whose next writing gains the most.
    """
    rows = [
        (strip, fid, b) for strip, found in index.items() for fid, b in found.items() if b.vorschlag != VORSCHLAEGE[0]
    ]
    return sorted(rows, key=lambda row: (-VORSCHLAEGE.index(row[2].vorschlag), row[2].guete, row[0], row[1]))
