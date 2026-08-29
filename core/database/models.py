"""SQLAlchemy models — Style, Hand, Source, Bbox, Template, Instance, Aggregate.

Schema (see `docs/concepts/architektur.md` §3 for the library unit, §5 for the
width resolver, §12 for the statistics layers):

- `Style` is a script family / base template (Grundvorlage): Kurrent, Sütterlin,
  Offenbacher. It carries the `width_resolver` (§5) and the default lineature
  ratio + slant. The canonical templates hang off a style, not a single source.
- `Hand` is one writer. Manuscript sources and per-glyph instances reference a
  hand so statistics aggregate per hand (§12, MVP gate 2 allograph separation).
- `Source` is where bytes come from: a teaching chart (`kind="chart"`, e.g. Loth
  1866) or a manuscript page (`kind="manuscript"`). `chart_path` is relative to
  the repo root and points at the bytes on disk; the DB never stores the image.
- `Bbox` is the per-source crop config for one glyph_key on a chart: rectangle,
  freeform eraser `mask_strokes`, baseline/midband calibration, guides, lock.
- `Template` is the canonical ductus prior for a (style, glyph, position,
  variant) — anchors, half-widths, raw stylus path, entry/exit. This is §3's
  shared `canonical`. One template per style; `provenance_source_id` records the
  chart it was traced from.
- `Instance` is one glyph occurrence extracted from a real text (a manuscript
  source / hand). It holds the per-instance fit (§3 `control_points`) plus
  `measurements` for the §12 layer-1 statistics. Many rows per (glyph, position,
  variant). Defined now; the import pipeline that fills it is post-MVP.
- `Aggregate` is the §12 layer-2 per-hand aggregate (cluster centre + hull) per
  (hand, glyph, position, variant). Defined now; filled later.
"""

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database.connection import Base


# Portable JSON column type: JSONB on Postgres (runtime behavior unchanged),
# generic JSON on other dialects so the HTTP test harness can create the schema
# on SQLite (aiosqlite). Alembic migrations declare their column types
# themselves (sqlalchemy.dialects.postgresql.JSONB) and are unaffected.
PORTABLE_JSON = JSON().with_variant(JSONB(), "postgresql")

GLYPH_KEY_MAX = 32
GLYPH_CHAR_MAX = 8
POSITION_MAX = 16
SOURCE_ID_MAX = 64
STYLE_ID_MAX = 32
HAND_ID_MAX = 64
KIND_MAX = 16
WIDTH_RESOLVER_MAX = 16


