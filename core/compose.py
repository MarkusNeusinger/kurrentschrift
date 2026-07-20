"""Word composition geometry — Python port of the SPA's ``compose.ts``.

Lays a sequence of canonical glyphs along a shared baseline and generates the
connecting strokes (Übergänge) between them, so a whole word reads as one
continuous pen performance. Framework-free — consumes the per-glyph render
payloads (``core.pipeline.render_payload_for_template``: template-frame
centerlines, silhouette rings, entry point) and emits flat, render-ready draw
items in writing order (the client sweeps its reveal mask along them).

"Übergänge sind Konsequenz, keine Daten" (architektur.md §4): we never store a
bigram. A connector is a short cubic Bézier from glyph A's exit (point + travel
tangent measured on the RENDERED centerline) to glyph B's entry. Each glyph's
geometry stays in its own template frame (x origin at its first sample, y up,
baseline = 0); we only translate it horizontally by ``dx`` so its entry meets
the previous glyph's exit. Diacritic strokes — the marks floating above the
midband (i-/j-dot, the Sütterlin u-bow, the ä/ö/ü umlaut) — are deferred to the
end of their word; the join to the next letter leaves from the body's exit.

History: ported 1:1 from the SPA's ``compose.ts`` (PR #143, TS file deleted),
then deliberately evolved past it against the word bench (``tools/wordbench``,
same-hand specimens — see qualitaetsmetrik.md §6): ink-clearance spacing in
the join band, the backward-/high-exit rescues and the bow-launch clamp all
come from that loop. Pinned against accidental change by the golden regression
fixture (``tests/test_compose_golden.py``; re-baseline via ``REGEN_GOLDEN=1``).
"""

from __future__ import annotations

import math
import statistics

import numpy as np

from core.shaping import GlyphSlot
from core.template import chisel_union_rings, erase_silhouette_piece
from core.widths import PenStyle


