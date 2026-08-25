"""Cutting a single word out of a stored strip — pure millimetre arithmetic.

A word crop needs no storage of its own. The strip image covers one row's whole
Schnittband, the sheet's layout says where every word box sits in millimetres,
and the strip row remembers where its own crop started. That is enough to cut
any word out of any Fassung on demand — the same reasoning that lets the chart
endpoint serve per-glyph crops out of one chart image, only with mm instead of
chart pixels.

Vertically a word crop keeps the FULL strip height. The interesting part of a
word is how far it reaches above the waist and below the baseline, so cropping
to the band would throw away exactly what one wants to look at.

Everything but `cut_png` is arithmetic on millimetres and pixels; `cut_png` is
the one place that touches the image, and it re-encodes the grayscale unchanged
(two-channel doctrine: no binarisation baked into what gets served).
"""

from __future__ import annotations

import io


def px_per_mm(width_px: int, cut_mm: list[float] | tuple[float, ...]) -> float:
    """Scale of a stored strip: its pixel width over the cut rectangle's mm width.

    A row without a `cut_mm` is refused rather than indexed: a Bogen printed
    before the Schnittband existed has none (`tools/eigenhand/ingest.py` still
    carries the legacy branch that cuts such a row), and reaching past the end
    of the list would be an IndexError where every other refusal here is a
    SystemExit the callers turn into a 400.
    """
    if len(cut_mm) < 4:
        raise SystemExit(
            "this row has no Schnittband (`cut_mm`) — its Bogen was printed before the cut geometry "
            "existed, so a word crop cannot be placed in it; reprint the Bogen to get one"
        )
    span = float(cut_mm[2]) - float(cut_mm[0])
    if span <= 0 or width_px <= 0:
        raise SystemExit(f"strip has no usable width (cut span {span} mm, {width_px} px)")
    return width_px / span


def word_box_px(
    box: dict,
    crop_origin_mm: list[float] | tuple[float, ...],
    width_px: int,
    height_px: int,
    cut_mm: list[float] | tuple[float, ...],
    pad_mm: float = 1.0,
) -> tuple[int, int, int, int]:
    """The pixel rectangle of one word box inside a stored strip.

    `pad_mm` widens the cut on both sides: a letter's exit stroke may reach a
    little past its box, and a crop that clips it looks like a broken glyph
    rather than a tight one. Clamped to the strip, so a word at either end
    keeps its padding on the side where there is room.

    A strip without a recorded `crop_origin_mm` is refused rather than assumed
    to start at 0: the origin is half the arithmetic, and guessing it would
    serve a plausible-looking crop of the WRONG part of the strip — silently,
    which is worse than a refusal.
    """
    if len(crop_origin_mm) < 2:
        raise SystemExit(
            "this strip has no recorded crop origin — without it a word cannot be located in it; "
            "re-push the strip with the `crop_origin_mm` its meta.json carries"
        )
    scale = px_per_mm(width_px, cut_mm)
    origin = float(crop_origin_mm[0])
    x0 = (float(box["x0_mm"]) - pad_mm - origin) * scale
    x1 = (float(box["x1_mm"]) + pad_mm - origin) * scale
    left = max(0, min(width_px - 1, int(round(x0))))
    right = max(left + 1, min(width_px, int(round(x1))))
    return left, 0, right, height_px


def find_box(layout_row: dict, word: str | None, index: int | None) -> dict:
    """The layout row's box for a word (by text) or by position.

    Both spellings are accepted because both are natural: the admin view knows
    the word it is showing, a script walking a row knows the index. A word that
    appears twice in one row resolves to its first box — which is why the index
    exists.
    """
    boxes = layout_row.get("boxes") or []
    if index is not None:
        if not 0 <= index < len(boxes):
            raise SystemExit(f"row has {len(boxes)} boxes — there is no box {index}")
        return boxes[index]
    if word is None:
        raise SystemExit("name a word or a box index")
    for box in boxes:
        if box.get("word") == word:
            return box
    known = ", ".join(str(box.get("word")) for box in boxes)
    raise SystemExit(f"{word!r} is not in this row — it carries: {known}")


def cut_png(png: bytes, box: tuple[int, int, int, int]) -> bytes:
    """Cut a pixel rectangle out of stored PNG bytes, grayscale kept as it is.

    Imported lazily so the arithmetic above stays usable where Pillow is not —
    and so a Bestand read never pays for the image stack it does not use.
    """
    from PIL import Image

    with Image.open(io.BytesIO(png)) as image:
        cut = image.crop(box)
        buffer = io.BytesIO()
        cut.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
