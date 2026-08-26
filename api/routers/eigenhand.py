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
* ``POST /eigenhand/sheets`` — print the next Bogen or a stack: ONE selection
  for the whole job (the pages continue the queue, no strip on two sheets),
  every Bogen recorded as its own row. A job always starts at the front of the
  queue — a printed-but-unwritten Bogen holds nothing back (owner, 2026-08-26).
* ``GET /eigenhand/sheets/{hand}/{sheet}/pdf`` — the Bogen, re-rendered from
  its stored layout (the bytes follow from the geometry, not the other way
  round).
* ``GET /eigenhand/stacks/{hand}/pdf?sheets=B0007,B0008`` — several recorded
  Bögen as ONE PDF, one page each, re-rendered the same way.
* ``GET /eigenhand/sheets/{hand}/{sheet}/layout`` — that layout, for the local
  ingest run that registers a scan against it.
* ``POST /eigenhand/fassungen`` — the local Siebung pushing its verdicts up.
* ``GET /eigenhand/archive/{hand}`` — the hand's bookkeeping as rows, for the
  archive run and the restore check (strip hashes, never strip bytes).
* ``GET|PUT /eigenhand/setups[/{hand}]`` — the hand's standing nib/ink/paper.
* ``GET|PUT /eigenhand/strips/…`` — the written strip itself, and any single
  word cut out of it.

The strips are the one place where own-hand PIXELS do travel (owner, 2026-08-24)
— so that the workbench can show a written Streifen the way it shows a chart
crop. They stay admin-gated and uncacheable, and the private ARCHIVE stays the
master copy: every stored row carries the sha256 its archived file has, which is
what makes „repo + archive restores everything" a check rather than a hope.

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

import base64
import binascii
import hashlib
import io
import unicodedata
from datetime import date as date_cls
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db
from api.schemas import (
    EigenhandArchiveOut,
    EigenhandBestandOut,
    EigenhandHandsOut,
    EigenhandSetupIn,
    EigenhandSetupOut,
    EigenhandSetupsOut,
    EigenhandSheetImportIn,
    EigenhandSheetIn,
    EigenhandSheetsOut,
    EigenhandStripIn,
    EigenhandStripListOut,
    EigenhandStripOut,
    EigenhandSyncIn,
    EigenhandSyncOut,
)
from core.database import EigenhandRepository
from core.eigenhand import bogen, crop, geometry
from core.eigenhand.bestand import bestand as build_bestand
from core.eigenhand.ids import STYLE_IDS, is_fassung_id, is_hand_id, is_sheet_id, is_strip_id, style_of_hand
from core.eigenhand.plan import load_plan, words_of


router = APIRouter(prefix="/eigenhand", tags=["eigenhand"], dependencies=[Depends(require_admin)])

# A strip is one A4 row at 300 DPI — measured ~200–370 KB. The cap is generous
# enough for 600 DPI Kurrent (Schwellzug hairlines, proposal §6) and small
# enough that a mis-pointed upload cannot push a scan of a whole page into a
# row that is supposed to hold one strip.
MAX_STRIP_BYTES = 8 * 1024 * 1024

# The pixels are the reserved dataset: no shared cache, no disk cache, no
# revalidation. `private` alone would still let the browser keep a copy.
STRIP_CACHE_CONTROL = "private, no-store"


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
    """Compose the next Bogen or a whole stack in ONE selection, then record every Bogen as its own row.

    The queue is walked once for the job (`compose_stack`): the pages continue
    it among themselves, ids are minted consecutively, and the job starts at
    the queue's front — a printed-but-unwritten Bogen holds nothing back.
    """
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
    # One Kartei read, one selection for the whole stack: the pages continue
    # the queue among themselves, and the job starts at the queue's front.
    kartei = await repo.kartei(hand, style)
    stack = _guard(
        bogen.compose_stack,
        plan=plan,
        kartei=kartei,
        hand=hand,
        style=style,
        date=body.date or date_cls.today().isoformat(),
        sheets=body.sheets,
        rows=body.rows,
        repeat=body.repeat,
        strips=body.strips,
        hints=body.hints,
    )
    printed = []
    for composed in stack["sheets"]:
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


