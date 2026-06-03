"""bboxes.guides — per-glyph guide lines (Hilfslinien)

Adds a JSONB `guides` column to `bboxes` holding the practice-sheet-style
guide lines drawn over a glyph crop: the four-line system
(baseline/waist/ascender/descender) plus a positionable, angled main line
(slant). See GuideConfig in api/schemas.py for the shape.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bboxes",
        sa.Column("guides", JSONB(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("bboxes", "guides")
