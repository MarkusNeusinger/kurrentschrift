"""Der Streifen-Pfad — the followed pen path of one written word, as DATA.

A stored strip says WHERE the ink is. It never said in which ORDER the pen
laid it down, and that is the one thing the author asked to see in the
workbench (2026-09-12: „bitte auch im admin integrieren das ich bei den
handstreifen und den wörtern generell den pfad auch sehen kann").

The path is not measured here. It is followed OFFLINE by the Tintenfolger
(``tools.eigenhand.pfad`` over ``tools.pairlab.tintenpfad``) and pushed through
the admin API, because ``api`` and ``core`` must never import ``tools``. What
lives in this module is the pure half both sides need and neither may spell
twice: where a word box sits in a stored strip (``frame_for_box``) and what a
stored path has to look like (``check_paths``).

TWO FORMATS, ONE LIST. Since 2026-09-20 an entry can also say that a box has
NO path and why (the Skip-Eintrag: ``status`` + ``grund``), and it carries the
letter boundaries of its own path as a checked field with their provenance
(``letter_spans[].herkunft``). Both are format 2 and both are refused under
format 1 — what a row is stamped with has to be what its cell obeys. The API
reads and accepts ``SUPPORTED_FORMATS``; ``PFAD_FORMAT`` is only what this
image WRITES, and the distance between the two is the lockstep.

THE FRAME. A path's ``strokes`` use the same contract as
``word_instances.strokes`` — baseline 0, midband 1, x growing from the word's
own origin — so one overlay component serves the Wörter view and the Eigenhand
view alike. Its ``registration_px`` maps those units into the STRIP's own
pixels (``px = (u·xh + tx, baseline_row − v·xh)``), not into the word crop's:
the strip is the one image that always exists, and a crop's frame follows from
it by subtracting the box rectangle. The other way round would need the crop's
padding to be remembered along with the path.

NOMINAL, NOT MEASURED. The lineature ``frame_for_box`` hands back is the
PRINTED ruling of the Bogen — where the writer was asked to write, not where
the hand actually wrote. That is a good seed for a follower and a lie as a
measurement, which is why the stored ``registration_px`` is the follower's own
output and the UI says „Saat" where it shows the nominal one.

WHY THE PATH HANGS OFF THE STRIP. ``befund`` and ``flecken`` hang off the
Fassung because a Fassung can be judged before its pixels exist. A path is the
opposite: it can only be followed where the ink is stored. So it sits on
``eigenhand_strips`` (migration 0031), keyed by the same (hand, strip, fassung)
identity, deferred beside the PNG — a listing must never drag every path of
every Fassung along.

NOT ``word_instances``. Routing a strip path into that table would displace the
harvest's traced row under its UNIQUE (source_id, kind, specimen_id), and those
rows are frozen into ``word_instances.json``, which ``tools/tracebench/
reference.py`` pins as the reference set. It would also pull reserved own-hand
material into the bench sets, against ``docs/proposals/eigenhand-erfassung.md``
§12.2.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import date as date_cls
from typing import Any

from core.eigenhand.crop import px_per_mm, word_box_px


# The format this image WRITES: what a push declares when it names none, and
# what every writer in the repo puts on the wire. It is a MOVING number, which
# is why a row stores the one it was written under rather than trusting it
# (`eigenhand_strips.pfade_format`, migration 0032).
PFAD_FORMAT = 1

# Every format this image READS and ACCEPTS on a push, oldest first — wider than
# `PFAD_FORMAT` on purpose. That gap IS the lockstep (docs/proposals/
# admin-redesign.md §6.3): the API admits the newer shape one release before any
# writer produces it, so a tool and an API never have to land in the same
# minute, and the two shapes then coexist per ROW rather than per deployment.
SUPPORTED_FORMATS = (1, 2)

# The format that admits a Skip-Eintrag and checked `letter_spans`. Below it an
# entry has exactly the shape migration 0031 introduced, and both fields are
# REFUSED rather than stored under a number whose readers do not know them: a
# row stamped 1 whose cell carries format-2 fields is the mislabelling the
# stored marker exists to prevent, moved one layer down.
SKIP_AND_SPAN_FORMAT = 2

# The one `verfahren` the stored list treats as untouchable: a path the AUTHOR
# drew by hand. The twin of `word_instances.provenance == "authored"` — a
# follower run is a DERIVATION and never replaces ground truth
# (docs/proposals/eigenhand-erfassung.md §7.5).
AUTHORED = "authored"

# An entry's own answer to „is there a path in this box". A Skip-Eintrag is an
# entry of the SAME list rather than a second list beside it (author decision C,
# 2026-09-20): a box has exactly one state, and two lists would be two places
# the same box appears in until they contradict each other.
STATUS_OK = "ok"
STATUS_SKIPPED = "skipped"
STATUS_VALUES = (STATUS_OK, STATUS_SKIPPED)

# Why a box carries no path — CLOSED, and that is the whole point. Until format
# 2 these four situations were ONE indistinguishable state („no entry"), and
# they are not the same work at all: `unauthored` is a jump to the plate rather
# than tracing, `no_geometry` needs a Bogen re-measured, `gave_up` is the only
# one that is genuinely follower work, and `not_selected` is no finding at all.
# A free string would merge them again within a month, so an unknown reason is
# refused instead of stored (`other` is the honest place for a new one).
SKIP_NOT_SELECTED = "not_selected"
SKIP_NO_GEOMETRY = "no_geometry"
SKIP_UNAUTHORED = "unauthored"
SKIP_GAVE_UP = "gave_up"
SKIP_OTHER = "other"
SKIP_REASONS = (SKIP_NOT_SELECTED, SKIP_NO_GEOMETRY, SKIP_UNAUTHORED, SKIP_GAVE_UP, SKIP_OTHER)

# What a skip may add in its own words — the follower's `detail`, the missing
# glyph keys, the refused geometry. Short: the triage runs on `grund`, this is
# only what a human reads afterwards.
MAX_DETAIL = 200

# Where one letter boundary came from. `auto` is the follower's own assignment,
# `AUTHORED` one the author corrected by hand — the second provenance source
# `is_authored` was written to make room for, protected per FIELD rather than
# per box so an ordinary re-follow of a span-corrected box still passes.
SPAN_AUTO = "auto"
SPAN_HERKUNFT = (SPAN_AUTO, AUTHORED)

# A word box holds a couple of dozen letter boundaries; anything past this is a
# client sending a sample-level labelling rather than spans.
MAX_SPANS = 256

# The highest shaped slot a boundary may name. Bounded here and not only on the
# wire (`api.schemas.EigenhandPfadSpan`, which imports this number): the two
# layers refusing different things is how a 422 ends up naming the wrong rule,
# and `stroke`/`first`/`last` are bounded by the strokes they index while `slot`
# has nothing to be held against. A word of 256 slots is not a word.
MAX_SLOT = 255

# The two fields of one box a followed push may not take away. Named rather
# than implied, because the refusal has to say WHICH piece of hand work a push
# would lose — the Bahn and the boundaries on it are given up separately.
FIELD_PATH = "strokes"
FIELD_SPANS = "letter_spans"

# The format-2 fields, listed once: an older push must not carry them, and the
# refusal names the field it found rather than „your entry is wrong".
FORMAT_2_FIELDS = ("status", "grund", "detail", FIELD_SPANS)

# The same bounds `WordInstanceItem` puts on a stored trace, for the same
# reason: the strokes live in template units, so anything past this is a
# coordinate mix-up rather than an unusual word.
MAX_STROKES = 128
MAX_POINTS = 4096
MAX_UNIT = 100.0

# One row of the frozen plan carries a handful of words; a path list longer
# than its boxes is a client sending someone else's row.
MAX_PFADE = 32

# How far a registration may sit outside the strip before it is refused, in
# the PATH's own x-heights. Not zero: a word's origin can lie a little left of
# its ink (the composition starts at the Anstrich) and a baseline's descender
# band reaches past the cut. Two x-heights covers both and is far too little
# for a frame that belongs to a different image.
REGISTRATION_SLACK_XH = 2.0

# The registration slack above is measured in the path's OWN x-height, so that
# x-height has to be bounded first or the slack is whatever the client wants it
# to be: a declared `xh_px` of 1300 on a 343 px strip stretched the allowance to
# ±2600 px and let `tx = 2500` — an off-strip frame — through the very check
# that exists to refuse it. So `xh_px` is held against the PRINTED ruling of the
# row, which `check_paths` can derive from what it already receives: half to
# double the nominal x-height is every hand this Bogen could have been written
# in, and nothing further.
XH_NOMINAL_TOLERANCE = 2.0
# Where the ruling is not knowable (a Bogen printed before the cut geometry),
# the strip itself is the only witness left: an x-height below a few pixels
# carries no path, and one past half the strip height cannot be a lowercase
# body on a three-band ruling.
XH_MIN_PX = 4.0
XH_MAX_HEIGHT_SHARE = 0.5


def frame_for_box(
    layout_row: Mapping[str, Any],
    crop_origin_mm: Sequence[float],
    width_px: int,
    height_px: int,
    box_index: int,
    pad_mm: float = 1.0,
) -> dict[str, Any]:
    """Where one word box sits in a stored strip, and on which nominal ruling.

    Everything needed to seed a follower and to place a path over a word crop,
    derived from what is already stored: the row's Schnittband gives the mm→px
    scale, the strip's own ``crop_origin_mm`` the offset, the printed
    ``band_mm`` the lineature. No new storage, and the same arithmetic the word
    crop endpoint already cuts with (``crop.word_box_px``), so a path and the
    pixels under it cannot drift apart.

    ``rect_px`` is [x0, y0, x1, y1] in strip pixels; ``baseline_row`` and
    ``waist_row`` are rows of the STRIP (not of the crop), and ``xh_px`` the
    printed x-height in pixels. All four are NOMINAL — see the module docstring.
    """
    boxes = layout_row.get("boxes") or []
    if not 0 <= box_index < len(boxes):
        raise ValueError(f"this row has {len(boxes)} word boxes — there is no box {box_index}")
    band = layout_row.get("band_mm") or {}
    for key in ("baseline", "waist"):
        if key not in band:
            raise ValueError(f"this row has no printed `band_mm.{key}` — its Bogen predates the ruling geometry")
    # SystemExit from the shared crop arithmetic (a row without a Schnittband,
    # a strip without a recorded origin) becomes a ValueError here: this module
    # is read by an HTTP handler, where a BaseException would travel straight
    # past the exception middleware.
    try:
        scale = px_per_mm(width_px, layout_row.get("cut_mm") or [])
        rect = word_box_px(
            boxes[box_index], crop_origin_mm, width_px, height_px, layout_row.get("cut_mm") or [], pad_mm
        )
    except SystemExit as exc:
        raise ValueError(str(exc)) from exc
    origin_y = float(crop_origin_mm[1]) if len(crop_origin_mm) > 1 else 0.0
    baseline_row = (float(band["baseline"]) - origin_y) * scale
    waist_row = (float(band["waist"]) - origin_y) * scale
    return {
        "index": box_index,
        "word": boxes[box_index].get("word", ""),
        "rect_px": [int(v) for v in rect],
        "baseline_row": round(baseline_row, 2),
        "waist_row": round(waist_row, 2),
        "xh_px": round(baseline_row - waist_row, 2),
        "px_per_mm": round(scale, 4),
    }


def frames_of_row(
    layout_row: Mapping[str, Any], crop_origin_mm: Sequence[float], width_px: int, height_px: int, pad_mm: float = 1.0
) -> list[dict[str, Any]] | None:
    """Every box of one printed row, or None where the geometry is not there.

    The listing wants the rectangles for all boxes and must not fail over a
    Bogen printed before the cut geometry existed: a strip without them simply
    has no box rectangles to offer, and the view falls back to the whole image.
    """
    try:
        return [
            frame_for_box(layout_row, crop_origin_mm, width_px, height_px, index, pad_mm)
            for index in range(len(layout_row.get("boxes") or []))
        ]
    except ValueError:
        return None


def _checked_strokes(strokes: Any, where: str) -> list[list[list[float]]]:
    if not isinstance(strokes, Sequence) or isinstance(strokes, (str, bytes)) or not strokes:
        raise ValueError(f"{where}: `strokes` must be a non-empty list of polylines")
    if len(strokes) > MAX_STROKES:
        raise ValueError(f"{where}: {len(strokes)} strokes — at most {MAX_STROKES}")
    out: list[list[list[float]]] = []
    for stroke in strokes:
        if not isinstance(stroke, Sequence) or isinstance(stroke, (str, bytes)):
            raise ValueError(f"{where}: every stroke must be a list of points")
        if not 2 <= len(stroke) <= MAX_POINTS:
            raise ValueError(f"{where}: every stroke needs 2..{MAX_POINTS} points, got {len(stroke)}")
        points: list[list[float]] = []
        for point in stroke:
            if not isinstance(point, Sequence) or isinstance(point, (str, bytes)) or len(point) != 2:
                raise ValueError(f"{where}: stroke points must be [x, y] pairs")
            try:
                x, y = float(point[0]), float(point[1])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{where}: stroke points must be numbers") from exc
            # `isfinite` FIRST: `float("nan")` parses, and every comparison
            # against it is False — so a NaN would slip through the range check
            # below, be stored, and reach the overlay as a NaN SVG coordinate,
            # which draws nothing and says nothing (Copilot review, PR #598).
            if not (math.isfinite(x) and math.isfinite(y)):
                raise ValueError(f"{where}: stroke coordinates must be finite numbers")
            if abs(x) > MAX_UNIT or abs(y) > MAX_UNIT:
                raise ValueError(f"{where}: stroke coordinates out of range (template units, |v| ≤ {MAX_UNIT:g})")
            points.append([x, y])
        out.append(points)
    return out


def _checked_date(value: Any, where: str) -> str | None:
    """The day the path was followed — PARSED, not just counted.

    A length check let `2026-99-99` through and the workbench would print it as
    provenance (Copilot review, PR #598). Absent stays legitimate: a path
    pushed by an older tool simply does not say when it was made.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{where}: `erzeugt_am` must be an ISO date (YYYY-MM-DD) or absent")
    try:
        return date_cls.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"{where}: `erzeugt_am` {value!r} is not an ISO date (YYYY-MM-DD)") from exc


