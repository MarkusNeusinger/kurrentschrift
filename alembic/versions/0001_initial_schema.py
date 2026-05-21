"""initial schema: sources, bboxes, glyphs + Loth 1866 seed

Revision ID: 0001
Revises:
Create Date: 2026-05-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("license", sa.String(64), nullable=False),
        sa.Column("chart_path", sa.String(512), nullable=False),
        sa.Column("chart_size", JSONB(), nullable=False),
        sa.Column("style_ratio", JSONB(), nullable=False),
        sa.Column("slant_deg", sa.Float(), nullable=False),
        sa.Column("attribution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "bboxes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.String(64), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("glyph_key", sa.String(32), nullable=False),
        sa.Column("y0", sa.Integer(), nullable=False),
        sa.Column("y1", sa.Integer(), nullable=False),
        sa.Column("x0", sa.Integer(), nullable=False),
        sa.Column("x1", sa.Integer(), nullable=False),
        sa.Column("excludes", JSONB(), nullable=False, server_default="[]"),
        sa.Column("baseline_y", sa.Integer(), nullable=False),
        sa.Column("midband_y", sa.Integer(), nullable=False),
        sa.Column("n_anchors", sa.Integer(), nullable=False, server_default="50"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("source_id", "glyph_key", name="uq_bbox_source_glyph"),
    )
    op.create_index("ix_bboxes_source_id", "bboxes", ["source_id"])

    op.create_table(
        "glyphs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.String(64), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("glyph_key", sa.String(32), nullable=False),
        sa.Column("glyph", sa.String(8), nullable=False),
        sa.Column("position", sa.String(16), nullable=False),
        sa.Column("variant", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("advance", sa.Float(), nullable=False),
        sa.Column("entry", JSONB(), nullable=False),
        sa.Column("exit_pt", JSONB(), nullable=False),
        sa.Column("anchors", JSONB(), nullable=False),
        sa.Column("half_widths", JSONB(), nullable=False),
        sa.Column("raw_path", JSONB(), nullable=False),
        sa.Column("trace_meta", JSONB(), nullable=False),
        sa.Column("measurements", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("source_id", "glyph", "position", "variant", name="uq_glyph_source_gpv"),
    )
    op.create_index("ix_glyphs_source_id", "glyphs", ["source_id"])
    op.create_index("ix_glyphs_glyph_key", "glyphs", ["glyph_key"])

    # Seed Loth 1866 — Public Domain Mark 1.0 via Wikimedia Commons.
    # Slant 65° is a starting estimate; verify against the chart and update via PUT /sources later.
    op.execute(
        """
        INSERT INTO sources (id, title, license, chart_path, chart_size, style_ratio, slant_deg, attribution)
        VALUES (
          'loth-1866',
          'Loth Kurrent Vorlagen 1866',
          'PD',
          'data/sources/loth-1866/chart.jpg',
          '{"w": 1633, "h": 1869}'::jsonb,
          '[2, 1, 2]'::jsonb,
          65.0,
          'Via Wikimedia Commons, Public Domain Mark 1.0'
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_glyphs_glyph_key", table_name="glyphs")
    op.drop_index("ix_glyphs_source_id", table_name="glyphs")
    op.drop_table("glyphs")
    op.drop_index("ix_bboxes_source_id", table_name="bboxes")
    op.drop_table("bboxes")
    op.drop_table("sources")
