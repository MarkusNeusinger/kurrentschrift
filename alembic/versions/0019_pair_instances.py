"""Create pair_instances — observed letter-join occurrences (handmodell H2)

Additive: the per-occurrence layer under the sparse `glyph_pairs` overrides.
Every clean dissection of a joined adjacent pair on a specimen plate is one
row — the natural transition itself (connector + placement offset in the
GlyphPair.geometry frame, plus dissection QC in `measurements`). Nothing is
seeded — the pairlab occurrence harvest fills it through the admin API.

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pair_instances",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "source_id", sa.String(64), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("hand_id", sa.String(64), sa.ForeignKey("hands.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("left_key", sa.String(32), nullable=False, index=True),
        sa.Column("right_key", sa.String(32), nullable=False, index=True),
        sa.Column("kind", sa.String(16), nullable=False, server_default="word"),
        sa.Column("specimen_id", sa.String(64), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("geometry", JSONB(), nullable=False),
        sa.Column("measurements", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source_id", "kind", "specimen_id", "slot", name="uq_pair_instance_occurrence"),
    )


def downgrade() -> None:
    op.drop_table("pair_instances")
