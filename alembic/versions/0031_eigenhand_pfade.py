"""Add eigenhand_strips.pfade — the followed pen path of a written word

The author's request of 2026-09-12: „bitte auch im admin integrieren das ich
bei den handstreifen und den wörtern generell den pfad auch sehen kann". For
the words the path is already stored (`word_instances.strokes`); for the strips
nothing about a path existed at all — the row held an image, a verdict, a
Befund and a Fleckenmaske, but no ductus.

Stored is the reading, never a second image: a list of per-word-box entries,
each with its strokes in the word's own units (baseline 0, midband 1 — the
SAME frame `word_instances.strokes` uses, so one overlay serves both surfaces)
and the registration that maps them into the strip's pixels. The pixels are
untouched, exactly as with 0029 and 0030.

It hangs off the STRIP and not off the Fassung, which is where `befund` and
`flecken` sit: those two can be taken before the pixels are ever pushed up, a
path cannot — it can only be followed where the ink is stored.

Nullable and additive. NULL reads as „nobody has followed this Fassung yet",
an empty list as „followed, nothing found" — the same distinction 0030
established. The column is DEFERRED in the repository beside the PNG: a
Bestand read must never drag every path of every Fassung along.

Revision ID: 0031
Revises: 0030
Create Date: 2026-09-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0031"
down_revision: str | None = "0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PORTABLE_JSON = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column("eigenhand_strips", sa.Column("pfade", PORTABLE_JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("eigenhand_strips", "pfade")
