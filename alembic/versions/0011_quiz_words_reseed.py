"""Re-seed quiz_words from the expanded generator bank

Migration 0010 seeded the table once at apply time; already-migrated databases
keep their rows. This follow-up replaces ALL rows with the current committed
``tools/quizgen/quiz_words.json`` — the expanded ~500-word bank in which
``distractors`` holds the pinned anchor misread(s) only (usually exactly one);
the remaining quiz options are drawn at runtime by the similarity rules.

Content, not measurement — safe to replace wholesale; the table has no
foreign keys and the SPA falls back to its bundled bank while empty.

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-02
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# alembic/versions/0011_quiz_words_reseed.py → repo root is two parents up from versions/.
_SEED = Path(__file__).resolve().parents[2] / "tools" / "quizgen" / "quiz_words.json"

# Lightweight table stub for DML — matches the shape created in 0010.
_QUIZ_WORDS = sa.table(
    "quiz_words",
    sa.column("word", sa.String),
    sa.column("distractors", JSONB),
    sa.column("era", sa.String),
    sa.column("note", sa.Text),
    sa.column("fugen", sa.String),
)


def upgrade() -> None:
    op.execute(_QUIZ_WORDS.delete())
    rows = json.loads(_SEED.read_text(encoding="utf-8"))
    op.bulk_insert(
        _QUIZ_WORDS,
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
    # The pre-0011 rows are not recoverable from this revision; keep the
    # current bank (a superset) rather than leaving the table empty.
    pass
