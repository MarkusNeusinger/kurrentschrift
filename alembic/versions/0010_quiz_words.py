"""Add quiz_words table and seed it from the generator

Creates the flat `quiz_words` table (word + JSONB distractors + era/note/fugen)
and seeds it from `tools/quizgen/quiz_words.json`, the output of the word-bank
generator (`tools/quizgen/build.py`). Content, not measurement — the table is
unrelated to the style/hand/template graph.

NOTE: seeding reads the committed JSON at apply time, so re-running the
generator changes what a FRESH database is seeded with; already-migrated
databases keep their rows (edit them with a follow-up migration).

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-02
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# alembic/versions/0010_quiz_words.py → repo root is two parents up from versions/.
_SEED = Path(__file__).resolve().parents[2] / "tools" / "quizgen" / "quiz_words.json"


def upgrade() -> None:
    quiz_words = op.create_table(
        "quiz_words",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("word", sa.String(64), nullable=False),
        sa.Column("distractors", JSONB(), nullable=False, server_default="[]"),
        sa.Column("era", sa.String(16), nullable=False, server_default="modern"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("fugen", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("word", name="uq_quiz_word"),
    )

    rows = json.loads(_SEED.read_text(encoding="utf-8"))
    op.bulk_insert(
        quiz_words,
        [
            {
                "word": r["word"],
                "distractors": r["distractors"],
                "era": r.get("era", "modern"),
                "note": r.get("note"),
                "fugen": r.get("fugen"),
            }
            for r in rows
        ],
    )


def downgrade() -> None:
    op.drop_table("quiz_words")
