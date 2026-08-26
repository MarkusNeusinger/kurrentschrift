"""Pydantic wire types — request/response bodies for the FastAPI routers."""

from datetime import datetime
from typing import Annotated, Any, Literal, get_args

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


class PenOut(BaseModel):
    """The source-pooled writing instrument, flattened (`core.widths.PenStyle`).

    `pressure` carries only `hairline_half` (the pooled Haarstrich half-width);
    `broad_nib` only the three `nib_*` fields (Bandzugfeder calibration). A
    `constant` style has no pen — the pooled Gleichzug nib is its own scalar.
    """

    kind: str
    hairline_half: float | None = None
    nib_width_units: float | None = None
    nib_angle_deg: float | None = None
    nib_edge_fraction: float | None = None


class RenderContextOut(BaseModel):
    """Everything the render path resolves for one source before it draws
    (`api.rendering.RenderContext`), at FULL float precision.

    Admin-gated: the pooled nib/pen is measured geometry pooled over every
    authored template of the source (quellen-und-rechte.md §5), and the public
    surfaces need none of it — they consume the finished `/write` payloads,
    where the numbers are rounded to the 4 decimals the renderer draws at. This
    read exists for the tooling that must REPRODUCE a render bit-for-bit
    offline (`tools/wordbench/fetch_fixtures.py`): a 5th-decimal nib difference
    flips knife-edge ink-clearance decisions and jitters glyph placement, so
    the readback off a rounded payload is not precise enough.
    """

    style_id: str
    style_ratio: list[float]
    slant_deg: float
    width_resolver: str
    # Pooled Gleichzug nib (constant styles only), unrounded; null otherwise or
    # when nothing is traced for the source yet.
    constant_nib_units: float | None = None
    pen: PenOut | None = None


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
    # The sample's rect on the plate page, `[x0, y0, x1, y1]` in PAGE pixels.
    # Occurrence rows (`instances`) store their boxes in page pixels too, so a
    # client needs this origin to place a letter box inside the crop
    # (crop-local = page − rect[:2]). Public like the rest: this is PD-plate
    # measurement metadata from the committed sidecar, not learned data.
    rect: list[int] = Field(min_length=4, max_length=4)


# ------------------------------------------------------------------ Glyph pair


class PairGeometry(BaseModel):
    """Stored override geometry of ONE letter join (redesign R3, proposal B).

    Template units (baseline = 0, midband = 1), both parts relative to the
    LEFT glyph's exit point: `offset` is where the right glyph's entry lands
    (`[dx, dy]`; the composer currently applies the horizontal part),
    `connector` is the join's centerline drawn verbatim instead of the
    generated Übergang."""

    offset: list[float] = Field(min_length=2, max_length=2)
    connector: list[list[float]] = Field(min_length=2, max_length=500)

    def model_post_init(self, __context: Any) -> None:
        for pt in self.connector:
            if len(pt) != 2:
                raise ValueError("connector points must be [x, y] pairs")
            if not all(abs(float(v)) <= 20.0 for v in pt):
                raise ValueError("connector coordinates out of range (template units)")
        if not all(abs(float(v)) <= 20.0 for v in self.offset):
            raise ValueError("offset out of range (template units)")


class GlyphPairIn(BaseModel):
    """Body of `PUT /sources/{id}/pairs/{left_key}/{right_key}`."""

    geometry: PairGeometry
    provenance: Literal["harvested", "authored"]
    # The words.json sample a harvest fitted (e.g. an Abb.-20 pair id).
    specimen_id: str | None = None
    # Freigabe: only approved rows reach the composer.
    approved: bool = False
    variant: int = 0

    def model_post_init(self, __context: Any) -> None:
        # A harvested row without its specimen pointer would be untraceable —
        # the whole point of harvesting is citing the same-hand evidence.
        if self.provenance == "harvested" and not (self.specimen_id or "").strip():
            raise ValueError("harvested pairs must cite their specimen_id")


