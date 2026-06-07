"""Pydantic wire types — request/response bodies for the FastAPI routers."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ----------------------------------------------------------------------- Style / Hand


class StyleOut(BaseModel):
    """A script family / base template (Grundvorlage): Kurrent, Sütterlin, Offenbacher."""

    id: str
    name: str
    width_resolver: str
    default_slant_deg: float
    default_style_ratio: list[float]
    description: str | None = None
    # Whether a teaching-chart source exists for this style yet (only then can
    # the admin author templates against it). Kurrent (Loth 1866) is authorable;
    # Sütterlin/Offenbacher exist as rows but have no chart bytes yet.
    authorable: bool = False


class HandOut(BaseModel):
    """One writer."""

    id: str
    style_id: str | None = None
    label: str
    era: str | None = None
    note: str | None = None


# ----------------------------------------------------------------------- Source


class ChartSize(BaseModel):
    w: int
    h: int


class SourceOut(BaseModel):
    id: str
    style_id: str
    hand_id: str | None = None
    kind: str
    title: str
    license: str
    chart_path: str
    chart_size: ChartSize
    # Resolved: the per-source override if set, else the style default.
    style_ratio: list[float]
    slant_deg: float
    attribution: str | None = None
    origin_url: str | None = None
    note: str | None = None


# ----------------------------------------------------------------------- Bbox


class MaskStroke(BaseModel):
    """One freeform eraser stroke (German: Radierer): a brush polyline + radius.

    `points` are [x, y] in chart-pixel coords; `radius` is the brush radius in
    chart px. The crop pipeline rasterises these and blanks the covered pixels.
    """

    points: list[list[float]]
    radius: float = 4.0


class GuideConfig(BaseModel):
    """Practice-sheet-style guide lines (Hilfslinien) drawn over a glyph crop.

    Mirrors the worksheet rulers in `app/src/lib/lineatur.ts`: the horizontal
    four-line system (baseline/waist/ascender/descender — baseline and waist
    come from the bbox calibration, the outer two are toggled per glyph) plus a
    positionable, angled main line (slant). Some letters need several parallel
    main lines, hence `slant_count`/`slant_spacing`. Kept here (not on the
    Source) because placement is per glyph; reused later to draw letters and to
    render explanatory diagrams.
    """

    model_config = ConfigDict(extra="ignore")

    # Main-line angle in degrees from the horizontal baseline, matching
    # `Source.slant_deg` (≈65° = typical Kurrent lean; 90° = upright). null =>
    # derive from the source slant.
    slant_deg: float | None = None
    # Chart-x where the (centre) main line crosses baseline_y; the drag handle.
    # null => crop centre.
    slant_x: float | None = None
    # Number of parallel main lines and their horizontal spacing in chart px.
    slant_count: int = 1
    slant_spacing: float = 0.0
    # Whether the ascender/descender rulers apply to this glyph.
    show_ascender: bool = True
    show_descender: bool = True
    # Coupling height of the stroke's entry/exit — the guide line a neighbouring
    # letter joins at (architektur.md §3/§4). Persisted per glyph so the chosen
    # height survives without re-tracing; the trace/resample pipeline writes it
    # onto entry.coupling / exit_pt.coupling.
    entry_coupling: Literal["baseline", "midband", "ascender", "descender"] = "baseline"
    exit_coupling: Literal["baseline", "midband", "ascender", "descender"] = "baseline"


class BboxIn(BaseModel):
    """Body of `PUT /sources/{id}/bboxes/{glyph_key}`."""

    model_config = ConfigDict(extra="ignore")

    y0: int
    y1: int
    x0: int
    x1: int
    mask_strokes: list[MaskStroke] = Field(default_factory=list)
    baseline_y: int
    midband_y: int
    n_anchors: int = 50
    # Optional so an omitted `guides` (older clients, scripts, a plain bbox
    # save) is distinguishable from an explicit value: PUT then preserves the
    # stored guides instead of resetting them. See put_bbox.
    guides: GuideConfig | None = None
    # Manual "done" marker (German: gesperrt): the glyph is finished and should
    # not be edited. Optional so an omitted value preserves the stored flag,
    # like `guides`. See put_bbox.
    locked: bool | None = None


class BboxOut(BboxIn):
    glyph_key: str
    # Always materialised on the way out (see _to_out), so the response keeps a
    # concrete object even though the request body may omit it.
    guides: GuideConfig
    locked: bool


# ----------------------------------------------------------------------- Template


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
    """Body of `POST /sources/{id}/templates/{glyph_key}/trace`."""

    glyph: str
    position: Literal["initial", "medial", "final"]
    raw_path: list[StrokePoint]
    n_anchors: int | None = None
    variant: int = 0


class ResampleRequest(BaseModel):
    n_anchors: int


class TemplateSummary(BaseModel):
    """List item for the sidebar; `has_data` distinguishes traced vs empty."""

    glyph_key: str
    glyph: str | None = None
    position: str | None = None
    variant: int = 0
    advance: float | None = None
    has_data: bool


class TemplateOut(BaseModel):
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