SPACE_ADV = 0.55  # inter-word gap, x-height units
# Advance reserved for an unrenderable glyph — capped at the word gap, so a
# hole never yawns wider than an actual space.
MISSING_ADV = 0.55
# Ink clearance around a NON-JOINING glyph (digits, punctuation — slot.joins
# False): no Übergang enters or leaves it, the composer places it by ink
# clearance alone. Keyed by glyph_key base; the sentence marks hug their word
# (the plates set them tight), digits run at an even pitch narrower than the
# word gap. Between two detached glyphs the smaller clearance wins.
NONJOIN_CLEARANCE_DEFAULT = 0.24
NONJOIN_CLEARANCE: dict[str, float] = {
    "period": 0.12,
    "comma": 0.12,
    "semicolon": 0.14,
    "colon": 0.14,
    "apostrophe": 0.08,
    "quote-low": 0.14,
    "quote-high": 0.14,
    **{str(d): 0.16 for d in range(10)},
}
# Minimum horizontal span of a connecting stroke (exit → entry) for the
# clearance-based placement. The sawtooth pass-through alignment may
# deliberately place closer (its connector is the collinear middle piece of
# one continuous diagonal) — there the ALIGN_MIN_CLEARANCE ink floor bounds
# the span instead.
CONNECT_GAP = 0.16
# Minimum clearance between the previous glyph's rightmost body INK and the
# next glyph's leftmost body ink. The exit/entry anchors alone cannot carry the
# spacing rhythm: a bow that curls back (w, v) exits well LEFT of its rightmost
# ink, so an exit-anchored gap starts the next letter inside the bow — the
# words the bench flagged as far too narrow (einen/einer/wenn/zwei) all contain
# such exits, while exit≈ink-edge words (das, mit) were already sized right.
INK_CLEARANCE = 0.14
# Clearance when the previous exit tangent points BACKWARD (the w/v bow curls
# left at its end): there the join must travel over the whole bow before it
# can fall into the next entry — the plates give those pairs visibly more room
# (pairlab calibration 2026-07-11: w→e/i occurrences need +0.23 xh median on
# top of the composed spacing; the standard clearance already handled the
# audit's collapse, this widens it to the measured rhythm — 0.30 is the bench
# optimum of the 0.24–0.37 sweep, slightly under the raw calibration median).
BACKWARD_INK_CLEARANCE = 0.30
# The y-band the ink clearance is measured in: where connectors travel and the
# next letter's body sits. Ink above it (ascender loops) or below (descenders)
# may overlap the neighbour's column like on the teaching plates.
JOIN_BAND_Y = (-0.15, 0.8)
# Exit height above which the pen visibly REVERSES into the connector (the tall
# d finishes its loop upward; the join then drops next to the stem): follow the
# chord instead of the upward end tangent — the corner is authentic there.
HIGH_EXIT_Y = 1.05
# Midband-bow exits (Sütterlin b at ~0.98): the bow closes rising, but the pen
# flattens OUT of the bow into a level join that then falls into the next
# entry (the plates' Deckstrich-like connection) — following the rising end
# tangent instead humps the connector above the bow. Clamp the launch angle.
BOW_EXIT_Y = 0.7
BOW_LAUNCH_DEG = (-35.0, 5.0)
# The r-arm exception inside the bow band: a LOW pre-clamp tangent is the
# level Deckstrich arm ending in its knob (r ≈ +29°), not a closing bow
# (o ≈ +39°, b ≈ +44°). The plates write an Absatz there — the pen sets off
# the arm with a corner and falls steeply into the garland turn; rolling the
# crest like a bow reads as the V-notch wobble the jul09 join audit flagged
# (r→e 72°/65° seam kinks, worst connector of the corpus).
ARM_TAN_MAX_DEG = 33.0
ARM_FALL_DEG = -65.0
# Crest roll: when the bow-launch clamp bends a closing bow's rising tangent
# (b ≈ +44°, o ≈ +39°) down to the join's launch direction, the pen does not
# corner — it ROLLS over the crest. A short two-tangent arc from the ink
# tangent into the launch direction keeps the seam G1 (the "extra Zacken" of
# the jul09 audit at b→e/b→i was exactly this missing roll). Arc length in
# x-height units; 0 disables the roll.
CREST_ROLL_LEN = 0.09
CONNECT_SAMPLES = 24  # Bézier samples per connector (dense enough to read as a smooth arc)
# Entry coupling class — the school hand's e-vs-n rule: after a HIGH exit
# (r-arm, b/o bow, d loop) a round BODY (bowl or the e loop) is entered
# directly AT ITS TOP — the letter hangs from the covering join, the pen
# never dips first (verified on the plate originals: ren/roten/ihren/lieber
# Abb. 22, regieren/haben/das/do/der Abb. 19/20). Arcade letters (n m i u …)
# instead couple LOW through the baseline garland (bi, on originals do dip).
# A closed, enumerated set like NONJOIN_CLEARANCE — glyph_key bases.
HIGH_COUPLE_BASES = frozenset({"e", "a", "o", "c", "d", "g", "q", "ae", "oe"})
# Ascender-lean (R5): in BOUND context the school hand tilts the d loop 4-5°
# right of the upright chart cell — the slant sits above the midband, in the
# loop itself, while the midband stays ~90° (redesign §4: das 85.0°, der
# 86.25°, die 86.75°/87.0°, muß 86.5° full-height vs ~90° midband-only). A
# render-path rule like FLUENT_BODY_PITCH: the stored template remains the
# chart measurement, and a solitary (unbound) glyph renders chart-true.
# Class-based, d first; b/h/k measured separately (their loops did not show
# the lean in the §4 word table).
ASCENDER_LEAN_BASES = frozenset({"d"})
ASCENDER_LEAN_DEG = 4.5
# The lean is a property of FLOWING words: the isolated two-letter drills of
# Abb. 20 measure upright (§4: pairs full-height median 90.75° vs the leaning
# d-words of Abb. 19), so a run shorter than this stays chart-true.
ASCENDER_LEAN_MIN_RUN = 3
# Baseline garland — the join for ARCADE entries when a letter's stroke ends
# ABOVE where the next one begins. The plates show the pen leaving the exit,
# falling into a ROUNDED TURN near the Grundlinie and rising into the next
# letter's lead-in collinearly. The taut single cubic used to bridge such
# drops directly, which read as a V-notch / S-wobble at the seam (jul09 join
# audit: b→i 90°/77° seam kinks). Geometry + eligibility in
# ``_garland_centerline``: a fall cubic into a horizontal-tangent turn point
# plus a rise cubic that straightens into the entry tangent.
# How far down the lead-in line the pen merges: the merge point sits
# GARLAND_TURN_RATIO × (exit's perpendicular distance to the line) before the
# entry point — a close line (rb) is joined near the entry, a far one (r→e,
# d→e) is ridden from near its foot, which is exactly how the plates grade
# the depth of the turn.
GARLAND_TURN_RATIO = 0.8
# Exit closer than this (perpendicular) to the lead-in line: no garland, the
# plain taut cubic already merges shallowly — the plates join r→b/o→n with a
# small notch, not a full turn (jul10 sweep: garlanding those cost the pair
# bench ~+0.01 while the deep joins bi/Bi/rx/Of all gained).
GARLAND_MERGE_EPS = 0.40
# A strongly RISING launch is a sawtooth mid-rise exit (e, n, m …) — those
# letters already wrote their baseline turn; the connector only extends the
# diagonal and must NOT dip again.
GARLAND_MAX_LAUNCH_RISE = 0.35
GARLAND_MIN_DX = 0.05  # the merge point must sit right of the exit by at least this
# Word-final Endstrich (the finishing upswing of the school hand): the plates
# end a word by continuing the last letter's rising flank STRAIGHT up towards
# the Mittellinie (x-height line). Every Abb.-19 specimen word carries that
# stroke; the composed words lacked it — before the swing it was the largest
# single cause of the bench's width penalty on short words and of the n-final
# coverage signal (the swing's ink lies in the last letter's x-span; history
# in qualitaetsmetrik.md §6, Lauf jul08). A tangent-straight
# extension, generated at the word boundary, never stored — the transition
# into "nothing".
# Target height of the swing's end — SWING_MAX_RUN may cap a shallow exit's
# run short of it. Plate medians: n≈0.53, m/e≈0.6, r≈0.82; the jul10 composite
# sweep put the bench optimum at 0.55–0.6 (the old 0.7 overshot every word).
SWING_TOP_Y = 0.6
SWING_MAX_RUN = 0.9  # cap the horizontal run for shallow exits (x-height units)
# An exit still below the baseline (x's under-loop) flicks up only briefly —
# the plates never draw the full upswing there (dx/vx audit, jul10).
SWING_DEEP_MAX_RUN = 0.35
SWING_MIN_RISE = 0.2  # a flat/falling exit does not swing (needs a rising flank to continue)
# The LOW-exit Endstrich is not a straight continuation: it leaves along the
# exit tangent and FLATTENS towards the end (a long, gently convex upswing —
# the jul09 audit measured runs of ~0.5 x-heights ending near level, while
# the straight swing stopped after ~0.2). End direction of that curve:
SWING_END_DEG = 25.0
# Only a LOW forward exit swings up: a bow/Deckstrich exit (o, b, w) already
# ends high. A high FORWARD exit (the r-arm) instead runs level off the word —
# the plates extend the arm as a flat Auslauf (wordbench: der/der-2 carried the
# largest width penalties, 0.31/0.48, because the composed r stopped at the arm
# end); above SWING_MAX_EXIT_Y that level Auslauf replaces the upswing.
SWING_MAX_EXIT_Y = 0.7
SWING_HIGH_RUN = 0.25  # arc run of the level Auslauf (bench optimum of 0.15–0.65, xh units)
SWING_HIGH_LAUNCH_DEG = (-5.0, 15.0)  # level-ish band the Auslauf is clamped into
SWING_HIGH_MAX_TANGENT_DEG = 45.0  # a bow still closing steeply upward gets no Auslauf
DEFAULT_HALF = 0.05  # fallback stroke half-width
# Exit y (baseline = 0, descender ≈ −1) below which a glyph's stroke is judged
# to end inside its descender loop, so the connector becomes a return upstroke
# rather than following the downward exit tangent (see the long-s ſ).
DESCENDER_EXIT_Y = -0.2
# A HIGH exit is a coupling-stub tip, not the pen's true departure: the plates
# tuck the next letter back LEFT under it, proportionally to the exit height
# (pairlab independent-fit calibration, 2026-07-11: d-loop joins need −0.33 xh
# at exit_y 1.36, low arcade exits ~0). Constants are the bench-sweep optimum
# (rate 0.25–0.55 × y0 0.3–0.75, re-swept after the coupling anchor landed);
# the re-measured calibration halves the d-class error and drops joins needing
# ≥ 0.25 xh correction from 31 to 21 of 146. The ink-clearance guard still
# floors the placement, so the tuck can never push a letter into the previous
# body. Mid-height stub exits (c, t, f at ~0.5 xh) stay wrong on purpose:
# height alone cannot tell their stubs from a real arcade end at the same
# height (e, n) — that separation is the coupling-anchor work (O2,
# uebergaenge-befund.md §6).
TUCK_RATE = 0.35
TUCK_Y0 = 0.6
# Coupling anchor after a HIGH exit (O2, uebergaenge-befund.md §5b): when the
# previous letter leaves from a Deckstrich bow, a d-loop or the r-arm
# (exit ≥ HIGH_COUPLE_EXIT_Y), the plates' join falls in ONE diagonal onto the
# rising flank of the next letter's first downstroke — the chart cell's
# half-height entry stub is REPLACED by the join, not extended (measured
# head adaptation 0.14–0.43 xh of arc; fitted arrivals y 0.58–0.70). The
# connector therefore targets the first sample of B's first stroke at
# ENTRY_COUPLE_Y and the stub piece below it is trimmed — centerline and
# silhouette (see erase_silhouette_piece). Word-initial stubs stay: they ARE
# the Anstrich (E2 finding, qualitaetsmetrik.md §6), and low arcade exits keep
# the full stub too — there the connector IS the entry upstroke and lands on
# its foot (befund §4: the standard diagonal is generically right).
# 0.78 is the bench optimum (0.6/0.66/0.72/0.78/0.84 sweep), a touch above
# the fitted arrivals (0.58–0.70) — the join lands on the upper flank.
HIGH_COUPLE_EXIT_Y = 0.7
ENTRY_COUPLE_Y = 0.78
# Sawtooth pass-through alignment: when the previous letter hands over
# mid-rise and the next begins mid-rise (both tangents inside the diagonal
# band), the plates run ONE continuous diagonal from the previous baseline
# turn into the next letter — no shelf. Placement then PULLS the next glyph
# left onto the exit's rise line (never below the ALIGN_MIN_CLEARANCE ink
# floor), so the taut connector degenerates to the collinear middle piece.
# Backward (w/v), bow (o/b), arm (r) and descender exits never qualify —
# their tangent is not a diagonal.
ALIGN_TAN_DEG = (25.0, 55.0)
ALIGN_MIN_RISE = 0.02  # entry must sit above the exit for a pass-through
# Shared by the sawtooth pass-through AND the R4 "nested fall" placement (a
# rising mid-band exit whose neighbour enters below it — t's bar, f's flag —
# nests over the next letter instead of clearing its full ink column; the
# jul17 sweep put the nested floor exactly at the align floor, and shrinking
# the connect gap on top of it never bound).
ALIGN_MIN_CLEARANCE = 0.06
# The plates couple slightly FLATTER than the letters' internal diagonals (a
# subtle set-off remains between two sawtooth letters) — pull onto a line of
# this fraction of the mean tangent slope, not the full slope.
ALIGN_SLOPE_RATIO = 0.8
# Tall lead-ins (h 0.69, t 0.70 …) sweep in long and flat on the plates —
# alignment on their steep landing tangent over-pulls; leave them to the
# clearance placement.
ALIGN_MAX_ENTRY_Y = 0.62
# Straight-fit flank coupling — the "ne kink": between two sawtooth diagonals
# whose entry FOOT sits at/below the exit's rise line, no spacing can ever
# make the connector collinear (pulling closer only steepens it DOWNWARD) —
# the taut cubic then runs visibly flatter than both ink tangents (n→e chord
# −7° between 41°/39° flanks, e→n 23°, n→n 13° on the golden payloads). The
# plates instead run the ONE diagonal into the RISING FLANK of the next
# letter's lead-in and absorb the stub below it (befund §5b: arcade arrivals
# y 0.47–0.67 @ +31…+52°, i.e. mid-flank, not the foot). The connector
# becomes the straight middle piece of that diagonal: it couples at the first
# flank sample on/above the exit's rise line and the lead-in below the
# coupling point is trimmed — centerline and silhouette, the same O2
# mechanism as the high-exit couple. Where the entry foot sits at/below the
# exit (rise < ALIGN_MIN_RISE) the PLACEMENT is solved too, in two stages:
#
# 1. FUSION (``_fused_flank_placement``): the join continues the stroke
#    direction ITSELF — the pair is pushed together until the line through
#    the exit at the FULL mean ink tangent (no ALIGN_SLOPE_RATIO flattening:
#    a flattened line is near-parallel to the flank and can never reach it,
#    and its different slant was exactly the user-visible kink) meets the
#    rising lead-in flank. The connector degenerates to a short collinear
#    piece; the strokes fuse. The column ink floor cannot judge such a
#    placement (fusing stroke ends overlap by design), so legitimacy comes
#    from a HEIGHT-AWARE clearance guard (``_fused_clearance_ok``): per
#    y-bin over the join band, B's trimmed ink must clear A's ink by
#    ALIGN_MIN_CLEARANCE — except inside the fusion band around
#    [exit_y, couple_y] (± FUSE_BAND_PAD), where the joining strokes are
#    MEANT to share ink.
# 2. Fallback (``_flank_couple_steepest``): when the fused placement is
#    rejected, place at the stub-relaxed column floor (band ink LEFT of the
#    entry foot is the stub's own silhouette — absorbed by the trim, it must
#    not hold the pair apart) and couple at the top of the flank window: the
#    steepest straight join the ink allows, instead of a down-dipping cubic.
#
# Guards: only mid-band forward-diagonal exits (high exits keep their own
# coupling), BOTH tangents inside ALIGN_TAN_DEG, the flank must still rise
# diagonally at the coupling point (a head bending into its loop is a real
# form), the coupling point stays below ALIGN_MAX_ENTRY_Y, the pen must gain
# height and progress rightward — and the entry foot must not sit more than
# FLANK_COUPLE_MAX_DROP below the exit: a genuinely lower entry is the
# nested-fall class (t's bar, f's flag), whose gentle S-join is authentic
# (E6-verworfen straightening stays verworfen — qualitaetsmetrik.md §6).
FLANK_COUPLE_MAX_DROP = 0.05
FUSE_MIN_DX = 0.02  # a fused coupling still progresses rightward past the exit
FUSE_BAND_PAD = 0.12  # height pad around [exit_y, couple_y] where fusing ink may overlap
FUSE_CLEAR_BINS = 9  # y-bins of the height-aware clearance guard over JOIN_BAND_Y
# Travel direction measured over a short ARC-LENGTH window rather than the
# single final segment — the glyph centerline is a smooth spline through the
# anchors, so its true endpoint tangent rarely matches the stored single-chord
# anchor tangent; the window also rejects the jitter of one short segment.
TANGENT_WINDOW = 0.12  # x-height units (matches the corner-detection window)

