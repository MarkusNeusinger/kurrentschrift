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

import numpy as np

from core.shaping import GlyphSlot
from core.template import chisel_union_rings
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
CONNECT_GAP = 0.16  # minimum horizontal span of a connecting stroke (exit → entry)
# Minimum clearance between the previous glyph's rightmost body INK and the
# next glyph's leftmost body ink. The exit/entry anchors alone cannot carry the
# spacing rhythm: a bow that curls back (w, v) exits well LEFT of its rightmost
# ink, so an exit-anchored gap starts the next letter inside the bow — the
# words the bench flagged as far too narrow (einen/einer/wenn/zwei) all contain
# such exits, while exit≈ink-edge words (das, mit) were already sized right.
INK_CLEARANCE = 0.14
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
CONNECT_SAMPLES = 24  # Bézier samples per connector (dense enough to read as a smooth arc)
# Baseline garland — the school hand's default join when a letter's stroke
# ends ABOVE where the next one begins. The plates (Abb. 19/20) show the pen
# leaving the exit (r's arm, b's bow, d's loop, t), falling into a ROUNDED
# TURN near the Grundlinie and rising into the next letter's lead-in
# collinearly. The taut single cubic used to bridge such drops directly,
# which read as a V-notch / S-wobble at the seam (jul09 join audit: r→e
# 72°/65°, b→i 90°/77° seam kinks). Geometry + eligibility in
# ``_garland_centerline``: a fall cubic into a horizontal-tangent turn point
# plus a rise cubic that straightens into the entry tangent.
# How far down the lead-in line the pen merges: the merge point sits
# GARLAND_TURN_RATIO × (exit's perpendicular distance to the line) before the
# entry point — a close line (rb) is joined near the entry, a far one (r→e,
# d→e) is ridden from near its foot, which is exactly how the plates grade
# the depth of the turn.
GARLAND_TURN_RATIO = 0.8
GARLAND_MERGE_EPS = 0.15  # exit closer than this to the lead-in line: plain taut cubic
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
# run short of it. Bench optimum; plate medians: n≈0.53, m/e≈0.6, r≈0.82.
SWING_TOP_Y = 0.7
SWING_MAX_RUN = 0.9  # cap the horizontal run for shallow exits (x-height units)
SWING_MIN_RISE = 0.2  # a flat/falling exit does not swing (needs a rising flank to continue)
# The plates' Endstrich is not a straight continuation: it leaves along the
# exit tangent and FLATTENS towards the end (a long, gently convex upswing —
# the jul09 audit measured runs of ~0.5 x-heights ending near level, while
# the straight swing stopped after ~0.2). End direction of that curve:
SWING_END_DEG = 12.0
# Only a LOW forward exit swings: a bow/Deckstrich exit (o, b, w) already ends
# high and the plates show no extra flourish there.
SWING_MAX_EXIT_Y = 0.7
DEFAULT_HALF = 0.05  # fallback stroke half-width
# Exit y (baseline = 0, descender ≈ −1) below which a glyph's stroke is judged
# to end inside its descender loop, so the connector becomes a return upstroke
# rather than following the downward exit tangent (see the long-s ſ).
DESCENDER_EXIT_Y = -0.2
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
ALIGN_MIN_CLEARANCE = 0.06  # ink may approach this close when alignment pulls
# The plates couple slightly FLATTER than the letters' internal diagonals (a
# subtle set-off remains between two sawtooth letters) — pull onto a line of
# this fraction of the mean tangent slope, not the full slope.
ALIGN_SLOPE_RATIO = 0.8
# Tall lead-ins (h 0.69, t 0.70 …) sweep in long and flat on the plates —
# alignment on their steep landing tangent over-pulls; leave them to the
# clearance placement.
ALIGN_MAX_ENTRY_Y = 0.62
# Travel direction measured over a short ARC-LENGTH window rather than the
# single final segment — the glyph centerline is a smooth spline through the
# anchors, so its true endpoint tangent rarely matches the stored single-chord
# anchor tangent; the window also rejects the jitter of one short segment.
TANGENT_WINDOW = 0.12  # x-height units (matches the corner-detection window)

Point = tuple[float, float]


def _median(xs: list[float]) -> float:
    if not xs:
        return DEFAULT_HALF
    s = sorted(xs)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def _unit(deg: float) -> Point:
    r = math.radians(deg)
    return (math.cos(r), math.sin(r))


