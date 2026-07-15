"""Align quiz_words.created_at with the model: NOT NULL

Migration 0010 created `quiz_words.created_at` without `nullable=False` —
the only `created_at` in the schema missing it (0004 declares it on every
other table), while the model (`QuizWord.created_at: Mapped[datetime]`)
implies NOT NULL. Surfaced by the new `alembic check` step in CI
(autogenerate drift against the migrated DB). Safe to tighten: the column
carries `server_default=now()`, so every existing row has a value.

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("quiz_words", "created_at", existing_type=sa.DateTime(timezone=True), nullable=False)


def downgrade() -> None:
    op.alter_column("quiz_words", "created_at", existing_type=sa.DateTime(timezone=True), nullable=True)
