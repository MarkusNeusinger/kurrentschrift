"""Repository layer — thin AsyncSession wrappers per model."""

# Annotations are lazy strings: several repositories define a `list` method, which
# would otherwise shadow the builtin `list` when a LATER method in the same class
# is annotated `-> list[...]` (evaluated at class-definition time → "'function'
# object is not subscriptable" on import). Stringised annotations sidestep that.
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import delete, func, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from core.database.models import (
    Aggregate,
    Bbox,
    EigenhandFassung,
    EigenhandSheet,
    GlyphPair,
    Hand,
    Instance,
    PairAggregate,
    PairInstance,
    QuizWord,
    Source,
    Style,
    Template,
    WordInstance,
    WorkItem,
)


# Every `upsert` below writes through a CORE insert-on-conflict, which the ORM
# session cannot see: it never touches the identity map. A plain re-select then
# returns the ALREADY-LOADED instance with its pre-write column values — so an
# endpoint that read the row before writing it (put_bbox's `existing`, the
# /trace identity guard) answers with the state from *before* its own write, and
# the client's next edit builds on that stale copy and drops the last one.
# `populate_existing` forces the re-select to overwrite the loaded attributes.
REFRESH_LOADED = {"populate_existing": True}


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

    async def upsert(self, hand_id: str, **fields: Any) -> Hand:
        """Insert-or-update by primary key — the occurrence batches get-or-create
        their writer row in the same request."""
        payload = {"id": hand_id, **fields}
        stmt = pg_insert(Hand).values(**payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Hand.id], set_={k: v for k, v in payload.items() if k != "id"}
        )
        await self.session.execute(stmt)
        await self.session.flush()
        result = await self.session.execute(select(Hand).where(Hand.id == hand_id).execution_options(**REFRESH_LOADED))
        return result.scalar_one()


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
            select(Bbox)
            .where(Bbox.source_id == source_id, Bbox.glyph_key == glyph_key)
            .execution_options(**REFRESH_LOADED)
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


