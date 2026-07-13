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

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database.connection import Base


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
    default_style_ratio: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[2, 1, 2]")
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
    chart_size: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Per-source overrides of the style defaults; null => use the style's values.
    style_ratio: Mapped[list | None] = mapped_column(JSONB, nullable=True)
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
    mask_strokes: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    # Manual ink brush (German: Tinten-Pinsel): the eraser's positive twin — same
    # {points, radius} stroke shape, but painted as ink (black) before binarisation
    # instead of blanked, to close paper-coloured specks/gaps inside a stroke the
    # auto-fill can't reach (e.g. a gap open to the background).
    ink_strokes: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
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
    patches: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    baseline_y: Mapped[int] = mapped_column(Integer, nullable=False)
    midband_y: Mapped[int] = mapped_column(Integer, nullable=False)
    n_anchors: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    # Guide lines drawn over the crop (German: Hilfslinien): the four-line system
    # (Grundlinie/Mittellinie/Oberlinie/Unterlinie) plus a positionable, angled
    # main line (slant). Open JSONB; see GuideConfig in api/schemas.py.
    guides: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    # Manual "done" marker (German: gesperrt): a finished glyph is locked so it
    # reads as complete and is protected from accidental move/resize/redraw. The
    # wizard's final "approve" step sets this; unlocking re-enables editing.
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # Per-letter "positions authored separately" marker (German: aufgetrennt).
    # Default false: the three positional forms share one authored form (the
    # wizard fans the same trace across initial/medial/final) and the sidebar,
    # quiz and lock treat the letter as one unit. true marks a letter whose
    # positions genuinely differ, so each is authored/locked/quizzed on its own.
    # A letter-level intent stored on all three sibling rows, read with `.some`;
    # writes fan out across siblings exactly like `locked`.
    split: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

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


class Template(Base):
    """Canonical ductus template (Grundvorlage) for a (style, glyph, position, variant).

    `anchors` + `half_widths` are in normalised template coordinates (baseline=0,
    midband=1). `raw_path` is the dense stylus capture in chart-pixel coords, kept
    so /resample can re-derive anchors with a different n_anchors without the user
    redrawing. `provenance_source_id` is the teaching chart this canonical was
    traced from. `measurements` holds the authored trace's own derived stats
    (slant_deg, mean_half_width_px, …); per-text-occurrence statistics live on
    `Instance`, not here (§12 layer 1).
    """

    __tablename__ = "templates"
    __table_args__ = (UniqueConstraint("style_id", "glyph", "position", "variant", name="uq_template_style_gpv"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    style_id: Mapped[str] = mapped_column(
        String(STYLE_ID_MAX), ForeignKey("styles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provenance_source_id: Mapped[str | None] = mapped_column(
        String(SOURCE_ID_MAX), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    glyph_key: Mapped[str] = mapped_column(String(GLYPH_KEY_MAX), nullable=False, index=True)
    glyph: Mapped[str] = mapped_column(String(GLYPH_CHAR_MAX), nullable=False)
    position: Mapped[str] = mapped_column(String(POSITION_MAX), nullable=False)
    variant: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    advance: Mapped[float] = mapped_column(Float, nullable=False)
    entry: Mapped[dict] = mapped_column(JSONB, nullable=False)
    exit_pt: Mapped[dict] = mapped_column("exit_pt", JSONB, nullable=False)

    anchors: Mapped[list] = mapped_column(JSONB, nullable=False)
    half_widths: Mapped[list] = mapped_column(JSONB, nullable=False)

    raw_path: Mapped[list] = mapped_column(JSONB, nullable=False)
    trace_meta: Mapped[dict] = mapped_column(JSONB, nullable=False)
    measurements: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    style: Mapped[Style] = relationship(back_populates="templates")


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

    anchors: Mapped[list] = mapped_column(JSONB, nullable=False)
    half_widths: Mapped[list] = mapped_column(JSONB, nullable=False)
    raw_path: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    measurements: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Aggregate(Base):
    """Per-hand aggregate (§12 layer 2) per (hand, glyph, position, variant).

    Cluster centre of the control points, deviation hull (MAD/covariance), and
    mean of the layer-1 stats. Defined now; populated by the aggregation job
    later. Statistics are computed per hand, never averaged across hands
    (quellen-und-rechte.md §7).
    """

    __tablename__ = "aggregates"
    __table_args__ = (UniqueConstraint("hand_id", "glyph", "position", "variant", name="uq_aggregate_hand_gpv"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hand_id: Mapped[str] = mapped_column(
        String(HAND_ID_MAX), ForeignKey("hands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    glyph: Mapped[str] = mapped_column(String(GLYPH_CHAR_MAX), nullable=False)
    position: Mapped[str] = mapped_column(String(POSITION_MAX), nullable=False)
    variant: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    cluster_center: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    hull: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    mean_stats: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    n_instances: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

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
    distractors: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    era: Mapped[str] = mapped_column(String(16), nullable=False, server_default="modern")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    fugen: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
