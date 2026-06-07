"""library schema: styles/hands/sources/bboxes/templates/instances/aggregates

Rebuilds the data model from the flat (sources, bboxes, glyphs) MVP schema into
the full library model (architektur.md §3/§5/§12):
- a `styles` (Grundvorlage) dimension: Kurrent / Sütterlin / Offenbacher,
- the canonical↔instance split (`templates` per style ↔ `instances` per text),
- explicit `hands` + per-hand `aggregates` for the statistics layers.

This is a forward migration (down_revision 0003), NOT a history rewrite: prod
runs `alembic upgrade head` on deploy. It DROPS the old sources/bboxes/glyphs
(authorised: the data was throwaway admin scratch) and seeds the three styles +
the Loth 1866 chart source.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- drop the old flat schema (children first) ------------------------
    op.drop_table("glyphs")
    op.drop_table("bboxes")
    op.drop_table("sources")

    # --- styles (Grundvorlagen) ------------------------------------------
    op.create_table(
        "styles",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("width_resolver", sa.String(16), nullable=False, server_default="pressure"),
        sa.Column("default_slant_deg", sa.Float(), nullable=False, server_default="65"),
        sa.Column("default_style_ratio", JSONB(), nullable=False, server_default="[2, 1, 2]"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- hands (writers) -------------------------------------------------
    op.create_table(
        "hands",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("style_id", sa.String(32), sa.ForeignKey("styles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("era", sa.String(64), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_hands_style_id", "hands", ["style_id"])

    # --- sources (charts + manuscripts) ----------------------------------
    op.create_table(
        "sources",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("style_id", sa.String(32), sa.ForeignKey("styles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hand_id", sa.String(64), sa.ForeignKey("hands.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.String(16), nullable=False, server_default="chart"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("license", sa.String(64), nullable=False),
        sa.Column("chart_path", sa.String(512), nullable=False),
        sa.Column("chart_size", JSONB(), nullable=False),
        sa.Column("style_ratio", JSONB(), nullable=True),
        sa.Column("slant_deg", sa.Float(), nullable=True),
        sa.Column("attribution", sa.Text(), nullable=True),
        sa.Column("origin_url", sa.Text(), nullable=True),
        sa.Column("retrieved_date", sa.Date(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sources_style_id", "sources", ["style_id"])
    op.create_index("ix_sources_hand_id", "sources", ["hand_id"])

    # --- bboxes (chart crop config + freeform eraser) --------------------
    op.create_table(
        "bboxes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.String(64), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("glyph_key", sa.String(32), nullable=False),
        sa.Column("y0", sa.Integer(), nullable=False),
        sa.Column("y1", sa.Integer(), nullable=False),
        sa.Column("x0", sa.Integer(), nullable=False),
        sa.Column("x1", sa.Integer(), nullable=False),
        sa.Column("mask_strokes", JSONB(), nullable=False, server_default="[]"),
        sa.Column("baseline_y", sa.Integer(), nullable=False),
        sa.Column("midband_y", sa.Integer(), nullable=False),
        sa.Column("n_anchors", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("guides", JSONB(), nullable=False, server_default="{}"),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default="false"),
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

    # --- templates (canonical Grundvorlage, per style) -------------------
    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("style_id", sa.String(32), sa.ForeignKey("styles.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "provenance_source_id", sa.String(64), sa.ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
        ),
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
        sa.UniqueConstraint("style_id", "glyph", "position", "variant", name="uq_template_style_gpv"),
    )
    op.create_index("ix_templates_style_id", "templates", ["style_id"])
    op.create_index("ix_templates_glyph_key", "templates", ["glyph_key"])

    # --- instances (per-text occurrences, §12 layer 1) -------------------
    op.create_table(
        "instances",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.String(64), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hand_id", sa.String(64), sa.ForeignKey("hands.id", ondelete="SET NULL"), nullable=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("glyph_key", sa.String(32), nullable=False),
        sa.Column("glyph", sa.String(8), nullable=False),
        sa.Column("position", sa.String(16), nullable=False),
        sa.Column("variant", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("y0", sa.Integer(), nullable=False),
        sa.Column("y1", sa.Integer(), nullable=False),
        sa.Column("x0", sa.Integer(), nullable=False),
        sa.Column("x1", sa.Integer(), nullable=False),
        sa.Column("anchors", JSONB(), nullable=False),
        sa.Column("half_widths", JSONB(), nullable=False),
        sa.Column("raw_path", JSONB(), nullable=False, server_default="[]"),
        sa.Column("measurements", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("source_id", "glyph", "position", "variant", "y0", "x0", name="uq_instance_loc"),
    )
    op.create_index("ix_instances_source_id", "instances", ["source_id"])
    op.create_index("ix_instances_hand_id", "instances", ["hand_id"])
    op.create_index("ix_instances_glyph_key", "instances", ["glyph_key"])

    # --- aggregates (per-hand stats, §12 layer 2) ------------------------
    op.create_table(
        "aggregates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hand_id", sa.String(64), sa.ForeignKey("hands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("glyph", sa.String(8), nullable=False),
        sa.Column("position", sa.String(16), nullable=False),
        sa.Column("variant", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cluster_center", JSONB(), nullable=False, server_default="[]"),
        sa.Column("hull", JSONB(), nullable=False, server_default="{}"),
        sa.Column("mean_stats", JSONB(), nullable=False, server_default="{}"),
        sa.Column("n_instances", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("hand_id", "glyph", "position", "variant", name="uq_aggregate_hand_gpv"),
    )
    op.create_index("ix_aggregates_hand_id", "aggregates", ["hand_id"])

    # --- seed the three Grundvorlagen ------------------------------------
    op.execute(
        """
        INSERT INTO styles (id, name, width_resolver, default_slant_deg, default_style_ratio, description)
        VALUES
          ('kurrent', 'Kurrent', 'pressure', 65.0, '[2, 1, 2]'::jsonb,
           'Projekt-Normform / MVP-Baseline; Spitzfeder, voller Schwellzug (Loth 1866).'),
          ('suetterlin', 'Sütterlin', 'constant', 90.0, '[2, 1, 2]'::jsonb,
           '1911, aufrecht, gleichmäßige Strichstärke (Redisfeder, kein Schwellzug).'),
          ('offenbacher', 'Offenbacher Schrift', 'broad_nib', 90.0, '[2, 1, 2]'::jsonb,
           '1927, Rudolf Koch, Breitfeder; Strichbreite winkelabhängig.')
        """
    )

    # Seed Loth 1866 — Public Domain Mark 1.0 via Wikimedia Commons.
    # Slant 65° is a starting estimate; verify against the chart and update later.
    op.execute(
        """
        INSERT INTO sources
          (id, style_id, hand_id, kind, title, license, chart_path, chart_size, style_ratio, slant_deg, attribution)
        VALUES (
          'loth-1866', 'kurrent', NULL, 'chart',
          'Loth Kurrent Vorlagen 1866', 'PD',
          'data/sources/loth-1866/chart.jpg',
          '{"w": 1633, "h": 1869}'::jsonb,
          '[2, 1, 2]'::jsonb, 65.0,
          'Via Wikimedia Commons, Public Domain Mark 1.0'
        )
        """
    )


def downgrade() -> None:
    # drop the library schema (children first)
    op.drop_table("aggregates")
    op.drop_table("instances")
    op.drop_table("templates")
    op.drop_table("bboxes")
    op.drop_table("sources")
    op.drop_table("hands")
    op.drop_table("styles")

    # recreate the flat 0003-state schema (sources, bboxes, glyphs) + Loth seed
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
        sa.Column("guides", JSONB(), nullable=False, server_default="{}"),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default="false"),
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
    op.execute(
        """
        INSERT INTO sources (id, title, license, chart_path, chart_size, style_ratio, slant_deg, attribution)
        VALUES (
          'loth-1866', 'Loth Kurrent Vorlagen 1866', 'PD',
          'data/sources/loth-1866/chart.jpg',
          '{"w": 1633, "h": 1869}'::jsonb, '[2, 1, 2]'::jsonb, 65.0,
          'Via Wikimedia Commons, Public Domain Mark 1.0'
        )
        """
    )