class GlyphPairOut(BaseModel):
    left_key: str
    right_key: str
    variant: int
    geometry: PairGeometry
    provenance: str
    provenance_source_id: str | None = None
    specimen_id: str | None = None
    approved: bool


# ---------------------------------------------------- Occurrences (handmodell)


class HandIn(BaseModel):
    """The writer a batch of occurrences belongs to (get-or-create).

    `style_id` is taken from the source server-side — a hand is registered
    under the style it was observed writing."""

    id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=255)
    era: str | None = Field(default=None, max_length=64)
    note: str | None = None


class InstanceItem(BaseModel):
    """One glyph occurrence: the per-occurrence M4 fit from a specimen word.

    `anchors` are the fitted anchors CENTERED onto the chart template ("shapes,
    not placements" — the median over them is the Laufform); the rigid
    placement remainder and all fit context (specimen id, slot, neighbours,
    RMSE) live in `measurements`. Crop region in page pixels of the source."""

    glyph_key: str = Field(min_length=1, max_length=32)
    glyph: str = Field(min_length=1, max_length=8)
    position: Literal["initial", "medial", "final"]
    variant: int = 0
    y0: int
    y1: int
    x0: int
    x1: int
    anchors: list[tuple[float, float]] = Field(min_length=4, max_length=4096)
    # Widths are not re-fitted per occurrence (the template prior carries them);
    # an empty list is the honest default.
    half_widths: list[float] = Field(default_factory=list)
    measurements: dict[str, Any] = Field(default_factory=dict)


class InstanceBatchIn(BaseModel):
    """Body of `PUT /sources/{id}/instances` — a harvest run's occurrence rows."""

    hand: HandIn
    # True wipes the source's stored occurrences first (a full re-harvest);
    # False upserts on (glyph, position, variant, y0, x0).
    replace: bool = False
    items: list[InstanceItem] = Field(min_length=1, max_length=5000)


class InstanceOut(BaseModel):
    glyph_key: str
    glyph: str
    position: str
    variant: int
    hand_id: str | None = None
    y0: int
    y1: int
    x0: int
    x1: int
    anchors: list[list[float]]
    half_widths: list[float]
    measurements: dict[str, Any]


class BatchStoreOut(BaseModel):
    hand_id: str
    stored: int
    deleted: int = 0
    # Identities whose stored row is authored (manual admin work) — a traced
    # batch never overwrites them; they are reported instead.
    skipped: int = 0


class PairInstanceItem(BaseModel):
    """One observed letter join: the dissected transition, not the letters.

    `geometry` shares PairGeometry's frame (connector relative to the left
    exit + placement offset) so occurrences compare directly with `glyph_pairs`
    overrides; `measurements` carries the dissection QC."""

    left_key: str = Field(min_length=1, max_length=32)
    right_key: str = Field(min_length=1, max_length=32)
    # 'word' | 'pair': the word plates and the Abb.-20 pair drills are separate
    # id namespaces of one source — kind completes the occurrence identity.
    kind: Literal["word", "pair"] = "word"
    specimen_id: str = Field(min_length=1, max_length=64)
    slot: int = Field(ge=0)
    geometry: PairGeometry
    measurements: dict[str, Any] = Field(default_factory=dict)


class PairInstanceBatchIn(BaseModel):
    """Body of `PUT /sources/{id}/pair-instances`."""

    hand: HandIn
    replace: bool = False
    items: list[PairInstanceItem] = Field(min_length=1, max_length=5000)


class PairInstanceOut(BaseModel):
    left_key: str
    right_key: str
    kind: str
    specimen_id: str
    slot: int
    hand_id: str | None = None
    geometry: PairGeometry
    measurements: dict[str, Any]


