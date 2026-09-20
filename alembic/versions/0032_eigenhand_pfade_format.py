"""Add eigenhand_strips.pfade_format — the format marker of a stored Bahn

Until now nothing on the row said which Streifen-Pfad format its `pfade` cell
was written in. The write compared the pushed format against the core constant
`core.eigenhand.pfad.PFAD_FORMAT` and answered 409 on a mismatch, and the read
stamped its answer with that very same constant — so the answer said what the
RUNNING IMAGE believes, never what the row holds.

That is fine while there is exactly one format and fatal the moment there are
two: bumping the constant to 2 would make every row followed under 1 read as
2, and a later Ampel would show colours for sensors that were never computed
on it. Format 1 and 2 cannot coexist until the row says which it is; this
revision is what makes the coexistence possible, and it moves no semantics —
after it, writing still produces only format 1.

NOT NULL with `server_default "1"`, which IS the data migration: every row that
exists was written under format 1, and Postgres fills them in place. The marker
lands on every row of the table, including the ones whose `pfade` is NULL — a
Fassung nobody has followed is a format-1 row waiting for its first push, and
giving it a format costs nothing while a NULL would buy the read a second
„unknown" branch.

A column rather than an envelope `{format, eintraege}` inside the JSON cell:
the deferred `pfade` cell is not rewritten at all this way, which keeps the
revision off the one piece of own-hand data the archive chain had to be built
for (`tools.eigenhand.pull --pfade`, #635), and every reader of that cell — the
tool's merge, the SPA's Rohzahlen — keeps working untouched.

Not deferred in the repository, unlike `pfade` itself: it is one small integer,
and the list of „which Fassung still needs re-following" has to tell the
formats apart without loading a single path.

Revision ID: 0032
Revises: 0031
Create Date: 2026-09-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0032"
down_revision: str | None = "0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("eigenhand_strips", sa.Column("pfade_format", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("eigenhand_strips", "pfade_format")
