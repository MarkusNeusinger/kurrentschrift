"""Repository layer — thin AsyncSession wrappers per model."""

# Annotations are lazy strings: several repositories define a `list` method, which
# would otherwise shadow the builtin `list` when a LATER method in the same class
# is annotated `-> list[...]` (evaluated at class-definition time → "'function'
# object is not subscriptable" on import). Stringised annotations sidestep that.
from __future__ import annotations

from typing import Any

from sqlalchemy import delete, func, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from core.database.models import Aggregate, Bbox, GlyphPair, Hand, Instance, QuizWord, Source, Style, Template


class StyleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, style_id: str) -> Style | None:
        result = await self.session.execute(select(Style).where(Style.id == style_id))
        return result.scalar_one_or_none()

    async def list(self) -> list[Style]:
        result = await self.session.execute(select(Style).order_by(Style.id))
        return list(result.scalars().all())


class QuizWordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> list[QuizWord]:
        result = await self.session.execute(select(QuizWord).order_by(QuizWord.id))
        return list(result.scalars().all())


class HandRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, hand_id: str) -> Hand | None:
        result = await self.session.execute(select(Hand).where(Hand.id == hand_id))
        return result.scalar_one_or_none()

    async def list(self) -> list[Hand]:
        result = await self.session.execute(select(Hand).order_by(Hand.id))
        return list(result.scalars().all())


class SourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, source_id: str) -> Source | None:
        result = await self.session.execute(select(Source).where(Source.id == source_id))
        return result.scalar_one_or_none()

    async def list(self, style_id: str | None = None) -> list[Source]:
        stmt = select(Source).order_by(Source.id)
        if style_id is not None:
            stmt = stmt.where(Source.style_id == style_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class BboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, source_id: str, glyph_key: str) -> Bbox | None:
        result = await self.session.execute(
            select(Bbox).where(Bbox.source_id == source_id, Bbox.glyph_key == glyph_key)
        )
        return result.scalar_one_or_none()

    async def list(self, source_id: str) -> list[Bbox]:
        result = await self.session.execute(select(Bbox).where(Bbox.source_id == source_id).order_by(Bbox.glyph_key))
        return list(result.scalars().all())

    async def list_status(self, source_id: str) -> list[dict]:
        """Availability flags + layout scalars (glyph_key, locked, crop rect,
        baseline) — the public quiz's gating read and the Tafel's sheet
        layout, without the heavy mask/ink/patch JSONB columns."""
        result = await self.session.execute(
            select(Bbox.glyph_key, Bbox.locked, Bbox.x0, Bbox.x1, Bbox.y0, Bbox.y1, Bbox.baseline_y)
            .where(Bbox.source_id == source_id)
            .order_by(Bbox.glyph_key)
        )
        return [
            {"glyph_key": k, "locked": bool(locked), "x0": x0, "x1": x1, "y0": y0, "y1": y1, "baseline_y": baseline_y}
            for k, locked, x0, x1, y0, y1, baseline_y in result.all()
        ]

    async def upsert(self, source_id: str, glyph_key: str, **fields: Any) -> Bbox:
        """Insert-or-update by (source_id, glyph_key)."""
        payload = {"source_id": source_id, "glyph_key": glyph_key, **fields}
        update_cols = {k: v for k, v in payload.items() if k not in ("source_id", "glyph_key", "id")}
        stmt = pg_insert(Bbox).values(**payload)
        stmt = stmt.on_conflict_do_update(constraint="uq_bbox_source_glyph", set_=update_cols)
        await self.session.execute(stmt)
        await self.session.flush()
        result = await self.session.execute(
            select(Bbox).where(Bbox.source_id == source_id, Bbox.glyph_key == glyph_key)
        )
        return result.scalar_one()

    async def delete(self, source_id: str, glyph_key: str) -> bool:
        result = await self.session.execute(
            delete(Bbox).where(Bbox.source_id == source_id, Bbox.glyph_key == glyph_key)
        )
        return (result.rowcount or 0) > 0


# The render path (public /write endpoints) never reads the dense stylus
# capture or the trace statistics — deferring the two heavy JSONB columns
# (raw_path can be ~100 KB per glyph) skips their transfer + parse per request.
# Deferred attributes lazy-load on first access, so callers passing
# `render_only=True` must not touch `raw_path`/`measurements` off-session.
_RENDER_ONLY_DEFERS = (defer(Template.raw_path), defer(Template.measurements))


