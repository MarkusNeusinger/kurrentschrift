"""The site icons (`app/public/favicon.*`, `apple-touch-icon.png`), from the engine's own writing.

Why a tool. Until 2026-09-19 the icon was a capital K set in the GL-GermanCursive
SHOW FONT, rendered once by hand — the last brand asset that showed somebody
else's typeface instead of the product, which is the contradiction
`tools/ogcard` removed from the share card. It also had no re-buildable source
and no vector form. The icon now takes the route the card takes: one public
render call, `GET /sources/{id}/write/glyphs/K.svg`, whose filled outline is
fitted into the icon square.

What is site-true here, and where its source of truth lives:

* the letter — the written capital K of `PUBLIC_SOURCE_ID`, as `/write/glyphs`
  serves it (outline only; the lineature stays out, a 16 px icon has no room);
* the viridian dot — the header `Wordmark`'s leading dot
  (`app/src/components/HeaderBar`);
* the palette — `app/src/styles/paper.ts`, mirrored like `tools/ogcard` does.

The outline is a closed polygon set (`M`/`L`/`Z` under `fill-rule="evenodd"`),
so Pillow alone rasterises it — no browser, no SVG library: fill each subpath,
XOR the fills, supersample, downscale. The SVG and the rasters share one fitted
geometry, which is what keeps the tab icon and `/favicon.ico` the same mark.

A pen stroke that reads well at 180 px is a hairline at 16 px, so the outline is
thickened by `INK_BOOST` (a same-colour stroke on the SVG path, the same width
drawn along the polygon here).

The glyph geometry is fetched at build time and never committed as data: the
authored ductus is the reserved dataset (`docs/reference/quellen-und-rechte.md`
§5). What lands in the repo is the published icon of one letter — deliberate
product surface, like the share card.
"""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageChops, ImageDraw


REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DIR = REPO_ROOT / "app/public"

PUBLIC_SOURCE_ID = "suetterlin-1922"
PUBLIC_API = "https://api.kurrentschrift.ink"
GLYPH_KEY = "K"

# app/src/styles/paper.ts
PAPER = "#e7dabf"  # paper.bg
INK = "#241a10"  # paper.ink
VIRIDIAN = "#40826d"  # paper.viridian

# Icon geometry, in units of the 32-unit icon square.
ICON = 32
CORNER_RADIUS = 6
GLYPH_BOX = (4.0, 3.5, 20.0, 25.0)  # x, y, width, height the outline is fitted into
DOT = (25.5, 25.0, 2.6)  # cx, cy, r
INK_BOOST = 0.7

ICO_SIZES = (16, 32, 48)
TOUCH_SIZE = 180
SUPERSAMPLE = 8

Point = tuple[float, float]

_INK_GROUP = re.compile(r'<g class="ink">(.*?)</g>', re.S)
_PATH = re.compile(r"<path\b[^>]*>")
_D = re.compile(r'\bd="([^"]+)"')
_SUBPATH = re.compile(r"M([^MZ]+)Z?")
_PAIR = re.compile(r"(-?\d+(?:\.\d+)?)[ ,](-?\d+(?:\.\d+)?)")


def glyph_svg_url(api: str = PUBLIC_API, source_id: str = PUBLIC_SOURCE_ID, glyph_key: str = GLYPH_KEY) -> str:
    """The public single-glyph render call, as a URL."""
    return f"{api.rstrip('/')}/sources/{source_id}/write/glyphs/{quote(glyph_key)}.svg"


