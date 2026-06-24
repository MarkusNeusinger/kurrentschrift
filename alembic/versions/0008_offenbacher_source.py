"""Seed the Offenbacher (Koch 1928) chart source

Seeds the `koch-1928` chart source under the `offenbacher` style — the third
Grundvorlage, analogous to Loth 1866 (Kurrent) and Sütterlin 1922. The plate is
"Das deutsche Alphabet" from Rudolf Koch, *Die Offenbacher Schrift* (Heintze &
Blanckertz, 1928); PD — Koch died 1934 (§64 UrhG, 70 J. p. m. a., abgelaufen Ende
2004), Commons Public Domain Mark 1.0. The bytes already live committed on disk
(data/sources/koch-1928/chart.jpg, see its SOURCE.md); only the DB row was
missing, so the style read `authorable=false` and the public Schreibtafel had no
Offenbacher scan to show.

`authorable` is DERIVED (api/routers/styles.py::_authorable: a chart source whose
bytes exist on disk), so this insert alone flips Offenbacher to authorable and
makes GET /sources/koch-1928/chart serve the scan. chart_size (2190 × 1029)
matches the deskew-checked + content-cropped plate (see its SOURCE.md);
style_ratio (2:3:2, mittenbetont) and slant (~78°) follow the SOURCE.md note.

Also backfills `loth-1866` (Kurrent): the missing `origin_url` (so the public
Schreibtafel can link all three Grundvorlagen to their source) and the attributed
author in `attribution` (Johann Thomas Loth, zugeschrieben — no death year is
documented, unlike Sütterlin † 1917 / Koch † 1934), to match the other two.

NOTE downgrade: deleting the source CASCADEs any bboxes authored on it; none
exist today (Offenbacher is display-only), so the downgrade is clean. The
loth-1866 backfill reverts to its prior values (origin_url NULL, plain
Commons/PD attribution).

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-24
"""

from collections.abc import Sequence

from alembic import op


revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO sources
          (id, style_id, hand_id, kind, title, license, chart_path, chart_size,
           style_ratio, slant_deg, attribution, origin_url, retrieved_date)
        VALUES (
          'koch-1928', 'offenbacher', NULL, 'chart',
          'Offenbacher Schrift (Koch 1928)', 'PD',
          'data/sources/koch-1928/chart.jpg',
          '{"w": 2190, "h": 1029}'::jsonb,
          '[2, 3, 2]'::jsonb, 78.0,
          'Rudolf Koch († 1934), Die Offenbacher Schrift (Heintze & Blanckertz 1928), via Wikimedia Commons, Public Domain Mark 1.0',
          'https://commons.wikimedia.org/wiki/File:Rudolf_Koch_Die_Offenbacher_Schrift_1928.pdf',
          '2026-06-23'
        )
        """
    )
    op.execute(
        "UPDATE sources SET "
        "origin_url = 'https://commons.wikimedia.org/wiki/File:Deutsche_Kurrentschrift.jpg', "
        "attribution = 'Johann Thomas Loth (zugeschrieben), Der Damen-Briefsteller 1866, "
        "via Wikimedia Commons, Public Domain Mark 1.0' "
        "WHERE id = 'loth-1866'"
    )


def downgrade() -> None:
    op.execute("DELETE FROM sources WHERE id = 'koch-1928'")
    op.execute(
        "UPDATE sources SET origin_url = NULL, "
        "attribution = 'Via Wikimedia Commons, Public Domain Mark 1.0' "
        "WHERE id = 'loth-1866'"
    )