def _as_json_object(value: Any) -> dict | None:
    """Normalise a JSON sub-object selected out of a JSONB/JSON column.

    A SQL-side extraction (`col["key"]`) comes back already decoded on the
    drivers this repo uses, but the dialects disagree on the wire form, so a
    driver handing back raw JSON text would otherwise leak a string where every
    caller expects a mapping. Anything that is not an object (a scalar left by
    an older row) is dropped rather than passed on half-typed.
    """
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return None
    return value if isinstance(value, dict) else None


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

    async def list_quality(self, style_id: str) -> list[dict]:
        """The stored `trace_meta["quality"]` of every template of one style.

        The admin letter overview wants a score per letter; re-deriving it via
        `GET .../templates/{key}/quality` costs 0.3–2.5 s per glyph (it re-runs
        the image pipeline), while the derivation already stamped the score into
        `trace_meta` at trace/resample time. Extract exactly that sub-object in
        SQL — selecting whole `trace_meta` blobs would drag the dense
        `pixel_anchors`/`half_widths_px` arrays of ~60 rows over the wire for a
        handful of floats.

        Portable across both backends this repo runs on: the index operator
        compiles to `->` on Postgres (JSONB) and to `JSON_QUOTE(JSON_EXTRACT(…))`
        on SQLite (the HTTP test harness), and SQLAlchemy's JSON result
        processing hands back a dict on either. The `json.loads` fallback below
        covers drivers that hand the extraction back as raw JSON text instead.
        """
        result = await self.session.execute(
            select(Template.glyph_key, Template.variant, Template.trace_meta["quality"])
            .where(Template.style_id == style_id)
            .order_by(Template.glyph_key, Template.variant)
        )
        return [{"glyph_key": k, "variant": v, "quality": _as_json_object(q)} for k, v, q in result.all()]

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
            select(Template)
            .where(Template.style_id == style_id, Template.glyph == canonical["glyph"], Template.variant == variant)
            .execution_options(**REFRESH_LOADED)
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
            select(GlyphPair)
            .where(
                GlyphPair.style_id == style_id,
                GlyphPair.left_key == left_key,
                GlyphPair.right_key == right_key,
                GlyphPair.variant == variant,
            )
            .execution_options(**REFRESH_LOADED)
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
    """Per-text glyph occurrences (§12 layer 1), filled by the occurrence harvest."""

    # Everything except the identity columns of `uq_instance_loc` updates on conflict.
    _UPDATE_COLS = (
        "hand_id",
        "template_id",
        "glyph_key",
        "y1",
        "x1",
        "anchors",
        "half_widths",
        "raw_path",
        "measurements",
    )

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self, source_id: str | None = None, glyph_key: str | None = None, hand_id: str | None = None
    ) -> list[Instance]:
        stmt = select(Instance).order_by(Instance.glyph_key, Instance.id)
        if source_id is not None:
            stmt = stmt.where(Instance.source_id == source_id)
        if glyph_key is not None:
            stmt = stmt.where(Instance.glyph_key == glyph_key)
        if hand_id is not None:
            # The aggregation reads per HAND across sources — statistics are a
            # property of the writer, not of the plate they were seen on (§12).
            stmt = stmt.where(Instance.hand_id == hand_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_many(self, rows: list[dict]) -> int:
        """Batch insert-or-update on `uq_instance_loc` (source, glyph, position,
        variant, y0, x0) — a re-harvest of the same specimens refreshes rows in
        place instead of duplicating occurrences."""
        if not rows:
            return 0
        stmt = pg_insert(Instance).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_instance_loc",
            set_={col: stmt.excluded[col] for col in self._UPDATE_COLS} | {"updated_at": func.now()},
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return len(rows)

    async def delete_for_source(self, source_id: str) -> int:
        result = await self.session.execute(delete(Instance).where(Instance.source_id == source_id))
        return result.rowcount or 0


class PairInstanceRepository:
    """Observed letter-join occurrences (handmodell H2), filled by the pair harvest."""

    _UPDATE_COLS = ("hand_id", "left_key", "right_key", "geometry", "measurements")

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self,
        source_id: str | None = None,
        left_key: str | None = None,
        right_key: str | None = None,
        hand_id: str | None = None,
    ) -> list[PairInstance]:
        stmt = select(PairInstance).order_by(PairInstance.left_key, PairInstance.right_key, PairInstance.id)
        if source_id is not None:
            stmt = stmt.where(PairInstance.source_id == source_id)
        if left_key is not None:
            stmt = stmt.where(PairInstance.left_key == left_key)
        if right_key is not None:
            stmt = stmt.where(PairInstance.right_key == right_key)
        if hand_id is not None:
            # The aggregation reads per HAND across sources — statistics are a
            # property of the writer, not of the plate they were seen on (§12).
            stmt = stmt.where(PairInstance.hand_id == hand_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_many(self, rows: list[dict]) -> int:
        """Batch insert-or-update on `uq_pair_instance_occurrence` (source,
        kind, specimen, slot) — one row per observed join, re-harvests refresh
        it; `kind` separates the word-plate and pair-drill id namespaces."""
        if not rows:
            return 0
        stmt = pg_insert(PairInstance).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_pair_instance_occurrence",
            set_={col: stmt.excluded[col] for col in self._UPDATE_COLS} | {"updated_at": func.now()},
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return len(rows)

    async def delete_for_source(self, source_id: str) -> int:
        result = await self.session.execute(delete(PairInstance).where(PairInstance.source_id == source_id))
        return result.rowcount or 0


class WordInstanceRepository:
    """Traced word occurrences — the full learning templates (crop + ductus)."""

    _UPDATE_COLS = ("hand_id", "word", "slots", "strokes", "provenance", "measurements")

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self, source_id: str | None = None, specimen_id: str | None = None, word: str | None = None
    ) -> list[WordInstance]:
        stmt = select(WordInstance).order_by(WordInstance.kind, WordInstance.specimen_id)
        if source_id is not None:
            stmt = stmt.where(WordInstance.source_id == source_id)
        if specimen_id is not None:
            stmt = stmt.where(WordInstance.specimen_id == specimen_id)
        if word is not None:
            # All occurrences of one word TEXT — repeated words have distinct
            # specimen ids ("wenn", "wenn-2") but share `word`.
            stmt = stmt.where(WordInstance.word == word)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def authored_identities(self, source_id: str) -> set[tuple[str, str]]:
        """The (kind, specimen_id) pairs whose stored row is authored — manual
        admin traces a harvest batch must never overwrite."""
        result = await self.session.execute(
            select(WordInstance.kind, WordInstance.specimen_id).where(
                WordInstance.source_id == source_id, WordInstance.provenance == "authored"
            )
        )
        return {(k, s) for k, s in result.all()}

    async def upsert_many(self, rows: list[dict]) -> int:
        """Batch insert-or-update on `uq_word_instance_occurrence` (source,
        kind, specimen) — one trace per specimen sample. Authored-protection is
        the ROUTER's job (filter against `authored_identities` before calling)."""
        if not rows:
            return 0
        stmt = pg_insert(WordInstance).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_word_instance_occurrence",
            set_={col: stmt.excluded[col] for col in self._UPDATE_COLS} | {"updated_at": func.now()},
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return len(rows)

    async def delete_for_source(self, source_id: str, *, include_authored: bool = False) -> int:
        stmt = delete(WordInstance).where(WordInstance.source_id == source_id)
        if not include_authored:
            stmt = stmt.where(WordInstance.provenance != "authored")
        result = await self.session.execute(stmt)
        return result.rowcount or 0


