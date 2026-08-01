"""Re-key aggregates to (hand, glyph_key, variant) — Stufenplan H1

The per-hand statistics layer (§12 layer 2) has existed since `0004` but was
never populated: the H1 aggregation step (docs/proposals/handmodell-stufenplan.md
§4) is the first writer. Because the table has never held a row, a plain
drop+recreate is safe — no data migration is needed.

The rebuilt shape follows the R2 position removal (`0017`): the identity is
`(hand_id, glyph_key, variant)`, the display column `glyph` stays, and
`position` — an occurrence-level observation dimension, not an aggregate one —
goes away. `cluster_center` holds the per-anchor median (the Laufform), `hull`
the per-anchor spread (MAD).

Revision ID: 0021
Revises: 0020
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_aggregates_hand_id", table_name="aggregates")
    op.drop_table("aggregates")

    op.create_table(
        "aggregates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hand_id", sa.String(64), sa.ForeignKey("hands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("glyph_key", sa.String(32), nullable=False),
        sa.Column("glyph", sa.String(8), nullable=False),
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
        sa.UniqueConstraint("hand_id", "glyph_key", "variant", name="uq_aggregate_hand_kv"),
    )
    op.create_index("ix_aggregates_hand_id", "aggregates", ["hand_id"])
    op.create_index("ix_aggregates_glyph_key", "aggregates", ["glyph_key"])


def downgrade() -> None:
    op.drop_index("ix_aggregates_glyph_key", table_name="aggregates")
    op.drop_index("ix_aggregates_hand_id", table_name="aggregates")
    op.drop_table("aggregates")

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
