"""bboxes.split — per-letter "positions authored separately" marker

Adds a boolean `split` column to `bboxes`. By default a letter's three
positional forms (initial/medial/final = Anfang/Mitte/Ende) share one authored
form: the wizard fans the same trace out across all three, and the sidebar,
quiz and lock treat them as a single unit. Setting `split` marks a letter whose
positions genuinely differ, so each position is authored, locked and quizzed
independently. It is a letter-level intent stored on all three sibling rows and
read with `.some(...)`; writes fan out across siblings exactly like `locked`.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-09
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("bboxes", sa.Column("split", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("bboxes", "split")