Point = tuple[float, float]


def _unit(deg: float) -> Point:
    r = math.radians(deg)
    return (math.cos(r), math.sin(r))


def _key_base(key: str | None, position: str | None) -> str:
    """The glyph_key without its position suffix (`comma-final` → `comma`)."""
    if not key:
        return ""
    suffix = f"-{position}"
    return key[: -len(suffix)] if position and key.endswith(suffix) else key


def _joined_run_length(slots: list[GlyphSlot], index: int) -> int:
    """Length of the contiguous joined letter run around ``index`` — bound
    context is a property of the text (an unauthored neighbour still counts),
    never of template availability."""

    def _joins(i: int) -> bool:
        s = slots[i]
        return not s.space and bool(s.key) and bool(s.joins)

    if not _joins(index):
        return 0
    length = 1
    for step in (-1, 1):
        i = index + step
        while 0 <= i < len(slots) and _joins(i):
            length += 1
            i += step
    return length


def _lean_stroke(pts: list, shear: float, pivot_y: float) -> list[Point]:
    """Shear the stroke's above-``pivot_y`` part rightward (continuous at the
    pivot, identity below it)."""
    return [(x + shear * max(0.0, y - pivot_y), y) for x, y in pts]


def _nonjoin_clearance(base: str) -> float:
    return NONJOIN_CLEARANCE.get(base, NONJOIN_CLEARANCE_DEFAULT)


def _endpoint_tangent(line: list[Point], at_end: bool = False) -> float:
    """Travel direction (degrees, y up) entering (start) or leaving (end) a polyline.

    Entering = the pen's heading away from the first sample; leaving = its
    heading into the last sample, each measured over TANGENT_WINDOW of arc so
    the connector leaves/enters exactly tangent to the rendered ink (G1 at the
    join — the chord tangent of the stored anchors reads as a kink).
    """
    n = len(line)
    if n < 2:
        return 0.0
    tip = line[n - 1] if at_end else line[0]
    far = line[n - 2] if at_end else line[1]
    acc = 0.0
    if at_end:
        for i in range(n - 1, 0, -1):
            acc += math.hypot(line[i][0] - line[i - 1][0], line[i][1] - line[i - 1][1])
            far = line[i - 1]
            if acc >= TANGENT_WINDOW:
                break
    else:
        for i in range(n - 1):
            acc += math.hypot(line[i + 1][0] - line[i][0], line[i + 1][1] - line[i][1])
            far = line[i + 1]
            if acc >= TANGENT_WINDOW:
                break
    a, b = (far, tip) if at_end else (tip, far)
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _entry_couple_index(line: list[Point]) -> int:
    """Coupling-anchor index on B's first stroke for a high-exit join: the
    first sample reaching ENTRY_COUPLE_Y on the RISING entry flank. 0 = no
    trim: the stroke already starts at/above the couple height, it turns
    downward before reaching it (then its head is a real form, not a stub),
    or only the stroke's very last sample reaches it — the trimmed line must
    keep at least two samples for the entry-tangent estimate.
    """
    if len(line) < 3 or line[0][1] >= ENTRY_COUPLE_Y:
        return 0
    for i in range(1, len(line) - 1):
        if line[i][1] >= ENTRY_COUPLE_Y:
            return i
        if line[i][1] < line[i - 1][1]:
            return 0
    return 0


def _flank_candidates(first_line: list[Point]) -> list[int]:
    """Couple-able window of B's first stroke for the straight-fit coupling.

    Indices of the rising, diagonal-banded lead-in prefix (1 … n−2, so a
    trimmed line always keeps two samples for the entry tangent), stopping
    where the flank turns down or leaves ALIGN_TAN_DEG (a real head form, not
    a stub) or passes ALIGN_MAX_ENTRY_Y.
    """
    out: list[int] = []
    for i in range(1, len(first_line) - 1):
        p, q = first_line[i - 1], first_line[i]
        if q[1] < p[1]:
            break
        seg_deg = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        if not (ALIGN_TAN_DEG[0] <= seg_deg <= ALIGN_TAN_DEG[1]):
            break
        if q[1] > ALIGN_MAX_ENTRY_Y:
            break
        out.append(i)
    return out


def _flank_couple_index(first_line: list[Point], dx: float, exit_pt: Point, slope: float) -> int:
    """Coupling index on B's rising lead-in at a FIXED placement ``dx``.

    The first couple-able sample on/above the exit's rise line. 0 = no
    coupling: the foot already sits on/above the line (the pass-through
    placement owns that case), the flank ends before reaching the line, or
    the crossing gains no height / no rightward progress over the exit.
    """
    ex, ey = exit_pt

    def rise_over_line(p: Point) -> float:
        return (p[1] - ey) - slope * ((p[0] + dx) - ex)

    if not first_line or rise_over_line(first_line[0]) >= 0:
        return 0
    for i in _flank_candidates(first_line):
        q = first_line[i]
        if rise_over_line(q) >= 0:
            if q[1] < ey + ALIGN_MIN_RISE or (q[0] + dx) - ex < GARLAND_MIN_DX:
                return 0
            return i
    return 0


