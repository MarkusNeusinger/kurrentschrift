"""Chart→fluent body widening at render time (core.pipeline._fluent_widen).

Fully synthetic: a pinched round-letter body (two verticals at 0.30 x-heights)
must open to its FLUENT_BODY_PITCH target on the constant-width (Gleichzug)
writing path, while everything else — unlisted glyphs, the pressure path, the
stored row itself — stays untouched.
"""

from __future__ import annotations

import numpy as np

from core.pipeline import FLUENT_BODY_PITCH, render_payload_for_template


def _pinched_row(glyph: str, pitch: float = 0.30) -> dict:
    """A synthetic single-stroke glyph: entry stub, two verticals `pitch`
    apart joined by a top arc, exit stub — the chart-cell shape in miniature."""
    x2 = 0.5 + pitch
    anchors = [
        [0.0, 0.55],  # pen-down (entry stub)
        [0.25, 0.75],
        [0.5, 1.0],  # top of first vertical
        [0.5, 0.5],
        [0.5, 0.0],  # foot of first vertical
        [x2 - 0.1, 0.9],  # rise
        [x2, 1.0],  # top of second vertical
        [x2, 0.5],
        [x2, 0.0],  # foot of second vertical
        [x2 + 0.2, 0.25],
        [x2 + 0.45, 0.5],  # exit stub tip
    ]
    return {
        "glyph": glyph,
        "anchors": anchors,
        "half_widths": [0.06] * len(anchors),
        "trace_meta": {"stroke_starts": [0]},
        "entry": {"xy": [0.0, 0.55]},
        "exit_pt": {"xy": [x2 + 0.45, 0.5]},
        "advance": x2 + 0.45,
    }


def _verticals_x(payload: dict) -> list[float]:
    """x of near-vertical crossings at mid-height on the rendered centerline."""
    line = np.asarray(payload["centerlines_template"][0], dtype=float)
    xs = []
    for y in (0.35, 0.65):
        c = []
        for (x0, y0), (x1, y1) in zip(line[:-1], line[1:], strict=True):
            if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
                c.append(x0 + (y - y0) / (y1 - y0) * (x1 - x0))
        xs.append(sorted(c))
    verticals = []
    for x in xs[0]:
        near = [xh for xh in xs[1] if abs(xh - x) < 0.15]
        if near:
            verticals.append((x + near[0]) / 2)
    return verticals


def test_pinched_e_opens_to_target_on_gleichzug_path() -> None:
    row = _pinched_row("e")
    entry_before = [*row["entry"]["xy"]]
    exit_before = [*row["exit_pt"]["xy"]]
    advance_before = row["advance"]
    payload = render_payload_for_template(row, [1, 1, 1], "constant", 0.05)
    v = _verticals_x(payload)
    assert len(v) >= 2
    assert abs((max(v) - min(v)) - FLUENT_BODY_PITCH["e"]) < 0.05
    # connection metadata rides along: the exit shifted right by the growth
    assert payload["advance"] > row["advance"]
    assert payload["exit_pt"]["xy"][0] > row["exit_pt"]["xy"][0]
    assert payload["entry"]["xy"] == row["entry"]["xy"]  # entry sits left of the body
    # the stored row is never mutated — the remap copies the nested connection
    # dicts, the only place an in-place edit could actually leak (anchors are
    # re-arrayed by the renderer anyway)
    assert row["entry"]["xy"] == entry_before
    assert row["exit_pt"]["xy"] == exit_before
    assert row["advance"] == advance_before


def test_unlisted_glyph_and_pressure_path_stay_untouched() -> None:
    for glyph, resolver in (("n", "constant"), ("e", "pressure")):
        row = _pinched_row(glyph)
        payload = render_payload_for_template(row, [1, 1, 1], resolver, 0.05 if resolver == "constant" else None)
        v = _verticals_x(payload)
        assert len(v) >= 2
        assert abs((max(v) - min(v)) - 0.30) < 0.05
        assert payload["advance"] == row["advance"]


def test_wide_body_is_a_no_op_never_shrunk() -> None:
    row = _pinched_row("e", pitch=0.55)  # already wider than the 0.40 target
    payload = render_payload_for_template(row, [1, 1, 1], "constant", 0.05)
    v = _verticals_x(payload)
    assert len(v) >= 2
    assert abs((max(v) - min(v)) - 0.55) < 0.05
    assert payload["advance"] == row["advance"]
