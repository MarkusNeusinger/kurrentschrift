"""Pydantic wire types — request/response bodies for the FastAPI routers."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# Anchor-count bound, shared by BboxIn / TraceRequest / ResampleRequest: below 4
# the resampler breaks (single-sample linspace / negative counts), far above it
# the anchor JSONB and the SVG renderers blow up. 1000 is generous headroom over
# the ~50 norm (see core.pipeline.DEFAULT_N_ANCHORS).
NAnchors = Annotated[int, Field(ge=4, le=1000)]


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


class QuizWordOut(BaseModel):
    """A reading-drill word: the clean answer form plus form-similar distractors.

    `fugen` is the optional render form with a `|` morpheme marker (round
    Schluss-s in compounds); `note` glosses dated/rare words in the reveal.
    """

    word: str
    distractors: list[str]
    # Constrained to the two seeded tags (mirrors app/src/lib/api/types.ts).
    era: Literal["modern", "historic"]
    note: str | None = None
    fugen: str | None = None


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


class WordSampleOut(BaseModel):
    """One connected-writing specimen (word or letter pair) from a source's
    `words.json` sidecar — metadata only; the crop bytes come from the sibling
    `/word-samples/{sample_id}/crop` endpoint. `baseline_y`/`midband_y` are
    crop-local pixels so a client can register an engine-written overlay
    (scale = baseline_y − midband_y px per x-height)."""

    id: str
    word: str
    kind: Literal["word", "pair"]
    sample_set: str | None = None  # sidecar `set` tag, e.g. a plate by another writer
    width: int
    height: int
    baseline_y: int
    midband_y: int


# ----------------------------------------------------------------------- Bbox


class MaskStroke(BaseModel):
    """One freeform eraser stroke (German: Radierer): a brush polyline + radius.

    `points` are (x, y) in chart-pixel coords; `radius` is the brush radius in
    chart px. The crop pipeline rasterises these and blanks the covered pixels.
    The fixed-length tuple + positive radius reject malformed payloads with 422
    instead of letting `crop_with_mask` 500 on a bad index.
    """

    points: list[tuple[float, float]]
    radius: float = Field(default=4.0, gt=0)


class Patch(BaseModel):
    """One crop patch (German: eingesetzte Zelle): a donor rect + destination.

    `src` is `[x0, y0, x1, y1]` (the donor region on the same chart), `dst` is
    `[x, y]` (its top-left in the crop), all chart-pixel coords. The crop pipeline
    composites the donor by darken, so only its ink lands. Lets a glyph with no
    own cell borrow another's strokes (e.g. ü/ö taking the umlaut from ä). The
    fixed-length tuples reject malformed payloads with 422 instead of letting
    `crop_with_mask` 500 on a bad index.
    """

    src: tuple[float, float, float, float]
    dst: tuple[float, float]


class GuideConfig(BaseModel):
    """Practice-sheet-style guide lines (Hilfslinien) drawn over a glyph crop.

    Mirrors the worksheet rulers in `app/src/lib/lineatur.ts`: the horizontal
    four-line system (baseline/waist/ascender/descender — baseline and waist
    come from the bbox calibration, the outer two are toggled per glyph) plus
    one or more positionable, angled main lines (slant). Letters like m/n/u need
    several individually-placed slants, hence `slant_xs` (a list of baseline
    crossings; they all share `slant_deg`). Kept here (not on the Source)
    because placement is per glyph; reused later to draw letters and to render
    explanatory diagrams.
    """

    model_config = ConfigDict(extra="ignore")

    # Main-line angle in degrees from the horizontal baseline, matching
    # `Source.slant_deg` (90° = upright; Kurrent um 1900 ~60-70°, the Loth
    # 1866 chart measures ~50°). null => derive from the source slant.
    slant_deg: float | None = None
    # Chart-x where the (first/only) main line crosses baseline_y; kept for
    # backward compat as the single-line fallback when `slant_xs` is unset.
    slant_x: float | None = None
    # Baseline crossings of the slant guide lines (each individually draggable in
    # the wizard). null (never set) => the wizard falls back to a single line at
    # `slant_x`; an explicit empty list means the user removed every line (0 lines
    # is allowed). All lines share `slant_deg`.
    slant_xs: list[float] | None = None
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
    # Manual ink brush (German: Tinten-Pinsel): the eraser's positive twin, same
    # {points, radius} shape (reuses MaskStroke), painted as ink before
    # binarisation. Replace-semantics like mask_strokes (the client resends the
    # full list each save).
    ink_strokes: list[MaskStroke] = Field(default_factory=list)
    # Crop patches (German: eingesetzte Zelle): donor regions from elsewhere on the
    # same chart composited into the crop before binarisation, for glyphs with no
    # own cell (e.g. ü/ö borrowing ä's umlaut). Replace-semantics like ink_strokes
    # — the client holds the full list and resends it on every bbox save.
    patches: list[Patch] = Field(default_factory=list)
    baseline_y: int
    midband_y: int
    # Bounded via the shared `NAnchors` type. Optional like `guides`/`locked`: an
    # omitted value preserves the stored count instead of silently rewriting it
    # on every bbox edit.
    n_anchors: NAnchors | None = None
    # Optional so an omitted `guides` (older clients, scripts, a plain bbox
    # save) is distinguishable from an explicit value: PUT then preserves the
    # stored guides instead of resetting them. See put_bbox.
    guides: GuideConfig | None = None
    # Manual "done" marker (German: gesperrt): the glyph is finished and should
    # not be edited. Optional so an omitted value preserves the stored flag,
    # like `guides`. See put_bbox.
    locked: bool | None = None
    # Per-glyph speck auto-fill (German: Lücken füllen): max enclosed-hole area
    # (px²) to swallow before skeletonisation; 0 = off. Optional so an omitted
    # value preserves the stored setting, like `locked`. See put_bbox.
    fill_holes_max_area: int | None = Field(default=None, ge=0, le=10000)


class BboxOut(BboxIn):
    glyph_key: str
    # Always materialised on the way out (see _to_out), so the response keeps
    # concrete values even though the request body may omit them.
    n_anchors: int
    guides: GuideConfig
    locked: bool
    fill_holes_max_area: int


class BboxStatusOut(BaseModel):
    """Item of `GET /sources/{id}/bboxes/status` — flags + layout scalars only.

    The public quiz gates its vocabulary on locked per glyph_key, and the
    public Tafel additionally lays its "as written" sheet out from the crop
    rectangle + baseline; the full BboxOut list drags every mask/ink/patch
    JSONB blob over the wire for those scalars. This is the slim public
    read (pairs with TemplateSummary's has_data).
    """

    glyph_key: str
    locked: bool
    x0: int
    x1: int
    y0: int
    y1: int
    baseline_y: int


# ----------------------------------------------------------------------- Template


class StrokePoint(BaseModel):
    """One sample from the stylus capture.

    `pen_up` marks the last sample of a stroke before the pen is lifted (German:
    Absetzen); the next point starts a new stroke. Absent/false means the stroke
    continues — so a legacy single-stroke path needs no markers at all.
    """

    x: float
    y: float
    pressure: float | None = None
    t: float | None = None
    pen_up: bool = False


class CouplingPointOut(BaseModel):
    xy: list[float]
    tangent_deg: float
    coupling: Literal["baseline", "midband", "ascender", "descender"]


class TraceRequest(BaseModel):
    """Body of `POST /sources/{id}/templates/{glyph_key}/trace`."""

    glyph: str
    raw_path: list[StrokePoint]
    # Same bounds as BboxIn.n_anchors; None falls back to the stored bbox value.
    n_anchors: NAnchors | None = None
    variant: int = 0
    # A locked glyph (Bbox.locked) rejects writes unless this is set — the lock
    # used to be a UI-only contract; the flag makes overriding it an explicit,
    # deliberate decision (e.g. the diagnostics' "re-derive" button).
    force: bool = False


class ResampleRequest(BaseModel):
    """Body of `POST /sources/{id}/templates/{glyph_key}/resample`.

    `n_anchors=None` means "re-derive this template from its raw_path with the
    CURRENT pipeline code and its current recommended anchor density"
    (DEFAULT_N_ANCHORS, bench-calibrated) — the admin's per-glyph refresh after
    pipeline improvements land. An explicit count still wins (wizard slider).
    """

    n_anchors: NAnchors | None = None
    # See TraceRequest.force — required to resample a locked glyph.
    force: bool = False


class TemplateSummary(BaseModel):
    """List item for the sidebar; `has_data` distinguishes traced vs empty."""

    glyph_key: str
    glyph: str | None = None
    variant: int = 0
    advance: float | None = None
    has_data: bool


class TemplateOut(BaseModel):
    glyph_key: str
    glyph: str
    variant: int
    advance: float
    entry: CouplingPointOut
    exit_pt: CouplingPointOut
    anchors: list[list[float]]
    half_widths: list[float]
    raw_path: list[StrokePoint]
    trace_meta: dict[str, Any]
    measurements: dict[str, Any]
