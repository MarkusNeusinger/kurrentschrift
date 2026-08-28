"""One written glyph as an SVG document — the `/write/glyphs/{key}.svg` surface.

The JSON render payload (core/pipeline.py::render_payload_for_template) carries
the filled stroke silhouettes as rings; the SPA draws them as SVG paths with
`fill-rule: evenodd` (app/src/lib/svg.ts). This is the same drawing done
server-side, so a client that cannot run the SPA — an assistant asked "what
does the Sütterlin e look like?" — gets an image instead of a number list.
Same geometry, same cache class, same reservation as the JSON (write-api.md).
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


def glyph_svg(payload: dict, *, name: str, height_px: int = 160) -> str:
    """Render a glyph payload (outline rings + guides) as a complete SVG.

    The view box spans the stroke's own extent horizontally and the lineature
    (descender to ascender) vertically, so every glyph of a script sits on the
    same ruling at the same scale — the baseline is drawn solid, the midband
    dashed, ascender and descender dotted. `height_px` fixes the raster size a
    viewer picks; width follows the aspect.
    """
    strokes: Sequence[Sequence[Sequence[Sequence[float]]]] = payload.get("outline_paths") or []
    points = [p for stroke in strokes for ring in stroke for p in ring]
    guides = dict(
        payload.get("template_guides") or {"baseline": 0.0, "midband": 1.0, "ascender": 2.0, "descender": -1.0}
    )

    xs = [float(p[0]) for p in points] or [0.0, 1.0]
    ys = [float(p[1]) for p in points] or [0.0, 1.0]
    min_x, max_x = min(xs) - PAD, max(xs) + PAD
    top = max(float(guides["ascender"]), max(ys)) + PAD
    bottom = min(float(guides["descender"]), min(ys)) - PAD
    vb_w, vb_h = max_x - min_x, top - bottom
    width_px = max(1, round(height_px * vb_w / vb_h))

    dash = {"baseline": "", "midband": ' stroke-dasharray="0.08 0.05"', "ascender": ' stroke-dasharray="0.02 0.05"'}
    dash["descender"] = dash["ascender"]
    lines = "".join(
        f'<line x1="{_fmt(min_x)}" x2="{_fmt(max_x)}" y1="{_fmt(-float(y))}" y2="{_fmt(-float(y))}" '
        f'stroke="{GUIDE}" stroke-width="{_fmt(GUIDE_STROKE)}"{dash.get(key, "")}/>'
        for key, y in guides.items()
    )
    paths = "".join(
        f'<path d="{rings_to_path_d(stroke)}" fill="{INK}" fill-rule="evenodd" stroke="none"/>'
        for stroke in strokes
        if rings_to_path_d(stroke)
    )
    label = html.escape(name, quote=True)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_fmt(min_x)} {_fmt(-top)} {_fmt(vb_w)} {_fmt(vb_h)}" '
        f'width="{width_px}" height="{height_px}" role="img" aria-label="{label}">'
        f"<title>{label}</title>"
        f'<g class="guides">{lines}</g>'
        f'<g class="ink">{paths}</g>'
        "</svg>\n"
    )
