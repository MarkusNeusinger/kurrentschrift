"""Pydantic schemas for request/response bodies.

Wire-level types only. Persisted canonical/bbox files use the existing
JSON schemas from /mvp/canonical/ — those are not re-defined here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExcludeRect(BaseModel):
    """A whited-out sub-rectangle within a glyph bbox."""

    y0: int
    y1: int
    x0: int
    x1: int


class GlyphBbox(BaseModel):
    """One entry in loth_bboxes.json — main rect + optional calibration + excludes.

    None-able entries in the JSON file (`"a-initial": null`) are returned
    from /bboxes as None and PUT must always send a populated GlyphBbox.
    """

    y0: int
    y1: int
    x0: int
    x1: int
    exclude: list[ExcludeRect] = Field(default_factory=list)
    baseline_y: int | None = None
    midband_y: int | None = None
    start_xy: tuple[int, int] | None = None
    n_anchors: int | None = None


class BboxesResponse(BaseModel):
    """Full content of loth_bboxes.json — what `GET /bboxes` returns."""

    note: str = Field(default="", alias="_note")
    image_size: tuple[int, int]
    bboxes: dict[str, GlyphBbox | None]

    model_config = {"populate_by_name": True}


class StrokePoint(BaseModel):
    """One stylus sample. x/y are chart-global pixel coords (top-left origin)."""

    x: float
    y: float
    pressure: float | None = None
    t: float | None = None  # ms since stroke start, optional


class TraceRequest(BaseModel):
    """POST /canonical/{glyph_key}/trace body."""

    path: list[StrokePoint]
    n_anchors: int | None = None  # falls back to bbox.n_anchors or 14
