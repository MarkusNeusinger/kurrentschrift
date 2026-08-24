"""Eigenhand endpoints — the own-hand Bestand and the Bogen printer.

The capture chain is local: scans, crops and Fassung images are the reserved
own-hand dataset and never leave the author's machine
(docs/proposals/eigenhand-erfassung.md §8). Its BOOKKEEPING is not: which
Streifen exist how often, and which Bögen were printed, live in the shared DB
(``eigenhand_sheets`` / ``eigenhand_fassungen``, migration 0024) — the owner's
call on 2026-08-23, and the reason this view works on the deployed site at all.
The strip ids resolve to words through the committed plan
(``core/eigenhand/streifen.json``), so nothing about the pixels is needed to
count what a hand already covers.

* ``GET /eigenhand/hands`` — the hands that have rows, plus the styles.
* ``GET /eigenhand/bestand/{hand}`` — strips, Fassungen, Bögen, which glyphs
  and joins are written out of how many the plan can produce (capitals, digits
  and signs included), and the print queue.
* ``POST /eigenhand/sheets`` — print the next Bogen or a stack; each is
  recorded before the next selects, so no strip lands on two sheets.
* ``GET /eigenhand/sheets/{hand}/{sheet}/pdf`` — the Bogen, re-rendered from
  its stored layout (the bytes follow from the geometry, not the other way
  round).
* ``GET /eigenhand/sheets/{hand}/{sheet}/layout`` — that layout, for the local
  ingest run that registers a scan against it.
* ``POST /eigenhand/fassungen`` — the local Siebung pushing its verdicts up.

Compute is shared with the terminal chain (``core/eigenhand``), so the admin
view and ``python -m tools.eigenhand.report`` cannot disagree about one hand.
One difference is honest and deliberate: the Übergangsraum weight table is
derived from consult-only corpora and stays on the machine that built it, so
the server reports no Quoten and ranks repetition candidates by fewest
Fassungen rather than by weighted Soll gain.

Uploading scans is deliberately NOT here (owner, 2026-08-23): ingest needs the
file on disk, and the Siebung is already a local HTML review page.

Admin-gated in full — the reads too, because a Bestand is the reserved
dataset's inventory.
"""

from __future__ import annotations

import hashlib
from datetime import date as date_cls

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db
from api.schemas import (
    EigenhandBestandOut,
    EigenhandHandsOut,
    EigenhandSheetImportIn,
    EigenhandSheetIn,
    EigenhandSheetsOut,
    EigenhandSyncIn,
    EigenhandSyncOut,
)
from core.database import EigenhandRepository
from core.eigenhand import bogen, geometry
from core.eigenhand.bestand import bestand as build_bestand
from core.eigenhand.ids import STYLE_IDS, is_fassung_id, is_hand_id, is_sheet_id, is_strip_id, style_of_hand
from core.eigenhand.plan import load_plan


router = APIRouter(prefix="/eigenhand", tags=["eigenhand"], dependencies=[Depends(require_admin)])


def _checked_hand(hand: str) -> str:
    """A hand id is a row key here and a directory name locally — same shape."""
    if not is_hand_id(hand):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=(
                f"hand id {hand!r} must be a plain `<schreiber>-<stil>` name (lowercase ASCII, digits "
                f"and dashes) ending in a known style ({', '.join(STYLE_IDS)}), e.g. mn-suetterlin"
            ),
        )
    return hand


def _checked_sheet(sheet: str) -> str:
    if not is_sheet_id(sheet):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"sheet id {sheet!r} must be a plain `B<nnnn>`")
    return sheet


def _guard(call, *args, **kwargs):
    """Run shared compute and turn its CLI-style refusals into 400s.

    ``core.eigenhand`` refuses bad input with ``SystemExit`` — right for the
    terminal, fatal for a server: SystemExit is a BaseException and would
    travel straight past the exception middleware.
    """
    try:
        return call(*args, **kwargs)
    except SystemExit as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/hands", response_model=EigenhandHandsOut)
async def list_hands(db: AsyncSession = Depends(require_db)) -> EigenhandHandsOut:
    """The hands that already have rows, plus the styles a new one may use."""
    return EigenhandHandsOut(hands=await EigenhandRepository(db).hands(), styles=list(STYLE_IDS))


