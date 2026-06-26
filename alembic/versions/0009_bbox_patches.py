"""Add crop patches to bboxes

One additive, backward-compatible column on `bboxes`:

- `patches` (JSONB, default []) — donor regions copied from elsewhere on the
  *same* chart and composited into the crop before binarisation, each
  `{src: [x0, y0, x1, y1], dst: [x, y]}` (source rect + destination top-left,
  chart-pixel coords). For glyphs with no own teaching-chart cell, e.g. the
  Sütterlin ü/ö borrowing the two umlaut strokes from the ä cell. Composited by
  darken (np.minimum), so only the donor's ink transfers, never its background.

Defaults to the empty list, so no glyph changes until a wizard write opts in.
NOTE downgrade drops the column (any authored patches are lost).

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bboxes", sa.Column("patches", JSONB(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("bboxes", "patches")
