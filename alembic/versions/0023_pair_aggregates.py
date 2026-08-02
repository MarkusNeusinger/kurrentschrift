"""Add pair_aggregates — the per-hand pair statistics layer (Stufenplan H2)

Additive: a new table, nothing seeded and nothing migrated. It is the pair twin
of `aggregates` (re-keyed in `0021`) — one row per `(hand_id, left_key,
right_key)` holding the median placement offset, the per-point median of the
arc-length-resampled connector centerlines, their MAD hulls and the pooled
dissection QC of the hand's `pair_instances` (`0019`).

Same situation as `0021`: the table has never held a row, and the admin-gated
rebuild endpoint (`POST /hands/{hand_id}/pair-aggregates/rebuild`) is its first
writer. Nothing here affects rendering — `glyph_pairs` stays the sparse verbatim
override and the join generator stays the default.

Revision ID: 0023
Revises: 0022
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pair_aggregates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hand_id", sa.String(64), sa.ForeignKey("hands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("left_key", sa.String(32), nullable=False),
        sa.Column("right_key", sa.String(32), nullable=False),
        sa.Column("offset_center", JSONB(), nullable=False, server_default="[]"),
        sa.Column("connector_center", JSONB(), nullable=False, server_default="[]"),
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
        sa.UniqueConstraint("hand_id", "left_key", "right_key", name="uq_pair_aggregate_hand_lr"),
    )
    op.create_index("ix_pair_aggregates_hand_id", "pair_aggregates", ["hand_id"])
    op.create_index("ix_pair_aggregates_left_key", "pair_aggregates", ["left_key"])
    op.create_index("ix_pair_aggregates_right_key", "pair_aggregates", ["right_key"])


def downgrade() -> None:
    op.drop_index("ix_pair_aggregates_right_key", table_name="pair_aggregates")
    op.drop_index("ix_pair_aggregates_left_key", table_name="pair_aggregates")
    op.drop_index("ix_pair_aggregates_hand_id", table_name="pair_aggregates")
    op.drop_table("pair_aggregates")
