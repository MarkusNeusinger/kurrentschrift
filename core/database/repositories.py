"""Repository layer — thin AsyncSession wrappers per model."""

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Bbox, Glyph, Source


class SourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, source_id: str) -> Source | None:
        result = await self.session.execute(select(Source).where(Source.id == source_id))
        return result.scalar_one_or_none()

    async def list(self) -> list[Source]:
        result = await self.session.execute(select(Source).order_by(Source.id))
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


class GlyphRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, source_id: str, glyph_key: str, variant: int = 0) -> Glyph | None:
        result = await self.session.execute(
            select(Glyph).where(Glyph.source_id == source_id, Glyph.glyph_key == glyph_key, Glyph.variant == variant)
        )
        return result.scalar_one_or_none()

    async def list(self, source_id: str) -> list[Glyph]:
        result = await self.session.execute(
            select(Glyph).where(Glyph.source_id == source_id).order_by(Glyph.glyph_key, Glyph.variant)
        )
        return list(result.scalars().all())

    async def upsert(self, source_id: str, glyph_key: str, canonical: dict, variant: int = 0) -> Glyph:
        """Insert-or-update by (source_id, glyph, position, variant).

        `canonical` must carry `glyph`, `position`, `advance`, `entry`,
        `exit_pt`, `anchors`, `half_widths`, `raw_path`, `trace_meta`,
        `measurements`. Produced by `core.pipeline.canonical_from_path`.
        """
        payload = {
            "source_id": source_id,
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
        update_cols = {k: v for k, v in payload.items() if k not in ("source_id", "glyph", "position", "variant")}
        stmt = pg_insert(Glyph).values(**payload)
        stmt = stmt.on_conflict_do_update(constraint="uq_glyph_source_gpv", set_=update_cols)
        await self.session.execute(stmt)
        await self.session.flush()
        result = await self.session.execute(
            select(Glyph).where(
                Glyph.source_id == source_id,
                Glyph.glyph == canonical["glyph"],
                Glyph.position == canonical["position"],
                Glyph.variant == variant,
            )
        )
        return result.scalar_one()

    async def delete(self, source_id: str, glyph_key: str, variant: int = 0) -> bool:
        result = await self.session.execute(
            delete(Glyph).where(Glyph.source_id == source_id, Glyph.glyph_key == glyph_key, Glyph.variant == variant)
        )
        return (result.rowcount or 0) > 0
