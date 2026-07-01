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

Ported 1:1 from ``app/src/domain/compose.ts`` and pinned against its output by
the golden parity fixture (``tests/test_compose_golden.py``) — the TS file is
deleted once the server-side word endpoint carries the public writer.
"""

from __future__ import annotations

import math

from core.shaping import GlyphSlot


SPACE_ADV = 0.55  # inter-word gap, x-height units
# Advance reserved for an unrenderable glyph — capped at the word gap, so a
# hole never yawns wider than an actual space.
MISSING_ADV = 0.55
CONNECT_GAP = 0.16  # horizontal span of a connecting stroke
CONNECT_SAMPLES = 24  # Bézier samples per connector (dense enough to read as a smooth arc)
DEFAULT_HALF = 0.05  # fallback stroke half-width
# Exit y (baseline = 0, descender ≈ −1) below which a glyph's stroke is judged
# to end inside its descender loop, so the connector becomes a return upstroke
# rather than following the downward exit tangent (see the long-s ſ).
DESCENDER_EXIT_Y = -0.2
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


def compose_word(slots: list[GlyphSlot], data_by_key: dict[str, dict | None]) -> dict:
    """Compose shaped slots + per-glyph render payloads into draw items.

    Returns ``{"items", "bounds", "guides", "missing"}`` — one draw item per
    stroke/connector in writing order. A glyph item carries filled silhouette
    ``rings``; a connector carries a constant ``stroke_width`` (the Sütterlin
    Gleichzug; a Schwellzug taper is Phase D). Both carry the ``centerline``
    the renderer sweeps its reveal mask along (``mask_width`` wide), a ``lift``
    flag (a pen lift precedes this item → short pause) and ``diacritic`` on the
    deferred floating marks.
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

    for slot in slots:
        if slot.space:
            flush_diacritics()  # the word's marks land before the gap to the next word
            cursor_x += SPACE_ADV
            prev = None
            continue
        data = data_by_key.get(slot.key) if slot.key else None
        centerlines = (data or {}).get("centerlines_template")
        if not data or not centerlines:
            if slot.key:
                missing.append(slot.key)
            # A null-key slot (punctuation, digit) or a missing glyph breaks the
            # writing run just like a space: flush the marks gathered so far, so
            # a preceding i-dot/umlaut lands at the end of its word.
            flush_diacritics()
            cursor_x += MISSING_ADV
            prev = None
            continue
        if guides is None:
            guides = data["template_guides"]

        half_widths = data.get("half_widths_template") or []
        max_half = max(half_widths) if half_widths else DEFAULT_HALF
        med_half = _median(list(half_widths))

        # Classify each pen-stroke: a diacritic floats entirely above the
        # midband and is never the glyph's first stroke (the t-crossbar sits
        # inside the x-height band and correctly stays in flow).
        midband = (data.get("template_guides") or {}).get("midband", 1)
        diacritic_flags: list[bool] = []
        for si, cl in enumerate(centerlines):
            if si == 0:
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

        # Place this glyph so its entry meets the previous glyph's exit + a
        # small gap; with no connector start at the running cursor_x.
        desired_entry_x = prev["exit"][0] + CONNECT_GAP if prev else cursor_x
        dx = desired_entry_x - entry_xy[0]

        # Connector first (writing order): the pen slides from A's exit into B's entry.
        if prev:
            p0: Point = prev["exit"]
            # End exactly on the next glyph's first ink sample so the join sits
            # on the centerline the entry tangent is measured from.
            p3: Point = (first_line[0][0] + dx, first_line[0][1])
            span = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
            handle = max(0.05, span * 0.4)
            d_out = _unit(prev["tangent_deg"])
            # A glyph whose stroke ends deep in its descender loop (the long-s ſ)
            # exits pointing downward — there the connector IS the return
            # upstroke: aim it at the next entry instead of continuing the
            # descent. Glyphs that finish a descender properly exit above the
            # baseline, so the guard never fires for them.
            if p0[1] < DESCENDER_EXIT_Y and d_out[1] < 0 and span > 0:
                d_out = ((p3[0] - p0[0]) / span, (p3[1] - p0[1]) / span)
            entry_deg = _endpoint_tangent(first_line, at_end=False)
            d_in = _unit(entry_deg)
            p1: Point = (p0[0] + handle * d_out[0], p0[1] + handle * d_out[1])
            p2: Point = (p3[0] - handle * d_in[0], p3[1] - handle * d_in[1])
            centerline = _sample_bezier(p0, p1, p2, p3, CONNECT_SAMPLES)
            stroke_width = 2 * min(prev["width"], med_half)
            items.append(
                {
                    "centerline": [list(p) for p in centerline],
                    "stroke_width": stroke_width,
                    "mask_width": stroke_width * 1.3,
                    "lift": False,
                }
            )
            track(centerline)

        # The glyph's own strokes (silhouette + centerline), translated by dx.
        # Body strokes flow in writing order; diacritics are held back.
        rings_by_stroke = data.get("outline_paths") or []
        for si, cl in enumerate(centerlines):
            offset = [(x + dx, y) for x, y in cl]
            rings = [
                [(x + dx, y) for x, y in ring] for ring in (rings_by_stroke[si] if si < len(rings_by_stroke) else [])
            ]
            item: dict = {
                "centerline": [list(p) for p in offset],
                "mask_width": 2.2 * max_half,
                "lift": si > 0,  # a within-glyph pen lift precedes every stroke after the first
            }
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
        prev = {"exit": exit_abs, "tangent_deg": exit_deg, "width": med_half}
        cursor_x = exit_abs[0]

    flush_diacritics()  # the last word's marks, once its body is complete

    if not math.isfinite(min_x):
        min_x, max_x, min_y, max_y = 0.0, 1.0, 0.0, 1.0
    return {
        "items": items,
        "bounds": {"min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y},
        "guides": guides,
        "missing": missing,
    }
