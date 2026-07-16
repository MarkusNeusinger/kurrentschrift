"""Unique (style_id, glyph_key, variant) on templates

Every template read — including the public /write endpoints — keys on
glyph_key via scalar_one_or_none(), so two rows sharing a (style, glyph_key,
variant) would turn every read into a 500. The API's 409 backstops
(_reject_key_identity_mismatch + the stored-row check in /trace) are
read-then-write and bypassable out of band; this constraint makes the
invariant structural. Fails loudly on upgrade if duplicates already exist —
that state is exactly the corruption the constraint exists to prevent, and it
must be resolved by hand, not papered over.

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-16
"""

from collections.abc import Sequence

from alembic import op


revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint("uq_template_style_key_variant", "templates", ["style_id", "glyph_key", "variant"])


def downgrade() -> None:
    op.drop_constraint("uq_template_style_key_variant", "templates", type_="unique")