def _fused_flank_placement(
    first_line: list[Point], exit_pt: Point, slope: float, entry_x: float
) -> tuple[float, int] | None:
    """Entry-x placement + coupling index FUSING B's flank onto the exit line.

    The inverse of ``_flank_couple_index``: instead of intersecting the line
    with the flank at a fixed placement, solve for the placement — push the
    pair together until the line through the exit at the full mean ink
    tangent ``slope`` meets B's rising lead-in flank (the user-visible "ne"
    case: the entry foot sits at/below the exit, so no spacing can put the
    FOOT on the line, but a flank sample can — the strokes then continue as
    ONE diagonal). Returns ``(entry_x_placement, couple_index)`` for the
    LOWEST couple-able sample — least trim wins, the authored form is kept
    as far down as possible. No ink floor here: a fused placement is judged
    by the height-aware ``_fused_clearance_ok`` guard instead. None: no
    couple-able sample gains height and FUSE_MIN_DX rightward progress.
    """
    ex, ey = exit_pt
    for i in _flank_candidates(first_line):
        q = first_line[i]
        if q[1] < ey + ALIGN_MIN_RISE:
            continue
        run = (q[1] - ey) / slope  # composed x-distance exit → coupling point
        if run < FUSE_MIN_DX:
            continue
        return ex + run - q[0] + entry_x, i
    return None


def _band_bin(y: float) -> int:
    """Y-bin index of the height-aware clearance guard over JOIN_BAND_Y."""
    frac = (y - JOIN_BAND_Y[0]) / (JOIN_BAND_Y[1] - JOIN_BAND_Y[0])
    return min(FUSE_CLEAR_BINS - 1, max(0, int(frac * FUSE_CLEAR_BINS)))


def _fused_clearance_ok(
    a_profile: list[float],
    b_centerlines: list[list[Point]],
    diacritic_flags: list[bool],
    trim: int,
    dx: float,
    margin: float,
    exempt: tuple[float, float],
) -> bool:
    """Height-aware ink clearance for a fused flank placement.

    The column floor cannot judge a fusion (the joining stroke ends overlap
    in x by design), so collision is checked per y-bin instead: B's trimmed
    body ink (centerlines shifted by ``dx``, widened by ``margin``; stroke 0
    from the coupling index) must clear A's per-bin rightmost ink
    ``a_profile`` by ALIGN_MIN_CLEARANCE — except in the ``exempt`` height
    band around the join, where the fusing strokes are meant to share ink.
    """
    b_min = [math.inf] * FUSE_CLEAR_BINS
    for si, cl in enumerate(b_centerlines):
        if si < len(diacritic_flags) and diacritic_flags[si]:
            continue
        for x, y in cl[trim:] if si == 0 else cl:
            if JOIN_BAND_Y[0] <= y <= JOIN_BAND_Y[1]:
                b = _band_bin(y)
                b_min[b] = min(b_min[b], x)
    span = JOIN_BAND_Y[1] - JOIN_BAND_Y[0]
    for b in range(FUSE_CLEAR_BINS):
        if not math.isfinite(a_profile[b]) or not math.isfinite(b_min[b]):
            continue
        y_mid = JOIN_BAND_Y[0] + (b + 0.5) * span / FUSE_CLEAR_BINS
        if exempt[0] <= y_mid <= exempt[1]:
            continue
        if b_min[b] - margin + dx - a_profile[b] < ALIGN_MIN_CLEARANCE:
            return False
    return True


def _flank_couple_steepest(first_line: list[Point], dx: float, exit_pt: Point) -> int:
    """Fallback coupling index when no exact collinear fit clears the floor:
    the HIGHEST couple-able flank sample at the fixed placement ``dx`` — the
    steepest straight join the ink allows (still capped at
    ALIGN_MAX_ENTRY_Y by the candidate walk). 0 = no couple-able sample.
    """
    ex, ey = exit_pt
    best = 0
    for i in _flank_candidates(first_line):
        q = first_line[i]
        if q[1] >= ey + ALIGN_MIN_RISE and (q[0] + dx) - ex >= GARLAND_MIN_DX:
            best = i
    return best


def _straight_connector(p0: Point, first_line: list[Point], dx: float, couple_index: int) -> list[Point]:
    """The straight collinear middle piece from A's exit onto B's flank sample."""
    target: Point = (first_line[couple_index][0] + dx, first_line[couple_index][1])
    return [
        (p0[0] + (target[0] - p0[0]) * i / CONNECT_SAMPLES, p0[1] + (target[1] - p0[1]) * i / CONNECT_SAMPLES)
        for i in range(CONNECT_SAMPLES + 1)
    ]


def _sample_bezier(p0: Point, p1: Point, p2: Point, p3: Point, n: int) -> list[Point]:
    out: list[Point] = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0]
        y = u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]
        out.append((x, y))
    return out


def _garland_centerline(p0: Point, d_out: Point, p3: Point, d_in: Point) -> list[Point] | None:
    """Baseline-garland join (see the GARLAND_* constants): a fall cubic that
    kisses the lead-in line (through the entry along its tangent) at the merge
    point, then a straight ride along that line into the entry — the cubic's
    natural dip just below the merge IS the rounded turn of the school hand.
    Returns None whenever the geometry does not call for a garland — the
    caller falls back to the taut cubic (mid-rise sawtooth exits, descender
    returns, rising joins, no room).
    """
    if d_in[1] <= 0.2 or d_in[0] <= 0.0:
        return None  # entry stroke not a rising lead-in
    if p0[1] < DESCENDER_EXIT_Y:
        return None  # a descender return-upstroke rises, it never dips again
    if d_out[1] > GARLAND_MAX_LAUNCH_RISE:
        return None  # exit still mid-rise: extend the diagonal, don't dip again
    if p3[0] - p0[0] <= 2 * GARLAND_MIN_DX:
        return None
    # Signed perpendicular distance of the exit ABOVE the lead-in line
    # (through p3 along d_in): cross(d_in, p0 − p3) > 0 ⇔ exit left of/above
    # the rising line — only then is there a turn to write.
    d_perp = d_in[0] * (p0[1] - p3[1]) - d_in[1] * (p0[0] - p3[0])
    if d_perp <= GARLAND_MERGE_EPS:
        return None
    # Merge point: GARLAND_TURN_RATIO × d_perp down the lead-in line before
    # the entry, kept right of the exit so the pen always progresses.
    lam = GARLAND_TURN_RATIO * d_perp
    lam = min(lam, (p3[0] - p0[0] - GARLAND_MIN_DX) / d_in[0])
    if lam <= 0.0:
        return None
    m: Point = (p3[0] - lam * d_in[0], p3[1] - lam * d_in[1])

    # Fall cubic: leave along the (already rescue-clamped) launch direction,
    # kiss the lead-in line at the merge point tangentially — its natural dip
    # just below the merge IS the rounded garland turn of the school hand.
    fall_span = math.hypot(m[0] - p0[0], m[1] - p0[1])
    fall_dx = m[0] - p0[0]
    h_out = max(0.03, min(fall_span * 0.4, fall_dx * 0.6))
    h_in = max(0.03, min(fall_span * 0.4, fall_dx * 0.6))
    fall = _sample_bezier(
        p0, (p0[0] + h_out * d_out[0], p0[1] + h_out * d_out[1]), (m[0] - h_in * d_in[0], m[1] - h_in * d_in[1]), m, 18
    )
    # Ride the lead-in line straight into the entry point.
    ride = [(m[0] + (p3[0] - m[0]) * t / 6, m[1] + (p3[1] - m[1]) * t / 6) for t in range(1, 7)]
    return fall + ride


