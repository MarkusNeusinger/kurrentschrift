"""Create work_items — the Auftragskorb of the Werkbank (stage W1)

Additive: the admin's filed optimization tasks. One row per marked element —
`kind` names the level (letter | pair | word), the key columns name the
element, `specimen_kind`/`specimen_id` where the issue was seen, `note` the
observation. A working session lists the open rows, works them off and closes
each with status 'done' + `resolution`. Internal work notes, admin-gated,
never part of rendering — nothing is seeded.

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-31
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "work_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "source_id", sa.String(64), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("glyph_key", sa.String(32), nullable=True),
        sa.Column("left_key", sa.String(32), nullable=True),
        sa.Column("right_key", sa.String(32), nullable=True),
        sa.Column("word", sa.String(64), nullable=True),
        sa.Column("specimen_kind", sa.String(16), nullable=True),
        sa.Column("specimen_id", sa.String(64), nullable=True),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("work_items")