class WorkItemRepository:
    """Filed optimization tasks — the Werkbank's Auftragskorb (stage W1)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, source_id: str, status: str | None = None) -> list[WorkItem]:
        """A source's work items, oldest first — the order a session works
        them off. `status` filters to one of open | ack | done | returned."""
        stmt = select(WorkItem).where(WorkItem.source_id == source_id).order_by(WorkItem.id)
        if status is not None:
            stmt = stmt.where(WorkItem.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, status: str | None = None, source_id: str | None = None) -> list[WorkItem]:
        """Work items across ALL sources, oldest first — the round-start queue
        of a working session, which must not need to know a source id before it
        can read its own tasks. `source_id` narrows it back down to one chart."""
        stmt = select(WorkItem).order_by(WorkItem.id)
        if status is not None:
            stmt = stmt.where(WorkItem.status == status)
        if source_id is not None:
            stmt = stmt.where(WorkItem.source_id == source_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, item_id: int, source_id: str | None = None) -> WorkItem | None:
        stmt = select(WorkItem).where(WorkItem.id == item_id)
        if source_id is not None:
            stmt = stmt.where(WorkItem.source_id == source_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **values: Any) -> WorkItem:
        """Insert one item. No upsert: every filing is its own observation —
        two notes on the same letter are two tasks, not one overwritten row."""
        row = WorkItem(**values)
        self.session.add(row)
        await self.session.flush()
        return row

    async def update(self, row: WorkItem, **values: Any) -> WorkItem:
        """Partial update (note / status / the §5 protocol fields) — only the
        keys the caller actually sent, so a PATCH never clears an unmentioned
        field. The transition rules live in `api.routers.work_items`."""
        for key, value in values.items():
            setattr(row, key, value)
        await self.session.flush()
        # The `onupdate` timestamp is computed server-side and left expired by
        # the flush — refresh explicitly, an implicit reload on attribute
        # access would be lazy IO in async land (MissingGreenlet).
        await self.session.refresh(row)
        return row

    async def delete(self, item_id: int, source_id: str) -> bool:
        result = await self.session.execute(
            delete(WorkItem).where(WorkItem.id == item_id, WorkItem.source_id == source_id)
        )
        return (result.rowcount or 0) > 0


class AggregateRepository:
    """Per-hand aggregates (§12 layer 2), rebuilt from `instances` (Stufenplan H1)."""

    # Everything except the identity columns of `uq_aggregate_hand_kv`.
    _UPDATE_COLS = ("glyph", "cluster_center", "hull", "mean_stats", "n_instances")

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, hand_id: str | None = None, glyph_key: str | None = None) -> list[Aggregate]:
        stmt = select(Aggregate).order_by(Aggregate.glyph_key, Aggregate.variant)
        if hand_id is not None:
            stmt = stmt.where(Aggregate.hand_id == hand_id)
        if glyph_key is not None:
            stmt = stmt.where(Aggregate.glyph_key == glyph_key)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_many(self, rows: list[dict]) -> int:
        """Batch insert-or-update on `uq_aggregate_hand_kv` (hand, glyph_key,
        variant) — a rebuild refreshes the hand's aggregates in place."""
        if not rows:
            return 0
        stmt = pg_insert(Aggregate).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_aggregate_hand_kv",
            # The ORM-level `onupdate` never fires through on_conflict_do_update —
            # stamp the recency column explicitly so admin UIs can trust it.
            set_={col: stmt.excluded[col] for col in self._UPDATE_COLS} | {"updated_at": func.now()},
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return len(rows)

    async def delete_for_hand(self, hand_id: str) -> int:
        result = await self.session.execute(delete(Aggregate).where(Aggregate.hand_id == hand_id))
        return result.rowcount or 0


