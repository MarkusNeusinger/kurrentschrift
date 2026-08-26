"""Add eigenhand_uebergangsraum — the weighted Soll universe, one row

The author's decision of 2026-08-25: the DERIVED Übergangsraum weight table
(coverage item → summed corpus weight, ~1 300 rows once the curated pool's
own items are unioned in at weight 0) may live in the shared private DB. The
consult-only frequency lists it is computed from stay gitignored and out of
the DB — only the aggregate moves, with its provenance (list checksums,
`en_weight`, the filter constants, the pool it was unioned over).

What this buys, and why it is one row: the Werkbank can show the Erstbeleg-
and Ausbau-Quote the terminal report shows, and the server ranks repetition
candidates by weighted Soll gain exactly like `tools.eigenhand.sheet` does —
one Soll on both surfaces. The table is one indivisible build (every target
is scaled against its own maximum), so it is stored whole, replaced whole,
and made idempotent by a content hash; a second corpus mix could sit beside
it under another `name` without touching the schema.

Revision ID: 0026
Revises: 0025
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "eigenhand_uebergangsraum",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(32), nullable=False),
        sa.Column("format", sa.Integer(), nullable=False),
        sa.Column("en_weight", sa.Float(), nullable=False),
        sa.Column("min_count", sa.Integer(), nullable=False),
        sa.Column("min_word_len", sa.Integer(), nullable=False),
        sa.Column("corpora", JSONB(), nullable=False),
        sa.Column("words_used", JSONB(), nullable=False),
        sa.Column("corpus_items", sa.Integer(), nullable=False),
        sa.Column("pool_sha256", sa.String(64), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("items", JSONB(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_eigenhand_uebergangsraum"),
    )


def downgrade() -> None:
    op.drop_table("eigenhand_uebergangsraum")
