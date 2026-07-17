"""Correct two quiz glosses: Groschen and Witwe

The reading-quiz word bank glossed "Groschen" as "Münze (10 Pfennig)" — but
the Groschen is a centuries-old coin name and only the Kaiserreich pinned it
colloquially to the 10-Pfennig piece, so the bare equation is wrong for most
of the letters the quiz trains for. "Witwe" was glossed "Frau eines
Verstorbenen", which reads as "wife of any deceased man"; a Witwe is a woman
whose own husband has died. The generator source (tools/quizgen/corpus.py)
and quiz_words.json carry the corrected notes for fresh seeds; this
migration fixes the already-seeded rows in place.

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (word, old note, new note)
_FIXES: list[tuple[str, str, str]] = [
    ("Groschen", "Münze (10 Pfennig)", "alte Münze; im Kaiserreich das 10-Pfennig-Stück"),
    ("Witwe", "Frau eines Verstorbenen (veraltet: Wittib)", "Frau, deren Ehemann gestorben ist (veraltet: Wittib)"),
]


def upgrade() -> None:
    for word, old, new in _FIXES:
        op.execute(
            sa.text("UPDATE quiz_words SET note = :new WHERE word = :word AND note = :old").bindparams(
                word=word, new=new, old=old
            )
        )


def downgrade() -> None:
    for word, old, new in _FIXES:
        op.execute(
            sa.text("UPDATE quiz_words SET note = :old WHERE word = :word AND note = :new").bindparams(
                word=word, new=new, old=old
            )
        )
