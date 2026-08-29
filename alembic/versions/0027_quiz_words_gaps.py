"""Add the gap-fill words to quiz_words (letters the frequency-led bank never reached)

The reading-quiz word bank of 0011 had no word at all with C, Q, X, Y, q, x,
y, Ä, Ö, Ü and only 1–6 words with I, J, U, R, O, N, E, j, v, ß, ö — every
traced glyph was quizzable in letters mode, but a learner never read those
letters inside a word. ``tools/quizgen/corpus.py`` now carries the gap-fill
entries (reconciled with the Eigenhand Wortvorrat's rare-join words, plus the
names and old spellings of genealogical documents; quiz-wortbank.md §1
„Lückenschluss"); this migration inserts exactly those rows from the
committed ``quiz_words.json`` into an already-seeded database.

Insert-only, keyed by ``_ADDED``: rows that already exist are left alone, so
the migration is idempotent, and the downgrade removes exactly these words —
the pre-existing rows are never touched (unlike the wholesale reseed of 0011,
whose downgrade could only raise).

Revision ID: 0027
Revises: 0026
Create Date: 2026-08-29
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# alembic/versions/0027_quiz_words_gaps.py → repo root is two parents up from versions/.
_SEED = Path(__file__).resolve().parents[2] / "tools" / "quizgen" / "quiz_words.json"

_QUIZ_WORDS = sa.table(
    "quiz_words",
    sa.column("word", sa.String),
    sa.column("distractors", JSONB),
    sa.column("era", sa.String),
    sa.column("note", sa.Text),
    sa.column("fugen", sa.String),
)

# The gap-fill words of 2026-08-29, verbatim — the contract of this revision.
# tests/test_quizgen.py pins that every one of them is a bank entry.
_ADDED: tuple[str, ...] = (
    "Carl", "Conrad", "Caspar", "Cäcilie", "Christoph", "Christian", "Chef", "Chor", "Cousine", "Cousin",
    "Quelle", "Qualle", "Quark", "Quarz", "Quittung", "Quartier", "Quirin", "Aquarium", "Aquarell", "bequem",
    "Xaver", "Xylophon", "Hexe", "Hefe", "Taxi", "Taxe", "Axt", "Text", "Exempel", "boxen",
    "Yacht", "Ypsilon", "Physik", "Pyjama", "Zylinder", "Bayern", "Bauern",
    "Ähre", "Ehre", "Äpfel", "Ärger", "Ärmel", "Öfen", "Öl", "Übung", "Übel", "Überfluss",
    "Irrtum", "Inhalt", "Innung", "Jagd", "Jubel", "Jugend", "Tugend", "Urkunde", "Umzug", "Umweg",
    "Unterschrift", "Unterricht", "Rat", "Rad", "Rechnung", "Reise", "Reihe", "Obst", "Onkel", "Enkel",
    "Ordnung", "Nachbar", "Nachlass", "Not", "Macht", "Eltern", "Esel",
    "jetzt", "jetzo", "jemand", "niemand", "jeder", "vier", "Vogt", "Klavier",
    "Fuß", "Fluß", "Gruß", "Spaß", "Schloß", "Möwe", "Löwe", "Söhne", "Sühne",
)  # fmt: skip


def upgrade() -> None:
    rows = {r["word"]: r for r in json.loads(_SEED.read_text(encoding="utf-8"))}
    missing = [w for w in _ADDED if w not in rows]
    if missing:
        raise RuntimeError(f"quiz_words.json lacks gap-fill words: {missing}")
    conn = op.get_bind()
    present = {
        r[0] for r in conn.execute(sa.select(_QUIZ_WORDS.c.word).where(_QUIZ_WORDS.c.word.in_(list(_ADDED)))).all()
    }
    to_insert = [rows[w] for w in _ADDED if w not in present]
    if to_insert:
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
                for r in to_insert
            ],
        )


def downgrade() -> None:
    op.execute(_QUIZ_WORDS.delete().where(_QUIZ_WORDS.c.word.in_(list(_ADDED))))