@router.get("/stacks/{hand}/pdf")
async def read_stack_pdf(hand: str, sheets: str, db: AsyncSession = Depends(require_db)) -> Response:
    """Several recorded Bögen as ONE PDF — one page each, re-rendered from their layouts.

    `sheets` is a comma-separated list of ids in page order (the order the
    print job returned them). Every id must be recorded for this hand; a
    missing one is a 404 for the whole request, not a shorter document.
    """
    ids = [part.strip() for part in sheets.split(",") if part.strip()]
    if not ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="`sheets` names at least one Bogen")
    if len(ids) > 20:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="a stack holds at most 20 Bögen")
    layouts = [(await _sheet_row(hand, sheet, db)).layout for sheet in ids]
    pdf = _guard(bogen.render_stack_pdf, layouts)
    name = ids[0] if len(ids) == 1 else f"{ids[0]}-{ids[-1]}"
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{hand}-{name}.pdf"', "Cache-Control": "no-store"},
    )


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
            feder=item.feder,
            tinte=item.tinte,
            papier=item.papier,
            geraet=item.geraet,
        )
        recorded += 1
    await db.commit()
    return EigenhandSyncOut(hand=hand, recorded=recorded, skipped=skipped)


@router.get("/archive/{hand}", response_model=EigenhandArchiveOut)
async def read_archive(hand: str, db: AsyncSession = Depends(require_db)) -> EigenhandArchiveOut:
    """One hand's bookkeeping as rows — for the archive run and its restore check.

    Everything the `eigenhand_*` tables hold for this hand except the strip
    BYTES: the setup, every Bogen with its layout, every verdict, and every
    stored strip's metadata with its sha256. The images stay where they belong
    — in the private archive — and the hashes here are what a restore compares
    against, so „repo + archive brings it all back" is a check and not a hope.
    """
    _checked_hand(hand)
    repo = EigenhandRepository(db)
    setup = await repo.hand_setup(hand)
    sheets = await repo.sheets_of(hand)
    style = setup.style if setup else (sheets[0].style if sheets else style_of_hand(hand) or "")
    return EigenhandArchiveOut(
        hand=hand,
        style=style,
        setup=_setup_out(setup) if setup else None,
        sheets=[
            {
                "sheet": row.sheet,
                "style": row.style,
                "printed_on": row.printed_on,
                "strips": list(row.strips),
                "layout": row.layout,
                "layout_sha256": row.layout_sha256,
            }
            for row in sheets
        ],
        fassungen=[
            {
                "strip": row.strip,
                "fassung": row.fassung,
                "sheet": row.sheet,
                "row_index": row.row_index,
                "attempt": row.attempt,
                "attempts": row.attempts,
                "status": row.status,
                "reason": row.reason,
                "note": row.note,
                "png_sha256": row.png_sha256,
                "filed_on": row.filed_on,
                "feder": row.feder,
                "tinte": row.tinte,
                "papier": row.papier,
                "geraet": row.geraet,
            }
            for row in await repo.fassungen_of(hand)
        ],
        strips=[_strip_out(row) for row in await repo.strips_of(hand)],
    )


# --------------------------------------------------------------- standing setup


@router.get("/setups", response_model=EigenhandSetupsOut)
async def list_setups(db: AsyncSession = Depends(require_db)) -> EigenhandSetupsOut:
    """Every hand's standing nib/ink/paper — what a new session writes with."""
    return EigenhandSetupsOut(setups=[_setup_out(row) for row in await EigenhandRepository(db).hand_setups()])


@router.get("/setups/{hand}", response_model=EigenhandSetupOut)
async def read_setup(hand: str, db: AsyncSession = Depends(require_db)) -> EigenhandSetupOut:
    """One hand's standing setup — `ingest` reads it instead of asking again."""
    _checked_hand(hand)
    row = await EigenhandRepository(db).hand_setup(hand)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{hand} has no standing setup recorded yet")
    return _setup_out(row)


@router.put("/setups/{hand}", response_model=EigenhandSetupOut)
async def write_setup(hand: str, body: EigenhandSetupIn, db: AsyncSession = Depends(require_db)) -> EigenhandSetupOut:
    """Type the setup once. Every later Fassung records the values it really used.

    An update is deliberately a plain overwrite rather than a new cohort row:
    the standing setup answers „what do I reach for now", and the historical
    truth lives per Fassung, where a mid-campaign change shows up as a visible
    break in the data instead of a reconstruction.
    """
    _checked_hand(hand)
    style = body.style or style_of_hand(hand)
    if style not in geometry.PRESETS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"unknown style {style!r}")
    repo = EigenhandRepository(db)
    await repo.upsert_hand_setup(hand, style, **body.model_dump(exclude={"style"}))
    await db.commit()
    # Re-read rather than serialise the committed instance: `created_at` and
    # `updated_at` are server-side defaults, so the in-session object would have
    # to lazy-load them — which is exactly the IO an async session refuses to
    # do implicitly.
    return _setup_out(await repo.hand_setup(hand))