def outline_subpaths(glyph_svg: str) -> list[list[Point]]:
    """The filled outline of a `/write/glyphs/{key}.svg` response as closed polygons.

    Only the polygon form is accepted: a curve command or a stroked centreline
    would need a real SVG rasteriser, and silently flattening one would ship an
    icon that differs from the writing it claims to show.
    """
    ink = _INK_GROUP.search(glyph_svg)
    if ink is None:
        raise ValueError('no <g class="ink"> in the glyph SVG')
    subpaths: list[list[Point]] = []
    for tag in _PATH.findall(ink.group(1)):
        if 'fill="none"' in tag:
            raise ValueError("the glyph SVG carries a stroked path; only filled outlines are supported")
        d = _D.search(tag)
        if d is None:
            continue
        if unsupported := set(re.findall(r"[A-Za-z]", d.group(1))) - set("MLZ"):
            raise ValueError(f"unsupported path commands {sorted(unsupported)}; expected M/L/Z polygons")
        for body in _SUBPATH.findall(d.group(1)):
            points = [(float(x), float(y)) for x, y in _PAIR.findall(body)]
            if len(points) >= 3:
                subpaths.append(points)
    if not subpaths:
        raise ValueError("the glyph SVG has no filled outline")
    return subpaths


def fit(subpaths: list[list[Point]], box: tuple[float, float, float, float] = GLYPH_BOX) -> list[list[Point]]:
    """Scale the outline uniformly into `box` and centre it there."""
    xs = [x for sub in subpaths for x, _ in sub]
    ys = [y for sub in subpaths for _, y in sub]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    bx, by, bw, bh = box
    k = min(bw / (x1 - x0), bh / (y1 - y0))
    tx = bx + (bw - (x1 - x0) * k) / 2 - x0 * k
    ty = by + (bh - (y1 - y0) * k) / 2 - y0 * k
    return [[(x * k + tx, y * k + ty) for x, y in sub] for sub in subpaths]


def build_svg(fitted: list[list[Point]], corner_radius: float = CORNER_RADIUS) -> str:
    d = " ".join("M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in sub) + " Z" for sub in fitted)
    cx, cy, r = DOT
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ICON} {ICON}">\n'
        f'  <rect width="{ICON}" height="{ICON}" rx="{corner_radius}" fill="{PAPER}"/>\n'
        f'  <path fill="{INK}" fill-rule="evenodd" stroke="{INK}" stroke-width="{INK_BOOST}" '
        f'stroke-linejoin="round" d="{d}"/>\n'
        f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="{VIRIDIAN}"/>\n'
        "</svg>\n"
    )


def render(fitted: list[list[Point]], size: int, corner_radius: float = CORNER_RADIUS) -> Image.Image:
    """Rasterise the icon at `size` px — the SVG's geometry, drawn by Pillow."""
    big = size * SUPERSAMPLE
    s = big / ICON

    ink = Image.new("1", (big, big), 0)
    for sub in fitted:
        layer = Image.new("1", (big, big), 0)
        ImageDraw.Draw(layer).polygon([(x * s, y * s) for x, y in sub], fill=1)
        ink = ImageChops.logical_xor(ink, layer)  # fill-rule="evenodd"
    boost = ImageDraw.Draw(ink)
    width = max(1, round(INK_BOOST * s))
    for sub in fitted:
        closed = [(x * s, y * s) for x, y in [*sub, sub[0]]]
        boost.line(closed, fill=1, width=width, joint="curve")

    icon = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    draw.rounded_rectangle((0, 0, big - 1, big - 1), radius=corner_radius * s, fill=PAPER)
    icon.paste(Image.new("RGBA", (big, big), INK), (0, 0), ink.convert("L"))
    cx, cy, r = DOT
    draw.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), fill=VIRIDIAN)
    return icon.resize((size, size), Image.LANCZOS)


def ico_bytes(fitted: list[list[Point]]) -> bytes:
    """A multi-size ICO; every entry is drawn at its own size, not scaled from one bitmap."""
    frames = [render(fitted, size) for size in ICO_SIZES]
    out = BytesIO()
    frames[-1].save(out, format="ICO", sizes=[(s, s) for s in ICO_SIZES], append_images=frames[:-1])
    return out.getvalue()


def touch_icon(fitted: list[list[Point]]) -> Image.Image:
    # Full-bleed and opaque: iOS applies its own mask, and transparent corners
    # come out black on a home screen.
    return render(fitted, TOUCH_SIZE, corner_radius=0).convert("RGB")
