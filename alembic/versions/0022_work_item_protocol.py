"""Add the work-item handling protocol columns (Werkbank W4)

Additive: an Auftragskorb row used to carry only the admin's `note` and the
session's closing `resolution`. The protocol
(`docs/proposals/optimierungs-werkbank.md` §5) now also records what the
working session UNDERSTOOD the task to be before touching anything
(`understanding`), whether it could reproduce the complaint (`reproduced`),
and which stage of the writing path it diagnosed (`stage`) — so the closed
rows become a searchable archive of symptom → diagnosis → change → effect.
`acked_at`/`closed_at` timestamp the two transitions.

All columns are nullable: existing rows predate the protocol and stay valid.
`status` keeps its plain String(16) — the widened vocabulary
(open | ack | done | returned) is validated in the API, not by a DB enum, so
no type change is needed here.

Revision ID: 0022
Revises: 0021
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("work_items", sa.Column("understanding", sa.Text(), nullable=True))
    op.add_column("work_items", sa.Column("reproduced", sa.String(8), nullable=True))
    op.add_column("work_items", sa.Column("stage", sa.String(24), nullable=True))
    op.add_column("work_items", sa.Column("acked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("work_items", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("work_items", "closed_at")
    op.drop_column("work_items", "acked_at")
    op.drop_column("work_items", "stage")
    op.drop_column("work_items", "reproduced")
    op.drop_column("work_items", "understanding")
