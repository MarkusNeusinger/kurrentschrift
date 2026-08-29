"""Add lesart_forms + lesart_dictionary — the Lesart page's vocabulary

The Lesart page (/lesen/vergleichen) offers the real words a guessed word
could be read as: same length, every differing letter a documented look-alike
(core/lesarten). Owner decision 2026-08-30: readings are existing words only,
so the page needs a vocabulary — the igerman98 dictionary's ~800 000 forms ∪
the quiz bank — and it lives HERE, in the shared database, like everything
else (owner: „wie sqlite? das kann in unsere PostgreSQL wie der Rest").

`lesart_forms` is bucketed by the look-alike key (one key per length and
letter-class pattern), so a query is one indexed lookup; `gen` lets
`tools.lesarten.sync` load a new build into a fresh generation and switch it
live in one step (`lesart_dictionary.active_gen`), dropping the old one —
a load in progress never shows a half vocabulary. The dictionary bytes are
GPL and stay out of the repo (data/corpora/igerman98/SOURCE.md); the table is
server data behind `GET /lesarten?text=`, which answers a handful of words per
query, never the list.

Content, not measurement: both tables are empty after this migration and are
filled by the admin-gated load, exactly like eigenhand_uebergangsraum.

Revision ID: 0028
Revises: 0027
Create Date: 2026-08-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lesart_forms",
        sa.Column("gen", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("word", sa.String(64), nullable=False),
        sa.Column("bank", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.PrimaryKeyConstraint("gen", "key", "word", name="pk_lesart_forms"),
    )
    op.create_table(
        "lesart_dictionary",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("active_gen", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(200), nullable=False),
        sa.Column("forms", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("lesart_dictionary")
    op.drop_table("lesart_forms")
