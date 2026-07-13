"""Quiz word endpoints — the public read-only reading-drill word bank."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.cache import set_public_cache
from api.dependencies import require_db
from api.schemas import QuizWordOut
from core.database import QuizWord, QuizWordRepository


router = APIRouter(prefix="/quiz-words", tags=["quiz-words"])


def _to_out(row: QuizWord) -> QuizWordOut:
    return QuizWordOut(word=row.word, distractors=list(row.distractors), era=row.era, note=row.note, fugen=row.fugen)


@router.get("", response_model=list[QuizWordOut])
async def list_quiz_words(response: Response, db: AsyncSession = Depends(require_db)) -> list[QuizWordOut]:
    rows = await QuizWordRepository(db).list()
    set_public_cache(response)
    return [_to_out(r) for r in rows]