def _setup_out(row) -> EigenhandSetupOut:
    return EigenhandSetupOut(
        hand=row.hand,
        style=row.style,
        label=row.label,
        feder=row.feder,
        tinte=row.tinte,
        papier=row.papier,
        geraet=row.geraet,
        note=row.note,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )


# ---------------------------------------------------------------- strip images


@router.get("/strips/{hand}", response_model=EigenhandStripListOut)
async def list_strips(
    hand: str, strip: str | None = None, db: AsyncSession = Depends(require_db)
) -> EigenhandStripListOut:
    """Which strips a hand has stored — metadata only, never the pixels.

    The words come from the committed plan rather than from the row, so a
    listing says what is on a strip without loading a single byte of image.
    """
    _checked_hand(hand)
    if strip is not None and not is_strip_id(strip):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"strip id {strip!r} must be a plain `S<nnnn>`")
    plan = load_plan()
    rows = await EigenhandRepository(db).strips_of(hand, strip)
    return EigenhandStripListOut(hand=hand, strips=[_strip_out(row, plan) for row in rows])


def _strip_out(row, plan: dict | None = None) -> EigenhandStripOut:
    """One strip row as the API states it — metadata, words, never the bytes."""
    return EigenhandStripOut(
        strip=row.strip,
        fassung=row.fassung,
        sheet=row.sheet,
        row_index=row.row_index,
        width_px=row.width_px,
        height_px=row.height_px,
        dpi=row.dpi,
        crop_origin_mm=list(row.crop_origin_mm or []),
        sha256=row.sha256,
        bytes=row.bytes,
        words=words_of(plan, row.strip) if plan and row.strip in plan["strips"] else [],
    )


@router.get("/strips/{hand}/{strip}/{fassung}")
async def read_strip(
    hand: str,
    strip: str,
    fassung: str,
    wort: str | None = None,
    box: int | None = None,
    pad_mm: float = 1.0,
    db: AsyncSession = Depends(require_db),
) -> Response:
    """The stored strip as PNG — whole, or cut down to one word.

    A word crop needs no storage of its own: the row remembers where its crop
    started in mm, the sheet's layout says where the word's box sits, and the
    pixel width gives the scale. `wort` names the word, `box` its index in the
    row — the index is what disambiguates a word that appears twice.
    """
    _checked_hand(hand)
    _checked_strip(strip)
    _checked_fassung(fassung)
    row = await EigenhandRepository(db).strip(hand, strip, fassung)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{hand} has no stored strip {strip}/{fassung}")
    png = row.png
    filename = f"{hand}-{strip}-{fassung}"
    if wort is not None or box is not None:
        layout_row = await _layout_row(hand, row.sheet, row.row_index, db)
        word_box = _guard(crop.find_box, layout_row, wort, box)
        rect = _guard(
            crop.word_box_px,
            word_box,
            row.crop_origin_mm or [],
            row.width_px,
            row.height_px,
            layout_row.get("cut_mm") or [],
            max(0.0, min(pad_mm, 10.0)),
        )
        # Decode + re-encode is CPU-bound — off the event loop, like the chart
        # crops (api/routers/chart.py).
        png = await run_in_threadpool(crop.cut_png, png, rect)
        filename = f"{filename}-{word_box.get('word', 'wort')}"
    return Response(
        content=png,
        media_type="image/png",
        headers={"Content-Disposition": _disposition(f"{filename}.png"), "Cache-Control": STRIP_CACHE_CONTROL},
    )


def _disposition(name: str) -> str:
    """`Content-Disposition` for a filename that may not be Latin-1.

    Header values are encoded as Latin-1, so a word carrying a typographic
    quote or apostrophe would raise UnicodeEncodeError and turn the crop into a
    500 — and the frozen strip plan carries exactly those (`„wohl“`, `don’t`).
    So the plain `filename=` gets an ASCII fallback and the real name travels in
    RFC 5987 `filename*=`, which every current browser prefers.
    """
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode() or "streifen.png"
    ascii_name = ascii_name.replace('"', "").replace("\\", "")
    return f"inline; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name, safe='')}"