class WordInstanceItem(BaseModel):
    """One traced word occurrence — the full learning template's ductus side.

    `strokes` is the pen path in the word's registration frame (template
    units, baseline = 0, midband = 1, x from the word origin): one polyline
    per pen-down stretch. `traced` rows come from the harvest (fitted letter
    strokes; joins live in pair_instances); `authored` rows are manual admin
    traces and survive every re-harvest."""

    kind: Literal["word", "pair"] = "word"
    specimen_id: str = Field(min_length=1, max_length=64)
    word: str = Field(min_length=1, max_length=64)
    slots: list[str] = Field(min_length=1, max_length=64)
    strokes: list[list[list[float]]] = Field(min_length=1, max_length=128)
    provenance: Literal["traced", "authored"] = "traced"
    measurements: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        for stroke in self.strokes:
            if len(stroke) < 2 or len(stroke) > 4096:
                raise ValueError("each stroke needs 2..4096 points")
            for pt in stroke:
                if len(pt) != 2:
                    raise ValueError("stroke points must be [x, y] pairs")
                if not all(abs(float(v)) <= 100.0 for v in pt):
                    raise ValueError("stroke coordinates out of range (template units)")


class WordInstanceBatchIn(BaseModel):
    """Body of `PUT /sources/{id}/word-instances`."""

    hand: HandIn
    replace: bool = False
    items: list[WordInstanceItem] = Field(min_length=1, max_length=500)


class WordInstanceOut(BaseModel):
    kind: str
    specimen_id: str
    word: str
    slots: list[str]
    strokes: list[list[list[float]]]
    provenance: str
    hand_id: str | None = None
    measurements: dict[str, Any]


class AggregateOut(BaseModel):
    """One per-hand aggregate (§12 layer 2, Stufenplan H1).

    `cluster_center` is the per-anchor median of the hand's occurrences — the
    running form in normalised template coordinates (baseline = 0, midband = 1)
    — and `hull.anchor_mad` its per-anchor, per-axis spread in the same units.
    `mean_stats` pools the layer-1 measurements (fit RMSE in px, x-height in px,
    position histogram, distinct specimens).

    `laufform_anchors` is what the engine CURRENTLY writes for this glyph in a
    flowing run (the stored template variant 100), and `laufform_dev_xh` the
    mean anchor distance between it and the median above — the H1 Prüfstein as
    a plain read rather than a side effect of a rebuild. Both are null where the
    comparison has no meaning: a non-base variant (never a Laufform source), a
    glyph with no stored running form yet, or a differing anchor count."""

    glyph_key: str
    glyph: str
    variant: int
    cluster_center: list[list[float]]
    hull: dict[str, Any]
    mean_stats: dict[str, Any]
    n_instances: int
    laufform_anchors: list[list[float]] | None = None
    laufform_dev_xh: float | None = None


class AggregateKeySummary(BaseModel):
    """One rebuilt key in the rebuild report.

    `laufform_dev_xh` is the H1 Prüfstein: the mean anchor distance between the
    recomputed median and the stored Laufform (template variant 100) in
    x-height units; None when there is no such row or its anchor count
    differs."""

    glyph_key: str
    variant: int
    n_instances: int
    laufform_dev_xh: float | None = None


class AggregateRebuildOut(BaseModel):
    """Result of `POST /hands/{hand_id}/aggregates/rebuild`.

    `deleted` counts the hand's previous aggregate rows (the rebuild replaces
    wholesale), `skipped` the occurrences left out per reason (`anchor_shape`,
    `below_min_n`)."""

    hand_id: str
    stored: int
    deleted: int
    skipped: dict[str, int]
    keys: list[AggregateKeySummary]


class AggregateApplyKeySummary(BaseModel):
    """One glyph whose Laufform row was derived from the stored aggregate.

    `laufform_dev_xh` is measured BEFORE the write — the distance the apply
    just closed (None when no Laufform row existed yet or its anchor count
    differed); `created` separates a first write from an update."""

    glyph_key: str
    variant: int
    n_instances: int
    laufform_dev_xh: float | None = None
    created: bool


