"""Seed the Petzendorfer 1889 chart source (Kurrent digits + reserve forms)

Seeds the `petzendorfer-1889` source under the `kurrent` style — the PD
Schriften-Atlas plate (Tafel 1 "Deutsche Schreibschrift", anonymous
lithograph, §66 UrhG expired; see data/sources/petzendorfer-1889/SOURCE.md).
It is the only PD Kurrent chart in the repo carrying a DIGITS row (1–0),
which Loth 1866 lacks entirely — the digit templates for the Kurrent style
will be authored from here (docs/concepts/federmodelle.md §4).

Deliberately a SEPARATE source, never merged into loth-1866: it is another
hand (calligraphic 1880s Kurrent) at a different measured slant (~57° for
the thick downstrokes vs. Loth's ~50°) — provenance stays clean per source.
The bytes already live committed on disk; only the DB row was missing.

NOTE downgrade: deleting the source CASCADEs any bboxes authored on it.

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-08
"""

from collections.abc import Sequence

from alembic import op


revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO sources
          (id, style_id, hand_id, kind, title, license, chart_path, chart_size,
           style_ratio, slant_deg, attribution, origin_url, retrieved_date)
        VALUES (
          'petzendorfer-1889', 'kurrent', NULL, 'chart',
          'Deutsche Schreibschrift (Petzendorfer 1889)', 'PD',
          'data/sources/petzendorfer-1889/chart.jpg',
          '{"w": 4372, "h": 2994}'::jsonb,
          '[2, 1, 2]'::jsonb, 57.0,
          'Tafel anonym (Lithografie E. Hochdanz), aus Ludwig Petzendorfer († 1918), Schriften-Atlas, Stuttgart 1889, via archive.org, Public Domain (§66/§64 UrhG)',
          'https://archive.org/details/schriftenatlasei02petz',
          '2026-06-10'
        )
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM sources WHERE id = 'petzendorfer-1889'")
