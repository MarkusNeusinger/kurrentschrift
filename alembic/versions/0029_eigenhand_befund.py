"""Add eigenhand_fassungen.befund — the Streifen-Befund's measurement

The owner's loop of 2026-09-07: write · scan · Befund · tick · rewrite the
weak strips. The Befund is what one written Fassung says about itself in
numbers — pen width, continuity of the medial axis, the counters the ink
encloses, the body runs it fell into, how it sits in the ruling — computed
locally by `tools.eigenhand.apply` where the pixels are, pushed up by
`tools.eigenhand.sync` and shown per Fassung in the workbench.

Stored is the MEASUREMENT only. The suggestion (`sauber` · `brauchbar` ·
`neu schreiben`), the dominant reason and the rank among a strip's Fassungen
are DERIVED on read (`core.eigenhand.befund`), exactly like a strip's state:
a rank changes the moment a better Fassung arrives, so a stored one would be
wrong from that moment on.

Nullable and additive: every Fassung filed before the Befund existed keeps a
NULL, which reads as "no reading" and never as "a bad one". No pixels move —
the strip images stay where §7.2 put them, the reserved dataset stays local
and archived, and this column holds numbers derived from them.

Revision ID: 0029
Revises: 0028
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0029"
down_revision: str | None = "0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PORTABLE_JSON = sa.JSON().with_variant(JSONB(), "postgresql")


def upgrade() -> None:
    op.add_column("eigenhand_fassungen", sa.Column("befund", PORTABLE_JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("eigenhand_fassungen", "befund")
