"""Pydantic wire types — request/response bodies for the FastAPI routers."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ----------------------------------------------------------------------- Source


class ChartSize(BaseModel):
    w: int
    h: int


class SourceOut(BaseModel):
    id: str
    title: str
    license: str
    chart_path: str
    chart_size: ChartSize
    style_ratio: list[float]
    slant_deg: float
    attribution: str | None = None


# ----------------------------------------------------------------------- Bbox


class ExcludeRect(BaseModel):
    y0: int
    y1: int
    x0: int
    x1: int


class BboxIn(BaseModel):
    """Body of `PUT /sources/{id}/bboxes/{glyph_key}`."""

    model_config = ConfigDict(extra="ignore")

    y0: int
    y1: int
    x0: int
    x1: int
    excludes: list[ExcludeRect] = Field(default_factory=list)
    baseline_y: int
    midband_y: int
    n_anchors: int = 50


class BboxOut(BboxIn):
    glyph_key: str


# ----------------------------------------------------------------------- Glyph


class StrokePoint(BaseModel):
    """One sample from the stylus capture."""

    x: float
    y: float
    pressure: float | None = None
    t: float | None = None


class CouplingPointOut(BaseModel):
    xy: list[float]
    tangent_deg: float
    coupling: Literal["baseline", "midband", "ascender", "descender"]


class TraceRequest(BaseModel):
    """Body of `POST /sources/{id}/glyphs/{glyph_key}/trace`."""

    glyph: str
    position: Literal["initial", "medial", "final"]
    raw_path: list[StrokePoint]
    n_anchors: int | None = None
    variant: int = 0


class ResampleRequest(BaseModel):
    n_anchors: int


class GlyphSummary(BaseModel):
    """List item for the sidebar; `has_data` distinguishes traced vs empty."""

    glyph_key: str
    glyph: str | None = None
    position: str | None = None
    variant: int = 0
    advance: float | None = None
    has_data: bool


class GlyphOut(BaseModel):
    glyph_key: str
    glyph: str
    position: str
    variant: int
    advance: float
    entry: CouplingPointOut
    exit_pt: CouplingPointOut
    anchors: list[list[float]]
    half_widths: list[float]
    raw_path: list[StrokePoint]
    trace_meta: dict[str, Any]
    measurements: dict[str, Any]
