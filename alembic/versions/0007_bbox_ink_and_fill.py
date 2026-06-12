"""Add the ink brush + per-glyph speck-fill knobs to bboxes

Two additive, backward-compatible columns on `bboxes`:

- `ink_strokes` (JSONB, default []) — the manual ink brush (Tinten-Pinsel), the
  eraser's positive twin: same {points, radius} stroke shape, painted as ink
  before binarisation to close specks/gaps the auto-fill can't reach.
- `fill_holes_max_area` (Integer, default 0 = off) — per-glyph speck auto-fill
  threshold (px²) of an enclosed background hole to swallow before
  skeletonisation; 0 keeps every existing glyph bit-identical.

Both default to the "do nothing" value, so no glyph changes until a wizard write
opts in. NOTE downgrade drops the columns (any authored ink strokes are lost).

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bboxes", sa.Column("ink_strokes", JSONB(), nullable=False, server_default="[]"))
    op.add_column("bboxes", sa.Column("fill_holes_max_area", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("bboxes", "fill_holes_max_area")
    op.drop_column("bboxes", "ink_strokes")
