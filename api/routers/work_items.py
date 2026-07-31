"""Work-item endpoints — the Werkbank's Auftragskorb (stage W1).

The admin's channel into a working session: instead of screenshotting a bad
letter, join or word, they mark the element in the Werkbank and file it here.
A session lists the open items at round start, works them off and PATCHes each
row to status 'done' with a resolution note. These are internal work notes,
not measurement and not public content — every endpoint is admin-gated (unlike
the occurrence reads), and nothing here touches rendering.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.schemas import WorkItemIn, WorkItemOut, WorkItemUpdate
from core.database import Source, WorkItem, WorkItemRepository
from core.shaping import is_registry_glyph_key


router = APIRouter(prefix="/sources/{source_id}/work-items", tags=["work-items"], dependencies=[Depends(require_admin)])


def _reject_unknown_keys(keys: set[str | None]) -> None:
    """A marked element must be a registry glyph — a typo'd key would file
    fine but point at nothing a session could work on."""
    unknown = sorted(k for k in keys if k is not None and not is_registry_glyph_key(k))
    if unknown:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"not registry glyphs: {', '.join(map(repr, unknown))}"
        )


def _to_out(row: WorkItem) -> WorkItemOut:
    return WorkItemOut(
        id=row.id,
        kind=row.kind,
        glyph_key=row.glyph_key,
        left_key=row.left_key,
        right_key=row.right_key,
        word=row.word,
        specimen_kind=row.specimen_kind,
        specimen_id=row.specimen_id,
        note=row.note,
        status=row.status,
        resolution=row.resolution,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[WorkItemOut])
async def list_work_items(
    status: Literal["open", "done"] | None = None,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """This source's filed tasks, oldest first — the order a session works
    them off. `?status=open` is the round's queue, `?status=done` the archive;
    without the filter both come back. Uncached: the admin files while a
    session runs."""
    rows = await WorkItemRepository(db).list(source.id, status=status)
    return [_to_out(r) for r in rows]


@router.post("", response_model=WorkItemOut, status_code=201)
async def create_work_item(
    payload: WorkItemIn, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """File one task. Returns the stored row incl. its `id` — the handle the
    completing PATCH needs."""
    _reject_unknown_keys({payload.glyph_key, payload.left_key, payload.right_key})
    row = await WorkItemRepository(db).create(
        source_id=source.id,
        kind=payload.kind,
        glyph_key=payload.glyph_key,
        left_key=payload.left_key,
        right_key=payload.right_key,
        word=payload.word,
        specimen_kind=payload.specimen_kind,
        specimen_id=payload.specimen_id,
        note=payload.note,
        status="open",
    )
    return _to_out(row)


@router.patch("/{item_id}", response_model=WorkItemOut)
async def update_work_item(
    item_id: int,
    payload: WorkItemUpdate,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """Partial update of note / status / resolution. Setting `status` to
    'done' is how a session marks the item completed; unmentioned fields stay
    as they are (`exclude_unset` — an omitted note is not an empty note)."""
    repo = WorkItemRepository(db)
    row = await repo.get(item_id, source_id=source.id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no work item {item_id} for source {source.id!r}")
    await repo.update(row, **payload.model_dump(exclude_unset=True, exclude_none=True))
    return _to_out(row)


@router.delete("/{item_id}", status_code=204)
async def delete_work_item(
    item_id: int, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """Drop a filed task — a misfiling, not a completion (a worked item is
    closed with status 'done' so the archive stays readable)."""
    deleted = await WorkItemRepository(db).delete(item_id, source.id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no work item {item_id} for source {source.id!r}")
