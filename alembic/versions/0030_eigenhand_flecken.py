"""Add eigenhand_fassungen.flecken — the Fleckenmaske of one Fassung

The author's report of 2026-09-07: „Mein Laserdrucker macht leider im rechten
Bereich unkontrolliert schwarze Punkte, Reinigen hilft nichts … vielleicht
erkennst du sie und löscht sie raus, oder es gibt dann beim Einlesen vielleicht
direkt im Admin-Bereich, dass ich mit einem kleinen runden Pinsel die Punkte
löschen kann." Both halves are one mechanism: a MASK of circles in the strip
crop's own millimetres, found automatically at import (`core.eigenhand.flecken`)
and extended by hand in the workbench's brush.

Stored is the mask, never a modified image. The strip bytes are the reserved
dataset's primary evidence and the two-channel doctrine (owner, 2026-08-27)
keeps every cleanup a derived view: `crop.without_flecken` paints local paper
into the circles on read, and deleting the mask brings the raw strip back byte
for byte.

Nullable and additive, like 0029. NULL reads as „nobody has looked at this
Fassung yet" and an empty list as „looked, nothing to erase" — a distinction
the sync depends on: it fills a NULL and never overwrites a list, so a mask the
author painted by hand survives every re-push of the automatic one.

Revision ID: 0030
Revises: 0029
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PORTABLE_JSON = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column("eigenhand_fassungen", sa.Column("flecken", PORTABLE_JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("eigenhand_fassungen", "flecken")