class TemplateRepository:
    """Canonical templates (Grundvorlage), keyed per style.

    Templates hang off a `style`, not a single source: the canonical for
    (style, glyph, variant) is the norm. `provenance_source_id` records
    which teaching chart it was traced from. The router resolves the style from
    the source being worked on.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self, style_id: str, glyph_key: str, variant: int = 0, *, render_only: bool = False
    ) -> Template | None:
        stmt = select(Template).where(
            Template.style_id == style_id, Template.glyph_key == glyph_key, Template.variant == variant
        )
        if render_only:
            stmt = stmt.options(*_RENDER_ONLY_DEFERS)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, style_id: str) -> list[Template]:
        result = await self.session.execute(
            select(Template).where(Template.style_id == style_id).order_by(Template.glyph_key, Template.variant)
        )
        return list(result.scalars().all())

    async def list_summaries(self, style_id: str) -> list[dict]:
        """The sidebar's summary fields only — never the heavy JSONB columns.

        A fully authored source makes full-row `list()` decode multi-MB of
        `raw_path`/`anchors`/`trace_meta` per sidebar load just to render six
        scalar fields; select exactly those instead (same pattern as
        `half_widths_for_source`).
        """
        result = await self.session.execute(
            select(Template.glyph_key, Template.glyph, Template.variant, Template.advance)
            .where(Template.style_id == style_id)
            .order_by(Template.glyph_key, Template.variant)
        )
        return [{"glyph_key": k, "glyph": g, "variant": v, "advance": a} for k, g, v, a in result.all()]

    async def get_many(
        self, style_id: str, glyph_keys: list[str], variant: int = 0, *, render_only: bool = False
    ) -> list[Template]:
        """The requested keys' templates in one query (the batch write endpoint)."""
        if not glyph_keys:
            return []
        stmt = select(Template).where(
            Template.style_id == style_id, Template.glyph_key.in_(glyph_keys), Template.variant == variant
        )
        if render_only:
            stmt = stmt.options(*_RENDER_ONLY_DEFERS)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def half_widths_for_source(self, style_id: str, provenance_source_id: str) -> list[list[float]]:
        """Just the `half_widths` arrays of a style's templates traced from one source.

        Selects the single JSON column (not whole Template rows with their large
        anchors/raw_path/trace_meta payloads) — the source-pooled constant nib
        (`api.rendering.pooled_constant_nib`) only needs the widths.
        """
        result = await self.session.execute(
            select(Template.half_widths).where(
                Template.style_id == style_id, Template.provenance_source_id == provenance_source_id
            )
        )
        return [list(hw) for hw in result.scalars().all() if hw]

    async def upsert(
        self, style_id: str, glyph_key: str, canonical: dict, variant: int = 0, provenance_source_id: str | None = None
    ) -> Template:
        """Insert-or-update by (style_id, glyph, variant).

        `canonical` must carry `glyph`, `advance`, `entry`, `exit_pt`,
        `anchors`, `half_widths`, `raw_path`, `trace_meta`, `measurements`.
        Produced by `core.pipeline.canonical_from_path`.
        """
        payload = {
            "style_id": style_id,
            "provenance_source_id": provenance_source_id,
            "glyph_key": glyph_key,
            "glyph": canonical["glyph"],
            "variant": variant,
            "advance": canonical["advance"],
            "entry": canonical["entry"],
            "exit_pt": canonical["exit_pt"],
            "anchors": canonical["anchors"],
            "half_widths": canonical["half_widths"],
            "raw_path": canonical["raw_path"],
            "trace_meta": canonical["trace_meta"],
            "measurements": canonical.get("measurements", {}),
        }
        update_cols = {k: v for k, v in payload.items() if k not in ("style_id", "glyph", "variant")}
        stmt = pg_insert(Template).values(**payload)
        stmt = stmt.on_conflict_do_update(constraint="uq_template_style_gv", set_=update_cols)
        await self.session.execute(stmt)
        await self.session.flush()
        result = await self.session.execute(
            select(Template).where(
                Template.style_id == style_id, Template.glyph == canonical["glyph"], Template.variant == variant
            )
        )
        return result.scalar_one()

    async def delete(self, style_id: str, glyph_key: str, variant: int = 0) -> bool:
        result = await self.session.execute(
            delete(Template).where(
                Template.style_id == style_id, Template.glyph_key == glyph_key, Template.variant == variant
            )
        )
        return (result.rowcount or 0) > 0


