"""Work-item endpoints — the Werkbank's Auftragskorb (stages W1 + W4).

The admin's channel into a working session: instead of screenshotting a bad
letter, join or word, they mark the element in the Werkbank and file it here.
These are internal work notes, not measurement and not public content — every
endpoint is admin-gated (unlike the occurrence reads), and nothing here touches
rendering.

Two surfaces over the same rows:

- `/sources/{source_id}/work-items` — the SPA's source-scoped view: file,
  list, drop.
- `/work-items` — the working session's view: the queue across ALL sources plus
  the protocol PATCH. Deliberately source-free, because a session that has to
  guess a `source_id` before it can even read its tasks guesses the path
  instead and gets a bare 404 (`{"detail": "Not Found"}` is an unknown PATH;
  an unknown source answers `source 'x' not found`).

The protocol itself (`docs/proposals/optimierungs-werkbank.md` §5) is enforced
here rather than trusted: a session states what it understood and whether it
reproduced the complaint BEFORE it changes anything, and names the diagnosed
stage plus what changed when it closes. `check_transition` is the whole rule
set, kept pure so it can be tested without a DB.
"""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.schemas import WorkItemIn, WorkItemOut, WorkItemStatus, WorkItemUpdate
from core.database import Source, SourceRepository, WorkItem, WorkItemRepository
from core.shaping import is_registry_glyph_key


router = APIRouter(prefix="/sources/{source_id}/work-items", tags=["work-items"], dependencies=[Depends(require_admin)])
session_router = APIRouter(prefix="/work-items", tags=["work-items"], dependencies=[Depends(require_admin)])

# What each status transition demands. 'ack' is the restatement gate — the
# session says what it takes the task to be and whether it saw the problem;
# closing additionally needs the diagnosed stage and the outcome. `understanding`
# is NOT in the closing set: it must already be STORED, which is what makes the
# ack step unskippable (see `check_transition`).
_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "ack": ("understanding", "reproduced"),
    "done": ("stage", "resolution"),
    "returned": ("stage", "resolution"),
}

# The fields the protocol owns. They may only be written BY a transition that
# demands them — a restatement smuggled in on a status-less PATCH would never
# pass through 'ack', so the Korb could never offer it for rejection.
_PROTOCOL_FIELDS = ("understanding", "reproduced", "stage", "resolution")

_DOC = "see docs/proposals/optimierungs-werkbank.md §5"


def _blank(value: Any) -> bool:
    """A field counts as missing when it is unset or whitespace only — an empty
    `resolution` would satisfy the letter of the protocol and none of its point."""
    return value is None or (isinstance(value, str) and not value.strip())


def check_transition(stored: Mapping[str, Any], changes: Mapping[str, Any]) -> str | None:
    """The §5 protocol as a pure rule: `None` if the PATCH may proceed, else the
    422 message.

    `stored` is the row as it is now, `changes` the fields the PATCH sends. Three
    rules, all serving the same purpose — the restatement must be visible while
    it can still be corrected:

    1. Protocol fields travel WITH their transition. A status-less PATCH may
       edit the note and nothing else.
    2. 'ack' needs the restatement and whether the complaint reproduced.
    3. Closing needs a STORED `understanding` — the ack has to have happened in
       its own step — plus the diagnosed stage and the outcome.

    The way back to 'open' (the admin rejecting a restatement) is always
    allowed: rejecting must never be harder than filing.
    """
    target = changes.get("status")
    required = _REQUIRED_FIELDS.get(target) if target is not None else None
    if required is None:
        written = [f for f in _PROTOCOL_FIELDS if f in changes]
        if written:
            return (
                f"protocol fields ({', '.join(written)}) are written by the transition that demands them — "
                f"send them with status 'ack', 'done' or 'returned' ({_DOC})"
            )
        return None

    if target != "ack" and _blank(stored.get("understanding")):
        return (
            f"an item is closed only after it was understood — PATCH status 'ack' with `understanding` and "
            f"`reproduced` first, then close it ({_DOC})"
        )

    missing = [f for f in required if _blank(changes.get(f, stored.get(f)))]
    if not missing:
        return None
    listed = ", ".join(missing)
    if target == "ack":
        return (
            f"status 'ack' records what the session understood before it changes anything — missing: {listed} ({_DOC})"
        )
    return (
        f"closing a work item needs the protocol fields — missing: {listed}. `stage` names the diagnosed stage, "
        f"`resolution` what changed ({_DOC})"
    )


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
        source_id=row.source_id,
        kind=row.kind,
        glyph_key=row.glyph_key,
        left_key=row.left_key,
        right_key=row.right_key,
        word=row.word,
        specimen_kind=row.specimen_kind,
        specimen_id=row.specimen_id,
        note=row.note,
        status=row.status,
        understanding=row.understanding,
        reproduced=row.reproduced,
        stage=row.stage,
        resolution=row.resolution,
        acked_at=row.acked_at,
        closed_at=row.closed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _patch_row(row: WorkItem, payload: WorkItemUpdate, db: AsyncSession) -> WorkItemOut:
    """Shared body of both PATCH routes: check the protocol, stamp the
    transition, write. The timestamps are server-side — a session reporting when
    it worked is not evidence, the row's own clock is."""
    changes: dict[str, Any] = payload.model_dump(exclude_unset=True, exclude_none=True)
    problem = check_transition(
        {"understanding": row.understanding, "stage": row.stage, "resolution": row.resolution}, changes
    )
    if problem is not None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=problem)

    target = changes.get("status")
    now = datetime.now(UTC)
    if target == "ack" and row.acked_at is None:
        changes["acked_at"] = now
    elif target in ("done", "returned"):
        changes["closed_at"] = now
    elif target == "open":
        # Reopened by a rejection: the row is live again, so it has no closing
        # time. `acked_at` and `understanding` stay — the rejected restatement
        # is part of the record, and the admin's correction lands in `note`.
        changes["closed_at"] = None
    await WorkItemRepository(db).update(row, **changes)
    return _to_out(row)