def _apply_pen(item: dict, centerline: list[Point], default_width: float, pen: PenStyle | None) -> None:
    """Ink a GENERATED stroke (connector, Endstrich) with the style's pen.

    No pen / constant: the Gleichzug capsule — one stroke_width (today's
    behaviour, byte-identical). pressure: a Haarstrich — generated strokes
    never carry pressure (Spitzfeder physics), so the pooled hairline caps
    the width. broad_nib: the swept Bandzugfeder ships as filled rings
    (the client fills rings and never strokes them); the centerline stays
    for the reveal mask, widened to cover the nib's asymmetric extent.
    """
    stroke_width = default_width
    if pen is not None and pen.kind == "pressure" and pen.hairline_half is not None:
        stroke_width = min(stroke_width, 2 * pen.hairline_half)
    item["stroke_width"] = stroke_width
    item["mask_width"] = stroke_width * 1.3
    if pen is not None and pen.kind == "broad_nib" and pen.nib is not None:
        pts = np.asarray(centerline, dtype=float)
        item["rings"] = chisel_union_rings(pts[:, 0], pts[:, 1], pen.nib, simplify_tol=0.002)
        item["mask_width"] = max(item["mask_width"], pen.nib.width_units * 1.15)


def _endstrike_centerline(p0: Point, tangent_deg: float) -> list[Point] | None:
    """Word-final Endstrich centerline, or None when the exit does not swing.

    A LOW rising exit writes the finishing upswing (see SWING_TOP_Y) as a
    two-tangent quadratic that leaves along the last glyph's exit flank and
    flattens to SWING_END_DEG towards the target height, truncated at
    SWING_MAX_RUN (SWING_DEEP_MAX_RUN after a below-baseline exit). A HIGH
    forward exit (the r-arm, a Deckstrich cover-stroke) runs a short level
    Auslauf instead (SWING_HIGH_RUN). Backward or flat-low exits do not swing
    (None) and end the word as they are.
    """
    d_out = _unit(tangent_deg)
    if p0[1] >= SWING_MAX_EXIT_Y:
        # High forward exit (r-arm, Deckstrich): a short level Auslauf
        # along the arm — the plates draw no rising flourish this high.
        launch = math.degrees(math.atan2(d_out[1], d_out[0]))
        if d_out[0] <= 0 or launch > SWING_HIGH_MAX_TANGENT_DEG:
            return None
        d_run = _unit(min(max(launch, SWING_HIGH_LAUNCH_DEG[0]), SWING_HIGH_LAUNCH_DEG[1]))
        p3: Point = (p0[0] + SWING_HIGH_RUN * d_run[0], p0[1] + SWING_HIGH_RUN * d_run[1])
        return [p0, ((p0[0] + p3[0]) / 2, (p0[1] + p3[1]) / 2), p3]
    # Low rising exit: the finishing upswing as a two-tangent quadratic
    # that leaves along the exit tangent and flattens to SWING_END_DEG
    # at the top: run = rise × mean of the two cotangents. A flat or
    # falling exit has no rising flank to continue.
    if d_out[0] <= 0 or d_out[1] < SWING_MIN_RISE:
        return None
    rise = SWING_TOP_Y - p0[1]
    if rise <= 0:
        return None
    cot_out = d_out[0] / d_out[1]
    cot_end = 1.0 / math.tan(math.radians(SWING_END_DEG))
    run = rise * (cot_out + cot_end) / 2
    if run <= 0:
        return None
    p3 = (p0[0] + run, p0[1] + rise)
    # Control point: intersection of the two tangent lines (exists
    # because the directions differ; fall back to the midpoint when
    # nearly parallel).
    d_end = _unit(SWING_END_DEG)
    denom = d_out[0] * d_end[1] - d_out[1] * d_end[0]
    ctrl: Point = ((p0[0] + p3[0]) / 2, (p0[1] + p3[1]) / 2)
    if abs(denom) > 1e-9:
        t = ((p3[0] - p0[0]) * d_end[1] - (p3[1] - p0[1]) * d_end[0]) / denom
        if 0.0 < t and p0[0] < p0[0] + t * d_out[0] < p3[0]:
            ctrl = (p0[0] + t * d_out[0], p0[1] + t * d_out[1])
    centerline = [
        (
            (1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * ctrl[0] + t * t * p3[0],
            (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * ctrl[1] + t * t * p3[1],
        )
        for t in (i / 10 for i in range(11))
    ]
    # Truncate at the run cap — a deep exit ends its swing mid-curve.
    # The cap point is interpolated so a coarse sample step can never
    # carry the stroke (and ink_max_x) past the cap.
    run_cap = SWING_MAX_RUN if p0[1] >= 0 else SWING_DEEP_MAX_RUN
    limit = p0[0] + run_cap
    kept: list[Point] = [centerline[0]]
    for a, b in zip(centerline, centerline[1:], strict=False):
        if b[0] <= limit:
            kept.append(b)
            continue
        if a[0] < limit and b[0] > a[0]:
            t = (limit - a[0]) / (b[0] - a[0])
            kept.append((limit, a[1] + t * (b[1] - a[1])))
        break
    if len(kept) < 2:
        return None
    return kept


def _connector_centerline(
    exit_pt: Point,
    exit_tangent_deg: float,
    first_line: list[Point],
    dx: float,
    *,
    high_couple: bool,
    flank_trim: int = 0,
) -> tuple[list[Point], int]:
    """Centerline of the Übergang from A's exit into B's entry + the entry trim.

    All the rescue/clamp/garland/crest geometry factored out of ``compose_word``.
    ``entry_trim`` is how many lead-in samples B's first stroke drops when a HIGH
    exit couples onto its rising flank (O2/ENTRY_COUPLE_Y); the caller applies
    the same cut to B's centerline + silhouette. ``flank_trim`` is the coupling
    index of a straight-fit flank placement decided by the CALLER
    (``_fused_flank_placement`` / ``_flank_couple_steepest``) — the connector
    then IS the straight collinear middle piece of the shared diagonal.
    """
    entry_trim = 0
    p0: Point = exit_pt
    # A HIGH exit couples onto the rising flank of B's first downstroke
    # instead of the entry-stub foot (O2, see ENTRY_COUPLE_Y): the stub
    # piece below the anchor is dropped from centerline AND silhouette.
    if p0[1] >= HIGH_COUPLE_EXIT_Y:
        entry_trim = _entry_couple_index(first_line)
    elif flank_trim:
        # Placement already solved the pair distance so B's flank sample sits
        # exactly on the exit's rise line — draw that line.
        return _straight_connector(p0, first_line, dx, flank_trim), flank_trim
    elif ALIGN_TAN_DEG[0] <= exit_tangent_deg <= ALIGN_TAN_DEG[1]:
        # Straight-fit flank coupling (see the constant block at ALIGN_*): a
        # sawtooth exit whose rise line passes ABOVE the next letter's entry
        # foot couples mid-flank instead — the connector is the straight
        # collinear middle piece of one continuous diagonal, the lead-in stub
        # below the coupling point is absorbed by it.
        land_deg = _endpoint_tangent(first_line, at_end=False)
        if ALIGN_TAN_DEG[0] <= land_deg <= ALIGN_TAN_DEG[1]:
            slope = ALIGN_SLOPE_RATIO * math.tan(math.radians((exit_tangent_deg + land_deg) / 2))
            entry_trim = _flank_couple_index(first_line, dx, p0, slope)
            if entry_trim:
                return _straight_connector(p0, first_line, dx, entry_trim), entry_trim
    couple_line = first_line[entry_trim:]
    # End exactly on the next glyph's first ink sample so the join sits
    # on the centerline the entry tangent is measured from.
    p3: Point = (couple_line[0][0] + dx, couple_line[0][1])
    span = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
    d_out = _unit(exit_tangent_deg)
    # A glyph whose stroke ends deep in its descender loop (the long-s ſ)
    # exits pointing downward — there the connector IS the return
    # upstroke: aim it at the next entry instead of continuing the
    # descent. Glyphs that finish a descender properly exit above the
    # baseline, so the guard never fires for them. The same rescue
    # applies to a BACKWARD exit tangent (the Sütterlin w/v bow curls
    # left at its end): a pen travelling to the next letter always
    # progresses rightward — following the curl loops the connector
    # around the bow (the "wovon" collapse from the 2026-07 audit).
    backward = d_out[0] <= 0.0
    # A HIGH exit (tall d finishing its loop upward) reverses into the
    # join — a real corner on the plates, so the chord is truthful.
    high_reversal = p0[1] > HIGH_EXIT_Y and p3[1] < p0[1]
    rescued = ((p0[1] < DESCENDER_EXIT_Y and d_out[1] < 0) or backward or high_reversal) and span > 0
    if rescued:
        d_out = ((p3[0] - p0[0]) / span, (p3[1] - p0[1]) / span)
    # The entry tangent is measured from the COUPLED lead-in (the stub
    # dropped after a high exit, O2/ENTRY_COUPLE_Y); the bow-launch
    # clamp of the jul11 branch is subsumed by the crest-roll block
    # below, which clamps the same bow band and rolls the seam.
    entry_deg = _endpoint_tangent(couple_line, at_end=False)
    d_in = _unit(entry_deg)
    # Perpendicular distance of the exit above the lead-in line — the
    # garland trigger (see GARLAND_MERGE_EPS); also gates the r-Absatz:
    # a close line is joined with the shallow notch of the taut cubic.
    d_perp = d_in[0] * (p0[1] - p3[1]) - d_in[1] * (p0[0] - p3[0])
    crest: list[Point] = []
    if not rescued and BOW_EXIT_Y < p0[1] <= HIGH_EXIT_Y and p3[1] < p0[1]:
        launch = math.degrees(math.atan2(d_out[1], d_out[0]))
        if launch < ARM_TAN_MAX_DEG and d_perp > GARLAND_MERGE_EPS and not high_couple:
            # r-arm Absatz: corner off the arm, steep fall (see ARM_*).
            d_out = _unit(ARM_FALL_DEG)
        elif launch > BOW_LAUNCH_DEG[1]:
            d_orig = d_out
            d_out = _unit(min(max(launch, BOW_LAUNCH_DEG[0]), BOW_LAUNCH_DEG[1]))
            if CREST_ROLL_LEN > 0:
                # Roll over the crest (see CREST_ROLL_LEN): a short
                # two-tangent arc keeps the bow seam G1; the join
                # proper then launches from the roll's end.
                half = CREST_ROLL_LEN / 2
                ctrl = (p0[0] + half * d_orig[0], p0[1] + half * d_orig[1])
                roll_end = (ctrl[0] + half * d_out[0], ctrl[1] + half * d_out[1])
                crest = [
                    (
                        (1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * ctrl[0] + t * t * roll_end[0],
                        (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * ctrl[1] + t * t * roll_end[1],
                    )
                    for t in (i / 5 for i in range(6))
                ]
                p0 = roll_end
    # An ARCADE entry that must LOSE height writes as a baseline
    # garland (the school hand's rounded turn); a round body couples
    # high instead and everything else stays the taut cubic.
    centerline = None if high_couple else _garland_centerline(p0, d_out, p3, d_in)
    if centerline is None:
        span = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
        if high_couple and p3[1] < p0[1] and span > 0:
            # Land ON the body's top from above: the authored rising
            # Anstrich is absorbed by the covering join on the plates
            # (ren/roten/das originals) — following it would dip
            # below the entry and rise back, the very notch the
            # garland audit set out to remove.
            d_in = ((p3[0] - p0[0]) / span, (p3[1] - p0[1]) / span)
        hspan = abs(p3[0] - p0[0])
        handle = max(0.05, min(span * 0.4, hspan * 0.5))
        p1: Point = (p0[0] + handle * d_out[0], p0[1] + handle * d_out[1])
        p2: Point = (p3[0] - handle * d_in[0], p3[1] - handle * d_in[1])
        centerline = _sample_bezier(p0, p1, p2, p3, CONNECT_SAMPLES)
    if crest:
        centerline = crest + centerline[1:]
    return centerline, entry_trim


def compose_word(
    slots: list[GlyphSlot],
    data_by_key: dict[str, dict | None],
    *,
    pen: PenStyle | None = None,
    provenance: bool = False,
    pair_overrides: dict[tuple[str, str], dict] | None = None,
) -> dict:
    """Compose shaped slots + per-glyph render payloads into draw items.

    Returns ``{"items", "bounds", "guides", "missing"}`` — one draw item per
    stroke/connector in writing order. A glyph item carries filled silhouette
    ``rings``; a connector carries a constant ``stroke_width`` (the Sütterlin
    Gleichzug; a Schwellzug taper is Phase D). Both carry the ``centerline``
    the renderer sweeps its reveal mask along (``mask_width`` wide), a ``lift``
    flag (a pen lift precedes this item → short pause) and ``diacritic`` on the
    deferred floating marks.

    ``pen`` (default None = today's Gleichzug behaviour, byte-identical)
    selects how GENERATED strokes are inked (see ``apply_pen``): pressure
    caps them at the pooled Haarstrich, broad_nib sweeps the Bandzugfeder and
    ships the join as filled ``rings``. Non-joining slots (``slot.joins``
    False — digits, punctuation) render detached: no connector enters or
    leaves them, placement is by ink clearance (``NONJOIN_CLEARANCE``), the
    preceding letter run ends like a word (Endstrich + diacritic flush).

    ``provenance=True`` (diagnostics only) additionally tags every glyph item
    with ``slot_index``/``glyph_key`` and every connector with ``from_slot``/
    ``to_slot``/``pair=[prev_key, curr_key]``, so a downstream ruler can
    attribute a deviation to a letter or a specific join. Default off — the
    public ``/write/word`` payload and the golden fixture stay byte-identical.

    ``pair_overrides`` (redesign R3 / Vorschlag B) maps an adjacent joined
    key pair ``(left_key, right_key)`` to a stored override geometry (the
    APPROVED `glyph_pairs` rows, fetched by the word endpoint):

    - ``offset``: ``[dx, dy]`` — where the right glyph's entry point lands
      relative to the LEFT glyph's exit point (template units; the composer
      currently applies the horizontal part — vertical placement stays on the
      shared baseline).
    - ``connector``: ``[[x, y], …]`` — the join's centerline relative to the
      left glyph's exit point, drawn verbatim instead of the generated
      Übergang (same pen/width treatment as a generated connector).

    Overrides resolve left-to-right (the advance is carried forward), so two
    adjacent overrides never conflict: each constrains only its right glyph.
    ``None``/no matching pair keeps the generator path byte-identical.
    """
    items: list[dict] = []
    missing: list[str] = []
    guides: dict | None = None
    cursor_x = 0.0
    # The previous glyph's exit in the composed frame, for the next connector.
    prev: dict | None = None

    min_x = math.inf
    max_x = -math.inf
    min_y = math.inf
    max_y = -math.inf

    def track(pts: list[Point]) -> None:
        nonlocal min_x, max_x, min_y, max_y
        for x, y in pts:
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

    # Diacritic strokes are held back until the current word is finished, then
    # flushed in encounter (left-to-right) order — the writer dots the i's and
    # sets the umlauts after the word body, not mid-flow. Each becomes its own
    # pen-down (lift) so the renderer pauses before placing it.
    pending_diacritics: list[dict] = []

    def flush_diacritics() -> None:
        for it in pending_diacritics:
            it["lift"] = True
            items.append(it)
        pending_diacritics.clear()

    def end_swing() -> None:
        """Emit the word-final Endstrich (geometry in ``_endstrike_centerline``)."""
        nonlocal cursor_x
        if not prev or not prev["joins"]:
            return
        centerline = _endstrike_centerline(prev["exit"], prev["tangent_deg"])
        if centerline is None:
            return
        swing: dict = {"centerline": [list(p) for p in centerline], "lift": False}
        _apply_pen(swing, centerline, 2 * prev["width"], pen)
        if provenance:
            swing["pair"] = [prev["key"], None]
            swing["from_slot"] = prev["slot_index"]
            swing["to_slot"] = None
        items.append(swing)
        track(centerline)
        cursor_x = centerline[-1][0]
        # The swing's ink extends the word rightward — a detached mark placed
        # next (comma, period) must clear it, not the letter body alone.
        prev["ink_max_x"] = max(prev["ink_max_x"], centerline[-1][0])

    for slot_index, slot in enumerate(slots):
        if slot.space:
            end_swing()  # the pen finishes the word body before the marks and the gap
            flush_diacritics()  # the word's marks land before the gap to the next word
            cursor_x += SPACE_ADV
            prev = None
            continue
        data = data_by_key.get(slot.key) if slot.key else None
        centerlines = (data or {}).get("centerlines_template")
        if not data or not centerlines:
            if slot.key:
                if slot.key not in missing:  # repeated letters share one key now
                    missing.append(slot.key)
                if not slot.joins:
                    # A DETACHED glyph is a run boundary even while its
                    # template is unauthored: the word before a missing comma
                    # still earns its Endstrich (matching the pre-registry
                    # null-key behaviour for punctuation).
                    end_swing()
            else:
                # A null-key slot (a character with no glyph at all) is a real
                # word boundary in the slot stream — the word before it earns
                # its Endstrich. A MISSING LETTER, in contrast, is a mid-word
                # hole and must not fake one.
                end_swing()
            # Either way the writing run breaks like a space: flush the marks
            # gathered so far, so a preceding i-dot/umlaut lands at the end of
            # its word.
            flush_diacritics()
            cursor_x += MISSING_ADV
            prev = None
            continue
        if guides is None:
            guides = data["template_guides"]

        rings_by_stroke = data.get("outline_paths") or []
        # Ascender-lean (R5): tilt the loop of a BOUND d to the measured axis.
        # Applied to the shared payload's copies — centerlines, silhouette
        # rings and entry alike — before any exit/ink measurement, so every
        # downstream consumer sees one consistent glyph.
        if (
            slot.joins
            and _key_base(slot.key, slot.position) in ASCENDER_LEAN_BASES
            and _joined_run_length(slots, slot_index) >= ASCENDER_LEAN_MIN_RUN
        ):
            shear = math.tan(math.radians(ASCENDER_LEAN_DEG))
            pivot_y = (data.get("template_guides") or {}).get("midband", 1)
            centerlines = [_lean_stroke(cl, shear, pivot_y) for cl in centerlines]
            rings_by_stroke = [[_lean_stroke(ring, shear, pivot_y) for ring in rings] for rings in rings_by_stroke]

        # A detached glyph (digit, punctuation — slot.joins False) closes the
        # letter run before it like a word boundary: the body earns its
        # Endstrich and the word's floating marks land before the mark is
        # written.
        if not slot.joins and prev and prev["joins"]:
            end_swing()
            flush_diacritics()

        half_widths = data.get("half_widths_template") or []
        max_half = max(half_widths) if half_widths else DEFAULT_HALF
        med_half = statistics.median(half_widths) if half_widths else DEFAULT_HALF

        # Classify each pen-stroke: a diacritic floats entirely above the
        # midband and is never the glyph's first stroke (the t-crossbar sits
        # inside the x-height band and correctly stays in flow). A detached
        # glyph never defers: a quote's second mark or a ?'s dot writes in
        # place, in order.
        midband = (data.get("template_guides") or {}).get("midband", 1)
        diacritic_flags: list[bool] = []
        for si, cl in enumerate(centerlines):
            if si == 0 or not slot.joins:
                diacritic_flags.append(False)
                continue
            stroke_min_y = min(y for _, y in cl) if cl else math.inf
            diacritic_flags.append(stroke_min_y > midband)
        has_diacritic = any(diacritic_flags)

        first_line: list[Point] = [tuple(p) for p in centerlines[0]]
        # Last NON-diacritic stroke — the part on the writing line that carries
        # the join to the next glyph.
        last_body_idx = len(centerlines) - 1
        if has_diacritic:
            for si in range(len(centerlines) - 1, -1, -1):
                if not diacritic_flags[si]:
                    last_body_idx = si
                    break
        body_exit_line: list[Point] = [tuple(p) for p in centerlines[last_body_idx]]

        entry = data.get("entry") or {}
        entry_xy: Point = tuple(entry["xy"]) if entry.get("xy") else first_line[0]
        # The connector to the NEXT glyph leaves from the body's exit, never a
        # floating mark; point AND tangent come from the rendered centerline.
        exit_xy: Point = body_exit_line[-1]
        exit_deg = _endpoint_tangent(body_exit_line, at_end=True)

        # Horizontal body-INK extent in the glyph's own frame (rings where
        # available — the silhouette edge — else centerlines), measured ONLY
        # inside the JOIN BAND around the x-height (kerning, not bounding
        # boxes): an ascender loop reaching high right (d) must not push the
        # neighbour away — on the teaching plates the next letter tucks in
        # under it — while a bow at x-height (w, v) must. Diacritics never
        # count (they are deferred and float above the band anyway).
        ink_min_x = math.inf
        ink_max_x = -math.inf
        # Per-y-bin rightmost ink over the join band — the height-aware side
        # of the fused-flank clearance guard (see FUSE_CLEAR_BINS).
        ink_profile = [-math.inf] * FUSE_CLEAR_BINS
        # A detached glyph does not take part in join-band kerning — its whole
        # body (a comma below the baseline, a quote above the midband) is what
        # the neighbour must clear.
        band = JOIN_BAND_Y if slot.joins else (-math.inf, math.inf)
        for si, cl in enumerate(centerlines):
            if diacritic_flags[si]:
                continue
            rings = rings_by_stroke[si] if si < len(rings_by_stroke) else []
            for pts in rings if rings else (cl,):
                for x, y in pts:
                    if band[0] <= y <= band[1]:
                        ink_min_x = min(ink_min_x, x)
                        ink_max_x = max(ink_max_x, x)
                        if slot.joins and JOIN_BAND_Y[0] <= y <= JOIN_BAND_Y[1]:
                            bi = _band_bin(y)
                            ink_profile[bi] = max(ink_profile[bi], x)
        if not math.isfinite(ink_min_x):
            ink_min_x = ink_max_x = entry_xy[0]

        # Place this glyph so its entry meets the previous glyph's exit + a
        # small gap AND its body ink clears the previous glyph's body ink by
        # INK_CLEARANCE; with no connector start at the running cursor_x. A
        # detached pairing (either side non-joining) is placed by ink
        # clearance alone — the tighter of the two clearances wins.
        joined = bool(prev) and prev["joins"] and slot.joins
        # Coupling index of a straight-fit flank placement (the "ne" case) —
        # set by the nested-fall branch, consumed by the connector.
        flank_couple = 0
        # An approved pair override wins over the generated placement AND the
        # generated connector for exactly this adjacent pair (redesign R3).
        # All-or-nothing: a malformed row (connector under 2 points — e.g. a
        # hand-edited DB row) must not shift the glyph without drawing the
        # join, so it is ignored entirely and the generator path runs.
        override = (pair_overrides or {}).get((prev["key"], slot.key)) if joined and slot.key else None
        if override is not None and len(override.get("connector") or []) < 2:
            override = None
        if override is not None:
            offset = override.get("offset") or [CONNECT_GAP, 0.0]
            desired_entry_x = prev["exit"][0] + float(offset[0])
        elif joined:
            tuck = TUCK_RATE * max(0.0, prev["exit"][1] - TUCK_Y0)
            clearance = BACKWARD_INK_CLEARANCE if _unit(prev["tangent_deg"])[0] <= 0.0 else INK_CLEARANCE
            desired_entry_x = max(
                prev["exit"][0] + CONNECT_GAP - tuck, prev["ink_max_x"] + clearance - (ink_min_x - entry_xy[0])
            )
            # Sawtooth pass-through: pull the glyph onto the exit's rise line
            # (see ALIGN_*) so the diagonal continues without a shelf.
            entry_land_deg = _endpoint_tangent(first_line, at_end=False)
            rise = first_line[0][1] - prev["exit"][1]
            if (
                ALIGN_TAN_DEG[0] <= prev["tangent_deg"] <= ALIGN_TAN_DEG[1]
                and ALIGN_TAN_DEG[0] <= entry_land_deg <= ALIGN_TAN_DEG[1]
                and rise >= ALIGN_MIN_RISE
                and first_line[0][1] <= ALIGN_MAX_ENTRY_Y
            ):
                mean_slope = ALIGN_SLOPE_RATIO * math.tan(math.radians((prev["tangent_deg"] + entry_land_deg) / 2))
                align_entry_x = prev["exit"][0] + rise / mean_slope + (entry_xy[0] - first_line[0][0])
                floor_x = prev["ink_max_x"] + ALIGN_MIN_CLEARANCE - (ink_min_x - entry_xy[0])
                if align_entry_x < desired_entry_x:
                    desired_entry_x = max(align_entry_x, floor_x)
            elif (
                ALIGN_TAN_DEG[0] <= prev["tangent_deg"] <= ALIGN_TAN_DEG[1]
                and rise < ALIGN_MIN_RISE
                and prev["exit"][1] <= HIGH_COUPLE_EXIT_Y
            ):
                # Nested fall (R4): a rising mid-band exit whose neighbour
                # enters BELOW it cannot pass through — on the plate the next
                # letter nests under the exit ink (t's bar, f's flag) instead
                # of clearing it, so the ink floor relaxes to the align floor.
                floor_x = prev["ink_max_x"] + ALIGN_MIN_CLEARANCE - (ink_min_x - entry_xy[0])
                desired_entry_x = max(prev["exit"][0] + CONNECT_GAP - tuck, floor_x)
                # Straight-fit flank coupling (the "ne" case, see the ALIGN_*
                # constant block): with the entry FOOT at/below the exit no
                # spacing can make the diagonal collinear at the foot — but
                # fusing onto the RISING lead-in flank can. Stage 1: push the
                # pair together until the line through the exit at the FULL
                # mean ink tangent meets the flank — the join continues the
                # stroke direction itself, legitimacy judged by the
                # height-aware clearance guard. Stage 2 fallback: place at
                # the stub-relaxed column floor and couple at the top of the
                # flank window — the steepest straight join the ink allows.
                if rise > -FLANK_COUPLE_MAX_DROP and ALIGN_TAN_DEG[0] <= entry_land_deg <= ALIGN_TAN_DEG[1]:
                    full_slope = math.tan(math.radians((prev["tangent_deg"] + entry_land_deg) / 2))
                    fuse = _fused_flank_placement(first_line, prev["exit"], full_slope, entry_xy[0])
                    fused = False
                    if fuse is not None and fuse[0] <= desired_entry_x:
                        exempt = (
                            min(prev["exit"][1], first_line[0][1]) - FUSE_BAND_PAD,
                            first_line[fuse[1]][1] + FUSE_BAND_PAD,
                        )
                        if _fused_clearance_ok(
                            prev["ink_profile"],
                            centerlines,
                            diacritic_flags,
                            fuse[1],
                            fuse[0] - entry_xy[0],
                            max_half,
                            exempt,
                        ):
                            desired_entry_x, flank_couple = fuse
                            fused = True
                    if not fused:
                        floor_couple = prev["ink_max_x"] + ALIGN_MIN_CLEARANCE - max(ink_min_x - entry_xy[0], 0.0)
                        if floor_couple <= desired_entry_x:
                            steepest = _flank_couple_steepest(first_line, floor_couple - entry_xy[0], prev["exit"])
                            if steepest:
                                desired_entry_x, flank_couple = floor_couple, steepest
        elif prev:
            gap = _nonjoin_clearance(_key_base(slot.key, slot.position)) if not slot.joins else math.inf
            if not prev["joins"]:
                gap = min(gap, _nonjoin_clearance(prev["base"]))
            desired_entry_x = prev["ink_max_x"] + gap - (ink_min_x - entry_xy[0])
        else:
            desired_entry_x = cursor_x
        dx = desired_entry_x - entry_xy[0]

        # Connector first (writing order): the pen slides from A's exit into B's
        # entry. A round body (bowl / e-loop) is entered AT ITS TOP after a high
        # exit — the letter hangs from the covering join, never dipping first
        # (see HIGH_COUPLE_BASES; verified on the plate originals).
        entry_trim = 0
        if override is not None:
            # The stored join, verbatim: centerline points are relative to the
            # left glyph's exit point (template units; ≥2 points guaranteed by
            # the all-or-nothing check above).
            ex, ey = prev["exit"]
            centerline = [(ex + float(px), ey + float(py)) for px, py in override["connector"]]
            connector = {"centerline": [list(p) for p in centerline], "lift": False}
            _apply_pen(connector, centerline, 2 * min(prev["width"], med_half), pen)
            if provenance:
                connector["pair"] = [prev["key"], slot.key]
                connector["from_slot"] = prev["slot_index"]
                connector["to_slot"] = slot_index
                connector["override"] = True
            items.append(connector)
            track(centerline)
        elif joined:
            high_couple = _key_base(slot.key, slot.position) in HIGH_COUPLE_BASES
            centerline, entry_trim = _connector_centerline(
                prev["exit"], prev["tangent_deg"], first_line, dx, high_couple=high_couple, flank_trim=flank_couple
            )
            connector = {"centerline": [list(p) for p in centerline], "lift": False}
            _apply_pen(connector, centerline, 2 * min(prev["width"], med_half), pen)
            if provenance:
                connector["pair"] = [prev["key"], slot.key]
                connector["from_slot"] = prev["slot_index"]
                connector["to_slot"] = slot_index
            items.append(connector)
            track(centerline)

        # The glyph's own strokes (silhouette + centerline), translated by dx.
        # Body strokes flow in writing order; diacritics are held back. When no
        # connector precedes (a detached boundary on either side), the pen
        # visibly lifts into this glyph's first stroke.
        detached_entry = prev is not None and not joined
        glyph_mask_width = 2.2 * max_half
        if pen is not None and pen.kind == "broad_nib" and pen.nib is not None:
            # The stamped nib's diagonal extent can exceed the widest width the
            # glyph's own stroke directions reach — the reveal mask must cover
            # the nib, not just the widest measured direction.
            glyph_mask_width = max(glyph_mask_width, pen.nib.width_units * 1.15)
        for si, cl in enumerate(centerlines):
            src = cl[entry_trim:] if si == 0 and entry_trim else cl
            offset = [(x + dx, y) for x, y in src]
            raw_rings = rings_by_stroke[si] if si < len(rings_by_stroke) else []
            if si == 0 and entry_trim and raw_rings:
                # The trimmed stub piece (plus the anchor sample, so the erase
                # meets the kept flank without a sliver) leaves the silhouette
                # with the same cut the centerline took. Erased in the glyph's
                # own frame, BEFORE the dx shift — stub prefix and payload
                # rings share that frame, so no coordinate round-trips.
                raw_rings = erase_silhouette_piece(raw_rings, cl[: entry_trim + 1], med_half * 1.1)
            rings = [[(x + dx, y) for x, y in ring] for ring in raw_rings]
            item: dict = {
                "centerline": [list(p) for p in offset],
                "mask_width": glyph_mask_width,
                # a within-glyph pen lift precedes every stroke after the first
                "lift": si > 0 or detached_entry,
            }
            if provenance:
                item["slot_index"] = slot_index
                item["glyph_key"] = slot.key
            if rings:
                item["rings"] = [[list(p) for p in ring] for ring in rings]
            track(offset)
            for ring in rings:
                track(ring)
            if diacritic_flags[si]:
                item["diacritic"] = True
                pending_diacritics.append(item)
            else:
                items.append(item)

        exit_abs: Point = (exit_xy[0] + dx, exit_xy[1])
        prev = {
            "exit": exit_abs,
            "tangent_deg": exit_deg,
            "width": med_half,
            "ink_max_x": ink_max_x + dx,
            "ink_profile": [v + dx if math.isfinite(v) else v for v in ink_profile],
            "key": slot.key,
            "slot_index": slot_index,
            "joins": slot.joins,
            "base": _key_base(slot.key, slot.position),
        }
        cursor_x = max(exit_abs[0], ink_max_x + dx) if not slot.joins else exit_abs[0]

    end_swing()  # the last word's Endstrich …
    flush_diacritics()  # … then its marks, once the body is complete

    if not math.isfinite(min_x):
        min_x, max_x, min_y, max_y = 0.0, 1.0, 0.0, 1.0
    return {
        "items": items,
        "bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y},
        "guides": guides,
        "missing": missing,
    }