class Style(Base):
    """A script family / base template (Grundvorlage).

    `width_resolver` selects how `half_widths` is rendered (architektur.md §5):
    `pressure` = Kurrent Spitzfeder Schwellzug, `constant` = Sütterlin uniform,
    `broad_nib` = Offenbacher Breitfeder. `default_style_ratio` is
    [ascender, x_height, descender] (Kurrent = [2, 1, 2]); `default_slant_deg`
    is the dominant slant from the baseline (90 = upright; 65 = literature
    value for Kurrent um 1900 — individual charts differ, e.g. Loth 1866
    measures ~50°). A source may override both per chart.
    """

    __tablename__ = "styles"

    id: Mapped[str] = mapped_column(String(STYLE_ID_MAX), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    width_resolver: Mapped[str] = mapped_column(String(WIDTH_RESOLVER_MAX), nullable=False, server_default="pressure")
    default_slant_deg: Mapped[float] = mapped_column(Float, nullable=False, server_default="65")
    default_style_ratio: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[2, 1, 2]")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sources: Mapped[list["Source"]] = relationship(back_populates="style", cascade="all, delete-orphan")
    templates: Mapped[list["Template"]] = relationship(back_populates="style", cascade="all, delete-orphan")


class Hand(Base):
    """One writer. Groups manuscript sources + instances of a single hand."""

    __tablename__ = "hands"

    id: Mapped[str] = mapped_column(String(HAND_ID_MAX), primary_key=True)
    style_id: Mapped[str | None] = mapped_column(
        String(STYLE_ID_MAX), ForeignKey("styles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    era: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Source(Base):
    """Where bytes come from: a teaching chart or a manuscript page.

    `chart_path` is relative to the repo root (e.g. `data/sources/loth-1866/
    chart.jpg`). `style_ratio` / `slant_deg` are optional per-source overrides of
    the style defaults (a particular chart may be measured precisely); null =>
    fall back to the style.
    """

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(SOURCE_ID_MAX), primary_key=True)
    style_id: Mapped[str] = mapped_column(
        String(STYLE_ID_MAX), ForeignKey("styles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hand_id: Mapped[str | None] = mapped_column(
        String(HAND_ID_MAX), ForeignKey("hands.id", ondelete="SET NULL"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(KIND_MAX), nullable=False, server_default="chart")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    license: Mapped[str] = mapped_column(String(64), nullable=False)
    chart_path: Mapped[str] = mapped_column(String(512), nullable=False)
    chart_size: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False)
    # Per-source overrides of the style defaults; null => use the style's values.
    style_ratio: Mapped[list | None] = mapped_column(PORTABLE_JSON, nullable=True)
    slant_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    origin_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    style: Mapped[Style] = relationship(back_populates="sources")
    bboxes: Mapped[list["Bbox"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class Bbox(Base):
    """Crop rectangle + eraser mask + baseline/midband calibration for one glyph.

    `mask_strokes` is the freeform eraser (German: Radierer): a list of brush
    strokes `[{points: [[x, y], ...], radius}]` in chart-pixel coords. The crop
    pipeline rasterises them to a boolean mask and blanks those pixels *before*
    skeletonisation, so neighbouring-letter ink can't pollute the skeleton.
    """

    __tablename__ = "bboxes"
    __table_args__ = (UniqueConstraint("source_id", "glyph_key", name="uq_bbox_source_glyph"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        String(SOURCE_ID_MAX), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    glyph_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False)

    y0: Mapped[int] = mapped_column(Integer, nullable=False)
    y1: Mapped[int] = mapped_column(Integer, nullable=False)
    x0: Mapped[int] = mapped_column(Integer, nullable=False)
    x1: Mapped[int] = mapped_column(Integer, nullable=False)
    # Freeform eraser strokes (German: Radierer); see class docstring. JSONB list
    # of {points: [[x, y], ...], radius}. Replaces the old rectangle `excludes`.
    mask_strokes: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[]")
    # Manual ink brush (German: Tinten-Pinsel): the eraser's positive twin — same
    # {points, radius} stroke shape, but painted as ink (black) before binarisation
    # instead of blanked, to close paper-coloured specks/gaps inside a stroke the
    # auto-fill can't reach (e.g. a gap open to the background).
    ink_strokes: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[]")
    # Per-glyph speck auto-fill (German: Lücken füllen): max area (px²) of an
    # enclosed background hole to swallow before skeletonisation; 0 = off (default,
    # so existing glyphs stay bit-identical). See core.extract.fill_small_holes.
    fill_holes_max_area: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # Crop patches (German: eingesetzte Zelle): donor regions copied from elsewhere
    # on the *same* chart and composited into the crop before binarisation, each
    # {src: [x0, y0, x1, y1], dst: [x, y]} (source rect + destination top-left, all
    # chart-pixel coords). For glyphs with no own cell — e.g. the Sütterlin ü/ö
    # borrowing the two umlaut strokes from the ä cell. Composited by darken
    # (np.minimum), so only the donor's ink lands, never its background. See
    # core.chart.crop_with_mask.
    patches: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[]")
    baseline_y: Mapped[int] = mapped_column(Integer, nullable=False)
    midband_y: Mapped[int] = mapped_column(Integer, nullable=False)
    n_anchors: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    # Guide lines drawn over the crop (German: Hilfslinien): the four-line system
    # (Grundlinie/Mittellinie/Oberlinie/Unterlinie) plus a positionable, angled
    # main line (slant). Open JSONB; see GuideConfig in api/schemas.py.
    guides: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False, server_default="{}")
    # Manual "done" marker (German: gesperrt): a finished glyph is locked so it
    # reads as complete and is protected from accidental move/resize/redraw. The
    # wizard's final "approve" step sets this; unlocking re-enables editing.
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    source: Mapped[Source] = relationship(back_populates="bboxes")

    def to_pipeline_dict(self) -> dict:
        """The crop-affecting fields the extraction pipeline reads.

        Exactly the keys `core.chart.crop_with_mask` + `core.extract.
        binarize_adaptive` consume: the rectangle plus the eraser, donor patches,
        ink brush and speck auto-fill. The ONE serializer so a new crop-affecting
        field (as `patches` recently was) can't be added to the crop preview but
        silently dropped from the trace/resample/diagnostic derivation — or vice
        versa. The derivation dict (templates router) layers baseline/midband/
        n_anchors/coupling on top of this; the bbox read response coerces it into
        the Pydantic `BboxOut`.
        """
        return {
            "y0": self.y0,
            "y1": self.y1,
            "x0": self.x0,
            "x1": self.x1,
            "mask_strokes": list(self.mask_strokes),
            "ink_strokes": list(self.ink_strokes),
            "patches": list(self.patches),
            "fill_holes_max_area": int(self.fill_holes_max_area),
        }


# The templates variant number reserved for the derived median RUNNING form
# (Laufform, jul31). Deliberately far from the authored chart-form variants,
# which occupy 1..n (the "A = A" teaching-chart alternatives — Sütterlin Q
# and ü carry variants 1+2): the first Laufform write-up used variant 1 and
# silently overwrote an authored row via the upsert. Authored variants and
# derived forms must never share a number range.
LAUFFORM_VARIANT = 100


class Template(Base):
    """Canonical ductus template (Grundvorlage) for a (style, glyph, variant).

    One row per glyph since the position removal (redesign R2) — the word
    position is render context in `core/shaping.py`, not a stored form; true
    allographs (ſ vs s) are separate glyphs with separate keys.

    `anchors` + `half_widths` are in normalised template coordinates (baseline=0,
    midband=1). `raw_path` is the dense stylus capture in chart-pixel coords, kept
    so /resample can re-derive anchors with a different n_anchors without the user
    redrawing. `provenance_source_id` is the teaching chart this canonical was
    traced from. `measurements` holds the authored trace's own derived stats
    (slant_deg, mean_half_width_px, …); per-text-occurrence statistics live on
    `Instance`, not here (§12 layer 1).
    """

    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("style_id", "glyph", "variant", name="uq_template_style_gv"),
        # Every read keys on glyph_key (scalar_one_or_none) — two rows sharing a
        # key would 500 every public /write. The routers keep their friendly
        # 409 backstops; this makes the invariant structural (migration 0015).
        UniqueConstraint("style_id", "glyph_key", "variant", name="uq_template_style_key_variant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    style_id: Mapped[str] = mapped_column(
        String(STYLE_ID_MAX), ForeignKey("styles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provenance_source_id: Mapped[str | None] = mapped_column(
        String(SOURCE_ID_MAX), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    glyph_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False, index=True)
    glyph: Mapped[str] = mapped_column(String(GLYPH_CHAR_MAX), nullable=False)
    variant: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    advance: Mapped[float] = mapped_column(Float, nullable=False)
    entry: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False)
    exit_pt: Mapped[dict] = mapped_column("exit_pt", PORTABLE_JSON, nullable=False)

    anchors: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False)
    half_widths: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False)

    raw_path: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False)
    trace_meta: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False)
    measurements: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    style: Mapped[Style] = relationship(back_populates="templates")


def template_render_row(t: Template) -> dict:
    """`Template` → the plain dict the render layer consumes
    (`core.pipeline.render_payload_for_template`).

    THE single row builder for every production render path — `/write/*` and
    the labs' live-DB mirror (`tools/wordlab/cases.py`). `glyph` belongs in it:
    `core.pipeline._fluent_widen` keys the round-letter body widening on that
    field, and two hand-rolled copies of this dict each dropped it, so `/write`
    composed without the widening while the wordbench fixtures (which carry
    `glyph`) measured with it (issue #289). The fixture exporter's row is this
    shape plus bookkeeping; `tests/test_render_row.py` pins the two together.
    """
    return {
        "glyph": t.glyph,
        "anchors": list(t.anchors),
        "half_widths": list(t.half_widths),
        "trace_meta": dict(t.trace_meta or {}),
        "entry": dict(t.entry) if t.entry else {},
        "exit_pt": dict(t.exit_pt) if t.exit_pt else {},
        "advance": t.advance,
    }


class Instance(Base):
    """One glyph occurrence extracted from a real text (post-MVP import target).

    Holds the per-instance fit (§3 `control_points`) and `measurements` for the
    §12 layer-1 statistics. `template_id` links to the canonical it was fitted
    against. Defined now so the schema is ready; the extraction pipeline is
    post-MVP. Crop region (y0/y1/x0/x1) locates the occurrence on the page.
    """

    __tablename__ = "instances"
    __table_args__ = (
        UniqueConstraint("source_id", "glyph", "position", "variant", "y0", "x0", name="uq_instance_loc"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        String(SOURCE_ID_MAX), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hand_id: Mapped[str | None] = mapped_column(
        String(HAND_ID_MAX), ForeignKey("hands.id", ondelete="SET NULL"), nullable=True, index=True
    )
    template_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("templates.id", ondelete="SET NULL"), nullable=True
    )
    glyph_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False, index=True)
    glyph: Mapped[str] = mapped_column(String(GLYPH_CHAR_MAX), nullable=False)
    position: Mapped[str] = mapped_column(String(POSITION_MAX), nullable=False)
    variant: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    y0: Mapped[int] = mapped_column(Integer, nullable=False)
    y1: Mapped[int] = mapped_column(Integer, nullable=False)
    x0: Mapped[int] = mapped_column(Integer, nullable=False)
    x1: Mapped[int] = mapped_column(Integer, nullable=False)

    anchors: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False)
    half_widths: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False)
    raw_path: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[]")
    measurements: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Aggregate(Base):
    """Per-hand aggregate (§12 layer 2) per (hand, glyph_key, variant).

    Populated by the aggregates rebuild (Stufenplan H1) from the stored
    `instances` of one hand: `cluster_center` is the per-anchor median — the
    Laufform, since occurrence anchors are stored centered ("shapes, not
    placements") — `hull` the per-anchor spread (MAD per axis), `mean_stats`
    the pooled layer-1 statistics. Statistics are computed per hand, never
    averaged across hands (quellen-und-rechte.md §7).
    """

    __tablename__ = "aggregates"
    __table_args__ = (UniqueConstraint("hand_id", "glyph_key", "variant", name="uq_aggregate_hand_kv"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hand_id: Mapped[str] = mapped_column(
        String(HAND_ID_MAX), ForeignKey("hands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    glyph_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False, index=True)
    glyph: Mapped[str] = mapped_column(String(GLYPH_CHAR_MAX), nullable=False)
    variant: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    cluster_center: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[]")
    hull: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False, server_default="{}")
    mean_stats: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False, server_default="{}")
    n_instances: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PairAggregate(Base):
    """Per-hand pair aggregate (§12 layer 2) per (hand, left_key, right_key).

    Populated by the pair-aggregates rebuild (Stufenplan H2) from the stored
    `pair_instances` of one hand: the natural transition's distribution —
    `offset_center` the median placement offset, `connector_center` the
    per-point median of the arc-length-resampled connector centerlines (both in
    the `glyph_pairs` frame, template units relative to the left glyph's exit),
    `hull` their per-axis MAD spread, `mean_stats` the pooled dissection QC.
    Statistics are computed per hand, never averaged across hands
    (quellen-und-rechte.md §7).

    Read-only with respect to rendering: `glyph_pairs` stays the sparse verbatim
    override (redesign R3) and the §4 join generator stays the default — this
    table is measurement, and its first consumers are report surfaces.
    """

    __tablename__ = "pair_aggregates"
    __table_args__ = (UniqueConstraint("hand_id", "left_key", "right_key", name="uq_pair_aggregate_hand_lr"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hand_id: Mapped[str] = mapped_column(
        String(HAND_ID_MAX), ForeignKey("hands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    left_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False, index=True)
    right_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False, index=True)

    offset_center: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[]")
    connector_center: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[]")
    hull: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False, server_default="{}")
    mean_stats: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False, server_default="{}")
    n_instances: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GlyphPair(Base):
    """An observed/authored letter-pair override (redesign R3, proposal B).

    The §4 generator stays the DEFAULT for every join; a row here is a sparse
    opt-in override for ONE adjacent pair `(left_key, right_key)` within a
    style, used by `core/compose.py` only when `approved` is true. `geometry`
    (JSONB, see PairGeometry in api/schemas.py) carries the connector
    centerline relative to the left glyph's exit plus the right glyph's
    placement offset — template units, baseline = 0, midband = 1.

    `provenance` records how the row came to be: `harvested` (M4-fitted from a
    same-hand specimen; `provenance_source_id` + `specimen_id` point to the
    words.json sample) or `authored` (drawn freehand in the pair editor — the
    marked fallback for pairs without a specimen; never a wordbench reference).
    """

    __tablename__ = "glyph_pairs"
    __table_args__ = (
        UniqueConstraint("style_id", "left_key", "right_key", "variant", name="uq_glyph_pair_style_lr_variant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    style_id: Mapped[str] = mapped_column(
        String(STYLE_ID_MAX), ForeignKey("styles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    left_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False)
    right_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False)
    variant: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    geometry: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False)
    provenance: Mapped[str] = mapped_column(String(16), nullable=False)  # 'harvested' | 'authored'
    provenance_source_id: Mapped[str | None] = mapped_column(
        String(SOURCE_ID_MAX), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    # The words.json sample the harvest fitted (e.g. an Abb.-20 pair id).
    specimen_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Freigabe: only approved rows reach the composer; a fresh harvest lands
    # unapproved so the pair editor stays the human gate.
    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PairInstance(Base):
    """One observed letter-join occurrence from a specimen (handmodell plan H2).

    The per-occurrence layer under the sparse `glyph_pairs` overrides: every
    clean dissection of a joined adjacent pair on a specimen plate is one row —
    the natural transition itself, not the letters. `geometry` uses the SAME
    frame as `GlyphPair.geometry` (connector centerline relative to the left
    glyph's exit + placement offset, template units) so occurrences and
    overrides compare directly; `measurements` carries the dissection QC
    (independent-fit residuals, chamfers, ink-gap flag, …). Statistics over
    these rows are computed per hand, never across hands
    (quellen-und-rechte.md §7).
    """

    __tablename__ = "pair_instances"
    __table_args__ = (UniqueConstraint("source_id", "kind", "specimen_id", "slot", name="uq_pair_instance_occurrence"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        String(SOURCE_ID_MAX), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hand_id: Mapped[str | None] = mapped_column(
        String(HAND_ID_MAX), ForeignKey("hands.id", ondelete="SET NULL"), nullable=True, index=True
    )
    left_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False, index=True)
    right_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False, index=True)
    # The words.json sample the join was observed in + the left letter's slot
    # index within it. `kind` ('word' | 'pair') completes the identity: the
    # word plates and the Abb.-20 pair drills are separate id namespaces of
    # the same source.
    kind: Mapped[str] = mapped_column(String(KIND_MAX), nullable=False, server_default="word")
    specimen_id: Mapped[str] = mapped_column(String(64), nullable=False)
    slot: Mapped[int] = mapped_column(Integer, nullable=False)

    geometry: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False)
    measurements: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WordInstance(Base):
    """One traced word occurrence from a specimen — the full learning template.

    The word level of the occurrence layer: the specimen crop (served by the
    word-samples endpoints from the words.json rect) paired with the traced
    ductus and its slot labels. `strokes` holds the pen path in template units
    of the word's registration frame (baseline = 0, midband = 1, x from the
    word origin), one polyline per pen-down stretch — lifts only where the
    writing itself lifts. A `traced` row stores the harvest's M4-fitted letter
    strokes in writing order (the joins live in `pair_instances` under the
    same `(kind, specimen_id)` — together they assemble the continuous
    one-flow path); an `authored` row is a manually traced full path from the
    admin (the training-set growth loop) and is NEVER overwritten by a
    re-harvest — only another authored write replaces it.
    """

    __tablename__ = "word_instances"
    __table_args__ = (UniqueConstraint("source_id", "kind", "specimen_id", name="uq_word_instance_occurrence"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        String(SOURCE_ID_MAX), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hand_id: Mapped[str | None] = mapped_column(
        String(HAND_ID_MAX), ForeignKey("hands.id", ondelete="SET NULL"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(KIND_MAX), nullable=False, server_default="word")
    specimen_id: Mapped[str] = mapped_column(String(64), nullable=False)
    word: Mapped[str] = mapped_column(String(64), nullable=False)

    # Ordered glyph_keys of the shaped word — the labels of the training pair.
    slots: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False)
    strokes: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False)
    provenance: Mapped[str] = mapped_column(String(16), nullable=False)  # 'traced' | 'authored'
    measurements: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WorkItem(Base):
    """One filed optimization task — the Auftragskorb of the Werkbank (stage W1).

    The admin's channel into a working session: instead of screenshotting a bad
    letter, join or word and describing it in prose, they mark the element in
    the Werkbank and file a row here — `kind` names the level ('letter' | 'pair'
    | 'word'), the key columns name the element, `specimen_kind`/`specimen_id`
    (words.json namespace, same semantics as `PairInstance`) name where the
    issue was seen, and `note` carries the observation. That is the whole human
    side — everything after it is the working session's protocol
    (`docs/proposals/optimierungs-werkbank.md` §5, stage W4).

    The fourth kind, 'note', carries no target at all: a general small thing —
    an admin-UI wrinkle, a wording slip — jotted straight into the Korb because
    it is too small for a GitHub issue and belongs to no glyph. Its whole
    content is the `note`. It runs the same protocol minus the `stage`, which
    names a stage of the WRITING path and has nothing true to say about it.

    A session may not silently close a row. Before it changes anything it
    restates the task in its own words and says whether it could reproduce the
    complaint (`understanding` + `reproduced`, status 'ack'); when it is done it
    names the diagnosed stage of the writing path (`stage`) and what changed
    (`resolution`, status 'done'), or hands the row back when the missing piece
    is the author's ground truth (status 'returned'). The API enforces those
    fields, so the closed rows accumulate into a searchable archive of
    symptom → diagnosis → change → measured effect.

    Internal work notes, not measurement and not content — every endpoint is
    admin-gated, and nothing here ever affects rendering. See
    `docs/proposals/handmodell-stufenplan.md`.
    """

    __tablename__ = "work_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        String(SOURCE_ID_MAX), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The marked level: 'letter' (one glyph_key) | 'pair' (left+right) | 'word'
    # | 'note' (no target at all, the text is the task).
    kind: Mapped[str] = mapped_column(String(KIND_MAX), nullable=False)
    glyph_key: Mapped[str | None] = mapped_column(String(GLYPH_KEY_MAX), nullable=True)
    left_key: Mapped[str | None] = mapped_column(String(GLYPH_KEY_MAX), nullable=True)
    right_key: Mapped[str | None] = mapped_column(String(GLYPH_KEY_MAX), nullable=True)
    # The word text for kind 'word'; optional context for the other kinds (the
    # word the bad letter or join was spotted in).
    word: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Where it was seen: the words.json sample, its id namespace in
    # `specimen_kind` ('word' | 'pair') exactly like the occurrence rows.
    specimen_kind: Mapped[str | None] = mapped_column(String(KIND_MAX), nullable=True)
    specimen_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    # 'open' (filed or handed back for correction) | 'ack' (understood, being
    # worked on) | 'done' | 'returned' (needs a manual step from the author).
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="open")
    # The session's restatement of the task in its own words, written BEFORE it
    # changes anything, plus whether the complaint reproduced ('yes' | 'no' |
    # 'partly'). Lets the admin catch a misunderstanding early — and makes
    # "verified" a recorded fact instead of a claim buried in prose.
    understanding: Mapped[str | None] = mapped_column(Text, nullable=True)
    reproduced: Mapped[str | None] = mapped_column(String(8), nullable=True)
    # The diagnosed stage of the writing path (§3 table), from the fixed
    # vocabulary in `api.schemas.WORK_ITEM_STAGES` — a closed vocabulary is what
    # makes "which stage causes the most complaints" a query, not a reading task.
    stage: Mapped[str | None] = mapped_column(String(24), nullable=True)
    # The working session's completion note — filled by the PATCH that closes it.
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    acked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class QuizWord(Base):
    """A word shown in the reading quiz plus its form-similar distractors.

    Content, not measurement — it lives in its own flat table, unrelated to the
    style/hand/template graph. `word` is the clean display/answer form; `fugen`
    is the optional render form carrying a `|` morpheme-boundary marker where a
    compound's Fugen-s must render round (`Donners|tag`). `era` tags modern vs.
    around-1900 vocabulary; `note` glosses dated/rare words in the answer
    reveal. Seeded from `tools/quizgen/quiz_words.json` (0010).
    """

    __tablename__ = "quiz_words"
    __table_args__ = (UniqueConstraint("word", name="uq_quiz_word"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(64), nullable=False)
    distractors: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[]")
    era: Mapped[str] = mapped_column(String(16), nullable=False, server_default="modern")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    fugen: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LesartForm(Base):
    """One word the Lesart page may offer as a reading, bucketed by its
    look-alike key (core.lesarten.lesart_key).

    Content, not measurement: the igerman98 dictionary's forms ∪ the quiz
    bank, loaded whole by `tools.lesarten.sync` through the admin API into a
    new `gen` and switched over at commit (`LesartDictionary.active_gen`), so
    a load in progress never shows a half-filled vocabulary. The dictionary
    bytes stay out of the repo (GPL; data/corpora/igerman98/SOURCE.md) — this
    table is server data, read only through `GET /lesarten?text=`, which
    returns a handful of words per query, never the list.
    """

    __tablename__ = "lesart_forms"

    gen: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    word: Mapped[str] = mapped_column(String(64), primary_key=True)
    # True for the project's own curated words (quiz bank) — ranked first on a tie.
    bank: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")


class LesartDictionary(Base):
    """The one row that says which `lesart_forms` generation is live, and
    where it came from (source label, form count, content hash — the same
    build again is a no-op for the sync)."""

    __tablename__ = "lesart_dictionary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    active_gen: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    forms: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EigenhandSheet(Base):
    """One printed Bogen of the own-hand capture chain — bookkeeping, no pixels.

    The DB holds what the admin view needs to answer "which strips exist, how
    often" and to print the next sheet without repeating one (owner,
    2026-08-23): the rows a Bogen carried and the layout that was printed. The
    scans, crops and Fassung images stay on the author's machine — the reserved
    dataset (docs/proposals/eigenhand-erfassung.md §8) does not move here.

    `layout` is the importer's geometry contract (mm coordinates of Passmarken,
    rows and boxes). Storing it rather than the PDF is deliberate: the bytes are
    reproducible from the layout, the geometry is not reproducible from the
    bytes, and it is what a local ingest run has to register against.
    """

    __tablename__ = "eigenhand_sheets"
    __table_args__ = (UniqueConstraint("hand", "sheet", name="uq_eigenhand_sheet"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hand: Mapped[str] = mapped_column(String(HAND_ID_MAX), nullable=False, index=True)
    style: Mapped[str] = mapped_column(String(STYLE_ID_MAX), nullable=False)
    sheet: Mapped[str] = mapped_column(String(16), nullable=False)
    # The date PRINTED on the sheet, as a string: it is a provenance stamp that
    # has to match the layout byte for byte, not a queryable timestamp.
    printed_on: Mapped[str] = mapped_column(String(10), nullable=False)
    strips: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[]")
    layout: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False)
    layout_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EigenhandFassung(Base):
    """One judged row of a Bogen — the Siebung verdict, without the strip image.

    A Fassung is one recording of one Streifen. `angenommen` rows ARE the
    training data (their pixels live locally); `verworfen` and
    `zurueckgezogen` rows are recorded so the Sieb-Disziplin stays auditable
    by counts. `png_sha256` names the local file without containing it.

    Two unique constraints, both load-bearing: a Fassung id is unique per
    strip, and a printed ROW can only ever carry one verdict — which is the
    same idempotency rule the local `apply` enforces.
    """

    __tablename__ = "eigenhand_fassungen"
    __table_args__ = (
        UniqueConstraint("hand", "strip", "fassung", name="uq_eigenhand_fassung"),
        UniqueConstraint("hand", "sheet", "row_index", name="uq_eigenhand_row"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hand: Mapped[str] = mapped_column(String(HAND_ID_MAX), nullable=False, index=True)
    strip: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    fassung: Mapped[str] = mapped_column(String(8), nullable=False)
    sheet: Mapped[str] = mapped_column(String(16), nullable=False)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    png_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    filed_on: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # The EFFECTIVE session material, denormalised from the hand's standing
    # setup (0025). A Fassung says out of itself what it was written with — no
    # join, and no implicit "NULL means like the hand": the day the nib really
    # changes, the break is visible in the data instead of reconstructed.
    feder: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tinte: Mapped[str | None] = mapped_column(String(128), nullable=True)
    papier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    geraet: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EigenhandHand(Base):
    """One writing hand's STANDING setup — nib, ink, paper, capture device.

    Ink, paper and nib are photometric parameters of a whole campaign, not
    per-import details: a change mid-campaign splits the corpus into cohorts
    that cannot be compared. So they are typed once here, `ingest` reads them
    back as its defaults, and every Fassung records the effective values it was
    actually written with.

    Separate from `hands` (the harvest-side writer row) on purpose: a Bogen can
    be printed and written long before that writer has a single fit in the DB,
    and the capture chain must not wait on the harvest having started.
    """

    __tablename__ = "eigenhand_hands"
    __table_args__ = (UniqueConstraint("hand", name="uq_eigenhand_hand"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hand: Mapped[str] = mapped_column(String(HAND_ID_MAX), nullable=False)
    style: Mapped[str] = mapped_column(String(STYLE_ID_MAX), nullable=False)
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    feder: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tinte: Mapped[str | None] = mapped_column(String(128), nullable=True)
    papier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 128 like its per-Fassung copy: the two words it holds today fit anywhere,
    # but a column narrower than the one it is copied into turns a longer device
    # name into a truncation error instead of a validation one.
    geraet: Mapped[str | None] = mapped_column(String(128), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EigenhandStrip(Base):
    """The written strip itself — the one place own-hand PIXELS live in the DB.

    Everything else about the capture chain is bookkeeping; this is the image.
    It is here so the workbench can show a written Streifen the way it shows a
    chart crop — and it cannot follow the chart's model, because
    `sources.chart_path` points at committed bytes on disk, which the reserved
    own-hand dataset can never be.

    Its own table so the PNG never rides along on a Bestand query (same motive
    as the deferred `templates.raw_path` in the render path). The ARCHIVE stays
    the master: `tools/eigenhand/snapshot.py` files the same bytes as files, so
    every row here is reconstructible from repo + archive alone, and `sha256`
    is what makes that check mechanical.

    `crop_origin_mm` plus `width_px` give the mm→px scale; the word's box comes
    from the sheet's stored layout. A word crop therefore needs no extra
    storage at all — the server cuts it out of the strip.
    """

    __tablename__ = "eigenhand_strips"
    __table_args__ = (UniqueConstraint("hand", "strip", "fassung", name="uq_eigenhand_strip"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hand: Mapped[str] = mapped_column(String(HAND_ID_MAX), nullable=False, index=True)
    strip: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    fassung: Mapped[str] = mapped_column(String(8), nullable=False)
    sheet: Mapped[str] = mapped_column(String(16), nullable=False)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    png: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    width_px: Mapped[int] = mapped_column(Integer, nullable=False)
    height_px: Mapped[int] = mapped_column(Integer, nullable=False)
    dpi: Mapped[float] = mapped_column(Float, nullable=False)
    crop_origin_mm: Mapped[list] = mapped_column(PORTABLE_JSON, nullable=False, server_default="[]")
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


UEBERGANGSRAUM_NAME = "uebergangsraum"


class EigenhandUebergangsraum(Base):
    """The Übergangsraum — the weighted Soll universe of the own-hand capture.

    ONE row holding the whole table (`items`: coverage item → summed corpus
    weight, pool-only items at 0.0), because the table is one indivisible
    build: every consumer normalises against the table's own maximum, so a
    partial state would silently rescale every Soll. Hand-independent — the
    universe is the same for every writer — and keyed by `name` only so a
    second corpus mix could sit beside it one day without a migration.

    The author's decision of 2026-08-25 put it here: the table is a DERIVED
    aggregate of consult-only frequency lists (~1 300 numbers), not the lists
    themselves — the corpus bytes stay gitignored and out of the DB, and this
    row never leaves the admin-gated `/eigenhand/*` surface. Its provenance
    travels with it (`corpora` = the pinned list checksums, `en_weight`, the
    filter constants, `pool_sha256` = the curated pool the union was built
    over), so the row says out of itself which build it is; `sha256` over the
    canonical content is what makes the push idempotent.

    What it buys: the Werkbank shows the Erstbeleg- and Ausbau-Quote the
    terminal report shows, and the server ranks repetition candidates by
    weighted Soll gain instead of by fewest Fassungen — one Soll on both
    surfaces (proposal §7.1).
    """

    __tablename__ = "eigenhand_uebergangsraum"
    __table_args__ = (UniqueConstraint("name", name="uq_eigenhand_uebergangsraum"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False, default=UEBERGANGSRAUM_NAME)
    format: Mapped[int] = mapped_column(Integer, nullable=False)
    en_weight: Mapped[float] = mapped_column(Float, nullable=False)
    min_count: Mapped[int] = mapped_column(Integer, nullable=False)
    min_word_len: Mapped[int] = mapped_column(Integer, nullable=False)
    corpora: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False)
    words_used: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False)
    corpus_items: Mapped[int] = mapped_column(Integer, nullable=False)
    pool_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False)
    items: Mapped[dict] = mapped_column(PORTABLE_JSON, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