def nominal_xh_px(layout_row: Mapping[str, Any], width_px: int) -> float | None:
    """The PRINTED x-height of one row in strip pixels, or None where unknowable.

    The same two numbers `frame_for_box` reads, minus the crop origin — which
    cancels in a difference, so this needs no `crop_origin_mm` and works for a
    whole row rather than for one box. A Bogen printed before the ruling or the
    cut geometry existed simply has no nominal scale to compare against.
    """
    band = layout_row.get("band_mm") or {}
    if "baseline" not in band or "waist" not in band:
        return None
    try:
        scale = px_per_mm(width_px, layout_row.get("cut_mm") or [])
        xh = (float(band["baseline"]) - float(band["waist"])) * scale
    except (SystemExit, TypeError, ValueError):
        return None
    return xh if math.isfinite(xh) and xh > 0.0 else None


def _checked_xh(value: Any, height_px: int, nominal: float | None, where: str) -> float:
    """The path's x-height, bounded before anything is measured in it.

    It is not a free number: the registration slack is expressed in x-heights,
    so an inflated `xh_px` would widen that allowance until an off-strip frame
    passed (see `XH_NOMINAL_TOLERANCE`).
    """
    try:
        xh = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{where}: `xh_px` must be the path's x-height in strip pixels") from exc
    if not math.isfinite(xh) or xh <= 0.0:
        raise ValueError(f"{where}: x-height {xh} px is not a scale this strip could have")
    if nominal is None:
        low, high = XH_MIN_PX, height_px * XH_MAX_HEIGHT_SHARE
        against = f"the strip is {height_px} px high"
    else:
        low, high = nominal / XH_NOMINAL_TOLERANCE, nominal * XH_NOMINAL_TOLERANCE
        against = f"the printed ruling is {nominal:.1f} px"
    if not low <= xh <= high:
        raise ValueError(
            f"{where}: x-height {xh:.1f} px is not a scale this strip could have ({low:.1f}..{high:.1f} px — {against})"
        )
    return xh