class PairAggregateRepository:
    """Per-hand pair aggregates (§12 layer 2), rebuilt from `pair_instances` (Stufenplan H2)."""

    # Everything except the identity columns of `uq_pair_aggregate_hand_lr`.
    _UPDATE_COLS = ("offset_center", "connector_center", "hull", "mean_stats", "n_instances")

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(
        self, hand_id: str | None = None, left_key: str | None = None, right_key: str | None = None
    ) -> list[PairAggregate]:
        stmt = select(PairAggregate).order_by(PairAggregate.left_key, PairAggregate.right_key)
        if hand_id is not None:
            stmt = stmt.where(PairAggregate.hand_id == hand_id)
        if left_key is not None:
            stmt = stmt.where(PairAggregate.left_key == left_key)
        if right_key is not None:
            stmt = stmt.where(PairAggregate.right_key == right_key)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_many(self, rows: list[dict]) -> int:
        """Batch insert-or-update on `uq_pair_aggregate_hand_lr` (hand,
        left_key, right_key) — a rebuild refreshes the hand's pair aggregates
        in place."""
        if not rows:
            return 0
        stmt = pg_insert(PairAggregate).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_pair_aggregate_hand_lr",
            # The ORM-level `onupdate` never fires through on_conflict_do_update —
            # stamp the recency column explicitly so admin UIs can trust it.
            set_={col: stmt.excluded[col] for col in self._UPDATE_COLS} | {"updated_at": func.now()},
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return len(rows)

    async def delete_for_hand(self, hand_id: str) -> int:
        result = await self.session.execute(delete(PairAggregate).where(PairAggregate.hand_id == hand_id))
        return result.rowcount or 0


class EigenhandRepository:
    """The own-hand bookkeeping: printed Bögen and judged rows, per hand.

    Its one job beyond plain CRUD is `kartei`: the two tables collapse into
    exactly the dict shape `core.eigenhand.kartei` describes, so the print
    queue and the Bestand run on server rows and on the local `kartei.json`
    without knowing which they got.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def hands(self) -> "list[str]":
        sheets = await self.session.execute(select(EigenhandSheet.hand).distinct())
        fassungen = await self.session.execute(select(EigenhandFassung.hand).distinct())
        return sorted(set(sheets.scalars().all()) | set(fassungen.scalars().all()))

    async def sheets_of(self, hand: str) -> "list[EigenhandSheet]":
        result = await self.session.execute(
            select(EigenhandSheet).where(EigenhandSheet.hand == hand).order_by(EigenhandSheet.sheet)
        )
        return list(result.scalars().all())

    async def sheet(self, hand: str, sheet: str) -> EigenhandSheet | None:
        result = await self.session.execute(
            select(EigenhandSheet).where(EigenhandSheet.hand == hand, EigenhandSheet.sheet == sheet)
        )
        return result.scalar_one_or_none()

    async def fassungen_of(self, hand: str) -> "list[EigenhandFassung]":
        result = await self.session.execute(
            select(EigenhandFassung)
            .where(EigenhandFassung.hand == hand)
            .order_by(EigenhandFassung.strip, EigenhandFassung.fassung)
        )
        return list(result.scalars().all())

    async def kartei(self, hand: str, style: str) -> dict:
        """The hand's rows as a Kartei-shaped dict — the seam to the compute layer."""
        kartei = {"format": 1, "hand": hand, "style": style, "sheets": {}, "strips": {}, "redo": []}
        for row in await self.sheets_of(hand):
            kartei["sheets"][row.sheet] = {
                "printed": row.printed_on,
                "strips": list(row.strips),
                "layout_sha256": row.layout_sha256,
                "scans": [],
            }
        for row in await self.fassungen_of(hand):
            record = kartei["strips"].setdefault(row.strip, {"fassungen": []})
            record["fassungen"].append(
                {
                    "id": row.fassung,
                    "sheet": row.sheet,
                    "row_index": row.row_index,
                    "attempt": row.attempt,
                    "attempts": row.attempts,
                    "status": row.status,
                    "reason": row.reason,
                    "note": row.note,
                    "png_sha256": row.png_sha256,
                    "filed": row.filed_on,
                }
            )
        return kartei

    async def add_sheet(
        self, hand: str, style: str, sheet: str, printed_on: str, strips: "list[str]", layout: dict, sha256: str
    ) -> EigenhandSheet:
        row = EigenhandSheet(
            hand=hand,
            style=style,
            sheet=sheet,
            printed_on=printed_on,
            strips=list(strips),
            layout=layout,
            layout_sha256=sha256,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def record_fassung(self, **values: Any) -> EigenhandFassung:
        row = EigenhandFassung(**values)
        self.session.add(row)
        await self.session.flush()
        return row

    async def fassung_for_row(self, hand: str, sheet: str, row_index: int) -> EigenhandFassung | None:
        """The verdict already recorded for one printed row, if any (idempotency)."""
        result = await self.session.execute(
            select(EigenhandFassung).where(
                EigenhandFassung.hand == hand, EigenhandFassung.sheet == sheet, EigenhandFassung.row_index == row_index
            )
        )
        return result.scalar_one_or_none()
