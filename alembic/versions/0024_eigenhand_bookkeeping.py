"""Add eigenhand_sheets + eigenhand_fassungen — own-hand bookkeeping, no pixels

Additive: two new tables, nothing seeded and nothing migrated. They carry what
the admin view needs to answer "which Streifen exist, how often" and to print
the next Bogen without repeating one (owner, 2026-08-23): the rows a printed
Bogen carried plus its layout, and one verdict row per judged sheet row.

Deliberately NOT here: scans, crops, Fassung images. Those stay on the author's
machine as the reserved own-hand dataset (docs/proposals/eigenhand-erfassung.md
§8) — `png_sha256` names a local file without containing it. `hand` is a plain
`<schreiber>-<stil>` string rather than a foreign key into `hands`: a Bogen can
be printed and written before that writer has a single fit in the DB, and the
capture chain must not depend on the harvest having started.

The two unique constraints on the Fassungen are load-bearing: a Fassung id is
unique per strip, and a printed ROW can carry only one verdict — the same
idempotency rule the local `apply` enforces.

Revision ID: 0024
Revises: 0023
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "eigenhand_sheets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hand", sa.String(64), nullable=False),
        sa.Column("style", sa.String(32), nullable=False),
        sa.Column("sheet", sa.String(16), nullable=False),
        # The date printed on the sheet: a provenance stamp that has to match
        # the layout byte for byte, not a queryable timestamp.
        sa.Column("printed_on", sa.String(10), nullable=False),
        sa.Column("strips", JSONB(), nullable=False, server_default="[]"),
        sa.Column("layout", JSONB(), nullable=False),
        sa.Column("layout_sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("hand", "sheet", name="uq_eigenhand_sheet"),
    )
    op.create_index("ix_eigenhand_sheets_hand", "eigenhand_sheets", ["hand"])

    op.create_table(
        "eigenhand_fassungen",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hand", sa.String(64), nullable=False),
        sa.Column("strip", sa.String(16), nullable=False),
        sa.Column("fassung", sa.String(8), nullable=False),
        sa.Column("sheet", sa.String(16), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reason", sa.String(32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("png_sha256", sa.String(64), nullable=True),
        sa.Column("filed_on", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("hand", "strip", "fassung", name="uq_eigenhand_fassung"),
        sa.UniqueConstraint("hand", "sheet", "row_index", name="uq_eigenhand_row"),
    )
    op.create_index("ix_eigenhand_fassungen_hand", "eigenhand_fassungen", ["hand"])
    op.create_index("ix_eigenhand_fassungen_strip", "eigenhand_fassungen", ["strip"])


def downgrade() -> None:
    op.drop_index("ix_eigenhand_fassungen_strip", table_name="eigenhand_fassungen")
    op.drop_index("ix_eigenhand_fassungen_hand", table_name="eigenhand_fassungen")
    op.drop_table("eigenhand_fassungen")
    op.drop_index("ix_eigenhand_sheets_hand", table_name="eigenhand_sheets")
    op.drop_table("eigenhand_sheets")