@router.get("/bestand/{hand}", response_model=EigenhandBestandOut)
async def read_bestand(hand: str, queue: int = 9, db: AsyncSession = Depends(require_db)) -> EigenhandBestandOut:
    """Everything the hand holds — Ist against what the strip plan can produce."""
    _checked_hand(hand)
    repo = EigenhandRepository(db)
    kartei = await repo.kartei(hand, style_of_hand(hand) or "")
    return EigenhandBestandOut.model_validate(_guard(build_bestand, load_plan(), kartei, max(1, min(queue, 50))))


@router.post("/sheets", response_model=EigenhandSheetsOut, status_code=status.HTTP_201_CREATED)
async def print_sheets(body: EigenhandSheetIn, db: AsyncSession = Depends(require_db)) -> EigenhandSheetsOut:
    """Compose the next Bogen (or a stack) and record each one before the next selects."""
    hand = _checked_hand(body.hand)
    style = body.style or style_of_hand(hand)
    if style not in geometry.PRESETS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"unknown style {style!r}")
    if body.sheets > 1 and body.strips:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="`strips` names the rows of ONE Bogen — print a stack without it"
        )
    for strip in body.strips or []:
        if not is_strip_id(strip):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"strip id {strip!r} must be a plain `S<nnnn>`")

    plan = load_plan()
    repo = EigenhandRepository(db)
    printed = []
    for _ in range(body.sheets):
        # Re-read the Kartei each round: the previous Bogen is already a row,
        # so the queue moves on and no strip is printed twice in one stack.
        kartei = await repo.kartei(hand, style)
        composed = _guard(
            bogen.compose_sheet,
            plan=plan,
            kartei=kartei,
            hand=hand,
            style=style,
            date=body.date or date_cls.today().isoformat(),
            rows=body.rows,
            repeat=body.repeat,
            strips=body.strips,
            hints=body.hints,
        )
        await repo.add_sheet(
            hand=hand,
            style=style,
            sheet=composed["sheet"],
            printed_on=composed["layout"]["provenance"]["date"],
            strips=composed["strips"],
            layout=composed["layout"],
            sha256=composed["layout_sha256"],
        )
        printed.append({"sheet": composed["sheet"], "strips": composed["strips"], "bytes": len(composed["pdf"])})
    await db.commit()
    return EigenhandSheetsOut(hand=hand, style=style, sheets=printed)


@router.put("/sheets/{hand}/{sheet}", status_code=status.HTTP_201_CREATED)
async def import_sheet(
    hand: str, sheet: str, body: EigenhandSheetImportIn, db: AsyncSession = Depends(require_db)
) -> dict:
    """Register a Bogen that was printed locally, so both surfaces mint one id space.

    Sheet ids come from whichever Kartei composed the Bogen. Pushing the local
    ones up is what keeps the server from handing out an id the paper on the
    desk already carries. Idempotent: the same layout again is a no-op, a
    DIFFERENT layout under the same id is a conflict, never an overwrite — the
    layout is the contract a scan was registered against.
    """
    _checked_hand(hand)
    _checked_sheet(sheet)
    # The layout arrives from the client and then BECOMES the record: the PDF
    # is re-rendered from it and a scan is registered against it. So it has to
    # be the layout of THIS Bogen — same check tools/eigenhand/apply.py makes
    # locally before it files a row into a hand ("refusing to file into the
    # wrong hand"). Without it a PUT on B0001 could store a layout claiming
    # another hand, and every later read would answer with that.
    named = (body.layout.get("hand"), body.layout.get("sheet"), body.layout.get("style"))
    if named != (hand, sheet, body.style):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=(
                f"layout is for {named[0]}/{named[1]} ({named[2]}), not {hand}/{sheet} ({body.style}) — "
                "refusing to record a Bogen under the wrong id"
            ),
        )
    rows = [row.get("strip") for row in body.layout.get("rows", [])]
    if rows != list(body.strips):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=f"strips {body.strips} do not match the layout's rows {rows}"
        )
    # Derived, never trusted: the hash is what the idempotency and the conflict
    # below turn on, so a client could otherwise declare two different layouts
    # identical (or one layout different from itself).
    digest = hashlib.sha256(bogen.layout_text(body.layout).encode()).hexdigest()
    if digest != body.layout_sha256:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"layout_sha256 {body.layout_sha256[:10]}… does not match the layout ({digest[:10]}…)",
        )

    repo = EigenhandRepository(db)
    existing = await repo.sheet(hand, sheet)
    if existing is not None:
        if existing.layout_sha256 != digest:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail=f"{sheet} is already recorded with a different layout ({existing.layout_sha256[:10]}…)",
            )
        return {"sheet": sheet, "imported": False}
    await repo.add_sheet(
        hand=hand,
        style=body.style,
        sheet=sheet,
        printed_on=body.printed_on,
        strips=body.strips,
        layout=body.layout,
        sha256=digest,
    )
    await db.commit()
    return {"sheet": sheet, "imported": True}


