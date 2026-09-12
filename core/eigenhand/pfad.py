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


PFAD_FORMAT = 1

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


def check_paths(
    pfade: Sequence[Mapping[str, Any]],
    layout_row: Mapping[str, Any],
    width_px: int,
    height_px: int,
    words: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Validate a pushed path list against the strip it claims to describe.

    Refused rather than clamped, for the same reason the Fleckenmaske is: a
    coordinate mix-up that silently fitted itself to the strip would be stored
    forever and drawn as if it had been followed there.

    Checked: the declared format, one entry per box at most and no box twice,
    a box index the printed row actually has, a word that agrees with the
    printed box (and with the frozen plan, where `words` is given), strokes in
    template units, and a registration that lies on THIS strip.
    """
    if not isinstance(pfade, Sequence) or isinstance(pfade, (str, bytes)):
        raise ValueError("`pfade` must be a list of per-word entries")
    if len(pfade) > MAX_PFADE:
        raise ValueError(f"{len(pfade)} paths — a strip row carries at most {MAX_PFADE} words")
    boxes = layout_row.get("boxes") or []
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
        xh_px = entry.get("xh_px")
        try:
            xh = float(xh_px)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{where}: `xh_px` must be the path's x-height in strip pixels") from exc
        if not math.isfinite(xh) or not 0.0 < xh <= height_px * 4:
            raise ValueError(f"{where}: x-height {xh} px is not a scale this strip could have")
        out.append(
            {
                "box_index": index,
                "word": word,
                "strokes": _checked_strokes(entry.get("strokes"), where),
                "registration_px": _checked_registration(entry.get("registration_px"), width_px, height_px, xh, where),
                "xh_px": xh,
                "verfahren": verfahren,
                "konfiguration": dict(entry.get("konfiguration") or {}),
                "meta": dict(entry.get("meta") or {}),
                "erzeugt_am": erzeugt_am,
                "flecken_n": flecken_n,
            }
        )
    return sorted(out, key=lambda item: item["box_index"])