class AggregateApplySkip(BaseModel):
    """One aggregate the apply left alone, with the reason.

    Reasons: `laufform_variant` / `non_base_variant` (only base-variant
    aggregates may feed the derived row — never itself), `no_base_template`
    (the chart ductus prior is missing), `anchor_count` (aggregate and chart
    row disagree, so the topology would not carry over) and
    `below_min_occurrences` (fewer occurrences than the median needs to reject
    a bad anchor — see `core.aggregate.LAUFFORM_MIN_OCCURRENCES`).

    `n_instances` is filled for `below_min_occurrences`, where the count IS the
    reason; the other reasons leave it null rather than repeating a number that
    played no part in the decision."""

    glyph_key: str
    variant: int
    reason: str
    n_instances: int | None = None


class AggregateApplyOut(BaseModel):
    """Result of `POST /hands/{hand_id}/aggregates/apply-laufform` (Stufenplan
    H1): the stored aggregates written into the style's Laufform rows
    (templates variant 100). Unlike the rebuild this DOES affect rendering,
    which is why it is a separate, deliberate step.

    `excluded` names the glyph keys a `glyph_keys` selection left out — the
    request's own doing, not the endpoint's judgement, hence its own list
    beside `skipped` (which stays the "could not" report). Empty whenever the
    request named no selection at all."""

    hand_id: str
    style_id: str
    applied: list[AggregateApplyKeySummary]
    skipped: list[AggregateApplySkip]
    excluded: list[str] = []


class PairAggregateOut(BaseModel):
    """One per-hand pair aggregate (§12 layer 2, Stufenplan H2).

    The natural transition's distribution, in the same frame as a `glyph_pairs`
    override (template units relative to the LEFT glyph's exit):
    `offset_center` is the median placement offset, `connector_center` the
    per-point median of the arc-length-resampled connector centerlines, and
    `hull` their per-axis spread (`offset_mad`, `connector_mad`). `mean_stats`
    pools the dissection QC (generated + harvested chamfer, ink-gap share, the
    word-plate/pair-drill histogram, distinct specimens)."""

    left_key: str
    right_key: str
    offset_center: list[float]
    connector_center: list[list[float]]
    hull: dict[str, Any]
    mean_stats: dict[str, Any]
    n_instances: int


class PairAggregateKeySummary(BaseModel):
    """One rebuilt pair in the pair-rebuild report.

    `gen_chamfer_mean` is the audit number: the mean distance (x-height units)
    between the GENERATED connector and the specimen skeleton, measured at
    harvest time — „gemessen vs. komponiert" per pair. None when the stored
    occurrences carry no such measurement."""

    left_key: str
    right_key: str
    n_instances: int
    gen_chamfer_mean: float | None = None


class PairAggregateRebuildOut(BaseModel):
    """Result of `POST /hands/{hand_id}/pair-aggregates/rebuild`.

    `deleted` counts the hand's previous pair-aggregate rows (the rebuild
    replaces wholesale), `skipped` the occurrences left out per reason
    (`fit_bad`, `geometry`, `below_min_n`)."""

    hand_id: str
    stored: int
    deleted: int
    skipped: dict[str, int]
    pairs: list[PairAggregateKeySummary]


# ------------------------------------------------------- Work items (Werkbank)


# The stages of the writing path a complaint can be caused by
# (`docs/proposals/optimierungs-werkbank.md` §3), listed in the triage order §5
# prescribes: chart ductus first, an override only ever last. Closing an item
# picks exactly one — a closed vocabulary keeps "which stage causes the most
# complaints" a query instead of a reading task. `not_reproducible` is the
# honest outcome when the complaint could not be observed at all.
WorkItemStage = Literal[
    "chart_ductus", "laufform", "join_rule", "composition", "pair_override", "word_trace", "not_reproducible"
]
WORK_ITEM_STAGES: tuple[str, ...] = get_args(WorkItemStage)

# The row's life cycle: filed -> understood -> closed, plus the two exits.
# 'open' is also where a misunderstood item lands again when the admin rejects
# the session's restatement; 'returned' means the missing piece is the author's
# ground truth (§5.6), so the item stays on the human's side of the table.
WorkItemStatus = Literal["open", "ack", "done", "returned"]


