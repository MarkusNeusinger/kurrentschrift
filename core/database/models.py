"""SQLAlchemy models — Source, Bbox, Glyph.

Schema (see `docs/concepts/architektur.md` §3 for the library unit):
- `Source` is a PD geometry reference (e.g. Loth 1866) or, later, a user-hand
  upload variant. Style parameters live here (`style_ratio`, `slant_deg`) so
  the render code reads them from data, not from constants.
- `Bbox` is the per-source crop config for one glyph (rectangle, excludes,
  baseline/midband calibration). One row per (source, glyph_key).
- `Glyph` is the canonical ductus template for a (source, glyph, position,
  variant) combination — anchors, half-widths, raw stylus path, plus a
  `measurements` blob for per-instance derived statistics that future
  aggregation queries can plot as histograms.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database.connection import Base


GLYPH_KEY_MAX = 32
GLYPH_CHAR_MAX = 8
POSITION_MAX = 16
SOURCE_ID_MAX = 64


class Source(Base):
    """A geometry reference (PD original or own-hand upload).

    `chart_path` is relative to the repo root and points to the bytes on disk
    (e.g. `data/sources/loth-1866/chart.jpg`). We deliberately don't store the
    image bytes themselves in the DB; PD sources live in /data/ under git,
    user-hand uploads will land in GCS later.

    `style_ratio` is [ascender, x_height, descender]; Loth Kurrent = [2, 1, 2].
    `slant_deg` is the dominant writing slant (0 = upright; ~65° = typical
    Kurrent). Both are used by the diagnostic renderer to draw guide lines and
    apply a shear transform to the canonical preview.
    """

    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(SOURCE_ID_MAX), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    license: Mapped[str] = mapped_column(String(64), nullable=False)
    chart_path: Mapped[str] = mapped_column(String(512), nullable=False)
    chart_size: Mapped[dict] = mapped_column(JSONB, nullable=False)
    style_ratio: Mapped[list] = mapped_column(JSONB, nullable=False)
    slant_deg: Mapped[float] = mapped_column(Float, nullable=False)
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bboxes: Mapped[list["Bbox"]] = relationship("Bbox", back_populates="source", cascade="all, delete-orphan")
    glyphs: Mapped[list["Glyph"]] = relationship("Glyph", back_populates="source", cascade="all, delete-orphan")


class Bbox(Base):
    """Crop rectangle + excludes + baseline/midband calibration for one glyph."""

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
    excludes: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    baseline_y: Mapped[int] = mapped_column(Integer, nullable=False)
    midband_y: Mapped[int] = mapped_column(Integer, nullable=False)
    n_anchors: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    # Guide lines drawn over the crop (German: Hilfslinien), shaped like the
    # practice-sheet rulers in app/src/lib/lineatur.ts: the four-line system
    # (baseline/waist/ascender/descender) plus a positionable, angled main
    # line (slant). Open JSONB so the per-glyph set can grow; see GuideConfig
    # in api/schemas.py for the keys. Reused later for drawing letters and for
    # explanatory diagrams.
    guides: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    # Manual "done" marker: a finished glyph is locked so it reads as complete
    # and is protected from accidental move/resize/redraw in the admin chart.
    # Distinct from having a canonical (a stroke can exist while still being
    # worked on); this is the human's "this one is final".
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    source: Mapped[Source] = relationship("Source", back_populates="bboxes")


class Glyph(Base):
    """Canonical ductus template for a (glyph, position, variant) in one source.

    `anchors` + `half_widths` are in normalised template coordinates
    (baseline=0, midband=1). `raw_path` is the dense stylus capture in
    chart-pixel coords, kept so /resample can re-derive anchors with a
    different n_anchors without the user redrawing.

    `measurements` is open-schema JSONB: initial keys are `slant_deg`,
    `mean_half_width_px`, `path_length_px`, `aspect_ratio`. Designed for
    aggregation queries like `SELECT (measurements->>'slant_deg')::float ...`.
    """

    __tablename__ = "glyphs"
    __table_args__ = (UniqueConstraint("source_id", "glyph", "position", "variant", name="uq_glyph_source_gpv"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        String(SOURCE_ID_MAX), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
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

    source: Mapped[Source] = relationship("Source", back_populates="glyphs")
