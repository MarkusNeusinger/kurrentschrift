"""Remove the per-position template/bbox triplication (redesign R2)

One authored form per glyph: glyph_keys lose their `-initial/-medial/-final`
suffix (`a-medial` → `a`; the s-allographs untangle to `longs` — historically
`s-medial` — and `s`), fan-out sibling rows collapse to one, `templates.
position` and `bboxes.split` are dropped, and the template identity constraint
becomes (style_id, glyph, variant). The word position stays render context in
`core/shaping.py`; true allographs remain separate glyphs.

Safety: sibling rows are expected to be identical (the admin fan-out wrote the
same form to all three keys). A template sibling whose authored content
genuinely differs is NOT deleted — it is kept under the same base key as the
next free variant, per the redesign decision ("ein aufgetrennter Buchstabe
würde als variant erhalten"). Bbox siblings merge; `locked` is OR-ed.

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-17
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_SUFFIXES = ("-initial", "-medial", "-final")

# Historical special keys (see the pre-R2 registries in core/shaping.py /
# app/src/domain/glyphs.ts): `s-medial` was the LONG s ſ, `s-round-medial`
# the round medial s. Everything else was `{base}-{position}`.
_SPECIAL = {"s-medial": "longs", "s-round-medial": "s"}


def _rekey(old: str) -> str:
    if old in _SPECIAL:
        return _SPECIAL[old]
    for suffix in _SUFFIXES:
        if old.endswith(suffix):
            return old[: -len(suffix)]
    return old  # legacy lc-*/uc-* aliases and custom keys pass through


# Downgrade re-key: deterministic single representative per base key. The
# medial form is the historical default; the s-allographs map back to their
# historical medial keys.
_DOWN_SPECIAL = {"longs": "s-medial", "s": "s-round-medial"}


def _downkey(base: str) -> str:
    if base in _DOWN_SPECIAL:
        return _DOWN_SPECIAL[base]
    if base.endswith(tuple(_SUFFIXES)) or base.startswith(("lc-", "uc-")):
        return base
    return f"{base}-medial"


# Dedupe priority when collapsing siblings: the medial form is the historical
# default the admin surfaces preferred, then initial, then final.
def _priority(old_key: str) -> int:
    if old_key in ("s-medial", "s-round-medial") or old_key.endswith("-medial"):
        return 0
    if old_key.endswith("-initial"):
        return 1
    return 2


def upgrade() -> None:
    bind = op.get_bind()

    # ---- templates: re-key, collapse identical siblings, keep differing ones
    # as extra variants of the same base key.
    rows = bind.execute(sa.text("SELECT id, style_id, glyph_key, variant, raw_path, anchors FROM templates")).fetchall()
    groups: dict[tuple, list] = {}
    for row in rows:
        groups.setdefault((row.style_id, _rekey(row.glyph_key), row.variant), []).append(row)

    for (style_id, new_key, variant), members in groups.items():
        members.sort(key=lambda r: (_priority(r.glyph_key), r.glyph_key))
        kept = members[0]
        kept_blob = json.dumps([kept.raw_path, kept.anchors], sort_keys=True)
        next_variant = variant
        for extra in members[1:]:
            if json.dumps([extra.raw_path, extra.anchors], sort_keys=True) == kept_blob:
                bind.execute(sa.text("DELETE FROM templates WHERE id = :id"), {"id": extra.id})
            else:
                # A genuinely different authored form survives as its own variant.
                next_variant = _next_free_variant(bind, style_id, new_key, max(next_variant, variant) + 1)
                bind.execute(
                    sa.text("UPDATE templates SET glyph_key = :k, variant = :v WHERE id = :id"),
                    {"k": new_key, "v": next_variant, "id": extra.id},
                )
        bind.execute(sa.text("UPDATE templates SET glyph_key = :k WHERE id = :id"), {"k": new_key, "id": kept.id})

    # ---- bboxes: re-key + collapse siblings (rects are fan-out copies; OR the lock).
    rows = bind.execute(sa.text("SELECT id, source_id, glyph_key, locked FROM bboxes")).fetchall()
    bgroups: dict[tuple, list] = {}
    for row in rows:
        bgroups.setdefault((row.source_id, _rekey(row.glyph_key)), []).append(row)
    for (_, new_key), members in bgroups.items():
        members.sort(key=lambda r: (_priority(r.glyph_key), r.glyph_key))
        kept = members[0]
        locked = any(r.locked for r in members)
        for extra in members[1:]:
            bind.execute(sa.text("DELETE FROM bboxes WHERE id = :id"), {"id": extra.id})
        bind.execute(
            sa.text("UPDATE bboxes SET glyph_key = :k, locked = :locked WHERE id = :id"),
            {"k": new_key, "locked": locked, "id": kept.id},
        )

    # ---- schema: constraints + columns.
    op.drop_constraint("uq_template_style_gpv", "templates", type_="unique")
    op.drop_column("templates", "position")
    op.create_unique_constraint("uq_template_style_gv", "templates", ["style_id", "glyph", "variant"])
    op.drop_column("bboxes", "split")


def _next_free_variant(bind, style_id: str, glyph_key: str, start: int) -> int:
    variant = start
    while bind.execute(
        sa.text("SELECT 1 FROM templates WHERE style_id = :s AND glyph_key = :k AND variant = :v"),
        {"s": style_id, "k": glyph_key, "v": variant},
    ).fetchone():
        variant += 1
    return variant


def downgrade() -> None:
    bind = op.get_bind()
    op.add_column("bboxes", sa.Column("split", sa.Boolean(), nullable=False, server_default="false"))
    op.drop_constraint("uq_template_style_gv", "templates", type_="unique")
    op.add_column("templates", sa.Column("position", sa.String(16), nullable=False, server_default="medial"))
    op.create_unique_constraint("uq_template_style_gpv", "templates", ["style_id", "glyph", "position", "variant"])
    # Best-effort data reversal: one representative row per glyph gets its
    # historical medial-form key back (the deleted fan-out copies are NOT
    # re-created; the old code reads any position row it finds by key).
    for table in ("templates", "bboxes"):
        rows = bind.execute(sa.text(f"SELECT id, glyph_key FROM {table}")).fetchall()  # noqa: S608
        for row in rows:
            old = _downkey(row.glyph_key)
            if old != row.glyph_key:
                bind.execute(
                    sa.text(f"UPDATE {table} SET glyph_key = :k WHERE id = :id"),  # noqa: S608
                    {"k": old, "id": row.id},
                )