def _key_base(key: str | None, position: str | None) -> str:
    """The glyph_key without its position suffix (`comma-final` → `comma`)."""
    if not key:
        return ""
    suffix = f"-{position}"
    return key[: -len(suffix)] if position and key.endswith(suffix) else key


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
    """Baseline-garland join (see the GARLAND_* constants): fall cubic from the
    exit into a horizontal-tangent turn point near the Grundlinie, then a rise
    cubic that straightens into the entry tangent. Returns None whenever the
    geometry does not call for a garland — the caller falls back to the taut
    cubic (mid-rise sawtooth exits, descender returns, rising joins, no room).
    """
    if d_in[1] <= 0.2 or d_in[0] <= 0.0:
        return None  # entry stroke not a rising lead-in
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
        p0,
        (p0[0] + h_out * d_out[0], p0[1] + h_out * d_out[1]),
        (m[0] - h_in * d_in[0], m[1] - h_in * d_in[1]),
        m,
        18,
    )
    # Ride the lead-in line straight into the entry point.
    ride = [(m[0] + (p3[0] - m[0]) * t / 6, m[1] + (p3[1] - m[1]) * t / 6) for t in range(1, 7)]
    return fall + ride


def compose_word(
    slots: list[GlyphSlot],
    data_by_key: dict[str, dict | None],
    *,
    pen: PenStyle | None = None,
    provenance: bool = False,
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
    The same seam is where an approved per-pair override would hook in later
    (Vorschlag B — gated, nothing is stored today).
    """
    items: list[dict] = []
    missing: list[str] = []
    guides: dict | None = None
    cursor_x = 0.0
    # The previous glyph's exit in the composed frame, for the next connector.
    prev: dict | None = None

    def apply_pen(item: dict, centerline: list[Point], default_width: float) -> None:
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
        """Emit the word-final Endstrich — the finishing upswing (see
        SWING_TOP_Y): the last glyph's rising exit flank, continued straight
        towards the x-height line. High, backward or flat exits (bows, a
        Deckstrich cover-stroke) end the word as they are."""
        nonlocal cursor_x
        if not prev or not prev["joins"] or prev["exit"][1] >= SWING_MAX_EXIT_Y:
            return
        d_out = _unit(prev["tangent_deg"])
        if d_out[0] <= 0 or d_out[1] < SWING_MIN_RISE:
            return
        p0: Point = prev["exit"]
        rise = SWING_TOP_Y - p0[1]
        if rise <= 0:
            return
        # Quadratic that leaves along the exit tangent and flattens to
        # SWING_END_DEG at the top: run = rise × mean of the two cotangents.
        cot_out = d_out[0] / d_out[1]
        cot_end = 1.0 / math.tan(math.radians(SWING_END_DEG))
        run = min(rise * (cot_out + cot_end) / 2, SWING_MAX_RUN)
        if run <= 0:
            return
        p3: Point = (p0[0] + run, p0[1] + rise * min(1.0, run / (rise * (cot_out + cot_end) / 2)))
        # Control point: intersection of the two tangent lines (exists because
        # the directions differ; fall back to the midpoint when nearly parallel).
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
        swing: dict = {"centerline": [list(p) for p in centerline], "lift": False}
        apply_pen(swing, centerline, 2 * prev["width"])
        if provenance:
            swing["pair"] = [prev["key"], None]
            swing["from_slot"] = prev["slot_index"]
            swing["to_slot"] = None
        items.append(swing)
        track(centerline)
        cursor_x = p3[0]
        # The swing's ink extends the word rightward — a detached mark placed
        # next (comma, period) must clear it, not the letter body alone.
        prev["ink_max_x"] = max(prev["ink_max_x"], p3[0])

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

        # A detached glyph (digit, punctuation — slot.joins False) closes the
        # letter run before it like a word boundary: the body earns its
        # Endstrich and the word's floating marks land before the mark is
        # written.
        if not slot.joins and prev and prev["joins"]:
            end_swing()
            flush_diacritics()

        half_widths = data.get("half_widths_template") or []
        max_half = max(half_widths) if half_widths else DEFAULT_HALF
        med_half = _median(list(half_widths))

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
        rings_by_stroke = data.get("outline_paths") or []
        ink_min_x = math.inf
        ink_max_x = -math.inf
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
        if not math.isfinite(ink_min_x):
            ink_min_x = ink_max_x = entry_xy[0]

        # Place this glyph so its entry meets the previous glyph's exit + a
        # small gap AND its body ink clears the previous glyph's body ink by
        # INK_CLEARANCE; with no connector start at the running cursor_x. A
        # detached pairing (either side non-joining) is placed by ink
        # clearance alone — the tighter of the two clearances wins.
        joined = bool(prev) and prev["joins"] and slot.joins
        if joined:
            desired_entry_x = max(
                prev["exit"][0] + CONNECT_GAP, prev["ink_max_x"] + INK_CLEARANCE - (ink_min_x - entry_xy[0])
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
                mean_slope = ALIGN_SLOPE_RATIO * math.tan(
                    math.radians((prev["tangent_deg"] + entry_land_deg) / 2)
                )
                align_entry_x = prev["exit"][0] + rise / mean_slope + (entry_xy[0] - first_line[0][0])
                floor_x = prev["ink_max_x"] + ALIGN_MIN_CLEARANCE - (ink_min_x - entry_xy[0])
                if align_entry_x < desired_entry_x:
                    desired_entry_x = max(align_entry_x, floor_x)
        elif prev:
            gap = _nonjoin_clearance(_key_base(slot.key, slot.position)) if not slot.joins else math.inf
            if not prev["joins"]:
                gap = min(gap, _nonjoin_clearance(prev["base"]))
            desired_entry_x = prev["ink_max_x"] + gap - (ink_min_x - entry_xy[0])
        else:
            desired_entry_x = cursor_x
        dx = desired_entry_x - entry_xy[0]

        # Connector first (writing order): the pen slides from A's exit into B's entry.
        if joined:
            p0: Point = prev["exit"]
            # End exactly on the next glyph's first ink sample so the join sits
            # on the centerline the entry tangent is measured from.
            p3: Point = (first_line[0][0] + dx, first_line[0][1])
            span = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
            # Handle length: 40 % of the span, but never more than half the
            # HORIZONTAL run — a steep drop (d/t exits high above the next
            # entry) with span-scaled handles balloons the Bézier into an
            # S-bulge; clamping to the horizontal run keeps the curve taut
            # while preserving the end tangents (G1).
            hspan = abs(p3[0] - p0[0])
            handle = max(0.05, min(span * 0.4, hspan * 0.5))
            d_out = _unit(prev["tangent_deg"])
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
            if ((p0[1] < DESCENDER_EXIT_Y and d_out[1] < 0) or backward or high_reversal) and span > 0:
                d_out = ((p3[0] - p0[0]) / span, (p3[1] - p0[1]) / span)
            elif BOW_EXIT_Y < p0[1] <= HIGH_EXIT_Y and p3[1] < p0[1]:
                launch = math.degrees(math.atan2(d_out[1], d_out[0]))
                if launch < ARM_TAN_MAX_DEG:
                    # r-arm Absatz: corner off the arm, steep fall (see ARM_*).
                    d_out = _unit(ARM_FALL_DEG)
                else:
                    clamped = min(max(launch, BOW_LAUNCH_DEG[0]), BOW_LAUNCH_DEG[1])
                    if clamped != launch:
                        d_out = _unit(clamped)
            entry_deg = _endpoint_tangent(first_line, at_end=False)
            d_in = _unit(entry_deg)
            # A join that must LOSE height writes as a baseline garland (the
            # school hand's rounded turn); everything else stays the taut cubic.
            centerline = _garland_centerline(p0, d_out, p3, d_in)
            if centerline is None:
                p1: Point = (p0[0] + handle * d_out[0], p0[1] + handle * d_out[1])
                p2: Point = (p3[0] - handle * d_in[0], p3[1] - handle * d_in[1])
                centerline = _sample_bezier(p0, p1, p2, p3, CONNECT_SAMPLES)
            connector: dict = {"centerline": [list(p) for p in centerline], "lift": False}
            apply_pen(connector, centerline, 2 * min(prev["width"], med_half))
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
            offset = [(x + dx, y) for x, y in cl]
            rings = [
                [(x + dx, y) for x, y in ring] for ring in (rings_by_stroke[si] if si < len(rings_by_stroke) else [])
            ]
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
