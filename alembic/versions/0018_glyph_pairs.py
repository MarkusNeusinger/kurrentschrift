"""Create glyph_pairs — sparse letter-pair overrides (redesign R3, proposal B)

Additive: the §4 generator stays the default for every join; a row here is an
opt-in override for one adjacent pair within a style, rendered only when
`approved`. `geometry` carries the connector centerline + placement offset
(template units); `provenance` records harvested (M4-fitted from a same-hand
specimen, pointed at by provenance_source_id + specimen_id) vs authored
(freehand in the pair editor). Nothing is seeded — the harvest importer and
the editor fill it later.

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "glyph_pairs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "style_id", sa.String(32), sa.ForeignKey("styles.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("left_key", sa.String(32), nullable=False),
        sa.Column("right_key", sa.String(32), nullable=False),
        sa.Column("variant", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("geometry", JSONB(), nullable=False),
        sa.Column("provenance", sa.String(16), nullable=False),
        sa.Column(
            "provenance_source_id", sa.String(64), sa.ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("specimen_id", sa.String(64), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("style_id", "left_key", "right_key", "variant", name="uq_glyph_pair_style_lr_variant"),
    )


def downgrade() -> None:
    op.drop_table("glyph_pairs")