class WorkItemIn(BaseModel):
    """Body of `POST /sources/{id}/work-items` — one filed optimization task.

    `kind` names the marked level and decides which target columns are
    required: 'letter' needs `glyph_key`, 'pair' needs both `left_key` and
    `right_key`, 'word' needs the `word` text or the `specimen_id` it was seen
    in. Registry validation of the glyph keys happens in the router (same
    contract as the occurrence writes).

    'note' is the fourth kind and the only one with no target at all: a general
    small thing — a UI wrinkle, a wording slip, a "look at this later" — that is
    too small for a GitHub issue and belongs to no glyph. Its whole content is
    the `note`, which is therefore the one field it requires."""

    kind: Literal["letter", "pair", "word", "note"]
    glyph_key: str | None = Field(default=None, min_length=1, max_length=32)
    left_key: str | None = Field(default=None, min_length=1, max_length=32)
    right_key: str | None = Field(default=None, min_length=1, max_length=32)
    word: str | None = Field(default=None, min_length=1, max_length=64)
    # Where the issue was seen — the words.json namespace, like the occurrences.
    specimen_kind: Literal["word", "pair"] | None = None
    specimen_id: str | None = Field(default=None, min_length=1, max_length=64)
    note: str = ""

    def model_post_init(self, __context: Any) -> None:
        # An item whose target is ambiguous is unworkable — the whole point of
        # the Auftragskorb is that a session can act on the row alone.
        if self.kind == "letter" and not self.glyph_key:
            raise ValueError("a letter item needs glyph_key")
        if self.kind == "pair" and not (self.left_key and self.right_key):
            raise ValueError("a pair item needs left_key and right_key")
        if self.kind == "word" and not (self.word or self.specimen_id):
            raise ValueError("a word item needs word or specimen_id")
        # A note has no target column to fall back on: an empty one would be an
        # unreadable row nobody can act on.
        if self.kind == "note" and not self.note.strip():
            raise ValueError("a note item needs note text")
        # The specimen reference is only unambiguous as a pair: an id without
        # its namespace (word plates vs Abb.-20 drills) may point at nothing.
        if (self.specimen_id is None) != (self.specimen_kind is None):
            raise ValueError("specimen_id and specimen_kind must be given together")


class WorkItemUpdate(BaseModel):
    """Body of `PATCH /work-items/{item_id}` (or its source-scoped twin) —
    partial update; omitted fields stay untouched.

    This is where the §5 protocol is carried out, and the router enforces the
    two transitions instead of trusting the doctrine:

    - `status='ack'` — the session restates the task in its own words
      (`understanding`) and says whether it could reproduce it (`reproduced`).
      Both are required; the admin sees the restatement in the Auftragskorb and
      can reject it, which puts the row back to 'open'.
    - `status='done'` / `'returned'` — requires the earlier `understanding`, a
      `stage` from the vocabulary and a non-empty `resolution`. An item can
      therefore never be closed by a session that never said what it understood.
    """

    note: str | None = None
    status: WorkItemStatus | None = None
    understanding: str | None = None
    reproduced: Literal["yes", "no", "partly"] | None = None
    stage: WorkItemStage | None = None
    resolution: str | None = None


class WorkItemOut(BaseModel):
    id: int
    # The owning chart source — carried on every row so the source-free
    # `GET /work-items` round-start read stays actionable on its own.
    source_id: str
    kind: str
    glyph_key: str | None = None
    left_key: str | None = None
    right_key: str | None = None
    word: str | None = None
    specimen_kind: str | None = None
    specimen_id: str | None = None
    note: str
    status: str
    understanding: str | None = None
    reproduced: str | None = None
    stage: str | None = None
    resolution: str | None = None
    acked_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


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
    # NOTE: `entry_coupling`/`exit_coupling` used to live here. The coupling
    # height a neighbour joins at is decided by the composer's class rule
    # (`core/compose.py::HIGH_COUPLE_BASES` — round bodies couple high, arcade
    # letters low through the baseline garland), never by a stored label, so the
    # two authored fields were read by nothing. `extra="ignore"` above keeps an
    # older client's payload valid; stored `guides` JSON is left as it is.


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


