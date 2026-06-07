"""bboxes.locked — per-glyph "done" marker

Adds a boolean `locked` column to `bboxes`. A locked glyph reads as complete
in the admin chart (distinct colour + lock badge) and is protected from
accidental move/resize/redraw. It is distinct from owning a canonical: a
stroke can exist while the glyph is still being worked on; `locked` is the
human's explicit "this one is final".

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bboxes", sa.Column("locked", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("bboxes", "locked")
