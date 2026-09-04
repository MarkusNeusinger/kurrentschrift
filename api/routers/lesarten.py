"""Lesarten — the real words a guessed word could be read as.

Public read: `GET /lesarten?text=Muhme` answers the bucket of the guess's
look-alike key (core.lesarten), ranked — a handful of words per query, cached
like the other public reads; never the vocabulary itself (the dictionary is
GPL server data, data/corpora/igerman98/SOURCE.md).

Admin load (tools.lesarten.sync, the direction every write takes): open a
generation, post the words in batches — the server computes each bucket key
with the same function the read uses — then commit, which switches the live
generation in one step and drops the old one. An abandoned load is dropped
by DELETE or by the next `begin`.

A build's source label names the look-alike fold it was bucketed with
(`core.lesarten.is_current_fold`), and its content hash covers that fold, so a
changed table can neither be refused as already live nor stay live unnoticed:
the `dictionary` block reports such a generation as `stale`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db
from api.http import CACHE_CONTROL
from api.schemas import (
    LesartDictionaryOut,
    LesartenOut,
    LesartFormsIn,
    LesartFormsOut,
    LesartGenerationIn,
    LesartGenerationOut,
    LesartReadingOut,
    LesartSwapOut,
)
from core.database import LesartDictionary, LesartRepository
from core.lesarten import DEFAULT_LIMIT, MAX_TEXT_LEN, WORD_MAX, is_current_fold, lesart_key, rank_readings


router = APIRouter(prefix="/lesarten", tags=["lesarten"])


async def _require_open(repo: LesartRepository, gen: int) -> None:
    """Only ONE generation is ever open: the one `begin` hands out, live + 1.
    Anything else — the live one, an older one, a number skipped ahead — is
    refused, so two loads can never fill the table side by side."""
    meta = await repo.dictionary()
    open_gen = (meta.active_gen if meta else 0) + 1
    if gen != open_gen:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail=f"generation {gen} is not the open one ({open_gen}) — begin a new load"
        )


def _dictionary_out(meta: LesartDictionary | None) -> LesartDictionaryOut | None:
    if meta is None:
        return None
    # The loader stamps the fold it bucketed with into the source label; a build
    # carrying an older one answers from buckets this code no longer computes.
    return LesartDictionaryOut(
        source=meta.source,
        forms=meta.forms,
        sha256=meta.sha256,
        stale=not is_current_fold(meta.source),
        updated_at=meta.updated_at,
    )


@router.get("", response_model=LesartenOut, response_model_by_alias=True)
async def get_lesarten(
    response: Response,
    text: str = Query(min_length=1, max_length=MAX_TEXT_LEN),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=24),
    db: AsyncSession = Depends(require_db),
) -> LesartenOut:
    """The readings of one guessed word — real words only, cheapest swaps first."""
    guess = text.strip()
    if not guess:
        raise HTTPException(422, detail="text is blank")
    repo = LesartRepository(db)
    meta = await repo.dictionary()
    readings = rank_readings(guess, await repo.candidates(lesart_key(guess)), limit)
    response.headers["Cache-Control"] = CACHE_CONTROL
    return LesartenOut(
        text=guess,
        readings=[
            LesartReadingOut(
                word=r.word,
                bank=r.bank,
                cost=r.cost,
                swaps=[LesartSwapOut(index=s.index, **{"from": s.from_}, to=s.to) for s in r.swaps],
            )
            for r in readings
        ],
        dictionary=_dictionary_out(meta),
    )


@router.get("/dictionary", response_model=LesartDictionaryOut | None)
async def get_dictionary(response: Response, db: AsyncSession = Depends(require_db)) -> LesartDictionaryOut | None:
    """Which vocabulary build is live (null until the first load)."""
    response.headers["Cache-Control"] = CACHE_CONTROL
    return _dictionary_out(await LesartRepository(db).dictionary())


@router.post(
    "/dictionary/generations",
    response_model=LesartGenerationOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def begin_generation(body: LesartGenerationIn, db: AsyncSession = Depends(require_db)) -> LesartGenerationOut:
    """Open a new generation to load into. Idempotent per build: the same
    content hash as the live build is refused with 409 — nothing to load."""
    repo = LesartRepository(db)
    meta = await repo.dictionary()
    if meta is not None and meta.sha256 == body.sha256:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="this build is already live (same sha256) — nothing to load"
        )
    gen = await repo.begin_generation()
    await db.commit()
    return LesartGenerationOut(generation=gen)


@router.post(
    "/dictionary/generations/{gen}/forms", response_model=LesartFormsOut, dependencies=[Depends(require_admin)]
)
async def add_forms(gen: int, body: LesartFormsIn, db: AsyncSession = Depends(require_db)) -> LesartFormsOut:
    """Add a batch of words to the open generation (keys computed here).

    An unusable word — blank, containing whitespace, or longer than
    `WORD_MAX` (the column's own bound) — fails the WHOLE batch with 400
    rather than being skipped silently. Dropping is a loader decision and
    `tools.lesarten.sync` takes it visibly, printing what it left out; a
    server that swallowed the same word would leave every other client with
    an `inserted` count it cannot explain, and a vocabulary quietly short of
    what it sent.
    """
    repo = LesartRepository(db)
    await _require_open(repo, gen)
    rows: list[tuple[str, str, bool]] = []
    for word, bank in body.words:
        w = word.strip()
        if not w or len(w) > WORD_MAX or any(ch.isspace() for ch in w):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail=f"{word!r} is not a single word of at most {WORD_MAX} characters"
            )
        rows.append((lesart_key(w), w, bool(bank)))
    inserted = await repo.add_forms(gen, rows)
    total = await repo.count_forms(gen)
    await db.commit()
    return LesartFormsOut(generation=gen, inserted=inserted, total=total)


@router.post(
    "/dictionary/generations/{gen}/commit", response_model=LesartDictionaryOut, dependencies=[Depends(require_admin)]
)
async def commit_generation(
    gen: int, body: LesartGenerationIn, db: AsyncSession = Depends(require_db)
) -> LesartDictionaryOut:
    """Make the open generation live and drop every other one."""
    repo = LesartRepository(db)
    await _require_open(repo, gen)
    if await repo.count_forms(gen) == 0:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"generation {gen} holds no forms — nothing to commit")
    meta = await repo.commit_generation(gen, body.source, body.sha256)
    await db.commit()
    out = _dictionary_out(meta)
    assert out is not None
    return out


@router.delete(
    "/dictionary/generations/{gen}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)]
)
async def drop_generation(gen: int, db: AsyncSession = Depends(require_db)) -> Response:
    """Abandon a load in progress (the live generation cannot be dropped)."""
    repo = LesartRepository(db)
    meta = await repo.dictionary()
    if meta is not None and gen == meta.active_gen:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"generation {gen} is live — commit a new one instead")
    await repo.drop_generation(gen)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