class EndPointOut(BaseModel):
    """One end of a stroke: where the pen lands/leaves and in which direction.

    Rows authored before the coupling label was dropped still carry a
    `coupling` key in their stored JSON — Pydantic ignores it by default, and
    nothing reads it (the coupling height is the composer's class rule).
    """

    xy: list[float]
    tangent_deg: float


class LaufformUpsert(BaseModel):
    """Body of `PUT /sources/{id}/templates/{glyph_key}/laufform` — the median
    running form (templates LAUFFORM_VARIANT) derived from the specimen words. The
    anchor list must match the chart row's anchor count exactly: the chart
    cell stays the ductus prior (stroke order, crossings), only the geometry
    comes from the written words."""

    anchors: list[tuple[float, float]] = Field(min_length=4, max_length=4096)
    # Number of clean specimen occurrences behind the median — provenance.
    n_occurrences: int = Field(ge=1)


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


class TemplateQualityOut(BaseModel):
    """Item of `GET /sources/{id}/templates/quality` — the score the derivation
    STAMPED onto the row, read straight out of `trace_meta.quality`.

    That is the quality AT AUTHORING TIME (the metric code as it stood when the
    glyph was traced or resampled), not a re-score with today's metric — the
    per-glyph `GET .../templates/{key}/quality` recomputes from the crop, and
    the two diverge the moment the metric changes. Cheap enough for a whole
    alphabet in one request precisely because nothing is recomputed; a letter
    whose stored score looks stale is re-scored (or resampled) there.

    `quality` is null for rows traced before the metric existed. Its shape
    depends on the style's metric (Kurrent pixel/width vs. Sütterlin Gleichzug
    naturalness, qualitaetsmetrik.md §1–§4 vs. §5), hence the open dict.

    One trap for consumers: a derived row (LAUFFORM_VARIANT) inherits the chart
    row's whole `trace_meta` via `build_laufform_canonical`, so it repeats the
    CHART form's score — nothing ever scored the median geometry against a
    crop. Read a variant != 0 score as the prior it came from, not as a verdict
    on the running form.
    """

    glyph_key: str
    variant: int = 0
    quality: dict[str, Any] | None = None


class TemplateOut(BaseModel):
    glyph_key: str
    glyph: str
    variant: int
    advance: float
    entry: EndPointOut
    exit_pt: EndPointOut
    anchors: list[list[float]]
    half_widths: list[float]
    raw_path: list[StrokePoint]
    trace_meta: dict[str, Any]
    measurements: dict[str, Any]


# ----------------------------------------------------------------------- Eigenhand
#
# The own-hand capture chain's admin surface. German field names appear where
# the project's own counting units do (`belege`, `erstbeleg`, `ausbau`,
# `quoten`) and where a value is Kartei DATA rather than an invented
# identifier (`belegt` · `unterwegs` · `geplant`, `angenommen` · `verworfen` ·
# `zurueckgezogen`) — glossar.md holds all of them.


class EigenhandHandsOut(BaseModel):
    """Which hands already have rows, and which styles a new one may use."""

    hands: list[str]
    styles: list[str]


class EigenhandKeyOut(BaseModel):
    """One glyph_key of the plan: how often written, how often planned."""

    key: str
    belege: int
    planned: int


class EigenhandBucketOut(BaseModel):
    """One glyph class (klein · gross · ligatur · ziffer · zeichen)."""

    covered: int
    possible: int
    belege: int
    keys: list[EigenhandKeyOut]


class EigenhandJoinOut(BaseModel):
    item: str
    belege: int
    planned: int


class EigenhandJoinsOut(BaseModel):
    covered: int
    possible: int
    belege: int
    rows: list[EigenhandJoinOut]