@router.get("/sheets/{hand}/{sheet}/pdf")
async def read_sheet_pdf(hand: str, sheet: str, db: AsyncSession = Depends(require_db)) -> Response:
    """The Bogen itself, re-rendered from its stored layout — same bytes, every time."""
    row = await _sheet_row(hand, sheet, db)
    pdf = _guard(bogen.render_pdf, row.layout)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{hand}-{sheet}.pdf"',
            # Never cached: this is a working document, and an operator who
            # reprints must not get the browser's older copy.
            "Cache-Control": "no-store",
        },
    )


@router.get("/sheets/{hand}/{sheet}/layout")
async def read_sheet_layout(hand: str, sheet: str, db: AsyncSession = Depends(require_db)) -> dict:
    """The layout sidecar — what a local ingest run registers the scan against."""
    row = await _sheet_row(hand, sheet, db)
    return row.layout


async def _sheet_row(hand: str, sheet: str, db: AsyncSession):
    _checked_hand(hand)
    _checked_sheet(sheet)
    row = await EigenhandRepository(db).sheet(hand, sheet)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Bogen {sheet} of {hand} is not recorded")
    return row


@router.post("/fassungen", response_model=EigenhandSyncOut)
async def record_fassungen(body: EigenhandSyncIn, db: AsyncSession = Depends(require_db)) -> EigenhandSyncOut:
    """Record the Siebung's verdicts — idempotent per printed row, never overwriting.

    The local chain owns the judging (the pixels are there); this is the push
    that makes the counts visible in the admin view. A row already judged is
    skipped when the verdict matches and refused when it conflicts — the same
    rule as `tools/eigenhand/apply.py`, so a re-run of a sync is safe and a
    contradiction is loud.

    Every verdict has to name a row that was actually PRINTED: the Bogen must
    be recorded for this hand, the row index must exist on it, and the strip
    must be the one that row carried. A Fassung IS a Beleg — it moves the
    Bestand and marks a Streifen `belegt` — so a verdict for a Bogen nobody
    printed would inflate the counts out of thin air. Push the sheets first
    (`tools.eigenhand.sync` does, in that order).
    """
    hand = _checked_hand(body.hand)
    repo = EigenhandRepository(db)
    recorded = skipped = 0
    sheets: dict[str, list[str]] = {}
    for item in body.fassungen:
        if not is_strip_id(item.strip) or not is_fassung_id(item.fassung) or not is_sheet_id(item.sheet):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail=f"malformed ids in {item.strip}/{item.fassung} on {item.sheet}"
            )
        if item.sheet not in sheets:
            row = await repo.sheet(hand, item.sheet)
            if row is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Bogen {item.sheet} is not recorded for {hand} — register the printed sheet first "
                        "(PUT /eigenhand/sheets/{hand}/{sheet}), then push its verdicts"
                    ),
                )
            sheets[item.sheet] = list(row.strips)
        printed = sheets[item.sheet]
        if item.row_index >= len(printed):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"{item.sheet} has {len(printed)} rows — there is no row {item.row_index}",
            )
        if printed[item.row_index] != item.strip:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"{item.sheet} row {item.row_index} carried {printed[item.row_index]}, not {item.strip}",
            )
        existing = await repo.fassung_for_row(hand, item.sheet, item.row_index)
        if existing is not None:
            if existing.status != item.status:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail=(
                        f"{item.sheet} row {item.row_index} is already recorded as {existing.status} "
                        f"({existing.strip}/{existing.fassung}) — conflicting verdict, withdraw it explicitly"
                    ),
                )
            skipped += 1
            continue
        await repo.record_fassung(
            hand=hand,
            strip=item.strip,
            fassung=item.fassung,
            sheet=item.sheet,
            row_index=item.row_index,
            attempt=item.attempt,
            attempts=item.attempts,
            status=item.status,
            reason=item.reason,
            note=item.note,
            png_sha256=item.png_sha256,
            filed_on=item.filed_on,
        )
        recorded += 1
    await db.commit()
    return EigenhandSyncOut(hand=hand, recorded=recorded, skipped=skipped)
