"""Quiz word endpoints — the public read-only reading-drill word bank."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db
from api.schemas import QuizWordOut
from core.database import QuizWord, QuizWordRepository


router = APIRouter(prefix="/quiz-words", tags=["quiz-words"])

# Public and rarely changing — cache hard at the edge (mirrors write.py).
CACHE_CONTROL = "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"


def _to_out(row: QuizWord) -> QuizWordOut:
    return QuizWordOut(word=row.word, distractors=list(row.distractors), era=row.era, note=row.note, fugen=row.fugen)


@router.get("", response_model=list[QuizWordOut])
async def list_quiz_words(response: Response, db: AsyncSession = Depends(require_db)) -> list[QuizWordOut]:
    rows = await QuizWordRepository(db).list()
    response.headers["Cache-Control"] = CACHE_CONTROL
    return [_to_out(r) for r in rows]