class EigenhandQuotenOut(BaseModel):
    """Erstbeleg- and Ausbau-Quote — only where an Übergangsraum table exists."""

    items: int
    erstbeleg: int
    erstbeleg_share: float
    erstbeleg_weighted: float
    soll_belege: int
    ausbau: int
    ausbau_share: float
    ausbau_weighted: float


class EigenhandStripsOut(BaseModel):
    total: int
    belegt: int
    unterwegs: int
    geplant: int


class EigenhandFassungenOut(BaseModel):
    angenommen: int
    verworfen: int
    zurueckgezogen: int


class EigenhandSheetsCountOut(BaseModel):
    printed: int
    last: str | None = None


class EigenhandBestandOut(BaseModel):
    """Everything one hand holds — Ist against what the strip plan can produce."""

    hand: str
    style: str
    strips: EigenhandStripsOut
    fassungen: EigenhandFassungenOut
    sheets: EigenhandSheetsCountOut
    glyphs: dict[str, EigenhandBucketOut]
    joins: EigenhandJoinsOut
    quoten: EigenhandQuotenOut | None = None
    queue: list[str]
    redo: list[str]


class EigenhandSheetIn(BaseModel):
    """Print request — the CLI's flags, with the same meaning."""

    hand: str
    style: str | None = None
    sheets: Annotated[int, Field(ge=1, le=20)] = 1
    rows: Annotated[int, Field(ge=1, le=20)] | None = None
    repeat: Annotated[int, Field(ge=1, le=8)] = 1
    strips: list[str] | None = None
    hints: bool = True
    date: str | None = None


class EigenhandSheetOut(BaseModel):
    sheet: str
    strips: list[str]
    bytes: int


class EigenhandSheetsOut(BaseModel):
    hand: str
    style: str
    sheets: list[EigenhandSheetOut]


class EigenhandSheetImportIn(BaseModel):
    """A Bogen printed LOCALLY, registered so the server stops re-minting its id."""

    style: str
    printed_on: str
    strips: list[str]
    layout: dict[str, Any]
    layout_sha256: str


class EigenhandFassungIn(BaseModel):
    """One judged row, pushed up by the local Siebung — verdict only, no pixels."""

    strip: str
    fassung: str
    sheet: str
    row_index: Annotated[int, Field(ge=0, le=99)]
    attempt: Annotated[int, Field(ge=1, le=99)] = 1
    attempts: Annotated[int, Field(ge=1, le=99)] = 1
    status: Literal["angenommen", "verworfen", "zurueckgezogen"]
    reason: str | None = None
    note: str | None = None
    png_sha256: str | None = None
    filed_on: str | None = None
    # The EFFECTIVE setup of this row, denormalised on purpose: a Fassung has
    # to say out of itself what it was written with, and the day the nib really
    # changes, the break is visible in the data instead of reconstructed.
    feder: str | None = None
    tinte: str | None = None
    papier: str | None = None
    geraet: str | None = None


class EigenhandSyncIn(BaseModel):
    hand: str
    fassungen: list[EigenhandFassungIn]


class EigenhandSyncOut(BaseModel):
    hand: str
    recorded: int
    skipped: int


class EigenhandUebergangsraumIn(BaseModel):
    """The Soll universe as `tools.eigenhand.universe --push` sends it — whole.

    `items` is the COMPLETE table (corpus items ∪ the curated pool's items at
    0.0), because every target is scaled against the table's own maximum and
    the server has no pool to union in. The rest is provenance: which corpus
    bytes (`corpora` checksums), which damping and filters, and which pool
    (`pool_sha256`) this build stands on.

    `name` is pinned: the API knows ONE universe. The column exists so a
    second corpus mix could sit beside it one day — that day brings its own
    routes; until then a different name would be a row nothing can read.
    """

    name: Literal["uebergangsraum"] = "uebergangsraum"
    format: Annotated[int, Field(ge=1)]
    en_weight: Annotated[float, Field(ge=0.0, le=1.0)]
    min_count: Annotated[int, Field(ge=0)]
    min_word_len: Annotated[int, Field(ge=1)]
    corpora: dict[str, str]
    words_used: dict[str, int]
    corpus_items: Annotated[int, Field(ge=0)]
    pool_sha256: Annotated[str, Field(min_length=64, max_length=64)]
    items: Annotated[dict[str, Annotated[float, Field(ge=0.0)]], Field(min_length=1)]


