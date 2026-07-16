"""Correct the quiz gloss for "Gulden": silver coin, not gold

The reading-quiz word bank glossed "Gulden" as "alte Goldmünze". The
19th-century South German Gulden — the one appearing in the old letters the
quiz trains for — was a silver coin (Münchner Münzvertrag 1837); only the
name derives from the medieval gold "guldin". The generator source
(tools/quizgen/corpus.py) and quiz_words.json carry the corrected note for
fresh seeds; this migration fixes the already-seeded row in place.

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-16
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_NOTE = "alte Silbermünze (süddeutsche Währung)"
_OLD_NOTE = "alte Goldmünze"


def upgrade() -> None:
    op.execute(
        sa.text("UPDATE quiz_words SET note = :new WHERE word = 'Gulden' AND note = :old").bindparams(
            new=_NEW_NOTE, old=_OLD_NOTE
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("UPDATE quiz_words SET note = :old WHERE word = 'Gulden' AND note = :new").bindparams(
            new=_NEW_NOTE, old=_OLD_NOTE
        )
    )