def _checked_registration(reg: Any, width_px: int, height_px: int, xh_px: float, where: str) -> dict[str, float]:
    """The path's own frame, bounded against the strip it claims to lie on.

    A registration from another image is the one error that would draw a
    plausible-looking path over the wrong ink — silently, because every stroke
    inside it is perfectly well-formed.

    The allowance is measured in the PATH's own x-height, not in a fraction of
    the image: a word's origin can sit a little outside the strip (the
    composition starts at the Anstrich, the descender band reaches past the
    cut) but never by more than a couple of letters. Slack scaled to the image
    instead accepted `tx = 2500` on a 1900 px strip, which is the very import
    this check exists to refuse (Copilot review, PR #598).

    That only holds while `xh_px` itself is bounded — the caller must pass one
    that went through `_checked_xh`, or a client buys any slack it likes simply
    by declaring a larger x-height (review of PR #598).
    """
    if not isinstance(reg, Mapping):
        raise ValueError(f"{where}: `registration_px` must be an object with tx, ty and baseline_row")
    try:
        tx, ty, baseline_row = (float(reg.get("tx", 0.0)), float(reg.get("ty", 0.0)), float(reg["baseline_row"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{where}: `registration_px` needs numeric tx, ty and baseline_row") from exc
    if not all(math.isfinite(value) for value in (tx, ty, baseline_row)):
        raise ValueError(f"{where}: `registration_px` must be finite numbers")
    slack = REGISTRATION_SLACK_XH * xh_px
    if not -slack <= tx <= width_px + slack:
        raise ValueError(f"{where}: tx {tx:.1f} lies outside the strip (0..{width_px} px, ±{slack:.0f} px allowed)")
    if not -slack <= baseline_row + ty <= height_px + slack:
        raise ValueError(
            f"{where}: baseline row {baseline_row + ty:.1f} lies outside the strip "
            f"(0..{height_px} px, ±{slack:.0f} px allowed)"
        )
    return {"tx": tx, "ty": ty, "baseline_row": baseline_row}


def _checked_spans(spans: Any, strokes: Sequence[Sequence[Any]], where: str) -> list[dict[str, Any]] | None:
    """The letter boundaries of one path, held against the strokes they index.

    They index SAMPLES of a stroke, and until format 2 nothing checked that the
    stroke still has them: the follower assigns spans on the path it decoded and
    stores the CAPPED strokes, which `tools.pairlab.trace.cap_word_strokes`
    downsamples past 4096 points and thins past 128 runs. A word that crossed
    either bound would have stored spans pointing into samples that no longer
    exist — silently, because every number in them is well-formed. So the
    refusal names the span AND the stroke: those two disagreeing is the whole
    finding, and a reader cannot see it from either side alone.

    `slot` is the shaped slot the boundary belongs to, and it has to be a real
    one: a span the follower could not label at all comes out of `spans_of` as
    `slot = -1`, which is not a boundary but „no letter here" and would read as
    letter number minus one in every consumer. Refused rather than dropped —
    the caller decides what to do with an unlabelled stretch, and silently
    swallowing entries is how a list starts disagreeing with its own length.

    The spans are also held against EACH OTHER, not only against their stroke:
    one sample belongs to one letter, so two boundaries claiming the same ink
    of the same stroke is the same class of nonsense as one that leaves it —
    well-formed in every number it carries, and it would reach the
    Span-Zuordner's training set as ground truth (found in review, PR #639).
    Two spans on DIFFERENT strokes may share a slot: a letter whose mark is its
    own stroke (the i-dot, an umlaut) is one slot written in two pen-downs.
    """
    if spans is None:
        return None
    if not isinstance(spans, Sequence) or isinstance(spans, (str, bytes)):
        raise ValueError(f"{where}: `letter_spans` must be a list of letter boundaries")
    if len(spans) > MAX_SPANS:
        raise ValueError(f"{where}: {len(spans)} letter spans — at most {MAX_SPANS}")
    out: list[dict[str, Any]] = []
    for position, span in enumerate(spans):
        if not isinstance(span, Mapping):
            raise ValueError(f"{where}: letter span {position} must be an object")
        values: dict[str, int] = {}
        for key in ("stroke", "slot", "first", "last"):
            value = span.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{where}: letter span {position} needs a non-negative integer `{key}`, got {value!r}")
            values[key] = value
        if values["slot"] > MAX_SLOT:
            raise ValueError(f"{where}: letter span {position} names slot {values['slot']} — at most {MAX_SLOT}")
        herkunft = span.get("herkunft")
        if herkunft not in SPAN_HERKUNFT:
            raise ValueError(
                f"{where}: letter span {position} claims herkunft {herkunft!r} — one of {', '.join(SPAN_HERKUNFT)}"
            )
        if values["stroke"] >= len(strokes):
            raise ValueError(
                f"{where}: letter span {position} indexes stroke {values['stroke']}, "
                f"but this path has {len(strokes)} stroke(s)"
            )
        length = len(strokes[values["stroke"]])
        if values["first"] > values["last"]:
            raise ValueError(
                f"{where}: letter span {position} starts at sample {values['first']} and ends at {values['last']}"
            )
        if values["last"] >= length:
            raise ValueError(
                f"{where}: letter span {position} ends at sample {values['last']} of stroke {values['stroke']}, "
                f"which has {length} point(s)"
            )
        out.append({**values, "herkunft": herkunft})
    _refuse_overlaps(out, where)
    return out


def _refuse_overlaps(spans: Sequence[Mapping[str, Any]], where: str) -> None:
    """No two boundaries of one stroke may claim the same sample."""
    for stroke in sorted({span["stroke"] for span in spans}):
        ordered = sorted(
            ((span["first"], span["last"], position) for position, span in enumerate(spans) if span["stroke"] == stroke)
        )
        for (first, last, position), (next_first, next_last, next_position) in zip(ordered, ordered[1:], strict=False):
            if next_first <= last:
                raise ValueError(
                    f"{where}: letter spans {position} and {next_position} both claim sample(s) "
                    f"{max(first, next_first)}..{min(last, next_last)} of stroke {stroke} — "
                    "one sample belongs to one letter"
                )


def _checked_grund(value: Any, where: str) -> str:
    if value not in SKIP_REASONS:
        raise ValueError(
            f"{where}: a skipped box needs a `grund` out of {', '.join(SKIP_REASONS)} — got {value!r}. "
            "A reason this list has no word for is `other` with a `detail`, never a new string"
        )
    return str(value)


def _checked_detail(value: Any, where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > MAX_DETAIL:
        raise ValueError(f"{where}: `detail` must be a short line (at most {MAX_DETAIL} characters) or absent")
    return value


def check_paths(
    pfade: Sequence[Mapping[str, Any]],
    layout_row: Mapping[str, Any],
    width_px: int,
    height_px: int,
    words: Sequence[str] | None = None,
    pfad_format: int = PFAD_FORMAT,
) -> list[dict[str, Any]]:
    """Validate a pushed path list against the strip it claims to describe.

    Refused rather than clamped, for the same reason the Fleckenmaske is: a
    coordinate mix-up that silently fitted itself to the strip would be stored
    forever and drawn as if it had been followed there.

    Checked: one entry per box at most and no box twice, a box index the
    printed row actually has, a word that agrees with the printed box (and with
    the frozen plan, where `words` is given), strokes in template units, an
    x-height the printed ruling could have produced, and a registration that
    lies on THIS strip.

    `pfad_format` says which shape the push declared, and it is a CONTENT rule
    rather than a version stamp: under format 1 an entry that carries a
    Skip-Eintrag or checked `letter_spans` is refused, under format 2 one that
    hides `letter_spans` in the free `meta` is — either way a row would end up
    stamped with a number its cell does not obey, which is exactly what the
    stored marker exists to prevent.

    NOT checked here: whether that format is one this image supports at all. It
    belongs to the pushed document rather than to an entry, so the envelope's
    own field never reaches this function — `api.routers.eigenhand.write_pfade`
    holds it against `SUPPORTED_FORMATS` and answers 409. A caller that
    assembles its own envelope has to do the same.
    """
    if not isinstance(pfade, Sequence) or isinstance(pfade, (str, bytes)):
        raise ValueError("`pfade` must be a list of per-word entries")
    if len(pfade) > MAX_PFADE:
        raise ValueError(f"{len(pfade)} paths — a strip row carries at most {MAX_PFADE} words")
    boxes = layout_row.get("boxes") or []
    nominal = nominal_xh_px(layout_row, width_px)
    seen: set[int] = set()
    out: list[dict[str, Any]] = []
    for entry in pfade:
        if not isinstance(entry, Mapping):
            raise ValueError("every path entry must be an object")
        index = entry.get("box_index")
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(boxes):
            raise ValueError(f"box_index {index!r} is not a box of this row (it has {len(boxes)})")
        if index in seen:
            raise ValueError(f"box {index} carries two paths — one path per word box")
        seen.add(index)
        where = f"box {index}"
        printed = boxes[index].get("word")
        word = entry.get("word")
        if word != printed:
            raise ValueError(f"{where}: the printed box carries {printed!r}, the path claims {word!r}")
        # The plan is the strip's identity (strip id → words, frozen forever),
        # so a layout that somehow disagreed with it would be caught here
        # rather than stored as a path for a word this strip never held.
        if words is not None and (index >= len(words) or words[index] != word):
            expected = words[index] if index < len(words) else None
            raise ValueError(f"{where}: the frozen plan says {expected!r}, the path says {word!r}")
        verfahren = entry.get("verfahren")
        if not isinstance(verfahren, str) or not 1 <= len(verfahren) <= 64:
            raise ValueError(f"{where}: `verfahren` must name how the path was made (1..64 characters)")
        erzeugt_am = _checked_date(entry.get("erzeugt_am"), where)
        flecken_n = entry.get("flecken_n")
        if flecken_n is not None and (not isinstance(flecken_n, int) or isinstance(flecken_n, bool) or flecken_n < 0):
            raise ValueError(f"{where}: `flecken_n` must be the size of the mask it was followed under")
        common = {
            "box_index": index,
            "word": word,
            "verfahren": verfahren,
            "konfiguration": dict(entry.get("konfiguration") or {}),
            "meta": dict(entry.get("meta") or {}),
            "erzeugt_am": erzeugt_am,
            "flecken_n": flecken_n,
        }
        if pfad_format < SKIP_AND_SPAN_FORMAT:
            for field in FORMAT_2_FIELDS:
                if entry.get(field) is not None:
                    raise ValueError(
                        f"{where}: `{field}` is a Streifen-Pfad format {SKIP_AND_SPAN_FORMAT} field and this push "
                        f"declares format {pfad_format} — push it as {SKIP_AND_SPAN_FORMAT} or leave the field out"
                    )
            xh = _checked_xh(entry.get("xh_px"), height_px, nominal, where)
            out.append(
                {
                    **common,
                    "strokes": _checked_strokes(entry.get("strokes"), where),
                    "registration_px": _checked_registration(
                        entry.get("registration_px"), width_px, height_px, xh, where
                    ),
                    "xh_px": xh,
                }
            )
            continue
        meta = entry.get("meta")
        if isinstance(meta, Mapping) and meta.get(FIELD_SPANS) is not None:
            raise ValueError(
                f"{where}: format {SKIP_AND_SPAN_FORMAT} carries `{FIELD_SPANS}` as a checked field of the entry — "
                "remove the copy in the free `meta`, so a box has one set of boundaries and not two"
            )
        status = entry.get("status") or STATUS_OK
        if status not in STATUS_VALUES:
            raise ValueError(f"{where}: `status` must be one of {', '.join(STATUS_VALUES)} — got {status!r}")
        skipped = status == STATUS_SKIPPED
        if skipped and entry.get("strokes"):
            raise ValueError(f"{where}: a skipped box carries no strokes — it says why there is no path, not one")
        # `is_authored` reads `verfahren` alone, and everything downstream of it
        # assumes a DRAWING: the 409 locks the box, `pull --pfade` archives it,
        # `--replace-authored` demands it be archived first. A skip carries no
        # drawing at all, so an authored one would be a phantom — 409-protected
        # ground truth that nothing can ever be lost from, and it would sail
        # past `displaced_authored` on an empty row, where there is nothing
        # stored for the guard to compare against (found in review, PR #639).
        if skipped and entry.get("verfahren") == AUTHORED:
            raise ValueError(
                f"{where}: a skipped box cannot claim `verfahren: {AUTHORED!r}` — that provenance means a path the "
                "author DREW, and a skip is the statement that there is none"
            )
        if not skipped and entry.get("grund") is not None:
            raise ValueError(f"{where}: `grund` says why a box was SKIPPED — a path that was followed has none")
        # Optional on a skip, required on a path (author decision C): a skipped
        # box may have been refused before anything was registered at all.
        registration = entry.get("registration_px")
        xh_value = entry.get("xh_px")
        if skipped and registration is None and xh_value is None:
            xh, frame = None, None
        else:
            xh = _checked_xh(xh_value, height_px, nominal, where)
            frame = _checked_registration(registration, width_px, height_px, xh, where)
        strokes = [] if skipped else _checked_strokes(entry.get("strokes"), where)
        spans = _checked_spans(entry.get(FIELD_SPANS), strokes, where)
        out.append(
            {
                **common,
                "status": status,
                "grund": _checked_grund(entry.get("grund"), where) if skipped else None,
                "detail": _checked_detail(entry.get("detail"), where),
                "strokes": strokes,
                FIELD_SPANS: spans,
                "registration_px": frame,
                "xh_px": xh,
            }
        )
    return sorted(out, key=lambda item: item["box_index"])


def format_of_entries(entries: Sequence[Mapping[str, Any]]) -> int:
    """The Streifen-Pfad format a push of exactly these entries has to declare.

    A writer does not only push what it produced. `tools.eigenhand.pfad` reads
    the stored list first and pushes the MERGE: the boxes it followed, the ones
    it did not touch, and the author's letter boundaries carried onto its own
    fresh Bahn. `tools.eigenhand.sync` restores entries an archive holds. Both
    therefore put entries on the wire this image would never write itself, and
    a push that declared `PFAD_FORMAT` would be refused by the very content
    rule that keeps a row's stamp honest (found in review, PR #639).

    So the declaration follows the CONTENT rather than the constant: format 2
    where any entry carries a format-2 field, what this image writes otherwise.
    It never over-declares — a cell of plain format-1 entries obeys format 1 —
    and it cannot quietly downgrade a row either: `check_paths` stamps every
    entry it accepts under format 2 with a `status`, and that field is what
    brings the number back on the next push.

    It says nothing about whether the SERVER knows that format. That is the
    envelope's question and stays with `SUPPORTED_FORMATS` and the 409.
    """
    for entry in entries:
        if any(entry.get(field) is not None for field in FORMAT_2_FIELDS):
            return max(PFAD_FORMAT, SKIP_AND_SPAN_FORMAT)
    return PFAD_FORMAT


def push_body(entries: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int, list[int]]:
    """One merged list as it can go on the wire: the entries, the format, what was given up.

    `format_of_entries` alone is not enough, because the two formats disagree
    about where letter boundaries live. A follower run still puts its own
    boundaries in the free `meta` (`tools.pairlab.tintenpfad` writes
    `meta.letter_spans`, the nested-by-stroke shape `spans_of` emits), and
    format 2 refuses exactly that — one box, one set of boundaries. So a body
    that has to be declared 2, because it CARRIES a skip or a corrected
    boundary from the stored row, would be refused over the entries the run
    produced itself (found in review, PR #639).

    They are dropped rather than converted, and the caller says so out loud.
    Converting would mean this image starts writing the checked field, which is
    the next release's job — and it would newly VALIDATE indices that are known
    to predate `cap_word_strokes`, so a run that succeeds today could start
    failing on a boundary nobody has looked at. An `auto` boundary is a
    derivation the next run makes again; that is what makes dropping it
    acceptable and a corrected one unthinkable.

    The third element is the boxes whose free-meta boundaries were given up, so
    the run can name them. Empty whenever the body stays format 1, which is
    every push this image makes on its own.
    """
    pfad_format = format_of_entries(entries)
    if pfad_format < SKIP_AND_SPAN_FORMAT:
        return [dict(entry) for entry in entries], pfad_format, []
    body: list[dict[str, Any]] = []
    dropped: list[int] = []
    for entry in entries:
        meta = entry.get("meta")
        if not isinstance(meta, Mapping) or meta.get(FIELD_SPANS) is None:
            body.append(dict(entry))
            continue
        dropped.append(entry.get("box_index"))
        body.append({**entry, "meta": {key: value for key, value in meta.items() if key != FIELD_SPANS}})
    return body, pfad_format, sorted(index for index in dropped if index is not None)


def is_authored(entry: Mapping[str, Any]) -> bool:
    """Whether this stored path is the author's own hand rather than a follow.

    One predicate rather than a comparison spelled at every call site, and the
    BAHN's half of the answer only: since format 2 a second provenance sits
    inside the entry (`letter_spans[].herkunft`, author decision Q15,
    2026-09-18), and it is read by `authored_spans` beside this.
    """
    return entry.get("verfahren") == AUTHORED


def authored_spans(entry: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The letter boundaries of one entry that the author corrected by hand.

    Defensive about the shape rather than validating it: this reads what is
    already STORED, including rows written under format 1, where the field does
    not exist at all. `check_paths` is where a pushed shape is held to account.
    """
    spans = entry.get(FIELD_SPANS)
    if not isinstance(spans, Sequence) or isinstance(spans, (str, bytes)):
        return []
    return [dict(span) for span in spans if isinstance(span, Mapping) and span.get("herkunft") == AUTHORED]


def _span_key(span: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(span.get(key) for key in ("stroke", "slot", "first", "last"))


def displaced_authored(
    stored: Sequence[Mapping[str, Any]] | None, pushed: Sequence[Mapping[str, Any]]
) -> list[tuple[int, str]]:
    """The hand work a push would take away, per box and per FIELD.

    Two pieces of the author's own hand can sit in one box, and they are given
    up separately, so the comparison is per field rather than per box:

    * `FIELD_PATH` — the stored Bahn is the author's own (`verfahren:
      "authored"`) and the push either leaves the box out (the write is a full
      replacement, so an omitted box is a deleted one) or answers it with a path
      made some other way. Authored over authored passes: that is the author
      correcting his own trace, and it is what keeps a hand-drawing surface
      possible at all.
    * `FIELD_SPANS` — the stored entry carries letter boundaries the author
      corrected, and the push does not carry them back. This is the case the
      box-level rule got WRONG in both directions: it locked a whole box that
      only had corrected boundaries, and it waved through a push that kept the
      `verfahren` and dropped the boundaries inside it. An ordinary re-follow
      of a span-corrected box passes here as long as it brings the boundaries
      along — which `tools.eigenhand.pfad` does by itself.

    An answer BY HAND passes for both fields, and it has to: boundaries are
    drawn on a Bahn and do not outlive it, so a box the author re-draws gives up
    the boundaries that belonged to the old drawing — the same rule
    `tools.eigenhand.pfad` applies to a box handed over. Without it the author
    could not re-draw a box he had corrected at all: dropping the boundaries
    would be this refusal, and bringing them back would be a 422, because they
    index samples the new Bahn no longer has (found in review, PR #639).

    A Skip-Eintrag is NOT an answer by hand, whatever `verfahren` it claims: it
    says there is no path in this box, so letting it pass as „the author
    correcting his own trace" would let an empty entry delete a drawing with
    neither a 409 nor the archive check that hangs off `--replace-authored`.

    Only the LOSS is reported, and only once per box: where the Bahn itself is
    displaced, its boundaries go with it and saying so twice would just make the
    refusal longer.

    Deliberately not part of `check_paths`: this compares against STORED state,
    which makes it the router's 409 rather than the entry-level 422 — the same
    split `format` already follows. Plain Python and no JSONB operator, because
    the HTTP suites run on SQLite.
    """
    answers = {entry.get("box_index"): entry for entry in pushed}
    displaced: list[tuple[int, str]] = []
    for entry in stored or []:
        index = entry.get("box_index")
        if index is None:
            continue
        answer = answers.get(index)
        by_hand = answer is not None and is_authored(answer) and answer.get("status") != STATUS_SKIPPED
        if is_authored(entry) and not by_hand:
            displaced.append((index, FIELD_PATH))
            continue
        if by_hand:
            continue
        kept = authored_spans(entry)
        if not kept:
            continue
        brought = {_span_key(span) for span in authored_spans(answer)} if answer is not None else set()
        if any(_span_key(span) not in brought for span in kept):
            displaced.append((index, FIELD_SPANS))
    return sorted(displaced)
