"""Unit tests for the site-icon builder.

The icons are built once and then only ever LOOKED at, so what breaks silently
gets pinned here: the reading of the `/write/glyphs/{key}.svg` outline, the fit
into the icon square, the even-odd fill that keeps a letter's counters open —
within ONE stroke only — and the ICO's per-size frames.

Nothing here calls the API; that belongs to `__main__`.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from tools import favicon


# An 8x8 square with a 4x4 hole — the smallest outline with a counter.
RING = "M0,0 L8,0 L8,8 L0,8 Z M2,2 L6,2 L6,6 L2,6 Z"
# A second pen stroke: a bar lying across the ring's counter and both walls.
BAR = "M0,3 L8,3 L8,5 L0,5 Z"


def glyph_svg(*path_ds: str) -> str:
    paths = "".join(f'<path d="{d}" fill="#2b2419" fill-rule="evenodd" stroke="none"/>' for d in path_ds)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 10 10" role="img"><title>K</title>'
        '<g class="guides"><line x1="-1" x2="9" y1="0" y2="0" stroke="#c9bda3"/></g>'
        f'<g class="ink">{paths}</g></svg>'
    )


GLYPH_SVG = glyph_svg(RING)


def _rgb(hex_colour: str) -> tuple[int, int, int]:
    return tuple(int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))


def _icon_px(unit_x: float, unit_y: float, size: int) -> tuple[int, int]:
    """Pixel of a point given in the ring's own 8-unit space, after `fit`."""
    bx, by, bw, bh = favicon.GLYPH_BOX
    k = bw / 8  # the square outline is width-limited in the taller box
    top = by + (bh - 8 * k) / 2
    scale = size / favicon.ICON
    return round((bx + unit_x * k) * scale), round((top + unit_y * k) * scale)


def test_glyph_svg_url_is_the_public_single_glyph_render():
    assert favicon.glyph_svg_url() == "https://api.kurrentschrift.ink/sources/suetterlin-1922/write/glyphs/K.svg"
    assert favicon.glyph_svg_url("http://localhost:8000/", glyph_key="ſt").endswith("/write/glyphs/%C5%BFt.svg")


def test_outline_strokes_reads_the_ink_and_skips_the_lineature():
    strokes = favicon.outline_strokes(GLYPH_SVG)

    assert [[len(sub) for sub in stroke] for stroke in strokes] == [[4, 4]]
    assert strokes[0][0][2] == (8.0, 8.0)


def test_outline_strokes_keeps_one_group_per_source_path():
    strokes = favicon.outline_strokes(glyph_svg(RING, BAR))

    assert [len(stroke) for stroke in strokes] == [2, 1]


def test_outline_strokes_refuses_what_pillow_cannot_draw_faithfully():
    with pytest.raises(ValueError, match="unsupported path commands"):
        favicon.outline_strokes(GLYPH_SVG.replace("L8,0", "C8,0 8,0 8,0"))
    with pytest.raises(ValueError, match="stroked path"):
        favicon.outline_strokes(GLYPH_SVG.replace('fill="#2b2419"', 'fill="none"'))
    with pytest.raises(ValueError, match="no <g"):
        favicon.outline_strokes("<svg></svg>")


def test_fit_centres_the_outline_in_the_glyph_box_without_distortion():
    fitted = favicon.fit(favicon.outline_strokes(GLYPH_SVG))
    bx, by, bw, bh = favicon.GLYPH_BOX
    xs = [x for x, _ in fitted[0][0]]
    ys = [y for _, y in fitted[0][0]]

    # a square outline in a taller box: width-limited, vertically centred
    assert min(xs) == pytest.approx(bx) and max(xs) == pytest.approx(bx + bw)
    assert max(ys) - min(ys) == pytest.approx(bw)
    assert (min(ys) + max(ys)) / 2 == pytest.approx(by + bh / 2)


def test_build_svg_is_self_contained_with_one_path_per_stroke():
    svg = favicon.build_svg(favicon.fit(favicon.outline_strokes(glyph_svg(RING, BAR))))

    # an SVG favicon loads no fonts and no external resources
    assert "<text" not in svg and "font-family" not in svg and "href" not in svg
    assert svg.count("<path") == 2 and svg.count('fill-rule="evenodd"') == 2
    assert svg.count(" Z") == 3
    assert favicon.PAPER in svg and favicon.INK in svg and favicon.VIRIDIAN in svg


def test_render_keeps_the_counter_open_and_draws_the_dot():
    icon = favicon.render(favicon.fit(favicon.outline_strokes(GLYPH_SVG)), 64).convert("RGB")
    scale = 64 / favicon.ICON
    dot = (round(favicon.DOT[0] * scale), round(favicon.DOT[1] * scale))

    assert icon.getpixel(_icon_px(4, 4, 64)) == _rgb(favicon.PAPER)  # fill-rule="evenodd"
    assert icon.getpixel(_icon_px(0.5, 4, 64)) == _rgb(favicon.INK)
    assert icon.getpixel(dot) == _rgb(favicon.VIRIDIAN)


def test_overlapping_strokes_stay_ink():
    """Even-odd holds within a stroke; across strokes an overlap is ink, never a hole."""
    # 256 px: the sliver of counter beside the bar is wide enough there that the
    # downscale filter's ringing does not reach its middle.
    icon = favicon.render(favicon.fit(favicon.outline_strokes(glyph_svg(RING, BAR))), 256).convert("RGB")

    assert icon.getpixel(_icon_px(1, 4, 256)) == _rgb(favicon.INK)  # bar over the ring's wall
    assert icon.getpixel(_icon_px(4, 4, 256)) == _rgb(favicon.INK)  # bar through the counter
    assert icon.getpixel(_icon_px(4, 2.5, 256)) == _rgb(favicon.PAPER)  # counter beside the bar


def test_ico_entries_are_the_per_size_renders_not_downscales():
    fitted = favicon.fit(favicon.outline_strokes(GLYPH_SVG))

    with Image.open(BytesIO(favicon.ico_bytes(fitted))) as ico:
        assert sorted(ico.info["sizes"]) == [(s, s) for s in favicon.ICO_SIZES]
        for size in favicon.ICO_SIZES:
            ico.size = (size, size)
            assert ico.copy().convert("RGBA").tobytes() == favicon.render(fitted, size).tobytes()


def test_touch_icon_is_opaque_and_full_bleed():
    touch = favicon.touch_icon(favicon.fit(favicon.outline_strokes(GLYPH_SVG)))

    assert touch.mode == "RGB" and touch.size == (favicon.TOUCH_SIZE, favicon.TOUCH_SIZE)
    assert touch.getpixel((0, 0)) == _rgb(favicon.PAPER)