async def _require_known_source(source_id: str, db: AsyncSession) -> None:
    """404 on a source that does not exist. Lives outside the list route because
    the route's own `status` query parameter shadows FastAPI's `status` module."""
    if await SourceRepository(db).get(source_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"source {source_id!r} not found")


async def _require_row(item_id: int, db: AsyncSession, source_id: str | None = None) -> WorkItem:
    row = await WorkItemRepository(db).get(item_id, source_id=source_id)
    if row is None:
        scope = f" for source {source_id!r}" if source_id is not None else ""
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no work item {item_id}{scope}")
    return row


# ------------------------------------------------------- Source-scoped (the SPA)


@router.get("", response_model=list[WorkItemOut])
async def list_work_items(
    status: WorkItemStatus | None = None,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """This source's filed tasks, oldest first — the order a session works
    them off. `?status=open` is the round's queue, `?status=done` the archive;
    without the filter all four states come back. Uncached: the admin files
    while a session runs."""
    rows = await WorkItemRepository(db).list(source.id, status=status)
    return [_to_out(r) for r in rows]


@router.post("", response_model=WorkItemOut, status_code=201)
async def create_work_item(
    payload: WorkItemIn, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """File one task. Returns the stored row incl. its `id` — the handle the
    protocol PATCHes need."""
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
    """Source-scoped twin of `PATCH /work-items/{item_id}` — same protocol
    rules, used by the admin UI (which always knows its source). Unmentioned
    fields stay as they are (`exclude_unset` — an omitted note is not an empty
    note)."""
    row = await _require_row(item_id, db, source_id=source.id)
    return await _patch_row(row, payload, db)


@router.delete("/{item_id}", status_code=204)
async def delete_work_item(
    item_id: int, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """Drop a filed task — a misfiling, not a completion (a worked item is
    closed with status 'done' so the archive stays readable)."""
    deleted = await WorkItemRepository(db).delete(item_id, source.id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no work item {item_id} for source {source.id!r}")


# ------------------------------------------------- Source-free (working session)


@session_router.get("", response_model=list[WorkItemOut])
async def list_all_work_items(
    status: WorkItemStatus | None = None, source_id: str | None = None, db: AsyncSession = Depends(require_db)
):
    """The round's queue across every source, oldest first — the one call a
    session needs at round start (`?status=open`). Each row carries its own
    `source_id`, so the Werkbank links and any follow-up read are reachable
    from the response alone. `?source_id=` narrows it and 404s on an unknown
    source instead of quietly returning an empty list."""
    if source_id is not None:
        await _require_known_source(source_id, db)
    rows = await WorkItemRepository(db).list_all(status=status, source_id=source_id)
    return [_to_out(r) for r in rows]


@session_router.get("/{item_id}", response_model=WorkItemOut)
async def get_work_item(item_id: int, db: AsyncSession = Depends(require_db)):
    """One filed task by id — the row a session re-reads before closing it."""
    return _to_out(await _require_row(item_id, db))


@session_router.patch("/{item_id}", response_model=WorkItemOut)
async def patch_work_item(item_id: int, payload: WorkItemUpdate, db: AsyncSession = Depends(require_db)):
    """The protocol PATCH: 'ack' with the restatement before working, 'done'
    (or 'returned') with the diagnosed stage and the outcome afterwards. A
    422 names exactly which protocol field is missing."""
    row = await _require_row(item_id, db)
    return await _patch_row(row, payload, db)
