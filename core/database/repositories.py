"""Repository layer — thin AsyncSession wrappers per model."""

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Aggregate, Bbox, Hand, Instance, Source, Style, Template


class StyleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, style_id: str) -> Style | None:
        result = await self.session.execute(select(Style).where(Style.id == style_id))
        return result.scalar_one_or_none()

    async def list(self) -> list[Style]:
        result = await self.session.execute(select(Style).order_by(Style.id))
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


class TemplateRepository:
    """Canonical templates (Grundvorlage), keyed per style.

    Templates hang off a `style`, not a single source: the canonical for
    (style, glyph, position, variant) is the norm. `provenance_source_id` records
    which teaching chart it was traced from. The router resolves the style from
    the source being worked on.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, style_id: str, glyph_key: str, variant: int = 0) -> Template | None:
        result = await self.session.execute(
            select(Template).where(
                Template.style_id == style_id, Template.glyph_key == glyph_key, Template.variant == variant
            )
        )
        return result.scalar_one_or_none()

    async def list(self, style_id: str) -> list[Template]:
        result = await self.session.execute(
            select(Template)
            .where(Template.style_id == style_id)
            .order_by(Template.glyph_key, Template.variant)
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        style_id: str,
        glyph_key: str,
        canonical: dict,
        variant: int = 0,
        provenance_source_id: str | None = None,
    ) -> Template:
        """Insert-or-update by (style_id, glyph, position, variant).

        `canonical` must carry `glyph`, `position`, `advance`, `entry`,
        `exit_pt`, `anchors`, `half_widths`, `raw_path`, `trace_meta`,
        `measurements`. Produced by `core.pipeline.canonical_from_path`.
        """
        payload = {
            "style_id": style_id,
            "provenance_source_id": provenance_source_id,
            "glyph_key": glyph_key,
            "glyph": canonical["glyph"],
            "position": canonical["position"],
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
        update_cols = {k: v for k, v in payload.items() if k not in ("style_id", "glyph", "position", "variant")}
        stmt = pg_insert(Template).values(**payload)
        stmt = stmt.on_conflict_do_update(constraint="uq_template_style_gpv", set_=update_cols)
        await self.session.execute(stmt)
        await self.session.flush()
        result = await self.session.execute(
            select(Template).where(
                Template.style_id == style_id,
                Template.glyph == canonical["glyph"],
                Template.position == canonical["position"],
                Template.variant == variant,
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
