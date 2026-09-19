"""Unit tests for the site-icon builder.

The icons are built once and then only ever LOOKED at, so what breaks silently
gets pinned here: the reading of the `/write/glyphs/{key}.svg` outline, the fit
into the icon square, and the even-odd fill that keeps a letter's counters open.

Nothing here calls the API; that belongs to `__main__`.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from tools import favicon


# An 8x8 square with a 4x4 hole — the smallest outline with a counter.
GLYPH_SVG = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 10 10" role="img"><title>K</title>'
    '<g class="guides"><line x1="-1" x2="9" y1="0" y2="0" stroke="#c9bda3"/></g>'
    '<g class="ink"><path d="M0,0 L8,0 L8,8 L0,8 Z M2,2 L6,2 L6,6 L2,6 Z"'
    ' fill="#2b2419" fill-rule="evenodd" stroke="none"/></g></svg>'
)


def _rgb(hex_colour: str) -> tuple[int, int, int]:
    return tuple(int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))


def test_glyph_svg_url_is_the_public_single_glyph_render():
    assert favicon.glyph_svg_url() == "https://api.kurrentschrift.ink/sources/suetterlin-1922/write/glyphs/K.svg"
    assert favicon.glyph_svg_url("http://localhost:8000/", glyph_key="ſt").endswith("/write/glyphs/%C5%BFt.svg")


def test_outline_subpaths_reads_the_ink_and_skips_the_lineature():
    subpaths = favicon.outline_subpaths(GLYPH_SVG)

    assert [len(sub) for sub in subpaths] == [4, 4]
    assert subpaths[0][2] == (8.0, 8.0)


def test_outline_subpaths_refuses_what_pillow_cannot_draw_faithfully():
    with pytest.raises(ValueError, match="unsupported path commands"):
        favicon.outline_subpaths(GLYPH_SVG.replace("L8,0", "C8,0 8,0 8,0"))
    with pytest.raises(ValueError, match="stroked path"):
        favicon.outline_subpaths(GLYPH_SVG.replace('fill="#2b2419"', 'fill="none"'))
    with pytest.raises(ValueError, match="no <g"):
        favicon.outline_subpaths("<svg></svg>")


def test_fit_centres_the_outline_in_the_glyph_box_without_distortion():
    fitted = favicon.fit(favicon.outline_subpaths(GLYPH_SVG))
    bx, by, bw, bh = favicon.GLYPH_BOX
    xs = [x for x, _ in fitted[0]]
    ys = [y for _, y in fitted[0]]

    # a square outline in a taller box: width-limited, vertically centred
    assert min(xs) == pytest.approx(bx) and max(xs) == pytest.approx(bx + bw)
    assert max(ys) - min(ys) == pytest.approx(bw)
    assert (min(ys) + max(ys)) / 2 == pytest.approx(by + bh / 2)


def test_build_svg_is_self_contained_outline_only():
    svg = favicon.build_svg(favicon.fit(favicon.outline_subpaths(GLYPH_SVG)))

    # an SVG favicon loads no fonts and no external resources
    assert "<text" not in svg and "font-family" not in svg and "href" not in svg
    assert 'fill-rule="evenodd"' in svg
    assert svg.count(" Z") == 2
    assert favicon.PAPER in svg and favicon.INK in svg and favicon.VIRIDIAN in svg


def test_render_keeps_the_counter_open_and_draws_the_dot():
    fitted = favicon.fit(favicon.outline_subpaths(GLYPH_SVG))
    icon = favicon.render(fitted, 64).convert("RGB")
    scale = 64 / favicon.ICON
    bx, by, bw, bh = favicon.GLYPH_BOX
    centre = (round((bx + bw / 2) * scale), round((by + bh / 2) * scale))
    wall = (round((bx + bw / 16) * scale), centre[1])
    dot = (round(favicon.DOT[0] * scale), round(favicon.DOT[1] * scale))

    assert icon.getpixel(centre) == _rgb(favicon.PAPER)  # fill-rule="evenodd"
    assert icon.getpixel(wall) == _rgb(favicon.INK)
    assert icon.getpixel(dot) == _rgb(favicon.VIRIDIAN)


def test_ico_carries_every_size_and_the_touch_icon_is_opaque_full_bleed():
    fitted = favicon.fit(favicon.outline_subpaths(GLYPH_SVG))

    with Image.open(BytesIO(favicon.ico_bytes(fitted))) as ico:
        assert sorted(ico.info["sizes"]) == [(s, s) for s in favicon.ICO_SIZES]

    touch = favicon.touch_icon(fitted)
    assert touch.mode == "RGB" and touch.size == (favicon.TOUCH_SIZE, favicon.TOUCH_SIZE)
    assert touch.getpixel((0, 0)) == _rgb(favicon.PAPER)
