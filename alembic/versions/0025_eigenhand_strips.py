"""Add eigenhand_hands + eigenhand_strips, and the session columns on Fassungen

Three additions, one purpose: the workbench should show a written Streifen the
way it shows a chart crop today — and the capture chain should stop asking for
the same three strings on every import.

* `eigenhand_hands` carries a hand's STANDING setup (nib, ink, paper). Ink,
  paper and nib are photometric parameters of the whole campaign, so they are
  typed once and read back from here; `ingest` only records deviations.
* `eigenhand_fassungen` gains the EFFECTIVE values per row. Denormalised on
  purpose: a Fassung has to say out of itself what it was written with, without
  a join and without the implicit rule "NULL means like the hand" — and the day
  the nib really changes, the break is visible in the data instead of being
  reconstructed.
* `eigenhand_strips` holds the strip image. Its own table, because the PNG must
  never ride along on a Bestand query — the same motive that defers
  `templates.raw_path` in the render path.

The chart crops cannot serve as the model here: `sources.chart_path` points at
bytes on disk and "the DB never stores the image", which works because Loth
1866 is public domain and committed. The own-hand strips are the reserved
dataset and can never be in the repo, so for them the bytes have to travel the
other way — into the DB, admin-gated, never public.

The ARCHIVE stays the master. `tools/eigenhand/snapshot.py` already files every
Fassung directory (`streifen.png` + `meta.json`), the Kartei and each Bogen's
`layout.json` into the private archive, so every row added here is
reconstructible from repo + archive alone (owner requirement 2026-08-24). The
`sha256` column is what makes that check mechanical rather than hopeful.

Revision ID: 0025
Revises: 0024
Create Date: 2026-08-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op


revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# The session strings, shared by the hand's standing setup and the per-row copy.
_SESSION_COLUMNS = ("feder", "tinte", "papier")


def upgrade() -> None:
    op.create_table(
        "eigenhand_hands",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hand", sa.String(64), nullable=False),
        sa.Column("style", sa.String(32), nullable=False),
        sa.Column("label", sa.String(128), nullable=True),
        # The standing setup: what this hand writes with unless a run says
        # otherwise. `geraet` is 128 like the rest and like its per-Fassung
        # copy: it holds two words today (`scanner` · `kamera`) but a narrower
        # column than the column it is copied into would turn a longer device
        # name into a truncation error rather than a validation one.
        *(sa.Column(name, sa.String(128), nullable=True) for name in _SESSION_COLUMNS),
        sa.Column("geraet", sa.String(128), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("hand", name="uq_eigenhand_hand"),
    )

    for name in (*_SESSION_COLUMNS, "geraet"):
        op.add_column("eigenhand_fassungen", sa.Column(name, sa.String(128), nullable=True))

    op.create_table(
        "eigenhand_strips",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hand", sa.String(64), nullable=False),
        sa.Column("strip", sa.String(16), nullable=False),
        sa.Column("fassung", sa.String(8), nullable=False),
        sa.Column("sheet", sa.String(16), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        # The unmodified grayscale crop, exactly the bytes apply.py filed
        # locally (two-channel doctrine: no binarisation baked in).
        sa.Column("png", sa.LargeBinary(), nullable=False),
        sa.Column("width_px", sa.Integer(), nullable=False),
        sa.Column("height_px", sa.Integer(), nullable=False),
        sa.Column("dpi", sa.Float(), nullable=False),
        # Where the crop starts on the sheet, in mm — with width_px this is the
        # scale a word crop needs, and the layout supplies the word's box.
        sa.Column("crop_origin_mm", JSONB(), nullable=False, server_default="[]"),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("hand", "strip", "fassung", name="uq_eigenhand_strip"),
    )
    op.create_index("ix_eigenhand_strips_hand", "eigenhand_strips", ["hand"])
    op.create_index("ix_eigenhand_strips_strip", "eigenhand_strips", ["strip"])


def downgrade() -> None:
    op.drop_index("ix_eigenhand_strips_strip", table_name="eigenhand_strips")
    op.drop_index("ix_eigenhand_strips_hand", table_name="eigenhand_strips")
    op.drop_table("eigenhand_strips")
    for name in ("geraet", *reversed(_SESSION_COLUMNS)):
        op.drop_column("eigenhand_fassungen", name)
    op.drop_table("eigenhand_hands")
