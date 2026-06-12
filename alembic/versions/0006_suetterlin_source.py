"""Seed the Suetterlin 1922 Ausgangsschrift chart + fix the style ratio

Seeds the `suetterlin-1922` source (Abbildung 10 "Die Ausgangsschrift" from
Ludwig Suetterlin, *Neuer Leitfaden fuer den Schreibunterricht*, 1922 edition;
PD — author died 1917, DNB scan, see data/sources/suetterlin-1922/SOURCE.md)
and fixes the `suetterlin` style's lineature ratio: 0004 seeded the Kurrent
placeholder [2, 1, 2], but Suetterlin is 1:1:1 per
docs/schriftkunde/suetterlin.md.

NOTE downgrade: deleting the source CASCADEs all bboxes authored on it
(wizard work on the Suetterlin chart is lost); templates keep their rows.

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op


revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE styles SET default_style_ratio = '[1, 1, 1]'::jsonb WHERE id = 'suetterlin'")
    op.execute(
        """
        INSERT INTO sources
          (id, style_id, hand_id, kind, title, license, chart_path, chart_size,
           style_ratio, slant_deg, attribution, origin_url, retrieved_date)
        VALUES (
          'suetterlin-1922', 'suetterlin', NULL, 'chart',
          'Sütterlin Ausgangsschrift (Leitfaden 1922)', 'PD',
          'data/sources/suetterlin-1922/chart.jpg',
          '{"w": 1614, "h": 1300}'::jsonb,
          '[1, 1, 1]'::jsonb, 90.0,
          'Ludwig Sütterlin († 1917), via Wikimedia Commons (DNB-Scan), Public Domain Mark 1.0',
          'https://commons.wikimedia.org/wiki/File:%22Neuer_Leitfaden_f%C3%BCr_den_Schreibunterricht%22_-_Abbildung_10._Die_Ausgangsschrift.jpg',
          '2026-06-12'
        )
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM sources WHERE id = 'suetterlin-1922'")
    op.execute("UPDATE styles SET default_style_ratio = '[2, 1, 2]'::jsonb WHERE id = 'suetterlin'")