class EigenhandUebergangsraumOut(EigenhandUebergangsraumIn):
    item_count: int
    sha256: str
    updated_at: str | None = None


class EigenhandUebergangsraumStoreOut(BaseModel):
    name: str
    stored: bool  # False = the same build was already there (no-op)
    replaced: bool  # True = a different build was overwritten
    sha256: str


class EigenhandSetupIn(BaseModel):
    """A hand's STANDING setup — typed once, read back by every import.

    Nib, ink and paper are photometric parameters of a whole campaign: keeping
    them in one place is what makes „identisch weiterschreiben" a lookup rather
    than a memory exercise. `geraet` is the capture device — the same two words
    `ingest` and the CLI take: `scanner` · `kamera`.

    The lengths mirror the columns (`String(128)`): without them an over-long
    value is a Postgres `StringDataRightTruncation` — a 500 the SQLite test
    harness cannot even produce, because SQLite ignores varchar limits.
    """

    style: str | None = None
    label: Annotated[str, Field(max_length=128)] | None = None
    feder: Annotated[str, Field(max_length=128)] | None = None
    tinte: Annotated[str, Field(max_length=128)] | None = None
    papier: Annotated[str, Field(max_length=128)] | None = None
    geraet: Annotated[str, Field(max_length=128)] | None = None
    note: str | None = None


class EigenhandSetupOut(EigenhandSetupIn):
    hand: str
    style: str
    updated_at: str | None = None


class EigenhandSetupsOut(BaseModel):
    setups: list[EigenhandSetupOut]


class EigenhandStripOut(BaseModel):
    """One stored strip — metadata only; the pixels come from the image route."""

    strip: str
    fassung: str
    sheet: str
    row_index: int
    width_px: int
    height_px: int
    dpi: float
    crop_origin_mm: list[float]
    sha256: str
    bytes: int
    words: list[str] = []


class EigenhandStripListOut(BaseModel):
    hand: str
    strips: list[EigenhandStripOut]


class EigenhandArchiveOut(BaseModel):
    """One hand's complete bookkeeping as ROWS — what an archive run files.

    The Bestand answers „how far am I"; this answers „what exactly is in the
    tables", which is a different question and the only one a restore check can
    be built on. Strips appear with their sha256 and without their bytes: the
    private archive holds the images, and matching the hashes is what turns
    „repo + archive restores everything" into something mechanical.
    """

    hand: str
    style: str
    setup: EigenhandSetupOut | None = None
    sheets: list[dict[str, Any]]
    fassungen: list[dict[str, Any]]
    strips: list[EigenhandStripOut]


class EigenhandStripIn(BaseModel):
    """A strip image pushed up by `tools.eigenhand.sync --mit-streifen`.

    The PNG travels base64-encoded in JSON rather than as multipart: the whole
    capture chain speaks JSON to this API, and one encoding beats a second
    upload path for ~350 KB. `sha256` is the archive's identity for these
    bytes — the server verifies it instead of trusting it.
    """

    sheet: str
    row_index: Annotated[int, Field(ge=0, le=99)]
    png_base64: str
    width_px: Annotated[int, Field(ge=1, le=20000)]
    height_px: Annotated[int, Field(ge=1, le=20000)]
    dpi: Annotated[float, Field(gt=0, le=4800)]
    # Exactly [x, y] in millimetres. Bounded rather than free: the origin is
    # half the crop arithmetic, so a missing or malformed one would serve a
    # plausible-looking crop of the wrong part of the strip.
    crop_origin_mm: Annotated[list[float], Field(min_length=2, max_length=2)]
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
