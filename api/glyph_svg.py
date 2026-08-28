"""Written glyphs and words as SVG documents — the `/write/glyphs/{key}.svg`
and `/write/word.svg` surfaces.

The JSON payloads (core/pipeline.py::render_payload_for_template for a glyph,
core/compose.py::compose_word for a word) carry the filled stroke silhouettes
as rings and the generated connectors as centerlines; the SPA draws them as
SVG paths (app/src/lib/svg.ts, WrittenGlyph/WrittenWord). This is the same
drawing done server-side, so a client that cannot run the SPA — an assistant
asked "what does the Sütterlin e look like?" or "write Glück in Sütterlin" —
gets an image instead of a number list. Same geometry, same cache class, same
reservation as the JSON (write-api.md).
"""

from __future__ import annotations

import html
from collections.abc import Sequence


# Paper tokens (design-system.md): ink for the stroke, the ruling colour for
# the guide lines. A glyph reads as a specimen, not as a diagram.
INK = "#2b2419"
GUIDE = "#c9bda3"
# Template units: x-height = 1. Padding keeps ascender loops and the guide
# labels' whitespace off the edge.
PAD = 0.15
GUIDE_STROKE = 0.02
_DEFAULT_GUIDES = {"baseline": 0.0, "midband": 1.0, "ascender": 2.0, "descender": -1.0}


def _fmt(v: float) -> str:
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def rings_to_path_d(rings: Sequence[Sequence[Sequence[float]]]) -> str:
    """All rings of one stroke as one path `d` (subpath per ring), y flipped
    from template space (y up) to SVG space (y down) — the twin of the SPA's
    `ringsToPathD(rings, true)`."""
    parts: list[str] = []
    for ring in rings:
        if len(ring) < 3:
            continue
        parts.append(" ".join(f"{'M' if i == 0 else 'L'}{_fmt(x)},{_fmt(-y)}" for i, (x, y) in enumerate(ring)) + " Z")
    return " ".join(parts)


def polyline_to_path_d(points: Sequence[Sequence[float]]) -> str:
    """An open centerline as a path `d`, y flipped like the rings — the twin
    of the SPA's `polylineToPathD` (a generated connector is STROKED)."""
    return " ".join(f"{'M' if i == 0 else 'L'}{_fmt(x)},{_fmt(-y)}" for i, (x, y) in enumerate(points))


def _document(
    *, min_x: float, max_x: float, top: float, bottom: float, guides: dict, ink: str, name: str, height_px: int
) -> str:
    """The SVG around a drawn body: view box spanning the ink horizontally and
    the lineature (descender to ascender) vertically, so every glyph or word of
    a script sits on the same ruling at the same scale — baseline solid, midband
    dashed, ascender and descender dotted. `height_px` fixes the raster size a
    viewer picks; width follows the aspect."""
    vb_w, vb_h = max_x - min_x, top - bottom
    width_px = max(1, round(height_px * vb_w / vb_h))
    dash = {"baseline": "", "midband": ' stroke-dasharray="0.08 0.05"', "ascender": ' stroke-dasharray="0.02 0.05"'}
    dash["descender"] = dash["ascender"]
    # Fixed emission order (bottom to top), independent of the payload dict's
    # order, so two renders of one glyph are byte-identical.
    lines = "".join(
        f'<line x1="{_fmt(min_x)}" x2="{_fmt(max_x)}" y1="{_fmt(-float(guides[key]))}" y2="{_fmt(-float(guides[key]))}" '
        f'stroke="{GUIDE}" stroke-width="{_fmt(GUIDE_STROKE)}"{dash.get(key, "")}/>'
        for key in ("descender", "baseline", "midband", "ascender")
        if key in guides
    )
    label = html.escape(name, quote=True)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_fmt(min_x)} {_fmt(-top)} {_fmt(vb_w)} {_fmt(vb_h)}" '
        f'width="{width_px}" height="{height_px}" role="img" aria-label="{label}">'
        f"<title>{label}</title>"
        f'<g class="guides">{lines}</g>'
        f'<g class="ink">{ink}</g>'
        "</svg>\n"
    )


def glyph_svg(payload: dict, *, name: str, height_px: int = 160) -> str:
    """Render a glyph payload (outline rings + guides) as a complete SVG."""
    strokes: Sequence[Sequence[Sequence[Sequence[float]]]] = payload.get("outline_paths") or []
    points = [p for stroke in strokes for ring in stroke for p in ring]
    guides = dict(payload.get("template_guides") or _DEFAULT_GUIDES)

    xs = [float(p[0]) for p in points] or [0.0, 1.0]
    ys = [float(p[1]) for p in points] or [0.0, 1.0]
    stroke_ds = [d for d in (rings_to_path_d(stroke) for stroke in strokes) if d]
    ink = "".join(f'<path d="{d}" fill="{INK}" fill-rule="evenodd" stroke="none"/>' for d in stroke_ds)
    return _document(
        min_x=min(xs) - PAD,
        max_x=max(xs) + PAD,
        top=max(float(guides["ascender"]), max(ys)) + PAD,
        bottom=min(float(guides["descender"]), min(ys)) - PAD,
        guides=guides,
        ink=ink,
        name=name,
        height_px=height_px,
    )


def word_svg(composed: dict, *, name: str, height_px: int = 160) -> str:
    """Render a composed word (core.compose draw items) as a complete SVG.

    One draw item per glyph — its silhouette rings, filled — and per generated
    connector — its centerline, stroked at the connector's constant width with
    round caps, exactly what WrittenWord.tsx draws. `bounds` and `guides` come
    from the composition; a word with nothing to draw is the caller's 404.
    """
    items: Sequence[dict] = composed.get("items") or []
    bounds = composed.get("bounds") or {}
    guides = dict(composed.get("guides") or _DEFAULT_GUIDES)
    parts: list[str] = []
    for item in items:
        if item.get("rings"):
            d = rings_to_path_d(item["rings"])
            if d:
                parts.append(f'<path d="{d}" fill="{INK}" fill-rule="evenodd" stroke="none"/>')
        elif item.get("centerline"):
            width = float(item.get("stroke_width") or 0.06)
            parts.append(
                f'<path d="{polyline_to_path_d(item["centerline"])}" fill="none" stroke="{INK}" '
                f'stroke-width="{_fmt(width)}" stroke-linecap="round" stroke-linejoin="round"/>'
            )
    min_x = float(bounds.get("min_x", 0.0))
    max_x = float(bounds.get("max_x", min_x + 1.0))
    min_y = float(bounds.get("min_y", 0.0))
    max_y = float(bounds.get("max_y", 1.0))
    return _document(
        min_x=min_x - PAD,
        max_x=max_x + PAD,
        top=max(float(guides["ascender"]), max_y) + PAD,
        bottom=min(float(guides["descender"]), min_y, 0.0) - PAD,
        guides=guides,
        ink="".join(parts),
        name=name,
        height_px=height_px,
    )