@router.put("/strips/{hand}/{strip}/{fassung}", status_code=status.HTTP_201_CREATED)
async def write_strip(
    hand: str, strip: str, fassung: str, body: EigenhandStripIn, db: AsyncSession = Depends(require_db)
) -> dict:
    """Store one strip image — pushed by `tools.eigenhand.sync --mit-streifen`.

    Every stored strip has to belong to a Fassung that was judged on a Bogen
    that was printed: same „no ghost rows" rule as the verdicts above, one step
    further, because pixels without a verdict would be an image nothing in the
    Bestand accounts for. The declared sha256 is VERIFIED against the bytes
    (it is the archive's identity for this file — a wrong one would break the
    restore check silently), and where the Fassung already recorded a hash, the
    two must be the same file.

    Idempotent: the same bytes again are a no-op, different bytes under the
    same id are a conflict. Overwriting is never right — the strip is the
    reserved dataset's primary evidence.
    """
    _checked_hand(hand)
    _checked_strip(strip)
    _checked_fassung(fassung)
    if not is_sheet_id(body.sheet):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"sheet id {body.sheet!r} must be a plain `B<nnnn>`")

    png = _decoded_png(body.png_base64)
    digest = hashlib.sha256(png).hexdigest()
    if digest != body.sha256:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"sha256 {body.sha256[:10]}… does not match the uploaded bytes ({digest[:10]}…)",
        )

    repo = EigenhandRepository(db)
    verdict = await repo.fassung_for_row(hand, body.sheet, body.row_index)
    if verdict is None or (verdict.strip, verdict.fassung) != (strip, fassung):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=(
                f"no Fassung {strip}/{fassung} recorded for {hand} on {body.sheet} row {body.row_index} — "
                "push the Siebung's verdicts first (POST /eigenhand/fassungen), then the strips"
            ),
        )
    if verdict.png_sha256 and verdict.png_sha256 != digest:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=(
                f"{strip}/{fassung} was recorded with png_sha256 {verdict.png_sha256[:10]}… — "
                f"these bytes are a different file ({digest[:10]}…)"
            ),
        )

    # Metadata only: this compares hashes, and reading the PNG to do it would
    # pull ~350 KB off the DB for every already-stored strip on a sync re-run.
    existing = await repo.strip_meta(hand, strip, fassung)
    if existing is not None:
        if existing.sha256 != digest:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail=f"{strip}/{fassung} is already stored with different bytes ({existing.sha256[:10]}…)",
            )
        return {"strip": strip, "fassung": fassung, "stored": False}

    # The stored dimensions are the crop's scale — a listing that disagrees
    # with the pixels would cut word crops in the wrong place, silently.
    width_px, height_px = await run_in_threadpool(_png_size, png)
    if (width_px, height_px) != (body.width_px, body.height_px):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"declared {body.width_px}×{body.height_px} px, image is {width_px}×{height_px}",
        )

    await repo.add_strip(
        hand=hand,
        strip=strip,
        fassung=fassung,
        sheet=body.sheet,
        row_index=body.row_index,
        png=png,
        width_px=width_px,
        height_px=height_px,
        dpi=body.dpi,
        crop_origin_mm=[float(v) for v in body.crop_origin_mm],
        sha256=digest,
        bytes=len(png),
    )
    await db.commit()
    return {"strip": strip, "fassung": fassung, "stored": True}


def _checked_strip(strip: str) -> str:
    if not is_strip_id(strip):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"strip id {strip!r} must be a plain `S<nnnn>`")
    return strip


def _checked_fassung(fassung: str) -> str:
    if not is_fassung_id(fassung):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Fassung id {fassung!r} must be a plain `F<nn>`")
    return fassung


def _decoded_png(encoded: str) -> bytes:
    """Base64 in, PNG bytes out — refusing anything that is not one."""
    try:
        png = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="png_base64 is not valid base64") from exc
    if len(png) > MAX_STRIP_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"strip is {len(png)} bytes — the limit is {MAX_STRIP_BYTES}",
        )
    if not png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="the uploaded bytes are not a PNG")
    return png


def _png_size(png: bytes) -> tuple[int, int]:
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(png)) as image:
            return image.size
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="the uploaded PNG could not be read") from exc


async def _layout_row(hand: str, sheet: str, row_index: int, db: AsyncSession) -> dict:
    """The layout row a strip was cut from — the word boxes a crop needs."""
    row = await EigenhandRepository(db).sheet(hand, sheet)
    if row is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Bogen {sheet} of {hand} is not recorded — its layout is what a word crop is cut against",
        )
    rows = row.layout.get("rows", [])
    if not 0 <= row_index < len(rows):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"{sheet} has no row {row_index}")
    return rows[row_index]