class GlyphPairRepository:
    """Sparse letter-pair overrides (redesign R3); the §4 generator is the default."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, style_id: str) -> list[GlyphPair]:
        result = await self.session.execute(
            select(GlyphPair)
            .where(GlyphPair.style_id == style_id)
            .order_by(GlyphPair.left_key, GlyphPair.right_key, GlyphPair.variant)
        )
        return list(result.scalars().all())

    async def get(self, style_id: str, left_key: str, right_key: str, variant: int = 0) -> GlyphPair | None:
        result = await self.session.execute(
            select(GlyphPair).where(
                GlyphPair.style_id == style_id,
                GlyphPair.left_key == left_key,
                GlyphPair.right_key == right_key,
                GlyphPair.variant == variant,
            )
        )
        return result.scalar_one_or_none()

    async def approved_for_pairs(
        self, style_id: str, pairs: list[tuple[str, str]], variant: int = 0
    ) -> dict[tuple[str, str], dict]:
        """The APPROVED override geometries for a word's adjacent key pairs.

        One query for the whole word (the /write/word path); returns
        {(left_key, right_key): geometry}. Unapproved rows never render.
        """
        if not pairs:
            return {}
        result = await self.session.execute(
            select(GlyphPair).where(
                GlyphPair.style_id == style_id,
                # Exact pair set in SQL (row-value IN) — no over-fetch of the
                # cartesian lefts×rights as the table grows.
                tuple_(GlyphPair.left_key, GlyphPair.right_key).in_(list(set(pairs))),
                GlyphPair.variant == variant,
                GlyphPair.approved.is_(True),
            )
        )
        return {(row.left_key, row.right_key): dict(row.geometry) for row in result.scalars().all()}

    async def upsert(self, style_id: str, left_key: str, right_key: str, variant: int = 0, **fields: Any) -> GlyphPair:
        """Insert-or-update by (style_id, left_key, right_key, variant)."""
        payload = {"style_id": style_id, "left_key": left_key, "right_key": right_key, "variant": variant, **fields}
        update_cols = {
            k: v for k, v in payload.items() if k not in ("style_id", "left_key", "right_key", "variant", "id")
        }
        # The ORM-level `onupdate` never fires through on_conflict_do_update —
        # stamp the recency column explicitly so admin UIs can trust it.
        update_cols["updated_at"] = func.now()
        stmt = pg_insert(GlyphPair).values(**payload)
        stmt = stmt.on_conflict_do_update(constraint="uq_glyph_pair_style_lr_variant", set_=update_cols)
        await self.session.execute(stmt)
        await self.session.flush()
        result = await self.session.execute(
            select(GlyphPair).where(
                GlyphPair.style_id == style_id,
                GlyphPair.left_key == left_key,
                GlyphPair.right_key == right_key,
                GlyphPair.variant == variant,
            )
        )
        return result.scalar_one()

    async def delete(self, style_id: str, left_key: str, right_key: str, variant: int = 0) -> bool:
        result = await self.session.execute(
            delete(GlyphPair).where(
                GlyphPair.style_id == style_id,
                GlyphPair.left_key == left_key,
                GlyphPair.right_key == right_key,
                GlyphPair.variant == variant,
            )
        )
        return (result.rowcount or 0) > 0


class InstanceRepository:
    """Per-text glyph occurrences (§12 layer 1). Defined for the post-MVP import."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, source_id: str | None = None) -> list[Instance]:
        stmt = select(Instance).order_by(Instance.glyph_key)
        if source_id is not None:
            stmt = stmt.where(Instance.source_id == source_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class AggregateRepository:
    """Per-hand aggregates (§12 layer 2). Defined for the later aggregation job."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, hand_id: str | None = None) -> list[Aggregate]:
        stmt = select(Aggregate).order_by(Aggregate.glyph)
        if hand_id is not None:
            stmt = stmt.where(Aggregate.hand_id == hand_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
